import math, os, sys
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
FPS = 30
SS = 4  # vẽ phóng to 4 lần cho mượt rồi thu nhỏ
SKIN = (242, 199, 165)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13 * SS)

def nguoi(kind, phase, walking):
    """Vẽ 1 người nhìn ngang, hướng sang phải. Trả về ảnh RGBA, gốc = giữa bàn chân."""
    W, H = 70 * SS, 112 * SS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = SS
    cx = 35 * s
    foot_y = 108 * s
    hip_y = foot_y - 40 * s
    sh_y = hip_y - 30 * s
    head_c = (cx + 2 * s, sh_y - 12 * s)
    if kind == 'bao_ve':
        shirt, pants, hat = (37, 70, 120), (30, 41, 59), (25, 45, 85)
    else:
        shirt, pants, hat = (59, 130, 246), (51, 65, 85), (250, 204, 21)
    sw = math.sin(phase) if walking else 0.0
    leg = 22 * sw  # độ
    arm = -18 * sw

    def limb(x0, y0, length, ang, width, color):
        a = math.radians(ang)
        x1 = x0 + length * math.sin(a)
        y1 = y0 + length * math.cos(a)
        d.line([(x0, y0), (x1, y1)], fill=color, width=width)
        r = width // 2
        d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=color)
        d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=color)
        return x1, y1

    darker = tuple(max(0, c - 25) for c in pants)
    # chân sau, tay sau
    x, y = limb(cx, hip_y, 38 * s, -leg, 9 * s, darker)
    d.rounded_rectangle([x - 4 * s, y - 2 * s, x + 9 * s, y + 3 * s], radius=2 * s, fill=(20, 24, 33))
    limb(cx, sh_y + 3 * s, 26 * s, -arm, 7 * s, tuple(max(0, c - 30) for c in shirt))
    # thân
    d.rounded_rectangle([cx - 9 * s, sh_y - 2 * s, cx + 9 * s, hip_y + 4 * s], radius=6 * s, fill=shirt)
    if kind == 'can':  # áo phản quang
        d.rounded_rectangle([cx - 9 * s, sh_y + 2 * s, cx + 9 * s, hip_y + 2 * s], radius=5 * s, fill=(249, 115, 22))
        d.rectangle([cx - 9 * s, sh_y + 14 * s, cx + 9 * s, sh_y + 17 * s], fill=(229, 231, 235))
        d.rectangle([cx - 9 * s, sh_y + 21 * s, cx + 9 * s, sh_y + 24 * s], fill=(229, 231, 235))
    else:  # cầu vai, thắt lưng
        d.rectangle([cx - 9 * s, hip_y - 2 * s, cx + 9 * s, hip_y + 1 * s], fill=(15, 23, 42))
        d.rectangle([cx - 6 * s, sh_y + 6 * s, cx - 1 * s, sh_y + 10 * s], fill=(250, 204, 21))
    # chân trước
    x, y = limb(cx, hip_y, 38 * s, leg, 9 * s, pants)
    d.rounded_rectangle([x - 4 * s, y - 2 * s, x + 9 * s, y + 3 * s], radius=2 * s, fill=(20, 24, 33))
    # tay trước (cầm sổ kiểm tra)
    hx, hy = limb(cx, sh_y + 3 * s, 26 * s, arm, 7 * s, shirt)
    d.ellipse([hx - 3 * s, hy - 3 * s, hx + 3 * s, hy + 3 * s], fill=SKIN)
    if kind == 'bao_ve':
        d.rounded_rectangle([hx, hy - 12 * s, hx + 10 * s, hy + 2 * s], radius=1 * s, fill=(255, 255, 255), outline=(100, 116, 139), width=s)
    # cổ, đầu
    d.rectangle([cx - 2 * s, sh_y - 5 * s, cx + 4 * s, sh_y + 1 * s], fill=SKIN)
    hx0, hy0 = head_c
    d.ellipse([hx0 - 9 * s, hy0 - 10 * s, hx0 + 9 * s, hy0 + 9 * s], fill=SKIN)
    d.ellipse([hx0 + 4 * s, hy0 - 3 * s, hx0 + 6 * s, hy0 - 1 * s], fill=(30, 41, 59))
    if kind == 'bao_ve':  # mũ kê-pi
        d.chord([hx0 - 10 * s, hy0 - 16 * s, hx0 + 9 * s, hy0 + 2 * s], 180, 360, fill=hat)
        d.rounded_rectangle([hx0 - 2 * s, hy0 - 8 * s, hx0 + 14 * s, hy0 - 5 * s], radius=1 * s, fill=(15, 23, 42))
    else:  # mũ bảo hộ
        d.chord([hx0 - 11 * s, hy0 - 18 * s, hx0 + 11 * s, hy0 + 3 * s], 180, 360, fill=hat)
        d.rounded_rectangle([hx0 - 12 * s, hy0 - 9 * s, hx0 + 14 * s, hy0 - 6 * s], radius=1 * s, fill=(234, 179, 8))
    return im

def nhan(text, color):
    tw = FONT.getbbox(text)[2]
    pad = 7 * SS
    im = Image.new('RGBA', (tw + 2 * pad, 22 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=11 * SS, fill=color)
    d.text((pad, 3 * SS), text, font=FONT, fill=(255, 255, 255))
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)

TAG_BV = nhan('Bảo vệ', (30, 58, 138))
TAG_CC = nhan('Cầu cân', (234, 88, 12))
FOOT_Y = 230  # mặt cân

# Đường đi: (x đầu, x cuối). Bảo vệ đi từ đuôi xe (trái) tới, NV cầu cân đi từ đầu xe (phải) tới.
WALK_END = 5.0  # giây: đi tới vị trí rồi đứng lại
PATHS = {'bao_ve': (420, 615), 'can': (965, 790)}

files = sorted(f for f in os.listdir(SRC) if f.endswith('.png'))
for i, f in enumerate(files):
    t = i / FPS
    fr = Image.open(os.path.join(SRC, f)).convert('RGBA')
    k = min(t / WALK_END, 1.0)
    walking = t < WALK_END
    for kind, (x0, x1) in PATHS.items():
        x = x0 + (x1 - x0) * k
        phase = t * 2 * math.pi * 1.6
        p = nguoi(kind, phase + (math.pi if kind == 'can' else 0), walking)
        p = p.resize((p.width // SS, p.height // SS), Image.LANCZOS)
        if kind == 'can':
            p = p.transpose(Image.FLIP_LEFT_RIGHT)
        px = int(round(x - p.width / 2))
        py = FOOT_Y - p.height + 1
        fr.alpha_composite(p, (px, py))
        tag = TAG_BV if kind == 'bao_ve' else TAG_CC
        fr.alpha_composite(tag, (int(round(x - tag.width / 2)), max(0, py - 14)))
    fr.convert('RGB').save(os.path.join(OUT, f))
print('done', len(files))
