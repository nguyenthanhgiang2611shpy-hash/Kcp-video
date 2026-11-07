# Hướng dẫn cho Claude khi làm việc trong repo này

Repo của bộ phận Vận tải và Dịch vụ khách hàng, Công ty TNHH Công Nghiệp KCP Việt Nam (sản xuất đường).
Nội dung chính: bộ slide đào tạo "Quy trình xuất một xe đường tại cầu cân" và các video minh họa.

**Luôn làm theo SOP:** `tai_lieu/SOP_lam_slide_voi_Claude.docx` (bản tóm tắt bên dưới).
Đọc `sua_slide/TIEN_DO.md` trước khi bắt đầu để biết trang nào đã sửa, trang nào đang chờ duyệt.

## Cách làm việc với người dùng (bắt buộc)

1. **Hỏi lại khi chưa rõ** trước khi làm. Người dùng đã nhiều lần bị hiểu sai:
   - "Ok" có thể là duyệt trang vừa gửi, không phải đồng ý một đề xuất khác → hỏi lại nếu có hơn một việc đang chờ.
   - "Giữ nguyên" có thể là giữ bản cũ, không phải giữ đề xuất → hỏi lại.
2. **Gọi trang nào sửa đúng trang đó**, không đụng trang khác. Số trang người dùng gọi thường là **số in ở góc slide của bản final**; nếu khác với số trong bản gốc thì nói rõ và hỏi lại khi nghi ngờ.
3. **Nội dung nghiệp vụ (các bước trên phần mềm, câu chữ quy định): viết đề xuất ra khung chat trước**, chờ người dùng duyệt rồi mới làm vào slide. Đề xuất có bảng "hiện tại / đề xuất" và khung hình mẫu nếu là thay đổi về hình.
4. **Xem trước ngay trong khung chat sau mỗi lần sửa:**
   - Ảnh tĩnh (PNG/JPG) luôn hiện được.
   - Video và GIF có thể **không chạy** trong khung chat của người dùng → làm thêm trang xem trước (Artifact) có video, **chạy 1 lần rồi dừng**, có nút xem lại, và mở trang đó cho người dùng.
5. **Chỉ lưu khi người dùng nói "ok"**: lưu file 1 trang trong `sua_slide/` và đổi trạng thái trong `sua_slide/TIEN_DO.md` thành OK.
6. **Không ráp và không gửi cả bộ** trừ khi người dùng yêu cầu ("ráp final").
7. Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu (người dùng không chuyên kỹ thuật).

## Tiêu chuẩn slide

- Video thao tác phần mềm: gộp các slide từng bước thành 1 slide 1 video; chậm 2–3 lần; dừng 4–5 giây mỗi bước, bước cuối 6 giây; chạy 1 lần rồi đứng yên ở khung cuối.
- Trang tổng quan: mỗi giai đoạn một đoạn minh họa; khoanh đỏ giai đoạn đang nói và giữ tới cuối.
- Ảnh chờ của video phải có nội dung (không để trang trắng khi mở file).
- Ít chữ; tên ô và nút phần mềm in đậm (Truck No, Save, Print…).
- Đúng từ của công ty: Kho và Process **kiểm tra và xác nhận** (không "ký xác nhận"); Loại xe: container bạt → **Trailer** (nhập thêm Rơ moóc), 4 chân trở xuống → **Normal Truck**.
- Ghi chú người trình bày có mốc thời gian video; số trang liên tục; tham chiếu "trang X" phải khớp.
- Bản final dưới 10 MB để gửi email.

## Quy trình kỹ thuật

- File gốc (42 slide) do người dùng tải lên: `Quy_trinh_xuat_mot_xe_duong_tai_cau_can_NHO.pptx` (trong thư mục uploads của phiên).
- Ráp cả bộ: `python3 sua_slide/rap_file.py <file_goc.pptx> full_raw.pptx` (cấu hình các trang đã sửa nằm trong script: GOP, THAY_ANH, POSTER, GIU_LAP, BO_SLIDE, SUA_GHI_CHU).
- Lưu 1 trang: `python3 sua_slide/rap_file.py <file_goc.pptx> <ra.pptx> <số slide gốc>`.
- Hoàn thiện (đánh lại số trang, sửa tham chiếu trang, nén): `python3 sua_slide/hoan_thien.py full_raw.pptx FINAL.pptx <thư mục phông Nunito>`.
- Lời thuyết trình: `tai_lieu/loi_thuyet_trinh.json` → `node tai_lieu/tao_loi_thuyet_trinh.js ...` (file Word) và `python3 sua_slide/them_loi_vao_ghi_chu.py tai_lieu/loi_thuyet_trinh.json FINAL.pptx FINAL.pptx` (ghi vào ghi chú).
- Phông Nunito: gói npm `@fontsource/nunito`, gộp bộ latin + latin-ext + vietnamese bằng fontTools.
- Bản final: `Quy_trinh_xuat_xe_duong_tai_cau_can_FINAL.pptx` ở thư mục gốc repo.
