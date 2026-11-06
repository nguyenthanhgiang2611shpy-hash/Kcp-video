# Tiến độ sửa slide – Quy trình xuất một xe đường tại cầu cân

- File gốc: `Quy_trinh_xuat_mot_xe_duong_tai_cau_can_NHO.pptx` (42 slide)
- Số slide luôn tính theo **bản gốc 42 slide**.
- Cách làm:
  - Người dùng gọi trang nào thì chỉ sửa đúng trang đó, chỉ gửi đúng trang đó.
  - Người dùng nói "ok" thì lưu riêng **một trang đó** thành file `Trang_<số>_....pptx` (file chỉ có 1 trang).
  - **Không** ráp cả bộ, **không** gửi cả bộ slide, trừ khi người dùng yêu cầu ráp.
- Lưu 1 trang: `python3 sua_slide/rap_file.py <file_goc.pptx> <file_ra.pptx> <số slide gốc>`
- Ráp cả bộ (chỉ khi được yêu cầu): `python3 sua_slide/rap_file.py <file_goc.pptx> <file_ra.pptx>`

| Slide gốc | Nội dung sửa | Trạng thái | File 1 trang |
|---|---|---|---|
| 3 | Bỏ hẳn trang 3 (sơ đồ tổng quan) khỏi bộ slide cuối cùng | OK – bỏ | (không có) |
| 5 | Giấy tờ hiện chậm (chậm 3 lần), mỗi giấy tờ dừng 2 giây; đủ hết thì đứng yên, không lặp lại (~27 giây) | OK | `Trang_05_giay_to.pptx` |
| 6–14 | Gộp 9 bước đăng ký xe thành 1 trang; video chậm 2 lần, dừng ~4 giây mỗi bước (~1 phút 50 giây) | OK | `Trang_06-14_dang_ky_xe.pptx` |
| 15–24 | Gộp 10 bước đăng ký tài xế thành 1 trang; cùng tốc độ chậm (~2 phút) | OK | `Trang_15-24_dang_ky_tai_xe.pptx` |
