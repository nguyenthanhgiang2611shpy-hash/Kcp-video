# -*- coding: utf-8 -*-
"""Xoá chữ + âm thanh khỏi video gốc (máy xếp bao xi măng, 720x1280).
- Cắt bỏ dải trên (logo + banner vàng, y < 316) và dải dưới (hình nhân vật hoạt hình, y >= 1188)
- Phụ đề vàng (y 860–1080): dò theo màu vàng, inpaint rồi cộng chi tiết vân lấy ngay phía dưới
- Số điện thoại chạy chéo: dò theo mẫu + quỹ đạo thẳng rồi vá
- Bỏ toàn bộ âm thanh
Chạy: python3 clean_video.py <video_vao.mp4> <video_ra.mp4> [frame_so]
"""
import sys, subprocess
import cv2, numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
ONE = int(sys.argv[3]) if len(sys.argv) > 3 else None
Y0, Y1 = 316, 1188                         # vùng giữ lại
TPL_FRAME, TPL_BOX = 120, (122, 552, 292, 40)   # mẫu số điện thoại (x, y, w, h)

def phone_pred(i):
    return 122 + 0.667 * (i - TPL_FRAME), 552 + 1.573 * (i - TPL_FRAME)

def build_template():
    cap = cv2.VideoCapture(SRC)
    cap.set(cv2.CAP_PROP_POS_FRAMES, TPL_FRAME)
    ok, fr = cap.read()
    x, y, w, h = TPL_BOX
    return cv2.cvtColor(fr[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)

def sub_boxes(fr):
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
    yl = cv2.inRange(hsv, (22, 225, 225), (32, 255, 255))   # vàng phụ đề rất thuần
    yl[:850] = 0; yl[1090:] = 0
    # khung phụ đề có các dải vàng nằm ngang dài; lan can vàng chéo thì không
    o = cv2.morphologyEx(yl, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (150, 1)))
    o = cv2.morphologyEx(o, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 61)))
    n, _, st, _ = cv2.connectedComponentsWithStats(o)
    # mảnh vàng lớn (khung phụ đề, có thể bị số điện thoại cắt làm đôi)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(yl)
    big = np.isin(lab2, [j for j in range(1, n2) if st2[j][4] > 400])
    bx = []
    for x, y, w, h, ar in st[1:]:
        if ar < 1500: continue
        # nới theo chiều dọc để phủ hết phần khung bị số điện thoại đè/cắt
        y0, y1 = max(850, y - 45), min(1090, y + h + 45)
        ys = np.nonzero(big[y0:y1, x:x + w].any(1))[0]
        if len(ys):
            ny0, ny1 = min(y, y0 + ys.min()), max(y + h, y0 + ys.max() + 1)
            y, h = ny0, ny1 - ny0
        bx.append((int(x), int(y), int(w), int(h)))
    return sorted(bx, key=lambda b: b[1])

def patch_fill(fr, boxes, phone_m, pad=6):
    """Vá phụ đề + số điện thoại trong một lần inpaint (tránh màu vàng loang ra),
    rồi cộng thêm chi tiết vân lấy ngay phía dưới vào chỗ phụ đề."""
    H, W = fr.shape[:2]
    m = phone_m.copy()
    for x, y, w, h in boxes:
        cv2.rectangle(m, (x - pad, y - pad), (x + w + pad, y + h + pad), 255, -1)
    a, b = Y0 - 20, min(H, Y1 + 20)
    out = fr.copy()
    if m[a:b].any():
        out[a:b] = cv2.inpaint(fr[a:b], m[a:b], 7, cv2.INPAINT_TELEA)
    if not boxes: return out
    bot = max(y + h for _, y, _, h in boxes) + pad + 10   # vân lấy từ phía dưới mọi phụ đề (bao + thành xe)
    for x, y, w, h in boxes:
        x0, y0 = max(0, x - pad - 8), max(0, y - pad - 8)
        x1, y1 = min(W, x + w + pad + 8), min(H, y + h + pad + 8)
        hh = y1 - y0
        sy = bot
        if sy + hh > H: continue
        src = out[sy:sy + hh, x0:x1].astype(np.float32)
        detail = src - cv2.GaussianBlur(src, (0, 0), 6)
        bm = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.rectangle(bm, (x - pad - x0, y - pad - y0), (x + w + pad - x0, y + h + pad - y0), 255, -1)
        al = (bm > 0).astype(np.float32)
        al = cv2.GaussianBlur(al, (0, 0), 3)[..., None]
        base = out[y0:y1, x0:x1].astype(np.float32)
        out[y0:y1, x0:x1] = np.clip(base + detail * al * 0.7, 0, 255).astype(np.uint8)
    return out

def mask_for(fr, i, tpl):
    H, W = fr.shape[:2]
    m = np.zeros((H, W), np.uint8)
    # số điện thoại
    px, py = phone_pred(i)
    tw, th = TPL_BOX[2], TPL_BOX[3]
    sx0, sy0 = int(max(0, px - 15)), int(max(0, py - 15))
    sx1, sy1 = int(min(W, px + tw + 15)), int(min(H, py + th + 15))
    bx, by = int(px), int(py)
    if sx1 - sx0 >= tw and sy1 - sy0 >= th:
        g = cv2.cvtColor(fr[sy0:sy1, sx0:sx1], cv2.COLOR_BGR2GRAY)
        r = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(r)
        if mx > 0.35:
            bx, by = sx0 + loc[0], sy0 + loc[1]
    cv2.rectangle(m, (bx - 4, by - 2), (bx + tw + 4, by + th + 2), 255, -1)
    return m

def clean(fr, i, tpl):
    boxes = sub_boxes(fr)
    fr = patch_fill(fr, boxes, mask_for(fr, i, tpl))
    return fr[Y0:Y1]

def main():
    tpl = build_template()
    cap = cv2.VideoCapture(SRC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if ONE is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, ONE)
        ok, fr = cap.read()
        cv2.imwrite(OUT, clean(fr, ONE, tpl)); return
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                          "-s", f"{W}x{Y1 - Y0}", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
                          "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        p.stdin.write(clean(fr, i, tpl).tobytes()); i += 1
    p.stdin.close(); p.wait()
    print("done", i, "frames ->", OUT)

if __name__ == "__main__":
    main()
