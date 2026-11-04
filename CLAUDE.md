# Hướng dẫn cho Claude – repo Kcp-video

## Xuất video
- Mỗi lần làm video chỉ xuất **MỘT file duy nhất, nén sẵn để gửi email** (khoảng 960×540, H.264 CRF ~30, `-movflags +faststart`, mục tiêu dưới ~2–3 MB).
- **Không** tạo thêm bản chất lượng cao riêng; không tạo 2 video (bản gốc + bản email) như trước.
- Render thẳng ra file email trong một lần (scale ngay trong lệnh ffmpeg), không giữ file trung gian trong repo.
- Kiểm tra file bằng ffprobe (thời lượng, kích thước) trước khi gửi.

(Yêu cầu của anh Giảng, Phòng Logistics KCP, ngày 04/11/2026.)
