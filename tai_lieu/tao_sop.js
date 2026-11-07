const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
        HeadingLevel, LevelFormat, BorderStyle, Header, Footer, PageNumber, TabStopType } = require('docx');

const FONT = 'Arial';
const BLUE = '1F4E9A', GREY = '595959', LIGHT = 'EAF1FB', LINE = 'B7C4D6';
const W = 9638; // vùng chữ A4 lề 2 cm (DXA)

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color });
const P = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs)], spacing: { after: o.after ?? 100, before: o.before ?? 0, line: 300 }, alignment: o.align, ...(o.extra || {}) });
// chuỗi có **đậm**
const rich = (s, size) => s.split('**').map((x, i) => t(x, { bold: i % 2 === 1, size }));
const H1 = s => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(s)] });
const H2 = s => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(s)] });
const bullet = (s, lvl = 0) => new Paragraph({ numbering: { reference: 'dot', level: lvl }, children: rich(s), spacing: { after: 60, line: 290 } });
const num = (s, ref = 'num') => new Paragraph({ numbering: { reference: ref, level: 0 }, children: rich(s), spacing: { after: 60, line: 290 } });
const check = s => new Paragraph({ numbering: { reference: 'box', level: 0 }, children: rich(s), spacing: { after: 60, line: 290 } });

const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(content, width, o = {}) {
  const paras = (Array.isArray(content) ? content : [content]).map(c =>
    typeof c === 'string' ? new Paragraph({ children: rich(c, 20), spacing: { after: 40, line: 276 } }) : c);
  return new TableCell({ children: paras, width: { size: width, type: WidthType.DXA }, borders,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 80, bottom: 80, left: 110, right: 110 } });
}
function table(widths, header, rows) {
  const hdr = new TableRow({ tableHeader: true, children: header.map((h, i) =>
    cell(new Paragraph({ children: [t(h, { bold: true, size: 20, color: 'FFFFFF' })], spacing: { after: 20 } }), widths[i], { fill: BLUE })) });
  const body = rows.map((r, k) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], { fill: k % 2 ? 'F6F8FB' : undefined })) }));
  return new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, rows: [hdr, ...body] });
}
const gap = (n = 120) => new Paragraph({ children: [], spacing: { after: n } });

// ---------- Khối thông tin tài liệu ----------
const info = table([2400, 7238], ['Thông tin', 'Nội dung'], [
  ['Tên tài liệu', '**Quy trình làm và sửa slide đào tạo cùng Claude**'],
  ['Mã số', 'SOP-VT-01 (đề xuất, bộ phận điều chỉnh theo hệ thống mã của công ty)'],
  ['Phiên bản / Ngày', '1.0 / 07/11/2026'],
  ['Bộ phận áp dụng', 'Vận tải và Dịch vụ khách hàng'],
  ['Ví dụ áp dụng', 'Bộ slide "Quy trình xuất một xe đường tại cầu cân" (42 slide gốc → 18 slide bản final)'],
  ['Người soạn / Người duyệt', '……………………… / ………………………'],
]);

// ---------- Bảng các bước ----------
const steps = table([900, 2200, 4238, 2300], ['Bước', 'Việc cần làm', 'Cách làm', 'Kết quả'], [
  ['1', 'Chuẩn bị file gốc', ['Tải file PowerPoint gốc lên khung chat.', 'Nói rõ mục đích bộ slide và người xem (ví dụ: đào tạo nhân viên cầu cân).'], 'Claude có đủ file gốc để làm.'],
  ['2', 'Thống nhất cách đánh số trang', ['Chọn một cách gọi trang và giữ nguyên tới cuối: **theo bản gốc** hoặc **theo số in ở góc slide**.', 'Khi gọi theo số in ở góc, nói rõ "số in ở góc".'], 'Hai bên hiểu cùng một trang.'],
  ['3', 'Gọi trang và nêu yêu cầu', ['Mỗi lần gọi **một trang** hoặc **một nhóm trang liền nhau**.', 'Nêu cụ thể: gộp trang, tốc độ video, thêm hình, bớt chữ, sửa câu chữ.', 'Nội dung nghiệp vụ (các bước trên phần mềm): yêu cầu Claude **viết quy trình ra khung chat trước** để duyệt chữ.'], 'Yêu cầu rõ ràng, đúng trang.'],
  ['4', 'Claude hỏi lại khi chưa rõ', ['Claude hỏi trước khi làm nếu còn điểm chưa rõ.', 'Người yêu cầu trả lời ngắn từng ý.'], 'Không làm sai ý.'],
  ['5', 'Claude sửa đúng trang được gọi', ['Chỉ sửa trang đó, **không đụng các trang khác**.', 'Giữ phông chữ, màu, bố cục giống các trang còn lại.'], 'Trang đã sửa, chờ duyệt.'],
  ['6', 'Xem trước ngay trong khung chat', ['Claude đưa **ảnh hoặc ảnh động (GIF)** hiện thẳng trong khung chat, kèm file chỉ có trang đó.', 'Kiểm tra: chữ đúng, hình đúng, tốc độ đủ để nói kịp.'], 'Người yêu cầu thấy kết quả mà không cần tải file.'],
  ['7', 'Duyệt', ['Đạt: nói **"ok"**. Claude lưu riêng trang đó (file 1 trang) và ghi trạng thái OK trong file theo dõi.', 'Chưa đạt: nói rõ điểm cần sửa, quay lại bước 5.'], 'Trang được chốt.'],
  ['8', 'Ráp bản final', ['Chỉ ráp khi người yêu cầu nói **"ráp final"**.', 'Trang không sửa giữ nguyên như bản gốc; trang đã duyệt thay vào đúng chỗ; trang bị bỏ thì xoá.', 'Claude đánh lại số trang liên tục, sửa các chỗ ghi "trang X" cho khớp, nén nhỏ file.'], 'File final hoàn chỉnh, gửi email được.'],
  ['9', 'Kiểm tra bản final', ['Xem bản PDF hoặc trang web xem slide ngay trong khung chat.', 'Mở thử bằng PowerPoint trước khi gửi: video tự chạy, trang đầu không trống.'], 'Không còn lỗi trước khi gửi.'],
  ['10', 'Lưu trữ và gửi', ['Tải file final về (thẻ file trong khung chat hoặc nút "Download raw file" trên GitHub).', 'Gửi email; cần cho người khác xem trên web thì bấm Share trên trang web xem slide.'], 'Hồ sơ được lưu, người nhận mở được.'],
]);

// ---------- Tiêu chuẩn kỹ thuật ----------
const stds = table([2700, 6938], ['Hạng mục', 'Tiêu chuẩn'], [
  ['Video thao tác phần mềm', ['Gộp các slide từng bước thành **1 slide 1 video**.', 'Phát **chậm 2–3 lần**, mỗi bước dừng **4–5 giây**, bước cuối dừng **6 giây**.', 'Chạy **1 lần rồi đứng yên ở khung cuối**; không lặp lại.']],
  ['Hình minh hoạ ngắn', 'Có thể chạy lặp lại (ví dụ: hình kiểm tra xe trước khi cân).'],
  ['Trang tổng quan', ['Chỉ giữ **mỗi giai đoạn một đoạn minh hoạ**, bỏ phần chi tiết.', 'Khoanh **vòng đỏ** giai đoạn đang nói; giai đoạn đã nói **giữ vòng đỏ tới cuối**.']],
  ['Ảnh chờ của video', 'Phải là khung hình **có nội dung** (ví dụ khung đã vẽ xong). Không để trang trắng khi mở file.'],
  ['Chữ trên slide', ['Ít chữ, câu ngắn, viết theo đúng thứ tự thao tác.', 'Tên ô và nút trên phần mềm **in đậm** (ví dụ: **Truck No**, **Save**, **Print**).', 'Dùng đúng từ của công ty (ví dụ: Kho và Process **kiểm tra và xác nhận**).']],
  ['Ghi chú người trình bày', 'Có **mốc thời gian** từng bước của video và các lưu ý cần nói thêm.'],
  ['Số trang và tham chiếu', 'Số trang ở góc **liên tục**; mọi chỗ ghi "trang X" phải khớp với bản final.'],
  ['Giấy tờ mẫu', 'CCCD, bằng lái, cà vẹt trên slide là **bản mẫu**, tên và số là giả.'],
  ['Dung lượng file', ['Video nén H.264, rộng 1280 điểm ảnh; ảnh nền JPEG.', 'Mục tiêu **dưới 10 MB** để gửi email (Gmail giới hạn 25 MB, Outlook 20 MB).']],
]);

// ---------- Mẫu câu ----------
const phrases = table([4100, 5538], ['Muốn làm', 'Nói với Claude'], [
  ['Gộp nhiều slide bước thành 1', '"Từ slide 26 đến 32 gộp lại thành 1, tốc độ chậm như slide 6–14."'],
  ['Cho chạy chậm, dừng khi đủ', '"Trang 5: giấy tờ hiện ra chậm, đủ hết thì dừng, không chạy liên tục."'],
  ['Duyệt chữ trước khi làm', '"Trang 16: viết quy trình ra đây trước khi làm vào slide."'],
  ['Bỏ một trang', '"Bỏ trang 3, không dùng trang 3."'],
  ['Chốt trang', '"ok"'],
  ['Xem trước', '"Cho tôi xem trên khung chat."'],
  ['Ra bản cuối', '"Ráp lại thành bản final, dung lượng nhỏ nhất để gửi email."'],
]);

// ---------- Hồ sơ ----------
const files = table([3600, 6038], ['Hồ sơ', 'Nơi lưu'], [
  ['File gốc', 'File người yêu cầu tải lên (ví dụ: Quy_trinh_xuat_mot_xe_duong_tai_cau_can_NHO.pptx).'],
  ['File từng trang đã duyệt', 'Thư mục **sua_slide/** trên GitHub, tên dạng Trang_05_giay_to.pptx.'],
  ['Theo dõi tiến độ', '**sua_slide/TIEN_DO.md**: trang nào đã sửa, nội dung sửa, trạng thái (Chờ duyệt / OK / Bỏ).'],
  ['Bản final', '**Quy_trinh_xuat_xe_duong_tai_cau_can_FINAL.pptx** ở thư mục gốc của repo.'],
  ['Xem trên web', 'Trang web xem slide (link riêng tư, chia sẻ bằng nút Share).'],
]);

const doc = new Document({
  creator: 'KCP Việt Nam', title: 'SOP làm và sửa slide đào tạo cùng Claude',
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', run: { font: FONT, size: 36, bold: true, color: BLUE }, paragraph: { spacing: { before: 0, after: 80 }, keepNext: true } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 28, bold: true, color: BLUE }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 24, bold: true, color: '1A1A1A' }, paragraph: { spacing: { before: 180, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: 'dot', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
                                 { level: 1, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1000, hanging: 270 } } } }] },
    { reference: 'box', levels: [{ level: 0, format: LevelFormat.BULLET, text: '☐', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 320 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ children: [t('CÔNG TY TNHH CÔNG NGHIỆP KCP VIỆT NAM', { size: 16, bold: true, color: GREY }), t('\tSOP-VT-01 · Phiên bản 1.0', { size: 16, color: GREY })],
      tabStops: [{ type: TabStopType.RIGHT, position: W }], border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE, space: 4 } } })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [t('Trang ', { size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: GREY }), t(' / ', { size: 16, color: GREY }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: GREY })] })] }) },
    children: [
      new Paragraph({ style: 'Title', children: [t('QUY TRÌNH LÀM VÀ SỬA SLIDE ĐÀO TẠO CÙNG CLAUDE', { size: 34, bold: true, color: BLUE })] }),
      P([t('Standard Operating Procedure (SOP) · Bộ phận Vận tải và Dịch vụ khách hàng', { color: GREY, size: 20 })], { after: 200 }),
      info,
      H1('1. Mục đích'),
      P(rich('Thống nhất cách phối hợp với Claude khi làm và sửa bộ slide đào tạo: sửa **đúng trang**, **xem trước** ngay trong khung chat, **chỉ chốt khi người yêu cầu nói "ok"**, và ra **bản final gọn nhẹ** để gửi email.')),
      H1('2. Phạm vi áp dụng'),
      bullet('Bộ slide đào tạo nội bộ có hình ảnh, video thao tác phần mềm (TMS, Sales Order and Despatch, Weighbridge…).'),
      bullet('Áp dụng cho người yêu cầu (nhân viên soạn bài đào tạo) và Claude (người thực hiện chỉnh sửa).'),
      H1('3. Thuật ngữ'),
      table([2600, 7038], ['Thuật ngữ', 'Nghĩa'], [
        ['Slide gốc', 'Slide trong file ban đầu người yêu cầu tải lên.'],
        ['Số in ở góc', 'Số trang in ở góc phải dưới của mỗi slide.'],
        ['File 1 trang', 'File PowerPoint chỉ chứa đúng trang vừa sửa, dùng để duyệt và lưu.'],
        ['Bản final', 'Bộ slide hoàn chỉnh sau khi ráp các trang đã duyệt.'],
        ['Xem trước', 'Ảnh hoặc ảnh động (GIF) Claude đưa thẳng vào khung chat để xem ngay.'],
        ['Trang web xem slide', 'Trang xem cả bộ slide trên trình duyệt, có video chạy, không cần PowerPoint.'],
      ]),
      H1('4. Trách nhiệm'),
      table([2600, 7038], ['Vai trò', 'Trách nhiệm'], [
        ['Người yêu cầu', ['Cung cấp file gốc, gọi đúng trang, nêu yêu cầu cụ thể.', 'Duyệt nội dung nghiệp vụ, nói "ok" khi đạt.', 'Mở thử bản final bằng PowerPoint trước khi gửi.']],
        ['Claude', ['Hỏi lại khi chưa rõ; chỉ sửa đúng trang được gọi.', 'Đưa bản xem trước vào khung chat sau mỗi lần sửa.', 'Lưu file từng trang, ghi tiến độ, ráp và nén bản final khi được yêu cầu.']],
      ]),
      H1('5. Các bước thực hiện'),
      steps,
      H1('6. Tiêu chuẩn kỹ thuật của slide'),
      stds,
      H1('7. Mẫu câu yêu cầu thường dùng'),
      phrases,
      H1('8. Danh mục kiểm tra trước khi gửi bản final'),
      check('Tất cả trang đã sửa có trạng thái **OK** trong file theo dõi.'),
      check('Số trang ở góc liên tục từ đầu tới cuối; các chỗ ghi "trang X" khớp.'),
      check('Trang 1 hiện chữ ngay khi mở file (không trống).'),
      check('Video tự chạy khi vào trang; video thao tác chạy 1 lần rồi dừng.'),
      check('Câu chữ nghiệp vụ đúng quy định công ty (đã duyệt ở khung chat).'),
      check('Dung lượng file dưới 10 MB.'),
      check('Đã mở thử bằng PowerPoint trên máy sẽ trình chiếu.'),
      H1('9. Hồ sơ lưu trữ'),
      files,
      H1('10. Lịch sử thay đổi'),
      table([1600, 1800, 6238], ['Phiên bản', 'Ngày', 'Nội dung'], [
        ['1.0', '07/11/2026', 'Ban hành lần đầu, đúc kết từ việc làm bộ slide "Quy trình xuất một xe đường tại cầu cân".'],
      ]),
    ],
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2], b); console.log('ok'); });
