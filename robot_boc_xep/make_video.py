# -*- coding: utf-8 -*-
"""Video trình chiếu: Bốc xếp bao lên xe bằng robot (16:9, tiếng Việt).
Ghép 6 clip gốc (khổ dọc, phụ đề tiếng Anh) thành 1 video ngang 1280x720:
cắt bỏ khung đen + phụ đề gốc, chú thích tiếng Việt bên phải.
Chạy:  python3 make_video.py           -> render đầy đủ (OUT)
       python3 make_video.py test      -> contact sheet khung mẫu
"""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
W, H, FPS = 1280, 720, 25
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "Robot_boc_xep_bao_len_xe_v1.mp4")

CREAM = (243, 236, 220); INK = (29, 43, 58); ORANGE = (217, 119, 75)
MUTED = (110, 116, 120); WHITE = (255, 255, 255)

FP = {"serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
      "serifb": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
      "mono": "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
      "monob": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"}
_fc = {}
def F(n, s):
    if (n, s) not in _fc: _fc[(n, s)] = ImageFont.truetype(FP[n], s)
    return _fc[(n, s)]

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, t0, t1): return ss((t - t0) / (t1 - t0))
def mix(c1, c2, k): return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))

def wrap(d, s, font, maxw):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

def text_block(d, x, y, s, name, size, maxw, fill, gap=1.25, minsize=16):
    while True:
        f = F(name, size); lines = wrap(d, s, f, maxw)
        if all(d.textlength(l, font=f) <= maxw for l in lines) or size <= minsize: break
        size -= 1
    for l in lines:
        d.text((x, y), l, font=f, fill=fill); y += int(size * gap)
    return y

def chapter_label(img, x, y, s, alpha=1.0):
    f = F("monob", 22)
    tw = int(ImageDraw.Draw(img).textlength(s, font=f))
    lab = Image.new("RGBA", (tw + 36, 44), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lab)
    dl.rectangle([0, 0, tw + 36, 44], fill=INK + (int(255 * alpha),))
    dl.text((18, 9), s, font=f, fill=CREAM + (int(255 * alpha),))
    lab = lab.rotate(2, expand=True, resample=Image.BICUBIC)
    img.paste(lab, (x, y), lab)

def corners(d, x0, y0, x1, y1, c=ORANGE, L=26, w=4):
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(x, y), (x + sx * L, y)], fill=c, width=w)
        d.line([(x, y), (x, y + sy * L)], fill=c, width=w)

def footer(d, n, N):
    d.line([(40, 676), (W - 40, 676)], fill=mix(CREAM, INK, 0.25), width=1)
    d.text((40, 686), "KCP VIỆT NAM · LOGISTICS · ROBOT BỐC XẾP BAO LÊN XE", font=F("mono", 15), fill=MUTED)
    s = f"Nguồn clip: Shandong Tengyang (Facebook) · {n}/{N}"
    d.text((W - 40 - d.textlength(s, font=F("mono", 15)), 686), s, font=F("mono", 15), fill=MUTED)

# ---------- clip gốc: vùng hình thật (x0, y0, x1, y1) trên khung 716/720 x 1274/1280 ----------
CLIPS = {
    1: (0, 352, 716, 908),
    2: (0, 0, 720, 900),
    3: (0, 420, 716, 838),
    4: (0, 372, 716, 896),
    5: (0, 262, 716, 990),
    6: (0, 312, 716, 904),
}
TRIM = {1: 1.3}  # clip1: 1,3 giây đầu là góc quay khác, khung đen -> bỏ
BOX_H, BOX_Y, BOX_X, BOX_MAXW = 540, 108, 40, 720

def clip_box(i):
    x0, y0, x1, y1 = CLIPS[i]
    cw, ch = x1 - x0, y1 - y0
    h = BOX_H; w = int(round(cw * h / ch / 2) * 2)
    if w > BOX_MAXW:
        w = BOX_MAXW; h = int(round(ch * w / cw / 2) * 2)
    return w, h

def probe_dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode())

def read_clip(i):
    x0, y0, x1, y1 = CLIPS[i]; w, h = clip_box(i)
    p = os.path.join(SRC, f"clip{i}.mp4")
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(TRIM.get(i, 0)), "-i", p, "-vf",
        f"fps={FPS},crop={x1-x0}:{y1-y0}:{x0}:{y0},scale={w}:{h}:flags=lanczos",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    n = len(raw) // (w * h * 3)
    return [Image.frombuffer("RGB", (w, h), raw[k * w * h * 3:(k + 1) * w * h * 3]) for k in range(n)]

# ---------- kịch bản ----------
# (clip, nhãn chương, phụ đề chính, dòng phụ, con dấu)
SHOTS = [
    (3, "01 · THAY BỐC VÁC", "Máy xếp bao tự động thay người bốc vác lên xe",
     "Xếp bao gọn, chạy liên tục, giảm rách bao", "BỚT BỐC VÁC"),
    (1, "01 · THAY BỐC VÁC", "Robot xếp bao theo chương trình, chồng hàng ngay ngắn",
     "Giảm sức lao động nặng nhọc", "XẾP GỌN"),
    (2, "02 · XẾP LÊN XE", "Cánh tay robot gắp bao, xếp thẳng vào thùng xe",
     "Bao đi từ băng tải lên xe, không qua tay người", "TĂNG TỐC"),
    (6, "02 · XẾP LÊN XE", "Băng tải và robot chạy dọc theo xe thùng dài",
     "Xếp lần lượt từ đầu thùng ra cuối thùng", "XE DÀI"),
    (4, "03 · TỰ NHẬN DIỆN XE", "Robot quét LiDAR, tự nhận diện xe và vạch đường xếp",
     "Không cần chỉnh tay cho từng loại xe", "QUÉT LIDAR"),
    (5, "04 · CHẠY 24/24", "Máy xếp bao thông minh, chạy ổn định 24 giờ",
     "Hoạt động liên tục nhiều ca", "24/24"),
]

N_TOTAL = len(SHOTS) + 3

def sc_hook(t, D):
    img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img)
    a = seg(t, 0, 0.6)
    d.text((80, 150), "BỐC XẾP BAO LÊN XE", font=F("monob", 26), fill=mix(CREAM, ORANGE, a))
    d.text((80, 195), "Xếp bao lên xe", font=F("serifb", 60), fill=mix(CREAM, INK, a))
    d.text((80, 270), "không cần người bốc vác?", font=F("serifb", 60), fill=mix(CREAM, INK, seg(t, 0.4, 1.0)))
    labs = ["01 · THAY BỐC VÁC", "02 · XẾP LÊN XE", "03 · TỰ NHẬN DIỆN XE", "04 · CHẠY 24/24"]
    x = 80
    for k, s in enumerate(labs):
        al = seg(t, 1.4 + 0.35 * k, 1.9 + 0.35 * k)
        if al > 0:
            chapter_label(img, x, 420, s, al)
        x += int(d.textlength(s, font=F("monob", 22))) + 60
    d.text((80, 520), "Tư liệu: 6 clip giới thiệu robot xếp bao lên xe tải (nhà sản xuất Trung Quốc)",
           font=F("serif", 22), fill=mix(CREAM, MUTED, seg(t, 2.6, 3.2)))
    footer(d, 1, N_TOTAL)
    return img

def make_shot(idx, shot, frames):
    ci, lab, cap, sub, stamp = shot
    bw, bh = frames[0].size
    bx, by = BOX_X + (BOX_MAXW - bw) // 2 if bw < 560 else BOX_X, BOX_Y
    px = bx + bw + 50; pw = W - 40 - px
    def sc(t, D):
        img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img)
        k = min(int(t * FPS), len(frames) - 1)
        d.rectangle([bx - 6, by - 6, bx + bw + 5, by + bh + 5], fill=INK)
        img.paste(frames[k], (bx, by))
        corners(d, bx - 16, by - 16, bx + bw + 15, by + bh + 15)
        chapter_label(img, 40, 28, lab)
        a = seg(t, 0.3, 0.9)
        y = by + 40
        y = text_block(d, px, y, cap, "serifb", 36, pw, mix(CREAM, INK, a))
        y += 18
        d.line([(px, y), (px + 60, y)], fill=mix(CREAM, ORANGE, a), width=4)
        y += 24
        y = text_block(d, px, y, sub, "serif", 24, pw, mix(CREAM, MUTED, seg(t, 0.8, 1.4)))
        b = seg(t, 1.8, 2.3)
        if b > 0:
            f = F("monob", 26); tw = d.textlength(stamp, font=f)
            st = Image.new("RGBA", (int(tw) + 40, 56), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
            ds.rectangle([2, 2, tw + 37, 53], outline=ORANGE + (int(255 * b),), width=4)
            ds.text((20, 12), stamp, font=f, fill=ORANGE + (int(255 * b),))
            st = st.rotate(-6, expand=True, resample=Image.BICUBIC)
            img.paste(st, (px, by + bh - 110), st)
        footer(d, idx + 2, N_TOTAL)
        return img
    return sc

TILES = [("ÍT NGƯỜI", "bốc vác, giảm", "việc nặng nhọc"),
         ("XẾP GỌN", "bao ngay hàng,", "giảm rách bao"),
         ("TỰ ĐỘNG", "quét LiDAR,", "nhận diện xe"),
         ("24/24", "chạy liên tục", "nhiều ca")]

def sc_sum(t, D):
    img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img)
    chapter_label(img, 40, 28, "TÓM TẮT · ROBOT LÀM ĐƯỢC GÌ")
    tw_, gap = 270, 23
    for k, (big, l1, l2) in enumerate(TILES):
        a = seg(t, 0.3 + 0.4 * k, 0.9 + 0.4 * k)
        x = 40 + k * (tw_ + gap); y = 150
        d.rectangle([x, y, x + tw_, y + 330], fill=mix(CREAM, INK, a))
        d.rectangle([x, y, x + tw_, y + 10], fill=mix(CREAM, ORANGE, a))
        sz = 46
        while d.textlength(big, font=F("serifb", sz)) > tw_ - 30: sz -= 1
        f = F("serifb", sz); bw = d.textlength(big, font=f)
        d.text((x + (tw_ - bw) / 2, y + 90), big, font=f, fill=mix(CREAM, CREAM, a))
        for j, l in enumerate((l1, l2)):
            f2 = F("serif", 24); lw = d.textlength(l, font=f2)
            d.text((x + (tw_ - lw) / 2, y + 190 + 36 * j), l, font=f2, fill=mix(CREAM, (220, 214, 200), a))
    d.text((40, 520), "Theo giới thiệu của nhà sản xuất trong clip, chưa kiểm chứng thực tế tại KCP.",
           font=F("serif", 22), fill=mix(CREAM, MUTED, seg(t, 2.2, 2.8)))
    footer(d, N_TOTAL - 1, N_TOTAL)
    return img

QUESTIONS = ["Có xếp được bao đường 50 kg, xe container bạt?",
             "Năng suất bao nhiêu bao/giờ so với tổ bốc xếp?",
             "Chi phí đầu tư, mặt bằng kho, thời gian hoàn vốn?"]

def sc_end(t, D):
    img = Image.new("RGB", (W, H), ORANGE); d = ImageDraw.Draw(img)
    d.text((80, 90), "CẦN LÀM RÕ CHO KCP", font=F("monob", 26), fill=INK)
    d.text((80, 135), "Robot có hợp với kho KCP?", font=F("serifb", 52), fill=WHITE)
    for k, q in enumerate(QUESTIONS):
        a = seg(t, 0.6 + 0.5 * k, 1.1 + 0.5 * k)
        y = 250 + 80 * k
        d.text((80, y), f"({k+1})", font=F("monob", 30), fill=mix(ORANGE, INK, a))
        d.text((150, y - 2), q, font=F("serif", 32), fill=mix(ORANGE, WHITE, a))
    d.text((80, 560), "Đề xuất: liên hệ nhà cung cấp lấy thông số, báo giá và video chạy với bao 50 kg.",
           font=F("serif", 22), fill=mix(ORANGE, INK, seg(t, 2.4, 3.0)))
    d.line([(40, 676), (W - 40, 676)], fill=mix(ORANGE, INK, 0.4), width=1)
    d.text((40, 686), "KCP VIỆT NAM · LOGISTICS · ROBOT BỐC XẾP BAO LÊN XE", font=F("mono", 15), fill=INK)
    s = f"Nguồn clip: Shandong Tengyang (Facebook) · {N_TOTAL}/{N_TOTAL}"
    d.text((W - 40 - d.textlength(s, font=F("mono", 15)), 686), s, font=F("mono", 15), fill=INK)
    return img

def build():
    scenes = [("hook", 5.0, sc_hook)]
    for idx, shot in enumerate(SHOTS):
        fr = read_clip(shot[0])
        scenes.append((f"clip{shot[0]}", len(fr) / FPS, make_shot(idx, shot, fr)))
    scenes += [("tom_tat", 7.0, sc_sum), ("chot", 8.0, sc_end)]
    return scenes

XF = 8  # số khung trộn chuyển cảnh

def render(scenes, out):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-shortest", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    prev_last = None
    for name, D, fn in scenes:
        n = int(round(D * FPS))
        for k in range(n):
            im = fn(k / FPS, D)
            if prev_last is not None and k < XF:
                im = Image.blend(prev_last, im, (k + 1) / (XF + 1))
            p.stdin.write(im.tobytes())
        prev_last = fn((n - 1) / FPS, D)
        print(name, round(D, 2), flush=True)
    p.stdin.close(); p.wait()
    print("done", flush=True)

def test(scenes, out):
    ims = []
    for name, D, fn in scenes:
        for t in (0.2, D * 0.5, D - 0.1):
            ims.append(fn(t, D).resize((427, 240)))
    cols = 3; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (427 * cols, 240 * rows), "white")
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * 427, (k // cols) * 240))
    sheet.save(out)
    for name, D, fn in scenes:
        fn(D * 0.6, D).save(out.replace(".png", f"_{name}.png"))

if __name__ == "__main__":
    sc = build()
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test(sc, sys.argv[2] if len(sys.argv) > 2 else "sheet.png")
    else:
        render(sc, OUT)
