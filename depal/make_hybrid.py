# -*- coding: utf-8 -*-
"""Video kết hợp 3D + motion graphic 2D – máy DEPAL bao (KCP Phú Yên).
Nguyên liệu:
  - các đoạn 3D render từ depal/3d (render.js, HQ=1), thư mục HY (mặc định: biến môi trường HY)
  - các cảnh 2D và hàm vẽ sơ đồ trong make_depal.py
Bố cục: xen kẽ 3D / 2D; chia đôi màn hình (3D trái – sơ đồ 2D phải) ở cảnh luồng sling và chất xe;
sơ đồ 2D thu nhỏ ở góc phải dưới các cảnh 3D (chấm đỏ = vị trí đang xem).
Chạy: HY=/đường/dẫn python3 make_hybrid.py [out.mp4]     (một file nén gửi email)
      HY=... python3 make_hybrid.py test out.png            (khung mẫu)
"""
import os, sys, math, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
import make_depal as m

W, H, FPS, XF = 1280, 720, 25, 8
HY = os.environ.get("HY", "hy")
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "test" else "Depal_3D_va_so_do.mp4"
seg, lin, lerp, ss, clamp, mix = m.seg, m.lin, m.lerp, m.ss, m.clamp, m.mix
CREAM, INK, RED, MUTED, ORANGE = m.CREAM, m.INK, m.RED, m.MUTED, m.ORANGE

def footer(d, n=0, color=INK):
    f = m.F("mono", 12)
    d.text((66 * m.SS, 692 * m.SS), "KCP VIỆT NAM · LOGISTICS · MÁY DEPAL BAO · 3D + SƠ ĐỒ", font=f, fill=color, anchor="ls")
    d.text((1214 * m.SS, 692 * m.SS), "bản vẽ 20/10/2026 · Phon-Tech 04/11/2026", font=f, fill=color, anchor="rs")
m.footer = footer          # các cảnh 2D dùng chân trang chung

# ---------- danh sách đoạn ----------
SEGS = [("2d", "title", 5.0), ("3d", "ov", 14.0), ("2d", "area", 16.0), ("split", "flow", 27.0),
        ("3d", "pick", 20.0), ("3d", "jour", 14.0), ("split", "truck", 24.0), ("3d", "sens", 21.0),
        ("3d", "back", 12.0), ("2d", "stats", m.STAT_T * len(m.STATS)), ("2d", "end", 7.5)]
SC2D = {"title": m.sc_title, "area": m.sc_area, "stats": m.sc_stats, "end": m.sc_end}

def px(mtr): return mtr * 1000 / m.MM + 337          # mét (3D) -> px bản vẽ (2D)

# ---------- sơ đồ thu nhỏ ----------
MM_BOX = (1012, 438, 1252, 594)            # khung trên màn hình (1x)
MM_CAM = m.Cam(1000, 728, 0.6)
MM_CROP = (230, 85, 1075, 630)
_mm = None
def minimap_base():
    global _mm
    if _mm is None:
        im, d = m.frame_base()
        m.draw_plant(d, MM_CAM, {"slings": m.default_slings() + [(m.POS_C, m.NBAG)], "robot": (m.PLACE, False, 0)})
        im = im.resize((W, H), Image.LANCZOS).crop(MM_CROP)
        _mm = im.resize((MM_BOX[2] - MM_BOX[0], MM_BOX[3] - MM_BOX[1] - 18), Image.LANCZOS)
    return _mm
def mm_xy(wx, wy):
    sx, sy = MM_CAM.scr(wx, wy)
    bw, bh = MM_BOX[2] - MM_BOX[0], MM_BOX[3] - MM_BOX[1] - 18
    return (MM_BOX[0] + (sx - MM_CROP[0]) / (MM_CROP[2] - MM_CROP[0]) * bw,
            MM_BOX[1] + 18 + (sy - MM_CROP[1]) / (MM_CROP[3] - MM_CROP[1]) * bh)
def draw_minimap(im, focus, t, label="ĐANG XEM"):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = MM_BOX
    d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], fill=(250, 246, 236), outline=INK, width=2)
    d.text((x0 + 6, y0 + 3), "SƠ ĐỒ · " + label, font=ImageFont.truetype(m.FP["monob"], 11), fill=INK)
    im.paste(minimap_base(), (x0, y0 + 18))
    if focus is not None:
        fx, fy = mm_xy(*focus)
        r = 5 + 2 * math.sin(t * 6)
        d.ellipse([fx - r - 4, fy - r - 4, fx + r + 4, fy + r + 4], outline=RED, width=2)
        d.ellipse([fx - 4, fy - 4, fx + 4, fy + 4], fill=RED)

# vị trí đang xem trong từng cảnh 3D (tọa độ px bản vẽ)
JT = [("V", 0, 3.5), ("S", 3.5, 7.0), ("K", 7.0, 9.0), ("T", 9.0, 14.0)]
JPATH = {"V": [m.PLACE, (m.BELT_X, 597)], "S": [(m.BELT_X, 597), (m.BELT_X, 400)], "K": m.PATH["K"], "T": [(683, 345), (1100, 345)]}
def focus_of(name, t):
    if name == "pick": return (628, 820)
    if name == "jour":
        for k, a, b in JT:
            if t < b or k == "T":
                pts = JPATH[k]; s = m.plen(pts) * ss(clamp((t - a) / (b - a)))
                return m.ppoint(pts, s)[0]
    if name == "sens": return (1500, 345)
    if name == "back": return (628, 1110) if t < 7.5 else (628, lerp(1050, 700, seg(t, 7.5, 12)))
    return None

# ---------- chia đôi: luồng sling (đồng bộ với 3D) ----------
L_X, P_Y, P_W, P_H = 16, 172, 624, 351
R_X = 640
FLOWK = {
    "A": dict(keys=[(0.3, px(-3.5)), (2.6, 375), (3.2, 375), (4.6, 536), (9.2, 536), (10.8, 627.5), (14.0, 627.5), (15.6, 723), (20.0, 723), (22.0, 536)], dep=(11.0, 13.8), out=(22.2, 23.6), show=0.3),
    "B": dict(keys=[(4.4, px(-3.5)), (6.7, 375), (7.3, 375), (8.3, 455), (9.4, 455), (10.8, 536), (16.0, 536), (17.4, 627.5), (20.0, 627.5), (22.0, 455)], dep=(17.6, 19.8), out=(22.2, 23.6), show=4.4),
    "R1": dict(keys=[(0, 792), (23.8, 792), (25.6, 627.5)], dep=None, out=None, show=0),
    "R0": dict(keys=[(0, 875), (23.9, 875), (25.6, 723)], dep=None, out=None, show=0),
}
FLOW_SUBS = [(0, 4.4, "Xe nâng đưa sling đầy vào băng con lăn bên trái"), (4.4, 7.6, "Xe nâng đặt sling thứ hai – mỗi bên 2 sling"),
             (7.6, 10.8, "Công nhân kiểm tra bao ngay ngắn, không rách, rồi bấm nút"), (10.8, 14.0, "Sling vào cell, máy hút hết 45 bao (tua nhanh)"),
             (14.0, 16.0, "Sling rỗng sang vị trí chờ bên phải"), (16.0, 20.0, "Bấm nút: sling thứ hai vào hút"),
             (20.0, 22.2, "Hút xong, cả 2 sling rỗng trả về bên trái"), (22.2, 23.8, "Công nhân lấy 2 sling rỗng ra"),
             (23.8, 99, "Bên phải làm giống hệt – lúc đó xe nâng nạp 2 sling mới bên trái")]
def flow2d(t):
    im, d = m.frame_base()
    cam = m.Cam(545, 832, 1.75)
    slings = []
    for k, f in FLOWK.items():
        if t < f["show"]: continue
        x = m.kx(t, f["keys"])
        n = NBAG_at(t, f["dep"]) if f["dep"] else m.NBAG
        kk = 1 - seg(t, f["out"][0] + 0.6, f["out"][1]) if f["out"] else 1.0
        if kk > 0.02: slings.append(((x, m.CY), n, kk))
    forks = []
    if 0.3 <= t < 3.2: forks.append(m.kx(t, FLOWK["A"]["keys"]) - m.FL_OFF)
    elif 3.2 <= t < 4.3: forks.append(lerp(375 - m.FL_OFF, px(-7) - m.FL_OFF, seg(t, 3.2, 4.3)))
    elif 4.4 <= t < 7.3: forks.append(m.kx(t, FLOWK["B"]["keys"]) - m.FL_OFF)
    elif 7.3 <= t < 8.4: forks.append(lerp(375 - m.FL_OFF, px(-7) - m.FL_OFF, seg(t, 7.3, 8.4)))
    rob = m.PLACE
    for k in ("A", "B"):
        a, b = FLOWK[k]["dep"]
        if a <= t < b:
            u = 0.5 - 0.5 * math.cos(2 * math.pi * 1.6 * (t - a)); rob = m.lerp_p(m.PLACE, (627.5, m.CY - 10), u)
    btn = [(m.BTN_L, seg(t, tp, tp + 0.8) if tp <= t < tp + 0.9 else 0.0) for tp in (8.8, 15.8)]
    m.draw_plant(d, cam, {"slings": slings, "forklifts": [((x, m.CY), 0.0) for x in forks], "robot": (rob, False, 0),
                          "buttons": btn, "hl": {"L": 1.0 if t < 23.8 else 0.0, "R": 1.0 if t >= 23.8 else 0.0}})
    return im.resize((W, H), Image.LANCZOS)
def NBAG_at(t, dep): return int(round(lerp(45, 0, lin(t, dep[0], dep[1])) / 3)) * 3

# ---------- chia đôi: chất xe – mặt cắt hàng đang chất (đồng bộ với kế hoạch 3D) ----------
PLAN = []
_t = 2.5
for r in range(16):
    nl = 9 if r < 14 else 5; n = 5 * nl
    if r == 0: times = [(_t + 0.7 * (i + 1)) if i < 5 else (_t + 3.5 + 0.1 * (i - 4)) for i in range(n)]; dur = 3.5 + 0.1 * (n - 5)
    else: dur = 2.2 if r == 1 else 0.32; times = [_t + dur * (i + 1) / n for i in range(n)]
    PLAN.append((r, _t, dur, times)); _t += dur + (1.4 if r == 0 else 0.3 if r == 1 else 0.08)
T_DONE = PLAN[-1][1] + PLAN[-1][2]
assert sum(len(p[3]) for p in PLAN) == 680
TRUCK_SUBS = [(0, 2.5, "Băng tải ống lồng vươn vào sát đầu thùng xe (tối đa 18 m)"),
              (2.5, 10, "Đầu băng tự rải bao từ trái sang phải, đủ 5 bao mới lên lớp trên"),
              (10, 11.6, "Đủ 9 lớp = 45 bao, băng thụt lại 75 cm để chất hàng tiếp theo"),
              (11.6, 15.4, "Chất cao tối đa: cách trần xe 30 cm"),
              (15.4, T_DONE + 0.4, "Lặp lại tới hàng 16 – không cần người trong thùng xe"),
              (T_DONE + 0.4, 99, "14 hàng × 45 bao + 2 hàng × 25 bao = 680 bao = 34 tấn")]
def truck2d(d, t):
    """vẽ trực tiếp vào khung 1x (d: ImageDraw 1280x720)"""
    F = lambda n, s: ImageFont.truetype(m.FP[n], s)
    total = 0; cur = 0; cnt = 0
    for r, t0, dur, times in PLAN:
        n = sum(1 for x in times if x <= t); total += n
        if n: cur, cnt = r, n
    s_ = 133                                        # px/m
    cx0, cy1 = R_X + 30, P_Y + P_H - 16             # góc trái dưới mặt cắt
    w_, h_ = 2.35 * s_, 2.15 * s_
    d.rectangle([cx0, cy1 - h_, cx0 + w_, cy1], fill=(236, 233, 224), outline=INK, width=3)
    d.line([cx0, cy1 - 0.8 * s_, cx0 + w_, cy1 - 0.8 * s_], fill=mix(CREAM, INK, 0.45), width=1)
    yl = cy1 - 1.85 * s_
    for x in range(int(cx0), int(cx0 + w_), 12): d.line([x, yl, x + 6, yl], fill=RED, width=2)
    d.text((cx0 + 4, yl - 15), "cách trần 30 cm", font=F("mono", 11), fill=RED)
    nl = 9 if cur < 14 else 5
    for i in range(cnt):
        k, c = i // 5, i % 5
        x = cx0 + c * 0.47 * s_; y = cy1 - (k + 1) * 0.13 * s_
        last = (i == cnt - 1 and cnt < 5 * nl)
        d.rounded_rectangle([x + 2, y + 1, x + 0.47 * s_ - 2, y + 0.13 * s_ - 1], radius=4, fill=(252, 250, 244), outline=ORANGE if last else INK, width=2 if last else 1)
    if cnt < 5 * nl and t >= 2.5 and t < T_DONE:
        k, c = cnt // 5, cnt % 5
        x = cx0 + (c + 0.5) * 0.47 * s_; y = cy1 - (k + 0.5) * 0.13 * s_
        d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=m.TEAL, width=3)
    for c in range(5):
        d.text((cx0 + (c + 0.5) * 0.47 * s_, cy1 + 4), str(c + 1), font=F("monob", 11), fill=MUTED, anchor="mt")
    d.text((cx0, P_Y + 2), "MẶT CẮT HÀNG ĐANG CHẤT (nhìn từ cửa sau)", font=F("monob", 12), fill=INK)
    d.text((cx0 + w_ / 2, cy1 - h_ - 4), "trái → phải", font=F("monob", 12), fill=RED, anchor="ms")
    # cột bên phải: tiến độ 16 hàng
    bx = cx0 + w_ + 30
    d.text((bx, P_Y + 30), f"HÀNG {cur + 1}/16", font=F("monob", 16), fill=INK)
    d.text((bx, P_Y + 54), f"{total}/680 BAO", font=F("monob", 16), fill=m.TEAL if total < 680 else ORANGE)
    d.text((bx, P_Y + 80), f"lớp {min(9, (cnt - 1) // 5 + 1) if cnt else 0}/{nl}", font=F("mono", 14), fill=INK)
    for r in range(16):
        hh = (9 if r < 14 else 5) * 9
        x = bx + r * 11; full = r < cur or (r == cur and cnt == len(PLAN[r][3]))
        d.rectangle([x, cy1 - hh, x + 8, cy1], fill=(252, 250, 244) if full else (236, 233, 224), outline=INK if full else mix(CREAM, INK, 0.3))
    d.text((bx, cy1 + 4), "16 hàng (đầu thùng → cửa sau)", font=F("mono", 10), fill=MUTED)

# ---------- khung chung cho màn hình chia đôi ----------
def split_frame(name, t, raw):
    if name == "flow":
        base = flow2d(t)
    else:
        base = Image.new("RGB", (W, H), CREAM)
    im = Image.new("RGB", (W * m.SS, H * m.SS), CREAM); d2 = ImageDraw.Draw(im)
    m.chapter(im, "(1)(2) SLING VÀO – SLING RỖNG RA" if name == "flow" else "(7)(8) BĂNG ỐNG LỒNG TỰ CHẤT LÊN XE", t)
    m.subs(d2, t, FLOW_SUBS if name == "flow" else TRUCK_SUBS)
    m.corners(d2); footer(d2)
    im = im.resize((W, H), Image.LANCZOS)
    v3 = Image.frombytes("RGB", (W, H), raw).resize((P_W, P_H), Image.LANCZOS)
    im.paste(v3, (L_X, P_Y))
    d = ImageDraw.Draw(im)
    d.rectangle([L_X - 1, P_Y - 1, L_X + P_W, P_Y + P_H], outline=INK, width=2)
    if name == "flow":
        im.paste(base.crop((0, 0, W, H)).resize((P_W, P_H), Image.LANCZOS), (R_X, P_Y))
    else:
        truck2d(d, t)
    d.rectangle([R_X - 1, P_Y - 1, R_X + P_W, P_Y + P_H], outline=INK, width=2)
    F = ImageFont.truetype(m.FP["monob"], 13)
    for x, s in ((L_X, "HÌNH 3D"), (R_X, "SƠ ĐỒ NHÌN TỪ TRÊN" if name == "flow" else "SƠ ĐỒ 2D")):
        tw = d.textlength(s, font=F)
        d.rectangle([x, P_Y - 24, x + tw + 16, P_Y - 2], fill=INK)
        d.text((x + 8, P_Y - 13), s, font=F, fill=CREAM, anchor="lm")
    if name == "flow" and ((11 <= t < 13.8) or (17.6 <= t < 19.8)):
        d.text((W - 40, P_Y - 13), "TUA NHANH >>", font=F, fill=INK, anchor="rm")
    if name == "flow":
        Fm = ImageFont.truetype(m.FP["mono"], 12)
        d.text((L_X, P_Y + P_H + 8), "mỗi bên 3 vị trí, 2 sling đầy · sling chỉ vào khi bấm nút · 4 công nhân · Phon-Tech xác nhận 04/11/2026", font=Fm, fill=MUTED)
    else:
        Fm = ImageFont.truetype(m.FP["mono"], 12)
        d.text((L_X, P_Y + P_H + 8), "thùng 34T: 12,26 × 2,35 × 2,15 m · 5 bao ngang × 9 lớp · đã bỏ bạt để nhìn vào trong · sơ đồ chất: KCP", font=Fm, fill=MUTED)
        if t > T_DONE + 0.4:
            im2 = im.resize((W * m.SS, H * m.SS)); m.stamp(im2, "XONG 1 XE · 680 BAO · 34 TẤN", t - T_DONE - 0.4, ORANGE, (W / 2, 330), -3, 20)
            im = im2.resize((W, H), Image.LANCZOS)
    return im

# ---------- một khung ----------
def frame(args):
    kind, name, t, D, raw = args
    if kind == "2d":
        return SC2D[name](t, D).resize((W, H), Image.LANCZOS).tobytes()
    if kind == "split":
        return split_frame(name, t, raw).tobytes()
    im = Image.frombytes("RGB", (W, H), raw).copy()
    f = focus_of(name, t)
    if f is not None: draw_minimap(im, f, t)
    return im.tobytes()

def seg_tasks(kind, name, D):
    n = int(round(D * FPS))
    if kind == "2d":
        for i in range(n): yield (kind, name, i / FPS, D, None)
        return
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(HY, name + ".mp4"), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = None
    for i in range(n):
        raw = p.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: raw = last          # thiếu khung cuối: giữ khung trước
        last = raw
        yield (kind, name, i / FPS, D, raw)
    p.stdout.close(); p.wait()

def render_segment(idx, pool):
    kind, name, D = SEGS[idx]
    out = os.path.join(HY, f"seg{idx:02d}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for b in pool.imap(frame, seg_tasks(kind, name, D), chunksize=4):
        ff.stdin.write(b)
    ff.stdin.close(); ff.wait()
    print("seg", idx, name, "ok", flush=True)
    return out

def concat(files, out):
    """ghép có chuyển cảnh mờ dần XF khung, xuất một file nén gửi email 960x540"""
    durs = [s[2] for s in SEGS]
    xd = XF / FPS
    inputs = sum([["-i", f] for f in files], [])
    fc = []; prev = "[0:v]"; off = 0.0
    for i in range(1, len(files)):
        off += durs[i - 1] - xd
        lab = f"[x{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={xd:.2f}:offset={off:.2f}{lab}")
        prev = lab
    fc.append(f"{prev}scale=960:-2,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]",
                    "-c:v", "libx264", "-crf", "33", "-preset", "slow", "-movflags", "+faststart", out], check=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        picks = [(3, 2.0), (3, 9.0), (3, 16.0), (6, 6.0), (6, 12.0), (6, 21.5), (4, 6.0), (5, 8.0)]
        tiles = []
        for idx, t in picks:
            kind, name, D = SEGS[idx]
            raw = None
            if kind != "2d":
                p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", os.path.join(HY, name + ".mp4"), "-frames:v", "1",
                                    "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
                raw = p.stdout
            tiles.append(Image.frombytes("RGB", (W, H), frame((kind, name, t, D, raw))).resize((640, 360)))
        sheet = Image.new("RGB", (1280, 360 * 4), "white")
        for i, im in enumerate(tiles): sheet.paste(im, ((i % 2) * 640, (i // 2) * 360))
        sheet.save(sys.argv[2]); print("saved")
    else:
        with Pool(4) as pool:
            files = [render_segment(i, pool) for i in range(len(SEGS))]
        concat(files, OUT)
        print("done", OUT, flush=True)
