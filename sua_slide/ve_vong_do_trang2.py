"""Ghép trang 2: nền + video chậm + vòng đỏ khoanh giai đoạn đang nói (giữ tới cuối)."""
import math, subprocess, sys
from PIL import Image, ImageDraw

BG, SLOW, OUT = sys.argv[1:4]
W, H, FPS = 1600, 900, 30
VX, VY, VW, VH, R = 107, 249, 907, 510, 18          # khung video trên nền
BOXES = [(1052, 297, 1495, 352), (1052, 368, 1495, 422),
         (1052, 437, 1495, 491), (1052, 506, 1495, 560)]
PHASE_START = [float(x) for x in sys.argv[4].split(",")]  # giây: bắt đầu giai đoạn 1..4
DRAW_TIME = 0.8                                      # thời gian vẽ vòng đỏ
RED, PAD, STROKE, SS = (220, 38, 38, 255), 5, 4, 3

bg = Image.open(BG).convert('RGB')
mask = Image.new('L', (VW * SS, VH * SS), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, VW * SS - 1, VH * SS - 1], radius=R * SS, fill=255)
mask = mask.resize((VW, VH), Image.LANCZOS)

def stadium_points(x0, y0, x1, y1, n=400):
    """Các điểm theo viền hình viên thuốc, bắt đầu từ giữa cạnh trên bên trái, đi theo chiều kim đồng hồ."""
    r = (y1 - y0) / 2
    cy = (y0 + y1) / 2
    L = x1 - x0 - 2 * r
    per = 2 * L + 2 * math.pi * r
    pts = []
    for i in range(n + 1):
        s = per * i / n
        if s < L:
            pts.append((x0 + r + s, y0))
        elif s < L + math.pi * r:
            a = -math.pi / 2 + (s - L) / r
            pts.append((x1 - r + r * math.cos(a), cy + r * math.sin(a)))
        elif s < 2 * L + math.pi * r:
            pts.append((x1 - r - (s - L - math.pi * r), y1))
        else:
            a = math.pi / 2 + (s - 2 * L - math.pi * r) / r
            pts.append((x0 + r + r * math.cos(a), cy + r * math.sin(a)))
    return pts

RX0, RY0, RX1, RY1 = 1030, 280, 1520, 580   # vùng chứa các vòng đỏ
def ring_layer(progress):
    """progress: list 4 số 0..1. Trả về lớp RGBA của vùng bên phải."""
    lw, lh = (RX1 - RX0) * SS, (RY1 - RY0) * SS
    im = Image.new('RGBA', (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (x0, y0, x1, y1), p in zip(BOXES, progress):
        if p <= 0:
            continue
        pts = stadium_points((x0 - PAD - RX0) * SS, (y0 - PAD - RY0) * SS,
                             (x1 + PAD - RX0) * SS, (y1 + PAD - RY0) * SS)
        k = max(2, int(len(pts) * min(p, 1.0)))
        d.line(pts[:k], fill=RED, width=STROKE * SS, joint='curve')
        for (px, py) in (pts[0], pts[k - 1]):
            rr = STROKE * SS / 2
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=RED)
    return im.resize((RX1 - RX0, RY1 - RY0), Image.LANCZOS)

cache = {}
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SLOW, '-vf', f'scale={VW}:{VH}:flags=lanczos',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18',
                        '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                       stdin=subprocess.PIPE)
fsize = VW * VH * 3
i = 0
while True:
    buf = dec.stdout.read(fsize)
    if len(buf) < fsize:
        break
    t = i / FPS
    prog = tuple(round(min(max((t - s) / DRAW_TIME, 0), 1), 2) for s in PHASE_START)
    if prog not in cache:
        cache[prog] = ring_layer(prog)
    fr = bg.copy()
    fr.paste(Image.frombytes('RGB', (VW, VH), buf), (VX, VY), mask)
    reg = fr.crop((RX0, RY0, RX1, RY1)).convert('RGBA')
    reg.alpha_composite(cache[prog])
    fr.paste(reg.convert('RGB'), (RX0, RY0))
    enc.stdin.write(fr.tobytes())
    i += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('frames', i)
