# Robot bốc xếp bao lên xe – video trình chiếu (v1)

Ngày 03/11/2026. Ghép 6 clip gốc (khổ dọc, phụ đề tiếng Anh) thành 1 video ngang 16:9, chú thích tiếng Việt.

| File | Dùng cho |
|---|---|
| `Robot_boc_xep_bao_len_xe_v1.mp4` | Bản chiếu họp (1280×720, 67 giây, ~9,9 MB) |
| `Robot_boc_xep_bao_len_xe_v1_email.mp4` | Bản nén gửi email/Zalo (960×540, ~2,1 MB) |
| `make_video.py` | Script dựng lại (Python/PIL + ffmpeg) |
| `src/clip1–6.mp4` | Clip gốc |

## Trình tự
1. Mở đầu: "Xếp bao lên xe không cần người bốc vác?" + 4 chương
2. 01 · Thay bốc vác – clip 3, clip 1
3. 02 · Xếp lên xe – clip 2, clip 6
4. 03 · Tự nhận diện xe (LiDAR) – clip 4
5. 04 · Chạy 24/24 – clip 5
6. Tóm tắt 4 ô
7. Chốt: 3 câu hỏi cần làm rõ cho KCP

## Ghi chú
- Đã cắt bỏ khung đen, chữ Hoa và phụ đề tiếng Anh của clip gốc; bỏ 1,3 giây đầu clip 1.
- Video không tiếng (bỏ âm thanh gốc) để người trình bày thuyết minh.
- Nội dung theo giới thiệu của nhà sản xuất (Shandong Tengyang), chưa kiểm chứng tại KCP.

---
# Video 3D: Robot gắp bao chất lên xe (v1)

| File | Dùng cho |
|---|---|
| `Robot_gap_bao_3D_v1.mp4` | Bản chiếu (1280×720, 52 giây, ~11,8 MB), chưa có lời |
| `Robot_gap_bao_3D_v1_email.mp4` | Bản nén (~2,5 MB) |
| `3d/scene.js`, `3d/render.js` | Dựng lại: `cd 3d && npm install && node render.js ../Robot_gap_bao_3D_v1.mp4` |

Theo clip 4: robot 4 trục chạy trên ray dọc xe, băng tải song song; gắp từng bao, xoay 90°, đặt nằm ngang thùng.
Xe container bạt 12,26 × 2,35 m, mở mui bạt; bao 50 kg 75 × 50 × 13 cm. Số bao/lớp chỉ để minh họa.
6 bước: xe vào · mở bạt + quét LiDAR · gắp bao · xếp từ đầu thùng · xếp dần ra cửa sau (tua nhanh) · xe đầy, đóng bạt.
