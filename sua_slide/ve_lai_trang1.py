"""Trang 1: dựng lại video vẽ tay, bỏ cây bút to, vẽ cây bút nhỏ theo đầu nét."""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC, OUT, LAST = sys.argv[1], sys.argv[2], int(sys.argv[3])
W, H, FPS = 1600, 900, 30
BG = np.array([251, 251, 248], np.int16)
TOL, K = 26, 5

def frames():
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-frames:v', str(LAST + 1),
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()

# 1) khung cuối = hình hoàn chỉnh
final = None
for i, f in enumerate(frames()):
    final = f.copy()
F = final.astype(np.int16)
stroke = np.abs(F - BG).max(axis=2) > 10

# 2) thời điểm xuất hiện của từng điểm ảnh (khớp hình cuối K khung liên tiếp)
appear = np.full((H, W), 10 ** 6, np.int32)
run = np.zeros((H, W), np.int16)
n = 0
for t, f in enumerate(frames()):
    match = (np.abs(f.astype(np.int16) - F).max(axis=2) <= TOL) & stroke
    # trong vùng bút: không tính là khớp, nhưng cũng không xoá chuỗi đang đếm của điểm đã hiện
    run = np.where(match, run + 1, 0).astype(np.int16)
    newly = (run >= K) & (appear > t)
    appear[newly] = t - run[newly] + 1
    n = t + 1
left = stroke & (appear > n) & (run > 0)
appear[left] = n - run[left]
appear[stroke & (appear > n)] = n - 1
# điểm mờ (gần màu nền): lấy thời điểm của nét rõ gần nhất, tránh hiện lờ mờ từ đầu
diff = np.abs(F - BG).max(axis=2)
strong = diff > 45
INF = 10 ** 6
a = np.where(strong, appear, INF).astype(np.int64)
for _ in range(6):
    p = np.pad(a, 1, constant_values=INF)
    a = np.minimum.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:],
                           p[:-2, :-2], p[:-2, 2:], p[2:, :-2], p[2:, 2:]])
weak = stroke & ~strong
appear[weak] = np.where(a[weak] < INF, np.maximum(appear[weak], a[weak]), n - 1)
# lọc chấm lẻ: một điểm rõ chỉ hiện khi đã có ít nhất 24 điểm rõ khác quanh nó (ô 11x11) hiện
R_, KK = 5, 24
a = np.where(strong, appear, INF).astype(np.int32)
p = np.pad(a, R_, constant_values=INF)
kth = np.empty((H, W), np.int32)
for y0 in range(0, H, 60):
    y1 = min(H, y0 + 60)
    st = np.stack([p[y0 + dy:y1 + dy, dx:dx + W] for dy in range(2 * R_ + 1) for dx in range(2 * R_ + 1)])
    kth[y0:y1] = np.partition(st, KK, axis=0)[KK]
fix = strong & (kth < INF)
appear[fix] = np.maximum(appear[fix], kth[fix])
# vùng biển số 50.860: các điểm hiện quá sớm cho hiện cùng lúc với biển số
x0, y0, x1, y1 = 1360, 345, 1560, 460
reg = np.zeros((H, W), bool); reg[y0:y1, x0:x1] = True
rs = strong & reg
med_sign = int(np.median(appear[rs]))
lo = med_sign - 20
appear[rs & (appear < lo)] = lo
print('biển số: trung vị khung', med_sign)
# điểm mờ theo lại điểm rõ đã lọc
a = np.where(strong, appear, INF).astype(np.int64)
for _ in range(6):
    p = np.pad(a, 1, constant_values=INF)
    a = np.minimum.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:],
                           p[:-2, :-2], p[:-2, 2:], p[2:, :-2], p[2:, 2:]])
appear[weak] = np.where(a[weak] < INF, np.maximum(appear[weak], a[weak]), n - 1)
stroke_tip = strong
print('khung', n, 'điểm nét', int(stroke.sum()))

# 3) đường đi của đầu bút: tâm các điểm mới hiện trong mỗi khung
tips = []
ys, xs = np.nonzero(stroke_tip)
at = appear[ys, xs]
order = np.argsort(at)
cur = None
first_draw = int(at.min()); last_draw = int(at.max())
for t in range(n):
    sel = at == t
    if sel.sum() >= 3:
        # ưu tiên điểm dưới-phải nhất (đầu bút thường ở mép nét mới)
        px, py = xs[sel].astype(float), ys[sel].astype(float)
        c = (float(np.median(px)), float(np.median(py)))
        cur = c if cur is None else (cur[0] * 0.55 + c[0] * 0.45, cur[1] * 0.55 + c[1] * 0.45)
    tips.append(cur)

# 4) cây bút nhỏ (đầu bút ở gốc toạ độ, thân hướng lên phải)
SS = 4
L, Wd = 128, 13            # dài, rộng (điểm ảnh)
ANG = math.radians(58)     # góc thân bút so với phương ngang
def make_pen():
    big = Image.new('RGBA', ((L + 40) * SS, (Wd + 40) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    y0 = 20 * SS; y1 = y0 + Wd * SS; x0 = 20 * SS
    tip = 16 * SS; cap = 22 * SS
    # đầu ngòi
    d.polygon([(x0, (y0 + y1) / 2), (x0 + tip, y0 + 2 * SS), (x0 + tip, y1 - 2 * SS)], fill=(40, 40, 42, 255))
    # thân trắng viền xám
    d.rounded_rectangle([x0 + tip, y0, x0 + L * SS - cap, y1], radius=3 * SS, fill=(250, 250, 250, 255),
                        outline=(70, 72, 78, 255), width=2 * SS)
    d.line([(x0 + tip + 6 * SS, y0 + 4 * SS), (x0 + L * SS - cap - 6 * SS, y0 + 4 * SS)], fill=(205, 208, 214, 255), width=2 * SS)
    # nắp đen
    d.rounded_rectangle([x0 + L * SS - cap, y0 - 1 * SS, x0 + L * SS, y1 + 1 * SS], radius=4 * SS, fill=(30, 30, 32, 255))
    d.rectangle([x0 + L * SS - cap - 24 * SS, y0 - 3 * SS, x0 + L * SS - cap - 18 * SS, (y0 + y1) / 2], fill=(30, 30, 32, 255))
    pen = big.resize((big.width // SS, big.height // SS), Image.LANCZOS)
    rot = pen.rotate(math.degrees(ANG), resample=Image.BICUBIC, expand=True)
    # vị trí đầu ngòi sau khi xoay
    cx, cy = pen.width / 2, pen.height / 2
    tx, ty = 20 - cx, (pen.height / 2) - cy
    a = ANG
    rx = tx * math.cos(a) + ty * math.sin(a) + rot.width / 2
    ry = -tx * math.sin(a) + ty * math.cos(a) + rot.height / 2
    sh = rot.getchannel('A').filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.25))
    return rot, sh, (rx, ry)
PEN, SHADOW, TIPOFF = make_pen()

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
bgimg = np.empty((H, W, 3), np.uint8); bgimg[:] = BG.astype(np.uint8)
FADE = 5
for t in range(n):
    show = appear <= t
    fr = np.where(show[..., None], final, bgimg)
    im = Image.fromarray(fr)
    tip = tips[t]
    alpha = 1.0
    if t > last_draw:
        alpha = max(0.0, 1 - (t - last_draw) / FADE)
    if tip is not None and alpha > 0 and t >= first_draw:
        x = int(round(tip[0] - TIPOFF[0])); y = int(round(tip[1] - TIPOFF[1]))
        lay = im.convert('RGBA')
        sh = Image.new('RGBA', PEN.size, (0, 0, 0, 0)); sh.putalpha(SHADOW.point(lambda v: int(v * alpha)))
        lay.alpha_composite(sh, (max(0, x + 6), max(0, y + 8)) if x + 6 >= 0 and y + 8 >= 0 else (0, 0))
        p = PEN.copy(); p.putalpha(p.getchannel('A').point(lambda v: int(v * alpha)))
        if x >= 0 and y >= 0:
            lay.alpha_composite(p, (x, y))
        else:
            tmp = Image.new('RGBA', (W + 400, H + 400), (0, 0, 0, 0)); tmp.alpha_composite(p, (x + 200, y + 200))
            lay.alpha_composite(tmp.crop((200, 200, 200 + W, 200 + H)))
        im = lay.convert('RGB')
    enc.stdin.write(im.tobytes())
for _ in range(15):
    enc.stdin.write(final.tobytes())
enc.stdin.close(); enc.wait()
print('xong; vẽ từ khung', first_draw, 'tới', last_draw)
