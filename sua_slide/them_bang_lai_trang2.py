"""Bước 3 video trang 2: thêm thẻ 'Bằng lái' và chữ ', bằng lái' vào dòng 'Tài xế mang theo'."""
import colorsys, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT, F390, F470, FONTDIR = sys.argv[1:6]
W, H = 1600, 900
ref = Image.open(F390).convert('RGB')     # khung có đủ 3 thẻ
clean = Image.open(F470).convert('RGB')   # khung không có thẻ
F_SUB = ImageFont.truetype(f'{FONTDIR}/Nunito-600.ttf', 32)
F_LAB = ImageFont.truetype(f'{FONTDIR}/Nunito-800.ttf', 29)
SUB_COLOR = (74, 81, 92)
LAB_COLOR = (27, 31, 35)

# ---- dòng chữ: chèn ', bằng lái' sau 'CCCD' ----
sub_txt = 'Tài xế mang theo: đăng kiểm xe, cà vẹt xe, CCCD'
add_txt = ', bằng lái'
x_add = 100 + F_SUB.getlength(sub_txt) + 4
y_sub = 255 - F_SUB.getbbox(sub_txt)[1]
SUB_STABLE = None

def sub_dark(fr):
    g = fr.crop((100, 250, 814, 292)).convert('L')
    return sum(255 - v for v in g.get_flattened_data() if v < 200)

# ---- thẻ giấy tờ ----
CW, CH, R = 222, 275, 18
CY = 392
GAP = 22
CX = [140 + k * (CW + GAP) for k in range(4)]
ICON_BOX = {0: (175, 412, 350, 555), 1: (476, 412, 651, 555), 2: (775, 412, 950, 555)}
LABELS = ['Đăng kiểm xe', 'Cà vẹt xe', 'CCCD', 'Bằng lái']

def recolor_orange(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y][:3]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s > 0.25 and 0.65 < h < 0.85:  # màu tím của CCCD
                nr, ng, nb = colorsys.hsv_to_rgb(0.07, s, v)
                px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255))
    return im

def make_card(k):
    pad = 30
    im = Image.new('RGBA', (CW + 2 * pad, CH + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 8, pad + CW, pad + CH + 4], radius=R, fill=40)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    im.paste((60, 80, 110, 255), (0, 0), sh)
    ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + CW - 1, pad + CH - 1], radius=R, fill=(255, 255, 255, 255))
    icon = ref.crop(ICON_BOX[min(k, 2)])
    if k == 3:
        icon = recolor_orange(icon.copy())
    im.paste(icon, (pad + (CW - icon.width) // 2, pad + 20))
    d = ImageDraw.Draw(im)
    tw = F_LAB.getlength(LABELS[k])
    d.text((pad + (CW - tw) / 2, pad + 205), LABELS[k], font=F_LAB, fill=LAB_COLOR, anchor='ls')
    return im, pad

CARDS = [make_card(k) for k in range(4)]
APPEAR = [323, 340, 357, 374]     # khung bắt đầu hiện từng thẻ
APPEAR_LEN = 10
SLIDE = [411, 408, 405, 402]      # khung bắt đầu trượt vào màn hình (thẻ bên phải đi trước)
SLIDE_LEN = 21
TARGET_X = 1215                   # tâm màn hình
CLIP_X = 1112                     # mép trái màn hình
P0, P1 = 323, 434                 # khoảng khung vẽ lại hàng thẻ

def ease_out(t): return 1 - (1 - t) ** 3
def ease_in(t): return t ** 3

def draw_cards(fr, n):
    layer = Image.new('RGBA', (CLIP_X, H), (0, 0, 0, 0))
    for k in range(4):
        card, pad = CARDS[k]
        if n < APPEAR[k]:
            continue
        a = ease_out(min((n - APPEAR[k]) / APPEAR_LEN, 1))
        scale = 0.85 + 0.15 * a
        cx = CX[k] + CW / 2
        cy = CY + CH / 2
        if n >= SLIDE[k]:
            t = ease_in(min((n - SLIDE[k]) / SLIDE_LEN, 1))
            cx = cx + (TARGET_X - cx) * t
            scale = 1 - 0.5 * t
        if scale <= 0:
            continue
        c = card.resize((max(1, int(card.width * scale)), max(1, int(card.height * scale))), Image.LANCZOS)
        if a < 1:
            al = c.getchannel('A').point(lambda v: int(v * a))
            c.putalpha(al)
        layer.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)) if cx - c.width / 2 >= 0 else (0, 0))
    region = fr.crop((0, 0, CLIP_X, H)).convert('RGBA')
    region.alpha_composite(layer)
    fr.paste(region.convert('RGB'), (0, 0))

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30',
                        '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT],
                       stdin=subprocess.PIPE)
SUB_STABLE = sub_dark(ref)
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    if 312 <= n <= 507 or P0 <= n <= P1:
        fr = Image.frombytes('RGB', (W, H), buf)
        if P0 <= n <= P1:
            fr.paste(clean.crop((0, 370, CLIP_X, 720)), (0, 370))
            draw_cards(fr, n)
        if 312 <= n <= 507:
            a = min(sub_dark(fr) / SUB_STABLE, 1.0)
            if a > 0.01:
                lay = Image.new('RGBA', (W, 60), (0, 0, 0, 0))
                ImageDraw.Draw(lay).text((x_add, y_sub - 240), add_txt, font=F_SUB, fill=SUB_COLOR + (int(255 * a),))
                reg = fr.crop((0, 240, W, 300)).convert('RGBA'); reg.alpha_composite(lay)
                fr.paste(reg.convert('RGB'), (0, 240))
        buf = fr.tobytes()
    enc.stdin.write(buf)
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('frames', n)
