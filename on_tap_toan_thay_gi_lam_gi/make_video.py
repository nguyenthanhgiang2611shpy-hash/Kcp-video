# -*- coding: utf-8 -*-
"""Video ôn bài cho bé: Tờ tra nhanh "Thấy gì thì làm gì" (có giọng đọc + đố vui).

Dựng bằng PIL + ffmpeg. Giọng đọc: Piper TTS, giọng vi_VN-vais1000-medium (offline).
Chạy:  PIPER_MODEL=/đường/dẫn/vi_VN-vais1000-medium.onnx python3 make_video.py
"""
import os, subprocess, math, wave, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "On_tap_Thay_gi_lam_gi.mp4")
CACHE = os.path.join(HERE, ".tts_cache")
MODEL = os.environ.get("PIPER_MODEL", "vi_VN-vais1000-medium.onnx")
W, H, SS, FPS, SR = 1280, 720, 2, 24, 22050
os.makedirs(CACHE, exist_ok=True)

# ---------- màu ----------
BG = (250, 246, 236); INK = (38, 44, 56); MUTED = (110, 116, 128)
GRAY = (226, 229, 236); GRAY_E = (150, 156, 168)
TEAL = (14, 96, 84); TEAL_L = (196, 240, 226); TEAL_E = (40, 170, 140)
ORANGE = (238, 132, 36); RED = (214, 64, 56); GREEN = (40, 156, 88)
BLUE = (52, 110, 200); YELLOW = (255, 200, 40); BROWN = (140, 90, 50)
GRASS = (200, 232, 180); WHITE = (255, 255, 255)

_fc = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _fc:
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
        _fc[k] = ImageFont.truetype(p, size * SS)
    return _fc[k]

def S(v): return int(round(v * SS))

# ---------- vẽ cơ bản (toạ độ theo khung 1280×720) ----------
def text(d, xy, s, size=28, bold=False, fill=INK, anchor="mm"):
    d.text((S(xy[0]), S(xy[1])), s, font=F(size, bold), fill=fill, anchor=anchor)

def twidth(d, s, size, bold=False): return d.textlength(s, font=F(size, bold)) / SS

def rrect(d, box, r=16, fill=None, outline=None, width=2):
    d.rounded_rectangle([S(box[0]), S(box[1]), S(box[2]), S(box[3])], radius=S(r),
                        fill=fill, outline=outline, width=S(width) if outline else 0)

def line(d, pts, fill=INK, width=3):
    d.line([(S(x), S(y)) for x, y in pts], fill=fill, width=S(width), joint="curve")

def arrow(d, x0, y, x1, fill=GRAY_E, width=4):
    line(d, [(x0, y), (x1 - 4, y)], fill, width)
    d.polygon([(S(x1), S(y)), (S(x1 - 16), S(y - 10)), (S(x1 - 16), S(y + 10))], fill=fill)

def circle(d, cx, cy, r, fill=None, outline=None, width=3):
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=fill, outline=outline,
              width=S(width) if outline else 0)

def star(d, cx, cy, r, fill=YELLOW):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((S(cx + rr * math.cos(a)), S(cy + rr * math.sin(a))))
    d.polygon(pts, fill=fill)

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

# ---------- các khối nội dung ----------
RULES = [
    ("dài hơn", "Cộng", "rộng + phần hơn"),
    ("đi vòng quanh", "Chu vi", "(dài + rộng) × 2"),
    ("chừa cửa", "Trừ", "bề rộng cửa"),
    ("nhiều số cộng", "Ghép số tròn", "dùng ngoặc"),
]

def rule_row(i, y, x0=200, hl=False, show_right=True, lw=380, rw=420, h=86):
    key, act, sub = RULES[i]
    def draw(d, ts):
        rrect(d, (x0, y, x0 + lw, y + h), 16, GRAY, ORANGE if hl else GRAY_E, 4 if hl else 2)
        text(d, (x0 + lw / 2, y + h / 2), key, 32, True, INK)
        if show_right:
            ax = x0 + lw + 14; bx = x0 + lw + 80
            arrow(d, ax, y + h / 2, bx - 6)
            rrect(d, (bx, y, bx + rw, y + h), 16, TEAL, TEAL_E, 2)
            text(d, (bx + rw / 2, y + h * 0.36), act, 32, True, WHITE)
            text(d, (bx + rw / 2, y + h * 0.74), sub, 22, False, TEAL_L)
    return draw

def right_card(i, x, y, w=420, h=86):
    key, act, sub = RULES[i]
    def draw(d, ts):
        rrect(d, (x, y, x + w, y + h), 16, TEAL, TEAL_E, 2)
        text(d, (x + w / 2, y + h * 0.36), act, 32, True, WHITE)
        text(d, (x + w / 2, y + h * 0.74), sub, 22, False, TEAL_L)
    return draw

def big_title(s, y, size=56, fill=INK, bold=True):
    return lambda d, ts: text(d, (W / 2, y), s, size, bold, fill)

def label(s, x, y, size=28, fill=INK, bold=False, anchor="mm"):
    return lambda d, ts: text(d, (x, y), s, size, bold, fill, anchor)

def math_line(parts, x, y, size=40):
    """parts: list of (chuỗi, màu). Vẽ liền nhau, căn trái tại x."""
    def draw(d, ts):
        cx = x
        for s, c in parts:
            text(d, (cx, y), s, size, True, c, "lm")
            cx += twidth(d, s, size, True)
    return draw

def header(s):
    def draw(d, ts):
        d.rectangle([0, 0, S(W), S(66)], fill=TEAL)
        text(d, (40, 34), s, 28, True, WHITE, "lm")
    return draw

# --- sơ đồ mảnh vườn ---
PX = 38  # px mỗi mét
def garden(x, y, Lm, Wm):
    def draw(d, ts):
        rrect(d, (x, y, x + Lm * PX, y + Wm * PX), 6, GRASS, (120, 170, 100), 3)
        for k in range(6):  # vài khóm cây
            fx = x + 30 + (k * 53) % (Lm * PX - 50); fy = y + 30 + (k * 37) % (Wm * PX - 50)
            circle(d, fx, fy, 9, (120, 190, 100))
    return draw

def dim_h(x0, x1, y, s, col=INK, size=26):
    def draw(d, ts):
        line(d, [(x0, y), (x1, y)], col, 3)
        line(d, [(x0, y - 9), (x0, y + 9)], col, 3); line(d, [(x1, y - 9), (x1, y + 9)], col, 3)
        text(d, ((x0 + x1) / 2, y - 22), s, size, True, col)
    return draw

def dim_v(x, y0, y1, s, col=INK, size=26):
    def draw(d, ts):
        line(d, [(x, y0), (x, y1)], col, 3)
        line(d, [(x - 9, y0), (x + 9, y0)], col, 3); line(d, [(x - 9, y1), (x + 9, y1)], col, 3)
        text(d, (x - 14, (y0 + y1) / 2), s, size, True, col, "rm")
    return draw

def walker(x, y, Lm, Wm, period=6.0):
    """Chấm đỏ đi vòng quanh, để lại vệt."""
    L, Wd = Lm * PX, Wm * PX
    per = 2 * (L + Wd)
    def pos(s):
        s = s % per
        if s < L: return x + s, y
        s -= L
        if s < Wd: return x + L, y + s
        s -= Wd
        if s < L: return x + L - s, y + Wd
        s -= L
        return x, y + Wd - s
    def draw(d, ts):
        prog = min(ts / period, 1.0) * per
        n = max(2, int(prog / 6))
        pts = [pos(prog * k / n) for k in range(n + 1)]
        line(d, pts, RED, 6)
        px_, py_ = pos(prog) if prog < per else pos(per - 0.01)
        circle(d, px_, py_, 11, RED, WHITE, 3)
    return draw

def fence(x, y, Lm, Wm, gap_m):
    """Hàng rào nâu quanh vườn, chừa cửa ở cạnh dưới."""
    L, Wd = Lm * PX, Wm * PX
    gx0 = x + L / 2 - gap_m * PX / 2; gx1 = gx0 + gap_m * PX
    def draw(d, ts):
        line(d, [(gx0, y + Wd), (x, y + Wd), (x, y), (x + L, y), (x + L, y + Wd), (gx1, y + Wd)], BROWN, 8)
        # cột rào
        for (ax, ay, bx, by) in [(x, y, x + L, y), (x, y + Wd, gx0, y + Wd), (gx1, y + Wd, x + L, y + Wd),
                                 (x, y, x, y + Wd), (x + L, y, x + L, y + Wd)]:
            n = max(1, int(math.hypot(bx - ax, by - ay) / 30))
            for k in range(n + 1):
                circle(d, ax + (bx - ax) * k / n, ay + (by - ay) * k / n, 5, BROWN)
        # cửa
        line(d, [(gx0, y + Wd + 30), (gx1, y + Wd + 30)], ORANGE, 3)
        text(d, ((gx0 + gx1) / 2, y + Wd + 54), "cửa 2 m", 24, True, ORANGE)
    return draw

def bracket_group(x0, x1, y, col):
    def draw(d, ts):
        line(d, [(x0, y), (x0, y + 14), (x1, y + 14), (x1, y)], col, 4)
    return draw

def check_box(i, x, y, w=330, h=120, ok=False):
    titles = [("Đủ số?", "chép hết"), ("Dấu phẩy?", "thẳng hàng"), ("Đơn vị?", "ghi m")]
    t, s = titles[i]
    def draw(d, ts):
        rrect(d, (x, y, x + w, y + h), 16, GRAY, GREEN if ok else GRAY_E, 4 if ok else 2)
        text(d, (x + w / 2, y + 44), t, 34, True, INK)
        text(d, (x + w / 2, y + 86), s, 26, False, MUTED)
        if ok:
            circle(d, x + w - 6, y + 6, 22, GREEN)
            line(d, [(x + w - 17, y + 6), (x + w - 9, y + 15), (x + w + 6, y - 6)], WHITE, 5)
    return draw

def tick_mark(x, y, r=26):
    def draw(d, ts):
        circle(d, x, y, r, GREEN)
        line(d, [(x - r * .45, y), (x - r * .1, y + r * .38), (x + r * .5, y - r * .35)], WHITE, 6)
    return draw

def stars_burst(cx, cy):
    def draw(d, ts):
        for k in range(7):
            a = k * 2 * math.pi / 7 + ts * 0.6
            rr = 1 + 0.06 * math.sin(ts * 3 + k)
            star(d, cx + 400 * rr * math.cos(a), cy + 170 * rr * math.sin(a), 26 + 6 * math.sin(ts * 4 + k))
    return draw

def countdown(n, x=W / 2, y=400):
    def draw(d, ts):
        left = max(0.0, n - ts)
        r = 80
        circle(d, x, y, r, WHITE, GRAY_E, 6)
        if left > 0:
            frac = left / n
            d.arc([S(x - r), S(y - r), S(x + r), S(y + r)], -90, -90 + 360 * frac, fill=ORANGE, width=S(12))
            text(d, (x, y), str(int(math.ceil(left))), 72, True, ORANGE)
        text(d, (x, y + 118), "Bé nói to câu trả lời!", 28, True, MUTED)
    return draw

def quiz_q(num, s, y=200, size=44):
    def draw(d, ts):
        text(d, (W / 2, 120), "Câu %d" % num, 34, True, ORANGE)
        rrect(d, (W / 2 - twidth(d, s, size, True) / 2 - 40, y - 52, W / 2 + twidth(d, s, size, True) / 2 + 40, y + 52),
              20, GRAY, ORANGE, 4)
        text(d, (W / 2, y), s, size, True, INK)
    return draw

def lines_block(rows, x, y, size=30, gap=50, col=INK, bold=False):
    def draw(d, ts):
        for k, s in enumerate(rows):
            text(d, (x, y + k * gap), s, size, bold, col, "lm")
    return draw

# ---------- kịch bản ----------
# Mỗi cảnh: tiêu đề thanh trên (hoặc None) + danh sách nhịp.
# Nhịp: say = lời đọc (đọc bằng chữ), cap = phụ đề, add = khối hiện thêm, cd = đếm ngược (giây), ding = chuông.
GX, GY = 120, 300  # góc vườn trong cảnh ví dụ

SCENES = []
def scene(head, beats): SCENES.append((head, beats))

scene(None, [
    dict(say="Chào bé! Hôm nay mình cùng ôn tờ tra nhanh: thấy gì trong đề, thì làm gì ngay.",
         cap="Chào bé! Hôm nay mình cùng ôn tờ tra nhanh: thấy gì trong đề, thì làm gì ngay.",
         add=[big_title("Thấy gì  →  Làm gì", 260, 72, TEAL), big_title("Tờ tra nhanh ôn toán", 350, 36, MUTED, False)]),
    dict(say="Xem xong, bé chơi trò đố vui, để biết mình đã thuộc bài chưa nhé!",
         cap="Xem xong, bé chơi trò đố vui để biết mình đã thuộc bài chưa nhé!",
         add=[lambda d, ts: [star(d, 470 + 85 * k, 450, 26 + 3 * math.sin(ts * 4 + k)) for k in range(5)]]),
])

def overview_rows(hl=None):
    out = [label("Thấy trong đề", 390, 100, 26, MUTED, True), label("Làm ngay", 870, 100, 26, MUTED, True)]
    return out

scene("Tờ tra nhanh: 4 dòng", [
    dict(say="Tờ tra nhanh có bốn dòng. Bên trái, là chữ bé thấy trong đề. Bên phải, là việc bé làm ngay.",
         cap="Bên trái: chữ bé thấy trong đề.  Bên phải: việc bé làm ngay.",
         add=overview_rows() + [rule_row(0, 130)]),
    dict(say="Dài hơn, thì cộng.", cap="dài hơn → Cộng", add=[]),
    dict(say="Đi vòng quanh, thì tính chu vi.", cap="đi vòng quanh → Chu vi", add=[rule_row(1, 240)]),
    dict(say="Chừa cửa, thì trừ.", cap="chừa cửa → Trừ", add=[rule_row(2, 350)]),
    dict(say="Nhiều số cộng, thì ghép số tròn.", cap="nhiều số cộng → Ghép số tròn", add=[rule_row(3, 460)]),
])

# Dòng 1: dài hơn
L1 = 8; W1 = 5
scene("Dòng 1:  dài hơn  →  Cộng", [
    dict(say="Dòng thứ nhất. Thấy chữ dài hơn, bé làm phép cộng.", cap="Thấy “dài hơn” → làm phép Cộng.",
         add=[rule_row(0, 90, hl=True)]),
    dict(say="Ví dụ: mảnh vườn rộng năm mét. Chiều dài, hơn chiều rộng ba mét.",
         cap="Ví dụ: vườn rộng 5 m, chiều dài hơn chiều rộng 3 m.",
         add=[garden(GX, GY, L1, W1), dim_v(GX - 14, GY, GY + W1 * PX, "5 m"),
              dim_h(GX, GX + 5 * PX, GY - 22, "5 m", BLUE), dim_h(GX + 5 * PX, GX + 8 * PX, GY - 22, "hơn 3 m", ORANGE)]),
    dict(say="Chiều dài là: năm cộng ba, bằng tám mét.", cap="Chiều dài: 5 + 3 = 8 (m)",
         add=[label("Chiều dài:", 620, 340, 32, MUTED, True, "lm"),
              math_line([("5", BLUE), (" + ", INK), ("3", ORANGE), (" = 8 (m)", INK)], 620, 400, 48),
              dim_h(GX, GX + 8 * PX, GY + W1 * PX + 34, "dài 8 m", RED)]),
    dict(say="Nhớ nhé: dài hơn, là cộng!", cap="Nhớ: dài hơn → Cộng!",
         add=[label("dài hơn  →  CỘNG", 820, 500, 40, GREEN, True)]),
])

# Dòng 2: chu vi
scene("Dòng 2:  đi vòng quanh  →  Chu vi", [
    dict(say="Dòng thứ hai. Thấy đi vòng quanh, bé tính chu vi: lấy dài cộng rộng, rồi nhân hai.",
         cap="Thấy “đi vòng quanh” → tính Chu vi = (dài + rộng) × 2.", add=[rule_row(1, 90, hl=True)]),
    dict(say="Bé đi một vòng quanh mảnh vườn, dài tám mét, rộng năm mét.",
         cap="Đi một vòng quanh vườn dài 8 m, rộng 5 m.",
         add=[garden(GX, GY, L1, W1), dim_h(GX, GX + 8 * PX, GY - 22, "8 m"), dim_v(GX - 14, GY, GY + W1 * PX, "5 m"),
              walker(GX, GY, L1, W1, 5.0)]),
    dict(say="Chu vi là: tám cộng năm, được mười ba. Nhân hai, bằng hai mươi sáu mét.",
         cap="Chu vi: (8 + 5) × 2 = 26 (m)",
         add=[label("Chu vi:", 620, 340, 32, MUTED, True, "lm"),
              math_line([("(8 + 5)", BLUE), (" × 2", ORANGE), (" = 26 (m)", INK)], 620, 400, 48)]),
    dict(say="Nhớ nhé: đi vòng quanh, là tính chu vi!", cap="Nhớ: đi vòng quanh → Chu vi!",
         add=[label("vòng quanh  →  CHU VI", 840, 500, 40, GREEN, True)]),
])

# Dòng 3: chừa cửa
scene("Dòng 3:  chừa cửa  →  Trừ", [
    dict(say="Dòng thứ ba. Thấy chừa cửa, bé trừ đi bề rộng cửa.", cap="Thấy “chừa cửa” → Trừ bề rộng cửa.",
         add=[rule_row(2, 90, hl=True)]),
    dict(say="Rào quanh mảnh vườn đó, chừa một cái cửa rộng hai mét. Chỗ cửa, thì không cần rào.",
         cap="Rào quanh vườn (chu vi 26 m), chừa cửa rộng 2 m – chỗ cửa không rào.",
         add=[garden(GX, GY, L1, W1), fence(GX, GY, L1, W1, 2), dim_h(GX, GX + 8 * PX, GY - 22, "8 m"),
              dim_v(GX - 14, GY, GY + W1 * PX, "5 m")]),
    dict(say="Hàng rào dài: hai mươi sáu, trừ hai, bằng hai mươi bốn mét.", cap="Hàng rào: 26 − 2 = 24 (m)",
         add=[label("Hàng rào dài:", 620, 340, 32, MUTED, True, "lm"),
              math_line([("26", BLUE), (" − 2", ORANGE), (" = 24 (m)", INK)], 620, 400, 48)]),
    dict(say="Nhớ nhé: chừa cửa, là trừ!", cap="Nhớ: chừa cửa → Trừ!",
         add=[label("chừa cửa  →  TRỪ", 820, 500, 40, GREEN, True)]),
])

# Dòng 4: ghép số tròn
def r4_line2(d, ts):
    x = 250; y = 420; sz = 52
    parts = [("= ", INK), ("(17 + 3)", BLUE), (" + ", INK), ("(25 + 5)", ORANGE)]
    cx = x
    for s, c in parts:
        text(d, (cx, y), s, sz, True, c, "lm"); cx += twidth(d, s, sz, True)

def r4_arcs(d, ts):
    # nối 17 với 3, 25 với 5 ở dòng đề bài
    x = 250; y = 300; sz = 52
    segs = ["17", " + ", "25", " + ", "3", " + ", "5"]
    xs = []; cx = x
    for s in segs:
        w = twidth(d, s, sz, True); xs.append(cx + w / 2); cx += w
    for (a, b, c, yy) in [(0, 4, BLUE, 40), (2, 6, ORANGE, 62)]:
        line(d, [(xs[a], y + 32), (xs[a], y + yy), (xs[b], y + yy), (xs[b], y + 32)], c, 5)

scene("Dòng 4:  nhiều số cộng  →  Ghép số tròn", [
    dict(say="Dòng thứ tư. Thấy nhiều số cộng với nhau, bé ghép các số thành số tròn chục, và dùng dấu ngoặc.",
         cap="Thấy “nhiều số cộng” → Ghép thành số tròn, dùng ngoặc.", add=[rule_row(3, 90, hl=True)]),
    dict(say="Ví dụ: mười bảy, cộng hai mươi lăm, cộng ba, cộng năm.", cap="Ví dụ: 17 + 25 + 3 + 5",
         add=[math_line([("17 + 25 + 3 + 5", INK)], 250, 300, 52)]),
    dict(say="Ghép mười bảy với ba, được hai mươi. Ghép hai mươi lăm với năm, được ba mươi.",
         cap="17 + 3 = 20  ·  25 + 5 = 30", add=[r4_arcs, r4_line2]),
    dict(say="Hai mươi cộng ba mươi, bằng năm mươi. Tính nhẩm thật nhanh!", cap="= 20 + 30 = 50",
         add=[math_line([("= 20 + 30 = ", INK), ("50", GREEN)], 250, 520, 52)]),
])

# Kiểm tra 10 giây
def comma_demo(d, ts):
    # đặt tính, dấu phẩy thẳng hàng
    x = 600; y = 300; sz = 44
    rows = [("", "12", "5"), ("+", "3", "25")]
    cw = twidth(d, "0", sz, True)
    for k, (op, a, b) in enumerate(rows):
        yy = y + k * 60
        text(d, (x - 4 * cw, yy), op, sz, True, INK, "lm")
        text(d, (x, yy), a, sz, True, INK, "rm")
        text(d, (x, yy), ",", sz, True, RED, "lm")
        text(d, (x + twidth(d, ",", sz, True), yy), b, sz, True, INK, "lm")
    line(d, [(x - 4 * cw, y + 96), (x + 3 * cw, y + 96)], INK, 3)
    text(d, (x, y + 136), "15", sz, True, INK, "rm")
    text(d, (x, y + 136), ",", sz, True, RED, "lm")
    text(d, (x + twidth(d, ",", sz, True), y + 136), "75", sz, True, INK, "lm")
    line(d, [(x + 4, y - 34), (x + 4, y + 166)], (240, 150, 140), 2)

scene("Kiểm tra 10 giây trước khi nộp", [
    dict(say="Trước khi nộp bài, bé kiểm tra mười giây, với ba câu hỏi.", cap="Kiểm tra 10 giây – 3 câu hỏi.",
         add=[check_box(0, 95, 110), check_box(1, 475, 110), check_box(2, 855, 110)]),
    dict(say="Một: đủ số chưa? Bé chép hết các số trong đề, không bỏ sót số nào.",
         cap="1. Đủ số? Chép hết các số trong đề.", add=[check_box(0, 95, 110, ok=True),
         lines_block(["Đề: vườn dài 8 m, rộng 5 m, cửa 2 m", "Bài làm có đủ  8 · 5 · 2  chưa?"], 120, 330, 30, 56)]),
    dict(say="Hai: dấu phẩy thẳng hàng chưa? Khi đặt tính, các dấu phẩy phải nằm thẳng một hàng.",
         cap="2. Dấu phẩy? Đặt tính cho các dấu phẩy thẳng hàng.",
         add=[lambda d, ts: d.rectangle([0, S(240), S(W), S(600)], fill=BG), check_box(1, 475, 110, ok=True), comma_demo]),
    dict(say="Ba: ghi đơn vị chưa? Đáp số phải có chữ mét.", cap="3. Đơn vị? Đáp số ghi m.",
         add=[lambda d, ts: d.rectangle([0, S(240), S(W), S(600)], fill=BG), check_box(2, 855, 110, ok=True),
              math_line([("Đáp số: 24 ", INK), ("m", RED)], 470, 400, 56)]),
])

# Đố vui
scene("Đố vui: Bé đã thuộc bài chưa?", [
    dict(say="Bây giờ là trò đố vui! Bé nghe câu hỏi, rồi nói to câu trả lời, trước khi hết giờ nhé.",
         cap="Đố vui! Nghe câu hỏi – nói to câu trả lời trước khi hết giờ.",
         add=[big_title("Đố vui!", 300, 80, ORANGE), lambda d, ts: [star(d, 470 + 85 * k, 430, 24) for k in range(5)]]),
])

QUIZ = [(1, "đi vòng quanh"), (2, "chừa cửa"), (3, "dài hơn"), (4, "nhiều số cộng")]
for n, ri in [(1, 1), (2, 2), (3, 0), (4, 3)]:
    key = RULES[ri][0]
    num_word = ["", "một", "hai", "ba", "bốn"][n]
    ans_say = {0: "Đúng rồi! Dài hơn, là phép cộng: rộng, cộng phần hơn.",
               1: "Đúng rồi! Đi vòng quanh, là tính chu vi: dài cộng rộng, rồi nhân hai.",
               2: "Đúng rồi! Chừa cửa, là trừ đi bề rộng cửa.",
               3: "Đúng rồi! Nhiều số cộng, là ghép thành số tròn, dùng dấu ngoặc."}[ri]
    scene("Đố vui", [
        dict(say="Câu %s. Thấy chữ: %s. Bé làm gì?" % (num_word, key), cap="Câu %d: Thấy “%s” – bé làm gì?" % (n, key),
             add=[quiz_q(n, key)]),
        dict(say=None, cap="Bé nói to câu trả lời!", cd=4, add=[countdown(4)]),
        dict(say=ans_say, cap=ans_say.replace("Đúng rồi! ", "✔ "), ding=True,
             add=[lambda d, ts: d.rectangle([0, S(290), S(W), S(600)], fill=BG),
                  right_card(ri, W / 2 - 210, 330), tick_mark(W / 2 + 250, 373)]),
    ])

def q5_text(d, ts):
    text(d, (W / 2, 120), "Câu 5", 34, True, ORANGE)
    for k, s in enumerate(["Sân hình chữ nhật dài 10 m, rộng 6 m.",
                           "Rào quanh sân, chừa cửa rộng 1 m.",
                           "Hàng rào dài bao nhiêu mét?"]):
        text(d, (W / 2, 172 + k * 46), s, 32, k == 2, INK)

scene("Đố vui", [
    dict(say="Câu năm. Sân hình chữ nhật, dài mười mét, rộng sáu mét. Người ta rào quanh sân, chừa cửa rộng một mét. Hàng rào dài bao nhiêu mét?",
         cap="Câu 5: Sân dài 10 m, rộng 6 m. Rào quanh, chừa cửa 1 m. Hàng rào dài bao nhiêu mét?", add=[q5_text]),
    dict(say="Gợi ý: rào quanh, là chu vi. Chừa cửa, là trừ.", cap="Gợi ý: “rào quanh” → Chu vi,  “chừa cửa” → Trừ.",
         add=[]),
    dict(say=None, cap="Bé tính nhé!", cd=8, add=[countdown(8, y=420)]),
    dict(say="Chu vi: mười cộng sáu, được mười sáu, nhân hai, bằng ba mươi hai mét. Trừ cửa một mét, còn ba mươi mốt mét. Đáp số: ba mươi mốt mét.",
         cap="(10 + 6) × 2 = 32 (m)   →   32 − 1 = 31 (m).  Đáp số: 31 m", ding=True,
         add=[lambda d, ts: d.rectangle([0, S(300), S(W), S(600)], fill=BG),
              math_line([("Chu vi: ", MUTED), ("(10 + 6) × 2 = 32 (m)", INK)], 300, 350, 42),
              math_line([("Chừa cửa: ", MUTED), ("32 − 1 = 31 (m)", INK)], 300, 420, 42),
              math_line([("Đáp số: ", INK), ("31 m", GREEN)], 300, 500, 46), tick_mark(1000, 500)]),
])

scene("Đố vui", [
    dict(say="Câu sáu. Trước khi nộp bài, bé kiểm tra ba điều gì?", cap="Câu 6: Trước khi nộp bài, kiểm tra 3 điều gì?",
         add=[quiz_q(6, "Kiểm tra 10 giây: 3 điều gì?", size=38)]),
    dict(say=None, cap="Bé nói to câu trả lời!", cd=5, add=[countdown(5)]),
    dict(say="Đúng rồi! Đủ số. Dấu phẩy thẳng hàng. Và ghi đơn vị.", cap="✔ Đủ số – Dấu phẩy thẳng hàng – Ghi đơn vị.",
         ding=True, add=[lambda d, ts: d.rectangle([0, S(290), S(W), S(600)], fill=BG),
                         check_box(0, 95, 340, ok=True), check_box(1, 475, 340, ok=True), check_box(2, 855, 340, ok=True)]),
])

scene(None, [
    dict(say="Bé trả lời đúng cả sáu câu, là bé đã thuộc bài rồi! Câu nào chưa đúng, bé xem lại phần đó nhé.",
         cap="Đúng cả 6 câu = bé đã thuộc bài!  Câu nào sai, xem lại phần đó nhé.",
         add=[big_title("Bé đã thuộc bài!", 330, 72, GREEN), stars_burst(W / 2, 330)]),
    dict(say="Giỏi lắm! Hẹn gặp lại bé nhé!", cap="Giỏi lắm! Hẹn gặp lại bé nhé!", ding=True, add=[]),
])

# ---------- âm thanh ----------
def tts(s):
    h = hashlib.md5(s.encode()).hexdigest()[:12]
    p = os.path.join(CACHE, h + ".wav")
    if not os.path.exists(p):
        subprocess.run(["python3", "-m", "piper", "-m", MODEL, "-f", p, "--length-scale", "1.12",
                        "--sentence-silence", "0.25"], input=s.encode(), check=True, capture_output=True)
    with wave.open(p) as w:
        assert w.getframerate() == SR
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a

def tone(freqs, dur, vol=0.25):
    t = np.arange(int(dur * SR)) / SR
    a = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    return (a * np.exp(-t * 6) * vol).astype(np.float32)

TICK = tone([1200], 0.08, 0.15)
DING = np.concatenate([tone([880, 1320], 0.25, 0.22), tone([1175, 1760], 0.5, 0.22)])

# ---------- dựng dòng thời gian ----------
timeline = []  # (t0, t1, scene_idx, beat_idx)
audio_events = []
t = 0.0
PAD = 0.7
for si, (head, beats) in enumerate(SCENES):
    s0 = t
    for bi, b in enumerate(beats):
        b0 = t
        if b.get("ding"):
            audio_events.append((t, DING)); t += 0.35
        if b.get("say"):
            a = tts(b["say"]); audio_events.append((t + 0.15, a)); t += 0.15 + len(a) / SR + PAD
        if b.get("cd"):
            for k in range(b["cd"]):
                audio_events.append((t + k, TICK))
            t += b["cd"] + 0.2
        timeline.append((b0, t, si, bi))
    t += 0.4  # nghỉ giữa cảnh
TOTAL = t + 0.6
print("Tổng thời lượng: %.1f giây" % TOTAL)

buf = np.zeros(int(TOTAL * SR) + SR, dtype=np.float32)
for t0, a in audio_events:
    i = int(t0 * SR); buf[i:i + len(a)] += a
buf = np.clip(buf, -1, 1)
wav_path = os.path.join(CACHE, "mix.wav")
with wave.open(wav_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf * 32767).astype(np.int16).tobytes())

# ---------- vẽ khung ----------
def wrap(d, s, size, maxw):
    words = s.split(" "); lines = [""]
    for wd in words:
        trial = (lines[-1] + " " + wd).strip()
        if twidth(d, trial, size) <= maxw: lines[-1] = trial
        else: lines.append(wd)
    return lines

def scene_start(si):
    return min(b0 for b0, _, s, _ in timeline if s == si)

def render(tt):
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)
    cur = None
    for b0, b1, si, bi in timeline:
        if b0 <= tt: cur = (b0, b1, si, bi)
    if cur is None: cur = timeline[0]
    _, _, si, bi = cur
    head, beats = SCENES[si]
    if head: header(head)(d, 0)
    for k in range(bi + 1):
        bstart = [b0 for b0, _, s, b in timeline if s == si and b == k][0]
        ts = tt - bstart
        for el in beats[k].get("add", []):
            if ts < 0.35:  # hiện dần
                layer = Image.new("RGBA", img.size, BG + (0,))
                ld = ImageDraw.Draw(layer)
                el(ld, ts)
                al = layer.getchannel("A").point(lambda v: int(v * ease(ts / 0.35)))
                layer.putalpha(al)
                img.paste(layer, (0, 0), layer)
                d = ImageDraw.Draw(img)
            else:
                el(d, ts)
    # phụ đề
    cap = beats[bi].get("cap", "")
    if cap:
        d.rectangle([0, S(618), S(W), S(H)], fill=(34, 40, 52))
        ls = wrap(d, cap, 28, 1180)[:2]
        for k, s in enumerate(ls):
            yy = 669 if len(ls) == 1 else 650 + k * 38
            text(d, (W / 2, yy), s, 28, True, (255, 236, 170))
    # chuyển cảnh: mờ dần từ trắng kem
    s0 = scene_start(si)
    img = img.resize((W, H), Image.LANCZOS)
    if tt - s0 < 0.3:
        img = Image.blend(Image.new("RGB", (W, H), BG), img, ease((tt - s0) / 0.3))
    return img

nframes = int(TOTAL * FPS)
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav_path,
                       "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)
for fi in range(nframes):
    ff.stdin.write(render(fi / FPS).tobytes())
    if fi % 240 == 0: print("khung %d/%d" % (fi, nframes), flush=True)
ff.stdin.close(); ff.wait()
print("Xong:", OUT)
