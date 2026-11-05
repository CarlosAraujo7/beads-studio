"""Recorte ampliado com régua (linha/coluna) de moldes do catálogo, para desenhar olhos conta a conta:
  python tools/r30_grid.py tag "trecho|l0|l1|c0|c1" ... [--new] [--codes]
--new usa data/r30_rev_new.json (resultado do tools/r30_rev.py build); --codes escreve o código da cor em cada conta. Saída tools/out/r30g_<tag>_N.png (3 por folha)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import tplfile
from palette import ALL
HEX = {p['letter']: p['hex'] for p in ALL}
CODE = {p['letter']: p['code'] for p in ALL}
OUT = os.path.join(HERE, 'out')
try:
    FNT = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 11); FS = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 9); FB = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 14)
except Exception:
    FNT = FS = FB = ImageFont.load_default()


def ink(hx):
    r, g, b = int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
    return (0, 0, 0) if 0.299 * r + 0.587 * g + 0.114 * b > 140 else (255, 255, 255)


def main():
    a = sys.argv[1:]; tag = a[0]; specs = [x for x in a[1:] if not x.startswith('--')]
    cat = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    if '--new' in a:
        for n, r in json.load(open(os.path.join(HERE, 'data', 'r30_rev_new.json'), encoding='utf-8')).items(): cat[n] = r
    codes = '--codes' in a
    tiles = []
    for sp in specs:
        q, *lim = sp.split('|')
        hits = [n for n in cat if q.lower() in n.lower()]
        if not hits: print('não achado:', q); continue
        n = hits[0]; rows = cat[n]; H, W = len(rows), len(rows[0])
        if len(lim) == 4: r0, r1, c0, c1 = (int(v) for v in lim)
        else:                                  # sem janela: o rosto achado pelo _face_eyes da remessa 29, com folga (4 em cima e dos lados, 3 embaixo)
            import numpy as np, r29_exfinal as P
            face, hull, eyes = P._face_eyes(rows)
            if face is None: r0, r1, c0, c1 = 0, H // 2, 0, W - 1
            else:
                ys, xs = np.nonzero(face); r0, r1, c0, c1 = max(0, ys.min() - 5), ys.max() + 3, max(0, xs.min() - 4), xs.max() + 4
        r1 = min(r1, H - 1); c1 = min(c1, W - 1)
        px = 24; L = 26; T = 36
        im = Image.new('RGB', (L + (c1 - c0 + 1) * px, T + (r1 - r0 + 1) * px), (36, 36, 44)); d = ImageDraw.Draw(im)
        d.text((2, 1), f'{n[:58]}  {W}x{H}', fill=(255, 230, 80), font=FB)
        for x in range(c0, c1 + 1): d.text((L + (x - c0) * px + 5, 19), str(x), fill=(220, 220, 220), font=FNT)
        for y in range(r0, r1 + 1):
            d.text((2, T + (y - r0) * px + 6), str(y), fill=(220, 220, 220), font=FNT)
            for x in range(c0, c1 + 1):
                c = rows[y][x]; X, Y = L + (x - c0) * px, T + (y - r0) * px
                hx = HEX.get(c)
                d.rectangle((X, Y, X + px - 1, Y + px - 1), fill=hx if hx else (92, 70, 140), outline=(70, 70, 80))
                if codes and hx: d.text((X + 2, Y + 7), CODE[c], fill=ink(hx), font=FS)
        tiles.append(im)
    per = 3
    for f in os.listdir(OUT):
        if f.startswith(f'r30g_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for s in range(0, len(tiles), per):
        part = tiles[s:s + per]
        sh = Image.new('RGB', (sum(t.width for t in part) + 10 * len(part), max(t.height for t in part)), (20, 20, 24)); x = 0
        for t in part: sh.paste(t, (x, 0)); x += t.width + 10
        sh.save(os.path.join(OUT, f'r30g_{tag}_{s // per}.png'))
    print(len(tiles), 'recortes')


if __name__ == '__main__':
    main()
