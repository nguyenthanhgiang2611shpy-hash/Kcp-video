# -*- coding: utf-8 -*-
"""Video motion graphic: Chất xá 680 bao (34 tấn) vào xe container bạt – kho PC.
Dựng lại từ bản "Chat_xa_34T_kho_PC_v3_giong_doc_email" (giữ nội dung + giọng đọc gốc),
thêm chuyển động: chuyển cảnh quét chéo, chữ bật từng từ, bao rơi có nảy, camera trôi, thẻ bật.

Trình tự: mỗi lớp 5 bao ngang, đặt bao 1·3·5 trước rồi ép 2·4 vào khe;
hàng 1–8: 9 lớp = 45 bao (cao 117 cm); hàng 9–16: 8 lớp = 40 bao (cao 104 cm); trống 26 cm.

Chạy:  python3 make_video_motion.py full <giong_doc.mp4|wav> [out.mp4]
       python3 make_video_motion.py test [sheet.png]
       python3 make_video_motion.py frame <giây> <out.png>
"""
import sys, math, subprocess, os
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 1280, 720, 2, 25

# ---------- màu ----------
CREAM = (243, 236, 220); INK = (29, 43, 58); ORANGE = (217, 119, 75)
GREEN = (38, 122, 64); RED = (178, 52, 44); MUTED = (110, 116, 120)
CARD = (250, 246, 236)
BAG_TOP = (252, 250, 244); BAG_FRONT = (220, 214, 200); BAG_END = (236, 231, 219)
FLOOR_C = (160, 168, 172); FLOOR_EDGE = (44, 62, 80)
WALL_FAR = (112, 138, 160); WALL_HEAD = (88, 114, 140)

# ---------- số liệu ----------
L, WD, HROOF, HWALL = 1226, 235, 215, 80
BL, BW, BH = 75, 47, 13
COLS, ROWS, FULL = 5, 16, 8
ORDER = [0, 2, 4, 1, 3]               # bao 1, 3, 5 trước rồi 2, 4
def POS(c): return ORDER.index(c)
def NL(r): return 9 if r < FULL else 8
assert sum(COLS * NL(r) for r in range(ROWS)) == 680
assert 9 * BH == 117 and 8 * BH == 104 and L - ROWS * BL == 26 and COLS * BW == WD

# ---------- font ----------
FP = {"serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
      "serifb": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
      "mono": "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
      "monob": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"}
_fc = {}
def F(name, size):
    k = (name, max(4, int(size * SS)))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FP[name], k[1])
    return _fc[k]

# ---------- easing ----------
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def eoc(x): x = clamp(x); return 1 - (1 - x) ** 3
def eob(x, s=1.9):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)
def seg(t, t0, t1): return ss((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)
def sego(t, t0, t1): return eoc((t - t0) / (t1 - t0))
def segb(t, t0, t1): return eob((t - t0) / (t1 - t0))
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): k = clamp(k); return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))
def vn(n): return f"{n:,}".replace(",", ".")
def inout(t, a, b, d=0.35): return seg(t, a, a + d) * (1 - seg(t, b, b + d))

G_T = 0.0  # thời gian toàn cục (cho nền trôi)

# ---------- camera ----------
class Cam:
    def __init__(s, cx, cy, z, dy=0): s.cx, s.cy, s.z, s.dy = cx, cy, z, dy
    def P(s, x, y, z):
        u = 0.95 * x - 0.50 * y
        v = 0.18 * x + 0.32 * y - 0.90 * z
        return ((u - s.cx) * s.z * SS + W * SS / 2, (v - s.cy) * s.z * SS + H * SS / 2 + s.dy * SS)

def cam_lerp(a, b, k):
    return Cam(lerp(a.cx, b.cx, k), lerp(a.cy, b.cy, k), lerp(a.z, b.z, k), lerp(a.dy, b.dy, k))

def breathe(c, t, amp=1.0):
    """camera trôi nhẹ liên tục"""
    return Cam(c.cx + 4 * amp * math.sin(t * 0.45), c.cy + 2 * amp * math.sin(t * 0.37 + 1),
               c.z * (1 + 0.018 * amp * math.sin(t * 0.3)), c.dy)

CAM_FULL = Cam(525, 30, 0.86)
CAM_HEAD = Cam(70, 10, 2.0)
CAM_HEAD2 = Cam(110, -5, 1.7)

# ---------- vẽ cơ bản ----------
def ctext(d, xy, s, font, fill, anchor="mm"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=font, fill=fill, anchor=anchor)

def tw_(d, s, font): return d.textlength(s, font=font) / SS

def fit_font(d, s, name, size, maxw):
    while size > 10 and d.textlength(s, font=F(name, size)) > maxw * SS:
        size -= 1
    return size

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
    d.polygon([p1, (p1[0] - h * math.cos(ang - 0.45), p1[1] - h * math.sin(ang - 0.45)),
               (p1[0] - h * math.cos(ang + 0.45), p1[1] - h * math.sin(ang + 0.45))], fill=fill)

def dim_line(d, p0, p1, label, color, font, offset=(0, 0), both=True):
    d.line([p0, p1], fill=color, width=2 * SS)
    for a, b in ((p0, p1), (p1, p0)) if both else ((p0, p1),):
        ang = math.atan2(a[1] - b[1], a[0] - b[0]); h = 9 * SS
        d.polygon([a, (a[0] - h * math.cos(ang - 0.5), a[1] - h * math.sin(ang - 0.5)),
                   (a[0] - h * math.cos(ang + 0.5), a[1] - h * math.sin(ang + 0.5))], fill=color)
    if label:
        mx, my = (p0[0] + p1[0]) / 2 + offset[0] * SS, (p0[1] + p1[1]) / 2 + offset[1] * SS
        bb = d.textbbox((mx, my), label, font=font, anchor="mm")
        d.rectangle([bb[0] - 6 * SS, bb[1] - 4 * SS, bb[2] + 6 * SS, bb[3] + 4 * SS], fill=CREAM)
        d.text((mx, my), label, font=font, fill=color, anchor="mm")

def tag(d, xy, s, color, font=None, anchor="mm", bg=CREAM):
    font = font or F("monob", 14)
    bb = d.textbbox(xy, s, font=font, anchor=anchor)
    d.rectangle([bb[0] - 6 * SS, bb[1] - 4 * SS, bb[2] + 6 * SS, bb[3] + 4 * SS], fill=bg)
    d.text(xy, s, font=font, fill=color, anchor=anchor)

# ---------- chữ chuyển động ----------
def pop(d, xy, s, name, size, color, t, t0, dur=0.45, bg=CREAM, anchor="mm", t_out=None):
    """chữ bật phóng to có độ nảy"""
    k = (t - t0) / dur
    if k <= 0: return
    a = eoc(k * 1.6)
    if t_out is not None:
        o = seg(t, t_out, t_out + 0.3)
        if o >= 1: return
        a *= 1 - o
    sc = eob(k)
    d.text((xy[0] * SS, xy[1] * SS), s, font=F(name, size * max(0.05, sc)), fill=mix(bg, color, a), anchor=anchor)

def kin(d, center, s, name, size, color, t, t0, step=0.07, bg=CREAM, t_out=None, rise=26):
    """chữ hiện từng từ, trượt lên"""
    if t < t0: return
    if t_out is not None and t > t_out + 0.4: return
    f = F(name, size)
    words = s.split(" ")
    sp = tw_(d, " ", f)
    ws = [tw_(d, w, f) for w in words]
    x = center[0] - (sum(ws) + sp * (len(words) - 1)) / 2
    o = seg(t, t_out, t_out + 0.35) if t_out is not None else 0
    for i, w in enumerate(words):
        k = sego(t, t0 + i * step, t0 + i * step + 0.45)
        if k > 0:
            y = center[1] + rise * (1 - k) - 18 * o
            ctext(d, (x, y), w, f, mix(bg, color, k * (1 - o)), anchor="lm")
        x += ws[i] + sp

def subtitle(d, s, t, y=640):
    if t < 0.15: return
    size = fit_font(d, s, "serif", 29, 1080)
    f = F("serif", size)
    k = sego(t, 0.15, 0.55)
    w = tw_(d, s, f)
    hw = (w / 2 + 24) * k
    d.rounded_rectangle([(W / 2 - hw) * SS, (y - 26) * SS, (W / 2 + hw) * SS, (y + 26) * SS], radius=8 * SS, fill=CREAM)
    d.rectangle([(W / 2 - hw) * SS, (y + 24) * SS, (W / 2 - hw + 2 * hw * seg(t, 0.3, 1.2)) * SS, (y + 27) * SS], fill=ORANGE)
    kin(d, (W / 2, y), s, "serif", size, INK, t, 0.25, step=0.035, rise=14)

def chapter(im, label, t, color=INK):
    k = (t - 0.05) / 0.55
    if k <= 0: return
    f = F("monob", 18)
    dd = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    tw = int(dd.textlength(label, font=f)); pad = 14 * SS
    lab = Image.new("RGBA", (tw + 2 * pad, 40 * SS), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lab)
    dl.rectangle([0, 0, lab.width, lab.height], fill=color + (255,))
    dl.rectangle([0, 0, 5 * SS, lab.height], fill=(ORANGE if color != ORANGE else INK) + (255,))
    dl.text((pad, lab.height // 2), label, font=f, fill=CREAM, anchor="lm")
    lab = lab.rotate(lerp(-8, 2.0, eob(k)), expand=True, resample=Image.BICUBIC)
    x = int(lerp(-lab.width, 44 * SS, eob(k)))
    im.paste(lab, (x, 40 * SS), lab)

def counter(d, n, color=INK):
    f = F("monob", 17)
    d.text((1238 * SS, 62 * SS), f"ĐÃ CHẤT {n}/680 BAO", font=f, fill=color, anchor="rm")
    x0, x1, y = 1238 - 230, 1238, 80
    d.rectangle([x0 * SS, y * SS, x1 * SS, (y + 6) * SS], fill=mix(CREAM, INK, 0.15))
    xe = x0 + (x1 - x0) * n / 680
    c = GREEN if n < 680 else ORANGE
    d.rectangle([x0 * SS, y * SS, xe * SS, (y + 6) * SS], fill=c)
    if 0 < n < 680:
        r = 5 + 1.5 * math.sin(G_T * 8)
        d.ellipse([(xe - r) * SS, (y + 3 - r) * SS, (xe + r) * SS, (y + 3 + r) * SS], fill=c)

def stamp(im, s, t, color=RED, pos=(1010, 520), angle=-6):
    k = seg(t, 0.0, 0.22)
    if k <= 0: return
    f = F("monob", 24)
    tw = int(ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(s, font=f))
    pad = 16 * SS
    st = Image.new("RGBA", (tw + 2 * pad, 52 * SS), (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    ds.rectangle([2 * SS, 2 * SS, st.width - 2 * SS, st.height - 2 * SS], outline=color + (255,), width=4 * SS)
    ds.rectangle([7 * SS, 7 * SS, st.width - 7 * SS, st.height - 7 * SS], outline=color + (160,), width=1 * SS)
    ds.text((st.width // 2, st.height // 2), s, font=f, fill=color + (255,), anchor="mm")
    sc = lerp(2.0, 1.0, k)
    st = st.resize((int(st.width * sc), int(st.height * sc)), Image.LANCZOS)
    shake = 6 * math.sin(t * 60) * (1 - seg(t, 0.22, 0.5)) if t > 0.22 else 0
    st = st.rotate(angle + shake * 0.4, expand=True, resample=Image.BICUBIC)
    if k < 1:
        st.putalpha(st.split()[3].point(lambda v: int(v * k)))
    im.paste(st, (int((pos[0] + shake) * SS - st.width / 2), int(pos[1] * SS - st.height / 2)), st)

def badge(d, xy, s, color, t, t0, r=13):
    k = (t - t0) / 0.4
    if k <= 0: return
    rr = r * eob(k) * SS
    x, y = xy
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color, outline=CREAM, width=2 * SS)
    if k > 0.4:
        d.text((x, y), s, font=F("monob", 13), fill=CREAM, anchor="mm")

def card(d, box, t, t0, outline=INK):
    """thẻ trắng bật lên, trả hệ số k"""
    k = (t - t0) / 0.5
    if k <= 0: return 0
    x0, y0, x1, y1 = box
    sc = eob(k)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hw, hh = (x1 - x0) / 2 * sc, (y1 - y0) / 2 * sc
    d.rounded_rectangle([(cx - hw + 6) * SS, (cy - hh + 6) * SS, (cx + hw + 6) * SS, (cy + hh + 6) * SS],
                        radius=10 * SS, fill=mix(CREAM, INK, 0.12 * eoc(k)))
    d.rounded_rectangle([(cx - hw) * SS, (cy - hh) * SS, (cx + hw) * SS, (cy + hh) * SS], radius=10 * SS,
                        fill=CARD, outline=mix(CREAM, outline, eoc(k)), width=2 * SS)
    return eoc(k * 1.5)

# ---------- nền + khung ----------
def frame_base(bg=CREAM):
    im = Image.new("RGB", (W * SS, H * SS), bg)
    d = ImageDraw.Draw(im)
    dot = mix(bg, INK, 0.07)
    off = (G_T * 8) % 40
    for gx in range(-1, 33):
        for gy in range(-1, 19):
            x, y = gx * 40 + off, gy * 40 + off * 0.5
            d.rectangle([x * SS, y * SS, (x + 2) * SS, (y + 2) * SS], fill=dot)
    return im, d

def corners(d, color=INK):
    m, ln = 22 * SS, 34 * SS
    for (x, y, sx, sy) in ((m, m, 1, 1), (W * SS - m, m, -1, 1), (m, H * SS - m, 1, -1), (W * SS - m, H * SS - m, -1, -1)):
        d.line([(x, y), (x + sx * ln, y)], fill=color, width=3 * SS)
        d.line([(x, y), (x, y + sy * ln)], fill=color, width=3 * SS)

N_SC = 13
def footer(d, n, color=INK):
    f = F("mono", 12)
    d.text((66 * SS, 692 * SS), "KCP VIỆT NAM · LOGISTICS · CHẤT BAO XE CONTAINER BẠT 34 TẤN · KHO PC", font=f, fill=color, anchor="ls")
    d.text((1214 * SS, 692 * SS), f"minh họa, không theo tỷ lệ · {n}/{N_SC}", font=f, fill=color, anchor="rs")

def finish(im, d, n, t, chap=None, chap_c=INK, sub=None, cnt=None):
    if chap: chapter(im, chap, t, chap_c)
    if cnt is not None: counter(d, cnt)
    if sub: subtitle(d, sub, t)
    corners(d); footer(d, n)
    return im

# ---------- thùng xe + bao ----------
def draw_truck_back(d, cam, grow=1.0):
    P = cam.P
    d.polygon([P(0, 0, 0), P(L, 0, 0), P(L, WD, 0), P(0, WD, 0)], fill=FLOOR_C)
    hw, hr = HWALL * grow, HROOF * grow
    if grow > 0:
        d.polygon([P(0, 0, 0), P(L, 0, 0), P(L, 0, hw), P(0, 0, hw)], fill=WALL_FAR, outline=FLOOR_EDGE)
        d.polygon([P(0, 0, 0), P(0, WD, 0), P(0, WD, hr), P(0, 0, hr)], fill=WALL_HEAD, outline=FLOOR_EDGE)
    for r in range(1, ROWS + 1):
        d.line([P(r * BL, 0, 0), P(r * BL, WD, 0)], fill=(150, 158, 163), width=1 * SS)

def draw_truck_front(d, cam, a=1.0):
    P = cam.P
    d.polygon([P(0, WD, 0), P(L, WD, 0), P(L, WD, -8), P(0, WD, -8)], fill=FLOOR_EDGE)
    d.polygon([P(L, 0, 0), P(L, WD, 0), P(L, WD, -8), P(L, 0, -8)], fill=(60, 80, 100))
    if a <= 0: return
    c = mix(CREAM, INK, 0.75 * a); c2 = mix(CREAM, INK, 0.4 * a)
    dashed(d, P(0, WD, HWALL), P(L, WD, HWALL), c, 1)
    dashed(d, P(L, 0, HWALL), P(L, WD, HWALL), c, 1)
    dashed(d, P(L, WD, 0), P(L, WD, HWALL), c, 1)
    dashed(d, P(L, 0, 0), P(L, 0, HWALL), c, 1)
    for p0, p1 in ((P(0, 0, HROOF), P(L, 0, HROOF)), (P(0, WD, HROOF), P(L, WD, HROOF)),
                   (P(L, 0, HROOF), P(L, WD, HROOF)), (P(0, WD, 0), P(0, WD, HROOF))):
        dashed(d, p0, p1, c2, 1, 6, 8)

def bag_box(r, c, k):
    x0 = r * BL; y1 = WD - c * BW
    return (x0, y1 - BW, k * BH, x0 + BL, y1, k * BH + BH)

STY = {"n": ((120, 120, 112), BAG_TOP, BAG_FRONT, BAG_END),
       "g": (GREEN, BAG_TOP, BAG_FRONT, BAG_END),
       "o": (ORANGE, (255, 238, 222), (240, 196, 168), (248, 214, 190)),
       "on": ((170, 120, 95), (255, 238, 222), (240, 196, 168), (248, 214, 190)),
       "hl": (GREEN, (232, 246, 232), (196, 226, 200), (214, 236, 216))}

def draw_bag(d, cam, box, dz=0.0, style="n", alpha=1.0):
    x0, y0, z0, x1, y1, z1 = box
    z0 += dz; z1 += dz
    P = cam.P
    g = 1.2
    x0g, x1g, y0g, y1g = x0 + g, x1 - g, y0 + g, y1 - g
    col, top, front, end = STY[style]
    if alpha < 1:
        top, front, end = mix(CREAM, top, alpha), mix(CREAM, front, alpha), mix(CREAM, end, alpha)
    lw = SS * (2 if style in ("g", "o", "hl") and cam.z > 1.1 else 1)
    d.polygon([P(x0g, y1g, z0), P(x1g, y1g, z0), P(x1g, y1g, z1), P(x0g, y1g, z1)], fill=front, outline=col, width=lw)
    d.polygon([P(x1g, y0g, z0), P(x1g, y1g, z0), P(x1g, y1g, z1), P(x1g, y0g, z1)], fill=end, outline=col, width=lw)
    d.polygon([P(x0g, y0g, z1), P(x1g, y0g, z1), P(x1g, y1g, z1), P(x0g, y1g, z1)], fill=top, outline=col, width=lw)
    if cam.z > 1.0:
        ym = (y0 + y1) / 2
        for a, b in ((0.25, 0.38), (0.45, 0.58), (0.65, 0.78)):
            d.line([P(lerp(x0, x1, a), ym, z1), P(lerp(x0, x1, b), ym, z1)], fill=(214, 120, 90), width=max(1, int(SS * cam.z * 0.7)))

def all_slots():
    for r in range(ROWS):
        for k in range(NL(r)):
            for c in range(COLS):
                yield r, c, k

def draw_bags(d, cam, visible):
    items = []
    for r, c, k in all_slots():
        v = visible(r, c, k)
        if v is None: continue
        items.append((r, -c, k, c, v))
    items.sort(key=lambda it: (it[0], it[1], it[2]))
    for r, _, k, c, v in items:
        draw_bag(d, cam, bag_box(r, c, k), v[0], v[1])

def drop(t, T, dur=0.35, h=80):
    """bao rơi xuống + nảy nhẹ; None nếu chưa xuất hiện"""
    if t < T: return None
    p = (t - T) / dur
    if p < 1: return h * (1 - p * p)
    q = (t - T - dur) / 0.2
    if q < 1: return h * 0.07 * math.sin(math.pi * q)
    return 0.0

def idx_in_row(c, k): return k * 5 + POS(c)

# ================= CÁC CẢNH =================
def sc_hook(t, D):
    im, d = frame_base()
    grow = segb(t, 0.6, 1.6)
    cam = breathe(Cam(525, 55, lerp(0.7, 0.9, sego(t, 0, 2.5))), t)
    draw_truck_back(d, cam, grow); draw_truck_front(d, cam, seg(t, 1.2, 2.0))
    kin(d, (W / 2, 128), "680 bao, 34 tấn", "serifb", 46, INK, t, 0.3, step=0.12)
    kin(d, (W / 2, 186), "chất vào xe container bạt", "serifb", 44, ORANGE, t, 0.9, step=0.1)
    f = F("monob", 16)
    chips = ["01 · MỘT LỚP", "02 · MỘT HÀNG", "03 · LÙI 75 CM"]
    ws = [tw_(d, s, f) + 28 for s in chips]
    x = W / 2 - (sum(ws) + 26 * 2) / 2
    for i, s in enumerate(chips):
        k = (t - (2.4 + i * 0.5)) / 0.45
        if k > 0:
            sc = eob(k); cx = x + ws[i] / 2; y = 590
            hw, hh = ws[i] / 2 * sc, 18 * sc
            d.rectangle([(cx - hw) * SS, (y - hh) * SS, (cx + hw) * SS, (y + hh) * SS], fill=INK)
            if k > 0.5: ctext(d, (cx, y), s, f, CREAM)
        x += ws[i] + 26
    counter(d, 0)
    corners(d); footer(d, 1)
    return im

def sc_map(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(Cam(525, 60, 0.8), Cam(525, 45, 0.87), sego(t, 0, D)), t)
    draw_truck_back(d, cam); draw_truck_front(d, cam)
    P = cam.P; fm = F("monob", 15)
    a = sego(t, 0.4, 1.4)
    if a > 0: dim_line(d, P(0, WD + 30, 0), P(L * a, WD + 30, 0), "dài 1.226 cm" if a > 0.6 else "", RED, fm)
    b = sego(t, 1.3, 2.0)
    if b > 0: dim_line(d, P(L + 25, 0, 0), P(L + 25, WD * b, 0), "rộng 235" if b > 0.6 else "", RED, fm, offset=(48, 0))
    c = sego(t, 1.8, 2.5)
    if c > 0: dim_line(d, P(0, 0, 0), P(0, 0, HROOF * c), "cao 215" if c > 0.6 else "", RED, fm, offset=(-50, 0))
    e = segb(t, 2.6, 3.1)
    if e > 0:
        tag(d, P(0, WD / 2, HROOF + 22), "ĐẦU THÙNG (sát cabin)", mix(CREAM, INK, e), F("monob", max(4, 14 * e)))
        tag(d, P(L, WD / 2, HWALL + 40), "CUỐI THÙNG (cửa sau)", mix(CREAM, INK, e), F("monob", max(4, 14 * e)))
    g = sego(t, 3.0, 4.6)
    if g > 0:
        arrow(d, P(60, WD / 2, 2), P(lerp(60, L - 60, g), WD / 2, 2), GREEN, 5, 18)
        # các chấm chạy theo mũi tên
        for j in range(4):
            u = ((t * 0.5 + j / 4) % 1) * g
            x, y = P(lerp(60, L - 60, u), WD / 2, 2)
            d.ellipse([x - 5 * SS, y - 5 * SS, x + 5 * SS, y + 5 * SS], fill=GREEN)
    k = card(d, (50, 410, 330, 550), t, 1.2)
    if k > 0:
        cb = Cam(22.6 - (190 - W / 2) / 1.6, 8.3 - (478 - H / 2) / 1.6, 1.6)
        dz = drop(t, 1.5, 0.35, 40)
        if dz is not None: draw_bag(d, cb, (0, 0, 0, 75, 50, 13), dz, "n")
        ctext(d, (190, 432), "1 bao = 50 kg", F("serifb", 18), mix(CARD, INK, k))
        ctext(d, (190, 530), "75 × 50 × 13 cm", F("mono", 15), mix(CARD, INK, k))
    return finish(im, d, 2, t, "TOÀN CẢNH", sub="Chất từ trong ra ngoài: đầu thùng trước, cửa sau cuối", cnt=0)

def sc_bag(t, D):
    im, d = frame_base()
    z = lerp(2.7, 3.3, sego(t, 0, D))
    cam = Cam(22.6 - (430 - W / 2) / z, 8.3 - (370 - H / 2) / z, z)
    dz = drop(t, 0.3, 0.5, 120)
    if dz is not None:
        # bóng đổ
        P = cam.P; sh = clamp(1 - dz / 120)
        d.polygon([P(4, 4, 0), P(BL + 4, 4, 0), P(BL + 4, 54, 0), P(4, 54, 0)], fill=mix(CREAM, INK, 0.15 * sh))
        draw_bag(d, cam, (0, 0, 0, BL, 50, BH), dz, "n")
    P = cam.P
    k1 = sego(t, 1.4, 1.9)
    if k1 > 0:
        c = mix(CREAM, INK, k1)
        dim_line(d, P(-6, 56, 0), P(-6 + BL * k1, 56, 0), "dài 75 cm" if k1 > 0.7 else "", c, F("monob", 16), offset=(-10, 22))
        dim_line(d, P(-8, 50, 0), P(-8, 50, BH * k1), "", c, F("monob", 16))
        tag(d, P(-8, 72, BH / 2), "dày 13", c, F("monob", 15))
    k2 = sego(t, 2.4, 3.0)
    if k2 > 0:
        dim_line(d, P(BL + 8, 0, 0), P(BL + 8, 50 * k2, 0), "", RED, F("monob", 16))
        x, y = P(BL + 8, 25, 0)
        pulse = 1 + 0.1 * math.sin(max(0, t - 3.0) * 6) * (t > 3.0)
        pop(d, (x / SS + 95, y / SS + 5), "ngang 0,5 m", "monob", 26 * pulse, RED, t, 2.6)
    kin(d, (930, 250), "Bao đường", "serifb", 40, INK, t, 0.8)
    if t > 1.2:
        n = int(round(50 * sego(t, 1.2, 2.2)))
        pop(d, (930, 312), f"{n} kg", "serifb", 60, ORANGE, t, 1.2, 0.5)
    kin(d, (930, 385), "dài 0,75 m · ngang 0,5 m", "mono", 20, INK, t, 3.2, step=0.05)
    kin(d, (930, 417), "dày 13 cm", "mono", 20, INK, t, 3.5)
    return finish(im, d, 3, t, "BAO ĐƯỜNG", sub="Mỗi bao đường 50 kg rộng 0,5 m", cnt=0)

SEC_S = 3.4
SEC_X0 = 640 - WD * SEC_S / 2
SEC_Y = 470

def bag2d(d, x, y, w, h, outline=GREEN, fill=BAG_TOP, lw=2):
    d.rounded_rectangle([x * SS, (y - h) * SS, (x + w) * SS, y * SS], radius=int(min(h, w) * 0.35 * SS),
                        fill=fill, outline=outline, width=lw * SS)
    cy = y - h / 2
    for a, b in ((0.3, 0.42), (0.58, 0.7)):
        d.line([(x + w * a) * SS, cy * SS, (x + w * b) * SS, cy * SS], fill=(214, 120, 90), width=2 * SS)

def sc_section(t, D):
    im, d = frame_base()
    s_ = SEC_S; x0 = SEC_X0; fy = SEC_Y; wall = 16; hw = HWALL * s_
    d.rectangle([(x0 - wall) * SS, (fy - hw) * SS, x0 * SS, (fy + 14) * SS], fill=WALL_FAR)
    d.rectangle([(x0 + WD * s_) * SS, (fy - hw) * SS, (x0 + WD * s_ + wall) * SS, (fy + 14) * SS], fill=WALL_FAR)
    d.rectangle([(x0 - wall) * SS, fy * SS, (x0 + WD * s_ + wall) * SS, (fy + 14) * SS], fill=FLOOR_EDGE)
    tag(d, ((x0 - wall - 10) * SS, (fy - hw / 2) * SS), "thành", MUTED, F("mono", 14), anchor="rm")
    k0 = sego(t, 0.3, 1.2)
    if k0 > 0:
        dim_line(d, (x0 * SS, (fy + 48) * SS), ((x0 + WD * s_ * k0) * SS, (fy + 48) * SS),
                 "lòng thùng rộng 2,35 m" if k0 > 0.8 else "", INK, F("monob", 20))
    T = {0: 1.8, 2: 2.6, 4: 3.4, 1: 7.4, 3: 8.6}
    bw = BW * s_; bh = BH * s_
    # khe trống chờ bao 2, 4
    gap = inout(t, 4.0, 8.4 + 1.0)
    for c in (1, 3):
        if gap > 0 and t < T[c] + 0.5:
            pul = 0.5 + 0.5 * math.sin(t * 6)
            col = mix(CREAM, ORANGE, gap * (0.4 + 0.6 * pul))
            xx = x0 + c * bw
            dashed(d, (xx * SS, (fy - bh) * SS), ((xx + bw) * SS, (fy - bh) * SS), col, 2, 6, 5)
            dashed(d, (xx * SS, (fy - bh) * SS), (xx * SS, fy * SS), col, 2, 6, 5)
            dashed(d, ((xx + bw) * SS, (fy - bh) * SS), ((xx + bw) * SS, fy * SS), col, 2, 6, 5)
    n = 0
    for c in ORDER:
        if t < T[c] - 0.6: continue
        cx = x0 + (c + 0.5) * bw
        if c in (1, 3) and t < T[c]:
            # mũi tên chỉ xuống khe
            bob = 6 * math.sin(t * 8)
            arrow(d, (cx * SS, (fy - 150 + bob) * SS), (cx * SS, (fy - 95 + bob) * SS), ORANGE, 3, 12)
            continue
        if t < T[c]: continue
        p = (t - T[c]) / 0.45
        y = fy - 130 * (1 - eoc(p)) if c in (0, 2, 4) else fy - 130 * (1 - clamp(p) ** 2)
        if c in (1, 3):
            # ép vào khe: hơi rộng hơn rồi co lại vừa
            sq = clamp((p - 0.6) / 0.6)
            w = lerp(bw * 1.12, bw, eob(sq)) if p > 0.6 else bw * 1.12
            if p > 0.75: y = fy
            col, fill = ORANGE, (255, 232, 216)
        else:
            w = bw; col, fill = GREEN, BAG_TOP
        bag2d(d, cx - w / 2, y, w, bh, col, fill)
        if p > 0.6: n += 1
        badge(d, (cx * SS, (fy - bh - 26) * SS), str(c + 1), col, t, T[c] + 0.3)
    # thước 47 cm
    k = sego(t, 10.6, 11.6)
    if k > 0:
        ry = fy - bh - 58
        d.line([x0 * SS, ry * SS, (x0 + WD * s_ * k) * SS, ry * SS], fill=GREEN, width=3 * SS)
        for c in range(6):
            xx = x0 + c * bw
            if xx <= x0 + WD * s_ * k + 1:
                d.line([xx * SS, (ry - 8) * SS, xx * SS, (ry + 8) * SS], fill=GREEN, width=2 * SS)
                if c < 5 and xx + bw <= x0 + WD * s_ * k + 1:
                    ctext(d, (xx + bw / 2, ry - 18), "47 cm", F("mono", 15), GREEN)
    kin(d, (640, 150), "Bước 1: đặt bao 1 · 3 · 5 trước", "serifb", 32, GREEN, t, 1.0, t_out=6.4)
    kin(d, (640, 150), "Bước 2: ép bao 2 · 4 vào khe giữa", "serifb", 32, ORANGE, t, 6.8, t_out=10.0)
    kin(d, (640, 150), "5 × 47 = 2,35 m: vừa khít lòng thùng", "serifb", 32, GREEN, t, 10.4)
    if t > 13.4: stamp(im, "1·3·5 TRƯỚC → 2·4 SAU", t - 13.4, RED, (1010, 300), -6)
    ctext(d, (640, 100), "MẶT CẮT NGANG THÙNG · nhìn từ cửa sau", F("mono", 15), MUTED)
    return finish(im, d, 4, t, "01 · MỘT LỚP", sub="Đặt bao 1, 3, 5 trước, sau đó ép bao 2, 4 vào khe", cnt=n)

def sc_layer_a(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(Cam(260, 20, 1.0), CAM_HEAD, sego(t, 0, 1.4)), t, 0.6)
    draw_truck_back(d, cam)
    T = {0: 1.2, 2: 1.6, 4: 2.0, 1: 2.9, 3: 3.4}
    def vis(r, c, k):
        if r == 0 and k == 0:
            dz = drop(t, T[c], 0.35, 90)
            return None if dz is None else (dz, "o" if c in (1, 3) else "g")
        return None
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    for c in range(5):
        x0, y0, z0, x1, y1, z1 = bag_box(0, c, 0)
        badge(d, P((x0 + x1) / 2, (y0 + y1) / 2, z1 + 4), str(c + 1), ORANGE if c in (1, 3) else GREEN, t, T[c] + 0.35)
    tag(d, P(0, WD / 2, 175), "VÁCH ĐẦU THÙNG", CREAM, F("monob", 15), bg=WALL_HEAD)
    k = sego(t, 4.2, 4.9)
    if k > 0:
        dim_line(d, P(BL + 18, 0, 0), P(BL + 18, WD * k, 0), "5 × 47 = 2,35 m" if k > 0.7 else "", GREEN, F("monob", 16), offset=(80, 6))
    return finish(im, d, 5, t, "01 · MỘT LỚP", sub="Lớp 1 sát vách đầu thùng: bao 1, 3, 5 trước, rồi 2, 4", cnt=5)

def row_T(c, k):
    if k == 0: return -1
    if k == 1: return 0.8 + POS(c) * 0.45
    if k == 2: return 3.6 + POS(c) * 0.4
    return 6.4 + (k - 3) * 0.75 + POS(c) * 0.12

def sc_row(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(CAM_HEAD, CAM_HEAD2, seg(t, 3.5, 6.5)), t, 0.6)
    draw_truck_back(d, cam)
    def vis(r, c, k):
        if r != 0: return None
        dz = drop(t, row_T(c, k), 0.3, 70)
        return None if dz is None else (dz, "g")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = 5 + sum(1 for k in range(1, 9) for c in range(5) if t >= row_T(c, k) + 0.3)
    fm = F("mono", 13)
    for k in range(9):
        if k == 0 or t >= row_T(0, k) + 0.3:
            x, y = P(0, WD, k * BH + BH / 2)
            d.text((x - 10 * SS, y), f"lớp {k + 1}", font=fm, fill=GREEN if t < row_T(0, k) + 1.2 or (k == 8) else MUTED, anchor="rm")
    for kk, (a, b) in enumerate([(0.6, 3.3), (3.5, 6.1)], start=2):
        pop(d, (930, 245), f"LỚP {kk}", "serifb", 54, GREEN, t, a, t_out=b)
        kin(d, (930, 298), f"bao {(kk - 1) * 5 + 1}–{kk * 5} · cùng hướng lớp 1", "mono", 18, INK, t, a + 0.3, t_out=b)
        kin(d, (930, 326), "thứ tự: 1 · 3 · 5 · 2 · 4", "monob", 18, ORANGE, t, a + 0.6, t_out=b)
    if 6.3 <= t < 11.2:
        kc = min(9, max(4, 3 + sum(1 for k in range(3, 9) if t >= row_T(0, k))))
        since = t - row_T(0, kc - 1) if kc > 3 else 1
        sc = 1 + 0.25 * (1 - sego(since, 0, 0.3))
        a = seg(t, 6.3, 6.6) * (1 - seg(t, 10.9, 11.2))
        ctext(d, (930, 250), f"LỚP 4 → {kc}", F("serifb", 54 * sc), mix(CREAM, GREEN, a))
    k2 = sego(t, 11.0, 11.8)
    if k2 > 0:
        dim_line(d, P(BL + 22, WD, 0), P(BL + 22, WD, 117 * k2), "cao 117 cm" if k2 > 0.7 else "", RED, F("monob", 15), offset=(62, 0))
    k3 = seg(t, 12.0, 12.6)
    if k3 > 0:
        c = mix(CREAM, INK, k3)
        d.line([P(-5, 0, HWALL), P(BL + 70 * k3, 0, HWALL)], fill=c, width=2 * SS)
        tag(d, P(BL + 110, 0, HWALL), "thành thùng 80 cm", c, F("mono", 14))
        tag(d, P(BL + 110, 0, HWALL + 37), "vượt thành 37 cm", mix(CREAM, RED, k3), F("monob", 14))
    if t > 13.2: stamp(im, "ĐẦY · 45 BAO", t - 13.2, GREEN, (940, 520))
    return finish(im, d, 6, t, "02 · MỘT HÀNG", sub="Lớp nào cũng 1, 3, 5 trước rồi 2, 4; đủ 9 lớp mới sang hàng mới", cnt=n)

def move_T(r, c, k):
    if r == 0: return -1
    if r == 1: return 1.6 + idx_in_row(c, k) * 0.065
    return 6.6 + (r - 2) * 0.55 + idx_in_row(c, k) * (0.45 / 45)

def sc_move(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(Cam(150, -40, 1.6), CAM_FULL, seg(t, 4.6, 6.8)), t)
    draw_truck_back(d, cam)
    cur = 1 if t < 6.6 else min(FULL - 1, 2 + int((t - 6.6) / 0.55))
    def vis(r, c, k):
        if r >= FULL: return None
        dz = drop(t, move_T(r, c, k), 0.25 if r == 1 else 0.14, 60)
        if dz is None: return None
        return (dz, "g" if r == cur and t < 10.6 else "n")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = sum(1 for r, c, k in all_slots() if r < FULL and t >= move_T(r, c, k))
    a = sego(t, 0.3, 1.4)
    if a > 0 and t < 5.2:
        col = mix(CREAM, GREEN, a * (1 - seg(t, 4.6, 5.2)))
        arrow(d, P(BL + 5, WD + 18, 0), P(BL + 5 + 70 * a, WD + 18, 0), col, 4, 14)
        tag(d, P(BL + 40, WD + 45, 0), "lùi 75 cm", col, F("monob", 16))
    if t > 6.4:
        for r in range(FULL):
            if t >= move_T(r, 0, 0):
                tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), GREEN if r == cur and t < 10.6 else INK, F("mono", 12))
        if int(t * 2.5) % 2 == 0 or t > 10.4:
            tag(d, (W * SS / 2, 112 * SS), "VIDEO TUA NHANH >>", RED, F("monob", 15))
    return finish(im, d, 7, t, "03 · LÙI 75 CM", sub="Lùi ra 75 cm, lặp lại 9 lớp cho đến hàng 8", cnt=n)

def layer_counter_card(d, t, title, kc, nmax, col, line1, line2, box=(1010, 210)):
    bx, by = box
    k = card(d, (bx - 160, by - 95, bx + 160, by + 95), t, 0.4, col)
    if k <= 0: return
    ctext(d, (bx, by - 68), title, F("monob", 16), mix(CARD, MUTED, k))
    sc = 1 + 0.3 * (1 - sego((t % 0.6), 0, 0.3)) if kc < nmax else 1
    ctext(d, (bx - 12, by - 8), str(kc), F("serifb", 62 * sc), mix(CARD, col, k), anchor="rm")
    ctext(d, (bx - 4, by - 2), f"/ {nmax} LỚP", F("serifb", 28), mix(CARD, INK, k), anchor="lm")
    ctext(d, (bx, by + 45), line1, F("mono", 15), mix(CARD, INK, k))
    ctext(d, (bx, by + 70), line2, F("monob", 16), mix(CARD, RED, k))

def sc_check1(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(CAM_FULL, Cam(280, 40, 1.15), sego(t, 0, 1.4)), t)
    draw_truck_back(d, cam)
    Tk = lambda k: 0.9 + k * 0.55
    kc = sum(1 for k in range(9) if t >= Tk(k))
    def vis(r, c, k):
        if r >= FULL: return None
        if k < kc:
            return (0, "hl" if k == kc - 1 and t < Tk(8) + 0.6 else "g")
        return (0, "n")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    for r in range(FULL):
        tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), INK, F("mono", 12))
    for k in range(kc):
        x, y = P(FULL * BL + 6, WD, k * BH + BH / 2)
        d.text((x + 8 * SS, y), f"lớp {k + 1}", font=F("monob", 12), fill=GREEN if k == kc - 1 else INK, anchor="lm")
    k2 = sego(t, 6.0, 6.8)
    if k2 > 0:
        dim_line(d, P(-6, WD + 8, 0), P(-6, WD + 8, 117 * k2), "117 cm" if k2 > 0.7 else "", RED, F("monob", 14), offset=(-40, 0))
    layer_counter_card(d, t, "HÀNG 1–8", max(kc, 0), 9, GREEN, "5 bao × 9 lớp = 45 bao", "cao 117 cm")
    return finish(im, d, 8, t, "KIỂM TRA HÀNG 1–8", GREEN, "Hàng 1 đến 8: mỗi hàng chất đủ 9 lớp = 45 bao, cao 117 cm", 360)

def rows2_T(r, c, k):
    i = k * 5 + POS(c)
    if r == FULL: return 1.2 + i * 0.085
    return 5.6 + (r - FULL - 1) * 0.65 + i * (0.5 / 40)

def sc_rows2(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(Cam(480, 40, 1.25), CAM_FULL, seg(t, 4.6, 6.4)), t)
    draw_truck_back(d, cam)
    cur = FULL if t < 5.6 else min(ROWS - 1, FULL + 1 + int((t - 5.6) / 0.65))
    def vis(r, c, k):
        if r < FULL: return (0, "n")
        dz = drop(t, rows2_T(r, c, k), 0.25 if r == FULL else 0.14, 60)
        if dz is None: return None
        return (dz, "g" if r == cur and t < 10.4 else "o")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    n = 360 + sum(1 for r, c, k in all_slots() if r >= FULL and t >= rows2_T(r, c, k))
    for r in range(ROWS):
        if r < FULL or t >= rows2_T(r, 0, 0):
            tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), (GREEN if r == cur and t < 10.4 else (ORANGE if r >= FULL else INK)), F("mono", 12))
    pop(d, (930, 230), "HÀNG 9 → 16", "serifb", 44, ORANGE, t, 0.6, t_out=5.0)
    kin(d, (930, 278), "5 bao × 8 lớp = 40 bao", "mono", 19, INK, t, 1.0, t_out=5.0)
    kin(d, (930, 306), "thứ tự: 1 · 3 · 5 · 2 · 4", "monob", 18, ORANGE, t, 1.4, t_out=5.0)
    if t > 5.4 and (int(t * 2.5) % 2 == 0 or t > 10.2):
        tag(d, (W * SS / 2, 112 * SS), "VIDEO TUA NHANH >>", RED, F("monob", 15))
    return finish(im, d, 9, t, "04 · HÀNG 9–16 · 8 LỚP", ORANGE, "Hàng 9 đến 16: mỗi hàng 5 bao × 8 lớp = 40 bao", n)

def sc_check2(t, D):
    im, d = frame_base()
    cam = breathe(cam_lerp(CAM_FULL, Cam(860, 120, 1.15), sego(t, 0, 1.4)), t)
    draw_truck_back(d, cam)
    Tk = lambda k: 0.9 + k * 0.55
    kc = sum(1 for k in range(8) if t >= Tk(k))
    def vis(r, c, k):
        if r < FULL: return (0, "n")
        return (0, "o" if k < kc else "on")
    draw_bags(d, cam, vis)
    draw_truck_front(d, cam)
    P = cam.P
    for r in range(FULL - 2, ROWS):
        tag(d, P(r * BL + BL / 2, WD + 22, 0), str(r + 1), ORANGE if r >= FULL else INK, F("mono", 12))
    for k in range(kc):
        x, y = P(ROWS * BL + 6, WD, k * BH + BH / 2)
        d.text((x + 8 * SS, y), f"lớp {k + 1}", font=F("monob", 12), fill=ORANGE if k == kc - 1 else INK, anchor="lm")
    k2 = sego(t, 5.6, 6.4)
    if k2 > 0:
        dim_line(d, P(FULL * BL + 4, WD + 8, 0), P(FULL * BL + 4, WD + 8, 104 * k2), "104 cm" if k2 > 0.7 else "", RED, F("monob", 14), offset=(-40, 0))
    k3 = sego(t, 6.8, 7.6)
    if k3 > 0:
        d.line([P(ROWS * BL, WD / 2, 0), P(lerp(ROWS * BL, L, k3), WD / 2, 0)], fill=INK, width=3 * SS)
        pop(d, ((P(L + 20, WD / 2, 0)[0]) / SS + 40, P(L, WD / 2, 0)[1] / SS + 20), "trống 26 cm", "monob", 15, INK, t, 7.0)
    layer_counter_card(d, t, "HÀNG 9–16", max(kc, 0), 8, ORANGE, "5 bao × 8 lớp = 40 bao", "cao 104 cm", box=(1010, 210))
    return finish(im, d, 10, t, "KIỂM TRA HÀNG 9–16", ORANGE, "Hàng 9 đến 16: mỗi hàng chỉ 8 lớp = 40 bao, cao 104 cm", 680)

def sc_tour(t, D):
    im, d = frame_base()
    t0 = 1.2; step = (D - 3.0) / ROWS
    rf = clamp((t - t0) / step, -0.4, ROWS - 1)
    base = math.floor(rf); frac = rf - base
    pos = clamp(base + ss(clamp(frac / 0.6)), 0, ROWS - 1)
    xf = pos * BL + BL / 2
    cam_t = Cam(0.95 * xf - 75 + 120, 0.18 * xf + 48 - 54 + 20, 1.55)
    cam = cam_lerp(CAM_FULL, cam_t, sego(t, 0.0, 1.1))
    cam = breathe(cam_lerp(cam, CAM_FULL, seg(t, D - 1.7, D - 0.3)), t, 0.5)
    cur = min(int(round(pos)), ROWS - 1) if t >= t0 - 0.2 else -1
    draw_truck_back(d, cam)
    draw_bags(d, cam, lambda r, c, k: (0, "g") if r == cur and t < D - 1.6 else (0, "o" if r >= FULL else "n"))
    draw_truck_front(d, cam)
    P = cam.P
    for r in range(cur + 1 if cur >= 0 else 0):
        tag(d, P(r * BL + BL / 2, WD + 24, 0), str(r + 1), GREEN if r == cur else INK, F("monob", 14))
    if 0 <= cur < ROWS and t < D - 1.6:
        x0 = cur * BL; hh = NL(cur) * BH
        dim_line(d, P(x0 + BL / 2, 0, hh + 6), P(x0 + BL / 2, WD, hh + 6), "5 bao", GREEN, F("monob", 15), offset=(0, -16))
        dim_line(d, P(x0, WD + 10, 0), P(x0, WD + 10, hh), f"{NL(cur)} lớp", GREEN, F("monob", 15), offset=(-42, 0))
    done = cur + 1 if cur >= 0 else 0
    cum = sum(COLS * NL(r) for r in range(done))
    since = (t - t0) - max(cur, 0) * step
    pp = 1 + 0.35 * (1 - sego(since, 0, 0.3)) if cur >= 0 else 1
    bx, by = 1010, 200
    k = card(d, (bx - 175, by - 95, bx + 175, by + 115), t, 0.5)
    if k > 0:
        last = cur >= FULL
        ctext(d, (bx, by - 64), "HÀNG", F("monob", 18), mix(CARD, MUTED, k))
        ctext(d, (bx - 30, by - 8), str(done), F("serifb", 64 * pp), mix(CARD, ORANGE if last else GREEN, k), anchor="rm")
        ctext(d, (bx - 20, by - 4), "/ 16", F("serifb", 34), mix(CARD, INK, k), anchor="lm")
        nl = NL(max(cur, 0))
        ctext(d, (bx, by + 48), f"5 bao × {nl} lớp = {5 * nl} bao", F("mono", 17), mix(CARD, ORANGE if last else INK, k))
        ctext(d, (bx, by + 82), f"tổng: {cum} bao" + (" = 34 tấn" if cum == 680 else ""), F("monob", 20), mix(CARD, INK, k))
    if t > D - 1.4: stamp(im, "680 BAO = 34 TẤN", t - (D - 1.4), ORANGE, (640, 140), -4)
    return finish(im, d, 11, t, "KIỂM TRA · ĐẦU → CUỐI XE", sub="8 hàng × 45 bao + 8 hàng × 40 bao = 680 bao", cnt=680)

def sc_stats(t, D):
    im, d = frame_base()
    tiles = [(64, 120), (664, 120), (64, 370), (664, 370)]
    tw, th = 552, 230
    starts = [0.2, 3.7, 8.0, 10.2]
    for i, ((x, y), t0) in enumerate(zip(tiles, starts)):
        k = card(d, (x, y, x + tw, y + th), t, t0)
        if k <= 0: continue
        tt = t - t0
        c = mix(CARD, INK, k)
        if i == 0:
            n = int(round(680 * sego(tt, 0.3, 1.9)))
            ctext(d, (x + 150, y + 70), f"{n} bao", F("serifb", 40), c)
            ctext(d, (x + 150, y + 120), f"= {vn(round(n * 50 / 1000))} tấn", F("serifb", 30), mix(CARD, ORANGE, k))
            ctext(d, (x + 150, y + 175), "20 bao = 1 tấn", F("mono", 14), mix(CARD, MUTED, k))
            gx, gy, cw, ch = x + 300, y + 30, 6.5, 8.5
            for j in range(680):
                col_, row_ = j // 20, j % 20
                px, py = gx + col_ * cw, gy + (19 - row_) * ch
                fill = (GREEN if j < 360 else ORANGE) if j < n else mix(CARD, INK, 0.1)
                d.rectangle([px * SS, py * SS, (px + cw - 1.5) * SS, (py + ch - 1.5) * SS], fill=fill)
        if i == 1:
            kin(d, (x + 150, y + 80), "8 hàng", "serifb", 40, INK, tt, 0.1, bg=CARD)
            kin(d, (x + 150, y + 130), "× 45 bao", "serifb", 30, INK, tt, 0.3, bg=CARD)
            kin(d, (x + 150, y + 178), "+ 8 hàng × 40 bao", "mono", 14, ORANGE, tt, 0.6, bg=CARD)
            bx, by = x + 300, y + 190
            for r in range(16):
                hh = NL(r) * eob((tt - 0.3 - r * 0.09) / 0.4)
                if hh <= 0: continue
                d.rectangle([(bx + r * 14.5) * SS, (by - hh * 16) * SS, (bx + r * 14.5 + 11) * SS, by * SS], fill=GREEN if r < FULL else ORANGE)
            d.line([bx * SS, (by + 1) * SS, (bx + 232) * SS, (by + 1) * SS], fill=INK, width=2 * SS)
        if i == 2:
            kin(d, (x + 150, y + 80), "cao 117 cm", "serifb", 36, INK, tt, 0.1, bg=CARD)
            ctext(d, (x + 150, y + 128), "9 lớp × 13 cm", F("mono", 16), c)
            ctext(d, (x + 150, y + 163), "vượt thành 80 cm: 37 cm", F("mono", 14), mix(CARD, RED, k))
            ctext(d, (x + 150, y + 188), "hàng 9–16: 8 lớp, cao 104 cm", F("mono", 14), mix(CARD, ORANGE, k))
            bx, by = x + 330, y + 205
            nl = min(9, int(9 * seg(tt, 0.3, 1.6) + 0.999)) if tt > 0.3 else 0
            sc_ = 1.45
            for l in range(nl):
                d.rounded_rectangle([bx * SS, (by - (l + 1) * 13 * sc_ + 1.5) * SS, (bx + 150) * SS, (by - l * 13 * sc_) * SS], radius=5 * SS, fill=BAG_TOP, outline=GREEN, width=SS)
            wy = by - 80 * sc_
            d.line([(bx - 20) * SS, wy * SS, (bx + 175) * SS, wy * SS], fill=INK, width=2 * SS)
            d.text(((bx + 178) * SS, wy * SS), "80", font=F("mono", 13), fill=INK, anchor="lm")
            if nl == 9:
                d.text(((bx + 178) * SS, (by - 117 * sc_) * SS), "117", font=F("monob", 13), fill=RED, anchor="lm")
        if i == 3:
            kin(d, (x + 150, y + 80), "trống 26 cm", "serifb", 34, INK, tt, 0.1, bg=CARD)
            ctext(d, (x + 150, y + 128), "sau hàng 16", F("mono", 16), c)
            ctext(d, (x + 150, y + 163), "1.226 − 16 × 75 = 26", F("mono", 14), mix(CARD, MUTED, k))
            bx, by, bw = x + 300, y + 110, 225
            d.rectangle([bx * SS, by * SS, (bx + bw) * SS, (by + 34) * SS], outline=INK, width=2 * SS)
            f1 = sego(tt, 0.3, 1.0); f2 = sego(tt, 1.0, 1.6)
            g8 = bw * 600 / 1226; g16 = bw * 1200 / 1226
            d.rectangle([bx * SS, by * SS, (bx + g8 * f1) * SS, (by + 34) * SS], fill=GREEN)
            if f2 > 0:
                d.rectangle([(bx + g8) * SS, (by + 34 * (1 - 104 / 117)) * SS, (bx + g8 + (g16 - g8) * f2) * SS, (by + 34) * SS], fill=ORANGE)
            if f2 >= 1:
                dim_line(d, ((bx + g16) * SS, (by - 18) * SS), ((bx + bw) * SS, (by - 18) * SS), "", RED, F("mono", 12))
                d.text(((bx + bw) * SS, (by + 52) * SS), "cửa sau", font=F("mono", 12), fill=MUTED, anchor="rm")
                d.text((bx * SS, (by + 52) * SS), "đầu thùng", font=F("mono", 12), fill=MUTED, anchor="lm")
    chapter(im, "SỐ LIỆU", t)
    subtitle(d, "Bốn con số của một xe container bạt 34 tấn", t)
    corners(d); footer(d, 12)
    return im

def sc_end(t, D):
    im, d = frame_base(ORANGE)
    k = segb(t, 0.0, 0.6)
    px0, py0, px1, py1 = 140, 280, 1140, 590
    cy = lerp(800, (py0 + py1) / 2, k); hh = (py1 - py0) / 2
    d.rectangle([px0 * SS, (cy - hh) * SS, px1 * SS, (cy + hh) * SS], fill=CREAM, outline=INK, width=3 * SS)
    cam = breathe(Cam(525, 40, 0.68, dy=80 + (cy - (py0 + py1) / 2)), t, 0.4)
    draw_truck_back(d, cam)
    draw_bags(d, cam, lambda r, c, k_: (0, "o") if r >= FULL else (0, "n"))
    draw_truck_front(d, cam)
    steps = ["1 · 3 · 5", "2 · 4", "đủ lớp", "lùi 75 cm"]
    f = F("serifb", 36)
    widths = [tw_(d, s, f) for s in steps]
    gap = 62
    x = W / 2 - (sum(widths) + gap * 3) / 2
    for i, s in enumerate(steps):
        kk = sego(t, 0.4 + i * 0.45, 0.8 + i * 0.45)
        ctext(d, (x, 130 + 18 * (1 - kk)), s, f, mix(ORANGE, INK, kk), anchor="lm")
        x += widths[i]
        if i < 3:
            ka = sego(t, 0.7 + i * 0.45, 1.0 + i * 0.45)
            if ka > 0: arrow(d, ((x + 12) * SS, 130 * SS), ((x + 12 + (gap - 24) * ka) * SS, 130 * SS), CREAM, 4, 14)
            x += gap
    kin(d, (W / 2, 198), "8 hàng × 45 bao (9 lớp) · 8 hàng × 40 bao (8 lớp) · trống 26 cm", "serif", 22, INK, t, 2.4, step=0.04, bg=ORANGE)
    kin(d, (W / 2, 243), "Làm đúng trình tự này cho mọi xe container bạt 34 tấn", "serifb", 24, CREAM, t, 3.4, step=0.06, bg=ORANGE)
    ctext(d, (W / 2, 632), "Nguồn: cách chất theo xác nhận kho PC (KCP) · thùng 1.226 × 235 × 215 cm · bao 75 × 50 × 13 cm, 50 kg",
          F("mono", 13), mix(ORANGE, INK, seg(t, 4.2, 4.8)))
    corners(d, INK); footer(d, 13, INK)
    return im

# mốc cảnh khớp giọng đọc gốc (giây)
BOUNDS = [0.0, 6.6, 14.2, 22.0, 39.2, 46.2, 62.2, 74.2, 83.4, 95.7, 105.6, 121.1, 134.4, 143.2]
FNS = [sc_hook, sc_map, sc_bag, sc_section, sc_layer_a, sc_row, sc_move, sc_check1,
       sc_rows2, sc_check2, sc_tour, sc_stats, sc_end]
SCENES = [(fn, BOUNDS[i + 1] - BOUNDS[i]) for i, fn in enumerate(FNS)]
WIPE = 0.55  # giây chuyển cảnh quét chéo

def scene_at(t_abs, si):
    global G_T
    G_T = t_abs
    fn, D = SCENES[si]
    return fn(t_abs - BOUNDS[si], D)

def wipe(prev, nxt, p, bar1=ORANGE, bar2=INK):
    """quét chéo trái → phải: phía trái mép là cảnh mới"""
    Wp, Hp = W * SS, H * SS
    slant = 220 * SS
    e = lerp(-slant - 60 * SS, Wp + 60 * SS, eoc(p) if p > 0.5 else ss(p))
    m = Image.new("L", (Wp, Hp), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (e + slant, 0), (e, Hp), (0, Hp)], fill=255)
    out = Image.composite(nxt, prev, m)
    d = ImageDraw.Draw(out)
    for off, w, col in ((0, 26, bar1), (26, 12, bar2)):
        a = e + off * SS
        d.polygon([(a + slant, 0), (a + slant + w * SS, 0), (a + w * SS, Hp), (a, Hp)], fill=col)
    return out

def render(i_frame):
    t_abs = i_frame / FPS
    si = max(i for i in range(len(SCENES)) if BOUNDS[i] <= t_abs) if t_abs < BOUNDS[-1] else len(SCENES) - 1
    im = scene_at(t_abs, si)
    if si > 0 and t_abs - BOUNDS[si] < WIPE:
        prev = scene_at(t_abs, si - 1)
        im = wipe(prev, im, (t_abs - BOUNDS[si]) / WIPE)
    # vào/ra mờ
    if t_abs < 0.4 or t_abs > BOUNDS[-1] - 0.5:
        k = clamp(t_abs / 0.4) if t_abs < 0.4 else clamp((BOUNDS[-1] - t_abs) / 0.5)
        im = Image.blend(Image.new("RGB", im.size, INK), im, k)
    return im.resize((W, H), Image.LANCZOS).tobytes()

def total_frames(): return int(round(BOUNDS[-1] * FPS))

def test_sheet(path="test_sheet.png"):
    picks = []
    for i in range(len(SCENES)):
        a, b = BOUNDS[i], BOUNDS[i + 1]
        for f in (0.3, 0.6, 0.95):
            picks.append(int((a + (b - a) * f) * FPS))
    with Pool(4) as pool:
        tiles = [Image.frombytes("RGB", (W, H), b).resize((640, 360), Image.LANCZOS) for b in pool.map(render, picks)]
    cols = 3; rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (640 * cols, 360 * rows), "white")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(path); print("saved", path)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "test":
        test_sheet(sys.argv[2] if len(sys.argv) > 2 else "test_sheet.png")
    elif mode == "frame":
        Image.frombytes("RGB", (W, H), render(int(float(sys.argv[2]) * FPS))).save(sys.argv[3])
    else:
        audio = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else "Chat_xa_34T_kho_PC_motion.mp4"
        n = total_frames()
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                              "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
                              "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, b in enumerate(pool.imap(render, range(n), chunksize=8)):
                p.stdin.write(b)
                if i % 250 == 0: print(f"{i}/{n}", flush=True)
        p.stdin.close(); p.wait()
        print("done", out, flush=True)
