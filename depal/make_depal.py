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
OUT = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "full" else "Depal_cach_hoat_dong_v2.mp4"

# ---------- màu ----------
CREAM = (243, 236, 220); INK = (29, 43, 58); ORANGE = (217, 119, 75)
RED = (178, 52, 44); MUTED = (110, 116, 120)
BAG_TOP = (252, 250, 244); BAG_LOW = (214, 206, 188)
PERSON = (196, 104, 124)

# mỗi thiết bị một màu, dùng nhất quán mọi nơi
BLUE = (44, 95, 160); PURPLE = (118, 74, 150); BRICK = (176, 64, 48)
GREEN = (38, 122, 64); GOLD = (176, 128, 10); TEAL = (16, 124, 128)
NAVY = (29, 43, 58); MAG = (160, 48, 108)

EL = {  # mã: (số, tên, loại, tác dụng, màu)
    "L": (1, "Băng con lăn cấp sling – trái", "băng tải con lăn", "đưa sling đầy vào vị trí xả giữa cell", BLUE),
    "R": (2, "Băng con lăn cấp sling – phải", "băng tải con lăn", "đưa sling đầy vào, luân phiên với bên trái", PURPLE),
    "C": (3, "Cell robot – vị trí xả sling", "robot gắp bao", "gắp từng bao trên sling, đặt lên băng ra", BRICK),
    "S": (4, "Băng tải ra (đoạn thẳng)", "băng tải", "đưa bao ra khỏi cell", GREEN),
    "K": (5, "Băng cong 90°", "băng tải cong", "đổi hướng bao về phía xe", GOLD),
    "T": (6, "Băng tải ống lồng", "vươn ra / thụt vào (Phon-Tech xác nhận)", "đưa bao vào thùng, tự rải trái → phải, chất 9 lớp", TEAL),
    "X": (7, "Thùng xe", "xe container bạt 34T", "nhận 680 bao = 34 tấn, không cần người xếp", NAVY),
    "M": (8, "Trạm xả tay dự phòng", "băng tải + 1 công nhân", "khi robot dừng: xả tay bao vào line", MAG),
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

CAM_FULL = Cam(1000, 712, 0.64)
CAM_ROW = Cam(625, 835, 1.7)
CAM_CELL = Cam(628, 790, 2.6)
CAM_TRUCK = Cam(1400, 372, 2.7)
CAM_BOT = Cam(628, 1000, 1.55)

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
    "S": [(BELT_X, 735), (BELT_X, 400)],
    "K": arc_pts(CURVE_C, CURVE_R, 180, 270),
    "T": [(683, 345), (TELE_END, 345)],
    "M": [(BELT_X, 1050), (BELT_X, 914)],
}
OUT_PATH = [PLACE] + PATH["S"][1:] + PATH["K"][1:] + PATH["T"][1:]

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

L_SEG = {k: plen(PATH[k]) for k in ("S", "K", "T")}
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
    sh = rot_rect(c, 10, 22, face)          # vai (khoảng 450 mm)
    wpoly(d, cam, sh, fill=mix(CREAM, col, 0.35), outline=col, w=1.2)
    p = cam.P(*c); r = cam.S(4.5)
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

def draw_robot(d, cam, tgt, carry=False, suction=0.0, gray=False, ang=-math.pi / 2):
    col = mix(BRICK, MUTED, 0.85) if gray else BRICK
    b = ROBOT_BASE
    el = ik(b, tgt)
    if carry: draw_bag(d, cam, tgt, ang)
    # tay robot
    wline(d, cam, [b, el], mix(CREAM, col, 0.85), 7)
    wline(d, cam, [el, tgt], mix(CREAM, col, 0.85), 5)
    wline(d, cam, [b, el, tgt], col, 1.2)
    for p, r in ((b, 9), (el, 5)):
        q = cam.P(*p); rr = cam.S(r)
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=mix(CREAM, col, 0.55), outline=col, width=LW(1.4))
    # đầu gắp hút: khung + 3 cốc hút
    g = rot_rect(tgt, BL * 0.8, BW * 0.7, ang)
    wpoly(d, cam, g, outline=col, w=1.6)
    for j in (-1, 0, 1):
        q = cam.P(tgt[0] + math.cos(ang) * j * BL * 0.25, tgt[1] + math.sin(ang) * j * BL * 0.25); rr = cam.S(3.2)
        fc = mix((60, 200, 90), CREAM, 0.0 if suction > 0.5 else 0.7)
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=fc, outline=col, width=LW(1))

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
    belt(d, cam, (BELT_X - BELT_HALF, 400, BELT_X + BELT_HALF, 735), EL["S"][4], K("S"))
    wrect(d, cam, (BELT_X - 17, 597, BELT_X + 17, 658), fill=mix(CREAM, EL["S"][4], 0.08), outline=EL["S"][4], w=1.2)
    p = cam.P(BELT_X, 627); r = cam.S(6)
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=EL["S"][4], width=LW(1))
    curve(d, cam, EL["K"][4], K("K"))
    tele(d, cam, EL["T"][4], K("T"))
    truck(d, cam, K("X"))
    belt(d, cam, (BELT_X - BELT_HALF, 912, BELT_X + BELT_HALF, 1053), EL["M"][4], K("M"), chevron=True)
    station(d, cam, K("M"))
    if not st.get("no_station_sling"):
        draw_sling(d, cam, (629, 1115), st.get("station_n", NBAG), rot=True, k=st.get("station_k", 0.55))
    for p_, f_ in st.get("people", [((462, 781), 0), ((462, 915), 0), ((795, 781), math.pi), ((795, 915), math.pi), ((650, 1068), -math.pi / 2)]):
        draw_person(d, cam, p_, f_)
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
        draw_robot(d, cam, rb[0], rb[1], rb[2], st.get("robot_gray", False))
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
    off = {"L": (0, -32), "R": (0, -32), "S": (-22, 0), "K": None, "T": (0, -26), "M": (-22, 0)}[n]
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

N_SC = 11
def footer(d, n, color=INK):
    f = F("mono", 12)
    d.text((66 * SS, 692 * SS), "KCP VIỆT NAM · LOGISTICS · MÁY DEPAL BAO · bản vẽ Phon-Tech 20/10/2026", font=f, fill=color, anchor="ls")
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
    d.text((W / 2 * SS, 210 * SS), "MÁY DEPAL BAO TỰ ĐỘNG", font=F("serifb", 50), fill=mix(CREAM, INK, k), anchor="mm")
    k2 = seg(t, 0.5, 1.1)
    d.text((W / 2 * SS, 278 * SS), "cách hoạt động: từ sling 45 bao tới thùng xe", font=F("serif", 30), fill=mix(CREAM, ORANGE, k2), anchor="mm")
    k3 = seg(t, 1.2, 1.7)
    d.text((W / 2 * SS, 340 * SS), "KCP Phú Yên · bản vẽ LA26-PTC-KCP-DEP-301026 · Phon-Tech · 20/10/2026",
           font=F("mono", 15), fill=mix(CREAM, INK, k3), anchor="mm")
    chips = ["01 · SLING VÀO", "02 · ROBOT GẮP", "03 · BĂNG RA XE", "04 · TỰ CHẤT LÊN XE"]
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
    ("S", (BELT_X, 500), (-70, 0)), ("K", (660, 360), (-60, -45)), ("T", (950, 345), (10, 55)),
    ("X", (1330, 300), (40, -40)), ("M", (630, 1150), (60, 25)),
]
def sc_overview(t, D):
    im, d = frame_base()
    cam = CAM_FULL
    hl = {}; bars = {}
    for i, (c, _, _) in enumerate(OV_TAGS):
        t0 = 1.2 + i * 1.15
        hl[c] = seg(t, t0, t0 + 0.4) * (1 - seg(t, t0 + 1.1, t0 + 1.5)) * 1.0
    draw_plant(d, cam, {"slings": [(POS_C, NBAG)] + default_slings(), "hl": hl,
                        "robot": (PLACE, False, 0)})
    for i, (c, wp, off) in enumerate(OV_TAGS):
        t0 = 1.2 + i * 1.15
        name_tag(d, cam, c, wp, off, seg(t, t0, t0 + 0.4), 13)
    # kích thước tổng
    kd = seg(t, 10.6, 11.2)
    if kd > 0:
        col = mix(CREAM, RED, kd)
        p0 = cam.P(337, 1185); p1 = cam.P(910, 1185)
        arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p0, col, 2, 9); arrow(d, ((p0[0] + p1[0]) / 2, p0[1]), p1, col, 2, 9)
        tag(d, ((p0[0] + p1[0]) / 2 / SS, p0[1] / SS), "13.258 mm", RED, 13, "mm", kd)
        q0 = cam.P(250, 323); q1 = cam.P(250, 925)
        arrow(d, (q0[0], (q0[1] + q1[1]) / 2), q0, col, 2, 9); arrow(d, (q0[0], (q0[1] + q1[1]) / 2), q1, col, 2, 9)
        tag(d, (q0[0] / SS, (q0[1] + q1[1]) / 2 / SS), "3.954 + 9.950 mm", RED, 12, "mm", kd)
    subs(d, t, [(0, 1.2, "Mặt bằng máy depal theo bản vẽ Phon-Tech ngày 20/10/2026"),
                (1.2, 10.4, "Tám cụm chính, đánh số theo hành trình của bao đường 50 kg"),
                (10.4, D + 1, "Chiều ngang tổng 13.258 mm – tăng 1.503 mm so với bản cũ 11.755 mm")])
    chapter(im, "TỔNG QUAN BỐ TRÍ", t)
    corners(d); footer(d, 2)
    return im

# 3. Sling hàng
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
    corners(d); footer(d, 3)
    return im

# 4. Sling vào từ hai bên
def sc_infeed(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_FULL, CAM_ROW, seg(t, 0, 1.2))
    # sling A (trái): xuất hiện ở đầu ngoài -> vị trí chờ -> giữa cell
    ka = seg(t, 1.3, 1.9)
    m1 = seg(t, 3.4, 5.6); m2 = seg(t, 6.0, 7.8)
    xa = lerp(lerp(POS_L[0][0], POS_L[2][0], m1), POS_C[0], m2)
    slings = [((xa, CY), NBAG, ka)] + default_slings()
    bars = {"L": lin(t, 3.4, 7.8), "R": lin(t, 8.6, 10.4)}
    hl = {"L": seg(t, 3.0, 3.4) * (1 - seg(t, 8.0, 8.4)), "R": seg(t, 8.4, 8.8)}
    draw_plant(d, cam, {"slings": slings, "bars": bars, "hl": hl, "robot": (PLACE, False, 0)})
    if t > 1.3:
        p = cam.scr(POS_L[0][0], CY - 70)
        note(d, (p[0] - 20, p[1] - 10), "đưa sling vào đầu băng: chưa rõ phương tiện", seg(t, 1.6, 2.0) * (1 - seg(t, 6.2, 6.6)), RED, 13, "lm")
    card(d, "L", 60, 90, 430, seg(t, 3.4, 3.9) * (1 - seg(t, 8.2, 8.5)))
    card(d, "R", 790, 90, 430, seg(t, 8.5, 9.0))
    if t > 9.6:
        p = cam.scr(POS_R[1][0], CY + 70)
        note(d, (p[0], p[1] + 12), "sling bên phải chờ lượt sau", seg(t, 9.6, 10.0), PURPLE, 13, "mm")
    subs(d, t, [(0, 3.3, "Sling đầy đặt ở đầu ngoài băng con lăn"),
                (3.3, 8.2, "Băng con lăn bên trái đưa sling vào vị trí xả giữa cell"),
                (8.2, D + 1, "Bên phải chờ sẵn – hai bên luân phiên cấp sling")])
    chapter(im, "(1)(2) SLING VÀO TỪ HAI BÊN", t)
    corners(d); footer(d, 4)
    return im

# 5. Robot gắp
PICK_ORDER = list(range(9))
def robot_state(t, t_start, cycles):
    """trả (đích, mang bao, hút, số bao đã đặt, chỉ số đang gắp, thời điểm đặt các bao)"""
    acc = t_start; placed = []
    for i, Tc in enumerate(cycles):
        slot_i = i % 9
        layer = i // 9
        pick = sling_slots(POS_C)[8 - slot_i][0]
        if t < acc + Tc:
            u = (t - acc) / Tc
            if u < 0.35: return (lerp_p(PLACE, pick, ss(u / 0.35)), False, 0, i, None, placed)
            if u < 0.48: return (pick, False, 1, i, None, placed)
            if u < 0.88: return (lerp_p(pick, PLACE, ss((u - 0.48) / 0.4)), True, 1, i, 8 - slot_i, placed)
            return (PLACE, False, 0, i + 1, None, placed + [acc + Tc * 0.88])
        placed.append(acc + Tc * 0.88)
        acc += Tc
    return (PLACE, False, 0, len(cycles), None, placed)

def lerp_p(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))

CYC5 = [2.0, 1.7, 1.5] + [5.4 / 42] * 42      # 3 bao chậm, 42 bao tua nhanh
BELT_V = 60.0                                  # px/s – minh họa

def belt_bags(t, placed, speed=BELT_V, until=400):
    out = []
    for tp in placed:
        s = (t - tp) * speed
        if s < 0: continue
        if PLACE[1] - s < until - 20: continue
        out.append(((PLACE[0], PLACE[1] - s), -math.pi / 2))
    # bỏ bao chồng nhau khi tua nhanh
    res = []
    for b in out:
        if all(abs(b[0][1] - r[0][1]) > BL * 1.05 for r in res): res.append(b)
    return res

def sc_robot(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_ROW, CAM_CELL, seg(t, 0, 1.0))
    tgt, carry, suc, done, hole, placed = robot_state(t, 0.8, CYC5)
    n_left = NBAG - done - (1 if carry else 0)
    n_left = max(0, n_left)
    t_empty = 0.8 + sum(CYC5)
    # sling rỗng -> mờ dần (chưa rõ đi đâu); sling phải vào thay
    k_out = seg(t, t_empty + 1.6, t_empty + 2.4)
    mR = seg(t, t_empty + 2.6, t_empty + 4.6)
    slings = []
    if k_out < 1: slings.append((POS_C, n_left, 1 - k_out, hole))
    xr = lerp(POS_R[1][0], POS_C[0], mR)
    slings += [((xr, CY), NBAG), (POS_R[0], NBAG)]
    st = {"slings": slings, "robot": (tgt, carry, suc), "bags": belt_bags(t, placed, 60 if t < 6.2 else 140),
          "bars": {"C": lin(t, 0.6, 2.2), "R": lin(t, t_empty + 2.6, t_empty + 4.6)}, "hl": {"C": 1.0}}
    draw_plant(d, cam, st)
    card(d, "C", 850, 100, 380, seg(t, 0.8, 1.3) * (1 - seg(t, t_empty + 0.6, t_empty + 1.0)),
         "gắp 1 bao/lần: theo đường đi bao vẽ trên bản vẽ (To be confirm)")
    # đồng hồ đếm bao
    f = F("monob", 17)
    d.text((1238 * SS, 62 * SS), f"CÒN {n_left}/45 BAO TRÊN SLING", font=f, fill=INK, anchor="rm")
    x0, x1, y = 1238 - 260, 1238, 80
    d.rectangle([x0 * SS, y * SS, x1 * SS, (y + 6) * SS], fill=mix(CREAM, INK, 0.15))
    d.rectangle([x0 * SS, y * SS, (x0 + (x1 - x0) * n_left / 45) * SS, (y + 6) * SS], fill=BRICK if n_left else ORANGE)
    if 6.0 < t < t_empty:
        tag(d, (100, 130), "TUA NHANH >>", INK, 14, "lm", 1.0)
    if t >= t_empty + 0.6:
        stamp(im, "SLING RỖNG ĐI ĐÂU: CHƯA RÕ", t - t_empty - 0.6, RED, (250, 140), -4, 18)
    subs(d, t, [(0, 6.0, "Robot gắp từng bao trên sling, đặt lên đầu băng tải ra"),
                (6.0, t_empty, "Gắp hết lớp trên mới xuống lớp dưới – 5 lớp, 45 bao"),
                (t_empty, t_empty + 2.6, "Sling rỗng: bản vẽ chưa thể hiện được đưa đi đâu"),
                (t_empty + 2.6, D + 1, "Sling bên phải vào thay – hai bên luân phiên")])
    chapter(im, "(3) ROBOT GẮP BAO", t)
    corners(d); footer(d, 5)
    return im

# 6. Hành trình bao trên băng tải
J = [("S", 0.6, 4.6), ("K", 4.6, 6.6), ("T", 6.6, 13.6)]
def journey_s(t):
    """quãng đường bao đi trên OUT_PATH"""
    s0 = math.dist(PLACE, PATH["S"][0]) * 0  # bắt đầu tại điểm đặt
    off = 0.0
    base = math.dist(PLACE, (BELT_X, 735))
    lens = {"S": math.dist(PLACE, PATH["S"][1]), "K": L_SEG["K"], "T": L_SEG["T"]}
    for code, t0, t1 in J:
        if t < t1:
            return off + lens[code] * ss(clamp((t - t0) / (t1 - t0))) if t >= t0 else off
        off += lens[code]
    return off

def sc_journey(t, D):
    im, d = frame_base()
    s = journey_s(t)
    p, a = ppoint(OUT_PATH, s)
    z = 2.3 if t < 6.6 else lerp(2.3, 1.7, seg(t, 6.6, 8.0))
    tgt_cam = Cam(p[0] + (0 if t < 6.6 else 60), p[1] + 40, z)
    if t < 1.0:
        cam = cam_lerp(CAM_CELL, tgt_cam, seg(t, 0, 1.0))
    else:
        cam = tgt_cam
    bars = {"C": 1.0}
    for code, t0, t1 in J: bars[code] = lin(t, t0, t1)
    bags = [(p, a)]
    # bao trước/sau trên băng (minh họa dòng bao)
    for ds_ in (-120, 120, 240):
        s2 = s + ds_
        if 0 < s2 < L_OUT: bags.append(ppoint(OUT_PATH, s2))
    hl = {code: (1.0 if t0 <= t < t1 + 0.3 else 0.0) for code, t0, t1 in J}
    draw_plant(d, cam, {"slings": [(POS_C, 38)] + default_slings()[1:], "robot": (PLACE, False, 0), "bags": bags,
                        "bars": bars, "hl": hl})
    # vòng đánh dấu bao đang theo dõi
    q = cam.P(*p); r = cam.S(26)
    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], outline=ORANGE, width=LW(2.5))
    for code, t0, t1 in J:
        k = seg(t, t0, t0 + 0.4) * (1 - seg(t, t1 - 0.2, t1 + 0.1))
        if code == "T" and t > 12.5: k = seg(t, t0, t0 + 0.4)
        extra = "vươn ra / thụt vào theo hàng đang chất: Phon-Tech xác nhận" if code == "T" else None
        card(d, code, 820, 90, 400, k, extra)
    subs(d, t, [(0, 4.6, "Bao ra khỏi cell theo băng tải thẳng"),
                (4.6, 6.6, "Băng cong 90° đổi hướng bao về phía xe"),
                (6.6, D + 1, "Băng tải ống lồng đưa bao vào sâu trong thùng xe")])
    chapter(im, "(4)(5)(6) BAO RA XE", t)
    corners(d); footer(d, 6)
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

def sc_truck(t, D):
    im, d = frame_base()
    chapter(im, "(6)(7) BĂNG ỐNG LỒNG TỰ CHẤT LÊN XE", t)
    col = EL["T"][4]
    y1 = TY0 + TWD * TS
    roof = TFLOOR - TH * TS
    x_rear = txr(TL)
    # ---- khung thùng: nhìn từ trên ----
    d.text((x_rear * SS, (TY0 - 10) * SS), "NHÌN TỪ TRÊN", font=F("mono", 12), fill=INK, anchor="ls")
    d.rectangle([x_rear * SS, TY0 * SS, TX_FRONT * SS, y1 * SS], fill=mix(CREAM, NAVY, 0.05), outline=NAVY, width=3 * SS)
    cab = [(TX_FRONT, TY0 + 12), (TX_FRONT + 70, TY0 + 12), (TX_FRONT + 92, TY0 + 34), (TX_FRONT + 92, y1 - 34), (TX_FRONT + 70, y1 - 12), (TX_FRONT, y1 - 12)]
    d.polygon([(x * SS, y * SS) for x, y in cab], fill=mix(CREAM, NAVY, 0.14), outline=NAVY, width=2 * SS)
    tag(d, (x_rear, y1 + 16), "cửa sau", MUTED, 11, "lm", 1, bold=False)
    tag(d, (TX_FRONT, y1 + 16), "đầu thùng (sát cabin)", MUTED, 11, "rm", 1, bold=False)
    # ---- khung thùng: nhìn ngang ----
    d.text((x_rear * SS, (roof - 10) * SS), "NHÌN NGANG", font=F("mono", 12), fill=INK, anchor="ls")
    d.rectangle([x_rear * SS, roof * SS, TX_FRONT * SS, TFLOOR * SS], fill=mix(CREAM, NAVY, 0.03), outline=mix(CREAM, NAVY, 0.5), width=SS)
    d.line([x_rear * SS, TFLOOR * SS, TX_FRONT * SS, TFLOOR * SS], fill=NAVY, width=4 * SS)
    dashed(d, (x_rear * SS, (TFLOOR - TWALL * TS) * SS), (TX_FRONT * SS, (TFLOOR - TWALL * TS) * SS), mix(CREAM, NAVY, 0.6), 1.5, 8, 6)
    d.text(((x_rear + 6) * SS, (TFLOOR - TWALL * TS - 4) * SS), "thành 80 cm", font=F("mono", 11), fill=mix(CREAM, NAVY, 0.7), anchor="ls")
    d.rectangle([TX_FRONT * SS, (TFLOOR - 200 * TS) * SS, (TX_FRONT + 92) * SS, TFLOOR * SS], fill=mix(CREAM, NAVY, 0.14), outline=NAVY, width=2 * SS)
    # ---- bao đã chất ----
    total = 0; cur_r = 0
    for r, t0, dur, times in PLAN:
        n = sum(1 for x in times if x <= t)
        total += n
        if n: cur_r = r
        xa, xb = txr(RL * (r + 1)), txr(RL * r)
        for i in range(n):
            k, c = i // 5, i % 5
            if k == (n - 1) // 5 or n == len(times):   # top view: chỉ vẽ lớp trên cùng
                pass
        for c in range(5):
            cnt = sum(1 for i in range(n) if i % 5 == c)
            if cnt:
                ya = TY0 + c * RW * TS; yb = ya + RW * TS
                shade = mix(BAG_TOP, BAG_LOW, 0.6 * (1 - cnt / 9))
                d.rounded_rectangle([(xa + 2) * SS, (ya + 2) * SS, (xb - 2) * SS, (yb - 2) * SS], radius=4 * SS, fill=shade, outline=INK, width=SS)
        for k in range(row_layers(r)):
            cnt = sum(1 for i in range(n) if i // 5 == k)
            if cnt:
                za = TFLOOR - (k + 1) * RH * TS; zb = TFLOOR - k * RH * TS
                d.rounded_rectangle([(xa + 2) * SS, (za + 1) * SS, (xb - 2) * SS, (zb - 1) * SS], radius=3 * SS,
                                    fill=BAG_TOP if cnt == 5 else mix(CREAM, BAG_TOP, 0.6), outline=INK if cnt == 5 else MUTED, width=SS)
    # ---- băng tải ống lồng + đầu rải ----
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
    # nhìn ngang: băng nghiêng lên tới đầu rải theo lớp đang chất
    zh = TFLOOR - (k * RH + RH + 6) * TS
    zin = TFLOOR - 95 * TS
    pts = [(x_in, zin), (lerp(x_in, xh, 0.45), lerp(zin, zh, 0.45)), (lerp(x_in, xh, 0.75), lerp(zin, zh, 0.75)), (xh, zh)]
    for (p0, p1), w in zip(zip(pts[:-1], pts[1:]), (12, 10, 8)):
        d.line([p0[0] * SS, p0[1] * SS, p1[0] * SS, p1[1] * SS], fill=col, width=w * SS)
    d.rectangle([(xh + 2) * SS, (zh - 8) * SS, (xh + 20) * SS, (zh + 8) * SS], fill=col, outline=INK, width=SS)
    # bao đang được rải (chỉ ở hàng chậm)
    if r_act is not None and PLAN[r_act][2] >= 2:
        sx0, sx1 = txr(RL * (r_act + 1)), txr(RL * r_act)
        d.rounded_rectangle([(sx0 + 3) * SS, (yh - RW * TS / 2 + 3) * SS, (sx1 - 3) * SS, (yh + RW * TS / 2 - 3) * SS],
                            radius=4 * SS, fill=BAG_TOP, outline=ORANGE, width=2 * SS)
    # ---- chú thích động ----
    if r_act == 0 or (PLAN[0][1] + PLAN[0][2] <= t < PLAN[1][1]):
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
        tag(d, (txr(RL * 1.5), roof + 26), "← thụt lại 75 cm", col, 12, "mm", ka)
    # bộ đếm
    f = F("monob", 17)
    d.text((1238 * SS, 62 * SS), f"ĐÃ CHẤT {total}/680 BAO", font=f, fill=INK, anchor="rm")
    xa0, xa1 = 1238 - 230, 1238
    d.rectangle([xa0 * SS, 80 * SS, xa1 * SS, 86 * SS], fill=mix(CREAM, INK, 0.15))
    d.rectangle([xa0 * SS, 80 * SS, (xa0 + (xa1 - xa0) * total / 680) * SS, 86 * SS], fill=col if total < 680 else ORANGE)
    d.text((1238 * SS, 104 * SS), f"HÀNG {cur_r + 1}/16", font=F("mono", 13), fill=INK, anchor="rm")
    d.text((1238 * SS, 400 * SS), "cơ chế vươn/thụt, tự rải bao: Phon-Tech xác nhận · sơ đồ chất: Trình tự chất bao xe 34T v2 (KCP)",
           font=F("mono", 10), fill=MUTED, anchor="rs")
    if t > T_DONE + 0.4:
        stamp(im, "XONG 1 XE · 680 BAO · 34 TẤN", t - T_DONE - 0.4, ORANGE, (W / 2, 362), -3, 20)
    subs(d, t, [(0, T_START, "Băng tải ống lồng vươn hết cỡ vào sát đầu thùng xe"),
                (T_START, PLAN[0][1] + PLAN[0][2], "Đầu băng tự rải bao từ trái sang phải, đủ 5 bao mới lên lớp trên"),
                (PLAN[0][1] + PLAN[0][2], PLAN[2][1], "Đủ 9 lớp = 45 bao, băng thụt lại 75 cm để chất hàng tiếp theo"),
                (PLAN[2][1], T_DONE + 0.4, "Lặp lại tới hàng 16 – không cần người trong thùng xe"),
                (T_DONE + 0.4, D + 1, "14 hàng × 45 bao + 2 hàng × 25 bao = 680 bao = 34 tấn")])
    corners(d); footer(d, 7)
    return im

# 8. Trạm xả tay dự phòng
def sc_backup(t, D):
    im, d = frame_base()
    cam = cam_lerp(CAM_FULL, CAM_BOT, seg(t, 0, 1.2))
    period = 1.6; t0 = 2.4
    bags = []
    n_taken = 0
    worker = (650, 1068)
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
            s = (t - ta - 0.7) * 45
            y = 1040 - s
            if y > 918: bags.append(((BELT_X, y), -math.pi / 2))
    st = {"slings": [(POS_C, 20)] + default_slings(), "robot": ((640, 820), False, 0), "robot_gray": True,
          "bags": bags, "station_n": NBAG - n_taken, "station_k": 1.0,
          "bars": {"M": lin(t, 2.6, 5.0)}, "hl": {"M": 1.0}}
    draw_plant(d, cam, st)
    stamp(im, "ROBOT DỪNG", t - 1.0, RED, (300, 540), -4, 18)
    # đường nối qua cell: chưa rõ
    kq = seg(t, 6.5, 7.0)
    if kq > 0:
        p0 = cam.P(BELT_X + 30, 905); p1 = cam.P(BELT_X + 30, 745)
        dashed(d, p0, p1, mix(CREAM, RED, kq), 2.5, 7, 5)
        arrow(d, (p1[0], p1[1] + 2), (p1[0], p1[1] - 10 * SS), mix(CREAM, RED, kq), 2, 10)
        note(d, (cam.scr(BELT_X + 40, 945)[0], cam.scr(BELT_X + 40, 945)[1]),
             "bao đi tiếp qua cell ra băng (4): bản vẽ chưa thể hiện rõ", kq, RED, 12, "lm")
    card(d, "M", 820, 470, 400, seg(t, 1.6, 2.1), "chức năng dự phòng: đã chốt với Phòng Logistics")
    subs(d, t, [(0, 2.4, "Khi robot dừng, dùng trạm xả tay dự phòng phía dưới"),
                (2.4, 6.5, "Công nhân lấy từng bao trên sling, đặt lên băng tải"),
                (6.5, D + 1, "Băng tải đưa bao về phía cell để vào line ra xe")])
    chapter(im, "(8) TRẠM XẢ TAY DỰ PHÒNG", t)
    corners(d); footer(d, 8)
    return im

# 9. Tóm tắt chức năng
def sc_func(t, D):
    im, d = frame_base()
    chapter(im, "TÓM TẮT CHỨC NĂNG", t)
    codes = ["L", "R", "C", "S", "K", "T", "X", "M"]
    for i, c in enumerate(codes):
        k = seg(t, 0.5 + i * 1.1, 0.9 + i * 1.1)
        if k <= 0: continue
        no, name, typ, fn, col = EL[c]
        y = 128 + i * 58 + 8 * (1 - k)
        d.rectangle([90 * SS, (y - 22) * SS, 1190 * SS, (y + 22) * SS], fill=mix(CREAM, mix(CREAM, col, 0.08), k))
        d.rectangle([90 * SS, (y - 22) * SS, 98 * SS, (y + 22) * SS], fill=mix(CREAM, col, k))
        badge(d, (125, y), no, col, 14, k)
        d.text((152 * SS, y * SS), name, font=F("serifb", 18), fill=mix(CREAM, col, k), anchor="lm")
        d.text((560 * SS, y * SS), fn, font=F("serif", 16), fill=mix(CREAM, INK, k), anchor="lm")
    subs(d, t, [(0, D + 1, "Tám cụm, một dòng chảy: sling vào – robot gắp – băng ra – tự chất lên xe")], y=640)
    corners(d); footer(d, 9)
    return im

# 10. Số liệu (mỗi mục ~3,4 s)
STAT_T = 3.4
STATS = [
    ("Bao đường", "50 kg", "bản vẽ: 500 × 750 × 150 mm · KCP đo: 500 × 750 × 130 mm", "bag"),
    ("Sling", "2.250 × 1.500 mm", "3 × 3 bao mỗi lớp", "grid"),
    ("Số lớp", "5 lớp = 45 bao", "9 bao × 5 lớp", "layers"),
    ("Chiều cao hàng", "650 – 750 mm", "bản vẽ 5 × 150 = 750 · KCP 5 × 130 = 650 (To be confirm)", "height"),
    ("Khối lượng", "2.250 kg", "45 × 50 kg · bản vẽ ghi 'sling + hàng' (To be confirm)", "weight"),
    ("Chất xe 34T", "680 bao = 34 tấn", "5 ngang × 9 lớp = 45 bao/hàng · 14 hàng + 2 hàng × 25 bao", "truckload"),
    ("Mặt bằng", "13.258 mm ngang", "bản cũ 11.755 mm (+1.503) · sâu 3.954 + 9.950 mm", "plan"),
    ("Điện", "3 pha 380–440 V, 80 A", "3~380-440 + N + PE, 50 Hz · robot cell và băng tải", "power"),
    ("Khí nén", "1/2\" · 6 bar", "lưu lượng khí: To be confirm", "air"),
    ("Công suất", "chưa có số liệu", "bản vẽ chưa ghi bao/giờ – cần hỏi Phon-Tech", "rate"),
]
def sc_stats(t, D):
    im, d = frame_base()
    chapter(im, "TÓM TẮT SỐ LIỆU", t)
    i = min(len(STATS) - 1, int(t // STAT_T)); tt = t - i * STAT_T
    title, big, small, kind = STATS[i]
    k = seg(tt, 0.05, 0.45)
    d.text((1238 * SS, 62 * SS), f"{i + 1}/{len(STATS)}", font=F("monob", 17), fill=INK, anchor="rm")
    # thanh tiến độ mục
    for j in range(len(STATS)):
        x = 960 + j * 30
        d.rectangle([x * SS, 80 * SS, (x + 24) * SS, 86 * SS], fill=ORANGE if j < i else (INK if j == i else mix(CREAM, INK, 0.15)))
    d.text((100 * SS, (230 + 8 * (1 - k)) * SS), title.upper(), font=F("monob", 18), fill=mix(CREAM, MUTED, k), anchor="ls")
    col = RED if kind == "rate" else INK
    f = F("serifb", 40); sz = 40
    while d.textlength(big, font=f) > 560 * SS: sz -= 1; f = F("serifb", sz)
    d.text((100 * SS, (290 + 8 * (1 - k)) * SS), big, font=f, fill=mix(CREAM, col, k), anchor="ls")
    f2 = F("mono", 14); sz = 14
    while d.textlength(small, font=f2) > 580 * SS: sz -= 1; f2 = F("mono", sz)
    d.text((100 * SS, 330 * SS), small, font=f2, fill=mix(CREAM, INK, seg(tt, 0.3, 0.7)), anchor="ls")
    d.text((100 * SS, 560 * SS), "nguồn: bản vẽ LA26-PTC-KCP-DEP-301026 (Phon-Tech, 20/10/2026)" + (" · KCP: Trình tự chất bao xe 34T v2" if kind in ("bag", "height", "truckload") else ""),
           font=F("mono", 11), fill=mix(CREAM, MUTED, k), anchor="ls")
    # khung minh họa phải
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
    elif kind == "layers":
        n = int(a * 5 + 1e-4)
        for L in range(n):
            y = cy + 120 - L * 46
            for c in range(3):
                d.rounded_rectangle([(cx - 135 + c * 90) * SS, (y - 42) * SS, (cx - 49 + c * 90) * SS, y * SS], radius=12 * SS, fill=BAG_TOP, outline=INK, width=2 * SS)
        tag(d, (cx, cy + 170), f"{n * 9}/45 bao", INK, 14, "mm", 1.0)
    elif kind == "height":
        hh = lerp(0, 300, a)
        for xx, lab, hv, c in ((cx - 90, "750", hh, MUTED), (cx + 90, "650", hh * 650 / 750, RED)):
            d.rectangle([(xx - 50) * SS, (cy + 170 - hv) * SS, (xx + 50) * SS, (cy + 170) * SS], fill=mix(CREAM, c, 0.15), outline=c, width=2 * SS)
            arrow(d, ((xx + 65) * SS, (cy + 170) * SS), ((xx + 65) * SS, (cy + 170 - hv) * SS), c, 2, 9)
            tag(d, (xx, cy + 195), lab + " mm", c, 13, "mm", a)
        tag(d, (cx - 90, cy - 170), "bản vẽ", MUTED, 12, "mm", 1); tag(d, (cx + 90, cy - 170), "KCP đo", RED, 12, "mm", 1)
    elif kind == "weight":
        n = int(a * 45 + 1e-4)
        for j in range(45):
            r, c = j // 9, j % 9
            x = cx - 180 + c * 40; y = cy - 120 + r * 50
            d.rounded_rectangle([x * SS, y * SS, (x + 34) * SS, (y + 44) * SS], radius=6 * SS,
                                fill=BAG_TOP if j < n else mix(CREAM, INK, 0.05), outline=INK if j < n else mix(CREAM, INK, 0.25), width=SS)
        tag(d, (cx, cy + 170), f"{n} × 50 = {vn(n * 50)} kg", INK, 14, "mm", 1.0)
    elif kind == "truckload":
        n = int(a * 16 + 1e-4)
        for r in range(16):
            nl = 9 if r < 14 else 5
            x = cx + 200 - (r + 1) * 25
            hh = nl * 16 if r < n else 0
            d.rectangle([x * SS, (cy + 140) * SS, (x + 22) * SS, (cy + 142) * SS], fill=INK)
            if hh: d.rectangle([x * SS, (cy + 140 - hh) * SS, (x + 22) * SS, (cy + 140) * SS], fill=BAG_TOP, outline=INK, width=SS)
        tag(d, (cx, cy + 175), f"{n}/16 hàng · {sum(45 if r < 14 else 25 for r in range(n))} bao", INK, 14, "mm", 1.0)
    elif kind == "plan":
        w1 = 380 * 11755 / 13258; w2 = 380
        y = cy - 40
        d.rectangle([(cx - w1 / 2) * SS, (y - 30) * SS, (cx + w1 / 2) * SS, (y + 30) * SS], outline=MUTED, width=2 * SS)
        tag(d, (cx, y), "bản cũ 11.755", MUTED, 12, "mm", 1)
        y2 = cy + 70; ww = lerp(w1, w2, a)
        d.rectangle([(cx - ww / 2) * SS, (y2 - 30) * SS, (cx + ww / 2) * SS, (y2 + 30) * SS], outline=RED, width=3 * SS)
        tag(d, (cx, y2), "20/10/2026: 13.258", RED, 12, "mm", 1)
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
    elif kind == "rate":
        r = 120
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], outline=mix(CREAM, INK, 0.4), width=4 * SS)
        for j in range(12):
            an = math.radians(j * 30)
            d.line([(cx + 105 * math.cos(an)) * SS, (cy + 105 * math.sin(an)) * SS, (cx + 118 * math.cos(an)) * SS, (cy + 118 * math.sin(an)) * SS], fill=INK, width=2 * SS)
        an = math.radians(-90 + 360 * (tt / STAT_T))
        d.line([cx * SS, cy * SS, (cx + 95 * math.cos(an)) * SS, (cy + 95 * math.sin(an)) * SS], fill=RED, width=4 * SS)
        d.text((cx * SS, (cy + 50) * SS), "? bao/giờ", font=F("serifb", 26), fill=RED, anchor="mm")
    subs(d, t, [(j * STAT_T, (j + 1) * STAT_T, f"{STATS[j][0]}: {STATS[j][1]}") for j in range(len(STATS))])
    corners(d); footer(d, 10)
    return im

# 11. Kết: điểm còn mở
OPEN = ["Sling rỗng đưa đi đâu?", "Phương tiện đưa sling vào đầu băng?", "Công suất (bao/giờ)?",
        "Robot gắp 1 hay nhiều bao/lần?", "Bao 130 hay 150 mm? Vỏ sling nặng bao nhiêu?", "Lưu lượng khí nén?",
        "Đường bao từ trạm dự phòng qua cell?", "Băng ống lồng: tầm vươn tối đa, nhịp rải bao?"]
def sc_end(t, D):
    im, d = frame_base()
    d.text((W / 2 * SS, 120 * SS), "Điểm cần Phon-Tech xác nhận", font=F("serifb", 34), fill=mix(CREAM, INK, seg(t, 0.1, 0.6)), anchor="mm")
    for i, s in enumerate(OPEN):
        k = seg(t, 0.6 + i * 0.35, 1.0 + i * 0.35)
        if k <= 0: continue
        y = 180 + i * 48
        d.rectangle([250 * SS, (y - 20) * SS, 1030 * SS, (y + 20) * SS], fill=mix(CREAM, (255, 246, 230), k), outline=mix(CREAM, RED, k), width=SS)
        d.text((270 * SS, y * SS), f"({i + 1})", font=F("monob", 15), fill=mix(CREAM, RED, k), anchor="lm")
        d.text((320 * SS, y * SS), s, font=F("serif", 18), fill=mix(CREAM, INK, k), anchor="lm")
    stamp(im, "CHƯA CẬP NHẬT BÁO GIÁ THEO BẢN VẼ MỚI", t - 3.6, ORANGE, (W / 2, 590), -3, 16)
    corners(d); footer(d, 11)
    return im

SCENES = [("title", 5.0, sc_title), ("overview", 13.0, sc_overview), ("sling", 10.5, sc_sling),
          ("infeed", 11.5, sc_infeed), ("robot", 16.5, sc_robot), ("journey", 14.5, sc_journey),
          ("truck", 24.0, sc_truck), ("backup", 11.5, sc_backup), ("func", 11.0, sc_func),
          ("stats", STAT_T * len(STATS), sc_stats), ("end", 7.0, sc_end)]
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
