# Motion graphic – Chất xá 34 tấn vào xe container bạt (kho PC)

Dựng lại từ video `Chat_xa_34T_kho_PC_v3_giong_doc_email.mp4`: giữ nguyên 13 cảnh, số liệu và **giọng đọc gốc**, chuyển sang phong cách motion graphic.

| File | Dùng cho |
|---|---|
| `Chat_xa_34T_kho_PC_motion.mp4` | Bản chính 1280×720, 143 giây (~18 MB) |
| `Chat_xa_34T_kho_PC_motion_email.mp4` | Bản nén 960×540 (~3,3 MB) |
| `make_video_motion.py` | Script dựng (Python/PIL + ffmpeg) |

## Hiệu ứng thêm so với bản cũ
- Chuyển cảnh quét chéo (vệt cam + xanh đậm) thay cho mờ chồng
- Tiêu đề, phụ đề hiện từng từ, trượt lên; số, thẻ, huy hiệu số bao bật có độ nảy
- Bao rơi xuống có nảy nhẹ; bao 2, 4 "ép" co lại vào khe
- Camera trôi nhẹ liên tục, nền chấm lưới chuyển động
- Đếm số chạy (50 kg, 680 bao, số lớp, số hàng), dấu mộc rung khi đóng

## Dựng lại
```
python3 make_video_motion.py full <video_hoac_wav_giong_doc> Chat_xa_34T_kho_PC_motion.mp4
```
Mốc cảnh (`BOUNDS`) đã khớp theo giọng đọc của bản v3.
