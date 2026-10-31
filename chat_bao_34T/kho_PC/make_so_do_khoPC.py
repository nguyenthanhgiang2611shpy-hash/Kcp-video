# -*- coding: utf-8 -*-
"""Sơ đồ PDF 2 trang: chất xá 34 tấn vào xe container bạt – cách chất kho PC.
Dùng lại hàm vẽ của make_video_khoPC.py.  Chạy: python3 make_so_do_khoPC.py [out.pdf]
"""
import sys, os, importlib.util
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("mv", os.path.join(HERE, "make_video_khoPC.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "So_do_chat_xa_34T_kho_PC.pdf")

PW, PH = 3508, 2480                          # A4 ngang, 300 dpi
CREAM, INK, ORANGE, GREEN, RED, MUTED = m.CREAM, m.INK, m.ORANGE, m.GREEN, m.RED, m.MUTED
FP = m.FP
from PIL import ImageFont
_fc = {}
def F(name, size):
    k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(FP[name], size)
    return _fc[k]

def T(d, xy, s, font, fill, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)

FULL, ROWS, BL, BW, BH, WD, L = m.FULL, m.ROWS, m.BL, m.BW, m.BH, m.WD, m.L
NL, ORDER, OP = m.NL, m.ORDER, m.OP
assert sum(5 * NL(r) for r in range(ROWS)) == 680

def fitF(d, s, name, size, maxw):
    while size > 20 and d.textlength(s, font=F(name, size)) > maxw: size -= 2
    return F(name, size)

def fit_panel(item, w, h):
    """cắt theo vùng thế giới đã chọn, nới theo tỉ lệ khung w×h, đặt trên nền kem"""
    im, bb = item
    pad = 50
    x0, y0, x1, y1 = bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad
    aw, ah = x1 - x0, y1 - y0
    if aw / ah < w / h:
        nw = ah * w / h; x0 -= (nw - aw) / 2; x1 = x0 + nw
    else:
        nh = aw * h / w; y0 -= (nh - ah) / 2; y1 = y0 + nh
    canvas = Image.new("RGB", (int(x1 - x0), int(y1 - y0)), CREAM)
    canvas.paste(im, (int(-x0), int(-y0)))
    c = canvas
    sc = min(w / c.width, h / c.height)
    c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
    out = Image.new("RGB", (w, h), CREAM)
    out.paste(c, ((w - c.width) // 2, (h - c.height) // 2))
    return out

# ---------------- trang 1: 6 bước ----------------
def panel(cam, vis, extra=None, box=None):
    """box = (x0, x1, y0, y1, z0, z1) vùng thế giới cần hiện (cm)"""
    im, d = m.frame_base()
    m.draw_truck_back(d, cam)
    m.draw_bags(d, cam, vis)
    m.draw_truck_front(d, cam)
    if extra: extra(d, cam)
    pts = [cam.P(x, y, z) for x in box[:2] for y in box[2:4] for z in box[4:]]
    return (im, (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)))

def badge3d(d, cam, c, col):
    b = m.bag_box(0, c, 0)
    x, y = cam.P(BL / 2, (b[1] + b[4]) / 2, BH + 2)
    m.badge(d, x / m.SS, y / m.SS, str(c + 1), col, 17)

CAM_H = m.Cam(95, 15, 1.75)
def ex_b1(d, cam):
    for c in (1, 3):
        m.draw_bag(d, cam, m.bag_box(0, c, 0), 0, "o", 0.25)
    for c in (0, 2, 4): badge3d(d, cam, c, GREEN)
    m.tag(d, cam.P(0, WD / 2, 175), "VÁCH ĐẦU THÙNG", CREAM, m.F("monob", 15), bg=m.WALL_HEAD)
def ex_b2(d, cam):
    for c in range(5): badge3d(d, cam, c, GREEN if c in (0, 2, 4) else ORANGE)
    m.dim_line(d, cam.P(BL + 18, 0, 0), cam.P(BL + 18, WD, 0), "5 × 47 = 235 cm", GREEN, m.F("monob", 16), offset=(80, 6))
def ex_b3(d, cam):
    m.dim_line(d, cam.P(BL + 22, WD, 0), cam.P(BL + 22, WD, 117), "cao 117 cm", RED, m.F("monob", 16), offset=(64, 0))
    for k in range(9):
        x, y = cam.P(0, WD, k * BH + BH / 2)
        d.text((x - 10 * m.SS, y), f"lớp {k + 1}", font=m.F("mono", 13), fill=GREEN, anchor="rm")
def rowtags(n):
    def f(d, cam):
        for r in range(n):
            m.tag(d, cam.P(r * BL + BL / 2, WD + 24, 0), str(r + 1), ORANGE if r >= FULL else INK, m.F("monob", 14))
    return f
def ex_b6(d, cam):
    f = m.F("monob", 16)
    m.dim_line(d, cam.P(ROWS * BL - 4, WD, 0), cam.P(ROWS * BL - 4, WD, 104), "", RED, f)
    m.tag(d, cam.P(ROWS * BL, 0, 104 + 30), "hàng 16 · 8 lớp · cao 104 cm", RED, f, anchor="lm")
    d.line([cam.P(ROWS * BL, WD / 2, 0), cam.P(L, WD / 2, 0)], fill=INK, width=3 * m.SS)
    m.tag(d, cam.P(L + 25, WD / 2, 0), "trống 26 cm", INK, f, anchor="lm")
    m.tag(d, cam.P(FULL * BL - BL / 2, 0, 117 + 26), "hàng 8 · 9 lớp · 117 cm", INK, m.F("monob", 15))
    rowtags(ROWS)(d, cam)

def v_layer1(cols):
    return lambda r, c, k: (0, "g" if c in (0, 2, 4) else "o") if (r == 0 and k == 0 and c in cols) else None
def v_rows(nr, hi=None):
    def f(r, c, k):
        if r >= nr: return None
        if hi is not None and r in hi: return (0, "g")
        return (0, "o" if r >= FULL else "n")
    return f

STEPS = [
    ("BƯỚC 1 · Hàng 1 – lớp 1: bao 1 · 3 · 5", "Đặt bao 1, 3, 5 trước (2 bên thành + giữa); chừa 2 khe", 3,
     panel(CAM_H, v_layer1((0, 2, 4)), ex_b1, (0, 120, 0, WD, 0, 70))),
    ("BƯỚC 2 · Hàng 1 – lớp 1: ép bao 2 · 4", "Ép bao 2, 4 vào 2 khe 42,5 cm → mỗi bao ~47 cm", 5,
     panel(CAM_H, v_layer1(range(5)), ex_b2, (0, 200, 0, WD, 0, 70))),
    ("BƯỚC 3 · Hàng 1 – lớp 1 → 9", "Lớp nào cũng 1-3-5 rồi 2-4; đủ 9 lớp = 45 bao", 45,
     panel(m.Cam(110, -5, 1.6), lambda r, c, k: (0, "g") if r == 0 else None, ex_b3, (-60, 200, 0, WD, 0, 150))),
    ("BƯỚC 4 · Hàng 2 → 8 (9 lớp)", "Lùi 75 cm làm hàng mới; 8 hàng × 45 = 360 bao", 360,
     panel(m.CAM_FULL, v_rows(FULL, {FULL - 1}), rowtags(FULL), (0, L, 0, WD + 40, 0, 150))),
    ("BƯỚC 5 · Hàng 9 → 16 (8 lớp)", "Mỗi hàng 5 × 8 = 40 bao; 8 hàng × 40 = 320 bao", 680,
     panel(m.CAM_FULL, v_rows(ROWS), rowtags(ROWS), (0, L, 0, WD + 40, 0, 150))),
    ("BƯỚC 6 · Kiểm tra cuối thùng", "Hàng 16 cao 104 cm; còn trống 26 cm tới cửa sau", 680,
     panel(m.Cam(960, 130, 1.25), v_rows(ROWS), ex_b6, (480, L + 330, 0, WD + 40, 0, 160))),
]

def page1():
    pg = Image.new("RGB", (PW, PH), "white"); d = ImageDraw.Draw(pg)
    T(d, (120, 90), "CHẤT XÁ 680 BAO ĐƯỜNG (34 TẤN) VÀO XE CONTAINER BẠT – KHO PC", fitF(d, "CHẤT XÁ 680 BAO ĐƯỜNG (34 TẤN) VÀO XE CONTAINER BẠT – KHO PC", "serifb", 70, PW - 240), INK)
    T(d, (120, 190), "Thùng 1.226 × 235 × 215 cm  ·  Bao 75 × 50 × 13 cm, 50 kg  ·  680 bao = 34 tấn", F("mono", 38), MUTED)
    T(d, (PW - 120, 190), "1·3·5 → 2·4 → đủ lớp → lùi 75 cm", F("monob", 42), GREEN, "ra")
    cw, ch = 1600, 600
    xs = [120, PW - 120 - cw]; y0 = 290; gap_y = 40
    for i, (title, sub, cnt, im) in enumerate(STEPS):
        x = xs[i % 2]; y = y0 + (i // 2) * (ch + 62 + gap_y)
        col = ORANGE if i >= 4 else INK
        T(d, (x, y), title, F("serifb", 44), col)
        T(d, (x + cw, y + 6), f"Đã chất: {cnt}/680 bao", F("monob", 34), MUTED, "ra")
        T(d, (x, y + 58), sub, F("mono", 30), INK)
        pg.paste(fit_panel(im, cw, ch - 50), (x, y + 104))
    T(d, (120, PH - 70), "Viền xanh: bao 1·3·5 (chất trước) / hàng đang chất  ·  Viền cam: bao 2·4 (chất sau) và hàng 9–16 (8 lớp)  ·  "
      "minh họa, không theo tỷ lệ", F("monob", 30), INK)
    return pg

# ---------------- trang 2: nhìn hông, mặt cắt, mặt bằng ----------------
def bag2d(d, x, y, w, h, outline, fill, lw=3):
    d.rounded_rectangle([x, y - h, x + w, y], radius=int(min(w, h) * 0.35), fill=fill, outline=outline, width=lw)

def dim(d, p0, p1, label, col, font, vertical=False):
    d.line([p0, p1], fill=col, width=3)
    import math
    for a, b in ((p0, p1), (p1, p0)):
        ang = math.atan2(a[1] - b[1], a[0] - b[0]); h = 16
        d.polygon([a, (a[0] - h * math.cos(ang - 0.5), a[1] - h * math.sin(ang - 0.5)),
                   (a[0] - h * math.cos(ang + 0.5), a[1] - h * math.sin(ang + 0.5))], fill=col)
    if label:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        if vertical:
            tmp = Image.new("RGBA", (400, 60), (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
            td.text((200, 30), label, font=font, fill=col, anchor="mm")
            bb = tmp.getbbox(); tmp = tmp.crop(bb).rotate(90, expand=True)
            box = Image.new("RGB", (tmp.width + 12, tmp.height + 16), "white")
            d._image.paste(box, (int(mx - box.width / 2), int(my - box.height / 2)))
            d._image.paste(tmp, (int(mx - tmp.width / 2), int(my - tmp.height / 2)), tmp)
        else:
            bb = d.textbbox((mx, my), label, font=font, anchor="mm")
            d.rectangle([bb[0] - 10, bb[1] - 6, bb[2] + 10, bb[3] + 6], fill="white")
            d.text((mx, my), label, font=font, fill=col, anchor="mm")

BAG_F = (236, 234, 226); BAG_O = (255, 236, 222)

def page2():
    pg = Image.new("RGB", (PW, PH), "white"); d = ImageDraw.Draw(pg)
    T(d, (120, 90), "CÁC LỚP BAO TRONG THÙNG – NHÌN HÔNG, MẶT CẮT 1 LỚP, MẶT BẰNG (KHO PC)",
      fitF(d, "CÁC LỚP BAO TRONG THÙNG – NHÌN HÔNG, MẶT CẮT 1 LỚP, MẶT BẰNG (KHO PC)", "serifb", 70, PW - 240), INK)
    T(d, (120, 190), "Đơn vị: cm  ·  8 hàng × 45 bao + 8 hàng × 40 bao = 680 bao = 34.000 kg", F("mono", 38), MUTED)

    # ① nhìn hông
    T(d, (120, 290), "(1) NHÌN HÔNG: hàng 1–8 đủ 9 lớp, hàng 9–16 chất 8 lớp", F("serifb", 46), INK)
    s = 2.35                      # px/cm
    x0, fy = 330, 1030
    tw, th = L * s, 215 * s
    d.rectangle([x0 - 22, fy - th, x0, fy + 26], fill=(70, 95, 120))
    d.rectangle([x0 - 22, fy, x0 + tw, fy + 26], fill=(70, 95, 120))
    for yy in range(int(fy - th), int(fy), 28):
        d.line([x0 + tw, yy, x0 + tw, yy + 14], fill=(70, 95, 120), width=3)
    for xx in range(int(x0), int(x0 + tw), 28):
        d.line([xx, fy - th, xx + 14, fy - th], fill=(70, 95, 120), width=3)
    T(d, (x0 + 14, fy - th + 12), "nóc / khung mui 215 cm", F("mono", 26), (70, 95, 120))
    d.line([x0 - 22, fy - 80 * s, x0 + tw, fy - 80 * s], fill=(70, 95, 120), width=4)
    T(d, (x0 + tw + 16, fy - 80 * s - 20), "thành 80", F("mono", 24), (70, 95, 120), "lm")
    for r in range(ROWS):
        bx = x0 + r * BL * s
        for k in range(NL(r)):
            bag2d(d, bx + 4, fy - k * BH * s - 2, BL * s - 8, BH * s - 4,
                  (150, 150, 140) if r < FULL else ORANGE, BAG_F if r < FULL else BAG_O, 3)
        T(d, (bx + BL * s / 2, fy + 60), str(r + 1), F("serifb", 34), ORANGE if r >= FULL else INK, "mm")
    for k in range(9):
        T(d, (x0 - 40, fy - k * BH * s - BH * s / 2), f"lớp {k + 1}", F("mono", 24), INK, "rm")
    T(d, (x0 - 40, fy + 60), "Hàng", F("serifb", 34), INK, "rm")
    dim(d, (x0 + tw + 220, fy), (x0 + tw + 220, fy - th), "215", RED, F("monob", 30), True)
    dim(d, (x0 + tw + 150, fy), (x0 + tw + 150, fy - 104 * s), "104", RED, F("monob", 30), True)
    dim(d, (x0 - 210, fy), (x0 - 210, fy - 117 * s), "117", RED, F("monob", 30), True)
    dim(d, (x0 + ROWS * BL * s, fy - 150 * s), (x0 + tw, fy - 150 * s), "", RED, F("mono", 20))
    T(d, (x0 + (ROWS * BL + L) / 2 * s, fy - 150 * s - 40), "trống 26", F("monob", 28), RED, "mm")
    T(d, (x0 + FULL * BL * s / 2, fy - 117 * s - 50), "Hàng 1–8: 5 bao × 9 lớp = 45 bao/hàng", F("monob", 34), GREEN, "mm")
    T(d, (x0 + (FULL + ROWS) / 2 * BL * s, fy - 104 * s - 50), "Hàng 9–16: 5 bao × 8 lớp = 40 bao/hàng", F("monob", 34), ORANGE, "mm")
    d.line([x0 + 60, fy + 130, x0 + tw - 200, fy + 130], fill=GREEN, width=6)
    d.polygon([(x0 + tw - 200, fy + 130), (x0 + tw - 230, fy + 114), (x0 + tw - 230, fy + 146)], fill=GREEN)
    T(d, (x0 + tw / 2, fy + 172), "Hướng chất: từ trong (đầu thùng) ra ngoài (cửa sau) – xong 1 hàng mới lùi 75 cm",
      F("monob", 32), GREEN, "mm")
    T(d, (x0, fy + 225), "ĐẦU THÙNG", F("monob", 30), INK)
    T(d, (x0 + tw, fy + 225), "CỬA SAU", F("monob", 30), INK, "ra")

    # ② mặt cắt 1 lớp
    T(d, (120, 1330), "(2) MẶT CẮT 1 LỚP: bao 1 · 3 · 5 trước, 2 · 4 sau", F("serifb", 46), INK)
    s2 = 3.6; cx0 = 300
    def section(y, step):
        d.rectangle([cx0 - 18, y - 80 * s2 * 0.45, cx0, y + 18], fill=(70, 95, 120))
        d.rectangle([cx0 + WD * s2, y - 80 * s2 * 0.45, cx0 + WD * s2 + 18, y + 18], fill=(70, 95, 120))
        d.rectangle([cx0 - 18, y, cx0 + WD * s2 + 18, y + 18], fill=(70, 95, 120))
        if step == 1:
            pos = {0: (0, 50), 2: ((WD - 50) / 2, 50), 4: (WD - 50, 50)}
        else:
            pos = {c: (c * BW, BW) for c in range(5)}
        for c, (xx, ww) in pos.items():
            col = GREEN if c in (0, 2, 4) else ORANGE
            bag2d(d, cx0 + xx * s2 + 3, y - 3, ww * s2 - 6, BH * s2, col, BAG_F if c in (0, 2, 4) else BAG_O, 4)
            bx = cx0 + (xx + ww / 2) * s2; by = y - BH * s2 - 42
            d.ellipse([bx - 26, by - 26, bx + 26, by + 26], fill=col)
            T(d, (bx, by), str(c + 1), F("serifb", 32), "white", "mm")
        if step == 1:
            for g0 in (50, (WD + 50) / 2):
                dim(d, (cx0 + g0 * s2, y - 24), (cx0 + (g0 + 42.5) * s2, y - 24), "", RED, F("mono", 10))
                T(d, (cx0 + (g0 + 21.25) * s2, y - 70), "khe 42,5", F("monob", 28), RED, "mm")
            T(d, (cx0 + WD * s2 + 60, y - 30), "Bước 1: đặt 1 · 3 · 5", F("serifb", 38), GREEN, "lm")
            T(d, (cx0 + WD * s2 + 60, y + 20), "(rộng 50, chừa 2 khe)", F("mono", 28), INK, "lm")
        else:
            T(d, (cx0 + WD * s2 + 60, y - 30), "Bước 2: ép 2 · 4 vào khe", F("serifb", 38), ORANGE, "lm")
            T(d, (cx0 + WD * s2 + 60, y + 20), "→ 5 bao ~47 cm, vừa 235", F("mono", 28), INK, "lm")
            dim(d, (cx0, y + 70), (cx0 + WD * s2, y + 70), "235 = 5 × 47 cm", RED, F("monob", 30))
    section(1600, 1)
    section(1900, 2)
    T(d, (120, 2080), "Bao 6–10, 11–15 … ở các lớp trên đặt cùng thứ tự: 1 · 3 · 5 rồi 2 · 4.", F("mono", 30), INK)

    # ③ mặt bằng
    px0, py0 = 1990, 1420
    T(d, (px0 - 40, 1330), "(3) MẶT BẰNG: số lớp trên mỗi hàng", F("serifb", 46), INK)
    cwid, chei = 82, 56
    for r in range(ROWS):
        T(d, (px0 + r * cwid + cwid / 2, py0), str(r + 1), F("serifb", 28), ORANGE if r >= FULL else INK, "mm")
        for c in range(5):
            x = px0 + r * cwid; y = py0 + 30 + (4 - c) * chei
            col = (150, 150, 140) if r < FULL else ORANGE
            d.rounded_rectangle([x + 4, y + 4, x + cwid - 4, y + chei - 4], radius=10,
                                fill=BAG_F if r < FULL else BAG_O, outline=col, width=3)
            if r == 0:
                T(d, (x - 14, y + chei / 2), f"bao {c + 1}", F("mono", 22), GREEN if c in (0, 2, 4) else ORANGE, "rm")
        T(d, (px0 + r * cwid + cwid / 2, py0 + 30 + 5 * chei + 26), f"{NL(r)} lớp", F("mono", 22),
          ORANGE if r >= FULL else INK, "mm")
    d.rectangle([px0, py0 + 30, px0 + ROWS * cwid + 40, py0 + 30 + 5 * chei], outline=INK, width=5)
    T(d, (px0 + ROWS * cwid + 20, py0 + 30 + 2.5 * chei), "26", F("monob", 24), RED, "mm")
    dim(d, (px0, py0 + 30 + 5 * chei + 70), (px0 + ROWS * cwid + 40, py0 + 30 + 5 * chei + 70), "1.226 cm", RED, F("monob", 28))

    # ④ lưu ý
    nx, ny = 1990, 1880
    T(d, (nx - 40, ny), "(4) LƯU Ý KHI CHẤT", F("serifb", 46), RED)
    notes = [
        "• Mỗi lớp: đặt bao 1, 3, 5 trước, sau đó ép bao 2, 4 vào 2 khe 42,5 cm.",
        "• 5 × 50 = 250 cm > lòng thùng 235 cm: mỗi bao ép còn ~47 cm.",
        "• Hàng 1–8: 9 lớp = 45 bao, cao 117 cm (vượt thành 37 cm).",
        "• Hàng 9–16: 8 lớp = 40 bao, cao 104 cm (vượt thành 24 cm).",
        "• Xong 1 hàng mới lùi 75 cm; 16 × 75 = 1.200 cm, trống 26 cm.",
        "• Tổng: 8 × 45 + 8 × 40 = 680 bao × 50 kg = 34.000 kg.",
    ]
    for i, s_ in enumerate(notes):
        T(d, (nx - 40, ny + 75 + i * 50), s_, F("mono", 29), INK)
    T(d, (120, PH - 70), "Nguồn: cách chất theo xác nhận kho PC (video thực tế tại kho PC)  ·  KCP Việt Nam · Logistics  ·  minh họa, không theo tỷ lệ",
      F("monob", 30), MUTED)
    return pg

if __name__ == "__main__":
    p1, p2 = page1(), page2()
    p1.save(OUT, save_all=True, append_images=[p2], resolution=300, quality=88)
    base = os.path.splitext(OUT)[0]
    for i, p in enumerate((p1, p2), 1):
        p.resize((PW // 3, PH // 3), Image.LANCZOS).save(f"{base}_trang{i}_preview.png")
    print("saved", OUT)
