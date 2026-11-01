# -*- coding: utf-8 -*-
"""Gọi API kie.ai: tạo ảnh (GPT-4o Image), giọng đọc (ElevenLabs TTS), nhạc nền (Suno).

API key đọc từ file .env (KIE_API_KEY=...) ở thư mục gốc dự án hoặc biến môi trường.
Lưu ý: đường dẫn API lấy theo tài liệu docs.kie.ai (11/2026). Nếu kie.ai đổi API,
chỉ cần sửa phần ENDPOINTS bên dưới.
"""
import json, os, re, sys, time
from pathlib import Path
import requests

BASE = "https://api.kie.ai"
ENDPOINTS = {
    "image_create": "/api/v1/gpt4o-image/generate",
    "image_status": "/api/v1/gpt4o-image/record-info",
    "job_create":   "/api/v1/jobs/createTask",      # ElevenLabs TTS và các model "market"
    "job_status":   "/api/v1/jobs/recordInfo",
    "music_create": "/api/v1/generate",              # Suno
    "music_status": "/api/v1/generate/record-info",
}
TTS_MODEL = "elevenlabs/text-to-speech-multilingual-v2"   # đọc được tiếng Việt
DUMMY_CALLBACK = "https://example.com/kie-callback"         # một số API bắt buộc có callBackUrl


def load_key():
    if os.environ.get("KIE_API_KEY"):
        return os.environ["KIE_API_KEY"].strip()
    for d in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[4]]:
        f = d / ".env"
        if f.is_file():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("KIE_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and not v.startswith("dan_"):
                        return v
    return None


def _headers():
    key = load_key()
    if not key:
        sys.exit("Chưa có KIE_API_KEY trong file .env")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _post(path, body):
    r = requests.post(BASE + path, headers=_headers(), json=body, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("code") not in (200, None):
        raise RuntimeError(f"kie.ai lỗi {j.get('code')}: {j.get('msg')}")
    data = j.get("data") or {}
    tid = data.get("taskId") or data.get("task_id")
    if not tid:
        raise RuntimeError(f"Không nhận được taskId: {j}")
    return tid


MEDIA_RE = re.compile(r"https?://[^\s\"'\\]+?\.(?:png|jpe?g|webp|mp3|wav|m4a|ogg)(?:\?[^\s\"'\\]*)?", re.I)


def _find_urls(obj):
    """Tìm mọi link ảnh/âm thanh trong JSON trả về (kể cả JSON lồng dạng chuỗi)."""
    s = json.dumps(obj, ensure_ascii=False)
    s = s.replace("\\/", "/").replace('\\"', '"')
    return list(dict.fromkeys(MEDIA_RE.findall(s)))


def _status_text(data):
    for k in ("state", "status", "successFlag"):
        if k in data:
            return str(data[k]).lower()
    return ""


def _poll(path, tid, timeout=600, every=5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(BASE + path, headers=_headers(), params={"taskId": tid}, timeout=60)
        r.raise_for_status()
        data = (r.json() or {}).get("data") or {}
        st = _status_text(data)
        if any(x in st for x in ("fail", "error")) or st in ("2", "3"):
            raise RuntimeError(f"Tác vụ {tid} thất bại: {data.get('errorMessage') or data.get('failMsg') or data}")
        urls = _find_urls(data)
        done = st in ("success", "1", "succeeded", "completed") or st.startswith("success") \
            or (st in ("first_success", "text_success") and urls)
        if done and urls:
            return urls
        time.sleep(every)
    raise TimeoutError(f"Quá thời gian chờ tác vụ {tid}")


def _download(url, out):
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    Path(out).write_bytes(r.content)
    return out


def make_image(prompt, out, size="3:2"):
    tid = _post(ENDPOINTS["image_create"], {"prompt": prompt, "size": size, "nVariants": 1})
    urls = [u for u in _poll(ENDPOINTS["image_status"], tid) if re.search(r"\.(png|jpe?g|webp)", u, re.I)]
    return _download(urls[0], out)


def make_voice(text, out, voice="Rachel", speed=1.0):
    tid = _post(ENDPOINTS["job_create"], {"model": TTS_MODEL, "input": {
        "text": text, "voice": voice, "stability": 0.5, "similarity_boost": 0.75, "speed": speed}})
    urls = [u for u in _poll(ENDPOINTS["job_status"], tid, every=3) if re.search(r"\.(mp3|wav|m4a|ogg)", u, re.I)]
    return _download(urls[0], out)


def make_music(style, out):
    tid = _post(ENDPOINTS["music_create"], {"prompt": style, "customMode": False, "instrumental": True,
                                            "model": "V4_5", "callBackUrl": DUMMY_CALLBACK})
    urls = [u for u in _poll(ENDPOINTS["music_status"], tid, timeout=900, every=10) if re.search(r"\.(mp3|wav|m4a)", u, re.I)]
    return _download(urls[0], out)


if __name__ == "__main__":
    # Kiểm tra nhanh key: python3 kie_client.py check
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        print("Đã có API key" if load_key() else "CHƯA có API key trong .env")
