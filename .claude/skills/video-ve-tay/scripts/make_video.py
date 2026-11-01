# -*- coding: utf-8 -*-
"""Dựng video vẽ tay (whiteboard animation) từ file script.json.

Cách dùng:
    python3 make_video.py <thư_mục_dự_án>            # tạo đủ ảnh/giọng/nhạc rồi dựng video
    python3 make_video.py <thư_mục_dự_án> --offline  # không gọi API (ảnh nháp + im lặng) để thử nhanh
    python3 make_video.py <thư_mục_dự_án> --preview  # chỉ xuất ảnh khung mẫu preview.png

Trong thư mục dự án cần có script.json (xem SKILL.md). Ảnh/giọng đã có sẵn thì không tạo lại,
nên muốn sửa cảnh nào chỉ cần xoá file scene_XX.png / scene_XX.mp3 của cảnh đó rồi chạy lại.
"""
import json, math, subprocess, sys, textwrap
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import kie_client as kie

FPS = 25
PAPER = (250, 249, 245)
INK = (35, 38, 44)
ACCENT = (217, 119, 75)
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

STYLE_PRESETS = {
    "ve-tay": "hand-drawn whiteboard doodle illustration, black marker outlines, soft flat watercolor colors, "
              "pure white background, simple and clean, no text, no letters",
    "nguoi-que": "simple stick figure drawing, black marker lines, minimal accent color, pure white background, "
                 "no text, no letters",
    "dong-ho": "Vietnamese Dong Ho folk woodblock painting style, warm earthy colors, bold black outlines, "
               "plain light paper background, no text, no letters",
    "ky-thuat": "clean technical sketch, isometric line drawing, black ink, light flat colors, pure white "
                "background, no text, no letters",
}


# ---------------------------------------------------------------- tiện ích
def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def ss(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def font(path, size):
    return ImageFont.truetype(path, int(size))


# ---------------------------------------------------------------- bàn tay cầm cọ
def make_brush_hand(scale=1.0):
    """Vẽ bàn tay cầm cọ (vector) – đầu cọ nằm ở toạ độ trả về (tip)."""
    S = 4  # vẽ to rồi thu nhỏ cho mịn
    w, h = int(330 * scale), int(330 * scale)
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = scale * S
    P = lambda x, y: (x * k, y * k)
    skin, skin_d, line = (241, 196, 160, 255), (214, 160, 122, 255), (90, 60, 45, 255)
    # cán cọ (gỗ) chéo từ đầu cọ (10,10) lên phải-dưới
    d.line([P(30, 30), P(250, 250)], fill=(140, 82, 44, 255), width=int(14 * k))
    d.line([P(34, 26), P(250, 242)], fill=(176, 110, 64, 255), width=int(5 * k))
    # đai kim loại
    d.line([P(22, 22), P(48, 48)], fill=(185, 188, 194, 255), width=int(17 * k))
    d.line([P(22, 22), P(48, 48)], fill=(225, 228, 232, 255), width=int(5 * k))
    # đầu lông cọ
    d.polygon([P(4, 4), P(30, 14), P(26, 26), P(14, 30)], fill=(40, 34, 30, 255))
    d.ellipse([P(2, 2), P(10, 10)], fill=(25, 22, 20, 255))
    # bàn tay: lòng bàn tay + ngón cái + các ngón
    d.ellipse([P(120, 120), P(300, 280)], fill=skin, outline=line, width=int(2.5 * k))
    d.ellipse([P(70, 95), P(150, 140)], fill=skin, outline=line, width=int(2.5 * k))      # ngón trỏ
    d.ellipse([P(85, 130), P(165, 175)], fill=skin_d, outline=line, width=int(2.5 * k))   # ngón giữa
    d.ellipse([P(110, 60), P(165, 125)], fill=skin, outline=line, width=int(2.5 * k))     # ngón cái
    d.ellipse([P(105, 165), P(175, 205)], fill=skin_d, outline=line, width=int(2.5 * k))  # ngón áp út
    d.rectangle([P(250, 230), P(330, 330)], fill=(70, 96, 130, 255))                       # tay áo
    im = im.resize((w, h), Image.LANCZOS)
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 60), (0, 0), im.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(6 * scale))
    out = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    out.alpha_composite(shadow, (12, 12))
    out.alpha_composite(im, (0, 0))
    return out, (int(4 * scale), int(4 * scale))


# ---------------------------------------------------------------- chuẩn bị ảnh
def placeholder_image(text, size):
    """Ảnh nháp khi chạy offline: vẽ khung + vài nét để thử hiệu ứng."""
    W, H = size
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(abs(hash(text)) % 2**32)
    for _ in range(6):
        x, y = rng.integers(60, W - 260), rng.integers(60, H - 260)
        r = int(rng.integers(60, 140))
        col = tuple(int(c) for c in rng.integers(120, 230, 3))
        if rng.random() < .5:
            d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=col, outline=INK, width=6)
        else:
            d.rounded_rectangle([x, y, x + 2 * r, y + int(1.4 * r)], 20, fill=col, outline=INK, width=6)
    d.text((W // 2, H // 2), "\n".join(textwrap.wrap(text, 28)[:3]), font=font(FONT_B, 34),
           fill=INK, anchor="mm", align="center")
    return im


def fit_on_paper(img, box_w, box_h):
    img = img.convert("RGB")
    k = min(box_w / img.width, box_h / img.height)
    img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
    # làm nền gần trắng thành màu giấy
    a = np.asarray(img).astype(np.float32)
    white = (a.min(axis=2) > 235)[..., None]
    a = np.where(white, np.array(PAPER, np.float32), a)
    page = np.empty((box_h, box_w, 3), np.float32)
    page[:] = PAPER
    ox, oy = (box_w - img.width) // 2, (box_h - img.height) // 2
    page[oy:oy + img.height, ox:ox + img.width] = a
    return page


def line_art(color):
    """Tạo bản nét chì từ ảnh màu: viền + vùng đậm."""
    g = Image.fromarray(color.astype(np.uint8)).convert("L").filter(ImageFilter.GaussianBlur(1.2))
    ga = np.asarray(g).astype(np.float32)
    gy, gx = np.gradient(ga)
    mag = np.hypot(gx, gy)
    strength = np.clip(np.maximum((mag - 6) / 22, (110 - ga) / 70), 0, 1)
    paper = np.empty_like(color)
    paper[:] = PAPER
    ink = np.array(INK, np.float32)
    return paper * (1 - strength[..., None]) + ink * strength[..., None], strength


def cell_order(content_mask, cell, band=3):
    """Thứ tự vẽ: chia ô, đi theo từng dải ngang kiểu ziczac như người vẽ thật."""
    H, W = content_mask.shape
    ny, nx = math.ceil(H / cell), math.ceil(W / cell)
    has = np.zeros((ny, nx), bool)
    for j in range(ny):
        for i in range(nx):
            has[j, i] = content_mask[j * cell:(j + 1) * cell, i * cell:(i + 1) * cell].any()
    order = []
    for b, j0 in enumerate(range(0, ny, band)):
        cols = range(nx) if b % 2 == 0 else range(nx - 1, -1, -1)
        for i in cols:
            rows = range(j0, min(ny, j0 + band))
            for j in (rows if i % 2 == 0 else reversed(list(rows))):
                if has[j, i]:
                    order.append((j, i))
    rank = np.full((ny, nx), 10**9, np.int32)
    for n, (j, i) in enumerate(order):
        rank[j, i] = n
    pix = np.kron(rank, np.ones((cell, cell), np.int32))[:H, :W]
    centers = [((i + .5) * cell, (j + .5) * cell) for j, i in order]
    return pix, centers


# ---------------------------------------------------------------- dựng 1 cảnh
class Scene:
    def __init__(self, W, H, img, caption, dur, effect, hand, tip):
        self.W, self.H, self.dur, self.effect = W, H, dur, effect
        self.hand, self.tip = hand, tip
        cap_h = int(H * (0.17 if W > H else 0.22)) if caption else 0
        self.box = (int(W * .04), int(H * .04), W - int(W * .08), H - int(H * .06) - cap_h)
        bx, by, bw, bh = self.box
        self.color = fit_on_paper(img, bw, bh)
        self.lines, strength = line_art(self.color)
        content = np.abs(self.color - np.array(PAPER, np.float32)).max(axis=2) > 18
        cell = max(14, int(min(W, H) / 42))
        self.rank_line, self.path = cell_order(strength > .25, cell)
        self.rank_col, self.path_col = cell_order(content, cell)
        self.n_line = max(1, len(self.path))
        self.n_col = max(1, len(self.path_col))
        self.bg = np.empty((H, W, 3), np.float32)
        self.bg[:] = PAPER
        self.caption_img = self._caption(caption, cap_h) if caption else None
        self.t_draw = min(max(2.5, dur * .62), max(1.5, dur - 1.0))

    def _caption(self, text, cap_h):
        W = self.W
        im = Image.new("RGBA", (W, cap_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        size = cap_h * (.30 if W > self.H else .2)
        f = font(FONT_B, size)
        lines = textwrap.wrap(text, max(12, int(W / (size * .58))))[:3]
        y = cap_h * .12
        d.line([(W * .3, 4), (W * .7, 4)], fill=ACCENT + (255,), width=4)
        for ln in lines:
            d.text((W / 2, y + size * .6), ln, font=f, fill=INK + (255,), anchor="mm")
            y += size * 1.25
        return im

    def frame(self, t):
        W, H = self.W, self.H
        bx, by, bw, bh = self.box
        canvas = self.bg.copy()
        hand_xy = None
        if self.effect == "drop":
            # ảnh rơi từ trên xuống, nảy nhẹ (giống hiệu ứng HyperFrames)
            k = min(1.0, t / 0.9)
            bounce = 1 - math.exp(-6 * k) * math.cos(10 * k) if k < 1 else 1
            dy = int((1 - bounce) * -H * 0.9)
            y0 = by + dy
            ya, yb = max(0, y0), min(H, y0 + bh)
            if yb > ya:
                canvas[ya:yb, bx:bx + bw] = self.color[ya - y0:yb - y0]
        else:
            td = self.t_draw
            p_line = ss(t / (td * .62)) if td else 1
            p_col = ss((t - td * .5) / (td * .5))
            kl = p_line * self.n_line
            kc = p_col * self.n_col
            page = np.empty((bh, bw, 3), np.float32)
            page[:] = PAPER
            m = (self.rank_line < kl)[..., None]
            page = np.where(m, self.lines, page)
            mc = (self.rank_col < kc)[..., None]
            page = np.where(mc, self.color, page)
            canvas[by:by + bh, bx:bx + bw] = page
            if t < td:
                path, k = (self.path, kl) if p_col <= 0 else (self.path_col, kc)
                if path:
                    i = min(len(path) - 1, int(k))
                    x, y = path[i]
                    wob = 3 * math.sin(t * 23)
                    hand_xy = (bx + x + wob, by + y + wob * .5)
            elif t < td + .6:
                e = ss((t - td) / .6)
                x0, y0 = self.path_col[-1] if self.path_col else (bw / 2, bh / 2)
                hand_xy = (bx + x0 + e * W * .6, by + y0 + e * H * .7)
            if self.effect == "zoom" and t > td:
                z = 1 + .06 * ss((t - td) / max(.1, self.dur - td))
                im = Image.fromarray(canvas.astype(np.uint8))
                cw, ch = int(W / z), int(H / z)
                im = im.crop(((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)).resize((W, H))
                canvas = np.asarray(im).astype(np.float32)
        im = Image.fromarray(canvas.astype(np.uint8)).convert("RGBA")
        if self.caption_img is not None:
            a = ss(t / .5)
            cap = self.caption_img.copy()
            cap.putalpha(cap.split()[3].point(lambda v: int(v * a)))
            im.alpha_composite(cap, (0, H - cap.height))
        if hand_xy:
            hx, hy = int(hand_xy[0] - self.tip[0]), int(hand_xy[1] - self.tip[1])
            # chỉ dán phần bàn tay nằm trong khung hình
            sx, sy = max(0, -hx), max(0, -hy)
            if hx < W and hy < H and sx < self.hand.width and sy < self.hand.height:
                im.alpha_composite(self.hand, (max(0, hx), max(0, hy)), (sx, sy))
        if t < .25:  # mở cảnh mềm
            white = Image.new("RGBA", (W, H), PAPER + (int(255 * (1 - t / .25)),))
            im.alpha_composite(white)
        return np.asarray(im.convert("RGB"))


def render_scene(sc, audio, out, W, H):
    n = int(math.ceil(sc.dur * FPS))
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(audio),
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
                          "-af", "apad", "-t", f"{n / FPS:.3f}", str(out)], stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(sc.frame(f / FPS).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg lỗi khi dựng " + str(out))


# ---------------------------------------------------------------- chương trình chính
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--offline" in sys.argv or not kie.load_key()
    preview = "--preview" in sys.argv
    proj = Path(args[0] if args else ".").resolve()
    cfg = json.loads((proj / "script.json").read_text(encoding="utf-8"))
    vertical = cfg.get("aspect", "16:9") == "9:16"
    W, H = (720, 1280) if vertical else (1280, 720)
    style = STYLE_PRESETS.get(cfg.get("style", "ve-tay"), cfg.get("style", STYLE_PRESETS["ve-tay"]))
    hand, tip = make_brush_hand(0.9 if not vertical else 0.75)
    work = proj / "build"
    work.mkdir(exist_ok=True)
    if offline:
        print("⚠ Chạy offline (chưa có KIE_API_KEY hoặc có --offline): ảnh nháp + không có giọng đọc.")

    parts = []
    for i, s in enumerate(cfg["scenes"], 1):
        tag = f"scene_{i:02d}"
        img_p, voc_p = proj / f"{tag}.png", proj / f"{tag}.mp3"
        print(f"[{i}/{len(cfg['scenes'])}] {s.get('caption') or s['text'][:50]}")
        if not img_p.exists():
            if offline:
                placeholder_image(s.get("image_prompt", s["text"]), (1536, 1024)).save(img_p)
            else:
                kie.make_image(f"{s['image_prompt']}. Style: {style}", img_p,
                               size="2:3" if vertical else "3:2")
        if not voc_p.exists() and not offline:
            kie.make_voice(s["text"], voc_p, voice=cfg.get("voice", "Rachel"), speed=cfg.get("speed", 1.0))
        if voc_p.exists():
            audio, dur = voc_p, duration(voc_p) + 0.5
        else:
            dur = max(3.0, len(s["text"].split()) / 2.6 + 0.6)
            audio = work / f"{tag}_silent.wav"
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                 "-t", f"{dur:.2f}", str(audio)])
        sc = Scene(W, H, Image.open(img_p), s.get("caption", ""), dur, s.get("effect", "draw"), hand, tip)
        if preview:
            frames = [Image.fromarray(sc.frame(t * sc.dur)) for t in (.15, .35, .55, .95)]
            sheet = Image.new("RGB", (W * 2, H * 2))
            for k, fr in enumerate(frames):
                sheet.paste(fr, ((k % 2) * W, (k // 2) * H))
            sheet.resize((W, H)).save(proj / f"preview_{i:02d}.png")
            continue
        out = work / f"{tag}.mp4"
        render_scene(sc, audio, out, W, H)
        parts.append(out)
    if preview:
        print("Đã xuất preview_XX.png")
        return

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    body = work / "body.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(body)])

    music = proj / "music.mp3"
    if not music.exists() and not offline and cfg.get("music_style"):
        try:
            kie.make_music(cfg["music_style"], music)
        except Exception as e:  # nhạc nền không bắt buộc
            print("Bỏ qua nhạc nền:", e)
    name = cfg.get("output", "video_ve_tay")
    final = proj / f"{name}.mp4"
    if music.exists():
        D = duration(body)
        vol = cfg.get("music_volume", 0.12)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(body), "-stream_loop", "-1", "-i", str(music),
             "-filter_complex", f"[1:a]volume={vol},afade=t=in:d=1.5,afade=t=out:st={max(0, D - 2.5):.2f}:d=2.5[m];"
                                f"[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", f"{D:.3f}", str(final)])
    else:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(body), "-c", "copy", str(final)])
    email = proj / f"{name}_email.mp4"
    sw = "480:-2" if vertical else "854:-2"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-vf", f"scale={sw}", "-c:v", "libx264",
         "-crf", "30", "-preset", "slow", "-c:a", "aac", "-b:a", "64k", str(email)])
    print(f"\n✅ Xong: {final}  ({duration(final):.1f} giây)\n   Bản nén gửi email: {email}")


if __name__ == "__main__":
    main()
