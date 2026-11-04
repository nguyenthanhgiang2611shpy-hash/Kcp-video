# -*- coding: utf-8 -*-
"""Video: Cách hoạt động của máy DEPAL bao tự động (Phon-Tech) – KCP Phú Yên.
Nguồn: bản vẽ LA26-PTC-KCP-DEP-301026, Phon-Tech, ngày 20/10/2026 (SCALE: FREE).
Đã chốt với Phòng Logistics:
  - thùng xe: băng tải ống lồng vươn ra/thụt vào, tự rải bao trái→phải, chất 9 lớp; không dùng người (Phon-Tech xác nhận, 04/11/2026)
  - công nhân khu depal: giữ nguyên theo bản vẽ
  - sling vào từ hai bên, luân phiên
  - băng tải phía dưới + lưới 3x3 + 1 công nhân = trạm xả tay dự phòng
  - sling rỗng đi đâu, phương tiện đưa sling vào: CHƯA RÕ (ghi trong video)
Tọa độ thế giới = pixel của ảnh bản vẽ ở 110 dpi (1 px ≈ 23,1 mm).
Chạy:  python3 make_depal.py            -> render đầy đủ: MỘT video duy nhất, nén sẵn để gửi email (960x540)
       python3 make_depal.py test       -> contact sheet khung mẫu
       python3 make_depal.py frame 12.5 out.png
"""
import sys, math, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 1280, 720, 2, 25
OUT = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "full" else "Depal_cach_hoat_dong_v3.mp4"

# ---------- màu ----------
CREAM = (243, 236, 220); INK = (29, 43, 58); ORANGE = (217, 119, 75)
RED = (178, 52, 44); MUTED = (110, 116, 120)
BAG_TOP = (252, 250, 244); BAG_LOW = (214, 206, 188)
PERSON = (196, 104, 124)

# mỗi thiết bị một màu, dùng nhất quán mọi nơi
BLUE = (44, 95, 160); PURPLE = (118, 74, 150); BRICK = (176, 64, 48)
GREEN = (38, 122, 64); GOLD = (176, 128, 10); TEAL = (16, 124, 128)
NAVY = (29, 43, 58); MAG = (160, 48, 108); OLIVE = (96, 104, 20)
FORK_Y = (222, 168, 44)

EL = {  # mã: (số, tên, loại, tác dụng, màu)
    "L": (1, "Băng con lăn sling – trái", "băng tải con lăn · 3 vị trí", "nhận 2 sling đầy từ xe nâng, trả sling rỗng ra", BLUE),
    "R": (2, "Băng con lăn sling – phải", "băng tải con lăn · 3 vị trí", "như bên trái, chạy luân phiên với bên trái", PURPLE),
    "C": (3, "Cell robot – máy hút chân không", "đầu hút chân không, 3 bao/lần", "hút 1 hàng 3 bao, thả lần lượt từng bao lên băng", BRICK),
    "V": (4, "Băng tải vệ sinh bao", "băng tải có chổi quét", "quét sạch bụi bẩn trên bao", OLIVE),
    "S": (5, "Băng tải ra (đoạn thẳng)", "băng tải", "đưa bao ra khỏi cell", GREEN),
    "K": (6, "Băng cong 90°", "băng tải cong", "đổi hướng bao về phía xe", GOLD),
    "T": (7, "Băng tải ống lồng", "vươn ra / thụt vào, tối đa 18 m, có cảm biến", "tự rải bao trái → phải, chất 9 lớp, lùi từng hàng", TEAL),
    "X": (8, "Thùng xe", "xe container bạt 34T", "nhận 680 bao = 34 tấn, không cần người xếp", NAVY),
    "M": (9, "Trạm xả tay dự phòng", "băng tải + 1 công nhân", "khi robot không chạy: xếp tay bao, đi thẳng qua cell", MAG),
}

# ---------- số liệu (bản vẽ) ----------
MM = 13258 / (910 - 337)            # mm trên 1 px bản vẽ
BAG_W, BAG_L, BAG_T = 500, 750, 150  # bao đầy trên bản vẽ (mm)
KCP_T = 130                          # KCP đo: bao 75 x 50 x 13 cm (Trình tự chất bao xe 34T v2)
SL_L, SL_W = 2250, 1500              # sling (mm)
PER_LAYER, LAYERS = 9, 5
NBAG = PER_LAYER * LAYERS
assert NBAG == 45 and NBAG * 50 == 2250
assert 3 * BAG_L == SL_L and 3 * BAG_W == SL_W
assert LAYERS * BAG_T == 750 and LAYERS * KCP_T == 650
assert 13258 - 11755 == 1503 and 3954 + 9950 == 13904 and 5090 + 4859 == 9949
BW, BL = BAG_W / MM, BAG_L / MM      # bao trong thế giới (px)
SW, SLL = SL_W / MM, SL_L / MM       # sling 65 x 97 px

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
def lin(t, t0, t1): return clamp((t - t0) / (t1 - t0))
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))
def vn(n): return f"{n:,}".replace(",", ".")

class Cam:
    def __init__(s, cx, cy, z): s.cx, s.cy, s.z = cx, cy, z
    def P(s, x, y): return ((x - s.cx) * s.z * SS + W * SS / 2, (y - s.cy) * s.z * SS + H * SS / 2)
    def S(s, v): return v * s.z * SS
    def scr(s, x, y):  # tọa độ màn hình 1x
        p = s.P(x, y); return (p[0] / SS, p[1] / SS)

def cam_lerp(a, b, k): return Cam(lerp(a.cx, b.cx, k), lerp(a.cy, b.cy, k), lerp(a.z, b.z, k))

CAM_FULL = Cam(1000, 728, 0.6)
CAM_ROW = Cam(625, 835, 1.7)
CAM_CELL = Cam(628, 758, 1.9)
CAM_TRUCK = Cam(1400, 372, 2.7)
CAM_BOT = Cam(628, 1000, 1.55)
CAM_FLOW = Cam(560, 835, 1.45)

def LW(w): return max(1, int(round(w * SS)))

# ---------- hình học thế giới ----------
CY = 847.5                       # tâm hàng sling
POS_C = (627.5, CY)              # vị trí xả giữa cell
POS_L = [(375, CY), (455, CY), (536, CY)]
POS_R = [(875, CY), (792, CY), (723, CY)]
BELT_X = 628; BELT_HALF = 14
ROBOT_BASE = (628, 768)
PLACE = (628, 708)
CURVE_C, CURVE_R = (683, 400), 55
TELE_END = 1488
TRUCK = (1132, 293, 1540, 397)
STATION = (562, 1053, 695, 1158)

def arc_pts(c, r, a0, a1, n=24):
    return [(c[0] + r * math.cos(math.radians(lerp(a0, a1, i / n))),
             c[1] + r * math.sin(math.radians(lerp(a0, a1, i / n)))) for i in range(n + 1)]

PATH = {
    "L": [(342, CY), (568, CY)],
    "R": [(908, CY), (692, CY)],
    "V": [(BELT_X, 660), (BELT_X, 597)],
    "S": [(BELT_X, 597), (BELT_X, 400)],
    "K": arc_pts(CURVE_C, CURVE_R, 180, 270),
    "T": [(683, 345), (TELE_END, 345)],
    "M": [(BELT_X, 1050), (BELT_X, 914)],
}
OUT_PATH = [PLACE] + PATH["V"] + PATH["S"][1:] + PATH["K"][1:] + PATH["T"][1:]

def plen(pts): return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

def ppoint(pts, s):
    """điểm và hướng (rad) tại quãng đường s trên polyline"""
    for i in range(len(pts) - 1):
        L = math.dist(pts[i], pts[i + 1])
        if s <= L or i == len(pts) - 2:
            k = clamp(s / L) if L else 0
            a = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
            return (lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)), a
        s -= L
    return pts[-1], 0.0

def sub_path(pts, k):
    L = plen(pts) * clamp(k); out = [pts[0]]; acc = 0
    for i in range(len(pts) - 1):
        l = math.dist(pts[i], pts[i + 1])
        if acc + l >= L:
            f = (L - acc) / l if l else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)))
            return out
        out.append(pts[i + 1]); acc += l
    return out

L_SEG = {k: plen(PATH[k]) for k in ("V", "S", "K", "T")}
L_OUT = plen(OUT_PATH)

# ---------- vẽ cơ bản ----------
def wrect(d, cam, b, fill=None, outline=None, w=1.5, r=0):
    p0 = cam.P(b[0], b[1]); p1 = cam.P(b[2], b[3])
    box = [min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])]
    if r: d.rounded_rectangle(box, radius=cam.S(r), fill=fill, outline=outline, width=LW(w) if outline else 0)
    else: d.rectangle(box, fill=fill, outline=outline, width=LW(w) if outline else 0)

def wline(d, cam, pts, color, w=1.5):
    d.line([cam.P(*p) for p in pts], fill=color, width=LW(w), joint="curve")

def wpoly(d, cam, pts, fill=None, outline=None, w=1.5):
    d.polygon([cam.P(*p) for p in pts], fill=fill, outline=outline, width=LW(w) if outline else 0)

def dashed(d, p0, p1, fill, width=2, dash=8, gap=6):
    x0, y0 = p0; x1, y1 = p1
    ln = math.hypot(x1 - x0, y1 - y0)
    if ln < 1: return
    n = 0.0
    while n < ln:
        a = n / ln; b = min(n + dash * SS, ln) / ln
        d.line([(lerp(x0, x1, a), lerp(y0, y1, a)), (lerp(x0, x1, b), lerp(y0, y1, b))], fill=fill, width=LW(width))
        n += (dash + gap) * SS

def arrow(d, p0, p1, fill, width=3, head=12):
    d.line([p0, p1], fill=fill, width=LW(width))
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); h = head * SS
    d.polygon([p1, (p1[0] - h * math.cos(ang - 0.45), p1[1] - h * math.sin(ang - 0.45)),
               (p1[0] - h * math.cos(ang + 0.45), p1[1] - h * math.sin(ang + 0.45))], fill=fill)

def rot_rect(c, l, w, a):
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for dx, dy in ((l / 2, w / 2), (l / 2, -w / 2), (-l / 2, -w / 2), (-l / 2, w / 2)):
        out.append((c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca))
    return out

def draw_bag(d, cam, c, a=-math.pi / 2, fill=BAG_TOP, edge=INK, alpha_k=1.0):
    """bao nhìn từ trên: a = hướng trục dài; vạch may ở một đầu"""
    fill = mix(CREAM, fill, alpha_k); edge = mix(CREAM, edge, alpha_k)
    pts = rot_rect(c, BL * 0.94, BW * 0.9, a)
    wpoly(d, cam, pts, fill=fill, outline=edge, w=1.2 * min(1, cam.z / 1.5) + 0.3)
    # vạch may
    s = rot_rect((c[0] + math.cos(a) * BL * 0.36, c[1] + math.sin(a) * BL * 0.36), 0.1, BW * 0.75, a)
    wline(d, cam, [s[0], s[1]], mix(CREAM, MUTED, alpha_k), 1)

def draw_person(d, cam, c, face=0.0, color=PERSON, k=1.0):
    col = mix(CREAM, color, k)
    sh = rot_rect(c, 12, 26, face)          # vai (khoảng 450 mm)
    wpoly(d, cam, sh, fill=mix(CREAM, col, 0.35), outline=col, w=1.2)
    p = cam.P(*c); r = cam.S(5.5)
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=mix(CREAM, col, 0.6), outline=col, width=LW(1.2))

def hatch(d, cam, b, color=(80, 190, 200)):
    wrect(d, cam, b, fill=mix(CREAM, color, 0.15))
    for i in range(-12, 14, 3):
        wline(d, cam, [(b[0] + max(0, i), b[1] + max(0, -i)), (b[0] + min(b[2] - b[0], i + (b[3] - b[1])), b[1] + min(b[3] - b[1], (b[2] - b[0]) - i))], mix(CREAM, color, 0.8), 0.8)

# ---------- băng tải ----------
def roller(d, cam, b, color, k=0.0, horiz=True, pitch=5.5):
    wrect(d, cam, b, fill=mix(CREAM, color, 0.10 + 0.08 * k))
    if horiz:
        x = b[0] + pitch / 2
        while x < b[2]:
            wline(d, cam, [(x, b[1] + 3), (x, b[3] - 3)], mix(CREAM, color, 0.38), 1)
            x += pitch
    else:
        y = b[1] + pitch / 2
        while y < b[3]:
            wline(d, cam, [(b[0] + 3, y), (b[2] - 3, y)], mix(CREAM, color, 0.38), 1)
            y += pitch
    wrect(d, cam, b, outline=color, w=1.6 + 1.6 * k)

def belt(d, cam, b, color, k=0.0, chevron=False):
    wrect(d, cam, b, fill=mix(CREAM, color, 0.16 + 0.08 * k), outline=color, w=1.6 + 1.6 * k)
    if chevron:
        y = b[1] + 4
        cx = (b[0] + b[2]) / 2
        while y < b[3] - 6:
            wline(d, cam, [(b[0] + 3, y + 5), (cx, y), (b[2] - 3, y + 5)], mix(CREAM, color, 0.45), 0.8)
            y += 9

def curve(d, cam, color, k=0.0):
    c, r = CURVE_C, CURVE_R
    outer = arc_pts(c, r + BELT_HALF, 180, 270); inner = arc_pts(c, r - BELT_HALF, 270, 180)
    wpoly(d, cam, outer + inner, fill=mix(CREAM, color, 0.16 + 0.08 * k), outline=color, w=1.6 + 1.6 * k)
    for a in range(186, 270, 9):
        p0 = (c[0] + (r - BELT_HALF + 2) * math.cos(math.radians(a)), c[1] + (r - BELT_HALF + 2) * math.sin(math.radians(a)))
        p1 = (c[0] + (r + BELT_HALF - 2) * math.cos(math.radians(a)), c[1] + (r + BELT_HALF - 2) * math.sin(math.radians(a)))
        wline(d, cam, [p0, p1], mix(CREAM, color, 0.4), 0.8)

def tele(d, cam, color, k=0.0):
    for b, f in (((683, 328, 1100, 362), 0.10), ((1095, 330, 1292, 360), 0.16), ((1288, 332, TELE_END + 4, 358), 0.22)):
        wrect(d, cam, b, fill=mix(CREAM, color, f + 0.08 * k), outline=color, w=1.5 + 1.5 * k)
        x = b[0] + 8
        while x < b[2] - 4:
            wline(d, cam, [(x, b[1] + 3), (x - 5, (b[1] + b[3]) / 2), (x, b[3] - 3)], mix(CREAM, color, 0.32), 0.7)
            x += 12

def truck(d, cam, k=0.0):
    x0, y0, x1, y1 = TRUCK
    wrect(d, cam, TRUCK, fill=mix(CREAM, NAVY, 0.06), outline=NAVY, w=2 + 1.5 * k)
    # cabin (đầu xe bên phải)
    cab = [(1540, 304), (1600, 304), (1606, 300), (1665, 300), (1682, 318), (1682, 372), (1665, 390), (1606, 390), (1600, 386), (1540, 386)]
    wpoly(d, cam, cab, fill=mix(CREAM, NAVY, 0.14), outline=NAVY, w=1.8)
    wrect(d, cam, (1606, 312, 1668, 378), outline=mix(CREAM, NAVY, 0.6), w=1, r=6)

def cell(d, cam, k=0.0, gray=False):
    col = mix(BRICK, MUTED, 0.85) if gray else BRICK
    # hàng rào (đường cam trên bản vẽ)
    fence = [(500, 770), (556, 770), (556, 715), (700, 715), (700, 770), (748, 770), (748, 925), (500, 925), (500, 770)]
    for i in range(len(fence) - 1):
        dashed(d, cam.P(*fence[i]), cam.P(*fence[i + 1]), mix(CREAM, ORANGE, 0.7), 1.2, 6, 5)
    wrect(d, cam, (570, 720, 690, 912), outline=col, w=1.6 + 1.6 * k)
    wrect(d, cam, (574, 724, 686, 908), outline=mix(CREAM, col, 0.35), w=0.8)
    wrect(d, cam, (594, 797, 661, 900), fill=mix(CREAM, col, 0.06 + 0.06 * k), outline=mix(CREAM, col, 0.55), w=1)

def station(d, cam, k=0.0):
    wrect(d, cam, STATION, fill=mix(CREAM, MAG, 0.05), outline=MAG, w=1.6 + 1.4 * k)
    hatch(d, cam, (583, 1060, 605, 1076), (120, 120, 120))
    hatch(d, cam, (660, 1060, 682, 1076), (120, 120, 120))

# ---------- sling ----------
def sling_slots(c, rot=False):
    """9 vị trí bao trong 1 lớp. rot=False: trục dài bao theo N-S (sling 65 x 97)"""
    out = []
    for r in range(3):
        for col in range(3):
            if not rot:
                out.append(((c[0] + (col - 1) * SW / 3, c[1] + (r - 1) * SLL / 3), -math.pi / 2))
            else:
                out.append(((c[0] + (col - 1) * SLL / 3, c[1] + (r - 1) * SW / 3), 0.0))
    return out

def draw_sling(d, cam, c, n=NBAG, rot=False, k=1.0, empty_style=False, hole=None, fill_first=False):
    """n = số bao còn trên sling (lớp trên cùng có thể thiếu). hole: chỉ số bao đang được gắp (ẩn)"""
    w, h = (SW, SLL) if not rot else (SLL, SW)
    b = (c[0] - w / 2 - 2, c[1] - h / 2 - 2, c[0] + w / 2 + 2, c[1] + h / 2 + 2)
    base = mix(CREAM, (180, 166, 130), 0.55 * k)
    wrect(d, cam, b, fill=mix(CREAM, base, 0.5), outline=mix(CREAM, INK, k * (0.5 if empty_style else 0.9)), w=1.4, r=4)
    # quai sling ở 4 góc
    for sx, sy in ((b[0], b[1]), (b[2], b[1]), (b[0], b[3]), (b[2], b[3])):
        p = cam.P(sx, sy); r = cam.S(2.6)
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=mix(CREAM, INK, k * 0.8), width=LW(1))
    if n <= 0: return
    full_below = (n - 1) // PER_LAYER
    top = n - full_below * PER_LAYER
    slots = sling_slots(c, rot)
    for i, (p, a) in enumerate(slots):
        gone = (i >= top) if fill_first else (i < PER_LAYER - top)
        if gone:   # bao lớp trên đã gắp -> thấy lớp dưới
            if full_below > 0:
                draw_bag(d, cam, p, a, fill=BAG_LOW, edge=mix(INK, CREAM, 0.35), alpha_k=k)
        else:
            if hole is not None and i == hole:
                if full_below > 0: draw_bag(d, cam, p, a, fill=BAG_LOW, edge=mix(INK, CREAM, 0.35), alpha_k=k)
                continue
            draw_bag(d, cam, p, a, alpha_k=k)

# ---------- robot ----------
L1 = L2 = 60
def ik(base, tgt):
    dx, dy = tgt[0] - base[0], tgt[1] - base[1]
    dd = clamp(math.hypot(dx, dy), 1, L1 + L2 - 0.5)
    a = math.atan2(dy, dx)
    cb = clamp((L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd), -1, 1)
    best = None
    for sg in (1, -1):          # chọn phía khuỷu nằm gần trục giữa cell
        e = a + sg * math.acos(cb)
        p = (base[0] + L1 * math.cos(e), base[1] + L1 * math.sin(e))
        if best is None or abs(p[0] - base[0]) + (0 if p[1] < base[1] + 20 else 30) < abs(best[0] - base[0]) + (0 if best[1] < base[1] + 20 else 30):
            best = p
    return best

def draw_robot(d, cam, tgt, carry=False, suction=0.0, gray=False, labels=False):
    """đầu hút chân không 3 bao (1 hàng ngang 1,5 m); carry = danh sách bao đang hút (0,1,2)"""
    col = mix(BRICK, MUTED, 0.85) if gray else BRICK
    carry = [0, 1, 2] if carry is True else (list(carry) if carry else [])
    offs = [-SW / 3, 0.0, SW / 3]
    b = ROBOT_BASE
    el = ik(b, tgt)
    wline(d, cam, [b, el], mix(CREAM, col, 0.85), 7)
    wline(d, cam, [el, tgt], mix(CREAM, col, 0.85), 5)
    wline(d, cam, [b, el, tgt], col, 1.2)
    for p, r in ((b, 9), (el, 5)):
        q = cam.P(*p); rr = cam.S(r)
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=mix(CREAM, col, 0.55), outline=col, width=LW(1.4))
    for j in carry:
        draw_bag(d, cam, (tgt[0] + offs[j], tgt[1]), -math.pi / 2)
        if labels:
            q = cam.P(tgt[0] + offs[j], tgt[1])
            d.text(q, str(j + 1), font=F("monob", max(9, int(cam.z * 6))), fill=BRICK, anchor="mm")
    g = rot_rect(tgt, SW * 0.98, BL * 0.6, 0.0)
    wpoly(d, cam, g, outline=col, w=1.8)
    for j in range(3):
        for dy in (-BL * 0.16, BL * 0.16):
            q = cam.P(tgt[0] + offs[j], tgt[1] + dy); rr = cam.S(3.0)
            on = suction > 0.5 or j in carry
            fc = (60, 200, 90) if on else mix((60, 200, 90), CREAM, 0.7)
            d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=fc, outline=col, width=LW(1))

def draw_forklift(d, cam, c, ang=0.0):
    """xe nâng nhìn từ trên, càng nâng hướng theo ang"""
    ca, sa = math.cos(ang), math.sin(ang)
    def Lp(x, y): return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)
    def R(x0, y0, x1, y1): return [Lp(x0, y0), Lp(x1, y0), Lp(x1, y1), Lp(x0, y1)]
    for fy in (-14, 10):
        wpoly(d, cam, R(24, fy, 84, fy + 4), fill=(70, 70, 70))                        # càng nâng
    wpoly(d, cam, R(18, -24, 24, 24), fill=INK)                                          # khung nâng
    for wx, wy in ((8, -27), (8, 21), (-30, -27), (-30, 21)):
        wpoly(d, cam, R(wx, wy, wx + 12, wy + 6), fill=INK)                              # bánh xe
    wpoly(d, cam, R(-30, -21, 18, 21), fill=FORK_Y, outline=INK, w=1.2)                  # thân
    wpoly(d, cam, R(-40, -20, -29, 20), fill=mix(INK, FORK_Y, 0.35), outline=INK, w=1)   # đối trọng
    wpoly(d, cam, R(-12, -7, -2, 7), fill=(60, 60, 60))                                  # ghế lái
    wpoly(d, cam, R(-16, -19, 12, 19), outline=INK, w=1.5)                               # khung bảo vệ
    wline(d, cam, [Lp(-16, -19), Lp(12, 19)], INK, 0.8); wline(d, cam, [Lp(-16, 19), Lp(12, -19)], INK, 0.8)

def draw_button(d, cam, p, k):
    q = cam.P(*p); r = cam.S(4.5)
    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=(60, 160, 80), outline=INK, width=LW(1))
    if 0 < k < 1:
        rr = cam.S(4.5 + 10 * k)
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=mix(RED, CREAM, k), width=LW(2))

# ---------- toàn bộ mặt bằng ----------
def draw_plant(d, cam, st):
    hl = st.get("hl", {}); dim = st.get("dim", {})
    def K(n): return hl.get(n, 0.0)
    # lối đi + công nhân hai bên (theo bản vẽ)
    for b in ((350, 770, 500, 792), (350, 904, 500, 926), (752, 770, 905, 792), (752, 904, 905, 926)):
        wrect(d, cam, b, outline=mix(CREAM, INK, 0.45), w=1)
    for b in ((380, 773, 396, 789), (380, 907, 396, 923), (860, 773, 876, 789), (860, 907, 876, 923)):
        hatch(d, cam, b)
    roller(d, cam, (340, 800, 568, 895), EL["L"][4], K("L"))
    roller(d, cam, (690, 800, 910, 895), EL["R"][4], K("R"))
    for x in (420, 500): wline(d, cam, [(x, 800), (x, 895)], mix(CREAM, EL["L"][4], 0.7), 1.2)
    for x in (757, 834): wline(d, cam, [(x, 800), (x, 895)], mix(CREAM, EL["R"][4], 0.7), 1.2)
    cell(d, cam, K("C"), st.get("robot_gray", False))
    belt(d, cam, (BELT_X - BELT_HALF, 400, BELT_X + BELT_HALF, 597), EL["S"][4], K("S"))
    belt(d, cam, (BELT_X - BELT_HALF, 660, BELT_X + BELT_HALF, 735), MUTED, 0)          # đoạn nhận bao trong cell
    for ax, ay, sx in ((606, 684, -1), (650, 684, 1), (606, 712, -1), (650, 712, 1)):    # 4 tay xám (chưa rõ tên)
        wline(d, cam, [(ax, ay), (ax + sx * 10, ay + 3)], mix(CREAM, MUTED, 0.6), 2)
        q = cam.P(ax, ay); rr = cam.S(3)
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=mix(CREAM, MUTED, 0.8), width=LW(1))
    vcol = EL["V"][4]; kv = K("V")
    wrect(d, cam, (BELT_X - 17, 597, BELT_X + 17, 660), fill=mix(CREAM, vcol, 0.12 + 0.08 * kv), outline=vcol, w=1.4 + 1.4 * kv)
    ph = st.get("brush", 0.0)
    for yb in (608, 628, 648):                                                            # chổi quét
        wline(d, cam, [(BELT_X - 16, yb), (BELT_X + 16, yb)], mix(CREAM, vcol, 0.85), 1.6)
        for i in range(9):
            x = BELT_X - 15 + ((i * 3.6 + ph * 18) % 31)
            wline(d, cam, [(x, yb - 4.5), (x + 1.8, yb + 4.5)], mix(CREAM, vcol, 0.6), 0.8)
    curve(d, cam, EL["K"][4], K("K"))
    tele(d, cam, EL["T"][4], K("T"))
    truck(d, cam, K("X"))
    belt(d, cam, (BELT_X - BELT_HALF, 912, BELT_X + BELT_HALF, 1053), EL["M"][4], K("M"), chevron=True)
    station(d, cam, K("M"))
    if not st.get("no_station_sling"):
        draw_sling(d, cam, (629, 1115), st.get("station_n", NBAG), rot=True, k=st.get("station_k", 0.55))
    for p_, f_ in st.get("people", [((462, 781), 0), ((462, 915), 0), ((795, 781), math.pi), ((795, 915), math.pi), ((650, 1068), -math.pi / 2)]):
        draw_person(d, cam, p_, f_)
    for p_, k_ in st.get("buttons", []):
        draw_button(d, cam, p_, k_)
    for p_, a_ in st.get("forklifts", []):
        draw_forklift(d, cam, p_, a_)
    # sling
    for s in st.get("slings", []):
        draw_sling(d, cam, s[0], s[1], k=s[2] if len(s) > 2 else 1.0, hole=s[3] if len(s) > 3 else None)
    # bao trong thùng xe
    for p_, a_ in st.get("truck_bags", []):
        draw_bag(d, cam, p_, a_)
    for p_, a_ in st.get("truck_people", []):
        draw_person(d, cam, p_, a_, color=NAVY)
    # bao trên băng
    for p_, a_ in st.get("bags", []):
        draw_bag(d, cam, p_, a_)
    if st.get("robot") is not None:
        rb = st["robot"]
        draw_robot(d, cam, rb[0], rb[1], rb[2], st.get("robot_gray", False), labels=st.get("robot_labels", False))
    # vạch chạy dọc băng tải (đầu/cuối)
    for n, kk in st.get("bars", {}).items():
        run_bar(d, cam, n, kk)

def run_bar(d, cam, n, k):
    if k <= 0: return
    col = EL[n][4]
    if n in ("C", "X"):
        b = (590, 793, 665, 904) if n == "C" else (TRUCK[0] - 4, TRUCK[1] - 4, TRUCK[2] + 4, TRUCK[3] + 4)
        pts = [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3]), (b[0], b[1])]
        sp = sub_path(pts, k)
        if len(sp) > 1: d.line([cam.P(*p) for p in sp], fill=col, width=LW(3.5), joint="curve")
        return
    pts = PATH[n]
    # lệch ra bên cạnh băng tải
    off = {"L": (0, -32), "R": (0, -32), "V": (-24, 0), "S": (-22, 0), "K": None, "T": (0, -26), "M": (-22, 0)}[n]
    if n == "K":
        pts = arc_pts(CURVE_C, CURVE_R + 22, 180, 270)
    else:
        pts = [(p[0] + off[0], p[1] + off[1]) for p in pts]
    sp = sub_path(pts, k)
    if len(sp) > 1: d.line([cam.P(*p) for p in sp], fill=col, width=LW(3.5), joint="curve")
    # dấu đầu và cuối
    def tick(p, a):
        nx, ny = -math.sin(a), math.cos(a); h = 7 / max(cam.z, 0.3)
        d.line([cam.P(p[0] - nx * h, p[1] - ny * h), cam.P(p[0] + nx * h, p[1] + ny * h)], fill=col, width=LW(3))
    a0 = math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])
    tick(pts[0], a0)
    if k >= 1:
        a1 = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
        tick(pts[-1], a1)
        q = cam.P(*pts[-1])
        ang = a1; h = 9 * SS
        d.polygon([(q[0] + math.cos(ang) * h, q[1] + math.sin(ang) * h),
                   (q[0] - math.sin(ang) * h * 0.5, q[1] + math.cos(ang) * h * 0.5),
                   (q[0] + math.sin(ang) * h * 0.5, q[1] - math.cos(ang) * h * 0.5)], fill=col)

# ---------- khung chung ----------
def frame_base(bg=CREAM):
    im = Image.new("RGB", (W * SS, H * SS), bg)
    return im, ImageDraw.Draw(im)

def corners(d, color=INK):
    m, ln = 22 * SS, 34 * SS
    for (x, y, sx, sy) in ((m, m, 1, 1), (W * SS - m, m, -1, 1), (m, H * SS - m, 1, -1), (W * SS - m, H * SS - m, -1, -1)):
        d.line([(x, y), (x + sx * ln, y)], fill=color, width=3 * SS)
        d.line([(x, y), (x, y + sy * ln)], fill=color, width=3 * SS)

N_SC = 13
def footer(d, n, color=INK):
    f = F("mono", 12)
    d.text((66 * SS, 692 * SS), "KCP VIỆT NAM · LOGISTICS · MÁY DEPAL BAO · bản vẽ 20/10/2026 · Phon-Tech 04/11/2026", font=f, fill=color, anchor="ls")
    d.text((1214 * SS, 692 * SS), f"minh họa, không theo tỷ lệ · {n}/{N_SC}", font=f, fill=color, anchor="rs")

def chapter(im, label, t, color=INK):
    k = seg(t, 0.0, 0.4)
    if k <= 0: return
    f = F("monob", 18)
    dd = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = int(dd.textlength(label, font=f)); pad = 14 * SS
    lab = Image.new("RGBA", (tw + 2 * pad, 40 * SS), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lab)
    dl.rectangle([0, 0, lab.width, lab.height], fill=color + (255,))
    dl.text((pad, lab.height // 2), label, font=f, fill=CREAM, anchor="lm")
    lab = lab.rotate(2.0, expand=True, resample=Image.BICUBIC)
    x = int(lerp(-lab.width, 44 * SS, k))
    im.paste(lab, (x, 40 * SS), lab)

def subtitle(d, s, t, color=INK, y=640, t0=0.15):
    k = seg(t, t0, t0 + 0.45)
    if k <= 0: return
    f = F("serif", 26)
    size = 26
    while d.textlength(s, font=f) > 1120 * SS and size > 16:
        size -= 1; f = F("serif", size)
    tw = d.textlength(s, font=f) / SS
    d.rounded_rectangle([(W / 2 - tw / 2 - 22) * SS, (y - 24) * SS, (W / 2 + tw / 2 + 22) * SS, (y + 24) * SS],
                        radius=8 * SS, fill=mix(CREAM, (255, 252, 244), 0.6), outline=mix(CREAM, INK, 0.25 * k), width=SS)
    d.text((W / 2 * SS, (y + 6 * (1 - k)) * SS), s, font=f, fill=mix(CREAM, color, k), anchor="mm")

def subs(d, t, items, y=640):
    """items: [(t0, t1, text)] – mỗi lúc một câu"""
    for t0, t1, s in items:
        if t0 <= t < t1:
            subtitle(d, s, t - t0, y=y); return

def stamp(im, s, t, color=RED, pos=(1010, 520), angle=-6, size=22):
    k = seg(t, 0.0, 0.25)
    if k <= 0: return
    f = F("monob", size)
    tmp = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    tw = int(tmp.textlength(s, font=f)); pad = 14 * SS
    st = Image.new("RGBA", (tw + 2 * pad, int(size * 2.1) * SS), (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    ds.rectangle([0, 0, st.width - 1, st.height - 1], fill=CREAM + (235,))
    ds.rectangle([2 * SS, 2 * SS, st.width - 2 * SS, st.height - 2 * SS], outline=color + (255,), width=3 * SS)
    ds.text((st.width // 2, st.height // 2), s, font=f, fill=color + (255,), anchor="mm")
    sc = lerp(1.5, 1.0, k)
    st = st.resize((int(st.width * sc), int(st.height * sc)), Image.LANCZOS)
    st = st.rotate(angle, expand=True, resample=Image.BICUBIC)
    if k < 1:
        a = st.split()[3].point(lambda v: int(v * k)); st.putalpha(a)
    x = clamp(pos[0] * SS - st.width / 2, 30 * SS, W * SS - 30 * SS - st.width)
    im.paste(st, (int(x), int(pos[1] * SS - st.height / 2)), st)

def tag(d, xy, s, color, size=14, anchor="mm", k=1.0, bg=CREAM, bold=True):
    """nhãn trong tọa độ màn hình 1x, tự giữ trong khung"""
    if k <= 0: return None
    font = F("monob" if bold else "mono", size)
    bb = d.textbbox((xy[0] * SS, xy[1] * SS), s, font=font, anchor=anchor)
    dx = 0
    if bb[0] < 34 * SS: dx = 34 * SS - bb[0]
    if bb[2] > (W - 34) * SS: dx = (W - 34) * SS - bb[2]
    bb = (bb[0] + dx, bb[1], bb[2] + dx, bb[3])
    d.rectangle([bb[0] - 6 * SS, bb[1] - 4 * SS, bb[2] + 6 * SS, bb[3] + 4 * SS], fill=bg, outline=mix(bg, color, k), width=SS)
    d.text((xy[0] * SS + dx, xy[1] * SS), s, font=font, fill=mix(bg, color, k), anchor=anchor)
    return bb

def badge(d, xy, n, color, r=13, k=1.0):
    if k <= 0: return
    x, y = xy[0] * SS, xy[1] * SS; rr = r * SS * lerp(0.6, 1.0, k)
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=mix(CREAM, color, k))
    d.text((x, y), str(n), font=F("monob", r * 1.15), fill=CREAM, anchor="mm")

def card(d, code, x, y, w, k, extra=None):
    """thẻ giải thích thiết bị: số, tên, loại, tác dụng (màu riêng)"""
    if k <= 0: return
    no, name, typ, fn, col = EL[code]
    lines = [("serifb", 19, name, col), ("mono", 13, "loại: " + typ, INK), ("serif", 15, "tác dụng: " + fn, INK)]
    if extra: lines.append(("mono", 12, extra, MUTED))
    h = 22 + sum(int(s * 1.55) for _, s, _, _ in lines)
    y = y + 10 * (1 - k)
    bgc = mix(CREAM, (255, 252, 244), 0.7)
    d.rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], fill=mix(CREAM, bgc, k), outline=mix(CREAM, col, k), width=3 * SS)
    d.rectangle([x * SS, y * SS, (x + 7) * SS, (y + h) * SS], fill=mix(CREAM, col, k))
    badge(d, (x + w - 22, y + 22), no, col, 13, k)
    yy = y + 14
    for fn_, sz, s, c in lines:
        f = F(fn_, sz)
        while d.textlength(s, font=f) > (w - 62) * SS and sz > 10:
            sz -= 1; f = F(fn_, sz)
        d.text(((x + 20) * SS, yy * SS), s, font=f, fill=mix(CREAM, c, k), anchor="lt")
        yy += int(sz * 1.55)

def name_tag(d, cam, code, wp, off, k, size=13):
    """nhãn tên có đường dẫn từ thiết bị (wp) tới vị trí lệch off (màn hình)"""
    if k <= 0: return
    no, name, _, _, col = EL[code]
    p = cam.scr(*wp); q = (p[0] + off[0], p[1] + off[1])
    d.line([(p[0] * SS, p[1] * SS), (q[0] * SS, q[1] * SS)], fill=mix(CREAM, col, k), width=SS * 2)
    rr = 3 * SS; d.ellipse([p[0] * SS - rr, p[1] * SS - rr, p[0] * SS + rr, p[1] * SS + rr], fill=mix(CREAM, col, k))
    s = f"({no}) {name}"
    anchor = "lm" if off[0] >= 0 else "rm"
    tag(d, q, s, col, size, anchor, k)

def note(d, xy, s, k=1.0, color=RED, size=13, anchor="lm"):
    """ghi chú chỗ chưa rõ / suy luận"""
    tag(d, xy, s, color, size, anchor, k, bg=mix(CREAM, (255, 246, 230), 0.8))

# ================= CÁC CẢNH =================
def default_slings():
    return [(POS_R[1], NBAG), (POS_R[0], NBAG)]

# 1. Mở đầu
def sc_title(t, D):
    im, d = frame_base()
    cam = Cam(CAM_FULL.cx, CAM_FULL.cy + 30, CAM_FULL.z * lerp(0.86, 0.9, t / D))
    over = Image.new("RGB", im.size, CREAM); do = ImageDraw.Draw(over)
    draw_plant(do, cam, {"slings": default_slings()})
    im = Image.blend(im, over, 0.2); d = ImageDraw.Draw(im)
    k = seg(t, 0.1, 0.7)
    d.text((W / 2 * SS, 200 * SS), "MÁY DEPAL BAO TỰ ĐỘNG", font=F("serifb", 50), fill=mix(CREAM, INK, k), anchor="mm")
    k2 = seg(t, 0.5, 1.1)
    d.text((W / 2 * SS, 268 * SS), "cách hoạt động: từ sling 45 bao tới thùng xe", font=F("serif", 30), fill=mix(CREAM, ORANGE, k2), anchor="mm")
    k3 = seg(t, 1.2, 1.7)
    d.text((W / 2 * SS, 326 * SS), "KCP Phú Yên · bản vẽ LA26-PTC-KCP-DEP-301026 (20/10/2026)",
           font=F("mono", 15), fill=mix(CREAM, INK, k3), anchor="mm")
    d.text((W / 2 * SS, 352 * SS), "cập nhật theo trao đổi với Phon-Tech ngày 04/11/2026",
           font=F("mono", 15), fill=mix(CREAM, INK, k3), anchor="mm")
    chips = ["01 · SLING VÀO – RA", "02 · HÚT 3 BAO", "03 · VỆ SINH, RA XE", "04 · TỰ CHẤT LÊN XE"]
    f = F("monob", 16)
    widths = [d.textlength(s, font=f) / SS + 28 for s in chips]
    x = W / 2 - (sum(widths) + 20 * 3) / 2
    for i, s in enumerate(chips):
        kk = seg(t, 1.8 + i * 0.35, 2.2 + i * 0.35)
        if kk > 0:
            y = 560 + 10 * (1 - kk)
            d.rectangle([x * SS, (y - 18) * SS, (x + widths[i]) * SS, (y + 18) * SS], fill=mix(CREAM, INK, kk))
            d.text(((x + 14) * SS, y * SS), s, font=f, fill=CREAM, anchor="lm")
        x += widths[i] + 20
    corners(d); footer(d, 1)
    return im

# 2. Tổng quan bố trí
OV_TAGS = [  # mã, điểm trên thiết bị, lệch nhãn (màn hình)
    ("L", (380, 812), (-10, 95)), ("R", (880, 812), (20, 95)), ("C", (628, 760), (-110, -60)),
    ("V", (BELT_X + 17, 627), (60, 12)), ("S", (BELT_X, 480), (-70, 0)), ("K", (655, 362), (-75, 22)),
    ("T", (950, 345), (10, 55)), ("X", (1330, 300), (40, -40)), ("M", (630, 1150), (60, 25)),
]
OV_STEP = 1.0
def sc_overview(t, D):
    im, d = frame_base()
    cam = CAM_FULL
    hl = {}
    for i, (c, _, _) in enumerate(OV_TAGS):
        t0 = 1.2 + i * OV_STEP
        hl[c] = seg(t, t0, t0 + 0.4) * (1 - seg(t, t0 + 1.0, t0 + 1.4))
    draw_plant(d, cam, {"slings": [(POS_C, NBAG)] + default_slings(), "hl": hl,
                        "robot": (PLACE, False, 0), "brush": t})
    for i, (c, wp, off) in enumerate(OV_TAGS):
        t0 = 1.2 + i * OV_STEP
        name_tag(d, cam, c, wp, off, seg(t, t0, t0 + 0.4), 13)
    kd = seg(t, 10.8, 11.4)
    if kd > 0:
        col = mix(CREAM, RED, kd)
        p0 = cam.P(337, 296); p1 = cam.P(910, 296)
        arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p0, col, 2, 9); arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p1, col, 2, 9)
        tag(d, (cam.scr(450, 296)[0], p0[1] / SS), "13.258 mm", RED, 13, "mm", kd)
    subs(d, t, [(0, 1.2, "Mặt bằng máy depal theo bản vẽ Phon-Tech ngày 20/10/2026"),
                (1.2, 10.6, "Chín cụm chính, đánh số theo hành trình của bao đường 50 kg"),
                (10.6, D + 1, "Chiều ngang tổng 13.258 mm – tăng 1.503 mm so với bản cũ 11.755 mm")])
    chapter(im, "TỔNG QUAN BỐ TRÍ", t)
    corners(d); footer(d, 2)
    return im

# 3. Diện tích chiếm trong kho
AREA_W = 13258
AREA_D = (1158 - 323) * MM          # tới mép dưới trạm dự phòng (đo trên bản vẽ)
STRIP_L = (1132 - 910) * MM         # dải băng ống lồng ra tới đuôi xe (đo trên bản vẽ)
STRIP_W = (370 - 323) * MM
A_MAIN = AREA_W * AREA_D / 1e6
A_STRIP = STRIP_L * STRIP_W / 1e6
A_TOTAL = A_MAIN + A_STRIP
def vn1(v, nd=1): return f"{v:.{nd}f}".replace(".", ",")
def sc_area(t, D):
    im, d = frame_base()
    cam = Cam(1000, 748, 0.56)
    over = Image.new("RGB", im.size, CREAM); do = ImageDraw.Draw(over)
    draw_plant(do, cam, {"slings": [(POS_C, NBAG)] + default_slings(), "robot": (PLACE, False, 0)})
    im = Image.blend(im, over, 0.55); d = ImageDraw.Draw(im)
    # khung chính
    k1 = lin(t, 0.8, 3.0)
    pts = [(337, 323), (910, 323), (910, 1158), (337, 1158), (337, 323)]
    sp = sub_path(pts, k1)
    if k1 >= 1:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dv = ImageDraw.Draw(ov)
        p0 = cam.P(337, 323); p1 = cam.P(910, 1158)
        dv.rectangle([p0[0], p0[1], p1[0], p1[1]], fill=ORANGE + (int(40 * seg(t, 3.0, 3.6)),))
        im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
    if len(sp) > 1:
        for i in range(len(sp) - 1):
            dashed(d, cam.P(*sp[i]), cam.P(*sp[i + 1]), RED, 2.2, 9, 5)
    # dải ra xe
    k2 = seg(t, 6.0, 7.0)
    if k2 > 0:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dv = ImageDraw.Draw(ov)
        p0 = cam.P(910, 323); p1 = cam.P(lerp(910, 1132, k2), 370)
        dv.rectangle([p0[0], p0[1], p1[0], p1[1]], fill=ORANGE + (60,), outline=RED + (255,), width=2 * SS)
        im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
    # kích thước
    kd = seg(t, 3.0, 3.6)
    if kd > 0:
        col = mix(CREAM, RED, kd)
        p0 = cam.P(337, 290); p1 = cam.P(910, 290)
        arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p0, col, 2, 9); arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p1, col, 2, 9)
        tag(d, (cam.scr(450, 290)[0], p0[1] / SS), "13.258 mm (bản vẽ)", RED, 12, "mm", kd)
    kd2 = seg(t, 4.0, 4.6)
    if kd2 > 0:
        col = mix(CREAM, RED, kd2)
        x = 300
        for (ya, yb, s) in ((323, 925, "3.954 + 9.950 (bản vẽ)"), (925, 1158, f"≈{vn(round((1158 - 925) * MM / 10) * 10)} (ước tính)")):
            q0 = cam.P(x, ya); q1 = cam.P(x, yb)
            arrow(d, (q0[0], (q0[1] + q1[1]) / 2), q0, col, 2, 8); arrow(d, (q0[0], (q0[1] + q1[1]) / 2), q1, col, 2, 8)
            tag(d, (q0[0] / SS - 10, (q0[1] + q1[1]) / 2 / SS), s, RED, 11, "rm", kd2)
        q0 = cam.P(255, 323); q1 = cam.P(255, 1158)
    if k2 > 0:
        p = cam.scr(1021, 323)
        tag(d, (p[0], p[1] - 14), f"≈ {vn1(STRIP_L / 1000)} m (ước tính)", RED, 11, "mm", k2)
    # bảng diện tích
    px, py, pw = 770, 330, 450
    rows = [(8.0, "monob", 14, "DIỆN TÍCH CHIẾM TRONG KHO", INK),
            (8.6, "serif", 16, f"Khung chính: {vn1(AREA_W / 1000, 2)} × {vn1(AREA_D / 1000, 2)} m ≈ {A_MAIN:.0f} m²", INK),
            (9.6, "serif", 16, f"Dải băng ra xe: ≈ {vn1(STRIP_L / 1000)} × {vn1(STRIP_W / 1000)} m ≈ {A_STRIP:.0f} m²", INK),
            (10.6, "serifb", 22, f"Tổng ≈ {A_TOTAL:.0f} m²", RED),
            (11.4, "mono", 12, "không tính lối đi xe nâng và chỗ đậu xe", MUTED),
            (12.6, "serifb", 17, "Điểm cao nhất hệ thống băng tải: 1,5 m", TEAL),
            (13.4, "mono", 11, "số có dấu ≈: đo trên bản vẽ (SCALE: FREE), ước tính", MUTED),
            (13.4, "mono", 11, "cao 1,5 m: Phon-Tech xác nhận 04/11/2026", MUTED)]
    kp = seg(t, 7.6, 8.0)
    if kp > 0:
        d.rectangle([px * SS, py * SS, (px + pw) * SS, (py + 262) * SS], fill=mix(CREAM, (255, 252, 244), kp),
                    outline=mix(CREAM, INK, kp), width=2 * SS)
        y = py + 16
        for t0, fn, sz, s, c in rows:
            kk = seg(t, t0, t0 + 0.4)
            if kk > 0:
                d.text(((px + 18) * SS, y * SS), s, font=F(fn, sz), fill=mix(CREAM, c, kk), anchor="lt")
            y += int(sz * 1.75)
    subs(d, t, [(0, 3.2, "Phần hệ thống chiếm chỗ trong kho (khung đỏ)"),
                (3.2, 6.0, f"Khung chính khoảng {vn1(AREA_W / 1000, 1)} × {vn1(AREA_D / 1000, 1)} m, tính cả trạm dự phòng"),
                (6.0, 10.6, f"Thêm dải băng tải ống lồng ra tới đuôi xe khoảng {vn1(STRIP_L / 1000)} m"),
                (10.6, 12.6, f"Tổng khoảng {A_TOTAL:.0f} m², chưa tính lối đi xe nâng và chỗ đậu xe"),
                (12.6, D + 1, "Điểm cao nhất của hệ thống băng tải: 1,5 m")])
    chapter(im, "DIỆN TÍCH CHIẾM TRONG KHO", t)
    corners(d); footer(d, 3)
    return im

# 4. Sling hàng
def sc_sling(t, D):
    im, d = frame_base()
    chapter(im, "SLING HÀNG ĐẦU VÀO", t)
    # khung minh họa trái: lưới 3x3 nhìn từ trên
    x0, y0, cw, ch = 150, 150, 300, 380
    d.rectangle([x0 * SS, y0 * SS, (x0 + cw) * SS, (y0 + ch) * SS], outline=INK, width=2 * SS)
    d.text(((x0 + 12) * SS, (y0 + 12) * SS), "NHÌN TỪ TRÊN · 1 LỚP", font=F("mono", 12), fill=INK, anchor="lt")
    cam = Cam(0, 0, 3.2)
    cam = Cam(-(x0 + cw / 2 - W / 2) / 3.2, -(y0 + ch / 2 + 10 - H / 2) / 3.2, 3.2)
    n_top = int(clamp((t - 0.6) / 2.4) * 9 + 0.0001)
    if t > 0.6:
        draw_sling(d, cam, (0, 0), max(0, n_top), k=1.0, fill_first=True)
    p0 = cam.P(-SW / 2, SLL / 2 + 10); p1 = cam.P(SW / 2, SLL / 2 + 10)
    kd = seg(t, 3.0, 3.4)
    if kd > 0:
        arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p0, mix(CREAM, RED, kd), 2, 8); arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p1, mix(CREAM, RED, kd), 2, 8)
        tag(d, ((p0[0] + p1[0]) / 2 / SS, p0[1] / SS + 2), "1.500", RED, 12, "mm", kd)
        q0 = cam.P(-SW / 2 - 10, -SLL / 2); q1 = cam.P(-SW / 2 - 10, SLL / 2)
        arrow(d, (q0[0], (q0[1] + q1[1]) / 2), q0, mix(CREAM, RED, kd), 2, 8); arrow(d, (q0[0], (q0[1] + q1[1]) / 2), q1, mix(CREAM, RED, kd), 2, 8)
        tag(d, (q0[0] / SS, (q0[1] + q1[1]) / 2 / SS), "2.250", RED, 12, "mm", kd)
    # khung minh họa phải: 5 lớp nhìn ngang
    x1 = 520; cw2 = 330
    d.rectangle([x1 * SS, y0 * SS, (x1 + cw2) * SS, (y0 + ch) * SS], outline=INK, width=2 * SS)
    d.text(((x1 + 12) * SS, (y0 + 12) * SS), "NHÌN NGANG · 5 LỚP", font=F("mono", 12), fill=INK, anchor="lt")
    nl = int(clamp((t - 3.6) / 2.6) * 5 + 0.0001)
    bw, bh = 76, 30
    bx = x1 + cw2 / 2 - 1.5 * bw; by = y0 + ch - 70
    for L in range(nl):
        for c in range(3):
            yy = by - L * bh
            d.rounded_rectangle([(bx + c * bw + 2) * SS, (yy - bh + 3) * SS, (bx + (c + 1) * bw - 2) * SS, yy * SS],
                                radius=10 * SS, fill=BAG_TOP, outline=INK, width=2 * SS)
        d.text(((bx + 3 * bw + 12) * SS, (by - L * bh - bh / 2) * SS), f"lớp {L + 1}", font=F("mono", 12), fill=INK, anchor="lm")
    d.line([(bx - 6) * SS, (by + 3) * SS, (bx + 3 * bw + 6) * SS, (by + 3) * SS], fill=INK, width=3 * SS)
    if nl == 5:
        kd2 = seg(t, 6.2, 6.6)
        tag(d, (x1 + cw2 / 2, by + 30), "bản vẽ: 5 × 150 = 750 mm", RED, 12, "mm", kd2)
    # cột số liệu
    xs = 900
    rows = [(0.8, "3 × 3", "bao mỗi lớp", BLUE), (3.8, "5 lớp", "theo bản vẽ (nhìn ngang)", PURPLE),
            (6.6, "45 bao", "= 9 × 5 bao / sling", GREEN), (8.0, "2.250 kg", "45 × 50 kg", ORANGE)]
    for i, (t0, big, small, col) in enumerate(rows):
        kk = seg(t, t0, t0 + 0.5)
        if kk <= 0: continue
        y = 170 + i * 95
        d.text((xs * SS, y * SS), big, font=F("serifb", 36), fill=mix(CREAM, col, kk), anchor="lt")
        d.text((xs * SS, (y + 50) * SS), small, font=F("mono", 14), fill=mix(CREAM, INK, kk), anchor="lt")
    note(d, (900, 560), "bản vẽ ghi 'sling + hàng = 2.250 kg' → chưa tính vỏ sling? (To be confirm)", seg(t, 8.6, 9.0), RED, 11)
    subs(d, t, [(0, 3.6, "Mỗi sling 2.250 × 1.500 mm, xếp 3 × 3 bao mỗi lớp"),
                (3.6, 6.6, "Xếp 5 lớp chồng lên nhau"),
                (6.6, D + 1, "Một sling chứa 45 bao 50 kg, tức 2.250 kg đường")])
    corners(d); footer(d, 4)
    return im

def lerp_p(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))

# 5. Luồng sling: xe nâng cấp, bấm nút vào hút, sling rỗng trả ra (Phon-Tech xác nhận 04/11/2026)
def kx(t, keys):
    """vị trí theo mốc thời gian [(t, x)], chuyển động mượt giữa hai mốc"""
    if t <= keys[0][0]: return keys[0][1]
    for i in range(len(keys) - 1):
        if t < keys[i + 1][0]:
            return lerp(keys[i][1], keys[i + 1][1], seg(t, keys[i][0], keys[i + 1][0]))
    return keys[-1][1]

def nbags(t, t0, t1): return int(round(lerp(NBAG, 0, lin(t, t0, t1)) / 3)) * 3

FL_OFF = 57          # tâm xe nâng lùi sau tâm sling (càng nâng ở dưới sling)
FLOW = {  # sling: mốc vị trí x, khoảng hút (t0, t1), khoảng mờ đi (lấy ra)
    "A": dict(keys=[(0.5, -40), (2.5, 375), (3.2, 375), (4.6, 536), (10.2, 536), (11.8, 627.5), (15.2, 627.5), (17.0, 723), (22.2, 723), (24.4, 536)],
              dep=(12.0, 15.0), out=(24.6, 26.0), show=0.5),
    "B": dict(keys=[(4.4, -40), (6.4, 375), (6.6, 375), (7.6, 455), (10.4, 455), (11.8, 536), (17.7, 536), (19.3, 627.5), (22.2, 627.5), (24.4, 455)],
              dep=(19.5, 22.0), out=(24.6, 26.0), show=4.4),
    "R1": dict(keys=[(0, 792), (25.7, 792), (27.5, 627.5), (30.0, 627.5), (31.5, 536), (35.6, 536), (37.5, 723)],
               dep=(27.6, 30.0), out=(37.7, 39.2), show=0),
    "R0": dict(keys=[(0, 875), (25.9, 875), (27.5, 723), (31.7, 723), (33.0, 627.5), (35.6, 627.5), (37.5, 792)],
               dep=(33.1, 35.5), out=(37.7, 39.2), show=0),
    "A2": dict(keys=[(27.2, -40), (28.7, 375), (28.9, 375), (29.8, 455)], dep=None, out=None, show=27.2),
    "B2": dict(keys=[(30.4, -40), (31.9, 375)], dep=None, out=None, show=30.4),
}
FORK_TRIPS = [("A", 0.5, 2.5, 3.0, 4.2), ("B", 4.4, 6.4, 6.9, 8.0), ("A2", 27.2, 28.7, 29.2, 30.2), ("B2", 30.4, 31.9, 32.4, 33.4)]
BTN_L, BTN_R = (484, 784), (773, 784)
PRESS = [(10.0, BTN_L), (17.5, BTN_L), (25.5, BTN_R), (31.5, BTN_R)]
D_FLOW = 41.0

def flow_state(t):
    slings = []
    for name, f in FLOW.items():
        if t < f["show"]: continue
        x = kx(t, f["keys"])
        n = NBAG if f["dep"] is None else nbags(t, *f["dep"])
        k = 1.0 if f["out"] is None else 1 - seg(t, *f["out"])
        if k > 0.02: slings.append(((x, CY), n, k))
    forks = []
    for name, t0, t1, t2, t3 in FORK_TRIPS:
        if t0 <= t < t2:
            forks.append(kx(t, FLOW[name]["keys"]) - FL_OFF)
        elif t2 <= t < t3:
            forks.append(lerp(375 - FL_OFF, -160, seg(t, t2, t3)))
    deps = [f["dep"] for f in FLOW.values() if f["dep"]]
    rob = PLACE
    for t0, t1 in deps:
        if t0 <= t < t1:
            u = 0.5 - 0.5 * math.cos(2 * math.pi * 1.4 * (t - t0))
            rob = lerp_p(PLACE, (627.5, CY - 10), u)
    return slings, forks, rob

def sc_flow(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_FULL, CAM_FLOW, seg(t, 0, 1.0))
    slings, forks, rob = flow_state(t)
    presses = [(BTN, seg(t, tp, tp + 0.8) if tp <= t < tp + 0.9 else 0.0) for tp, BTN in PRESS]
    hl = {"L": 1.0 if t < 25 else 0.0, "R": 1.0 if t >= 25 else 0.0}
    draw_plant(d, cam, {"slings": slings, "forklifts": [((x, CY), 0.0) for x in forks], "robot": (rob, False, 0),
                        "buttons": presses, "hl": hl})
    for x in forks:
        p = cam.scr(x - 5, CY - 60)
        if p[0] > 60: tag(d, p, "XE NÂNG", INK, 12, "mm", 1.0)
    for tp, btn in PRESS:
        k = seg(t, tp - 0.2, tp) * (1 - seg(t, tp + 1.2, tp + 1.5))
        if k > 0:
            p = cam.scr(btn[0], btn[1] - 14)
            tag(d, p, "BẤM NÚT", RED, 12, "mm", k)
    def stag(x, s, col, t0, t1, dy=62):
        k = seg(t, t0, t0 + 0.3) * (1 - seg(t, t1 - 0.3, t1))
        if k > 0:
            p = cam.scr(x, CY + dy); tag(d, p, s, col, 12, "mm", k)
    stag(536, "chờ hút", BLUE, 12.0, 17.6)
    stag(723, "rỗng – chờ", PURPLE, 17.0, 22.2)
    stag(723, "chờ hút", PURPLE, 27.5, 31.6)
    stag(536, "rỗng – chờ", BLUE, 31.5, 35.6)
    for t0, t1 in [f["dep"] for f in FLOW.values() if f["dep"]]:
        k = seg(t, t0, t0 + 0.3) * (1 - seg(t, t1 - 0.2, t1))
        if k > 0:
            p = cam.scr(627.5, CY + 62); tag(d, p, "HÚT 45 BAO · TUA NHANH >>", BRICK, 12, "mm", k)
    # kiểm tra bao trước khi bấm
    k = seg(t, 7.9, 8.3) * (1 - seg(t, 9.8, 10.1))
    if k > 0:
        p = cam.scr(462, 760); note(d, (p[0], p[1] - 10), "kiểm tra: bao ngay ngắn, không rách", k, RED, 13, "mm")
    # lấy sling rỗng ra
    for (t0, t1, xs, ylane) in ((24.6, 26.2, (455, 536), 781), (37.7, 39.4, (723, 792), 781)):
        k = seg(t, t0, t0 + 0.3) * (1 - seg(t, t1 - 0.3, t1))
        if k > 0:
            for x in xs:
                arrow(d, cam.P(x, CY - 30), cam.P(x, ylane + 6), mix(CREAM, RED, k), 2.5, 10)
            p = cam.scr(sum(xs) / 2, 755); tag(d, (p[0], p[1] - 12), "công nhân lấy sling rỗng ra", RED, 12, "mm", k)
    card(d, "L", 60, 90, 420, seg(t, 0.6, 1.1) * (1 - seg(t, 8.6, 9.0)))
    card(d, "R", 800, 90, 420, seg(t, 25.0, 25.5) * (1 - seg(t, 31.0, 31.4)))
    subs(d, t, [(0, 7.8, "Xe nâng đặt 2 sling đầy lên băng con lăn bên trái"),
                (7.8, 12.0, "Công nhân kiểm tra bao ngay ngắn, không rách, rồi bấm nút cho sling vào"),
                (12.0, 15.1, "Máy hút hết 45 bao trên sling thứ nhất"),
                (15.1, 17.4, "Sling rỗng chuyển sang vị trí chờ bên phải"),
                (17.4, 22.1, "Bấm nút: sling đầy thứ hai vào, máy hút tiếp"),
                (22.1, 24.6, "Hút xong, cả 2 sling rỗng trả về bên trái"),
                (24.6, 27.0, "Công nhân bên trái lấy 2 sling rỗng ra"),
                (27.0, 33.4, "Bên phải làm giống hệt – lúc này xe nâng nạp 2 sling mới bên trái"),
                (33.4, 37.6, "Sling rỗng bên phải chờ bên trái, xong sling thứ hai thì cùng trả về bên phải"),
                (37.6, D + 1, "4 công nhân: kiểm tra bao, bấm đưa sling đầy vào, lấy sling rỗng ra")])
    chapter(im, "(1)(2) SLING VÀO – SLING RỖNG RA", t)
    corners(d); footer(d, 5)
    return im

# 6. Robot hút 3 bao/lần, thả lần lượt từng bao (cần chốt với Phon-Tech sáng 05/11/2026)
ROW_DX = SW / 3
BAG_DX = [-ROW_DX, 0.0, ROW_DX]          # 3 bao trong một hàng ngang (dài 1.500 mm)
def row_y(r): return CY + (r - 1) * SLL / 3
PH = [("a", 2.9), ("b", 0.9), ("c", 1.7), ("d", 0.6), ("e", 1.6), ("f", 0.6), ("g", 1.6), ("h", 0.6)]
PH_SUM = sum(v for _, v in PH)
STEP_OF = {"a": 0, "b": 0, "c": 1, "d": 2, "e": 3, "f": 3, "g": 4, "h": 4}

def pick_cycle(t, t0, T, r):
    """trả (tâm đầu hút, bao đang mang, hút?, thời điểm thả 3 bao, pha hiện tại, đã nhấc bao chưa)"""
    sc = T / PH_SUM
    marks = {}; acc = t0
    for name, v in PH:
        marks[name] = (acc, acc + v * sc); acc += v * sc
    start = (628 - ROW_DX, PLACE[1])
    pick = (627.5, row_y(r))
    over = [(628 - dx, PLACE[1]) for dx in BAG_DX]      # tâm đầu hút để bao j nằm trên băng
    drops = [marks["d"][0], marks["f"][0], marks["h"][0]]
    if t < t0: return start, [], 0, drops, None, False
    for name, _ in PH:
        a, b = marks[name]
        if t < b:
            u = seg(t, a, b)
            if name == "a": return lerp_p(start, pick, u), [], 0, drops, name, False
            if name == "b": return pick, [], 1, drops, name, u > 0.6
            if name == "c": return lerp_p(pick, over[0], u), [0, 1, 2], 1, drops, name, True
            if name == "d": return over[0], [1, 2], 1, drops, name, True
            if name == "e": return lerp_p(over[0], over[1], seg(t, a + (b - a) * 0.45, b)), [1, 2], 1, drops, name, True
            if name == "f": return over[1], [2], 1, drops, name, True
            if name == "g": return lerp_p(over[1], over[2], seg(t, a + (b - a) * 0.45, b)), [2], 1, drops, name, True
            if name == "h": return over[2], [], 0, drops, name, True
    return over[2], [], 0, drops, None, True

ROBOT_CYC = [(1.2, 12.0, 0), (13.6, 5.6, 1)]     # (bắt đầu, thời lượng, hàng)
FF0, FF1 = 19.6, 24.0                            # tua nhanh 13 lần hút còn lại
D_ROBOT = 28.0
STEPS = ["Hút 3 bao – 1 hàng ngang dài 1,5 m", "Đưa 3 bao tới đầu băng tải", "Thả bao thứ 1",
         "Dịch sang, thả bao thứ 2", "Dịch sang, thả bao thứ 3"]

def sc_robot(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_FLOW, CAM_CELL, seg(t, 0, 1.0))
    picked = 0; tgt = PLACE; carry = []; suc = 0; step = None; drop_list = []; lifted = False
    for (t0, T, r) in ROBOT_CYC:
        g, c, s, drops, ph, lf = pick_cycle(t, t0, T, r)
        v = 22.0 * 12.0 / T
        drop_list += [(td, v) for td in drops]
        if t0 <= t < t0 + T + 0.4:
            tgt, carry, suc, step, lifted = g, c, s, ph, lf
        if t >= t0 and lf: picked += 3
    # tua nhanh
    if t >= FF0:
        nff = min(13, int(lin(t, FF0, FF1) * 13 + 1e-6))
        picked = 6 + nff * 3
        if t < FF1:
            u = 0.5 - 0.5 * math.cos(2 * math.pi * 3.0 * (t - FF0))
            tgt = lerp_p((628, PLACE[1]), (627.5, CY), u); carry = [] ; suc = 0
            for i in range(int((t - FF0) / 0.11)):
                drop_list.append((FF0 + i * 0.11, 230.0))
        else:
            tgt = PLACE
    n_left = NBAG - picked
    bags = []
    for td, v in drop_list:
        if t >= td:
            y = PLACE[1] - (t - td) * v
            if y > 380: bags.append(((BELT_X, y), -math.pi / 2))
    st = {"slings": [(POS_C, n_left)] + default_slings(), "robot": (tgt, carry, suc), "bags": bags,
          "bars": {"C": lin(t, 0.6, 2.2)}, "hl": {"C": 1.0}, "brush": t, "robot_labels": True}
    draw_plant(d, cam, st)
    # kích thước 1,5 m của hàng 3 bao
    if step in ("b", "c"):
        k = seg(t, ROBOT_CYC[0][0] + 2.0, ROBOT_CYC[0][0] + 2.6) if t < 13 else 1.0
        p0 = cam.P(tgt[0] - SW / 2, tgt[1] + BL * 0.75); p1 = cam.P(tgt[0] + SW / 2, tgt[1] + BL * 0.75)
        if k > 0:
            col = mix(CREAM, RED, k)
            arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p0, col, 2, 8); arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p1, col, 2, 8)
            tag(d, ((p0[0] + p1[0]) / 2 / SS, p0[1] / SS + 2), "1,5 m · 3 bao", RED, 12, "mm", k)
    # bảng các bước (chậm, rõ)
    kp = seg(t, 1.0, 1.4) * (1 - seg(t, FF0 - 0.2, FF0 + 0.2))
    if kp > 0:
        px, py, pw = 50, 96, 405
        d.rectangle([px * SS, py * SS, (px + pw) * SS, (py + 236) * SS], fill=mix(CREAM, (255, 252, 244), kp), outline=mix(CREAM, BRICK, kp), width=2 * SS)
        d.text(((px + 14) * SS, (py + 12) * SS), "MỘT LẦN HÚT = 3 BAO", font=F("monob", 14), fill=mix(CREAM, BRICK, kp), anchor="lt")
        cur = STEP_OF.get(step) if step else None
        for i, s in enumerate(STEPS):
            y = py + 46 + i * 32
            on = cur == i
            done = cur is not None and i < cur
            col = BRICK if on else (INK if done else MUTED)
            if on:
                d.rectangle([(px + 8) * SS, (y - 13) * SS, (px + pw - 8) * SS, (y + 13) * SS], fill=mix(CREAM, BRICK, 0.12 * kp))
            d.text(((px + 16) * SS, y * SS), f"({i + 1})", font=F("monob", 14), fill=mix(CREAM, col, kp), anchor="lm")
            d.text(((px + 54) * SS, y * SS), s, font=F("serifb" if on else "serif", 15), fill=mix(CREAM, col, kp), anchor="lm")
        d.text(((px + 14) * SS, (py + 220) * SS), "thả lần lượt từng bao: chốt với Phon-Tech sáng 05/11/2026",
               font=F("mono", 10), fill=mix(CREAM, RED, kp), anchor="lm")
    card(d, "C", 850, 100, 380, seg(t, 0.8, 1.3) * (1 - seg(t, 12.6, 13.0)), "đầu hút chân không · Phon-Tech xác nhận")
    if t > 13.6 and t < FF0:
        note(d, (1230, 120), "nhịp thực tế: 12–13,5 giây / 3 bao", seg(t, 13.6, 14.0), BRICK, 13, "rm")
        note(d, (1230, 148), "(tính từ 40–45 tấn/giờ)", seg(t, 13.6, 14.0), MUTED, 11, "rm")
    f = F("monob", 17)
    d.text((1238 * SS, 62 * SS), f"CÒN {n_left}/45 BAO TRÊN SLING", font=f, fill=INK, anchor="rm")
    x0, x1, y = 1238 - 260, 1238, 80
    d.rectangle([x0 * SS, y * SS, x1 * SS, (y + 6) * SS], fill=mix(CREAM, INK, 0.15))
    d.rectangle([x0 * SS, y * SS, (x0 + (x1 - x0) * n_left / 45) * SS, (y + 6) * SS], fill=BRICK if n_left else ORANGE)
    if FF0 <= t < FF1:
        tag(d, (100, 120), "TUA NHANH >>", INK, 14, "lm", 1.0)
    c0 = ROBOT_CYC[0][0]; sc0 = ROBOT_CYC[0][1] / PH_SUM
    m = [c0]
    for _, v in PH: m.append(m[-1] + v * sc0)
    subs(d, t, [(0, c0, "Cell robot: đầu hút chân không gắp bao trên sling"),
                (c0, m[2], "Đầu hút chân không hút 1 hàng 3 bao nằm ngang, dài 1,5 m"),
                (m[2], m[3], "Đưa cả 3 bao tới đầu băng tải"),
                (m[3], m[5], "Thả bao thứ 1 xuống băng tải"),
                (m[5], m[7], "Dịch sang, thả bao thứ 2"),
                (m[7], ROBOT_CYC[1][0], "Dịch sang, thả bao thứ 3 – băng tải đưa bao đi"),
                (ROBOT_CYC[1][0], FF0, "Lần hút thứ 2: nhịp thực tế 12–13,5 giây cho 3 bao"),
                (FF0, FF1, "Lặp lại: 5 lớp × 3 hàng = 15 lần hút, hết 45 bao"),
                (FF1, D + 1, "Sling rỗng, chờ trả ra theo trình tự luân phiên")])
    chapter(im, "(3) HÚT 3 BAO – THẢ TỪNG BAO", t)
    corners(d); footer(d, 6)
    return im

# 7. Hành trình bao: vệ sinh -> băng thẳng -> băng cong -> băng ống lồng
J = [("V", 0.6, 4.4), ("S", 4.4, 7.6), ("K", 7.6, 9.6), ("T", 9.6, 15.6)]
def journey_s(t):
    lens = {"V": math.dist(PLACE, PATH["V"][1]), "S": L_SEG["S"], "K": L_SEG["K"], "T": L_SEG["T"]}
    off = 0.0
    for code, t0, t1 in J:
        if t < t1:
            return off + lens[code] * ss(clamp((t - t0) / (t1 - t0))) if t >= t0 else off
        off += lens[code]
    return off

def sc_journey(t, D):
    im, d = frame_base()
    s = journey_s(t)
    p, a = ppoint(OUT_PATH, s)
    z = 2.3 if t < 9.6 else lerp(2.3, 1.7, seg(t, 9.6, 11.0))
    tgt_cam = Cam(p[0] + (0 if t < 9.6 else 60), p[1] + 40, z)
    cam = cam_lerp(CAM_CELL, tgt_cam, seg(t, 0, 1.0)) if t < 1.0 else tgt_cam
    bars = {"C": 1.0}
    for code, t0, t1 in J: bars[code] = lin(t, t0, t1)
    bags = [(p, a)]
    for ds_ in (-120, 120, 240):
        s2 = s + ds_
        if 0 < s2 < L_OUT: bags.append(ppoint(OUT_PATH, s2))
    hl = {code: (1.0 if t0 <= t < t1 + 0.3 else 0.0) for code, t0, t1 in J}
    draw_plant(d, cam, {"slings": [(POS_C, 36)] + default_slings()[1:], "robot": (PLACE, False, 0), "bags": bags,
                        "bars": bars, "hl": hl, "brush": t * 2.5})
    q = cam.P(*p); r = cam.S(26)
    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], outline=ORANGE, width=LW(2.5))
    for code, t0, t1 in J:
        k = seg(t, t0, t0 + 0.4) * (1 - seg(t, t1 - 0.2, t1 + 0.1))
        if code == "T" and t > 14.5: k = seg(t, t0, t0 + 0.4)
        extra = {"V": "chổi quét bao: Phon-Tech xác nhận 04/11/2026",
                 "T": "vươn tối đa 18 m · có cảm biến: Phon-Tech xác nhận"}.get(code)
        card(d, code, 820, 90, 400, k, extra)
    subs(d, t, [(0, 4.4, "Băng tải vệ sinh bao: chổi quét sạch bụi trên bao"),
                (4.4, 7.6, "Bao ra khỏi cell theo băng tải thẳng"),
                (7.6, 9.6, "Băng cong 90° đổi hướng bao về phía xe"),
                (9.6, D + 1, "Băng tải ống lồng đưa bao vào sâu trong thùng xe")])
    chapter(im, "(4)–(7) VỆ SINH BAO, RA XE", t)
    corners(d); footer(d, 7)
    return im

# 7. Băng tải ống lồng tự chất bao lên xe (không dùng người)
# Thùng xe container bạt 34T (KCP – Trình tự chất bao xe 34T v2): 1.226 × 235 × 215 cm, thành 80 cm
# bao 75 × 50 × 13 cm, 5 bao ngang ép còn 47 cm; 14 hàng × 45 bao (9 lớp) + 2 hàng × 25 bao (5 lớp)
TL, TWD, TH, TWALL = 1226, 235, 215, 80
RL, RW, RH = 75, 47, 13
NROW, FULLR = 16, 14
def row_layers(r): return 9 if r < FULLR else 5
assert sum(5 * row_layers(r) for r in range(NROW)) == 680 and 680 * 50 == 34000
assert 5 * RW == TWD and 9 * RH == 117 and TL - NROW * RL == 26
TS = 0.80                    # px/cm trên màn hình
TX_FRONT = 1130              # vách đầu thùng (sát cabin)
TY0 = 118                    # mép trên hình nhìn từ trên
TFLOOR = 585                 # sàn ở hình nhìn ngang
def txr(u): return TX_FRONT - u * TS          # u = cm tính từ vách đầu thùng
T_START = 1.6

def load_plan():
    plan = []; t = T_START
    for r in range(NROW):
        n = 5 * row_layers(r)
        if r == 0:
            times = [t + 0.5 * (i + 1) for i in range(5)] + [t + 2.5 + 0.125 * (i + 1) for i in range(n - 5)]; dur = 7.5
        else:
            dur = 2.4 if r == 1 else 0.36
            times = [t + dur * (i + 1) / n for i in range(n)]
        plan.append((r, t, dur, times))
        t += dur + (1.5 if r == 0 else (0.5 if r == 1 else 0.12))
    return plan, t
PLAN, T_DONE = load_plan()

def head_state(t):
    """vị trí đầu rải: (u cm, cột, lớp, hàng đang chất hoặc None)"""
    face = lambda r: RL * (r + 1) + 10
    if t < T_START:
        return lerp(TL + 40, face(0), seg(t, 0.2, 1.4)), 2, 0, None
    for i, (r, t0, dur, times) in enumerate(PLAN):
        if t0 <= t < t0 + dur:
            n_done = sum(1 for x in times if x <= t)
            j = min(n_done, len(times) - 1)
            return face(r), j % 5, j // 5, r
        nxt = PLAN[i + 1][1] if i + 1 < len(PLAN) else None
        if nxt is not None and t0 + dur <= t < nxt:
            return lerp(face(r), face(r + 1), seg(t, t0 + dur, nxt)), 2, 0, None
    return lerp(face(NROW - 1), TL + 40, seg(t, T_DONE, T_DONE + 1.2)), 2, 0, None

def truck_view(d, t, side=True, bad=False):
    """vẽ thùng xe (nhìn từ trên, và nhìn ngang nếu side) + băng ống lồng + bao đã chất ở thời điểm t của PLAN"""
    col = EL["T"][4]
    y1 = TY0 + TWD * TS
    roof = TFLOOR - TH * TS
    x_rear = txr(TL)
    d.text((x_rear * SS, (TY0 - 10) * SS), "NHÌN TỪ TRÊN", font=F("mono", 12), fill=INK, anchor="ls")
    d.rectangle([x_rear * SS, TY0 * SS, TX_FRONT * SS, y1 * SS], fill=mix(CREAM, NAVY, 0.05), outline=NAVY, width=3 * SS)
    cab = [(TX_FRONT, TY0 + 12), (TX_FRONT + 70, TY0 + 12), (TX_FRONT + 92, TY0 + 34), (TX_FRONT + 92, y1 - 34), (TX_FRONT + 70, y1 - 12), (TX_FRONT, y1 - 12)]
    d.polygon([(x * SS, y * SS) for x, y in cab], fill=mix(CREAM, NAVY, 0.14), outline=NAVY, width=2 * SS)
    tag(d, (x_rear, y1 + 16), "cửa sau", MUTED, 11, "lm", 1, bold=False)
    tag(d, (TX_FRONT, y1 + 16), "đầu thùng (sát cabin)", MUTED, 11, "rm", 1, bold=False)
    if side:
        d.text((x_rear * SS, (roof - 10) * SS), "NHÌN NGANG", font=F("mono", 12), fill=INK, anchor="ls")
        d.rectangle([x_rear * SS, roof * SS, TX_FRONT * SS, TFLOOR * SS], fill=mix(CREAM, NAVY, 0.03), outline=mix(CREAM, NAVY, 0.5), width=SS)
        d.line([x_rear * SS, TFLOOR * SS, TX_FRONT * SS, TFLOOR * SS], fill=NAVY, width=4 * SS)
        dashed(d, (x_rear * SS, (TFLOOR - TWALL * TS) * SS), (TX_FRONT * SS, (TFLOOR - TWALL * TS) * SS), mix(CREAM, NAVY, 0.6), 1.5, 8, 6)
        d.text(((x_rear + 6) * SS, (TFLOOR - TWALL * TS - 4) * SS), "thành 80 cm", font=F("mono", 11), fill=mix(CREAM, NAVY, 0.7), anchor="ls")
        dashed(d, (x_rear * SS, (roof + 30 * TS) * SS), (TX_FRONT * SS, (roof + 30 * TS) * SS), mix(CREAM, RED, 0.5), 1.2, 4, 6)
        d.text(((x_rear + 6) * SS, (roof + 30 * TS - 4) * SS), "giới hạn chất cao: cách trần 30 cm", font=F("mono", 11), fill=mix(CREAM, RED, 0.7), anchor="ls")
        d.rectangle([TX_FRONT * SS, (TFLOOR - 200 * TS) * SS, (TX_FRONT + 92) * SS, TFLOOR * SS], fill=mix(CREAM, NAVY, 0.14), outline=NAVY, width=2 * SS)
    total = 0; cur_r = 0; last = None
    for r, t0, dur, times in PLAN:
        n = sum(1 for x in times if x <= t)
        total += n
        if n: cur_r = r
        xa, xb = txr(RL * (r + 1)), txr(RL * r)
        for c in range(5):
            cnt = sum(1 for i in range(n) if i % 5 == c)
            if cnt:
                ya = TY0 + c * RW * TS; yb = ya + RW * TS
                shade = mix(BAG_TOP, BAG_LOW, 0.6 * (1 - cnt / 9))
                is_last = n > 0 and (n - 1) % 5 == c and r == cur_r
                if bad and is_last:
                    last = ((xa + xb) / 2, (ya + yb) / 2)
                    continue
                d.rounded_rectangle([(xa + 2) * SS, (ya + 2) * SS, (xb - 2) * SS, (yb - 2) * SS], radius=4 * SS, fill=shade, outline=INK, width=SS)
        if side:
            for k in range(row_layers(r)):
                cnt = sum(1 for i in range(n) if i // 5 == k)
                if cnt:
                    za = TFLOOR - (k + 1) * RH * TS; zb = TFLOOR - k * RH * TS
                    d.rounded_rectangle([(xa + 2) * SS, (za + 1) * SS, (xb - 2) * SS, (zb - 1) * SS], radius=3 * SS,
                                        fill=BAG_TOP if cnt == 5 else mix(CREAM, BAG_TOP, 0.6), outline=INK if cnt == 5 else MUTED, width=SS)
    if bad and last is not None:   # bao đặt lệch: xoay và lệch khỏi ô
        pts = rot_rect((last[0] - 6, last[1] + 5), RL * TS - 4, RW * TS - 4, math.radians(14))
        d.polygon([(x * SS, y * SS) for x, y in pts], fill=BAG_TOP, outline=RED, width=3 * SS)
    u, c, k, r_act = head_state(t)
    xh = txr(u)
    yc = TY0 + TWD * TS / 2
    x_in = 44
    segs = [(x_in, lerp(x_in, xh, 0.45), 28), (lerp(x_in, xh, 0.43), lerp(x_in, xh, 0.75), 24), (lerp(x_in, xh, 0.73), xh, 20)]
    for xa, xb, hw in segs:
        d.rectangle([xa * SS, (yc - hw) * SS, xb * SS, (yc + hw) * SS], fill=mix(CREAM, col, 0.22), outline=col, width=2 * SS)
    yh = TY0 + (c + 0.5) * RW * TS
    d.line([xh * SS, yc * SS, (xh + 12) * SS, yh * SS], fill=col, width=5 * SS)
    d.rectangle([(xh + 4) * SS, (yh - 16) * SS, (xh + 22) * SS, (yh + 16) * SS], fill=col, outline=INK, width=SS)
    zh = TFLOOR - (k * RH + RH + 6) * TS
    if side:
        zin = TFLOOR - 95 * TS
        pts = [(x_in, zin), (lerp(x_in, xh, 0.45), lerp(zin, zh, 0.45)), (lerp(x_in, xh, 0.75), lerp(zin, zh, 0.75)), (xh, zh)]
        for (p0, p1), w in zip(zip(pts[:-1], pts[1:]), (12, 10, 8)):
            d.line([p0[0] * SS, p0[1] * SS, p1[0] * SS, p1[1] * SS], fill=col, width=w * SS)
        d.rectangle([(xh + 2) * SS, (zh - 8) * SS, (xh + 20) * SS, (zh + 8) * SS], fill=col, outline=INK, width=SS)
    if r_act is not None and PLAN[r_act][2] >= 2 and not bad:
        sx0, sx1 = txr(RL * (r_act + 1)), txr(RL * r_act)
        d.rounded_rectangle([(sx0 + 3) * SS, (yh - RW * TS / 2 + 3) * SS, (sx1 - 3) * SS, (yh + RW * TS / 2 - 3) * SS],
                            radius=4 * SS, fill=BAG_TOP, outline=ORANGE, width=2 * SS)
    return dict(xh=xh, yh=yh, yc=yc, zh=zh, total=total, cur_r=cur_r, r_act=r_act, y1=y1, roof=roof, last=last)

def truck_counter(d, total, cur_r):
    col = EL["T"][4]
    f = F("monob", 17)
    d.text((1238 * SS, 62 * SS), f"ĐÃ CHẤT {total}/680 BAO", font=f, fill=INK, anchor="rm")
    xa0, xa1 = 1238 - 230, 1238
    d.rectangle([xa0 * SS, 80 * SS, xa1 * SS, 86 * SS], fill=mix(CREAM, INK, 0.15))
    d.rectangle([xa0 * SS, 80 * SS, (xa0 + (xa1 - xa0) * total / 680) * SS, 86 * SS], fill=col if total < 680 else ORANGE)
    d.text((1238 * SS, 104 * SS), f"HÀNG {cur_r + 1}/16", font=F("mono", 13), fill=INK, anchor="rm")

def sc_truck(t, D):
    im, d = frame_base()
    chapter(im, "(7)(8) BĂNG ỐNG LỒNG TỰ CHẤT LÊN XE", t)
    col = EL["T"][4]
    v = truck_view(d, t)
    y1, roof = v["y1"], v["roof"]
    if t < T_START + 0.6:
        tag(d, (300, v["yc"] - 44), "tầm vươn tối đa 18 m", col, 12, "mm", seg(t, 0.2, 0.6))
    if v["r_act"] == 0 or (PLAN[0][1] + PLAN[0][2] <= t < PLAN[1][1]):
        kk = seg(t, 2.0, 2.4)
        xL = txr(RL) - 14
        arrow(d, (xL * SS, (TY0 + 6) * SS), (xL * SS, (y1 - 6) * SS), mix(CREAM, RED, kk), 2, 9)
        tag(d, (xL - 8, TY0 + 30), "trái → phải", RED, 12, "rm", kk)
    if PLAN[0][1] + PLAN[0][2] - 0.3 <= t < PLAN[1][1] + 0.2:
        kk = seg(t, PLAN[0][1] + PLAN[0][2] - 0.3, PLAN[0][1] + PLAN[0][2])
        x9 = txr(RL) - 30
        arrow(d, (x9 * SS, TFLOOR * SS), (x9 * SS, (TFLOOR - 117 * TS) * SS), mix(CREAM, RED, kk), 2, 9)
        tag(d, (x9 - 8, TFLOOR - 60 * TS), "9 lớp = 117 cm", RED, 12, "rm", kk)
        ka = seg(t, PLAN[0][1] + PLAN[0][2], PLAN[1][1])
        tag(d, (txr(RL * 1.5), roof + 50), "← thụt lại 75 cm", col, 12, "mm", ka)
    truck_counter(d, v["total"], v["cur_r"])
    d.text((1238 * SS, 400 * SS), "vươn/thụt, tự rải bao, vươn tối đa 18 m: Phon-Tech · sơ đồ chất: Trình tự chất bao xe 34T v2 (KCP)",
           font=F("mono", 10), fill=MUTED, anchor="rs")
    if t > T_DONE + 0.4:
        stamp(im, "XONG 1 XE · 680 BAO · 34 TẤN", t - T_DONE - 0.4, ORANGE, (W / 2, 362), -3, 20)
    subs(d, t, [(0, T_START, "Băng tải ống lồng vươn hết cỡ vào sát đầu thùng xe (tối đa 18 m)"),
                (T_START, PLAN[0][1] + PLAN[0][2], "Đầu băng tự rải bao từ trái sang phải, đủ 5 bao mới lên lớp trên"),
                (PLAN[0][1] + PLAN[0][2], PLAN[2][1], "Đủ 9 lớp = 45 bao, băng thụt lại 75 cm để chất hàng tiếp theo"),
                (PLAN[2][1], T_DONE + 0.4, "Lặp lại tới hàng 16 – không cần người trong thùng xe"),
                (T_DONE + 0.4, D + 1, "14 hàng × 45 bao + 2 hàng × 25 bao = 680 bao = 34 tấn")])
    corners(d); footer(d, 8)
    return im

# 9. Cảm biến định vị + người ở phòng điều khiển (chậm, rõ)
D_SENSOR = 27.0
T_BAD = 15.0
def sc_sensor(t, D):
    im, d = frame_base()
    chapter(im, "(7) CẢM BIẾN VÀ PHÒNG ĐIỀU KHIỂN", t)
    col = EL["T"][4]
    tp = T_START + 0.2 + min(t, T_BAD) * 0.18
    bad = t >= T_BAD
    v = truck_view(d, tp, side=False, bad=bad)
    xh, yh, yc, y1 = v["xh"], v["yh"], v["yc"], v["y1"]
    hx = xh + 13
    # (A) định vị thùng xe: tia tới 2 vách bên và vách đầu thùng
    kA = seg(t, 2.0, 2.8)
    if kA > 0:
        c = mix(CREAM, col, kA)
        for (px, py) in ((hx, TY0 + 2), (hx, y1 - 2), (TX_FRONT - 2, yc)):
            dashed(d, (hx * SS, yh * SS), (px * SS, py * SS), c, 2, 5, 4)
            r = 5 * SS; d.ellipse([px * SS - r, py * SS - r, px * SS + r, py * SS + r], outline=c, width=2 * SS)
        tag(d, (hx - 70, TY0 + 18), "(A) định vị thùng xe", col, 13, "rm", kA)
    # (B) vị trí bao: vùng quét lên ô đang đặt
    kB = seg(t, 6.0, 6.8)
    if kB > 0:
        tx = (txr(RL) + txr(0)) / 2
        ty = v["last"][1] if v["last"] else yh
        cB = RED if bad else (40, 150, 70)
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dv = ImageDraw.Draw(ov)
        dv.polygon([(hx * SS, yh * SS), ((tx - 14) * SS, (ty - 20) * SS), ((tx + 14) * SS, (ty + 20) * SS)], fill=cB + (int(70 * kB),))
        im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
        tag(d, (hx - 70, y1 - 18), "(B) vị trí bao", col, 13, "rm", kB)
    # bảng chú thích cảm biến (trái dưới)
    kL = seg(t, 1.0, 1.5)
    if kL > 0:
        lx, ly = 60, 372
        d.text((lx * SS, ly * SS), "CẢM BIẾN TRÊN ĐẦU BĂNG ỐNG LỒNG", font=F("monob", 14), fill=mix(CREAM, col, kL), anchor="lt")
        d.text((lx * SS, (ly + 34) * SS), "(A) định vị thùng xe: vách bên, vách đầu thùng", font=F("serif", 16), fill=mix(CREAM, INK, kA), anchor="lt")
        d.text((lx * SS, (ly + 64) * SS), "(B) vị trí bao: bao đặt đúng ô hay lệch", font=F("serif", 16), fill=mix(CREAM, INK, kB), anchor="lt")
        d.text((lx * SS, (ly + 100) * SS), "nguồn: Phon-Tech xác nhận 04/11/2026", font=F("mono", 11), fill=mix(CREAM, MUTED, kL), anchor="lt")
    # phòng điều khiển (phải dưới)
    kC = seg(t, 10.0, 10.6)
    if kC > 0:
        bx0, by0, bx1, by1 = 640, 352, 1230, 600
        d.rectangle([bx0 * SS, by0 * SS, bx1 * SS, by1 * SS], fill=mix(CREAM, (255, 252, 244), kC), outline=mix(CREAM, INK, kC), width=2 * SS)
        d.text(((bx0 + 14) * SS, (by0 + 12) * SS), "PHÒNG ĐIỀU KHIỂN · 1 người theo dõi", font=F("monob", 14), fill=mix(CREAM, INK, kC), anchor="lt")
        d.text(((bx0 + 14) * SS, (by0 + 34) * SS), "vị trí phòng: chưa có trên bản vẽ", font=F("mono", 11), fill=mix(CREAM, MUTED, kC), anchor="lt")
        # màn hình
        mx0, my0, mx1, my1 = bx0 + 16, by0 + 60, bx0 + 330, by0 + 200
        d.rectangle([mx0 * SS, my0 * SS, mx1 * SS, my1 * SS], fill=mix(CREAM, (30, 40, 50), kC), outline=INK, width=2 * SS)
        okc = (90, 200, 110); badc = (240, 90, 80)
        blink = (int(t * 3) % 2 == 0)
        lines = [("(A) THÙNG XE", "ĐÚNG", okc), ("(B) VỊ TRÍ BAO", "SAI" if bad else "ĐÚNG", badc if bad else okc)]
        for i, (a_, b_, cc) in enumerate(lines):
            yy = my0 + 34 + i * 46
            d.text(((mx0 + 14) * SS, yy * SS), a_, font=F("monob", 16), fill=mix(CREAM, (230, 230, 230), kC), anchor="lm")
            if not (bad and i == 1 and not blink):
                d.text(((mx1 - 14) * SS, yy * SS), b_, font=F("monob", 18), fill=mix(CREAM, cc, kC), anchor="rm")
        # người điều khiển
        ox, oy = bx0 + 390, by0 + 140
        r = 14 * SS
        d.ellipse([ox * SS - r, (oy - 40) * SS - r, ox * SS + r, (oy - 40) * SS + r], fill=mix(CREAM, PERSON, kC), outline=INK, width=SS)
        d.rounded_rectangle([(ox - 24) * SS, (oy - 22) * SS, (ox + 24) * SS, (oy + 34) * SS], radius=10 * SS, fill=mix(CREAM, PERSON, 0.6 * kC), outline=INK, width=SS)
        # nút dừng
        sx, sy = bx0 + 510, by0 + 140
        press = seg(t, 19.6, 20.0) * (1 - seg(t, 20.6, 21.0))
        r = (32 - 4 * press) * SS
        d.ellipse([sx * SS - r, sy * SS - r, sx * SS + r, sy * SS + r], fill=mix(CREAM, RED, kC), outline=INK, width=2 * SS)
        d.text((sx * SS, sy * SS), "DỪNG", font=F("monob", 14), fill=CREAM, anchor="mm")
        if press > 0:
            rr = (40 + 22 * press) * SS
            d.ellipse([sx * SS - rr, sy * SS - rr, sx * SS + rr, sy * SS + rr], outline=mix(CREAM, RED, 1 - press * 0.5), width=3 * SS)
            arrow(d, ((ox + 30) * SS, (oy - 10) * SS), ((sx - 36) * SS, sy * SS), RED, 3, 10)
        if t >= 20.0:
            d.text(((bx0 + 14) * SS, (by1 - 16) * SS), "bấm dừng khi cảm biến sai: giả định KCP – cần Phon-Tech xác nhận",
                   font=F("mono", 11), fill=RED, anchor="ls")
    if bad and v["last"]:
        p = v["last"]
        note(d, (p[0] - 60, p[1] - 44), "bao đặt lệch", seg(t, T_BAD, T_BAD + 0.4), RED, 13, "mm")
    if t >= 20.0:
        stamp(im, "DỪNG MÁY", t - 20.0, RED, (330, 548), -4, 22)
    truck_counter(d, v["total"], v["cur_r"])
    subs(d, t, [(0, 2.0, "Đầu băng ống lồng có cảm biến – xem chậm từng loại"),
                (2.0, 6.0, "Cảm biến (A) định vị thùng xe: đo khoảng cách tới vách bên và vách đầu thùng"),
                (6.0, 10.0, "Cảm biến (B) kiểm tra từng bao đặt đúng ô"),
                (10.0, T_BAD, "Luôn có 1 người ở phòng điều khiển theo dõi kết quả cảm biến"),
                (T_BAD, 19.6, "Cảm biến báo sai: bao đặt lệch khỏi ô"),
                (19.6, 23.5, "Người điều khiển bấm DỪNG máy (giả định KCP, cần Phon-Tech xác nhận)"),
                (23.5, D + 1, "Xử lý sau khi dừng và vị trí phòng điều khiển: cần chốt với Phon-Tech")])
    corners(d); footer(d, 9)
    return im

# 10. Trạm xả tay dự phòng: bao đi thẳng qua cell vào băng tải ra (Phon-Tech xác nhận)
D_BACKUP = 15.0
def sc_backup(t, D):
    im, d = frame_base()
    c1 = cam_lerp(CAM_FULL, CAM_BOT, seg(t, 0, 1.2))
    cam = cam_lerp(c1, Cam(628, 800, 1.35), seg(t, 7.5, 9.5))
    period = 1.6; t0 = 2.4
    bags = []; n_taken = 0
    slots = sling_slots((629, 1115), rot=True)
    for i in range(9):
        ta = t0 + i * period
        if t < ta: break
        n_taken = i + 1
        u = seg(t, ta, ta + 0.7)
        src = slots[8 - i][0]
        if u < 1:
            bags.append((lerp_p(src, (BELT_X, 1040), u), lerp(0.0, -math.pi / 2, u)))
        else:
            y = 1040 - (t - ta - 0.7) * 48
            if y > 390: bags.append(((BELT_X, y), -math.pi / 2))
    st = {"slings": default_slings(), "robot": ((585, 792), False, 0), "robot_gray": True,
          "bags": bags, "station_n": NBAG - n_taken, "station_k": 1.0, "brush": t * 2,
          "bars": {"M": lin(t, 2.6, 5.0)}, "hl": {"M": 1.0}}
    draw_plant(d, cam, st)
    if t < 7.6:
        stamp(im, "ROBOT KHÔNG HOẠT ĐỘNG", t - 1.0, RED, (300, 540), -4, 16)
    kq = seg(t, 9.5, 10.0)
    if kq > 0:
        p0 = cam.P(BELT_X + 26, 912); p1 = cam.P(BELT_X + 26, 600)
        dashed(d, p0, p1, mix(CREAM, RED, kq), 2.5, 7, 5)
        arrow(d, (p1[0], p1[1] + 2), (p1[0], p1[1] - 10 * SS), mix(CREAM, RED, kq), 2, 10)
        p = cam.scr(BELT_X - 40, 728)
        note(d, p, "đi thẳng qua cell – cùng trục với băng tải ra", kq, RED, 12, "rm")
        note(d, (p[0], p[1] + 24), "(Phon-Tech xác nhận)", kq, MUTED, 11, "rm")
    card(d, "M", 820, 470, 400, seg(t, 1.6, 2.1) * (1 - seg(t, 7.3, 7.6)), "1 công nhân · Phon-Tech xác nhận")
    subs(d, t, [(0, 2.4, "Khi robot không hoạt động: dùng trạm xả tay dự phòng"),
                (2.4, 7.5, "1 công nhân lấy từng bao trên sling, đặt lên băng tải dự phòng"),
                (7.5, D + 1, "Bao đi thẳng qua cell vào băng tải ra – vẫn xuất hàng được")])
    chapter(im, "(9) TRẠM XẢ TAY DỰ PHÒNG", t)
    corners(d); footer(d, 10)
    return im

# 11. Tóm tắt chức năng
def sc_func(t, D):
    im, d = frame_base()
    chapter(im, "TÓM TẮT CHỨC NĂNG", t)
    codes = ["L", "R", "C", "V", "S", "K", "T", "X", "M"]
    for i, c in enumerate(codes):
        k = seg(t, 0.5 + i * 1.0, 0.9 + i * 1.0)
        if k <= 0: continue
        no, name, typ, fn, col = EL[c]
        y = 122 + i * 53 + 8 * (1 - k)
        d.rectangle([90 * SS, (y - 21) * SS, 1190 * SS, (y + 21) * SS], fill=mix(CREAM, mix(CREAM, col, 0.08), k))
        d.rectangle([90 * SS, (y - 21) * SS, 98 * SS, (y + 21) * SS], fill=mix(CREAM, col, k))
        badge(d, (125, y), no, col, 14, k)
        d.text((152 * SS, y * SS), name, font=F("serifb", 17), fill=mix(CREAM, col, k), anchor="lm")
        f = F("serif", 15); sz = 15
        while d.textlength(fn, font=f) > 620 * SS: sz -= 1; f = F("serif", sz)
        d.text((560 * SS, y * SS), fn, font=f, fill=mix(CREAM, INK, k), anchor="lm")
    subs(d, t, [(0, D + 1, "Chín cụm, một dòng chảy: sling vào – hút 3 bao – vệ sinh – ra xe – tự chất")], y=640)
    corners(d); footer(d, 11)
    return im

# 12. Số liệu (mỗi mục ~3,4 s)
STAT_T = 3.4
assert 40000 // 50 == 800 and 45000 // 50 == 900
assert abs(45 / 900 * 60 - 3.0) < 1e-9 and abs(45 / 800 * 60 - 3.375) < 1e-9
assert abs(3 / 900 * 3600 - 12) < 1e-9 and abs(3 / 800 * 3600 - 13.5) < 1e-9
assert round(34 / 45 * 60) == 45 and round(34 / 40 * 60) == 51
assert TH - 30 == 185
STATS = [
    ("Bao đường", "50 kg", "bản vẽ: 500 × 750 × 150 mm · KCP đo: 500 × 750 × 130 mm", "bag", "kcp"),
    ("Sling", "2.250 × 1.500 mm", "3 × 3 bao mỗi lớp · 5 lớp = 45 bao", "grid", "dwg"),
    ("Khối lượng", "2.250 kg", "45 × 50 kg · bản vẽ ghi 'sling + hàng' (To be confirm)", "weight", "dwg"),
    ("Công suất máy hút", "40–45 tấn/giờ", "= 800–900 bao/giờ", "rate", "pt"),
    ("Nhịp hút", "3 bao / 12–13,5 giây", "1 sling 45 bao: 3,0–3,4 phút · tính từ 40–45 tấn/giờ", "cycle", "calc"),
    ("Chất 1 xe 34T", "680 bao · 45–51 phút", "5 ngang × 9 lớp = 45 bao/hàng · 14 hàng + 2 hàng × 25 bao", "truckload", "kcp"),
    ("Băng tải ống lồng", "vươn tối đa 18 m", "chất cao tới cách trần 30 cm · thùng 34T: tối đa 185 cm", "reach", "pt"),
    ("Diện tích trong kho", f"≈ {A_TOTAL:.0f} m²", f"{vn1(AREA_W / 1000, 2)} × {vn1(AREA_D / 1000, 2)} m + dải ra xe ≈ {vn1(STRIP_L / 1000)} × {vn1(STRIP_W / 1000)} m (ước tính)", "plan", "dwg"),
    ("Chiều cao", "cao nhất 1,5 m", "điểm cao nhất của hệ thống băng tải", "height15", "pt"),
    ("Điện", "3 pha 380–440 V, 80 A", "3~380-440 + N + PE, 50 Hz · robot cell và băng tải", "power", "dwg"),
    ("Khí nén", "1/2\" · 6 bar", "lưu lượng khí: To be confirm", "air", "dwg"),
]
SRC = {"dwg": "nguồn: bản vẽ LA26-PTC-KCP-DEP-301026 (Phon-Tech, 20/10/2026)",
       "pt": "nguồn: Phon-Tech xác nhận 04/11/2026",
       "calc": "tính từ công suất 40–45 tấn/giờ (Phon-Tech)",
       "kcp": "nguồn: bản vẽ Phon-Tech + KCP: Trình tự chất bao xe 34T v2"}
def sc_stats(t, D):
    im, d = frame_base()
    chapter(im, "TÓM TẮT SỐ LIỆU", t)
    i = min(len(STATS) - 1, int(t // STAT_T)); tt = t - i * STAT_T
    title, big, small, kind, src = STATS[i]
    k = seg(tt, 0.05, 0.45)
    d.text((1238 * SS, 62 * SS), f"{i + 1}/{len(STATS)}", font=F("monob", 17), fill=INK, anchor="rm")
    for j in range(len(STATS)):
        x = 1238 - (len(STATS) - j) * 26
        d.rectangle([x * SS, 80 * SS, (x + 21) * SS, 86 * SS], fill=ORANGE if j < i else (INK if j == i else mix(CREAM, INK, 0.15)))
    d.text((100 * SS, (230 + 8 * (1 - k)) * SS), title.upper(), font=F("monob", 18), fill=mix(CREAM, MUTED, k), anchor="ls")
    f = F("serifb", 40); sz = 40
    while d.textlength(big, font=f) > 560 * SS: sz -= 1; f = F("serifb", sz)
    d.text((100 * SS, (290 + 8 * (1 - k)) * SS), big, font=f, fill=mix(CREAM, INK, k), anchor="ls")
    f2 = F("mono", 14); sz = 14
    while d.textlength(small, font=f2) > 580 * SS: sz -= 1; f2 = F("mono", sz)
    d.text((100 * SS, 330 * SS), small, font=f2, fill=mix(CREAM, INK, seg(tt, 0.3, 0.7)), anchor="ls")
    d.text((100 * SS, 560 * SS), SRC[src], font=F("mono", 11), fill=mix(CREAM, MUTED, k), anchor="ls")
    bx0, by0, bx1, by1 = 720, 130, 1190, 590
    d.rectangle([bx0 * SS, by0 * SS, bx1 * SS, by1 * SS], outline=INK, width=2 * SS)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    a = seg(tt, 0.2, 2.6)
    if kind == "bag":
        w, h = 120, 180
        d.rounded_rectangle([(cx - w / 2) * SS, (cy - h / 2) * SS, (cx + w / 2) * SS, (cy + h / 2) * SS], radius=18 * SS, fill=BAG_TOP, outline=INK, width=2 * SS)
        d.text((cx * SS, cy * SS), "50 kg", font=F("serifb", 24), fill=INK, anchor="mm")
        tag(d, (cx, cy + h / 2 + 30), "500 × 750 mm", RED, 13, "mm", a)
    elif kind == "grid":
        n = int(a * 9 + 1e-4)
        for j in range(n):
            r, c = j // 3, j % 3
            x = cx - 105 + c * 70; y = cy - 150 + r * 100
            d.rounded_rectangle([x * SS, y * SS, (x + 66) * SS, (y + 96) * SS], radius=10 * SS, fill=BAG_TOP, outline=INK, width=2 * SS)
        tag(d, (cx, cy + 180), f"{n}/9 bao", INK, 14, "mm", 1.0)
    elif kind == "weight":
        n = int(a * 45 + 1e-4)
        for j in range(45):
            r, c = j // 9, j % 9
            x = cx - 180 + c * 40; y = cy - 120 + r * 50
            d.rounded_rectangle([x * SS, y * SS, (x + 34) * SS, (y + 44) * SS], radius=6 * SS,
                                fill=BAG_TOP if j < n else mix(CREAM, INK, 0.05), outline=INK if j < n else mix(CREAM, INK, 0.25), width=SS)
        tag(d, (cx, cy + 170), f"{n} × 50 = {vn(n * 50)} kg", INK, 14, "mm", 1.0)
    elif kind == "rate":
        r = 130
        d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], 150, 390, fill=mix(CREAM, INK, 0.3), width=8 * SS)
        a0, a1 = 150 + 240 * 40 / 60, 150 + 240 * 45 / 60
        d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], a0, a1, fill=BRICK, width=14 * SS)
        for v_ in (0, 20, 40, 60):
            an = math.radians(150 + 240 * v_ / 60)
            d.text(((cx + (r + 22) * math.cos(an)) * SS, (cy + (r + 22) * math.sin(an)) * SS), str(v_), font=F("mono", 12), fill=INK, anchor="mm")
        an = math.radians(150 + 240 * lerp(0, 42.5, a) / 60)
        d.line([cx * SS, cy * SS, (cx + 100 * math.cos(an)) * SS, (cy + 100 * math.sin(an)) * SS], fill=INK, width=4 * SS)
        d.text((cx * SS, (cy + 70) * SS), "tấn/giờ", font=F("serif", 18), fill=INK, anchor="mm")
        tag(d, (cx, cy + 170), "= 800–900 bao/giờ", BRICK, 14, "mm", a)
    elif kind == "cycle":
        r = 110
        d.ellipse([(cx - r) * SS, (cy - 30 - r) * SS, (cx + r) * SS, (cy - 30 + r) * SS], outline=mix(CREAM, INK, 0.4), width=4 * SS)
        d.arc([(cx - r) * SS, (cy - 30 - r) * SS, (cx + r) * SS, (cy - 30 + r) * SS], -90, -90 + 360 * (tt / STAT_T), fill=BRICK, width=8 * SS)
        d.text((cx * SS, (cy - 30) * SS), "12–13,5 s", font=F("serifb", 24), fill=INK, anchor="mm")
        nb = 1 + int(clamp(tt / STAT_T) * 2.999)
        for j in range(nb):
            x = cx - 75 + j * 52
            d.rounded_rectangle([x * SS, (cy + 110) * SS, (x + 46) * SS, (cy + 170) * SS], radius=8 * SS, fill=BAG_TOP, outline=INK, width=2 * SS)
            d.text(((x + 23) * SS, (cy + 140) * SS), str(j + 1), font=F("monob", 16), fill=BRICK, anchor="mm")
    elif kind == "truckload":
        n = int(a * 16 + 1e-4)
        for r in range(16):
            nl = 9 if r < 14 else 5
            x = cx + 200 - (r + 1) * 25
            hh = nl * 16 if r < n else 0
            d.rectangle([x * SS, (cy + 140) * SS, (x + 22) * SS, (cy + 142) * SS], fill=INK)
            if hh: d.rectangle([x * SS, (cy + 140 - hh) * SS, (x + 22) * SS, (cy + 140) * SS], fill=BAG_TOP, outline=INK, width=SS)
        tag(d, (cx, cy + 175), f"{n}/16 hàng · {sum(45 if r < 14 else 25 for r in range(n))} bao", INK, 14, "mm", 1.0)
    elif kind == "reach":
        x0 = cx - 200; sc_ = 400 / 18
        d.rectangle([x0 * SS, (cy - 20) * SS, (x0 + 12.26 * sc_) * SS, (cy + 40) * SS], outline=NAVY, width=2 * SS)
        tag(d, (x0 + 12.26 * sc_ / 2, cy + 58), "thùng 34T dài 12,26 m", NAVY, 12, "mm", 1)
        L_ = lerp(1, 18, a)
        d.rectangle([x0 * SS, (cy - 4) * SS, (x0 + L_ * sc_) * SS, (cy + 24) * SS], fill=mix(CREAM, TEAL, 0.3), outline=TEAL, width=2 * SS)
        tag(d, (x0 + L_ * sc_, cy - 40), f"{vn1(L_, 0)} m", TEAL, 14, "mm", 1)
        tag(d, (cx, cy + 150), "chất cao tới: trần − 30 cm", RED, 13, "mm", a)
    elif kind == "plan":
        w1 = 200; h1 = w1 * AREA_D / AREA_W
        sc_ = w1 / AREA_W
        x0 = cx - 160; y0 = cy - h1 / 2 + 10
        kk = a
        d.rectangle([x0 * SS, y0 * SS, (x0 + w1 * kk) * SS, (y0 + h1) * SS], fill=mix(CREAM, ORANGE, 0.25), outline=RED, width=2 * SS)
        if kk >= 1:
            d.rectangle([(x0 + w1) * SS, y0 * SS, (x0 + w1 + STRIP_L * sc_) * SS, (y0 + max(4, STRIP_W * sc_)) * SS], fill=mix(CREAM, ORANGE, 0.4), outline=RED, width=SS)
        tag(d, (x0 + w1 / 2, y0 + h1 + 20), f"{vn1(AREA_W / 1000, 2)} m", RED, 12, "mm", a)
        tag(d, (x0 - 10, y0 + h1 / 2), f"{vn1(AREA_D / 1000, 2)} m", RED, 12, "rm", a)
    elif kind == "height15":
        gx = cx - 120; gy = cy + 150; sc_ = 150   # px/m
        d.line([(gx - 40) * SS, gy * SS, (gx + 300) * SS, gy * SS], fill=INK, width=3 * SS)
        hh = lerp(0, 1.5, a) * sc_
        d.rectangle([gx * SS, (gy - hh) * SS, (gx + 200) * SS, (gy - hh + 18) * SS], fill=mix(CREAM, TEAL, 0.3), outline=TEAL, width=2 * SS)
        arrow(d, ((gx + 240) * SS, gy * SS), ((gx + 240) * SS, (gy - hh) * SS), RED, 2, 9)
        tag(d, (gx + 250, gy - hh / 2), "1,5 m", RED, 14, "lm", a)
    elif kind == "power":
        for j in range(3):
            kk = seg(tt, 0.2 + j * 0.4, 0.6 + j * 0.4)
            y = cy - 90 + j * 70
            d.line([(cx - 150) * SS, y * SS, (cx - 150 + 300 * kk) * SS, y * SS], fill=GOLD, width=5 * SS)
            d.text(((cx - 170) * SS, y * SS), f"L{j + 1}", font=F("monob", 14), fill=INK, anchor="rm")
        tag(d, (cx, cy + 150), "80 A · 50 Hz", INK, 14, "mm", a)
    elif kind == "air":
        r = 120
        d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], 135, 405, fill=mix(CREAM, INK, 0.3), width=6 * SS)
        d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], 135, 135 + 270 * a * 0.6, fill=TEAL, width=6 * SS)
        ang = math.radians(135 + 270 * a * 0.6)
        d.line([cx * SS, cy * SS, (cx + 90 * math.cos(ang)) * SS, (cy + 90 * math.sin(ang)) * SS], fill=INK, width=3 * SS)
        d.text((cx * SS, (cy + 60) * SS), "6 bar", font=F("serifb", 26), fill=INK, anchor="mm")
        tag(d, (cx, cy + 170), "lưu lượng: To be confirm", RED, 13, "mm", a)
    subs(d, t, [(j * STAT_T, (j + 1) * STAT_T, f"{STATS[j][0]}: {STATS[j][1]}") for j in range(len(STATS))])
    corners(d); footer(d, 12)
    return im

# 13. Kết: điểm còn cần chốt
OPEN = ["Hút 3 bao, thả lần lượt từng bao – chốt sáng 05/11/2026",
        "Cảm biến sai → người phòng điều khiển bấm dừng? (giả định KCP)",
        "Vị trí phòng điều khiển; xử lý sau khi dừng máy",
        "Sàn xe cao thấp khác nhau – KCP kiểm tra, báo Phon-Tech",
        "Khung xanh có 4 tay xám ở cửa cell là thiết bị gì?",
        "Bao 130 hay 150 mm? Vỏ sling nặng bao nhiêu?",
        "Lưu lượng khí nén?",
        "Kích thước chính thức trạm dự phòng, dải ra xe (đang ước tính)",
        "Số bản vẽ 301026 / ngày 20/10; báo giá theo bản vẽ mới"]
def sc_end(t, D):
    im, d = frame_base()
    d.text((W / 2 * SS, 112 * SS), "Điểm còn cần chốt với Phon-Tech", font=F("serifb", 32), fill=mix(CREAM, INK, seg(t, 0.1, 0.6)), anchor="mm")
    for i, s in enumerate(OPEN):
        k = seg(t, 0.6 + i * 0.35, 1.0 + i * 0.35)
        if k <= 0: continue
        y = 168 + i * 46
        d.rectangle([210 * SS, (y - 19) * SS, 1070 * SS, (y + 19) * SS], fill=mix(CREAM, (255, 246, 230), k), outline=mix(CREAM, RED, k), width=SS)
        d.text((230 * SS, y * SS), f"({i + 1})", font=F("monob", 15), fill=mix(CREAM, RED, k), anchor="lm")
        d.text((280 * SS, y * SS), s, font=F("serif", 17), fill=mix(CREAM, INK, k), anchor="lm")
    corners(d); footer(d, 13)
    return im

SCENES = [("title", 5.0, sc_title), ("overview", 14.0, sc_overview), ("area", 16.0, sc_area),
          ("sling", 10.5, sc_sling), ("flow", D_FLOW, sc_flow), ("robot", D_ROBOT, sc_robot),
          ("journey", 17.0, sc_journey), ("truck", 24.0, sc_truck), ("sensor", D_SENSOR, sc_sensor),
          ("backup", D_BACKUP, sc_backup), ("func", 12.0, sc_func),
          ("stats", STAT_T * len(STATS), sc_stats), ("end", 7.5, sc_end)]
assert len(SCENES) == N_SC

XF = 8

def render(i_frame):
    t_abs = i_frame / FPS
    acc = 0.0
    for si, (name, D, fn) in enumerate(SCENES):
        if t_abs < acc + D or si == len(SCENES) - 1:
            t = t_abs - acc
            im = fn(t, D)
            fi = int(round(t * FPS))
            if si > 0 and fi < XF:
                pn, pD, pfn = SCENES[si - 1]
                prev = pfn(pD + t, pD)
                im = Image.blend(prev, im, (fi + 1) / (XF + 1))
            return im.resize((W, H), Image.LANCZOS).tobytes()
        acc += D

def total_frames(): return int(round(sum(s[1] for s in SCENES) * FPS))

def test_sheet(path="test_sheet.png", only=None):
    picks = []; acc = 0
    for name, D, fn in SCENES:
        if only is None or name in only:
            for f in (0.12, 0.45, 0.8, 0.97):
                picks.append(int((acc + D * f) * FPS))
        acc += D
    with Pool(4) as pool:
        raws = pool.map(render, picks)
    tiles = [Image.frombytes("RGB", (W, H), r).resize((640, 360), Image.LANCZOS) for r in raws]
    cols = 4 if len(tiles) >= 4 else len(tiles); rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (640 * cols, 360 * rows), "white")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(path); print("saved", path)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "test":
        test_sheet(sys.argv[2] if len(sys.argv) > 2 else "test_sheet.png", sys.argv[3].split(",") if len(sys.argv) > 3 else None)
    elif mode == "frame":
        Image.frombytes("RGB", (W, H), render(int(float(sys.argv[2]) * FPS))).save(sys.argv[3])
    else:
        n = total_frames()
        print("frames", n, "giây", n / FPS, flush=True)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", "scale=960:-2",
                              "-c:v", "libx264", "-crf", "30", "-preset", "slow",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, b in enumerate(pool.imap(render, range(n), chunksize=8)):
                p.stdin.write(b)
                if i % 250 == 0: print(f"{i}/{n}", flush=True)
        p.stdin.close(); p.wait()
        print("done", OUT, flush=True)
