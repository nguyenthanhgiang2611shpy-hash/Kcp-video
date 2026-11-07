"""Tạo bản TỰ CHẠY từ bản final: mỗi trang tự chuyển sang trang sau.

- Trang có video: chuyển sau khi video chạy xong + THEM_GIAY giây.
- Trang không có video: chuyển sau số giây đọc trong lời thuyết trình (tai_lieu/loi_thuyet_trinh.json).
- Vẫn bấm chuột được; phím S để tạm dừng / chạy tiếp cả bài.

Cách chạy: python3 tao_ban_tu_chay.py <final.pptx> <loi_thuyet_trinh.json> <ra.pptx>
"""
import json, re, sys, zipfile

SRC, JSON, OUT = sys.argv[1:4]
THEM_GIAY = 3
giay_doc = {t['so']: t['giay'] for t in json.load(open(JSON, encoding='utf-8'))['trang']}

zin = zipfile.ZipFile(SRC)
pres = zin.read('ppt/presentation.xml').decode('utf-8')
prels = zin.read('ppt/_rels/presentation.xml.rels').decode('utf-8')
order = ['ppt/slides/' + re.search(rf'Id="{r}"[^>]*Target="slides/([^"]+)"', prels).group(1)
         for r in re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres)]
moi = {}
for so, path in enumerate(order, 1):
    x = zin.read(path).decode('utf-8')
    x = re.sub(r'<p:transition\b[^>]*/>|<p:transition\b.*?</p:transition>', '', x, flags=re.S)
    durs = [int(d) for d in re.findall(r'<p:cTn id="4" dur="(\d+)"', x)]
    ms = (max(durs) + THEM_GIAY * 1000) if durs else giay_doc[so] * 1000
    tr = f'<p:transition spd="med" advTm="{ms}"><p:fade/></p:transition>'
    if '<p:timing>' in x:
        x = x.replace('<p:timing>', tr + '<p:timing>', 1)
    elif '<p:extLst>' in x.split('</p:clrMapOvr>')[-1]:
        x = x.replace('</p:clrMapOvr>', '</p:clrMapOvr>' + tr, 1)
    else:
        x = x.replace('</p:sld>', tr + '</p:sld>', 1)
    moi[path] = x
    print(f'trang {so}: tự chuyển sau {ms / 1000:.1f} giây' + (' (video)' if durs else ''))
with zipfile.ZipFile(OUT, 'w') as zout:
    for it in zin.infolist():
        data = moi[it.filename].encode('utf-8') if it.filename in moi else zin.read(it.filename)
        zout.writestr(it, data)
print('xong', OUT)
