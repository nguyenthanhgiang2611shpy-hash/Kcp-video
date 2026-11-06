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
    (5, 5, 'Trang05_giay_to_cham.mp4', 27.3,
     """[Video tự chạy 1 lần, khoảng 27 giây, đủ 4 giấy tờ thì đứng yên – không lặp lại]
0:00 Đăng kiểm xe – 0:06 Cà vẹt xe – 0:11 CCCD – 0:14 Bằng lái (GPLX) – 0:19 hai form nhập TMS, đủ dấu tích ở 0:25.

Tài xế lên cầu cân làm phiếu, mang theo 4 giấy tờ: đăng kiểm xe, cà vẹt xe, CCCD và bằng lái (GPLX). Đăng kiểm và cà vẹt dùng để nhập form Đăng ký xe vận chuyển đường (trang 6). CCCD và bằng lái dùng để nhập form Đăng ký tài xế (trang 7); ảnh chân dung chụp tại cầu cân bằng webcam. Xe hoặc tài xế đã có trên hệ thống thì chỉ cần kiểm tra thông tin còn đúng không. Cà vẹt, CCCD và bằng lái trên slide là bản mẫu."""),
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
]

# Slide thay bằng ảnh thiết kế mới: {số slide gốc: file ảnh}
THAY_ANH = {
    3: 'Slide03_tong_quan_canva.jpg',  # thiết kế lại trên Canva (DAHaJvmsdZo)
}


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
            ctn.attrib.pop('repeatCount', None)  # chạy 1 lần, dừng ở khung cuối
        s.notes_slide.notes_text_frame.text = ghichu
        xoa += ids[dau:cuoi]
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
