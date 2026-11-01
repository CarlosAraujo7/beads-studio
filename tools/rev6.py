"""6º pedido (2026-10-31, CLAUDE.md §7.27): rosto do Shenlong e olhos do Goku Blue (de lado: só o olho de perto é inteiro). Grava por retoque.gravar.
  python tools/rev6.py            prévia tools/out/r6v.png
  python tools/rev6.py --apply"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
from tplfile import parse
import facetools as FT
import palette as P
import retoque
from rev4 import blocks
L = {c['code']: c['letter'] for c in P.ALL}
GID, SID = 'goku-super-saiyajin-blue-aura-pixel', 'shenlong-dragon-ball-chibi-pixel'
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}


def goku(b, v='a'):
    # olho de perto inteiro (branco, íris, branco, com a pálpebra e o branco de baixo); o de longe é só a íris, na borda do rosto
    O_ = L['B10']
    return blocks(b, [(26, 20, ['kkkk}kk']), (27, 20, ['tw' + O_ + 'w}' + O_ + 'k']), (28, 19, ['tttw}}k'])])


def shen(b):
    # cabeça desenhada conta a conta sobre a arte: dois olhos vermelhos diferentes (de lado), faixa escura em cima, focinho claro com narina, faixa marrom e boca
    E = L['F8']; G6 = L['G6']
    return blocks(b, [
        (5, 15, ['hLLkLLLhQhhk']),
        (6, 15, ['hhhLLLLLQQhkhk']),
        (7, 15, ['hhhLLLLLLQhkhk']),
        (8, 15, ['hhhLLhhLLLQkLhk']),
        (9, 15, ['QkhLLLLLhLLLLhk']),
        (10, 15, ['khhQhhhhLhLLQLh']),
        (11, 15, ['khhhQQQQhLhLQLk']),
        (12, 15, [G6 + G6 + 'hhh' + E + 'rrhLQLr' + E + 'k']),
        (13, 15, [G6 + G6 + G6 + 'hh' + E + 'rrrQQQr' + E + 'k']),
        (14, 15, ['k' + G6 * 3 + 'hh' + E + 'rrQLLr' + E + 'k']),
        (15, 15, ['Lk' + G6 * 3 + 'hhQLLLkLhk']),
        (16, 15, ['kLk' + G6 * 2 + 'kkhLLLLkhk']),
        (17, 21, ['kkkkQQQQk']),
        (18, 22, [G6 + 'rrwww' + G6 + 'k'])])


def ren(rows, sc, bg=(98, 70, 140)):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (len(rows[0]) * sc, len(rows) * sc), bg); d = ImageDraw.Draw(im)
    for y, l in enumerate(rows):
        for x, c in enumerate(l):
            if c != '.': d.rectangle((x * sc, y * sc, x * sc + sc - 1, y * sc + sc - 1), fill=HEX[c])
    return im


def main():
    cur = {t['id']: t['rows'] for t in parse(os.path.join(ROOT, 'templates.js'))['items']}
    if '--apply' in sys.argv:
        v = sys.argv[sys.argv.index('--apply') + 1] if len(sys.argv) > sys.argv.index('--apply') + 1 else 'a'
        retoque.gravar({GID: goku(cur[GID], v), SID: shen(cur[SID])}, {GID: cur[GID], SID: cur[SID]}); return
    from PIL import Image
    raw = FT.src_raw(24, 12); geo = FT.align(raw, cur[GID], verbose=False); ox, oy, cw, ch = geo
    def crop(raw, geo, r0, r1, c0, c1, sc):
        ox, oy, cw, ch = geo
        return Image.fromarray(raw[max(0, int(oy + r0 * ch)):int(oy + r1 * ch), max(0, int(ox + c0 * cw)):int(ox + c1 * cw)]).resize(((c1 - c0) * sc, (r1 - r0) * sc), Image.LANCZOS)
    tiles = [crop(raw, geo, 18, 34, 12, 30, 20)]
    for v in 'a':
        r = goku(cur[GID], v); tiles.append(ren([l[12:30] for l in r[18:34]], 20)); tiles.append(ren(r, 4))
    raw2 = FT.src_raw(24, 16); geo2 = FT.align(raw2, cur[SID], verbose=False)
    tiles.append(crop(raw2, geo2, 3, 21, 8, 33, 16)); r = shen(cur[SID]); tiles.append(ren([l[8:33] for l in cur[SID][3:21]], 16)); tiles.append(ren([l[8:33] for l in r[3:21]], 16)); tiles.append(ren(r, 6))
    W = 1900; x = y = 6; h = 0; pos = []
    for t in tiles:
        if x + t.width + 6 > W: x = 6; y += h + 6; h = 0
        pos.append((x, y)); x += t.width + 6; h = max(h, t.height)
    S = Image.new('RGB', (W, y + h + 6), (40, 40, 44))
    for t, q in zip(tiles, pos): S.paste(t, q)
    S.save(os.path.join(HERE, 'out', 'r6v.png')); print(S.size)


if __name__ == '__main__':
    main()
