"""Folha geral da revisão da remessa 30 (tools/r30_rev.py): para cada molde, o rosto ANTES (catálogo) | DEPOIS (data/r30_rev_new.json), na mesma janela.
  python tools/r30_overview.py [saída.png] [--cols 5] [--px 7]"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
from PIL import Image, ImageDraw, ImageFont
import tplfile
from palette import ALL
HEX = {p['letter']: p['hex'] for p in ALL}
try: FB = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 12)
except Exception: FB = ImageFont.load_default()


def draw(rows, px, r0, r1, c0, c1):
    im = Image.new('RGB', ((c1 - c0) * px, (r1 - r0) * px), (92, 70, 140)); d = ImageDraw.Draw(im)
    for y in range(r0, r1):
        for x in range(c0, c1):
            c = rows[y][x]
            if c != '.': d.rectangle(((x - c0) * px, (y - r0) * px, (x - c0) * px + px - 1, (y - r0) * px + px - 1), fill=HEX[c])
    return im


def main():
    a = sys.argv[1:]; cols = 5; px = 9
    if '--cols' in a: k = a.index('--cols'); cols = int(a[k + 1]); del a[k:k + 2]
    if '--px' in a: k = a.index('--px'); px = int(a[k + 1]); del a[k:k + 2]
    out = a[0] if a else os.path.join(HERE, 'out', 'r30_revisao_antes_depois.png')
    cat = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    applied = os.path.join(HERE, 'data', 'r30_rev_applied.json')
    olds = {n: v['old'] for n, v in json.load(open(applied, encoding='utf-8')).items()} if os.path.exists(applied) else {}
    new = json.load(open(os.path.join(HERE, 'data', 'r30_rev_new.json'), encoding='utf-8'))
    tiles = []
    for n, nr in new.items():
        old = olds.get(n) or cat.get(n)
        if old is None: continue
        H, W = len(nr), len(nr[0])
        if (len(old), len(old[0])) == (H, W):
            diff = [(y, x) for y in range(H) for x in range(W) if nr[y][x] != old[y][x]]
            if not diff: continue
            ys = [p[0] for p in diff]; xs = [p[1] for p in diff]
            r0, r1 = max(0, min(ys) - 4), min(H, max(ys) + 5); c0, c1 = max(0, min(xs) - 4), min(W, max(xs) + 5)
            if r1 - r0 < 14: r0 = max(0, r0 - (14 - (r1 - r0)) // 2); r1 = min(H, r0 + 14)
            if c1 - c0 < 18: c0 = max(0, c0 - (18 - (c1 - c0)) // 2); c1 = min(W, c0 + 18)
            A = draw(old, px, r0, r1, c0, c1); B = draw(nr, px, r0, r1, c0, c1)
        else:
            A = draw(old, 4, 0, len(old), 0, len(old[0])); B = draw(nr, 4, 0, H, 0, W)
        t = Image.new('RGB', (A.width + B.width + 18, max(A.height, B.height) + 20), (32, 32, 38)); d = ImageDraw.Draw(t)
        d.text((3, 2), n.split(' (')[0][:34], fill=(255, 230, 80), font=FB)
        t.paste(A, (0, 20)); t.paste(B, (A.width + 18, 20))
        d.text((A.width + 3, 20 + A.height // 2 - 6), '>', fill=(255, 255, 255), font=FB)
        tiles.append(t)
    maxw = 2400                                   # empacota em fileiras (os moldes reconvertidos inteiros são mais largos)
    rows_t, cur, w = [], [], 0
    for t in tiles:
        if cur and w + t.width + 10 > maxw: rows_t.append(cur); cur, w = [], 0
        cur.append(t); w += t.width + 10
    if cur: rows_t.append(cur)
    H = sum(max(t.height for t in r) + 10 for r in rows_t)
    sh = Image.new('RGB', (maxw, H), (20, 20, 24)); y = 0
    for r in rows_t:
        x = 5
        for t in r: sh.paste(t, (x, y + 5)); x += t.width + 10
        y += max(t.height for t in r) + 10
    sh.save(out); print(len(tiles), 'moldes ->', out, sh.size)


if __name__ == '__main__':
    main()
