"""Hoàn thiện bộ slide sau khi ráp: đánh lại số trang, sửa tham chiếu trang, nén nhỏ để gửi email.

Cách chạy: python3 hoan_thien.py <vào.pptx> <ra.pptx> <thư mục phông Nunito>
"""
import os, re, shutil, subprocess, sys, tempfile, zipfile
from PIL import Image, ImageChops, ImageDraw, ImageFont

SRC, OUT, FONTDIR = sys.argv[1:4]
F_NUM = ImageFont.truetype(os.path.join(FONTDIR, 'Nunito-400.ttf'), 22)
F_REF = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Medium.otf', 19)
NUM_BOX = (1450, 814, 1502, 850)       # vùng số trang (toạ độ ảnh 1600x900)
NUM_RIGHT, NUM_BASE = 1494.5, 840

tmp = tempfile.mkdtemp()
with zipfile.ZipFile(SRC) as z:
    z.extractall(tmp)
P = lambda *a: os.path.join(tmp, *a)

pres = open(P('ppt/presentation.xml'), encoding='utf-8').read()
prels = open(P('ppt/_rels/presentation.xml.rels'), encoding='utf-8').read()
order = [re.search(rf'Id="{r}"[^>]*Target="([^"]+)"', prels).group(1).split('/')[-1]
         for r in re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"', pres)]

def rels_of(slide):
    t = open(P('ppt/slides/_rels', slide + '.rels'), encoding='utf-8').read()
    return dict(re.findall(r'Id="(rId\d+)"[^>]*Target="\.\./media/([^"]+)"', t))

def renumber(im, n):
    """Xoá số trang cũ, viết số mới cùng kiểu."""
    im = im.convert('RGB')
    x0, y0, x1, y1 = NUM_BOX
    bgc = im.getpixel((1440, 832))
    # màu chữ = điểm khác nền nhiều nhất trong vùng số cũ
    ink = max((im.getpixel((x, y)) for x in range(x0, x1) for y in range(y0, y1)),
              key=lambda p: sum(abs(a - b) for a, b in zip(p, bgc)))
    d = ImageDraw.Draw(im)
    for y in range(y0, y1):                      # tô nền theo từng hàng (giữ dải màu)
        d.line([(x0, y), (x1, y)], fill=im.getpixel((x0 - 8, y)))
    d.text((NUM_RIGHT, NUM_BASE), f'{n:02d}', font=F_NUM, fill=ink, anchor='rs')
    return im

def save_jpg(im, path, q=78):
    im.convert('RGB').save(path, 'JPEG', quality=q, optimize=True, progressive=False)

def encode(src, dst, width, overlay=None, frame_fn=None):
    """Nén lại video H.264 cho PowerPoint; overlay = ảnh PNG (x, y, file) đè cố định."""
    w, h = map(int, subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height', '-of', 'csv=p=0', src]).decode().strip().split(','))
    out_w = min(width, w) // 2 * 2
    out_h = int(round(h * out_w / w / 2)) * 2
    enc_args = ['-c:v', 'libx264', '-profile:v', 'main', '-preset', 'slow', '-crf', '31', '-pix_fmt', 'yuv420p',
                '-r', '30', '-movflags', '+faststart', '-an', dst]
    if frame_fn is None:
        vf = f'scale={out_w}:{out_h}:flags=lanczos'
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', src]
        if overlay:
            ox, oy, png = overlay
            cmd += ['-i', png, '-filter_complex', f'[0:v][1:v]overlay={ox}:{oy},{vf}[v]', '-map', '[v]']
        else:
            cmd += ['-vf', vf]
        subprocess.run(cmd + enc_args, check=True)
        return
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
                            '-r', '30', '-i', '-', '-vf', f'scale={out_w}:{out_h}:flags=lanczos'] + enc_args,
                           stdin=subprocess.PIPE)
    i = 0
    while True:
        b = dec.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        enc.stdin.write(frame_fn(Image.frombytes('RGB', (w, h), b), i).tobytes())
        i += 1
    enc.stdin.close(); enc.wait(); dec.wait()

# ---------- sửa "(trang 6)" -> "(trang 5)", "(trang 7)" -> "(trang 6)" trong video trang giấy tờ ----------
def make_trang_fixer(video):
    last = Image.frombytes('RGB', (1386, 550), subprocess.check_output(
        ['ffmpeg', '-v', 'error', '-sseof', '-0.1', '-i', video, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']))
    fixes = []
    for (dx0, dx1, cx, newd) in ((376, 388, 381.5, '5'), (1164, 1174, 1169.5, '6')):
        reg = (dx0 - 2, 451, dx1 + 1, 471)
        old = last.crop(reg)
        new = old.copy()
        d = ImageDraw.Draw(new)
        for y in range(new.height):
            c1 = new.getpixel((0, y)); c2 = new.getpixel((new.width - 1, y))
            d.line([(0, y), (new.width - 1, y)], fill=tuple((a + b) // 2 for a, b in zip(c1, c2)))
        d.text((cx - reg[0], 468 - reg[1]), newd, font=F_REF, fill=(255, 255, 255), anchor='ms')
        # vùng rộng hơn để ước lượng độ hiện của khung
        probe = (dx0 - 40, 451, dx0 - 5, 471)
        fixes.append((reg, old, new, probe, last.crop(probe)))
    absent = None
    def fn(fr, i):
        nonlocal absent
        for reg, old, new, probe, pref in fixes:
            cur = fr.crop(probe)
            diff = sum(ImageChops.difference(cur, pref).convert('L').get_flattened_data()) / (pref.width * pref.height)
            a = max(0.0, min(1.0, 1 - diff / 100.0))
            if a <= 0.02:
                continue
            region = fr.crop(reg)
            # cộng phần chênh (mới - cũ) theo độ hiện của khung
            delta = ImageChops.subtract(new, old, 1, 128)
            mix = Image.blend(Image.new('RGB', new.size, (128, 128, 128)), delta, a)
            region = ImageChops.add(region, mix, 1, -128)
            fr.paste(region, reg[:2])
        return fr
    return fn

media_dir = P('ppt/media')
done = set()
for idx, slide in enumerate(order, 1):
    x = open(P('ppt/slides', slide), encoding='utf-8').read()
    rmap = rels_of(slide)
    pics = re.findall(r'<p:pic>(.*?)</p:pic>', x, re.S)
    bg_rid = re.search(r'r:embed="(rId\d+)"', pics[0]).group(1)
    bg = rmap[bg_rid]
    vids = []
    for pic in pics[1:]:
        vr = re.search(r'p14:media[^>]*r:embed="(rId\d+)"', pic)
        pr = re.search(r'<a:blip r:embed="(rId\d+)"', pic)
        off = re.search(r'<a:off x="(\d+)" y="(\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', pic)
        full = off and off.group(1) == '0' and off.group(3) == '12192000'
        vids.append((rmap[vr.group(1)], rmap[pr.group(1)] if pr else None, full))
    print(idx, slide, 'nền', bg, 'video', vids)

    # 1) ảnh nền
    im = Image.open(os.path.join(media_dir, bg))
    if idx >= 3:
        im = renumber(im, idx)
    save_jpg(im, os.path.join(media_dir, bg))
    # 2) video + ảnh chờ
    for vid, poster, full in vids:
        vpath = os.path.join(media_dir, vid)
        tmpv = vpath + '.new.mp4'
        if poster:
            pim = Image.open(os.path.join(media_dir, poster))
            if full and idx >= 3 and pim.size == (1600, 900):
                pim = renumber(pim, idx)
            pim = pim.convert('RGB')
            if pim.width > 1600:
                pim = pim.resize((1600, int(pim.height * 1600 / pim.width)), Image.LANCZOS)
            save_jpg(pim, os.path.join(media_dir, poster))
        if full and idx >= 3:
            first = Image.frombytes('RGB', (1600, 900), subprocess.check_output(
                ['ffmpeg', '-v', 'error', '-i', vpath, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']))
            patch = renumber(first, idx).crop(NUM_BOX)
            png = vpath + '.num.png'; patch.save(png)
            encode(vpath, tmpv, 1280, overlay=(NUM_BOX[0], NUM_BOX[1], png))
            os.remove(png)
        elif idx == 4:  # video giấy tờ có '(trang 6)', '(trang 7)'
            encode(vpath, tmpv, 1280, frame_fn=make_trang_fixer(vpath))
        else:
            encode(vpath, tmpv, 1280)
        os.replace(tmpv, vpath)
        done.add(vid)

# 3) ghi chú: tham chiếu trang sau khi bỏ trang 3
for idx, slide in enumerate(order, 1):
    nrel = open(P('ppt/slides/_rels', slide + '.rels'), encoding='utf-8').read()
    m = re.search(r'Target="\.\./notesSlides/([^"]+)"', nrel)
    if not m:
        continue
    npath = P('ppt/notesSlides', m.group(1))
    t = open(npath, encoding='utf-8').read()
    t2 = t.replace('(trang 6)', '(trang 5)').replace('(trang 7)', '(trang 6)')
    if t2 != t:
        open(npath, 'w', encoding='utf-8').write(t2)
        print('sửa ghi chú trang', idx)

# 4) đóng gói lại (nén tối đa phần XML)
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(P('[Content_Types].xml'), '[Content_Types].xml')
    for root, _, files in os.walk(tmp):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, tmp)
            if arc == '[Content_Types].xml':
                continue
            ctype = zipfile.ZIP_STORED if f.lower().endswith(('.mp4', '.jpg', '.jpeg', '.png')) else zipfile.ZIP_DEFLATED
            z.write(full, arc, compress_type=ctype)
shutil.rmtree(tmp)
print('xong', OUT, os.path.getsize(OUT) // 1024, 'KB')
