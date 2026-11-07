"""Trang 15 (gốc 39): đổi nhãn 'Kho ký'/'Process ký' thành 'Kho xác nhận'/'Process xác nhận'."""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont
SRC, OUT, FULL = sys.argv[1:4]
W, H = 1386, 190
BG = (254, 250, 242)
PILL, INK = (209, 250, 229), (6, 95, 70)
F = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 19)
full = Image.open(FULL).convert('RGB')
OLD = [(776, 16, 876, 50), (904, 16, 1044, 50)]          # nhãn cũ
TXT = ['Kho xác nhận', 'Process xác nhận']
PADX, GAP, X0, Y0, PH = 17, 28, 776, 16, 34
SS = 4

def darkness(im, box):
    g = im.crop(box).convert('L')
    return sum(255 - v for v in g.get_flattened_data())
absent = [darkness(Image.new('RGB', (W, H), BG), b) for b in OLD]
present = [darkness(full, b) for b in OLD]

def pill(text):
    tw = F.getlength(text)
    w = int(round(tw + 2 * PADX))
    im = Image.new('RGBA', (w * SS, PH * SS), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * SS - 1, PH * SS - 1], radius=PH * SS // 2, fill=PILL + (255,))
    im = im.resize((w, PH), Image.LANCZOS)
    ImageDraw.Draw(im).text((w / 2, PH / 2 + 1), text, font=F, fill=INK + (255,), anchor='mm')
    return im
PILLS = [pill(t) for t in TXT]
POS = [X0, X0 + PILLS[0].width + GAP]
print('vùng nhãn mới', POS[0], POS[1] + PILLS[1].width)
ERASE = (770, 12, max(1050, POS[1] + PILLS[1].width + 4), 54)

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                        '-i', '-', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                       stdin=subprocess.PIPE)
n = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    fr = Image.frombytes('RGB', (W, H), b)
    alphas = [max(0.0, min(1.0, (darkness(fr, box) - a0) / (p - a0))) for box, a0, p in zip(OLD, absent, present)]
    ImageDraw.Draw(fr).rectangle(ERASE, fill=BG)
    lay = fr.convert('RGBA')
    for pimg, x, a in zip(PILLS, POS, alphas):
        if a <= 0.01:
            continue
        p = pimg.copy()
        p.putalpha(p.getchannel('A').point(lambda v: int(v * a)))
        lay.alpha_composite(p, (x, Y0))
    enc.stdin.write(lay.convert('RGB').tobytes())
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('frames', n)
