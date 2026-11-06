"""Ráp file hoàn chỉnh: áp các slide đã sửa lên bản gốc 42 slide.

Ráp cả bộ:  python3 rap_file.py <file_goc.pptx> <file_ra.pptx>
Lưu 1 trang: python3 rap_file.py <file_goc.pptx> <file_ra.pptx> <số slide gốc>
Số slide trong GOP tính theo bản gốc 42 slide.
"""
import os
import sys
from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
NS = '{http://schemas.openxmlformats.org/presentationml/2006/main}'

# (slide đầu, slide cuối, video ghép, thời lượng giây, ghi chú người trình bày)
# slide đầu = slide cuối: chỉ thay video của 1 slide, không gộp.
GOP = [
    (2, 2, 'Trang02_toan_bo_quy_trinh_cham.mp4', 220.8,
     """[Video tự chạy 1 lần, khoảng 3 phút 41 giây, phủ toàn trang; hết video thì đứng yên] Video phát chậm 3 lần, mỗi bước dừng khoảng 5 giây. Giai đoạn đang nói được khoanh đỏ trong danh sách bên phải; giai đoạn đã nói vẫn giữ vòng đỏ tới cuối. Bấm vào video (hoặc phím Space) để tạm dừng khi cần giải thích thêm – vòng đỏ dừng theo video.

Mốc thời gian:
0:00  Giai đoạn 1 – Trước khi cân (khoanh đỏ ô 1)
      0:00 Bước 1 Xe đến bãi đậu xe KCP · 0:19 Bước 2 Đăng ký tài ở cổng bảo vệ · 0:40 Bước 3 Làm phiếu tại cầu cân · 1:05 Bước 4 Nhập thông tin lên TMS · 1:25 Bước 5 Bảo vệ mở xe trên hệ thống
1:46  Giai đoạn 2 – Cân vào và bốc hàng (khoanh thêm ô 2)
      1:46 Bước 6 Kiểm tra trước khi cân xe vào · 2:10 Bước 7 Cân xe vào, so với lần cân đầu · 2:35 Bước 8 Vào kho bốc hàng
2:53  Giai đoạn 3 – Cân ra (khoanh thêm ô 3)
      2:53 Bước 9 Cân xe ra: Net = Gross – Tare, đối chiếu tờ duyệt dư cân
3:20  Giai đoạn 4 – Chứng từ và ra cổng (khoanh thêm ô 4)
      3:20 Bước 10 Đủ bộ chứng từ xuất hàng: DC → hợp đồng vận chuyển → COA

Các slide sau đi chi tiết từng bước."""),
    (6, 14, 'Dang_ky_xe_9_buoc_cham.mp4', 110.2,
     """[Video tự chạy – 9 bước trong 1 slide, khoảng 1 phút 50 giây] Video phát chậm, mỗi bước dừng khoảng 4 giây để giải thích. Muốn dừng lâu hơn: bấm vào video (hoặc phím Space) để tạm dừng, bấm lần nữa để chạy tiếp.

Mốc thời gian:
0:00  Bước 1 – Bấm Thêm mới để mở form đăng ký xe trống.
0:10  Bước 2 – Mã nhà vận chuyển: chọn mã có sẵn trong danh sách.
0:21  Bước 3 – Số xe: biển số 78C-033.89 gõ có dấu cách 78C 03389.
0:34  Bước 4 – Loại xe: chọn Ô tô tải có mui (theo Loại phương tiện trên đăng kiểm).
0:47  Bước 5 – Số đăng kiểm: số seri tem KĐ VB 3813018.
1:00  Bước 6 – Hạn đăng kiểm: 29/04/2027.
1:13  Bước 7 – Tải trọng: đổi 16.700 kg ra 16,7 tấn.
1:26  Bước 8 – Ảnh xe: chỉ nhận JPG, tối đa 5 MB.
1:38  Bước 9 – Bấm Lưu: xe đã được đăng ký trên TMS.

Lưu ý: Mỗi ô khung đỏ trên TMS lấy từ một dòng trên giấy đăng kiểm. Biển số và thông tin xe đối chiếu thêm với cà vẹt. Khi xe đăng kiểm lại, phải cập nhật số tem và hạn mới."""),
    (15, 24, 'Dang_ky_tai_xe_10_buoc_cham.mp4', 119.9,
     """[Video tự chạy – 10 bước trong 1 slide, khoảng 2 phút] Video phát chậm, mỗi bước dừng khoảng 4 giây để giải thích. Muốn dừng lâu hơn: bấm vào video (hoặc phím Space) để tạm dừng, bấm lần nữa để chạy tiếp.

Mốc thời gian:
0:00  Bước 1 – Bấm Thêm mới để mở form đăng ký tài xế trống.
0:09  Bước 2 – Mã tài xế: mã trên hệ thống (dạng DR + số).
0:20  Bước 3 – Tên tài xế: họ và tên trên CCCD.
0:33  Bước 4 – Số CCCD: 12 số trên CCCD.
0:45  Bước 5 – Số GPLX: số trên giấy phép lái xe.
0:59  Bước 6 – Số điện thoại: hỏi trực tiếp tài xế.
1:11  Bước 7 – Ảnh bằng lái: Choose File, chọn ảnh GPLX.
1:23  Bước 8 – Ảnh CCCD: Choose File, chọn ảnh CCCD.
1:35  Bước 9 – Chụp mặt: chọn webcam, bấm Camera, chụp mặt tài xế tại cầu cân.
1:47  Bước 10 – Bấm Lưu. Lần sau tìm lại tài xế bằng mã hoặc tên.

Lưu ý: Ảnh chân dung chụp trực tiếp tại cầu cân bằng webcam, không dùng ảnh tài xế gửi qua điện thoại. Tài xế đã có trên hệ thống thì tìm theo mã hoặc tên và kiểm tra lại thông tin. CCCD và GPLX trên slide là bản mẫu, tên và số là giả."""),
    (26, 32, 'Loading_request_7_buoc_cham.mp4', 91.3,
     """[Video tự chạy – 7 bước trong 1 slide, khoảng 1 phút 31 giây] Video phát chậm, mỗi bước dừng khoảng 4 giây để giải thích. Muốn dừng lâu hơn: bấm vào video (hoặc phím Space) để tạm dừng, bấm lần nữa để chạy tiếp.

Mốc thời gian:
0:00  Bước 1 – Mở Loading Request: menu Sales Order and Despatch → Loading Request.
0:11  Bước 2 – Order No: chọn đúng số PO nội bộ của KCP, kiểm tra Balance còn đủ hàng.
0:25  Bước 3 – Kho xuất: Store From = 01 là kho KCP Sơn Hòa; kho ngoài chọn 48, 49 hoặc 50.
0:37  Bước 4 – Vận tải, xe, tài xế: Trpt Code → Truck No → Truck Driver; xe và tài xế phải đã đăng ký TMS.
0:52  Bước 5 – Số lượng: 17 tấn = 340 bao (50 kg/bao).
1:03  Bước 6 – Chọn lô theo FIFO: lô nhập trước xuất trước (ví dụ lô 278, 05/07/2026).
1:18  Bước 7 – Bấm Save. Số Load Req dùng để cân xe vào ở bước sau.

Lưu ý: Phần cân (Weigh Bridge Weightment Detail) do cầu cân tự điền khi cân."""),
    (33, 33, 'Trang33_kiem_tra_xe_2_nguoi.mp4', 6.8,
     """Hình động: nhân viên bảo vệ đi từ đuôi xe tới, nhân viên cầu cân đi từ đầu xe tới, cùng giám sát xe trước khi cân.

Trước khi cân xe vào phải có nhân viên phòng bảo vệ và nhân viên cầu cân cùng kiểm tra. Không cân khi bánh xe dính bùn, sàn xe ướt hoặc nước đọng trên bạt trần xe, hoặc xe không đậu giữa cầu cân. Bùn và nước làm sai xác xe, xe lệch làm sai số cân."""),
]

# Slide có video phủ toàn trang: {số slide gốc: ảnh hiện trước khi video chạy}
TOAN_TRANG = {2: 'Trang02_poster.jpg'}

# Slide giữ chế độ chạy lặp lại như bản gốc (không tắt lặp)
GIU_LAP = {33}

# Slide thay bằng ảnh thiết kế mới: {số slide gốc: file ảnh}
THAY_ANH = {
    2: 'Trang02_nen.jpg',  # tiêu đề mới, bỏ dòng 'Video không có tiếng'
}

# Slide gốc bỏ hẳn khỏi bộ slide cuối cùng
BO_SLIDE = [3]


def main(src, out, chi_giu=None):
    """chi_giu: số slide gốc cần giữ lại một mình (lưu 1 trang); None = ráp cả bộ."""
    p = Presentation(src)
    slides = list(p.slides)
    ids = list(p.slides._sldIdLst)
    for so, anh in THAY_ANH.items():
        s = slides[so - 1]
        blob = open(os.path.join(HERE, anh), 'rb').read()
        for rel in s.part.rels.values():
            if rel.reltype.endswith('/image'):
                rel.target_part._blob = blob
    xoa = []
    for dau, cuoi, video, giay, ghichu in GOP:
        s = slides[dau - 1]
        blob = open(os.path.join(HERE, video), 'rb').read()
        for rel in s.part.rels.values():
            if 'media' in rel.reltype or rel.reltype.endswith('/video'):
                rel.target_part._blob = blob
        for ctn in s._element.iter(NS + 'cTn'):
            if ctn.get('id') == '4':
                ctn.set('dur', str(int(giay * 1000)))
            if dau not in GIU_LAP:
                ctn.attrib.pop('repeatCount', None)  # chạy 1 lần, dừng ở khung cuối
        s.notes_slide.notes_text_frame.text = ghichu
        if dau in TOAN_TRANG:
            for sh in s.shapes:
                if sh.shape_type == 16:  # MEDIA
                    sh.left, sh.top = 0, 0
                    sh.width, sh.height = p.slide_width, p.slide_height
                    blip = sh._element.find('.//' + '{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                    rid = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    s.part.related_part(rid)._blob = open(os.path.join(HERE, TOAN_TRANG[dau]), 'rb').read()
        xoa += ids[dau:cuoi]
    xoa += [ids[so - 1] for so in BO_SLIDE]
    if chi_giu is not None:
        xoa = [sid for i, sid in enumerate(ids) if i != chi_giu - 1]
    for sid in xoa:
        p.part.drop_rel(sid.rId)
        p.slides._sldIdLst.remove(sid)
    p.save(out)
    print('Số slide:', len(p.slides))


if __name__ == '__main__':
    # Lưu 1 trang:  python3 rap_file.py <goc.pptx> <ra.pptx> <số slide gốc>
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
