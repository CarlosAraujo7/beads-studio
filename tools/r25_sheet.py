"""Folha de LEITURA de rosto da remessa 25: arte com a grade das contas | molde com a mesma grade e régua. Lê o molde do CATÁLOGO (com as edições dele).
  BEADPAL=120 python tools/r25_sheet.py "trecho do nome" r0 r1 c0 c1 [célula] [saida.png] [--new arquivo.json]"""
import os, sys, json
os.environ['REMNUM'] = '25'; os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r25_exfinal as X
import facetools as FT
import palette as P
from tplfile import parse
from PIL import Image, ImageDraw
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}


def sheet(key, r0, r1, c0, c1, cell=26, out=None, rows=None, idx=None, verbose=True):
    if rows is None:
        t = next(x for x in parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items'] if key.lower() in x['name'].lower())
        n, rows = t['name'], t['rows']
    else:
        n = key
    if idx is None: idx = next(c[2] for c in X.CFG if key.lower() in c[0].lower())
    raw = FT.src_raw(25, idx)
    ox, oy, cw, ch = FT.align(raw, rows, verbose=verbose)
    W, H = (c1 - c0 + 1) * cell, (r1 - r0 + 1) * cell
    crop = Image.fromarray(raw).crop((int(ox + c0 * cw), int(oy + r0 * ch), int(ox + (c1 + 1) * cw), int(oy + (r1 + 1) * ch))).resize((W, H), Image.NEAREST)
    m = Image.new('RGB', (W, H), (98, 70, 140)); d = ImageDraw.Draw(m)
    for y in range(r0, r1 + 1):
        for x in range(c0, c1 + 1):
            c_ = rows[y][x] if y < len(rows) and x < len(rows[y]) else '.'
            if c_ != '.': d.rectangle(((x - c0) * cell, (y - r0) * cell, (x - c0 + 1) * cell - 1, (y - r0 + 1) * cell - 1), fill=HEX[c_])
    for im in (crop, m):
        d = ImageDraw.Draw(im)
        for x in range(c0, c1 + 2): d.line([((x - c0) * cell, 0), ((x - c0) * cell, H)], fill=(255, 255, 255), width=1)
        for y in range(r0, r1 + 2): d.line([(0, (y - r0) * cell), (W, (y - r0) * cell)], fill=(255, 255, 255), width=1)
        for x in range(c0, c1 + 1): d.text(((x - c0) * cell + 2, 1), str(x), fill=(255, 255, 0))
        for y in range(r0, r1 + 1): d.text((1, (y - r0) * cell + 2), str(y), fill=(0, 255, 255))
    S = Image.new('RGB', (W * 2 + 10, H), (40, 40, 44)); S.paste(crop, (0, 0)); S.paste(m, (W + 10, 0))
    if out: S.save(out)
    if verbose:
        print(n, len(rows[0]), len(rows)); print('\n'.join('%2d %s' % (y, rows[y][c0:c1 + 1]) for y in range(r0, min(r1 + 1, len(rows)))))
    return S


if __name__ == '__main__':
    a = sys.argv
    sheet(a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]) if len(a) > 6 else 26, a[7] if len(a) > 7 else os.path.join(HERE, 'out', 'r25_face.png'))
