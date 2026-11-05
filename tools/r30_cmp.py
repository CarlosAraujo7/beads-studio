"""Conferência da revisão (tools/r30_rev.py): para cada molde, ANTES (catálogo) | DEPOIS (data/r30_rev_new.json) do rosto ampliado e o molde inteiro depois, pequeno.
  python tools/r30_cmp.py [tag] ["trecho" ...]   -> tools/out/r30c_<tag>_N.png (4 por folha)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tplfile
from palette import ALL
HEX = {p['letter']: p['hex'] for p in ALL}
OUT = os.path.join(HERE, 'out')
try: FB = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 13)
except Exception: FB = ImageFont.load_default()


def img(rows, px, r0=0, r1=None, c0=0, c1=None):
    r1 = len(rows) if r1 is None else r1; c1 = len(rows[0]) if c1 is None else c1
    im = Image.new('RGB', ((c1 - c0) * px, (r1 - r0) * px), (92, 70, 140)); d = ImageDraw.Draw(im)
    for y in range(r0, r1):
        for x in range(c0, c1):
            c = rows[y][x]
            if c != '.': d.rectangle(((x - c0) * px, (y - r0) * px, (x - c0) * px + px - 1, (y - r0) * px + px - 1), fill=HEX[c])
    return im


def window(rows):
    import r29_exfinal as P
    H, W = len(rows), len(rows[0])
    face, hull, eyes = P._face_eyes(rows)
    if face is None: return 0, min(H, 22), 0, W
    ys, xs = np.nonzero(face)
    return max(0, ys.min() - 6), min(H, ys.max() + 4), max(0, xs.min() - 5), min(W, xs.max() + 6)


def main():
    a = sys.argv[1:]; tag = a[0] if a else 'c'; qs = a[1:]
    cat = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    new = json.load(open(os.path.join(HERE, 'data', 'r30_rev_new.json'), encoding='utf-8'))
    tiles = []
    for n, nr in new.items():
        if qs and not any(q.lower() in n.lower() for q in qs): continue
        old = cat.get(n)
        if old is None: continue
        same = (len(old), len(old[0])) == (len(nr), len(nr[0]))
        r0, r1, c0, c1 = window(nr)
        if same:                                   # mesmo tamanho: a janela é a área que mudou, com folga
            diff = [(y, x) for y in range(len(nr)) for x in range(len(nr[0])) if nr[y][x] != old[y][x]]
            if diff:
                ys = [p[0] for p in diff]; xs = [p[1] for p in diff]
                r0, r1 = max(0, min(ys) - 5), min(len(nr), max(ys) + 6); c0, c1 = max(0, min(xs) - 5), min(len(nr[0]), max(xs) + 6)
        px = max(10, min(18, 300 // max(1, c1 - c0)))
        a_ = img(old, px, r0, r1, c0, c1) if same else img(old, max(3, 300 // len(old)))
        b_ = img(nr, px, r0, r1, c0, c1)
        full = img(nr, 4)
        H = max(a_.height, b_.height, full.height) + 22
        t = Image.new('RGB', (a_.width + b_.width + full.width + 30, H), (32, 32, 38)); d = ImageDraw.Draw(t)
        d.text((4, 2), n[:70], fill=(255, 230, 80), font=FB)
        t.paste(a_, (0, 22)); t.paste(b_, (a_.width + 12, 22)); t.paste(full, (a_.width + b_.width + 26, 22))
        tiles.append(t)
    for f in os.listdir(OUT):
        if f.startswith(f'r30c_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    per = 4
    for s in range(0, len(tiles), per):
        part = tiles[s:s + per]; cols = 2
        Wc = max(t.width for t in part) + 10; Hc = max(t.height for t in part) + 10
        sh = Image.new('RGB', (Wc * cols, Hc * ((len(part) + 1) // cols)), (20, 20, 24))
        for j, t in enumerate(part): sh.paste(t, ((j % cols) * Wc, (j // cols) * Hc))
        sh.save(os.path.join(OUT, f'r30c_{tag}_{s // per}.png'))
    print(len(tiles), 'moldes,', (len(tiles) + per - 1) // per, 'folhas')


if __name__ == '__main__':
    main()
