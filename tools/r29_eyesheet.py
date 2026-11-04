"""Folha de LEITURA de rosto da remessa 29 ALINHADA com a grade do convert6 (sem o desalinho do facetools.align):
esquerda = a arte recortada exatamente nas contas do molde, com a grade e a régua; direita = o molde com o código de cada conta.
  BEADPAL=120 python tools/r29_eyesheet.py "trecho do nome" r0 r1 c0 c1 [px] [saída.png]          (r1/c1 exclusivos)
O molde mostrado é o da conversão de agora (o mesmo fn() do CFG, com os retoques de TOUCH6), então serve para conferir um retoque antes de gravar."""
import os, sys, json
os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import r29_exfinal as Z
import illus6
from palette import ALL

HEX = {c['letter']: c['hex'] for c in ALL}; CODE = {c['letter']: c['code'] for c in ALL}


def offset(big, small):
    """(dy, dx) em que o molde final `small` mais coincide (contas não vazias iguais) com a saída `big` do convert6"""
    Hb, Wb, Hs, Ws = len(big), len(big[0]), len(small), len(small[0])
    B = np.array([list(r) for r in big]); S = np.array([list(r) for r in small]); sm = S != '.'
    best = (-1, 0, 0)
    for dy in range(0, max(1, Hb - Hs + 1)):
        for dx in range(0, max(1, Wb - Ws + 1)):
            sub = B[dy:dy + Hs, dx:dx + Ws]
            if sub.shape != S.shape: continue
            sc = int(((sub == S) & sm).sum())
            if sc > best[0]: best = (sc, dy, dx)
    return best[1], best[2]


def sheet(name, r0, r1, c0, c1, px=30, out=None):
    n, g, idx, fn, grp = next(c for c in Z.CFG if name.lower() in c[0].lower())
    Z.CUR[0] = n
    rows = Z.touch6(n, fn())
    G = dict(illus6.LAST_GEOM)
    dy, dx = offset(G['rows'], rows)          # o molde final pode ter perdido linhas/colunas depois do convert6 (peça solta, marca d'água): onde ele fica na saída do convert6
    box = getattr(fn, 'box', None)
    src = Z.R.illus._load(Z.F[idx], box)
    r1 = min(r1, len(rows)); c1 = min(c1, len(rows[0]))
    cw, ch = G['w'] / G['nw'], G['h'] / G['nh']
    def pix(r, c):            # canto da conta (r, c) do molde final na imagem
        return G['x0'] + (c + dx + G['left'] - 1) * cw, G['y0'] + (r + dy + G['top'] - 1) * ch
    xa, ya = pix(r0, c0); xb, yb = pix(r1, c1)
    W, H = (c1 - c0) * px, (r1 - r0) * px
    crop = Image.fromarray(src).crop((int(round(xa)), int(round(ya)), int(round(xb)), int(round(yb)))).resize((W, H), Image.LANCZOS)
    pad = 26
    im = Image.new('RGB', (2 * W + 3 * pad, H + 2 * pad), (40, 40, 46)); d = ImageDraw.Draw(im)
    try: fnt = ImageFont.truetype('arial.ttf', max(9, px // 3))
    except Exception: fnt = ImageFont.load_default()
    im.paste(crop, (pad, pad))
    for k in range(r1 - r0 + 1): d.line([(pad, pad + k * px), (pad + W, pad + k * px)], fill=(255, 0, 255), width=1)
    for k in range(c1 - c0 + 1): d.line([(pad + k * px, pad), (pad + k * px, pad + H)], fill=(255, 0, 255), width=1)
    ox = 2 * pad + W
    for y in range(r0, r1):
        for x in range(c0, c1):
            chr_ = rows[y][x]; X, Y = ox + (x - c0) * px, pad + (y - r0) * px
            if chr_ == '.': d.rectangle([X, Y, X + px - 1, Y + px - 1], outline=(70, 70, 76)); continue
            hx = HEX[chr_]; d.rectangle([X, Y, X + px - 2, Y + px - 2], fill=hx)
            lum = int(hx[1:3], 16) * .3 + int(hx[3:5], 16) * .59 + int(hx[5:7], 16) * .11
            d.text((X + 2, Y + px // 3), CODE[chr_], fill=(0, 0, 0) if lum > 120 else (255, 255, 255), font=fnt)
    for y in range(r0, r1):
        d.text((3, pad + (y - r0) * px + px // 3), str(y), fill=(255, 255, 0), font=fnt)
        d.text((ox - pad + 3, pad + (y - r0) * px + px // 3), str(y), fill=(255, 255, 0), font=fnt)
    for x in range(c0, c1):
        d.text((pad + (x - c0) * px + px // 4, 6), str(x), fill=(255, 255, 0), font=fnt)
        d.text((ox + (x - c0) * px + px // 4, 6), str(x), fill=(255, 255, 0), font=fnt)
    out = out or os.path.join(HERE, 'out', 'r29_eyes.png')
    im.save(out)
    return out, rows


if __name__ == '__main__':
    a = sys.argv[1:]
    px = int(a[5]) if len(a) > 5 else 30
    o, rows = sheet(a[0], *[int(v) for v in a[1:5]], px=px, out=a[6] if len(a) > 6 else None)
    print(o, len(rows[0]), 'x', len(rows))
