---
name: video-ve-tay
description: Tạo video dạng vẽ tay (whiteboard animation) tiếng Việt từ một chủ đề - tự viết kịch bản, tạo ảnh AI (kie.ai GPT-4o Image), giọng đọc (ElevenLabs qua kie.ai), nhạc nền (Suno), vẽ dần bằng bàn tay cầm cọ và xuất MP4 + bản nén gửi email. Dùng khi người dùng nói "làm video vẽ tay", "video whiteboard", "video giải thích kiểu vẽ tay", "video người que", "video tranh Đông Hồ".
---

# Skill: Video vẽ tay (KCP)

Người dùng chỉ cần đưa **chủ đề**. Claude làm phần còn lại, rồi để người dùng xem và yêu cầu sửa.

## Quy trình

1. **Hỏi lại nếu thiếu** (hỏi gộp một lần, có gợi ý mặc định):
   - Chủ đề / nội dung chính, người xem là ai (tài xế, khách hàng, nhân viên mới…)
   - Độ dài (mặc định 45–60 giây ≈ 6–8 cảnh), khổ `16:9` (mặc định) hay `9:16` (Facebook Reels/TikTok)
   - Phong cách: `ve-tay` (mặc định), `nguoi-que`, `dong-ho`, `ky-thuat` – hoặc một mô tả tự do bằng tiếng Anh
   - Số liệu thật (giá, tấn, km…) – **không tự bịa số liệu của KCP**; số liệu chung thì ghi nguồn.
2. **Viết kịch bản** thành `video_ve_tay/<ten-video>/script.json`:
   - Cảnh 1 là câu mở đầu gây tò mò (hook). Cảnh cuối chốt ý / kêu gọi hành động.
   - Mỗi cảnh 1–2 câu (12–30 từ), văn nói tự nhiên, câu ngắn.
   - `caption`: chữ ngắn (≤ 40 ký tự) hiện dưới hình – từ khoá hoặc con số chính.
   - `image_prompt`: **tiếng Anh**, mô tả MỘT hình đơn giản, ít chi tiết, không có chữ trong ảnh.
   - `effect`: `draw` (vẽ dần – mặc định), `drop` (hình rơi xuống nảy nhẹ, dùng cho vật nặng/con số bất ngờ), `zoom` (vẽ xong rồi zoom chậm). Xen kẽ, đa số là `draw`.
   - Cho người dùng xem kịch bản (bảng ngắn) trước khi tạo ảnh/giọng nếu video > 60 giây.
3. **Kiểm tra API key**: `python3 .claude/skills/video-ve-tay/scripts/kie_client.py check`.
   Nếu chưa có key → hướng dẫn theo `HUONG_DAN_KIE_AI.md` ở thư mục gốc, hoặc chạy `--offline` để xem thử.
4. **Xem trước nhanh** (không tốn tiền nếu ảnh đã có): `python3 .claude/skills/video-ve-tay/scripts/make_video.py video_ve_tay/<ten-video> --preview`, mở `preview_XX.png` để soát.
5. **Dựng video**: `python3 .claude/skills/video-ve-tay/scripts/make_video.py video_ve_tay/<ten-video>`.
   Ra `<output>.mp4` (bản chuẩn) và `<output>_email.mp4` (bản nén). Gửi file cho người dùng.
6. **Sửa theo góp ý**: muốn đổi ảnh/giọng cảnh nào thì sửa `script.json`, xoá `scene_XX.png` hoặc `scene_XX.mp3` của cảnh đó rồi chạy lại – các cảnh khác giữ nguyên, không tốn thêm tiền.
7. Commit thư mục video (script.json, ảnh, mp3, mp4) lên nhánh đang làm.

## Mẫu script.json

```json
{
  "title": "Vì sao cước vận chuyển thay đổi theo giá dầu",
  "aspect": "16:9",
  "style": "ve-tay",
  "voice": "Rachel",
  "speed": 1.0,
  "music_style": "calm light acoustic background music for explainer video",
  "music_volume": 0.12,
  "output": "cuoc_van_chuyen_gia_dau",
  "scenes": [
    {"text": "Cùng một chuyến xe, vì sao tháng này cước lại cao hơn tháng trước?",
     "caption": "Cước tăng – vì đâu?",
     "image_prompt": "a cargo truck on a road with a question mark above it",
     "effect": "draw"}
  ]
}
```

## Ghi chú kỹ thuật
- Ảnh: `scene_XX.png`, giọng: `scene_XX.mp3`, nhạc: `music.mp3` (có thể tự đặt file nhạc của mình vào).
- Có thể dùng ảnh tự chụp/tự vẽ: đặt sẵn `scene_XX.png` – skill sẽ dùng thay vì tạo ảnh AI.
- Giọng đọc mặc định ElevenLabs `Rachel` (đa ngôn ngữ). Muốn giọng khác: đổi `voice` (xem danh sách trên kie.ai).
- Đường dẫn API kie.ai nằm ở `ENDPOINTS` trong `scripts/kie_client.py`. Lần chạy thật đầu tiên nếu lỗi 404/422 → đối chiếu docs.kie.ai và sửa ở đó.
- Không bao giờ in API key ra màn hình hay commit file `.env`.
- Chi phí tham khảo: 1 video 1 phút (8 ảnh + giọng + nhạc) khoảng 0,3–0,8 USD trên kie.ai (kiểm tra bảng giá thực tế).
