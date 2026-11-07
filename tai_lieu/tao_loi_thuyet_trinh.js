// Tạo file Word lời thuyết trình từ loi_thuyet_trinh.json
// Cách chạy: node tao_loi_thuyet_trinh.js <json> <thư mục ảnh slide p-01.jpg...> <ra.docx>
const fs = require('fs'), path = require('path');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
        HeadingLevel, BorderStyle, Header, Footer, PageNumber, TabStopType, ImageRun, VerticalAlign } = require('docx');
const [jsonPath, imgDir, out] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
const FONT = 'Arial', BLUE = '1F4E9A', GREY = '666666', LINE = 'C9D3E0';
const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color });
const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const thin = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const fmt = s => s < 60 ? `${s} giây` : `${Math.floor(s / 60)} phút${s % 60 ? ' ' + String(s % 60).padStart(2, '0') + ' giây' : ''}`;
const total = data.trang.reduce((a, p) => a + p.giay, 0);

const children = [
  new Paragraph({ children: [t('LỜI THUYẾT TRÌNH', { size: 34, bold: true, color: BLUE })], spacing: { after: 40 } }),
  new Paragraph({ children: [t('Quy trình xuất một xe đường tại cầu cân · 18 trang', { size: 24, bold: true })], spacing: { after: 120 } }),
  new Paragraph({ children: [t(`Tổng thời gian dự kiến: ${fmt(total)}. Xưng hô: tôi – các anh chị.`, { color: GREY })], spacing: { after: 60 } }),
  new Paragraph({ children: [t('Cách đọc: ', { bold: true }), t('chữ đậm như '), t('[0:21]', { bold: true, color: 'C0392B' }),
    t(' là mốc thời gian trong video của trang đó – nói câu đó khi video chạy tới mốc này. Cần nói lâu hơn thì bấm vào video hoặc phím Space để tạm dừng.')], spacing: { after: 200, line: 300 } }),
];

data.trang.forEach(p => {
  const img = path.join(imgDir, `p-${String(p.so).padStart(2, '0')}.jpg`);
  const left = [new Paragraph({ children: [new ImageRun({ type: 'jpg', data: fs.readFileSync(img), transformation: { width: 208, height: 117 } })] }),
                new Paragraph({ children: [t(`Trang ${p.so} · ~${fmt(p.giay)}`, { size: 17, color: GREY })], spacing: { before: 40 } })];
  const right = [new Paragraph({ heading: HeadingLevel.HEADING_2, children: [t(`Trang ${p.so}. ${p.ten}`)] })];
  if (p.thao_tac) right.push(new Paragraph({ children: [t('Thao tác: ', { bold: true, size: 19, color: GREY }), t(p.thao_tac, { italics: true, size: 19, color: GREY })], spacing: { after: 80 } }));
  p.loi.forEach(([moc, cau]) => {
    const runs = moc ? [t(`[${moc}] `, { bold: true, color: 'C0392B' }), t(cau)] : [t(cau)];
    right.push(new Paragraph({ children: runs, spacing: { after: 80, line: 300 } }));
  });
  children.push(new Table({
    width: { size: 9638, type: WidthType.DXA }, columnWidths: [3300, 6338],
    rows: [new TableRow({ cantSplit: true, children: [
      new TableCell({ children: left, width: { size: 3300, type: WidthType.DXA }, verticalAlign: VerticalAlign.TOP,
        borders: { top: thin, bottom: thin, left: none, right: none }, margins: { top: 120, bottom: 120, left: 0, right: 160 } }),
      new TableCell({ children: right, width: { size: 6338, type: WidthType.DXA },
        borders: { top: thin, bottom: thin, left: none, right: none }, margins: { top: 120, bottom: 120, left: 160, right: 0 } }),
    ] })],
  }));
  children.push(new Paragraph({ children: [], spacing: { after: 60 } }));
});

const doc = new Document({
  creator: 'KCP Việt Nam', title: data.tieu_de,
  styles: { default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [{ id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: FONT, size: 24, bold: true, color: BLUE }, paragraph: { spacing: { before: 0, after: 80 }, keepNext: true, outlineLevel: 1 } }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ children: [t('CÔNG TY TNHH CÔNG NGHIỆP KCP VIỆT NAM', { size: 16, bold: true, color: GREY }), t('\tLời thuyết trình · Xuất xe đường tại cầu cân', { size: 16, color: GREY })],
      tabStops: [{ type: TabStopType.RIGHT, position: 9638 }], border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE, space: 4 } } })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [t('Trang ', { size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: GREY }), t(' / ', { size: 16, color: GREY }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: GREY })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log('ok'); });
