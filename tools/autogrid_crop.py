"""autogrid.py numa CAIXA da imagem de uma remessa: recorta (x0,y0,x1,y1 em pixels), acha a grade pelo recorte e grava a sobreposição do recorte inteiro com as linhas.
uso:  python tools/autogrid_crop.py REMESSA IDX x0,y0,x1,y1 [--pmin 6] [--pmax 60] [--out ov.png] [--scale 2]
Imprime  crop_img=(x0,y0,x1,y1), px=dict(px=…, py=…, ox=…, oy=…, W=…, H=…)  já para colar no CFG (a grade é do RECORTE: no exact6/E o crop_img vem antes do px).
Confira a sobreposição: a 1ª e a última linha/coluna do desenho têm que cair nas linhas da grade (CLAUDE.md §7.37)."""
import os, sys, glob, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
import autogrid as AG

ap = argparse.ArgumentParser(); ap.add_argument('rem'); ap.add_argument('idx', type=int); ap.add_argument('box'); ap.add_argument('--pmin', type=float, default=6); ap.add_argument('--pmax', type=float, default=60)
ap.add_argument('--out'); ap.add_argument('--scale', type=float, default=2.0); ap.add_argument('--roi')
a = ap.parse_args()
files = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa ' + a.rem, '*.*')))
x0, y0, x1, y1 = [int(v) for v in a.box.split(',')]
im = Image.open(files[a.idx]).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB').crop((x0, y0, x1, y1))
tmp = os.path.join(HERE, 'out', '_agc_%s_%d.png' % (a.rem, a.idx)); im.save(tmp)
roi = tuple(int(v) for v in a.roi.split(',')) if a.roi else None
r = AG.autogrid(tmp, roi, a.pmin, a.pmax)
print('crop_img=(%d, %d, %d, %d), px=dict(px=%s, py=%s, ox=%s, oy=%s, W=%s, H=%s)   # score %s, recorte %s' % (x0, y0, x1, y1, r['px'], r['py'], r['ox'], r['oy'], r['W'], r['H'], r['score'], r['size']))
out = a.out or os.path.join(HERE, 'out', 'agc_%s_%d.png' % (a.rem, a.idx))
ov = im.copy(); d = ImageDraw.Draw(ov)
for i in range(r['W'] + 1): d.line([(r['ox'] + i * r['px'], 0), (r['ox'] + i * r['px'], im.size[1])], fill=(255, 0, 255), width=1)
for j in range(r['H'] + 1): d.line([(0, r['oy'] + j * r['py']), (im.size[0], r['oy'] + j * r['py'])], fill=(255, 0, 255), width=1)
if a.scale != 1: ov = ov.resize((int(ov.width * a.scale), int(ov.height * a.scale)), Image.NEAREST)
ov.save(out); print('sobreposição:', out)
