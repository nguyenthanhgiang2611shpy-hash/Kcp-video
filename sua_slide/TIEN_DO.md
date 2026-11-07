# Tiến độ sửa slide – Quy trình xuất một xe đường tại cầu cân

- File gốc: `Quy_trinh_xuat_mot_xe_duong_tai_cau_can_NHO.pptx` (42 slide)
- Số slide tính theo **bản gốc 42 slide**. Riêng khi người dùng nói "trang N" theo số in ở góc slide thì đối chiếu lại (ví dụ "trang 10" = slide gốc 33).
- Cách làm:
  - Người dùng gọi trang nào thì chỉ sửa đúng trang đó, chỉ gửi đúng trang đó.
  - Người dùng nói "ok" thì lưu riêng **một trang đó** thành file `Trang_<số>_....pptx` (file chỉ có 1 trang).
  - Mỗi lần sửa xong: đưa bản xem trước hiện thẳng trong khung chat (ảnh / ảnh động GIF), không chỉ gửi file hay link.
  - **Không** ráp cả bộ, **không** gửi cả bộ slide, trừ khi người dùng yêu cầu ráp.
- Lưu 1 trang: `python3 sua_slide/rap_file.py <file_goc.pptx> <file_ra.pptx> <số slide gốc>`
- Ráp cả bộ (chỉ khi được yêu cầu): `python3 sua_slide/rap_file.py <file_goc.pptx> <file_ra.pptx>`

| Slide gốc | Nội dung sửa | Trạng thái | File 1 trang |
|---|---|---|---|
| 3 | Bỏ hẳn trang 3 (sơ đồ tổng quan) khỏi bộ slide cuối cùng | OK – bỏ | (không có) |
| 5 | Giấy tờ hiện chậm (chậm 3 lần), mỗi giấy tờ dừng 2 giây; đủ hết thì đứng yên, không lặp lại (~27 giây) | OK | `Trang_05_giay_to.pptx` |
| 6–14 | Gộp 9 bước đăng ký xe thành 1 trang; video chậm 2 lần, dừng ~4 giây mỗi bước (~1 phút 50 giây) | OK | `Trang_06-14_dang_ky_xe.pptx` |
| 15–24 | Gộp 10 bước đăng ký tài xế thành 1 trang; cùng tốc độ chậm (~2 phút) | OK | `Trang_15-24_dang_ky_tai_xe.pptx` |
| 26–32 | Gộp 7 bước Loading Request thành 1 trang; video chậm 2 lần, dừng ~4 giây mỗi bước (~1 phút 31 giây) | OK | `Trang_26-32_loading_request.pptx` |
| 33 (số in "10") | Thêm 2 người giám sát: bảo vệ đi từ đuôi xe tới, NV cầu cân đi từ đầu xe tới; giữ chạy lặp như gốc | OK | `Trang_33_kiem_tra_xe.pptx` |
| 2 | Tiêu đề "Quy trình xuất một xe đường tại cầu cân", bỏ dòng "Video không có tiếng…"; video rút gọn còn 4 đoạn minh họa cho 4 giai đoạn (xe đến bãi đậu · vào kho bốc hàng · cân xe ra · đủ bộ chứng từ), chậm 3 lần, dừng 5 giây, ~1 phút 6 giây; khoanh đỏ giai đoạn đang nói, giữ tới cuối; chạy 1 lần rồi dừng | OK | `Trang_02_toan_bo_quy_trinh.pptx` |
| 1 | Video vẽ tay dựng lại với cây bút nhỏ (~45% cỡ cũ), bỏ đoạn lật trang; ảnh chờ là khung đã vẽ xong nên không bị trống; chạy 1 lần ~17 giây | OK | (trong bản FINAL) |
| 39 (số in "15") | Dòng 2 chỉ ghi "Kho và Process kiểm tra và xác nhận."; nhãn trong video đổi thành "Kho xác nhận", "Process xác nhận"; ghi chú cập nhật | OK | (trong bản FINAL) |

| 40 (số in "16") | 4 bước làm DC: (1) Mở Sales Order and Despatch → Delivery Challan, bấm New; (2) Double click vào ô Truck No, chọn đúng xe cần làm DC; (3) Nhập số seal From Seal No và To Seal No; (4) Bấm Save, rồi in (Print). Bỏ ví dụ LR | OK | (trong bản FINAL) |

| 6–14 (trang 5 final) – sửa bước 4 | Loại xe: danh sách Trailer / Normal Truck, xe ví dụ chọn Normal Truck; dòng giải thích "Container bạt chọn Trailer · 4 chân trở xuống chọn Normal Truck"; ghi chú: chọn Trailer thì nhập thêm Rơ moóc | OK | `Trang_06-14_dang_ky_xe.pptx` |

## Bản FINAL
- File: `Quy_trinh_xuat_xe_duong_tai_cau_can_FINAL.pptx` (18 trang, ~7,5 MB, gửi email được, có lời thuyết trình trong ghi chú).
- Cách tạo:
  1. `python3 sua_slide/rap_file.py <file_goc.pptx> full_raw.pptx`
  2. `python3 sua_slide/hoan_thien.py full_raw.pptx Quy_trinh_xuat_xe_duong_tai_cau_can_FINAL.pptx <thư mục phông Nunito>`
- Lời thuyết trình: `tai_lieu/loi_thuyet_trinh.json` → file Word `tai_lieu/Loi_thuyet_trinh.docx` (node tai_lieu/tao_loi_thuyet_trinh.js) và ghi vào đầu ghi chú từng trang (python3 sua_slide/them_loi_vao_ghi_chu.py), chạy sau `hoan_thien.py`.
- `hoan_thien.py`: đánh lại số trang 03–18 (do bỏ trang 3), đổi "(trang 6)/(trang 7)" thành "(trang 5)/(trang 6)" trong video và ghi chú trang giấy tờ, nén video (H.264, 1280 px) và ảnh.
- Phông Nunito lấy từ gói npm `@fontsource/nunito`, gộp các bộ latin + latin-ext + vietnamese bằng fontTools.
