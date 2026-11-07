from PIL import Image, ImageFont, ImageDraw
im=Image.open('/tmp/claude-0/-home-user-Kcp-video/e3d33cc5-4ce4-5af3-a90a-a3883ae8e915/scratchpad/s40/goc.jpg').convert('RGB')
REG=ImageFont.truetype('/tmp/claude-0/-home-user-Kcp-video/e3d33cc5-4ce4-5af3-a90a-a3883ae8e915/scratchpad/fonts/Nunito-400.ttf',21.8); BLD=ImageFont.truetype('/tmp/claude-0/-home-user-Kcp-video/e3d33cc5-4ce4-5af3-a90a-a3883ae8e915/scratchpad/fonts/Nunito-800.ttf',21.8)
C_REG=(80,90,99); C_BLD=(55,65,74)
d=ImageDraw.Draw(im)
for y in range(286,548):
    d.line([(795,y),(1505,y)],fill=im.getpixel((1540,y)))
X0, XIND, XMAX = 804.5, 828, 1470
def toks(spec):
    # chuỗi có phần in đậm trong **...** -> [(đoạn chữ, đậm, có_cách_trước)]
    chars=[]; b=False; k=0
    while k < len(spec):
        if spec.startswith('**', k): b = not b; k += 2; continue
        chars.append((spec[k], b)); k += 1
    out=[]; cur=''; cb=None; sp=False; prev_space=False
    for ch, bb in chars + [(' ', False)]:
        if ch == ' ':
            if cur: out.append((cur, cb, sp)); cur=''
            prev_space=True; continue
        if cur and bb != cb:
            out.append((cur, cb, sp)); cur=''; sp=False
        if not cur:
            cb=bb; sp=prev_space
        cur += ch; prev_space=False
    return out
def item(num, spec, base):
    d.text((X0,base),num,font=REG,fill=C_REG,anchor='ls')
    x=XIND; y=base; startline=True
    for w,b,sp in toks(spec):
        F=BLD if b else REG
        gap=REG.getlength(' ') if (sp and not startline) else 0
        if not startline and x+gap+F.getlength(w)>XMAX and sp:
            y+=31; x=XIND; gap=0
        x+=gap
        d.text((x,y),w,font=F,fill=C_BLD if b else C_REG,anchor='ls'); x+=F.getlength(w); startline=False
    return y
y=item('2.','Double click vào ô **Truck No**, chọn đúng xe cần làm DC.',314)
y=item('3.','Nhập số seal: **From Seal No** và **To Seal No** đúng dãy seal niêm phong trên xe.',y+43)
y=item('4.','Bấm **Save**, rồi in (**Print**).',y+43)
im.save('/tmp/claude-0/-home-user-Kcp-video/e3d33cc5-4ce4-5af3-a90a-a3883ae8e915/scratchpad/s40/moi.png'); im.crop((760,230,1560,560)).save('/tmp/claude-0/-home-user-Kcp-video/e3d33cc5-4ce4-5af3-a90a-a3883ae8e915/scratchpad/s40/pv.png')
