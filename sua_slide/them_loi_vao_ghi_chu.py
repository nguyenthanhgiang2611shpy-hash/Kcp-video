"""Đưa lời thuyết trình (tai_lieu/loi_thuyet_trinh.json) vào đầu ghi chú người trình bày của từng trang.

Cách chạy: python3 them_loi_vao_ghi_chu.py <loi_thuyet_trinh.json> <vào.pptx> <ra.pptx>
"""
import json, sys
from pptx import Presentation

js, src, out = sys.argv[1:4]
data = json.load(open(js, encoding='utf-8'))
p = Presentation(src)
slides = list(p.slides)
assert len(slides) == len(data['trang']), 'số trang không khớp'
MARK = '— Ghi chú kỹ thuật —'
for s, d in zip(slides, data['trang']):
    g = d['giay']
    dur = f'{g} giây' if g < 60 else f'{g // 60} phút' + (f' {g % 60:02d} giây' if g % 60 else '')
    lines = [f'LỜI THUYẾT TRÌNH (~{dur})']
    if d.get('thao_tac'):
        lines.append(f'Thao tác: {d["thao_tac"]}')
    for moc, cau in d['loi']:
        lines.append(f'[{moc}] {cau}' if moc else cau)
    old = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ''
    if MARK in old:                       # chạy lại: bỏ lời cũ, giữ ghi chú kỹ thuật
        old = old.split(MARK, 1)[1].strip()
    s.notes_slide.notes_text_frame.text = '\n'.join(lines) + ('\n\n' + MARK + '\n' + old if old else '')
p.save(out)
print('đã ghi lời thuyết trình vào', len(slides), 'trang')
