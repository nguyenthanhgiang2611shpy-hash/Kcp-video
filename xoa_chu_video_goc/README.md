# Video gốc đã xoá chữ và âm thanh

- `video_khong_chu_khong_tieng.mp4`: video máy xếp bao (bản Facebook) đã bỏ hết chữ chèn thêm và toàn bộ âm thanh. Kích thước 720×872, 30 fps, 16,2 giây.
- `clean_video.py`: script xử lý (`python3 clean_video.py <vao.mp4> <ra.mp4>`; cần `opencv-python-headless`).

Cách xử lý:
- Cắt bỏ dải trên (logo + banner tiêu đề vàng) và dải dưới (hình nhân vật hoạt hình), nên khung còn 720×872 thay vì 720×1280.
- Phụ đề vàng: dò theo màu, xoá rồi vá bằng màu nền và vân lấy ngay bên dưới.
- Số điện thoại chạy chéo: dò theo đường chạy và xoá.
- Bỏ toàn bộ âm thanh.

Vẫn còn: chữ in sẵn trên bao xi măng (là một phần của cảnh quay, không phải chữ chèn thêm). Chỗ có phụ đề trước đây hơi mờ.
