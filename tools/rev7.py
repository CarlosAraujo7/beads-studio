"""7º pedido (2026-10-31, CLAUDE.md §7.28): cabeça do Omni-Man mais estreita (13 -> 11 contas, a proporção da arte). Só linhas 0-9; o corpo não muda.
  python tools/rev7.py            prévia tools/out/r7v.png (arte | atual | novo, cabeça e inteiro)
  python tools/rev7.py --apply"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
from tplfile import parse
import facetools as FT, palette as P, retoque
from rev4 import blocks
OID = 'omni-man-invencivel-pixel'
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}
L = {c['code']: c['letter'] for c in P.ALL}
N = L['C16']


def omni(b):
    h = [(0, 14, '...kkkk.k....'),
         (1, 14, '..k' + N + N + 'k' + N + 'kkkk..'),
         (2, 14, '.k' + N + 'kk' + N + 'k' + N + 'kk' + N + 'k.'),
         (3, 14, '.k' + N + 'k' + N + 'k' + N + 'k' + N + 'k' + N + 'k.'),
         (4, 14, '.kwtttttttwk.'),
         (5, 14, '.kwkkttt' + 'kkwk.'),
         (6, 14, '.ktwctÉtcwtk.'),
         (7, 14, '.kttttÉttttk.'),
         (8, 14, 'kkÈtkkkkktÈkk'[:12] + '.')]
    r = blocks(b, [(y, x, [s]) for y, x, s in h] + [(3, 27, ['.'])])
    return blocks(r, [(9, 15, ['Èktsssss' + 'tkÈ'])])


def ren(rows, sc):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (len(rows[0]) * sc, len(rows) * sc), (98, 70, 140)); d = ImageDraw.Draw(im)
    for y, l in enumerate(rows):
        for x, c in enumerate(l):
            if c != '.': d.rectangle((x * sc, y * sc, x * sc + sc - 1, y * sc + sc - 1), fill=HEX[c])
    return im


def main():
    cur = {t['id']: t['rows'] for t in parse(os.path.join(ROOT, 'templates.js'))['items']}[OID]
    new = omni(cur)
    if '--apply' in sys.argv: retoque.gravar({OID: new}, {OID: cur}); return
    from PIL import Image
    raw = FT.src_raw(24, 44); ox, oy, cw, ch = FT.align(raw, cur, verbose=False)
    box = (int(ox + 8 * cw), max(0, int(oy - 1 * ch)), int(ox + 33 * cw), int(oy + 15 * ch))
    src = Image.fromarray(raw[box[1]:box[3], box[0]:box[2]]); src = src.resize((25 * 20, src.height * 500 // src.width), Image.LANCZOS)
    ts = [src, ren([l[8:33] for l in cur[:15]], 20), ren([l[8:33] for l in new[:15]], 20), ren(new, 6), Image.fromarray(raw).resize((raw.shape[1] * 300 // raw.shape[0], 300))]
    S = Image.new('RGB', (sum(t.width + 8 for t in ts), max(t.height for t in ts)), (40, 40, 44)); x = 0
    for t in ts: S.paste(t, (x, 0)); x += t.width + 8
    S.save(os.path.join(HERE, 'out', 'r7v.png')); print(S.size)
    print('\n'.join('%2d %s' % (y, l[10:30]) for y, l in enumerate(new[:12])))


if __name__ == '__main__':
    main()
