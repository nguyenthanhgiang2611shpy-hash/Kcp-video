# Máy DEPAL bao tự động – video cách hoạt động

Nguồn: bản vẽ **LA26-PTC-KCP-DEP-301026**, Phon-Tech, ngày 20/10/2026 (SCALE: FREE) – ảnh `ban_ve_LA26-PTC-KCP-DEP_20-10-2026.png`.

| File | Dùng cho |
|---|---|
| `Depal_cach_hoat_dong_v2.mp4` | **Bản mới nhất** – một file nén gửi email (960×540): băng ống lồng tự chất lên xe, không dùng người |
| `make_depal.py` | Script v2 dựng lại (Python/PIL + ffmpeg). `python3 make_depal.py test out.png` để xem khung mẫu |

## Trình tự trong video (11 cảnh)
1. Mở đầu
2. Tổng quan bố trí – 8 cụm, đánh số theo hành trình bao
3. Sling: 2.250 × 1.500 mm, 3 × 3 bao/lớp, 5 lớp = 45 bao = 2.250 kg
4. (1)(2) Sling vào từ hai bên, luân phiên
5. (3) Robot gắp từng bao, đặt lên băng ra; sling rỗng → chưa rõ đi đâu
6. (4)(5)(6) Băng tải thẳng → băng cong 90° → băng tải ống lồng vào xe
7. (6)(7) Băng tải ống lồng vươn hết cỡ vào sát đầu thùng, tự rải bao trái → phải, hết lớp mới lên lớp, đủ 9 lớp = 45 bao thì thụt lại 75 cm; 14 hàng × 45 + 2 hàng × 25 = 680 bao = 34 tấn; không dùng người
8. (8) Trạm xả tay dự phòng khi robot dừng
9. Tóm tắt chức năng
10. Tóm tắt số liệu (10 mục)
11. Điểm cần Phon-Tech xác nhận

## Đã chốt với Phòng Logistics
- Thùng xe (04/11/2026, Phon-Tech xác nhận): băng tải ống lồng vươn ra/thụt vào, tự rải bao, chất 9 lớp, không dùng người
- Sơ đồ chất xe: theo Trình tự chất bao xe 34T v2 (KCP); rải hết lớp mới lên lớp
- Công nhân khu depal: giữ nguyên theo bản vẽ
- Sling vào từ hai bên, luân phiên
- Băng tải phía dưới + lưới 3×3 + 1 công nhân = trạm xả tay dự phòng

## Ghi "chưa rõ" / suy luận trong video
- Sling rỗng đưa đi đâu: chưa rõ
- Phương tiện đưa sling đầy vào đầu băng con lăn: chưa rõ
- Robot gắp 1 bao/lần: suy từ đường đi bao vẽ trên bản vẽ (To be confirm)
- Đường bao từ trạm dự phòng qua cell ra băng (4): bản vẽ chưa thể hiện rõ
- Chiều dày bao: bản vẽ 150 mm, KCP đo 130 mm (Trình tự chất bao xe 34T v2) → chiều cao 5 lớp 750 / 650 mm
- "Sling + hàng = 2.250 kg" trên bản vẽ, trong khi 45 × 50 kg = 2.250 kg chưa tính vỏ sling
- Công suất (bao/giờ), lưu lượng khí nén: chưa có trong bản vẽ
- Tốc độ băng tải, nhịp robot trong video chỉ để minh họa
- Số bản vẽ ghi 301026 nhưng ngày vẽ 20/10/2026 và tên file 201026 – cần Phon-Tech xác nhận

Từ 04/11/2026: script chỉ xuất **một** video nén sẵn để gửi email (xem `CLAUDE.md` ở gốc repo).
