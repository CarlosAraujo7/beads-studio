"""Prévias da remessa 31: mosaico com TODOS os moldes de data/final33_120.json (o que vai para o catálogo), cada um com o nome embaixo (fundo roxo: as contas claras aparecem).
    python tools/r31_prev.py [--per 40] [--cols 8] [--px 5] [--tag moldes] [--src]
Saída: tools/out/remessa31_<tag>_N.png. Com --src, cada tile leva a imagem de origem ao lado do molde (só para os de ilustração/folha, que têm a caixa no CFG); sem, só o molde.
Não toca em nada do catálogo: lê só o JSON."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
from PIL import Image, ImageDraw, ImageFont
from palette import ALL

HEX = {p['letter']: p['hex'] for p in ALL}
try: FNT = ImageFont.truetype('arial.ttf', 11)
except Exception: FNT = ImageFont.load_default()


def tile(name, rows, px, W, H):
    w, h = len(rows[0]) * px, len(rows) * px
    t = Image.new('RGB', (W, H), (40, 40, 46)); d = ImageDraw.Draw(t)
    mold = Image.new('RGB', (w, h), (92, 70, 140)); md = ImageDraw.Draw(mold)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.': md.rectangle((x * px, y * px, x * px + px - 1, y * px + px - 1), fill=HEX[c])
    t.paste(mold, ((W - w) // 2, 2))
    lab = name if len(name) <= 38 else name[:36] + '…'
    d.text((3, H - 30), lab.encode('ascii', 'replace').decode(), fill=(255, 255, 0), font=FNT)
    d.text((3, H - 16), f'{len(rows[0])}x{len(rows)}', fill=(190, 190, 200), font=FNT)
    return t


def main():
    a = sys.argv[1:]; per = 40; cols = 8; px = 5; tag = 'moldes'
    for opt in ('--per', '--cols', '--px', '--tag'):
        if opt in a:
            k = a.index(opt); v = a[k + 1]; del a[k:k + 2]
            if opt == '--per': per = int(v)
            elif opt == '--cols': cols = int(v)
            elif opt == '--px': px = int(v)
            else: tag = v
    data = json.load(open(os.path.join(HERE, 'data', 'final33_120.json'), encoding='utf-8'))
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.startswith(f'remessa31_{tag}_') and f.endswith('.png'): os.remove(os.path.join(out, f))
    W = 50 * px + 8; H = 50 * px + 36
    k = 0
    for s in range(0, len(data), per):
        grp = data[s:s + per]; rws = (len(grp) + cols - 1) // cols
        sh = Image.new('RGB', (cols * (W + 4) + 4, rws * (H + 4) + 4), (24, 24, 28))
        for i, (n, g, rows, *_r) in enumerate(grp):
            sh.paste(tile(n, rows, px, W, H), (4 + (i % cols) * (W + 4), 4 + (i // cols) * (H + 4)))
        pth = os.path.join(out, f'remessa31_{tag}_{k + 1}.png'); sh.save(pth); k += 1
        print(pth, sh.size, len(grp), 'moldes')


if __name__ == '__main__':
    main()
