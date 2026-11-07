"""Trang 14 (gốc 38): 'Kho + Process kiểm tra, ký xác nhận' -> 'Kho + Process kiểm tra và xác nhận'."""
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
SRC, OUT, BASE = sys.argv[1], sys.argv[2], int(sys.argv[3])
W, H = 1386, 550
F = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 19.2)
X_TRA = 960                     # chữ "tra," bắt đầu ở đây
mask = Image.new('L', (W, H), 0)
ImageDraw.Draw(mask).text((X_TRA, BASE), 'tra và xác nhận', font=F, fill=255, anchor='ls')
M = np.array(mask, np.float32)[..., None] / 255.0
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
n = 0
while True:
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    fr = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
    bg = fr[375, 1150].copy()                                   # màu nền khung số 2 lúc này
    word = fr[366:385, 829:904]                                 # chữ "Process" để lấy màu chữ lúc này
    px = word.reshape(-1, 3); dist = np.abs(px - bg).max(axis=1)
    strong = px[dist >= np.percentile(dist, 97)]
    ink = strong.mean(axis=0)                                   # màu lõi nét chữ (không lấy điểm đậm nhất)
    # xoá "tra, ký xác nhận" (giữ nguyên dòng trên)
    fr[361:391, 957:1114] = bg
    fr[352:361, 1012:1114] = bg
    fr = fr * (1 - M) + ink * M
    enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('khung', n)
