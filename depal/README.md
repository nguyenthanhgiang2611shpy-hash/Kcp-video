# Máy DEPAL bao tự động – video cách hoạt động

Nguồn: bản vẽ **LA26-PTC-KCP-DEP-301026**, Phon-Tech, ngày 20/10/2026 (SCALE: FREE) – ảnh `ban_ve_LA26-PTC-KCP-DEP_20-10-2026.png`,
cập nhật theo trao đổi với Phon-Tech ngày 04/11/2026.

| File | Dùng cho |
|---|---|
| `Depal_cach_hoat_dong_v3.mp4` | **Bản mới nhất** – một file nén gửi email (960×540) |
| `Depal_cach_hoat_dong_v2.mp4` | Bản trước (giữ lại theo quy tắc giữ bản cũ) |
| `Depal_3D_minh_hoa.mp4` | **Minh họa 3D** (một file nén gửi email, ~2 phút 35 giây) – dựng bằng three.js trong `3d/` |
| `3d/scene.js`, `3d/render.js` | Script cảnh 3D; chạy `cd 3d && npm install && node render.js ../Depal_3D_minh_hoa.mp4` (thử khung: `node render.js out_dir test 12 60`) |
| `make_depal.py` | Script dựng v3 (Python/PIL + ffmpeg). `python3 make_depal.py test out.png` để xem khung mẫu |
| `Cau_hoi_Phon-Tech.md` | Danh sách câu hỏi và trả lời của Phon-Tech |

## Trình tự trong video v3 (13 cảnh, ~4 phút 14 giây)
1. Mở đầu
2. Tổng quan bố trí – 9 cụm, đánh số theo hành trình bao
3. Diện tích chiếm trong kho: khung chính ≈ 13,26 × 19,32 m ≈ 256 m² + dải băng ra xe ≈ 5,1 × 1,1 m ≈ 6 m² → **≈ 262 m²** (không tính lối đi xe nâng, chỗ đậu xe); điểm cao nhất hệ thống băng tải 1,5 m
4. Sling: 2.250 × 1.500 mm, 3 × 3 bao/lớp, 5 lớp = 45 bao = 2.250 kg
5. (1)(2) Luồng sling: xe nâng đặt 2 sling đầy bên trái → công nhân kiểm tra bao, bấm nút → sling 1 vào hút → sling rỗng sang chờ bên phải → sling 2 vào hút → cả 2 sling rỗng trả về bên trái → công nhân lấy ra. Bên phải làm giống hệt; lúc đó xe nâng nạp 2 sling mới bên trái
6. (3) Đầu hút chân không hút 1 hàng 3 bao nằm ngang (1,5 m), thả lần lượt từng bao lên băng tải – làm chậm, có bảng 5 bước
7. (4)–(7) Băng tải vệ sinh bao (chổi quét) → băng thẳng → băng cong 90° → băng tải ống lồng
8. (7)(8) Băng ống lồng vươn tối đa 18 m, tự rải bao trái → phải, 9 lớp, thụt 75 cm mỗi hàng; 680 bao = 34 tấn; không dùng người
9. Cảm biến (A) định vị thùng xe, (B) vị trí bao; 1 người ở phòng điều khiển; cảm biến sai → bấm dừng (giả định KCP)
10. (9) Trạm xả tay dự phòng: 1 công nhân, bao đi thẳng qua cell vào băng tải ra
11. Tóm tắt chức năng
12. Tóm tắt số liệu (11 mục)
13. Điểm còn cần chốt với Phon-Tech

## Phon-Tech xác nhận (04/11/2026)
- Xe nâng đưa sling đầy vào băng con lăn; mỗi bên 2 sling, chạy luân phiên như cảnh 5
- Sling đầy chỉ vào khi công nhân bấm nút; 4 công nhân bấm đưa sling vào và lấy sling rỗng ra
- Bao rách/lệch thì không hút được → công nhân làm bao ngay ngắn, tránh bao rách trước khi đưa vào
- Đầu hút chân không, 3 bao/lần
- Ô gạch chéo: sàn lưới cho công nhân đi lại thao tác
- Cụm vuông giữa cell và băng tải ra: băng tải vệ sinh bao, có chổi quét
- Băng tải ống lồng: vươn tối đa 18 m; chất cao tới cách trần xe 30 cm; rải được 5 bao trong thùng 235 cm; có cảm biến định vị thùng xe và vị trí bao
- Công suất máy hút: 40–45 tấn/giờ
- Trạm xả tay dự phòng: 1 người, bao đi thẳng qua cell vào băng tải ra (cùng trục)
- Điểm cao nhất của hệ thống băng tải: 1,5 m

## Số tính ra (ghi rõ trong video)
- 40–45 tấn/giờ = 800–900 bao/giờ; 1 sling 45 bao: 3,0–3,4 phút; 1 lần hút 3 bao: 12–13,5 giây; 1 xe 34 tấn: 45–51 phút
- Thùng 34T cao 215 cm → chất tối đa 185 cm; sơ đồ đang dùng 9 lớp = 117 cm
- Diện tích: đo trên bản vẽ (SCALE: FREE, 1 px ≈ 23,1 mm), là ước tính

## Còn chờ chốt / giả định
- Hút 3 bao, thả lần lượt từng bao: anh Giảng chốt với Phon-Tech sáng 05/11/2026
- Cảm biến sai → người phòng điều khiển bấm dừng: giả định của KCP; vị trí phòng điều khiển, xử lý sau khi dừng: chưa rõ
- Sàn xe cao thấp khác nhau: KCP kiểm tra rồi báo Phon-Tech
- Khung xanh có 4 tay xám ở cửa cell: chưa rõ là thiết bị gì
- Bao 130 hay 150 mm; vỏ sling nặng bao nhiêu; lưu lượng khí nén
- Kích thước chính thức phần trạm dự phòng và dải ra xe (video đang ước tính)
- Số bản vẽ 301026 / ngày 20/10/2026; báo giá theo bản vẽ mới
- Tốc độ băng tải trong video chỉ để minh họa

## Video 3D (Depal_3D_minh_hoa.mp4)
9 cảnh: tổng quan (9 cụm) · diện tích trong kho · luồng sling với xe nâng + nút bấm · hút 3 bao thả từng bao (chậm, bảng 5 bước) ·
băng vệ sinh → ra xe · băng ống lồng tự chất 680 bao · cảm biến (A)(B) + phòng điều khiển + bấm dừng · trạm dự phòng · tóm tắt.

Giả định chỉ có trong bản 3D (ghi trên hình): băng con lăn sling cao 0,45 m, băng nhận bao 0,9 m rồi lên 1,5 m;
sàn xe 1,3 m; robot là cánh tay 6 trục có đầu hút; phòng điều khiển đặt cạnh băng ống lồng; thùng xe đã bỏ bạt để nhìn vào trong.
