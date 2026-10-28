# -*- coding: utf-8 -*-
"""Video dọc 9:16 mô phỏng máy xếp bao đường tự động lên xe tải (~20 giây).
Lấy ý tưởng từ video máy xếp bao xi măng tự động; đổi thành bao đường KCP 50 kg.
Chạy:  python3 make_video.py                 -> render video
       python3 make_video.py frame 5.0 a.png -> xuất 1 khung hình
"""
import sys, math, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS = 720, 1280, 2, 25
DUR = 20.5
OUT = "may_xep_bao_duong_tu_dong_9x16.mp4"

# ---------- màu ----------
YELLOW = (255, 214, 10); BLACK = (20, 20, 20)
BAG_TOP = (250, 248, 242); BAG_FRONT = (214, 209, 196); BAG_SIDE = (232, 228, 216)
BAG_LINE = (170, 165, 150); BAND = (38, 122, 64)
RED_IN = (178, 40, 40); RED_DARK = (130, 26, 28); RED_RIB = (150, 30, 32)
FLOOR = (120, 112, 104); GROUND = (70, 72, 76)
MACH = (236, 236, 230); MACH_S = (198, 198, 192); MACH_D = (160, 160, 156)
BELT = (60, 64, 70); BELT_S = (40, 42, 46)

# ---------- thùng xe & bao (cm) ----------
L, WD, HWALL = 1226, 235, 80
BL, BW, BH = 75, 47, 13
COLS, LAYERS, ROWS = 5, 9, 15
NPLACE = ROWS * LAYERS + 1            # 135 lượt × 5 bao + 1 lượt 5 bao bù = 680 bao
assert NPLACE * COLS == 680 and 680 * 50 == 34000
HALF = WD / 2

FONT = {"b": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "r": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"}
_fc = {}
def F(n, s):
    k = (n, int(s * SS))
    if k not in _fc: _fc[k] = ImageFont.truetype(FONT[n], k[1])
    return _fc[k]

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, a, b): return ss((t - a) / (b - a))
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))

# ---------- camera phối cảnh ----------
class Cam:
    def __init__(s, pos, yaw, pitch, f):
        s.c = pos; s.f = f
        cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
        s.fw = (sy * cp, cy * cp, -sp)
        s.r = (cy, -sy, 0.0)
        r, fw = s.r, s.fw
        s.u = (r[1] * fw[2] - r[2] * fw[1], r[2] * fw[0] - r[0] * fw[2], r[0] * fw[1] - r[1] * fw[0])
    def C(s, x, y, z):
        d = (x - s.c[0], y - s.c[1], z - s.c[2])
        return (d[0] * s.r[0] + d[1] * s.r[1] + d[2] * s.r[2],
                d[0] * s.u[0] + d[1] * s.u[1] + d[2] * s.u[2],
                d[0] * s.fw[0] + d[1] * s.fw[1] + d[2] * s.fw[2])
    def S(s, q):
        return (W * SS / 2 + s.f * SS * q[0] / q[2], H * SS / 2 - s.f * SS * q[1] / q[2])
    def P(s, x, y, z):
        q = s.C(x, y, z)
        return s.S((q[0], q[1], max(5.0, q[2])))
    def clip(s, pts, near=10.0):
        qs = [s.C(*p) for p in pts]
        out = []
        for i in range(len(qs)):
            a, b = qs[i], qs[(i + 1) % len(qs)]
            ia, ib = a[2] >= near, b[2] >= near
            if ia: out.append(a)
            if ia != ib:
                k = (near - a[2]) / (b[2] - a[2])
                out.append(tuple(a[j] + (b[j] - a[j]) * k for j in range(3)))
        return [s.S(q) for q in out]

def look(pos, tgt, f):
    dx, dy, dz = tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]
    yaw = math.atan2(dx, dy)
    pitch = math.atan2(-dz, math.hypot(dx, dy))
    return Cam(pos, yaw, pitch, f)

def make_cam(k, track_y):
    """k=0: cận cảnh bám đầu xếp, k=1: toàn cảnh thùng xe."""
    pc, tc = (CLOSE_P[0], track_y + CLOSE_P[1], CLOSE_P[2]), (CLOSE_T[0], track_y + CLOSE_T[1], CLOSE_T[2])
    pos = tuple(lerp(a, b, k) for a, b in zip(pc, WIDE_P))
    tgt = tuple(lerp(a, b, k) for a, b in zip(tc, WIDE_T))
    return look(pos, tgt, lerp(CLOSE_F, WIDE_F, k))

CLOSE_P, CLOSE_T, CLOSE_F = (170, -470, 450), (80, -80, 60), 800
WIDE_P, WIDE_T, WIDE_F = (160, -330, 1250), (0, 560, 0), 820

# ---------- vẽ ----------
def poly(d, cam, pts, fill, outline=None, w=1):
    q = cam.clip(pts)
    if len(q) >= 3:
        d.polygon(q, fill=fill, outline=outline, width=w * SS if outline else 0)

def box_faces(x0, x1, y0, y1, z0, z1):
    return {
        "top": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1), ((x0 + x1) / 2, (y0 + y1) / 2, z1)),
        "front": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0), ((x0 + x1) / 2, y0, (z0 + z1) / 2)),
        "back": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0), ((x0 + x1) / 2, y1, (z0 + z1) / 2)),
        "left": ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], (-1, 0, 0), (x0, (y0 + y1) / 2, (z0 + z1) / 2)),
        "right": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0), (x1, (y0 + y1) / 2, (z0 + z1) / 2)),
    }

def visible(cam, n, c):
    return n[0] * (cam.c[0] - c[0]) + n[1] * (cam.c[1] - c[1]) + n[2] * (cam.c[2] - c[2]) > 0

def draw_box(d, cam, x0, x1, y0, y1, z0, z1, cols, line=None):
    for name, (pts, n, c) in box_faces(x0, x1, y0, y1, z0, z1).items():
        if name == "bottom" or not visible(cam, n, c): continue
        poly(d, cam, pts, cols[name], line, 1)

def draw_bag(d, cam, xc, yc, z0):
    g = 1.2
    x0, x1, y0, y1, z1 = xc - BW / 2 + g, xc + BW / 2 - g, yc - BL / 2 + g, yc + BL / 2 - g, z0 + BH
    cols = {"top": BAG_TOP, "front": BAG_FRONT, "back": BAG_FRONT, "left": BAG_SIDE, "right": BAG_SIDE}
    draw_box(d, cam, x0, x1, y0, y1, z0, z1, cols, BAG_LINE)
    # băng xanh in trên mặt bao
    for a, b in ((0.30, 0.38), (0.62, 0.70)):
        poly(d, cam, [(x0 + 3, lerp(y0, y1, a), z1), (x1 - 3, lerp(y0, y1, a), z1),
                      (x1 - 3, lerp(y0, y1, b), z1), (x0 + 3, lerp(y0, y1, b), z1)], BAND)

def col_x(c): return -HALF + BW / 2 + c * BW
def row_y(r): return L - BL / 2 - r * BL
def target(k):
    if k < ROWS * LAYERS: return k // LAYERS, k % LAYERS
    return ROWS - 1, LAYERS            # lượt bù trên cùng hàng cuối

# ---------- dòng thời gian ----------
T_SLOW0, CYC, NSLOW = 0.4, 3.2, 3
T_FAST0, T_FAST1 = 10.2, 17.0

def state(t):
    """Trả về: done (số lượt đã xếp xong), k (lượt hiện tại), u (pha 0..1), fast(bool)"""
    if t < T_SLOW0 + CYC * NSLOW:
        x = max(0.0, (t - T_SLOW0) / CYC)
        k = int(x); return k, k, x - k, False
    if t < T_FAST0:
        return NSLOW, NSLOW, 0.0, False
    p = lerp(NSLOW, NPLACE, seg(t, T_FAST0, T_FAST1))
    k = min(int(p), NPLACE - 1)
    return int(p), k, p - int(p), True

HZ_UP = LAYERS * BH + 70

def head_pose(t):
    done, k, u, fast = state(t)
    if done >= NPLACE:
        r, l = target(NPLACE - 1)
        return row_y(r), (l + 1) * BH + 60, 0.0, 0, done
    r, l = target(k)
    if fast:
        p = lerp(NSLOW, NPLACE, seg(t, T_FAST0, T_FAST1))
        r2, l2 = target(min(int(p) + 1, NPLACE - 1))
        hy = lerp(row_y(r), row_y(r2), u)
        hz = max(l, l2) * BH + 30
        return hy, hz, 0.0, 5, done
    tz = l * BH + 1.5
    if u < 0.30:   hz, drop, held = HZ_UP, 0.0, min(5, int(u / 0.30 * 5.999))
    elif u < 0.55: hz, drop, held = lerp(HZ_UP, tz, seg(u, 0.30, 0.55)), 0.0, 5
    elif u < 0.70: hz, drop, held = tz, seg(u, 0.55, 0.62), 5
    else:
        hz, drop, held = lerp(tz, HZ_UP, seg(u, 0.72, 1.0)), 1.0, 0
        done = k + 1
    hy = row_y(r)
    if u >= 0.70 and k + 1 < NPLACE:  # di chuyển sang vị trí kế tiếp
        r2, _ = target(k + 1)
        hy = lerp(hy, row_y(r2), seg(u, 0.75, 1.0))
    return hy, hz, drop, held, done

def draw_truck(d, cam):
    # mặt đất
    poly(d, cam, [(-900, -800, -110), (900, -800, -110), (900, 2600, -110), (-900, 2600, -110)], GROUND)
    # vạch kẻ đường
    for xs in (-260, 260):
        poly(d, cam, [(xs - 6, -800, -110), (xs + 6, -800, -110), (xs + 6, 2600, -110), (xs - 6, 2600, -110)], (200, 170, 40))
    # cabin phía trước
    draw_box(d, cam, -HALF, HALF, L + 20, L + 230, -110, 170,
             {"top": (210, 210, 205), "front": (190, 190, 186), "back": (190, 190, 186), "left": (200, 200, 196), "right": (200, 200, 196)})
    # thân / sườn ngoài + sàn
    draw_box(d, cam, -HALF - 6, HALF + 6, 0, L, -110, 0,
             {"top": FLOOR, "front": (55, 55, 58), "back": (55, 55, 58), "left": (90, 30, 30), "right": (90, 30, 30)})
    # vách đầu thùng
    poly(d, cam, [(-HALF, L, 0), (HALF, L, 0), (HALF, L, HWALL + 60), (-HALF, L, HWALL + 60)], RED_DARK)
    # vách hai bên (mặt trong) + gân
    for xs in (-HALF, HALF):
        poly(d, cam, [(xs, 0, 0), (xs, L, 0), (xs, L, HWALL), (xs, 0, HWALL)], RED_IN)
        for yy in range(0, L + 1, 60):
            poly(d, cam, [(xs, yy - 2, 0), (xs, yy + 2, 0), (xs, yy + 2, HWALL), (xs, yy - 2, HWALL)], RED_RIB)
        poly(d, cam, [(xs - 5, 0, HWALL), (xs + 5, 0, HWALL), (xs + 5, L, HWALL), (xs - 5, L, HWALL)], RED_DARK)

def draw_rails(d, cam):
    for xs in (-260, 260):
        draw_box(d, cam, xs - 15, xs + 15, -300, L + 250, 600, 630,
                 {"top": (90, 96, 104), "front": (70, 74, 80), "back": (70, 74, 80), "left": (60, 64, 70), "right": (60, 64, 70)})

def draw_stack(d, cam, done):
    items = []
    for k in range(min(done, NPLACE)):
        r, l = target(k)
        for c in range(COLS):
            items.append((r, l, c))
    # xa trước, thấp trước, ngoài vào trong theo trục x so với camera
    items.sort(key=lambda it: (-row_y(it[0]), it[1], -abs(col_x(it[2]) - cam.c[0])))
    for r, l, c in items:
        draw_bag(d, cam, col_x(c), row_y(r), l * BH)

def draw_machine(d, cam, t, hy, hz, drop, held, k_target, fast):
    top = hz + 75
    # băng tải nghiêng phía sau đầu xếp
    S, E = (120, top + 10), (760, top + 260)
    bw = 42
    poly(d, cam, [(S[0], hy - bw, S[1]), (E[0], hy - bw, E[1]), (E[0], hy + bw, E[1]), (S[0], hy + bw, S[1])], BELT)
    poly(d, cam, [(S[0], hy - bw, S[1]), (E[0], hy - bw, E[1]), (E[0], hy - bw, E[1] - 16), (S[0], hy - bw, S[1] - 16)], BELT_S)
    # bao chạy trên băng tải
    blen = math.hypot(E[0] - S[0], E[1] - S[1]); dy, dz = (E[0] - S[0]) / blen, (E[1] - S[1]) / blen
    feed = t * 5.5 if fast else feed_count(t)
    sp = 95
    j0 = math.floor(feed)
    for j in range(j0 + 7, j0 - 1, -1):
        s = (j - feed) * sp + 40
        if s < 0 or s > blen - 40: continue
        cx, cz = S[0] + dy * s, S[1] + dz * s
        draw_tilted_bag(d, cam, cx, hy, cz, dy, dz)
    # cầu trục: ống lồng từ đầu xếp lên dầm ngang
    ZB = 560
    for i, zz in enumerate(range(int(top), ZB, 16)):
        cc = MACH if i % 2 == 0 else MACH_S
        z2 = min(zz + 16, ZB)
        draw_box(d, cam, -30, 30, hy - 30, hy + 10, zz, z2,
                 {"top": cc, "front": cc, "back": cc, "left": MACH_D, "right": MACH_D})
    draw_box(d, cam, -275, 275, hy - 30, hy + 30, ZB, ZB + 40,
             {"top": (210, 50, 45), "front": (180, 36, 34), "back": (180, 36, 34), "left": (150, 30, 28), "right": (150, 30, 28)})
    # thân đầu xếp
    hx = 132
    draw_box(d, cam, -hx, hx, hy - 48, hy + 48, hz + 22, top,
             {"top": MACH, "front": MACH_S, "back": MACH_S, "left": MACH_D, "right": MACH_D}, (150, 150, 146))
    # cửa sổ nhỏ mặt trước
    for xw in (-90, 30):
        poly(d, cam, [(xw, hy - 48, hz + 38), (xw + 55, hy - 48, hz + 38), (xw + 55, hy - 48, top - 10), (xw, hy - 48, top - 10)], (120, 128, 134))
    # bao đang được kẹp
    if held:
        r, l = target(k_target)
        z_hold, z_tgt = hz, l * BH
        zb = lerp(z_hold, z_tgt, drop)
        for c in range(held):
            draw_bag(d, cam, col_x(c), hy, zb)
    # ngón kẹp
    open_k = drop
    for c in range(COLS + 1):
        x = -HALF + c * BW
        xo = x + (8 * open_k if x > 0 else -8 * open_k)
        poly(d, cam, [(xo - 2, hy - 46, hz + 22), (xo + 2, hy - 46, hz + 22),
                      (xo + 2, hy - 46, hz - 2 + 14 * open_k), (xo - 2, hy - 46, hz - 2 + 14 * open_k)], (90, 92, 96))

def draw_tilted_bag(d, cam, cx, cy, cz, dx, dz):
    # bao nằm trên băng tải nghiêng (băng chạy theo trục x): trục dài theo trục y
    nx, nz = -dz, dx
    hw, hl, th = BW / 2, BL / 2, BH
    def p(a, yy, b):
        return (cx + dx * a + nx * b, cy + yy, cz + dz * a + nz * b)
    top = [p(-hw, -hl, th), p(hw, -hl, th), p(hw, hl, th), p(-hw, hl, th)]
    front = [p(-hw, -hl, 0), p(hw, -hl, 0), p(hw, -hl, th), p(-hw, -hl, th)]
    left = [p(-hw, -hl, 0), p(-hw, hl, 0), p(-hw, hl, th), p(-hw, -hl, th)]
    poly(d, cam, left, BAG_SIDE, BAG_LINE)
    poly(d, cam, front, BAG_FRONT, BAG_LINE)
    poly(d, cam, top, BAG_TOP, BAG_LINE)
    poly(d, cam, [p(-hw + 3, -hl * 0.3, th), p(hw - 3, -hl * 0.3, th), p(hw - 3, -hl * 0.1, th), p(-hw + 3, -hl * 0.1, th)], BAND)
    poly(d, cam, [p(-hw + 3, hl * 0.1, th), p(hw - 3, hl * 0.1, th), p(hw - 3, hl * 0.3, th), p(-hw + 3, hl * 0.3, th)], BAND)

def feed_count(t):
    if t < T_SLOW0: return 0.0
    if t >= T_SLOW0 + CYC * NSLOW: return NSLOW * 5.0
    x = (t - T_SLOW0) / CYC; k = int(x); u = x - k
    return 5 * k + 5 * clamp(u / 0.30)

# ---------- chữ ----------
def rrect(d, box, fill, r=14):
    d.rounded_rectangle([v * SS for v in box], radius=r * SS, fill=fill)

def wrap(d, s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if d.textlength(tst, font=font) <= maxw * SS: cur = tst
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def caption(d, s, yc, size=30, alpha=1.0):
    if alpha <= 0.01: return
    font = F("b", size)
    lines = wrap(d, s, font, W - 120)
    lh = size * 1.3
    hbox = lh * len(lines) + 26
    wbox = max(d.textlength(l, font=font) for l in lines) / SS + 44
    y0 = yc - hbox / 2
    rrect(d, (W / 2 - wbox / 2, y0, W / 2 + wbox / 2, y0 + hbox), mix((0, 0, 0), YELLOW, alpha), 12)
    for i, l in enumerate(lines):
        d.text((W / 2 * SS, (y0 + 13 + lh * (i + 0.5)) * SS), l, font=font, fill=mix(YELLOW, BLACK, alpha), anchor="mm")

CAPS = [
    (0.0, 3.6, "Băng tải đưa bao đường 50 kg vào đầu xếp"),
    (3.6, 6.8, "Đầu xếp hạ xuống, đặt 5 bao một lượt – phẳng và đều"),
    (6.8, 10.2, "Nâng lên, nhận lượt bao kế tiếp – người vận hành chỉ cần giám sát"),
    (10.2, 17.0, "Xếp từng lớp, từ đầu xe ra cửa sau (tua nhanh)"),
]

def render(fi):
    t = fi / FPS
    img = Image.new("RGB", (W * SS, H * SS), (30, 32, 36))
    d = ImageDraw.Draw(img)
    hy, hz, drop, held, done = head_pose(t)
    _, k, _, fast = state(t)
    kz = seg(t, 9.8, 12.0) * (1 - 0.0)
    track = row_y(0) if t < 9.8 else hy
    cam = make_cam(kz, track)
    draw_truck(d, cam)
    draw_stack(d, cam, done)
    draw_machine(d, cam, t, hy, hz, drop, held, k, fast)
    draw_rails(d, cam)

    # lan can vàng phía trước (giống góc quay gốc)
    d.line([(W * 0.70 * SS, H * SS), (W * 1.05 * SS, H * 0.80 * SS)], fill=YELLOW, width=16 * SS)
    d.line([(W * 0.82 * SS, H * SS), (W * 0.82 * SS, H * 0.90 * SS)], fill=(220, 180, 0), width=12 * SS)

    # banner trên cùng
    rrect(d, (14, 40, W - 14, 150), YELLOW, 16)
    d.text((W / 2 * SS, 74 * SS), "MÔ PHỎNG MÁY XẾP BAO ĐƯỜNG", font=F("b", 34), fill=BLACK, anchor="mm")
    d.text((W / 2 * SS, 118 * SS), "TỰ ĐỘNG LÊN XE TẢI – ÍT NHÂN CÔNG", font=F("b", 28), fill=BLACK, anchor="mm")

    # bộ đếm
    bags = min(done, NPLACE) * COLS
    rrect(d, (W - 270, 168, W - 18, 252), (0, 0, 0), 12)
    d.text(((W - 144) * SS, 192 * SS), f"Đã xếp: {bags} bao", font=F("b", 24), fill=(255, 255, 255), anchor="mm")
    d.text(((W - 144) * SS, 228 * SS), f"≈ {bags * 50 / 1000:.1f} tấn".replace(".", ","), font=F("b", 24), fill=YELLOW, anchor="mm")
    if fast and t < T_FAST1:
        rrect(d, (18, 168, 228, 214), (200, 30, 30), 10)
        d.text((123 * SS, 191 * SS), "▶▶ TUA NHANH", font=F("b", 24), fill=(255, 255, 255), anchor="mm")

    for a, b, s in CAPS:
        if a <= t < b:
            al = min(seg(t, a, a + 0.25), 1 - seg(t, b - 0.2, b)) if a > 0 else 1 - seg(t, b - 0.2, b)
            caption(d, s, 1070, 30, al)

    if t >= 17.0:
        k2 = seg(t, 17.0, 17.6)
        ov = Image.new("RGB", img.size, (0, 0, 0))
        img = Image.blend(img, ov, 0.55 * k2)
        d = ImageDraw.Draw(img)
        cy = 640
        caption(d, "Hoàn tất: 680 bao · 34 tấn", cy - 120, 40, k2)
        for i, s in enumerate(["✔ Xếp nhanh, đều, đúng vị trí", "✔ Giảm bốc vác thủ công", "✔ An toàn hơn cho người lao động"]):
            kk = seg(t, 17.6 + 0.4 * i, 18.0 + 0.4 * i)
            if kk > 0:
                d.text((W / 2 * SS, (cy + 20 + 70 * i) * SS), s, font=F("b", 32), fill=mix((0, 0, 0), (255, 255, 255), kk), anchor="mm")
        kk = seg(t, 19.0, 19.5)
        if kk > 0:
            d.text((W / 2 * SS, (cy + 270) * SS), "KCP Việt Nam – Logistics", font=F("r", 26), fill=mix((0, 0, 0), YELLOW, kk), anchor="mm")
    return img.resize((W, H), Image.LANCZOS).tobytes()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "frame":
        Image.frombytes("RGB", (W, H), render(int(float(sys.argv[2]) * FPS))).save(sys.argv[3])
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "21",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, b in enumerate(pool.imap(render, range(n), chunksize=8)):
                p.stdin.write(b)
                if i % 100 == 0: print(f"{i}/{n}", flush=True)
        p.stdin.close(); p.wait()
        print("done", OUT, flush=True)
