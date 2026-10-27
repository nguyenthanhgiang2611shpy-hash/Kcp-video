# -*- coding: utf-8 -*-
"""Video: Trình tự chất 680 bao đường vào xe 34 tấn (từ trong ra ngoài).
Nguồn số liệu: Trinh_tu_chat_bao_xe_34T_v2.pdf
Chạy:  python3 make_video.py            -> render đầy đủ
       python3 make_video.py test       -> contact sheet khung mẫu
"""
import sys, math, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 1280, 720, 2, 25
OUT = sys.argv[2] if len(sys.argv) > 2 else "chat_bao_xe_34T_v1.mp4"

# ---------- màu ----------
CREAM = (243, 236, 220); INK = (29, 43, 58); ORANGE = (217, 119, 75)
GREEN = (38, 122, 64); RED = (178, 52, 44); MUTED = (110, 116, 120)
BAG_TOP = (252, 250, 244); BAG_FRONT = (220, 214, 200); BAG_END = (236, 231, 219)
FLOOR_C = (160, 168, 172); FLOOR_EDGE = (44, 62, 80)
WALL_FAR = (112, 138, 160); WALL_HEAD = (88, 114, 140)

# ---------- số liệu (PDF) ----------
L, WD, HROOF, HWALL = 1226, 235, 215, 80     # thùng: dài, rộng, cao mui, cao thành (cm)
BL, BW0, BW, BH = 75, 50, 47, 13             # bao: dài 75, rộng 50 (ép còn 47), dày 13
COLS, LAYERS, ROWS = 5, 9, 15
EXTRA = 5
TOTAL = ROWS * COLS * LAYERS + EXTRA
assert TOTAL == 680 and TOTAL * 50 == 34000
assert COLS * BW == WD and COLS * BW0 == 250
assert LAYERS * BH == 117 and 117 - HWALL == 37
assert L - ROWS * BL == 101

# ---------- font ----------
FP = {"serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
      "serifb": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
      "mono": "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
      "monob": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"}
_fc = {}
def F(name, size):
    k = (name, int(size * SS))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FP[name], k[1])
    return _fc[k]

# ---------- tiện ích ----------
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return ss((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))
def vn(n): return f"{n:,}".replace(",", ".")

class Cam:
    def __init__(s, cx, cy, z): s.cx, s.cy, s.z = cx, cy, z
    def P(s, x, y, z):
        # y = khoảng cách từ vách xa (0) tới mép gần người xem (235)
        u = 0.95 * x - 0.50 * y
        v = 0.18 * x + 0.32 * y - 0.90 * z
        return ((u - s.cx) * s.z * SS + W * SS / 2, (v - s.cy) * s.z * SS + H * SS / 2)

def cam_lerp(a, b, k):
    return Cam(lerp(a.cx, b.cx, k), lerp(a.cy, b.cy, k), lerp(a.z, b.z, k))

CAM_FULL = Cam(525, 30, 0.86)
CAM_HEAD = Cam(70, 10, 2.0)
CAM_HEAD2 = Cam(110, -5, 1.7)
CAM_REAR = Cam(930, 165, 1.3)

def text_w(d, s, font): return d.textlength(s, font=font)

def fit_font(d, s, name, size, maxw):
    while size > 10 and text_w(d, s, F(name, size)) > maxw * SS:
        size -= 1
    return F(name, size)

def ctext(d, xy, s, font, fill, anchor="mm"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=font, fill=fill, anchor=anchor)

def dashed(d, p0, p1, fill, width=2, dash=10, gap=8):
    x0, y0 = p0; x1, y1 = p1
    ln = math.hypot(x1 - x0, y1 - y0)
    if ln < 1: return
    n = 0.0
    while n < ln:
        a = n / ln; b = min(n + dash * SS, ln) / ln
        d.line([(lerp(x0, x1, a), lerp(y0, y1, a)), (lerp(x0, x1, b), lerp(y0, y1, b))], fill=fill, width=width * SS)
        n += (dash + gap) * SS

def arrow(d, p0, p1, fill, width=3, head=12):
    d.line([p0, p1], fill=fill, width=width * SS)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); h = head * SS
    pts = [p1, (p1[0] - h * math.cos(ang - 0.45), p1[1] - h * math.sin(ang - 0.45)),
           (p1[0] - h * math.cos(ang + 0.45), p1[1] - h * math.sin(ang + 0.45))]
    d.polygon(pts, fill=fill)

def dim_line(d, p0, p1, label, color, font, offset=(0, 0), both=True):
    """vạch đo có hai đầu mũi tên + nhãn ở giữa (tọa độ pixel 2x)"""
    d.line([p0, p1], fill=color, width=2 * SS)
    for a, b in ((p0, p1), (p1, p0)) if both else ((p0, p1),):
        ang = math.atan2(a[1] - b[1], a[0] - b[0]); h = 9 * SS
        d.polygon([a, (a[0] - h * math.cos(ang - 0.5), a[1] - h * math.sin(ang - 0.5)),
                   (a[0] - h * math.cos(ang + 0.5), a[1] - h * math.sin(ang + 0.5))], fill=color)
    mx, my = (p0[0] + p1[0]) / 2 + offset[0] * SS, (p0[1] + p1[1]) / 2 + offset[1] * SS
    bb = d.textbbox((mx, my), label, font=font, anchor="mm")
    d.rectangle([bb[0] - 6 * SS, bb[1] - 4 * SS, bb[2] + 6 * SS, bb[3] + 4 * SS], fill=CREAM)
    d.text((mx, my), label, font=font, fill=color, anchor="mm")

# ---------- vẽ thùng xe + bao ----------
def draw_truck_back(d, cam):
    P = cam.P
    # sàn
    d.polygon([P(0, 0, 0), P(L, 0, 0), P(L, WD, 0), P(0, WD, 0)], fill=FLOOR_C)
    # vách xa (thành 80 cm)
    d.polygon([P(0, 0, 0), P(L, 0, 0), P(L, 0, HWALL), P(0, 0, HWALL)], fill=WALL_FAR, outline=FLOOR_EDGE)
    # vách đầu thùng (sát cabin, cao tới mui)
    d.polygon([P(0, 0, 0), P(0, WD, 0), P(0, WD, HROOF), P(0, 0, HROOF)], fill=WALL_HEAD, outline=FLOOR_EDGE)
    # vạch kẻ sàn theo hàng (mờ)
    for r in range(1, ROWS + 1):
        d.line([P(r * BL, 0, 0), P(r * BL, WD, 0)], fill=(150, 158, 163), width=1 * SS)

def draw_truck_front(d, cam, alpha_frame=1.0):
    P = cam.P
    # mép sàn gần + đuôi (dày)
    d.polygon([P(0, WD, 0), P(L, WD, 0), P(L, WD, -8), P(0, WD, -8)], fill=FLOOR_EDGE)
    d.polygon([P(L, 0, 0), P(L, WD, 0), P(L, WD, -8), P(L, 0, -8)], fill=(60, 80, 100))
    if alpha_frame <= 0: return
    c = mix(CREAM, INK, 0.75 * alpha_frame)
    # thành gần, đuôi (nét đứt), khung mui
    dashed(d, P(0, WD, HWALL), P(L, WD, HWALL), c, 1)
    dashed(d, P(L, 0, HWALL), P(L, WD, HWALL), c, 1)
    dashed(d, P(L, WD, 0), P(L, WD, HWALL), c, 1)
    dashed(d, P(L, 0, 0), P(L, 0, HWALL), c, 1)
    dashed(d, P(0, 0, HROOF), P(L, 0, HROOF), mix(CREAM, INK, 0.4 * alpha_frame), 1, 6, 8)
    dashed(d, P(0, WD, HROOF), P(L, WD, HROOF), mix(CREAM, INK, 0.4 * alpha_frame), 1, 6, 8)
    dashed(d, P(L, 0, HROOF), P(L, WD, HROOF), mix(CREAM, INK, 0.4 * alpha_frame), 1, 6, 8)
    dashed(d, P(0, WD, 0), P(0, WD, HROOF), mix(CREAM, INK, 0.4 * alpha_frame), 1, 6, 8)

def bag_box(r, c, k, w=BW, x0=None):
    """trả (x0,y0,z0,x1,y1,z1). Cột c=0 nằm bên TRÁI màn hình (mép gần), đặt trái → phải."""
    if x0 is None: x0 = r * BL
    y1 = WD - c * w if w == BW else (COLS - c) * w
    # khi chưa ép (w=50): xếp sát vách xa, phần dư thò ra mép gần
    y0 = y1 - w
    z0 = k * BH
    return (x0, y0, z0, x0 + BL, y1, z0 + BH)

def draw_bag(d, cam, box, dz=0.0, style="n", alpha=1.0):
    x0, y0, z0, x1, y1, z1 = box
    z0 += dz; z1 += dz
    P = cam.P
    g = 1.2  # khe nhỏ giữa các bao
    x0g, x1g, y0g, y1g = x0 + g, x1 - g, y0 + g, y1 - g
    col = {"n": (120, 120, 112), "g": GREEN, "o": ORANGE, "f": (150, 150, 140)}[style]
    top = BAG_TOP if style != "o" else (255, 238, 222)
    front = BAG_FRONT if style != "o" else (240, 196, 168)
    end = BAG_END if style != "o" else (248, 214, 190)
    if alpha < 1:
        top, front, end = mix(CREAM, top, alpha), mix(CREAM, front, alpha), mix(CREAM, end, alpha)
    lw = SS * (2 if style in "go" and cam.z > 1.2 else 1)
    d.polygon([P(x0g, y1g, z0), P(x1g, y1g, z0), P(x1g, y1g, z1), P(x0g, y1g, z1)], fill=front, outline=col, width=lw)
    d.polygon([P(x1g, y0g, z0), P(x1g, y1g, z0), P(x1g, y1g, z1), P(x1g, y0g, z1)], fill=end, outline=col, width=lw)
    d.polygon([P(x0g, y0g, z1), P(x1g, y0g, z1), P(x1g, y1g, z1), P(x0g, y1g, z1)], fill=top, outline=col, width=lw)
    if cam.z > 1.0:  # vạch in trên mặt bao
        ym = (y0 + y1) / 2
        for a, b in ((0.25, 0.38), (0.45, 0.58), (0.65, 0.78)):
            d.line([P(lerp(x0, x1, a), ym, z1), P(lerp(x0, x1, b), ym, z1)], fill=(214, 120, 90), width=max(1, int(SS * cam.z * 0.7)))

def bag_index(r, c, k):
    return 675 + c if r == ROWS else r * 45 + k * 5 + c

def all_slots():
    for r in range(ROWS):
        for k in range(LAYERS):
            for c in range(COLS):
                yield r, c, k
    for c in range(EXTRA):
        yield ROWS, c, 0

def draw_bags(d, cam, visible, w=BW):
    """visible(r,c,k) -> None hoặc (dz, style). Thứ tự vẽ: x tăng, y tăng, z tăng."""
    items = []
    for r, c, k in all_slots():
        v = visible(r, c, k)
        if v is None: continue
        items.append((r, -c, k, r, c, k, v))
    items.sort(key=lambda it: (it[0], it[1], it[2]))
    for _, _, _, r, c, k, v in items:
        draw_bag(d, cam, bag_box(r, c, k, w), v[0], v[1], v[2] if len(v) > 2 else 1.0)

def drop(t, T, dur=0.35):
    """bao rơi xuống vị trí: trả dz hoặc None nếu chưa xuất hiện"""
    if t < T: return None
    return 70 * (1 - ss((t - T) / dur))

# ---------- khung chung ----------
def frame_base(bg=CREAM):
    im = Image.new("RGB", (W * SS, H * SS), bg)
    return im, ImageDraw.Draw(im)

def corners(d, color=INK):
    m, ln = 22 * SS, 34 * SS
    for (x, y, sx, sy) in ((m, m, 1, 1), (W * SS - m, m, -1, 1), (m, H * SS - m, 1, -1), (W * SS - m, H * SS - m, -1, -1)):
        d.line([(x, y), (x + sx * ln, y)], fill=color, width=3 * SS)
        d.line([(x, y), (x, y + sy * ln)], fill=color, width=3 * SS)

def footer(d, n, N, color=INK):
    f = F("mono", 12)
    d.text((66 * SS, 692 * SS), "KCP VIỆT NAM · LOGISTICS · CHẤT BAO XE 34 TẤN", font=f, fill=color, anchor="ls")
    d.text((1214 * SS, 692 * SS), f"minh họa, không theo tỷ lệ · {n}/{N}", font=f, fill=color, anchor="rs")

def chapter(im, label, t, color=INK):
    """nhãn chương nền navy hơi nghiêng, góc trên trái"""
    k = seg(t, 0.0, 0.4)
    if k <= 0: return
    f = F("monob", 18)
    tmp = Image.new("RGBA", (10, 10)); dd = ImageDraw.Draw(tmp)
    tw = int(dd.textlength(label, font=f))
    pad = 14 * SS
    lab = Image.new("RGBA", (tw + 2 * pad, 40 * SS), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lab)
    dl.rectangle([0, 0, lab.width, lab.height], fill=color + (255,))
    dl.text((pad, lab.height // 2), label, font=f, fill=CREAM, anchor="lm")
    lab = lab.rotate(2.0, expand=True, resample=Image.BICUBIC)
    x = int(lerp(-lab.width, 44 * SS, k))
    im.paste(lab, (x, 40 * SS), lab)

def counter(d, n, t=1.0, color=INK):
    f = F("monob", 17)
    s = f"ĐÃ CHẤT {n}/680 BAO"
    d.text((1238 * SS, 62 * SS), s, font=f, fill=color, anchor="rm")
    # thanh tiến độ
    x0, x1, y = 1238 - 230, 1238, 80
    d.rectangle([x0 * SS, y * SS, x1 * SS, (y + 6) * SS], fill=mix(CREAM, INK, 0.15))
    d.rectangle([x0 * SS, y * SS, (x0 + (x1 - x0) * n / 680) * SS, (y + 6) * SS], fill=GREEN if n < 680 else ORANGE)

def subtitle(d, s, t, color=INK, y=640):
    k = seg(t, 0.15, 0.6)
    if k <= 0: return
    f = fit_font(d, s, "serif", 30, 1100)
    c = mix(CREAM, color, k)
    tw = d.textlength(s, font=f) / SS
    d.rounded_rectangle([(W / 2 - tw / 2 - 24) * SS, (y - 26) * SS, (W / 2 + tw / 2 + 24) * SS, (y + 26) * SS],
                        radius=8 * SS, fill=CREAM)
    ctext(d, (W / 2, y + 8 * (1 - k)), s, f, c)

def stamp(im, s, t, color=RED, pos=(1010, 520), angle=-6):
    k = seg(t, 0.0, 0.25)
    if k <= 0: return
    f = F("monob", 24)
    tmp = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    tw = int(tmp.textlength(s, font=f))
    pad = 16 * SS
    st = Image.new("RGBA", (tw + 2 * pad, 52 * SS), (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    ds.rectangle([2 * SS, 2 * SS, st.width - 2 * SS, st.height - 2 * SS], outline=color + (255,), width=4 * SS)
    ds.rectangle([7 * SS, 7 * SS, st.width - 7 * SS, st.height - 7 * SS], outline=color + (160,), width=1 * SS)
    ds.text((st.width // 2, st.height // 2), s, font=f, fill=color + (255,), anchor="mm")
    sc = lerp(1.6, 1.0, k)
    st = st.resize((int(st.width * sc), int(st.height * sc)), Image.LANCZOS)
    st = st.rotate(angle, expand=True, resample=Image.BICUBIC)
    if k < 1:
        a = st.split()[3].point(lambda v: int(v * k)); st.putalpha(a)
    im.paste(st, (int(pos[0] * SS - st.width / 2), int(pos[1] * SS - st.height / 2)), st)

def tag(d, xy, s, color, font=None, anchor="mm", bg=CREAM):
    font = font or F("monob", 14)
    bb = d.textbbox(xy, s, font=font, anchor=anchor)
    d.rectangle([bb[0] - 6 * SS, bb[1] - 4 * SS, bb[2] + 6 * SS, bb[3] + 4 * SS], fill=bg)
    d.text(xy, s, font=font, fill=color, anchor=anchor)

# ---------- các cảnh ----------
N_SC = 9

def sc_hook(t, D):
    im, d = frame_base()
    cam = CAM_FULL
    cam = Cam(cam.cx, cam.cy + 25, cam.z * lerp(0.92, 0.96, t / D))
    draw_truck_back(d, cam); draw_truck_front(d, cam)
    k = seg(t, 0.1, 0.7)
    ctext(d, (W / 2, 128), "680 bao, 34 tấn:", F("serifb", 44), mix(CREAM, INK, k))
    k2 = seg(t, 0.5, 1.1)
    ctext(d, (W / 2, 184), "chất thế nào cho đúng?", F("serifb", 44), mix(CREAM, ORANGE, k2))
    chips = ["01 · MỘT LỚP", "02 · MỘT HÀNG", "03 · LÙI 75 CM"]
    f = F("monob", 16)
    x = W / 2 - 330
    for i, s in enumerate(chips):
        kk = seg(t, 1.5 + i * 0.45, 1.9 + i * 0.45)
        if kk <= 0: continue
        tw = d.textlength(s, font=f) / SS
        y = 590 + 10 * (1 - kk)
        d.rectangle([x * SS, (y - 18) * SS, (x + tw + 28) * SS, (y + 18) * SS], fill=mix(CREAM, INK, kk))
        d.text(((x + 14) * SS, y * SS), s, font=f, fill=CREAM, anchor="lm")
        x += tw + 28 + 26
    counter(d, 0)
    corners(d); footer(d, 1, N_SC)
    return im

def sc_map(t, D):
    im, d = frame_base()
    cam = cam_lerp(Cam(525, 55, 0.83), Cam(525, 45, 0.86), ss(t / D))
    draw_truck_back(d, cam); draw_truck_front(d, cam)
    P = cam.P
    fm = F("monob", 15)
    a = seg(t, 0.3, 1.0)
    if a > 0:
        dim_line(d, P(0, WD + 30, 0), P(L * a, WD + 30, 0), "dài 1.226 cm" if a > 0.6 else "", RED, fm)
    b = seg(t, 1.0, 1.6)
    if b > 0:
        dim_line(d, P(L + 25, 0, 0), P(L + 25, WD * b, 0), "rộng 235" if b > 0.6 else "", RED, fm, offset=(48, 0))
    c = seg(t, 1.4, 2.0)
    if c > 0:
        dim_line(d, P(0, 0, 0), P(0, 0, HROOF * c), "cao 215" if c > 0.6 else "", RED, fm, offset=(-50, 0))
    # nhãn đầu/cuối thùng
    e = seg(t, 2.0, 2.6)
    if e > 0:
        tag(d, P(0, WD / 2, HROOF + 22), "ĐẦU THÙNG (sát cabin)", mix(CREAM, INK, e))
        tag(d, P(L, WD / 2, HWALL + 40), "CUỐI THÙNG (cửa sau)", mix(CREAM, INK, e))
    g = seg(t, 2.6, 3.8)
    if g > 0:
        p0, p1 = P(60, WD / 2, 2), P(lerp(60, L - 60, g), WD / 2, 2)
        arrow(d, p0, p1, GREEN, 5, 18)
    # thẻ bao
    h = seg(t, 1.0, 1.6)
    if h > 0:
        bx, by = 80, 470
        cb = Cam(22.6 - (bx + 110 - W / 2) / 1.6, 8.3 - (by + 8 - H / 2) / 1.6, 1.6)
        d.rectangle([(bx - 30) * SS, (by - 60) * SS, (bx + 250) * SS, (by + 80) * SS], fill=mix(CREAM, (255, 255, 255), 0.5 * h), outline=mix(CREAM, INK, h), width=2 * SS)
        draw_bag(d, cb, (0, 0, 0, 75, 50, 13), 0, "n", h)
        ctext(d, (bx + 110, by - 38), "1 bao = 50 kg", F("serifb", 18), mix(CREAM, INK, h))
        ctext(d, (bx + 110, by + 58), "75 × 50 × 13 cm", F("mono", 15), mix(CREAM, INK, h))
    chapter(im, "TOÀN CẢNH", t)
    counter(d, 0)
    subtitle(d, "Chất từ trong ra ngoài: đầu thùng trước, cửa sau cuối", t)
    corners(d); footer(d, 2, N_SC)
    return im

def sc_layer_a(t, D):
    im, d = frame_base()
    cam = cam_lerp(Cam(200, 0, 1.2), CAM_HEAD, ss(t / 1.2))
    draw_truck_back(d, cam)
    Ts = [1.0 + i * 0.75 for i in range(5)]
    def vis(r, c, k):
        if r == 0 and k == 0:
            dz = drop(t, Ts[c])
            return None if dz is None else (dz, "g")
        return None
    draw_bags(d, cam, vis, w=BW0)
    draw_truck_front(d, cam)
    P = cam.P
    n = sum(1 for T in Ts if t >= T)
    # tên vách
    tag(d, P(0, WD / 2, 175), "VÁCH ĐẦU THÙNG", CREAM, F("monob", 15), bg=WALL_HEAD)
    # cảnh báo tràn
    k = seg(t, 4.6, 5.0)
    if k > 0:
        col = mix(CREAM, RED, k)
        dim_line(d, P(BL + 18, 0, 0), P(BL + 18, 250, 0), "5 × 50 = 250 cm", col, F("monob", 16), offset=(80, 6))
        tag(d, P(BL / 2, 250 + 6, 30), "lòng thùng chỉ 235 cm", col, F("monob", 15))
    chapter(im, "01 · MỘT LỚP", t)
    counter(d, n)
    subtitle(d, "Lớp 1: 5 bao nằm ngang, sát vách đầu thùng", t)
    corners(d); footer(d, 3, N_SC)
    return im

def sc_layer_b(t, D):
    im, d = frame_base()
    cam = CAM_HEAD
    draw_truck_back(d, cam)
    k = seg(t, 1.0, 3.0)
    w = lerp(BW0, BW, k)
    def vis(r, c, k_):
        if r == 0 and k_ == 0: return (0, "g")
        return None
    # khi đang ép: tính y theo w (sát vách xa)
    for c in range(COLS - 1, -1, -1):
        y1 = (COLS - c) * w; y0 = y1 - w
        # bao trái màn hình (c=0) nằm ở mép gần
    items = []
    for c in range(COLS):
        y1 = WD - c * w + (COLS * w - WD) if False else (COLS - c) * w
        items.append((c, (0, y1 - w, 0, BL, y1, BH)))
    for c, box in sorted(items, key=lambda it: it[1][1]):
        draw_bag(d, cam, box, 0, "g")
    draw_truck_front(d, cam)
    P = cam.P
    tag(d, P(0, WD / 2, 175), "VÁCH ĐẦU THÙNG", CREAM, F("monob", 15), bg=WALL_HEAD)
    total = COLS * w
    col = mix(RED, GREEN, k)
    lab = "5 × 50 = 250 cm" if k < 0.5 else "5 × 47 = 235 cm"
    dim_line(d, P(BL + 18, 0, 0), P(BL + 18, total, 0), lab, col, F("monob", 16), offset=(80, 6))
    if k > 0.95:
        # vạch 47 cm một bao
        dim_line(d, P(BL, WD - BW, BH + 4), P(BL, WD, BH + 4), "47", GREEN, F("monob", 14), offset=(-2, -16))
    if t > 3.4:
        stamp(im, "ÉP 50 → 47 CM", t - 3.4, RED, (930, 470))
    chapter(im, "01 · MỘT LỚP", t + 1)
    counter(d, 5)
    subtitle(d, "Mỗi bao phải ép còn khoảng 47 cm mới vừa", t)
    corners(d); footer(d, 4, N_SC)
    return im

def sc_row(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_HEAD, CAM_HEAD2, ss(t / 2.0))
    draw_truck_back(d, cam)
    def T(c, k): return 0.4 + (k - 1) * 0.85 + c * 0.13
    def vis(r, c, k):
        if r != 0: return None
        if k == 0: return (0, "g")
        dz = drop(t, T(c, k), 0.3)
        return None if dz is None else (dz, "g")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = 5 + sum(1 for k in range(1, 9) for c in range(5) if t >= T(c, k))
    fm = F("mono", 13)
    # nhãn lớp ở mép trái
    for k in range(LAYERS):
        if k == 0 or t >= T(0, k) + 0.3:
            x, y = P(0, WD, k * BH + BH / 2)
            d.text((x - 10 * SS, y), f"lớp {k + 1}", font=fm, fill=GREEN if k == 8 or t < T(0, k) + 1.2 else MUTED, anchor="rm")
    # thước đo cao
    k2 = seg(t, 8.0, 8.8)
    if k2 > 0:
        fx = BL + 22
        dim_line(d, P(fx, WD, 0), P(fx, WD, 117 * k2), "cao 117 cm" if k2 > 0.7 else "", mix(CREAM, RED, k2), F("monob", 15), offset=(62, 0))
    k3 = seg(t, 9.0, 9.6)
    if k3 > 0:
        c = mix(CREAM, INK, k3)
        d.line([P(-5, 0, HWALL), P(BL + 70, 0, HWALL)], fill=c, width=2 * SS)
        tag(d, P(BL + 110, 0, HWALL), "thành thùng 80 cm", c, F("mono", 14))
        tag(d, P(BL + 110, 0, HWALL + 37), "vượt thành 37 cm", mix(CREAM, RED, k3), F("monob", 14))
    if t > 10.4:
        stamp(im, "ĐẦY · 45 BAO", t - 10.4, GREEN, (940, 520))
    chapter(im, "02 · MỘT HÀNG", t)
    counter(d, n)
    subtitle(d, "Xếp đủ 9 lớp rồi mới sang hàng mới", t)
    corners(d); footer(d, 5, N_SC)
    return im

def sc_move(t, D):
    im, d = frame_base()
    # camera: đầu thùng → toàn cảnh
    cam = cam_lerp(Cam(150, -40, 1.6), CAM_FULL, seg(t, 5.0, 7.0))
    draw_truck_back(d, cam)
    T1 = lambda c, k: 1.8 + (k * 5 + c) * 0.07                # hàng 2
    def Trow(r): return 7.2 + (r - 2) * 0.5                    # hàng 3..15
    def Tb(r, c, k):
        if r == 0: return -1
        if r == 1: return T1(c, k)
        return Trow(r) + (k * 5 + c) * (0.42 / 45)
    cur = 1 if t < 7.2 else min(14, 2 + int((t - 7.2) / 0.5))
    def vis(r, c, k):
        if r >= ROWS: return None
        T = Tb(r, c, k)
        dz = drop(t, T, 0.25 if r == 1 else 0.12)
        if dz is None: return None
        style = "g" if r == cur and t < 13.8 else "n"
        return (dz, style)
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = sum(1 for r, c, k in all_slots() if r < ROWS and t >= Tb(r, c, k))
    # mũi tên lùi 75 cm
    a = seg(t, 0.3, 1.4)
    if a > 0 and t < 5.2:
        col = mix(CREAM, GREEN, a * (1 - seg(t, 4.6, 5.2)))
        arrow(d, P(BL + 5, WD + 18, 0), P(BL + 5 + 70 * a, WD + 18, 0), col, 4, 14)
        tag(d, P(BL + 40, WD + 45, 0), "lùi 75 cm", col, F("monob", 16))
    # nhãn hàng
    if t > 7.0:
        fm = F("mono", 12)
        for r in range(ROWS):
            if t >= Tb(r, 0, 0) or r < 2:
                tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), GREEN if (r == cur and t < 13.8) else INK, fm)
    if t > 7.0:
        tag(d, (W * SS / 2, 112 * SS), "VIDEO TUA NHANH >>", RED, F("monob", 15))
    chapter(im, "03 · LÙI 75 CM", t)
    counter(d, n)
    subtitle(d, "Lùi ra 75 cm, lặp lại cho đến hàng 15", t)
    corners(d); footer(d, 6, N_SC)
    return im

def full_rows(r, c, k):
    return (0, "n") if r < ROWS else None

def sc_extra(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_FULL, CAM_REAR, seg(t, 0.0, 1.4))
    draw_truck_back(d, cam)
    Ts = [1.4 + i * 0.4 for i in range(5)]
    def vis(r, c, k):
        if r < ROWS: return (0, "n")
        dz = drop(t, Ts[c])
        return None if dz is None else (dz, "o")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = 675 + sum(1 for T in Ts if t >= T)
    k = seg(t, 3.4, 4.0)
    if k > 0:
        col = mix(CREAM, RED, k)
        dim_line(d, P(ROWS * BL, 0, 117 + 12), P(L, 0, 117 + 12), "trống 101 cm", col, F("monob", 15), offset=(0, -18))
        tag(d, P(ROWS * BL - BL / 2, WD, 117 + 22), "hàng 15 · 9 lớp", mix(CREAM, INK, k), F("monob", 14))
    k2 = seg(t, 2.6, 3.2)
    if k2 > 0:
        tag(d, P(ROWS * BL + BL / 2, WD + 34, 0), "hàng 16 · 5 bao dư · 1 lớp", mix(CREAM, ORANGE, k2), F("monob", 15))
    if t > 4.3:
        stamp(im, "5 BAO DƯ · 1 LỚP", t - 4.3, ORANGE, (1000, 200), -5)
    chapter(im, "HÀNG 16 · BAO DƯ", t, ORANGE)
    counter(d, n)
    subtitle(d, "5 bao còn lại không đủ hàng: xếp 1 lớp ở hàng 16", t)
    corners(d); footer(d, 7, N_SC)
    return im

def sc_stats(t, D):
    im, d = frame_base()
    tiles = [(64, 120), (664, 120), (64, 370), (664, 370)]
    tw, th = 552, 230
    starts = [0.2, 2.4, 4.6, 6.8]
    for i, ((x, y), t0) in enumerate(zip(tiles, starts)):
        k = seg(t, t0, t0 + 0.4)
        if k <= 0: continue
        tt = t - t0
        d.rectangle([x * SS, (y + 10 * (1 - k)) * SS, (x + tw) * SS, (y + th + 10 * (1 - k)) * SS],
                    fill=mix(CREAM, (250, 246, 236), k), outline=mix(CREAM, INK, k), width=2 * SS)
        c = mix(CREAM, INK, k)
        if i == 0:
            ctext(d, (x + 150, y + 70), "680 bao", F("serifb", 40), c)
            ctext(d, (x + 150, y + 120), "= 34 tấn", F("serifb", 30), mix(CREAM, ORANGE, k))
            ctext(d, (x + 150, y + 175), "20 bao = 1 tấn", F("mono", 14), mix(CREAM, MUTED, k))
            # lưới 34 cột × 20 bao đầy dần
            nfill = int(680 * seg(tt, 0.3, 1.9))
            gx, gy, cw, ch = x + 300, y + 30, 6.5, 8.5
            for j in range(680):
                col_, row_ = j // 20, j % 20
                px, py = gx + col_ * cw, gy + (19 - row_) * ch
                fill = (GREEN if col_ < 34 and j < 675 else ORANGE) if j < nfill else mix(CREAM, INK, 0.1)
                d.rectangle([px * SS, py * SS, (px + cw - 1.5) * SS, (py + ch - 1.5) * SS], fill=fill)
        if i == 1:
            ctext(d, (x + 150, y + 80), "15 hàng", F("serifb", 40), c)
            ctext(d, (x + 150, y + 130), "× 45 bao", F("serifb", 30), c)
            ctext(d, (x + 150, y + 178), "+ 5 bao ở hàng 16", F("mono", 14), mix(CREAM, ORANGE, k))
            bx, by = x + 300, y + 190
            for r in range(16):
                hmax = 9 if r < 15 else 1
                hh = hmax * seg(tt, 0.3 + r * 0.09, 0.6 + r * 0.09)
                col = GREEN if r < 15 else ORANGE
                d.rectangle([(bx + r * 14.5) * SS, (by - hh * 16) * SS, (bx + r * 14.5 + 11) * SS, by * SS], fill=col)
            d.line([bx * SS, (by + 1) * SS, (bx + 232) * SS, (by + 1) * SS], fill=INK, width=2 * SS)
        if i == 2:
            ctext(d, (x + 150, y + 80), "cao 117 cm", F("serifb", 36), c)
            ctext(d, (x + 150, y + 130), "9 lớp × 13 cm", F("mono", 16), c)
            ctext(d, (x + 150, y + 165), "vượt thành 80 cm: 37 cm", F("mono", 14), mix(CREAM, RED, k))
            bx, by = x + 330, y + 205
            nl = int(9 * seg(tt, 0.3, 1.6) + 0.999) if tt > 0.3 else 0
            sc_ = 1.45
            for l in range(nl):
                d.rounded_rectangle([bx * SS, (by - (l + 1) * 13 * sc_ + 1.5) * SS, (bx + 150) * SS, (by - l * 13 * sc_) * SS], radius=5 * SS, fill=BAG_TOP, outline=GREEN, width=SS)
            wy = by - 80 * sc_
            d.line([(bx - 20) * SS, wy * SS, (bx + 175) * SS, wy * SS], fill=INK, width=2 * SS)
            d.text(((bx + 178) * SS, wy * SS), "80", font=F("mono", 13), fill=INK, anchor="lm")
            if nl == 9:
                d.text(((bx + 178) * SS, (by - 117 * sc_) * SS), "117", font=F("monob", 13), fill=RED, anchor="lm")
        if i == 3:
            ctext(d, (x + 150, y + 80), "trống 101 cm", F("serifb", 34), c)
            ctext(d, (x + 150, y + 130), "sau hàng 15", F("mono", 16), c)
            ctext(d, (x + 150, y + 165), "1.226 − 15 × 75 = 101", F("mono", 14), mix(CREAM, MUTED, k))
            bx, by, bw = x + 300, y + 110, 225
            d.rectangle([bx * SS, by * SS, (bx + bw) * SS, (by + 34) * SS], outline=INK, width=2 * SS)
            f15 = seg(tt, 0.3, 1.3)
            d.rectangle([bx * SS, by * SS, (bx + bw * 1125 / 1226 * f15) * SS, (by + 34) * SS], fill=GREEN)
            if f15 >= 1:
                gx0 = bx + bw * 1125 / 1226
                d.rectangle([gx0 * SS, (by + 20) * SS, (gx0 + bw * 75 / 1226) * SS, (by + 34) * SS], fill=ORANGE)
                dim_line(d, (gx0 * SS, (by - 18) * SS), ((bx + bw) * SS, (by - 18) * SS), "", RED, F("mono", 12))
                d.text(((bx + bw) * SS, (by + 52) * SS), "cửa sau", font=F("mono", 12), fill=MUTED, anchor="rm")
                d.text((bx * SS, (by + 52) * SS), "đầu thùng", font=F("mono", 12), fill=MUTED, anchor="lm")
    chapter(im, "SỐ LIỆU", t)
    subtitle(d, "Bốn con số của một xe 34 tấn", t, y=648)
    corners(d); footer(d, 8, N_SC)
    return im

def sc_end(t, D):
    im, d = frame_base(ORANGE)
    # khung kem chứa xe đầy (gọi lại hình mở đầu)
    k = seg(t, 0.0, 0.5)
    px0, py0, px1, py1 = 140, 280, 1140, 590
    d.rectangle([px0 * SS, py0 * SS, px1 * SS, py1 * SS], fill=CREAM, outline=INK, width=3 * SS)
    cam = Cam(525, 40, 0.68)
    def P2(x, y, z, _P=cam.P):
        u, v = _P(x, y, z); return (u, v + 80 * SS)
    cam.P = P2
    draw_truck_back(d, cam)
    def vis(r, c, k_): return (0, "o") if r == ROWS else (0, "n")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    steps = ["5 bao ngang", "9 lớp", "lùi 75 cm"]
    f = F("serifb", 40)
    widths = [d.textlength(s, font=f) / SS for s in steps]
    gap = 70
    total = sum(widths) + gap * 2
    x = W / 2 - total / 2
    for i, s in enumerate(steps):
        kk = seg(t, 0.3 + i * 0.5, 0.7 + i * 0.5)
        ctext(d, (x, 130), s, f, mix(ORANGE, INK, kk), anchor="lm")
        x += widths[i]
        if i < 2:
            ka = seg(t, 0.6 + i * 0.5, 0.9 + i * 0.5)
            if ka > 0:
                arrow(d, ((x + 12) * SS, 130 * SS), ((x + 12 + (gap - 24) * ka) * SS, 130 * SS), CREAM, 4, 14)
        x += gap
    kk = seg(t, 2.0, 2.5)
    ctext(d, (W / 2, 200), "Xong 1 hàng (45 bao) mới lùi ra · 5 bao dư xếp 1 lớp ở hàng 16", F("serif", 22), mix(ORANGE, INK, kk))
    ctext(d, (W / 2, 245), "Làm đúng trình tự này cho mọi xe 34 tấn", F("serifb", 24), mix(ORANGE, CREAM, kk))
    ctext(d, (W / 2, 640), "Nguồn: Trình tự chất bao xe 34T v2 (KCP) · thùng 1.226 × 235 × 215 cm · bao 75 × 50 × 13 cm, 50 kg",
          F("mono", 13), mix(ORANGE, INK, seg(t, 2.5, 3.0)))
    corners(d, INK); footer(d, 9, N_SC, INK)
    return im

SCENES = [("hook", 4.0, sc_hook), ("map", 5.0, sc_map), ("layer_a", 6.0, sc_layer_a),
          ("layer_b", 6.5, sc_layer_b), ("row", 12.5, sc_row), ("move", 15.0, sc_move),
          ("extra", 6.5, sc_extra), ("stats", 10.0, sc_stats), ("end", 6.5, sc_end)]
XF = 8  # số khung trộn chuyển cảnh

def render(i_frame):
    """trả bytes RGB cho khung toàn cục i"""
    t_abs = i_frame / FPS
    acc = 0.0
    for si, (name, D, fn) in enumerate(SCENES):
        if t_abs < acc + D or si == len(SCENES) - 1:
            t = t_abs - acc
            im = fn(t, D)
            # trộn với cuối cảnh trước
            fi = int(round(t * FPS))
            if si > 0 and fi < XF:
                pn, pD, pfn = SCENES[si - 1]
                prev = pfn(pD + t, pD)
                im = Image.blend(prev, im, (fi + 1) / (XF + 1))
            return im.resize((W, H), Image.LANCZOS).tobytes()
        acc += D

def total_frames(): return int(round(sum(s[1] for s in SCENES) * FPS))

def test_sheet(path="test_sheet.png"):
    picks = []
    acc = 0
    for name, D, fn in SCENES:
        for f in (0.15, 0.5, 0.97):
            picks.append(int((acc + D * f) * FPS))
        acc += D
    tiles = [Image.frombytes("RGB", (W, H), render(i)).resize((640, 360), Image.LANCZOS) for i in picks]
    cols = 3; rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (640 * cols, 360 * rows), "white")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(path)
    print("saved", path)

def single(t, path):
    Image.frombytes("RGB", (W, H), render(int(t * FPS))).save(path)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "test":
        test_sheet(sys.argv[2] if len(sys.argv) > 2 else "test_sheet.png")
    elif mode == "frame":
        single(float(sys.argv[2]), sys.argv[3])
    else:
        n = total_frames()
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, b in enumerate(pool.imap(render, range(n), chunksize=8)):
                p.stdin.write(b)
                if i % 100 == 0: print(f"{i}/{n}", flush=True)
        p.stdin.close(); p.wait()
        print("done", OUT, flush=True)
