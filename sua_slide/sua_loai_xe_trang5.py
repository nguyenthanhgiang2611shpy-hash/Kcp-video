"""Trang 5 (đăng ký xe): Loại xe = Normal Truck, danh sách Trailer / Normal Truck, dòng giải thích mới."""
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT, REF_VAL, REF_CAL, FONTDIR = sys.argv[1:6]
W, H = 1600, 900
F_VAL = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 18.5)
F_CAL = ImageFont.truetype(f'{FONTDIR}/Nunito-800.ttf', 23.6)
INK_VAL, INK_CAL = (20, 20, 22), (26, 34, 41)

# ---- giá trị trong ô Loại xe ----
VAL = (1094, 397, 1260, 429)
ref_val = np.array(Image.open(REF_VAL).convert('RGB').crop(VAL), np.float32)
new_val_img = Image.new('RGB', (VAL[2] - VAL[0], VAL[3] - VAL[1]), (255, 255, 255))
ImageDraw.Draw(new_val_img).text((1101 - VAL[0], 419 - VAL[1]), 'Normal Truck', font=F_VAL, fill=INK_VAL, anchor='ls')
new_val = np.array(new_val_img, np.float32)
white = np.full_like(ref_val, 255)
d_old = (ref_val - white).ravel()
VAL_FROM = 1205

# ---- dòng giải thích ----
CAL = (745, 662, 1482, 716)
ref_cal_img = Image.open(REF_CAL).convert('RGB').crop(CAL)
ref_cal = np.array(ref_cal_img, np.float32)
new_cal_img = ref_cal_img.copy()
dc = ImageDraw.Draw(new_cal_img)
for y in range(new_cal_img.height):
    dc.line([(748 - CAL[0], y), (CAL[2] - CAL[0] - 1, y)], fill=ref_cal_img.getpixel((CAL[2] - CAL[0] - 8, y)))
txt = [('Container bạt chọn ', False), ('Trailer', True), (' · 4 chân trở xuống chọn ', False), ('Normal Truck', True)]
F_CAL_R = ImageFont.truetype(f'{FONTDIR}/Nunito-600.ttf', 23.6)
x = 753 - CAL[0]
for s, b in txt:
    f = F_CAL if b else F_CAL_R
    dc.text((x, 701 - CAL[1]), s, font=f, fill=INK_CAL, anchor='ls'); x += f.getlength(s)
print('dòng giải thích kết thúc ở x =', CAL[0] + x)
new_cal = np.array(new_cal_img, np.float32)

# ---- danh sách xổ xuống: vẽ lại đúng vị trí, kiểu danh sách cũ ----
CLEAN = np.array(Image.open(sys.argv[6]).convert('RGB'))      # khung trước khi mở danh sách
FULL = np.array(Image.open(sys.argv[7]).convert('RGB'))       # khung danh sách cũ hiện đủ (chưa tô)
BX0, BY0, BX1, BY1 = 1091, 433, 1277, 532
CLR = (1080, 428, 1300, 562)                                   # vùng dán nền sạch
ROWS = [('-- Chọn loại xe --', 434, 466), ('Trailer', 467, 501), ('Normal Truck', 502, 531)]
HL, HL_FROM = (47, 126, 237), 1178
P0, P1 = 1144, 1224
def est_alpha(fr):
    c = CLEAN[BY0:BY1, BX0:BX1].astype(np.float32)
    full = np.abs(FULL[BY0:BY1, BX0:BX1].astype(np.float32) - c).mean()
    cur = np.abs(fr[BY0:BY1, BX0:BX1].astype(np.float32) - c).mean()
    return max(0.0, min(1.0, cur / full))
def popup(n):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle([BX0 + 2, BY0 + 6, BX1 + 2, BY1 + 6], fill=60)
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    lay = Image.composite(Image.new('RGBA', (W, H), (60, 60, 60, 255)), lay, sh)
    d = ImageDraw.Draw(lay)
    d.rectangle([BX0, BY0, BX1, BY1], fill=(255, 255, 255, 255), outline=(170, 170, 170, 255))
    for k, (txt, y0, y1) in enumerate(ROWS):
        hl = (k == 2 and n >= HL_FROM)
        if hl:
            d.rectangle([BX0 + 1, y0, BX1 - 1, y1], fill=HL + (255,))
        d.text((1101, y0 + (y1 - y0) / 2 + 7), txt, font=F_VAL, fill=((255, 255, 255, 255) if hl else INK_VAL + (255,)), anchor='ls')
    # con trỏ: đi từ dòng đầu xuống dòng Normal Truck
    k = max(0.0, min(1.0, (n - 1150) / 26))
    cx, cy = 1170, int(452 + (516 - 452) * k)
    pts = [(cx, cy), (cx, cy + 22), (cx + 6, cy + 17), (cx + 10, cy + 26), (cx + 14, cy + 24), (cx + 10, cy + 15), (cx + 17, cy + 15)]
    d.polygon(pts, fill=(20, 20, 20, 255), outline=(255, 255, 255, 255))
    return lay

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                       stdin=subprocess.PIPE)
n = 0; cal_hits = []; val_hits = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    fr = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
    # dòng giải thích: thay khi khung khớp với dòng cũ
    reg = fr[CAL[1]:CAL[3], CAL[0]:CAL[2]].astype(np.float32)
    if np.abs(reg - ref_cal).mean() < 4:
        fr[CAL[1]:CAL[3], CAL[0]:CAL[2]] = new_cal.astype(np.uint8); cal_hits.append(n)
    # giá trị ô Loại xe
    if n >= VAL_FROM:
        reg = fr[VAL[1]:VAL[3], VAL[0]:VAL[2]].astype(np.float32)
        a = float(np.dot((reg - white).ravel(), d_old) / np.dot(d_old, d_old))
        if a > 0.75:
            keep = (np.abs(reg - ref_val).max(axis=2) > 60)[..., None]   # con trỏ chuột đè lên ô
            fr[VAL[1]:VAL[3], VAL[0]:VAL[2]] = np.where(keep, reg, new_val).astype(np.uint8); val_hits += 1
    # danh sách xổ xuống
    if P0 <= n <= P1:
        al = est_alpha(fr)
        if al > 0.02:
            x0, y0, x1, y1 = CLR
            fr[y0:y1, x0:x1] = CLEAN[y0:y1, x0:x1]
            lay = popup(n)
            if al < 1:
                lay.putalpha(lay.getchannel('A').point(lambda v: int(v * al)))
            im = Image.fromarray(fr).convert('RGBA'); im.alpha_composite(lay)
            fr = np.array(im.convert('RGB'))
    enc.stdin.write(fr.tobytes())
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('khung', n, '| dòng giải thích thay', len(cal_hits), (cal_hits[0], cal_hits[-1]) if cal_hits else None, '| ô Loại xe thay', val_hits)
