# -*- coding: utf-8 -*-
"""Video: Trình tự chất 680 bao đường vào xe container bạt 34 tấn (từ trong ra ngoài).
Bản kho PC: 8 hàng × 45 bao (9 lớp) + 8 hàng × 40 bao (8 lớp); mỗi lớp đặt bao 1, 3, 5 trước rồi 2, 4.
Nguồn số liệu: Trinh_tu_chat_bao_xe_34T_v2.pdf
Chạy:  python3 make_video.py            -> render đầy đủ
       python3 make_video.py test       -> contact sheet khung mẫu
"""
import sys, math, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 1280, 720, 2, 25
OUT = sys.argv[2] if len(sys.argv) > 2 else "Chat_xa_34T_kho_PC_v1.mp4"

# ---------- màu ----------
CREAM = (243, 236, 220); INK = (29, 43, 58); ORANGE = (217, 119, 75)
GREEN = (38, 122, 64); RED = (178, 52, 44); MUTED = (110, 116, 120)
BAG_TOP = (252, 250, 244); BAG_FRONT = (220, 214, 200); BAG_END = (236, 231, 219)
FLOOR_C = (160, 168, 172); FLOOR_EDGE = (44, 62, 80)
WALL_FAR = (112, 138, 160); WALL_HEAD = (88, 114, 140)

# ---------- số liệu (PDF) ----------
L, WD, HROOF, HWALL = 1226, 235, 215, 80     # thùng: dài, rộng, cao mui, cao thành (cm)
BL, BW0, BW, BH = 75, 50, 47, 13             # bao: dài 75, rộng 50 (ép còn 47), dày 13
COLS, LAYERS = 5, 9
FULL = 8             # hàng 1-8: 9 lớp = 45 bao
LAST_L = 8           # hàng 9-16: 8 lớp = 40 bao
ROWS = 16
def NL(r): return LAYERS if r < FULL else LAST_L
TOTAL = sum(COLS * NL(r) for r in range(ROWS))
assert TOTAL == 680 and TOTAL * 50 == 34000
assert FULL * 45 == 360 and (ROWS - FULL) * COLS * LAST_L == 320 and LAST_L * 13 == 104
ORDER = [0, 2, 4, 1, 3]          # mỗi lớp: bao 1, 3, 5 trước; 2, 4 sau (c=0 là bao 1, bên trái)
OP = {c: i for i, c in enumerate(ORDER)}
GAP = ((WD - BW0) / 2 - BW0)     # khe còn lại sau khi đặt 1, 3, 5 (rộng 50)
assert abs(GAP - 42.5) < 1e-9
assert COLS * BW == WD and COLS * BW0 == 250
assert LAYERS * BH == 117 and 117 - HWALL == 37
assert L - ROWS * BL == 26

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
    return (r * 45 if r < FULL else 360 + (r - FULL) * 40) + k * 5 + OP[c]

def all_slots():
    for r in range(ROWS):
        for k in range(NL(r)):
            for c in range(COLS):
                yield r, c, k

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
    d.text((66 * SS, 692 * SS), "KCP VIỆT NAM · LOGISTICS · CHẤT BAO XE CONTAINER BẠT 34 TẤN · KHO PC", font=f, fill=color, anchor="ls")
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
N_SC = 11

def sc_hook(t, D):
    im, d = frame_base()
    cam = CAM_FULL
    cam = Cam(cam.cx, cam.cy + 25, cam.z * lerp(0.92, 0.96, t / D))
    draw_truck_back(d, cam); draw_truck_front(d, cam)
    k = seg(t, 0.1, 0.7)
    ctext(d, (W / 2, 128), "680 bao, 34 tấn", F("serifb", 44), mix(CREAM, INK, k))
    k2 = seg(t, 0.5, 1.1)
    ctext(d, (W / 2, 184), "chất vào xe container bạt", F("serifb", 44), mix(CREAM, ORANGE, k2))
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

def draw_bag2d(d, x, y, w, h, outline=GREEN, fill=BAG_TOP, lw=2):
    """bao nhìn mặt cắt: hình chữ nhật bo góc, (x,y) là góc dưới trái, đơn vị px 1x"""
    d.rounded_rectangle([x * SS, (y - h) * SS, (x + w) * SS, y * SS], radius=int(min(h, w) * 0.35 * SS),
                        fill=fill, outline=outline, width=lw * SS)
    if w > 40:
        cy = y - h / 2
        for a, b in ((0.3, 0.42), (0.58, 0.7)):
            d.line([(x + w * a) * SS, cy * SS, (x + w * b) * SS, cy * SS], fill=(214, 120, 90), width=2 * SS)

def sc_bag(t, D):
    """giới thiệu 1 bao đường 50 kg, nhấn bề ngang 0,5 m"""
    im, d = frame_base()
    z = lerp(3.0, 3.3, t / D)
    cam = Cam(22.6 - (430 - W / 2) / z, 8.3 - (370 - H / 2) / z, z)
    dz = drop(t, 0.3, 0.5)
    if dz is not None:
        draw_bag(d, cam, (0, 0, 0, BL, BW0, BH), dz, "n")
    P = cam.P
    k1 = seg(t, 1.2, 1.7)
    if k1 > 0:
        dim_line(d, P(-6, BW0 + 6, 0), P(BL - 6, BW0 + 6, 0), "dài 75 cm", mix(CREAM, INK, k1), F("monob", 16), offset=(-10, 22))
        dim_line(d, P(BL + 8, 0, 0), P(BL + 8, BW0, 0), "", mix(CREAM, INK, k1), F("monob", 16))
        dim_line(d, P(-8, BW0, 0), P(-8, BW0, BH), "", mix(CREAM, INK, k1), F("monob", 16))
        tag(d, P(-8, BW0 + 22, BH / 2), "dày 13", mix(CREAM, INK, k1), F("monob", 15))
    k2 = seg(t, 2.2, 2.7)
    if k2 > 0:
        pulse = 1 + 0.08 * math.sin(max(0, t - 2.7) * 5) * (t > 2.7)
        x, y = P(BL + 8, BW0 / 2, 0)
        tag(d, (x + 95 * SS, y + 10 * SS), "ngang 0,5 m", mix(CREAM, RED, k2), F("monob", int(26 * pulse)))
    k3 = seg(t, 0.8, 1.4)
    ctext(d, (930, 250), "Bao đường", F("serifb", 40), mix(CREAM, INK, k3))
    ctext(d, (930, 305), "50 kg", F("serifb", 56), mix(CREAM, ORANGE, k3))
    k4 = seg(t, 2.8, 3.4)
    ctext(d, (930, 380), "dài 0,75 m · ngang 0,5 m", F("mono", 20), mix(CREAM, INK, k4))
    ctext(d, (930, 412), "dày 13 cm", F("mono", 20), mix(CREAM, INK, k4))
    chapter(im, "BAO ĐƯỜNG", t)
    counter(d, 0)
    subtitle(d, "Mỗi bao đường 50 kg rộng 0,5 m", t)
    corners(d); footer(d, 3, N_SC)
    return im

SEC_S = 3.4          # px / cm trên mặt cắt
SEC_X0 = 640 - WD * SEC_S / 2
SEC_Y = 470          # mặt sàn

def badge(d, cx, cy, s, col, r=15):
    d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=col)
    d.text((cx * SS, cy * SS), s, font=F("serifb", 17), fill=CREAM, anchor="mm")

def phase_text(d, s, t, a, b, col, size=34, y=150):
    k = seg(t, a, a + 0.4) * (1 - seg(t, b - 0.3, b))
    if k > 0:
        ctext(d, (640, y), s, F("serifb", size), mix(CREAM, col, k))

def sc_section(t, D):
    """mặt cắt ngang thùng: đặt bao 1, 3, 5 trước, ép 2, 4 vào khe 42,5 cm"""
    im, d = frame_base()
    s_ = SEC_S; x0 = SEC_X0; fy = SEC_Y
    wall = 16
    hw = HWALL * s_
    d.rectangle([(x0 - wall) * SS, (fy - hw) * SS, x0 * SS, (fy + 14) * SS], fill=WALL_FAR)
    d.rectangle([(x0 + WD * s_) * SS, (fy - hw) * SS, (x0 + WD * s_ + wall) * SS, (fy + 14) * SS], fill=WALL_FAR)
    d.rectangle([(x0 - wall) * SS, fy * SS, (x0 + WD * s_ + wall) * SS, (fy + 14) * SS], fill=FLOOR_EDGE)
    tag(d, ((x0 - wall - 10) * SS, (fy - hw / 2) * SS), "thành", MUTED, F("mono", 14), anchor="rm")
    k0 = seg(t, 0.4, 1.2)
    if k0 > 0:
        dim_line(d, (x0 * SS, (fy + 48) * SS), ((x0 + WD * s_ * k0) * SS, (fy + 48) * SS),
                 "lòng thùng rộng 2,35 m" if k0 > 0.8 else "", mix(CREAM, INK, k0), F("monob", 20))
    P1 = {0: 0.0, 2: (WD - BW0) / 2, 4: WD - BW0}           # vị trí bao 1, 3, 5 (rộng 50)
    GAPS = {1: (BW0, BW0 + GAP), 3: (WD - BW0 - GAP, WD - BW0)}
    T = {0: 1.6, 2: 2.5, 4: 3.4, 1: 5.8, 3: 7.0}
    kq = seg(t, 8.6, 9.8)          # cả 5 bao về đều 47 cm
    n = 0
    for c in ORDER:
        if t < T[c]: continue
        n += 1
        if c in P1:
            x, w = P1[c], BW0
            e = ss((t - T[c]) / 0.4)
        else:
            g0, g1 = GAPS[c]
            e = ss((t - T[c]) / 0.9)
            w = lerp(BW0, GAP, ss((t - T[c] - 0.2) / 0.7))
            x = g0 + (GAP - w) / 2
        x = lerp(x, c * BW, kq); w = lerp(w, BW, kq)
        y = fy - 150 * (1 - e)
        col = GREEN if c in P1 else ORANGE
        draw_bag2d(d, x0 + x * s_, y, w * s_, BH * s_, col, BAG_TOP if c in P1 else (255, 238, 222))
        badge(d, x0 + (x + w / 2) * s_, y - BH * s_ - 24, str(c + 1), col)
    # khe trống
    kg = seg(t, 4.0, 4.5) * (1 - seg(t, 5.6, 6.0))
    if kg > 0:
        col = mix(CREAM, RED, kg)
        for c, (g0, g1) in GAPS.items():
            dim_line(d, ((x0 + g0 * s_) * SS, (fy - 22) * SS), ((x0 + g1 * s_) * SS, (fy - 22) * SS), "", col, F("mono", 12))
            ctext(d, (x0 + (g0 + g1) / 2 * s_, fy - 60), "khe 42,5", F("monob", 16), col)
    # mũi tên chỉ bao 2, 4 ép xuống
    for c in (1, 3):
        ka = seg(t, T[c] - 0.6, T[c] - 0.2) * (1 - seg(t, T[c] + 0.6, T[c] + 0.9))
        if ka > 0:
            g0, g1 = GAPS[c]; cx = x0 + (g0 + g1) / 2 * s_
            arrow(d, (cx * SS, (fy - 250) * SS), (cx * SS, (fy - 190) * SS), mix(CREAM, ORANGE, ka), 4, 14)
    phase_text(d, "Bước 1: đặt bao 1 · 3 · 5 trước", t, 1.2, 4.0, GREEN)
    phase_text(d, "Còn 2 khe 42,5 cm, mà bao rộng 50 cm", t, 4.0, 5.6, RED)
    phase_text(d, "Bước 2: ép bao 2 · 4 vào khe giữa", t, 5.6, 8.6, ORANGE)
    phase_text(d, "5 × 47 = 2,35 m: vừa khít lòng thùng", t, 8.8, D + 1, GREEN, 32)
    if t > 10.2:
        stamp(im, "1·3·5 TRƯỚC → 2·4 SAU", t - 10.2, RED, (1050, 290))
    ctext(d, (640, 100), "MẶT CẮT NGANG THÙNG · nhìn từ cửa sau", F("mono", 15), MUTED)
    chapter(im, "01 · MỘT LỚP", t)
    counter(d, n if t < D else 5)
    subtitle(d, "Đặt bao 1, 3, 5 trước, sau đó ép bao 2, 4 vào khe", t)
    corners(d); footer(d, 4, N_SC)
    return im


def vn_m(v):
    return f"{v:.1f}".replace(".", ",")

def sc_layer_a(t, D):
    """lớp 1 trong thùng 3D (đã ép 47 cm), sát vách đầu thùng"""
    im, d = frame_base()
    cam = cam_lerp(Cam(200, 0, 1.2), CAM_HEAD, ss(t / 1.2))
    draw_truck_back(d, cam)
    Ts = {c: 1.0 + OP[c] * 0.55 + (0.3 if OP[c] >= 3 else 0) for c in range(5)}
    def vis(r, c, k):
        if r == 0 and k == 0:
            dz = drop(t, Ts[c])
            return None if dz is None else (dz, "g" if c in (0, 2, 4) else "o")
        return None
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    tag(d, P(0, WD / 2, 175), "VÁCH ĐẦU THÙNG", CREAM, F("monob", 15), bg=WALL_HEAD)
    for c in range(5):
        if t >= Ts[c] + 0.35:
            b = bag_box(0, c, 0)
            x, y = P(BL / 2, (b[1] + b[4]) / 2, BH + 2)
            badge(d, x / SS, y / SS, str(c + 1), GREEN if c in (0, 2, 4) else ORANGE, 13)
    k = seg(t, 3.8, 4.3)
    if k > 0:
        dim_line(d, P(BL + 18, 0, 0), P(BL + 18, WD, 0), "5 × 47 = 2,35 m", mix(CREAM, GREEN, k), F("monob", 16), offset=(80, 6))
    chapter(im, "01 · MỘT LỚP", t)
    counter(d, 5)
    subtitle(d, "Lớp 1 sát vách đầu thùng: bao 1, 3, 5 trước, rồi 2, 4", t)
    corners(d); footer(d, 5, N_SC)
    return im

def sc_row(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_HEAD, CAM_HEAD2, seg(t, 3.5, 6.0))
    draw_truck_back(d, cam)
    def T(c, k):
        o = OP[c]
        if k == 1: return 0.8 + o * 0.55          # lớp 2: từng bao, 1-3-5 rồi 2-4
        if k == 2: return 4.0 + o * 0.4           # lớp 3
        return 6.6 + (k - 3) * 0.7 + o * 0.1     # lớp 4-9
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
        if k == 0 or t >= T(ORDER[0], k) + 0.3:
            x, y = P(0, WD, k * BH + BH / 2)
            d.text((x - 10 * SS, y), f"lớp {k + 1}", font=fm, fill=GREEN if k == 8 or t < T(ORDER[0], k) + 1.2 else MUTED, anchor="rm")
    # thước đo cao
    # nhãn lớp đang xếp
    for kk, (a, b) in enumerate([(0.6, 3.6), (3.8, 6.2)], start=1):
        e = seg(t, a, a + 0.3) * (1 - seg(t, b, b + 0.3))
        if e > 0:
            ctext(d, (930, 250), f"LỚP {kk + 1}", F("serifb", 52), mix(CREAM, GREEN, e))
            ctext(d, (930, 300), f"bao {kk * 5 + 1}–{kk * 5 + 5} · cùng hướng lớp 1", F("mono", 18), mix(CREAM, INK, e))
            ctext(d, (930, 335), "thứ tự: 1 · 3 · 5 → 2 · 4", F("monob", 18), mix(CREAM, ORANGE, e))
    e = seg(t, 6.4, 6.7) * (1 - seg(t, 10.6, 11.0))
    if e > 0:
        kcur = min(9, max(4, 3 + sum(1 for k in range(3, 9) if t >= T(ORDER[0], k))))
        ctext(d, (930, 250), f"LỚP 4 → {kcur}", F("serifb", 52), mix(CREAM, GREEN, e))
    k2 = seg(t, 11.0, 11.8)
    if k2 > 0:
        fx = BL + 22
        dim_line(d, P(fx, WD, 0), P(fx, WD, 117 * k2), "cao 117 cm" if k2 > 0.7 else "", mix(CREAM, RED, k2), F("monob", 15), offset=(62, 0))
    k3 = seg(t, 12.0, 12.6)
    if k3 > 0:
        c = mix(CREAM, INK, k3)
        d.line([P(-5, 0, HWALL), P(BL + 70, 0, HWALL)], fill=c, width=2 * SS)
        tag(d, P(BL + 110, 0, HWALL), "thành thùng 80 cm", c, F("mono", 14))
        tag(d, P(BL + 110, 0, HWALL + 37), "vượt thành 37 cm", mix(CREAM, RED, k3), F("monob", 14))
    if t > 13.4:
        stamp(im, "ĐẦY · 45 BAO", t - 13.4, GREEN, (940, 520))
    chapter(im, "02 · MỘT HÀNG", t)
    counter(d, n)
    subtitle(d, "Lớp nào cũng 1, 3, 5 trước rồi 2, 4; đủ 9 lớp mới sang hàng mới", t)
    corners(d); footer(d, 6, N_SC)
    return im

def sc_move(t, D):
    im, d = frame_base()
    # camera: đầu thùng → toàn cảnh
    cam = cam_lerp(Cam(150, -40, 1.6), CAM_FULL, seg(t, 5.0, 7.0))
    draw_truck_back(d, cam)
    T1 = lambda c, k: 1.8 + (k * 5 + OP[c]) * 0.07            # hàng 2
    def Trow(r): return 7.2 + (r - 2) * 0.6                    # hàng 3..8
    def Tb(r, c, k):
        if r == 0: return -1
        if r == 1: return T1(c, k)
        return Trow(r) + (k * 5 + OP[c]) * (0.5 / 45)
    cur = 1 if t < 7.2 else min(FULL - 1, 2 + int((t - 7.2) / 0.6))
    def vis(r, c, k):
        if r >= FULL: return None
        T = Tb(r, c, k)
        dz = drop(t, T, 0.25 if r == 1 else 0.12)
        if dz is None: return None
        style = "g" if r == cur and t < 11.0 else "n"
        return (dz, style)
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = sum(1 for r, c, k in all_slots() if r < FULL and t >= Tb(r, c, k))
    # mũi tên lùi 75 cm
    a = seg(t, 0.3, 1.4)
    if a > 0 and t < 5.2:
        col = mix(CREAM, GREEN, a * (1 - seg(t, 4.6, 5.2)))
        arrow(d, P(BL + 5, WD + 18, 0), P(BL + 5 + 70 * a, WD + 18, 0), col, 4, 14)
        tag(d, P(BL + 40, WD + 45, 0), "lùi 75 cm", col, F("monob", 16))
    # nhãn hàng
    if t > 7.0:
        fm = F("mono", 12)
        for r in range(FULL):
            if t >= Tb(r, 0, 0) or r < 2:
                tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), GREEN if (r == cur and t < 11.0) else INK, fm)
    if t > 7.0:
        tag(d, (W * SS / 2, 112 * SS), "VIDEO TUA NHANH >>", RED, F("monob", 15))
    chapter(im, "03 · LÙI 75 CM", t)
    counter(d, n)
    subtitle(d, "Lùi ra 75 cm, lặp lại 9 lớp cho đến hàng 8", t)
    corners(d); footer(d, 7, N_SC)
    return im

def full_rows(r, c, k):
    return (0, "n") if r < FULL else None


def sc_extra(t, D):
    """hàng 9-16: mỗi hàng 5 bao × 8 lớp = 40 bao"""
    im, d = frame_base()
    xf = FULL * BL + BL / 2
    cam_r9 = Cam(0.95 * xf - 0.5 * 150 + 60, 0.18 * xf + 0.32 * 150 - 0.9 * 60 + 10, 1.5)
    cam = cam_lerp(cam_lerp(CAM_FULL, cam_r9, seg(t, 0.0, 1.2)), CAM_FULL, seg(t, 5.4, 6.8))
    draw_truck_back(d, cam)
    def Tb(r, c, k):
        if r == FULL: return 1.4 + (k * 5 + OP[c]) * 0.09
        return 6.0 + (r - FULL - 1) * 0.55 + (k * 5 + OP[c]) * (0.45 / 40)
    cur = FULL if t < 6.0 else min(ROWS - 1, FULL + 1 + int((t - 6.0) / 0.55))
    def vis(r, c, k):
        if r < FULL: return (0, "n")
        dz = drop(t, Tb(r, c, k), 0.2 if r == FULL else 0.12)
        if dz is None: return None
        return (dz, "g" if (r == cur and t < 10.2) else "o")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = 360 + sum(1 for r, c, k in all_slots() if r >= FULL and t >= Tb(r, c, k))
    fm = F("monob", 15)
    e = seg(t, 1.0, 1.4) * (1 - seg(t, 5.2, 5.6))
    if e > 0:
        ctext(d, (1000, 150), "HÀNG 9 → 16", F("serifb", 44), mix(CREAM, ORANGE, e))
        ctext(d, (1000, 200), "5 bao × 8 lớp = 40 bao", F("mono", 20), mix(CREAM, INK, e))
        ctext(d, (1000, 232), "thứ tự: 1 · 3 · 5 → 2 · 4", F("monob", 18), mix(CREAM, ORANGE, e))
    k1 = seg(t, 4.6, 5.0) * (1 - seg(t, 5.4, 5.8))
    if k1 > 0:
        fx = FULL * BL + BL + 14
        dim_line(d, P(fx, WD, 0), P(fx, WD, 104), "cao 104 cm", mix(CREAM, RED, k1), fm, offset=(62, 0))
        tag(d, P(FULL * BL - BL / 2, 0, 117 + 26), "hàng 8 · 9 lớp · 117 cm", mix(CREAM, INK, k1), F("monob", 14))
    if t > 5.8:
        tag(d, (W * SS / 2, 112 * SS), "VIDEO TUA NHANH >>", RED, F("monob", 15))
    if t > 6.8:
        f12 = F("mono", 12)
        for r in range(ROWS):
            if r < FULL + 1 or t >= Tb(r, ORDER[0], 0):
                tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), ORANGE if r >= FULL else INK, f12)
    k2 = seg(t, 9.8, 10.3)
    if k2 > 0:
        d.line([P(ROWS * BL, WD / 2, 0), P(L, WD / 2, 0)], fill=mix(CREAM, INK, k2), width=3 * SS)
        tag(d, P(L + 25, WD / 2, 0), "trống 26 cm", mix(CREAM, INK, k2), F("monob", 14), anchor="lm")
    if t > 10.4:
        stamp(im, "8 HÀNG × 40 BAO", t - 10.4, ORANGE, (1000, 200), -5)
    chapter(im, "04 · HÀNG 9–16 · 8 LỚP", t, ORANGE)
    counter(d, n)
    subtitle(d, "Hàng 9 đến 16: mỗi hàng 5 bao × 8 lớp = 40 bao", t)
    corners(d); footer(d, 8, N_SC)
    return im


TOUR_STEP = 0.72
def sc_tour(t, D):
    """máy quay đi từ đầu xe tới cuối xe, đếm từng hàng"""
    im, d = frame_base()
    t0 = 1.2
    rf = clamp((t - t0) / TOUR_STEP, -0.4, ROWS - 1)          # vị trí hàng (số thực)
    base = math.floor(rf); frac = rf - base
    pos = base + ss(clamp(frac / 0.6))                      # đi 60% thời gian, dừng 40%
    pos = clamp(pos, 0, ROWS - 1)
    xf = pos * BL + BL / 2
    z = 1.55 * (1 - seg(t, D - 1.6, D - 0.2)) + 0.86 * seg(t, D - 1.6, D - 0.2)
    zoom_in = seg(t, 0.0, 1.0)
    cam_t = Cam(0.95 * xf - 0.5 * 150 + 120, 0.18 * xf + 0.32 * 150 - 0.9 * 60 + 20, 1.55)
    cam = cam_lerp(CAM_FULL, cam_t, zoom_in)
    cam = cam_lerp(cam, CAM_FULL, seg(t, D - 1.6, D - 0.2))
    cur = int(round(pos)) if t >= t0 - 0.2 else -1
    cur = min(cur, ROWS - 1)
    draw_truck_back(d, cam)
    def vis(r, c, k):
        if r == cur: return (0, "g")
        return (0, "o" if r >= FULL else "n")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    # số hàng đã đi qua ghi dọc mép sàn gần
    fm = F("monob", 14)
    for r in range(cur + 1 if cur >= 0 else 0):
        tag(d, P(r * BL + BL / 2, WD + 24, 0), str(r + 1), GREEN if r == cur else INK, fm)
    if 0 <= cur < ROWS:
        x0 = cur * BL; hh = NL(cur) * BH
        # 5 bao ngang (trên mặt hàng) và số lớp (cạnh gần)
        dim_line(d, P(x0 + BL / 2, 0, hh + 6), P(x0 + BL / 2, WD, hh + 6), "5 bao", GREEN, F("monob", 15), offset=(0, -16))
        dim_line(d, P(x0, WD + 10, 0), P(x0, WD + 10, hh), f"{NL(cur)} lớp", GREEN, F("monob", 15), offset=(-42, 0))
    # bảng đếm
    done_rows = cur + 1 if cur >= 0 else 0
    cum = sum(COLS * NL(r) for r in range(done_rows))
    since = (t - t0) - max(cur, 0) * TOUR_STEP
    pop = 1 + 0.3 * (1 - ss(clamp(since / 0.3))) if cur >= 0 else 1
    bx, by = 1010, 200
    kp = seg(t, 0.6, 1.1)
    if kp > 0:
        d.rounded_rectangle([(bx - 190) * SS, (by - 95) * SS, (bx + 190) * SS, (by + 120) * SS], radius=10 * SS,
                            fill=mix(CREAM, (250, 246, 236), kp), outline=mix(CREAM, INK, kp), width=2 * SS)
        last = cur >= FULL
        numc = ORANGE if last else GREEN
        ctext(d, (bx, by - 62), "HÀNG", F("monob", 18), mix(CREAM, MUTED, kp))
        ctext(d, (bx - 30, by - 8), f"{max(done_rows, 0)}", F("serifb", int(64 * pop)), mix(CREAM, numc, kp), anchor="rm")
        ctext(d, (bx - 20, by - 4), "/ 16", F("serifb", 34), mix(CREAM, INK, kp), anchor="lm")
        nl = NL(max(cur, 0))
        ctext(d, (bx, by + 50), f"5 bao × {nl} lớp = {5 * nl} bao", F("mono", 17), mix(CREAM, ORANGE if last else INK, kp))
        ctext(d, (bx, by + 85), f"tổng: {cum} bao" + (" = 34 tấn" if cum == 680 else ""), F("monob", 20), mix(CREAM, INK, kp))
    chapter(im, "KIỂM TRA · ĐẦU → CUỐI XE", t)
    counter(d, 680)
    subtitle(d, "8 hàng × 45 bao + 8 hàng × 40 bao = 680 bao", t)
    corners(d); footer(d, 9, N_SC)
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
                fill = (GREEN if j < 360 else ORANGE) if j < nfill else mix(CREAM, INK, 0.1)
                d.rectangle([px * SS, py * SS, (px + cw - 1.5) * SS, (py + ch - 1.5) * SS], fill=fill)
        if i == 1:
            ctext(d, (x + 150, y + 80), "8 hàng", F("serifb", 40), c)
            ctext(d, (x + 150, y + 130), "× 45 bao", F("serifb", 30), c)
            ctext(d, (x + 150, y + 178), "+ 8 hàng × 40 bao", F("monob", 15), mix(CREAM, ORANGE, k))
            bx, by = x + 300, y + 190
            for r in range(16):
                hmax = NL(r)
                hh = hmax * seg(tt, 0.3 + r * 0.09, 0.6 + r * 0.09)
                col = GREEN if r < FULL else ORANGE
                d.rectangle([(bx + r * 14.5) * SS, (by - hh * 16) * SS, (bx + r * 14.5 + 11) * SS, by * SS], fill=col)
            d.line([bx * SS, (by + 1) * SS, (bx + 232) * SS, (by + 1) * SS], fill=INK, width=2 * SS)
        if i == 2:
            ctext(d, (x + 150, y + 80), "cao 117 cm", F("serifb", 36), c)
            ctext(d, (x + 150, y + 130), "9 lớp × 13 cm", F("mono", 16), c)
            ctext(d, (x + 150, y + 165), "vượt thành 80 cm: 37 cm", F("mono", 14), mix(CREAM, RED, k))
            ctext(d, (x + 150, y + 190), "hàng 9–16: 8 lớp, cao 104 cm", F("mono", 14), mix(CREAM, ORANGE, k))
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
            ctext(d, (x + 150, y + 80), "trống 26 cm", F("serifb", 34), c)
            ctext(d, (x + 150, y + 130), "sau hàng 16", F("mono", 16), c)
            ctext(d, (x + 150, y + 165), "1.226 − 16 × 75 = 26", F("mono", 14), mix(CREAM, MUTED, k))
            bx, by, bw = x + 300, y + 110, 225
            d.rectangle([bx * SS, by * SS, (bx + bw) * SS, (by + 34) * SS], outline=INK, width=2 * SS)
            f15 = seg(tt, 0.3, 1.3)
            d.rectangle([bx * SS, by * SS, (bx + bw * 600 / 1226 * f15) * SS, (by + 34) * SS], fill=GREEN)
            if f15 >= 1:
                g14 = bx + bw * 600 / 1226
                gx0 = bx + bw * 1200 / 1226
                d.rectangle([g14 * SS, (by + 34 * 1 / 9) * SS, gx0 * SS, (by + 34) * SS], fill=ORANGE)
                dim_line(d, (gx0 * SS, (by - 18) * SS), ((bx + bw) * SS, (by - 18) * SS), "", RED, F("mono", 12))
                d.text(((bx + bw) * SS, (by + 52) * SS), "cửa sau", font=F("mono", 12), fill=MUTED, anchor="rm")
                d.text((bx * SS, (by + 52) * SS), "đầu thùng", font=F("mono", 12), fill=MUTED, anchor="lm")
    chapter(im, "SỐ LIỆU", t)
    subtitle(d, "Bốn con số của một xe container bạt 34 tấn", t, y=648)
    corners(d); footer(d, 10, N_SC)
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
    def vis(r, c, k_): return (0, "o") if r >= FULL else (0, "n")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    steps = ["1 · 3 · 5 → 2 · 4", "đủ lớp", "lùi 75 cm"]
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
    ctext(d, (W / 2, 200), "8 hàng × 45 bao (9 lớp) · 8 hàng × 40 bao (8 lớp) · trống 26 cm", F("serif", 22), mix(ORANGE, INK, kk))
    ctext(d, (W / 2, 245), "Làm đúng trình tự này cho mọi xe container bạt 34 tấn", F("serifb", 24), mix(ORANGE, CREAM, kk))
    ctext(d, (W / 2, 640), "Nguồn: cách chất theo xác nhận kho PC (KCP) · thùng 1.226 × 235 × 215 cm · bao 75 × 50 × 13 cm, 50 kg",
          F("mono", 13), mix(ORANGE, INK, seg(t, 2.5, 3.0)))
    corners(d, INK); footer(d, 11, N_SC, INK)
    return im

SCENES = [("hook", 4.0, sc_hook), ("map", 5.0, sc_map), ("bag", 5.5, sc_bag),
          ("section", 13.0, sc_section), ("layer_a", 5.0, sc_layer_a), ("row", 16.0, sc_row),
          ("move", 12.0, sc_move), ("extra", 12.0, sc_extra),
          ("tour", 15.0, sc_tour), ("stats", 10.0, sc_stats), ("end", 6.5, sc_end)]
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
