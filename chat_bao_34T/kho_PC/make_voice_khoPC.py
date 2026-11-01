# -*- coding: utf-8 -*-
"""Video kho PC có giọng đọc (eSpeak NG, tiếng Việt).
Đọc đều ở một tốc độ; cảnh nào ngắn hơn lời đọc thì kéo dài cảnh đó, rồi dựng lại hình và ghép tiếng.
Chạy: python3 make_voice_khoPC.py [giọng: vi | vi-vn-x-south | vi-vn-x-central] [tốc độ, mặc định 150]
Cần: espeak-ng, ffmpeg, make_video_khoPC_v2.py
"""
import os, sys, subprocess, json, tempfile, importlib.util
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = sys.argv[1] if len(sys.argv) > 1 else "vi-vn-x-south"
SPEED = int(sys.argv[2]) if len(sys.argv) > 2 else 150
OUT = os.path.join(HERE, "Chat_xa_34T_kho_PC_v3_giong_doc.mp4")
spec = importlib.util.spec_from_file_location("mv", os.path.join(HERE, "make_video_khoPC_v2.py"))
m = importlib.util.module_from_spec(spec); sys.modules["mv"] = m; spec.loader.exec_module(m)

def render_frame(i):
    return m.render(i)

# (giây bắt đầu cảnh, thời lượng cảnh, lời đọc viết bằng chữ để máy đọc đúng số)
LINES = [
    (0.0, 4.0, "Cách chất sáu trăm tám mươi bao đường vào xe công te nơ bạt."),
    (4.0, 5.0, "Thùng xe dài mười hai mét hai mươi sáu. Chất từ trong đầu thùng ra cửa sau."),
    (9.0, 5.5, "Mỗi bao đường nặng năm mươi ký, dài bảy mươi lăm phân, bề ngang năm mươi phân."),
    (14.5, 13.0, "Thùng chỉ rộng hai mét ba mươi lăm. Kho pê xê đặt bao một, ba, năm trước, sát hai bên thành và ở giữa. "
                 "Còn lại hai khe, ép bao hai và bốn vào. Năm bao vừa khít lòng thùng."),
    (27.5, 5.0, "Lớp một đặt sát vách đầu thùng. Một, ba, năm, rồi hai, bốn."),
    (32.5, 16.0, "Lớp nào cũng làm giống vậy. Một, ba, năm trước, hai, bốn sau. "
                 "Chồng thẳng lên đủ chín lớp, được bốn mươi lăm bao, cao một mét mười bảy, rồi mới sang hàng mới."),
    (48.5, 12.0, "Xong một hàng thì lùi ra bảy mươi lăm phân, làm hàng tiếp theo. Từ hàng một đến hàng tám, mỗi hàng đều chín lớp."),
    (60.5, 8.0, "Kiểm tra. Tám hàng đầu, mỗi hàng chín lớp, bốn mươi lăm bao. Tổng ba trăm sáu mươi bao."),
    (68.5, 12.0, "Từ hàng chín đến hàng mười sáu, chỉ chất tám lớp, mỗi hàng bốn mươi bao, cao một mét lẻ bốn. "
                 "Cuối thùng còn trống hai mươi sáu phân."),
    (80.5, 9.0, "Kiểm tra. Tám hàng sau, mỗi hàng tám lớp, thấp hơn hàng trước một lớp. Tổng ba trăm hai mươi bao."),
    (89.5, 15.0, "Đi lại từ đầu xe ra cuối xe. Tám hàng chín lớp, tám hàng tám lớp. "
                 "Tám nhân bốn mươi lăm, cộng tám nhân bốn mươi, đúng sáu trăm tám mươi bao, ba mươi tư tấn."),
    (104.5, 10.0, "Sáu trăm tám mươi bao bằng ba mươi tư tấn. Tám hàng bốn mươi lăm bao và tám hàng bốn mươi bao. "
                  "Cao một mét mười bảy. Trống hai mươi sáu phân."),
    (114.5, 6.5, "Một, ba, năm trước. Hai, bốn sau. Đủ lớp mới lùi. Làm đúng cho mọi xe."),
]
LEAD = 0.4           # đọc sau khi cảnh bắt đầu
TAIL = 0.8           # nghỉ sau câu đọc trước khi sang cảnh

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

def tts(text, path):
    subprocess.run(["espeak-ng", "-v", VOICE, "-s", str(SPEED), "-p", "45", "-g", "5", "-w", path, text], check=True)

def main():
    assert len(LINES) == len(m.SCENES)
    tmp = tempfile.mkdtemp(prefix="voice_")
    wavs, new_scenes, starts, acc = [], [], [], 0.0
    for i, ((_, D, text), (name, D0, fn)) in enumerate(zip(LINES, m.SCENES)):
        p = os.path.join(tmp, f"{i:02d}.wav"); tts(text, p)
        dd = dur(p)
        nd = round(max(D0, dd + LEAD + TAIL) * m.FPS) / m.FPS
        print(f"{i + 1:2d} {name:8s} cảnh {D0:5.1f}s -> {nd:5.1f}s  giọng {dd:4.1f}s")
        new_scenes.append((name, nd, fn)); wavs.append(p); starts.append(acc + LEAD); acc += nd
    m.SCENES[:] = new_scenes
    print(f"tổng {acc:.1f}s")
    # dựng hình mới, ghép tiếng
    inputs, filt = [], []
    for j, (st, p) in enumerate(zip(starts, wavs)):
        inputs += ["-i", p]; ms = int(st * 1000)
        filt.append(f"[{j + 1}:a]adelay={ms}|{ms},aresample=44100[a{j}]")
    filt.append("".join(f"[a{j}]" for j in range(len(wavs))) +
                f"amix=inputs={len(wavs)}:normalize=0,highpass=f=90,lowpass=f=7000,loudnorm=I=-16:TP=-1.5:LRA=11,apad[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{m.W}x{m.H}",
           "-r", str(m.FPS), "-i", "-"] + inputs + [
           "-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aout]",
           "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ac", "1",
           "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = m.total_frames()
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(render_frame, range(n), chunksize=8)):
            proc.stdin.write(b)
            if k % 300 == 0: print(f"{k}/{n}", flush=True)
    proc.stdin.close(); proc.wait()
    print("done", OUT, flush=True)

if __name__ == "__main__":
    main()
