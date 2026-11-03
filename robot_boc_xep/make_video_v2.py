# -*- coding: utf-8 -*-
"""v2: chỉ dựng lại + dịch toàn bộ chữ gốc sang tiếng Việt (không thêm nội dung).
16:9 1280x720; hình gốc (đã cắt khung đen/phụ đề Anh) ở giữa, nền là chính hình đó làm mờ;
phụ đề tiếng Việt phía dưới; giữ nhạc nền gốc (nhỏ lại, nối mượt).
Lồng tiếng: đặt file voice/clipN.wav (nếu có) -> tự chèn và kéo dài cảnh cho vừa lời đọc.
Chạy:  python3 make_video_v2.py [test]
"""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src"); VOICE = os.path.join(HERE, "voice")
W, H, FPS = 1280, 720, 25
OUT = os.path.join(HERE, "Robot_boc_xep_bao_len_xe_v2.mp4")
INK = (29, 43, 58); WHITE = (255, 255, 255); YELLOW = (255, 214, 64)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}
def F(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]

# vùng hình thật trên clip gốc (x0, y0, x1, y1) và số giây bỏ ở đầu
CROP = {1: (0, 352, 716, 908), 2: (0, 0, 720, 900), 3: (0, 420, 716, 838),
        4: (0, 372, 716, 896), 5: (0, 262, 716, 990), 6: (0, 312, 716, 904)}
TRIM = {1: 1.3}

# Tên công ty (chữ Hoa trên mọi clip): 山东腾阳智能装备公司
COMPANY = "Công ty Thiết bị Thông minh Đằng Dương Sơn Đông"

# Thứ tự logic: vấn đề -> giải pháp -> tính năng -> câu kết.
# Mỗi clip: danh sách câu phụ đề (dịch sát phụ đề tiếng Anh gốc), hiện lần lượt.
SHOTS = [
    (3, ["Bạn đã quá mệt mỏi với việc bốc hàng lên xe thủ công, vừa chậm vừa tốn sức?",
         "Máy bốc xếp bao tự động sẽ xếp bao lên xe thật gọn gàng.",
         "Chạy liên tục, lại giảm rách, hỏng bao."]),
    (1, ["Robot xếp bao giúp giảm bớt sức lao động chân tay,",
         "lập trình chính xác nên hàng luôn được xếp ngay ngắn."]),
    (2, ["Tự động xếp hàng, nâng cao hiệu suất."]),
    (4, ["Cánh tay robot kết hợp quét LiDAR,",
         "tự nhận diện xe và tự tính đường xếp hàng."]),
    (5, ["Máy bốc xếp tự động thông minh,", "vận hành ổn định suốt 24 giờ."]),
    (6, ["Muốn làm tốt công việc, trước hết phải có công cụ tốt.",
         "Tự động hóa thông minh giúp năng suất tăng cao hơn nữa."]),
]

def read_clip(i):
    x0, y0, x1, y1 = CROP[i]; w, h = x1 - x0, y1 - y0
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(TRIM.get(i, 0)),
        "-i", os.path.join(SRC, f"clip{i}.mp4"), "-vf", f"fps={FPS},crop={w}:{h}:{x0}:{y0}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    n = len(raw) // (w * h * 3)
    return [Image.frombuffer("RGB", (w, h), raw[k*w*h*3:(k+1)*w*h*3]) for k in range(n)]

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", p]).decode())

def wrap(d, s, f, maxw):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + ([cur] if cur else [])

TOP, BOTTOM = 52, 592          # vùng hình
def compose(fr, line, alpha):
    bg = fr.resize((64, 36)).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
    fw, fh = fr.size; h = BOTTOM - TOP; w = int(fw * h / fh)
    bg.paste(fr.resize((w, h), Image.LANCZOS), ((W - w) // 2, TOP))
    d = ImageDraw.Draw(bg)
    f = F(FB, 22); t = COMPANY
    d.text(((W - d.textlength(t, font=f)) / 2, 14), t, font=f, fill=YELLOW)
    if line:
        f = F(FB, 34); lines = wrap(d, line, f, W - 120)
        y = 606 if len(lines) == 1 else 598
        for l in lines:
            x = (W - d.textlength(l, font=f)) / 2
            c = tuple(int(v * alpha) for v in WHITE)
            d.text((x, y), l, font=f, fill=c, stroke_width=3, stroke_fill=(0, 0, 0))
            y += 44 if len(lines) > 1 else 0
    return bg

def build():
    """Trả về [(frames, lines, start_times, seconds, voice_path)]"""
    out = []
    for ci, lines in SHOTS:
        fr = read_clip(ci); D = len(fr) / FPS
        vp = os.path.join(VOICE, f"clip{ci}.wav")
        if os.path.exists(vp):
            D = max(D, dur(vp) + 0.6)
            # thời điểm từng câu theo file voice/clipN.txt (giây bắt đầu mỗi câu) nếu có
            tp = vp.replace(".wav", ".txt")
            starts = [float(x) for x in open(tp).read().split()] if os.path.exists(tp) else None
        else:
            vp = None; starts = None
        if starts is None:  # chia đều theo độ dài câu
            tot = sum(len(l) for l in lines); acc = 0; starts = []
            for l in lines: starts.append(0.2 + (D - 0.4) * acc / tot); acc += len(l)
        out.append((fr, lines, starts, D, vp))
    return out

def frame_at(shot, t):
    fr, lines, starts, D, _ = shot
    # cảnh dài hơn clip -> chạy chậm lại cho vừa (không lặp)
    k = min(int(t / D * len(fr)), len(fr) - 1)
    j = max([n for n, s in enumerate(starts) if t >= s] or [-1])
    line = lines[j] if j >= 0 else None
    a = min(1.0, (t - starts[j]) / 0.25) if j >= 0 else 0
    return compose(fr[k], line, a)

def render(shots):
    tmpv = OUT + ".video.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20",
        "-preset", "medium", "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    XF = 6; prev = None
    for s in shots:
        n = int(round(s[3] * FPS))
        for k in range(n):
            im = frame_at(s, k / FPS)
            if prev is not None and k < XF: im = Image.blend(prev, im, (k + 1) / (XF + 1))
            p.stdin.write(im.tobytes())
        prev = frame_at(s, (n - 1) / FPS)
        print(s[0][0].size, round(s[3], 2), flush=True)
    p.stdin.close(); p.wait()
    # âm thanh: nhạc gốc từng clip (nhỏ lại, fade 2 đầu) + giọng đọc nếu có
    inputs, filt, t0 = [], [], 0.0
    for n, ((ci, _), s) in enumerate(zip(SHOTS, shots)):
        D = s[3]
        inputs += ["-ss", str(TRIM.get(ci, 0)), "-i", os.path.join(SRC, f"clip{ci}.mp4")]
        vol = 0.18 if s[4] else 0.6
        filt.append(f"[{len(inputs)//4}:a]atrim=0:{D},apad=whole_dur={D},volume={vol},"
                    f"afade=t=in:d=0.3,afade=t=out:st={D-0.4}:d=0.4,adelay={int(t0*1000)}:all=1[m{n}]")
        t0 += D
    na = len(SHOTS); labels = [f"[m{n}]" for n in range(na)]
    t0 = 0.0; vi = na + 1
    for n, s in enumerate(shots):
        if s[4]:
            inputs += ["-i", s[4]]
            filt.append(f"[{vi}:a]adelay={int((t0 + s[2][0]) * 1000)}:all=1,volume=1.0[v{n}]")
            labels.append(f"[v{n}]"); vi += 1
        t0 += s[3]
    filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,atrim=0:{t0}[a]")
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", tmpv] + inputs +
        ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", OUT])
    os.remove(tmpv); print("done", flush=True)

if __name__ == "__main__":
    shots = build()
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        ims = [frame_at(s, s[3] * f).resize((640, 360)) for s in shots for f in (0.15, 0.85)]
        sheet = Image.new("RGB", (1280, 360 * len(shots)))
        for k, im in enumerate(ims): sheet.paste(im, ((k % 2) * 640, (k // 2) * 360))
        sheet.save(sys.argv[2])
    else:
        render(shots)
