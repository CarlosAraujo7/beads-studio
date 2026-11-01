"""8º pedido (2026-10-31, CLAUDE.md §7.28): cabeça do Omni-Man com as medidas da arte: 10 contas de largura e 13 de altura (estava 11 x 9), queixo e pescoço separados do tronco, testa rosada e bochechas creme.
O corpo desce 2 linhas; saem 2 linhas repetidas da capa (parte de baixo), para seguir com 50 de altura.
  python tools/rev8.py            prévia tools/out/r8v.png
  python tools/rev8.py --apply"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
from tplfile import parse
import facetools as FT, palette as P, retoque
OID = 'omni-man-invencivel-pixel'
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}
L = {c['code']: c['letter'] for c in P.ALL}
HEAD = {0: (15, '..k.k.....'), 1: (15, '..kkkkkk..'), 2: (15, 'kkNNkNkkNk'), 3: (15, '.kNkkNNkNk'), 4: (14, 'kkNNkNNkNNkk'),
        5: (15, 'kEttBBttEk'), 6: (15, 'kEttttttEk'), 7: (15, 'kmNNSSNNmk'), 8: (15, 'kGwcttcwGk'), 9: (15, 'ktGGSSGGtk'),
        10: (15, 'kkGkkkkGkk'), 11: (14, 'kDDGNkkNGDkk.'), 12: (17, 'kDGGDk-')}


def _drop(rows, k):
    """tira k linhas: as mais parecidas com a seguinte, nunca duas seguidas"""
    cost = sorted((sum(a != b for a, b in zip(rows[i], rows[i + 1])), i) for i in range(len(rows) - 1))
    out = set()
    for _, i in cost:
        if len(out) == k: break
        if i - 1 in out or i + 1 in out: continue
        out.add(i)
    return [r for i, r in enumerate(rows) if i not in out]


def omni(b, skin='G5'):
    M = {'N': L['C16'], 'E': L['E8'], 't': L[skin], 'B': L['F10'], 'S': L['F6'], 'G': L['G2'], 'm': L['H4'], 'c': L['C5'], 'D': L['F7'], '-': L['D14']}
    W = len(b[0])
    # linhas 8+ do corpo descem 2; as 2 linhas repetidas saem da capa (da linha 24 em diante)
    body = b[8:]
    body = body[:16] + _drop(body[16:], 2)
    g = [['.'] * W for _ in range(10)] + [list(r) for r in body]
    assert len(g) == len(b), len(g)
    for x in range(15, W): g[10][x] = '.'                 # o resto da cabeça antiga
    for y, (x0, s) in HEAD.items():
        for i, c in enumerate(s):
            g[y][x0 + i] = M.get(c, c)
    return [''.join(r) for r in g]


def ren(rows, sc):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (len(rows[0]) * sc, len(rows) * sc), (98, 70, 140)); d = ImageDraw.Draw(im)
    for y, l in enumerate(rows):
        for x, c in enumerate(l):
            if c != '.': d.rectangle((x * sc, y * sc, x * sc + sc - 1, y * sc + sc - 1), fill=HEX[c])
    return im


def main():
    cur = {t['id']: t['rows'] for t in parse(os.path.join(ROOT, 'templates.js'))['items']}[OID]
    if '--apply' in sys.argv:
        skin = sys.argv[sys.argv.index('--apply') + 1] if len(sys.argv) > sys.argv.index('--apply') + 1 else 'G5'
        retoque.gravar({OID: omni(cur, skin)}, {OID: cur}); return
    from PIL import Image
    raw = FT.src_raw(24, 44)
    crop = Image.fromarray(raw[40:50 + int(22 * 21.84), 56 + int(4 * 21.84):56 + int(30 * 21.84)]); crop = crop.resize((26 * 18, crop.height * 26 * 18 // crop.width), Image.LANCZOS)
    ts = [crop]
    for sk in ('G5', 'G3', 'G9'):
        r = omni(cur, sk); ts.append(ren([l[6:32] for l in r[:22]], 18))
    r = omni(cur, 'G5'); ts += [ren(r, 8), ren(cur, 8), Image.fromarray(raw).resize((raw.shape[1] * 400 // raw.shape[0], 400))]
    W = 1900; x = y = 6; h = 0; pos = []
    for t in ts:
        if x + t.width + 6 > W: x = 6; y += h + 6; h = 0
        pos.append((x, y)); x += t.width + 6; h = max(h, t.height)
    S = Image.new('RGB', (W, y + h + 6), (40, 40, 44))
    for t, q in zip(ts, pos): S.paste(t, q)
    S.save(os.path.join(HERE, 'out', 'r8v.png')); print(S.size)


if __name__ == '__main__':
    main()
