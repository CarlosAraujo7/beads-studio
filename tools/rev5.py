"""5º pedido (2026-10-31, CLAUDE.md §7.26): só os moldes que ele nomeou. Grava por retoque.gravar (só troca se o molde ainda é o que li).
  python tools/rev5.py          prévia tools/out/r5_0.png (fonte | atual | novo)
  python tools/rev5.py --apply"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import palette as P
from tplfile import parse
import facetools as FT
import rev_fix, retoque
from rev4 import flat, blocks, mirror
L = {c['code']: c['letter'] for c in P.ALL}
BK = lambda f: {t['id']: t for t in parse(os.path.join(HERE, 'backups', f))['items']}
SRC = {'goku-super-saiyajin-blue-aura-pixel': (24, 12), 'shenlong-dragon-ball-chibi-pixel': (24, 16), 'omni-man-invencivel-pixel': (24, 44), 'pennywise-chibi-corpo-inteiro': (24, 62)}


def goku(b):
    # olhos brancos com íris (a arte tem os dois), sobrancelha, sem a boca de dentes
    return blocks(b, [(26, 20, ['kk}}kk']), (27, 22, ['w']), (27, 25, ['gk']), (29, 19, ['tt}}}'])])


def omni(b):
    # têmporas brancas, sobrancelhas finas (a faixa preta inteira parecia máscara), olhos simétricos e bigode caindo nos dois lados
    return blocks(b, [(4, 14, ['kwtttttttttwk']), (5, 14, ['kwtkkktkkktwk']), (6, 14, ['kttwcttÉttcwt k'[:13]]), (7, 14, ['ktttttÉtttttk']),
                      (9, 15, ['Ètktsssskt È'[:11]])])


def penny(b):
    # metade esquerda desenhada da arte (colunas 3 a 14) e espelhada; nariz e um único traço de sorriso, sem dentes
    L_ = [(13, 'oowwwwwrwwww'), (14, 'oowwwwwrwwww'), (15, 'oowwwwwrwwww'), (16, 'oowkkwwrwwww'), (17, 'oowkkkkkkkww'), (18, 'kowykwkkywww'), (19, '.wwykkkkywww'),
          (20, '...wyyyywwww'), (21, '....wwwwwwrr'), (22, '....wrwwwwrr'), (23, '.....wrrwwww'), (24, '.....wwwrrrr'), (25, '....kjjwwwww')]
    g = [list(r) for r in b]
    for y, s in L_:
        for i, c in enumerate(s): g[y][3 + i] = c
    g[26][14] = 'w'
    return mirror([''.join(r) for r in g], 'L', len(b[0]) - 1)


def shen(b):
    # cabeça relida da arte com as cores puras dela (o molde tinha o verde escurecido); o corpo fica
    raw = FT.src_raw(24, 16); geo = FT.align(raw, b, verbose=False)
    pal = [((255, 255, 255), '.'), ((8, 8, 8), 'k'), ((72, 205, 50), L['B4']), ((35, 120, 80), 'h'), ((20, 75, 65), L['B12']), ((110, 75, 45), L['G6']), ((70, 40, 40), L['F10']), ((235, 30, 60), 'r'), ((150, 30, 50), L['E7'])]
    new = flat(raw, geo, len(b[0]), len(b), pal, {'k': 0.5})
    g = [list(r) for r in b]
    for y in range(0, 17):
        for x in range(len(b[0])):
            if x <= 32 and new[y][x] != '.' and b[y][x] != '.': g[y][x] = new[y][x]
    return [''.join(r) for r in g]


def main():
    cur = {t['id']: t for t in parse(os.path.join(ROOT, 'templates.js'))['items']}
    pf = BK('pre-faces.js'); lc = BK('pre-sb-claros.js')
    T = {'goku-super-saiyajin-blue-aura-pixel': goku, 'omni-man-invencivel-pixel': omni, 'pennywise-chibi-corpo-inteiro': penny, 'shenlong-dragon-ball-chibi-pixel': shen}
    new = {i: f(cur[i]['rows']) for i, f in T.items()}
    new['koro-sensei-emblema'] = pf['koro-sensei-emblema']['rows']
    new['koro-sensei-corpo-inteiro'] = pf['koro-sensei-corpo-inteiro']['rows']
    if '--apply' in sys.argv:
        retoque.gravar(new, {i: cur[i]['rows'] for i in new}); return
    from PIL import Image
    pairs = []
    for i, r in new.items():
        s = SRC.get(i)
        pairs.append(('%s %dx%d' % (i[:40], len(r[0]), len(r)), cur[i]['rows'], r, Image.fromarray(FT.src_raw(*s)) if s else None))
    rev_fix.sheet(pairs, os.path.join(HERE, 'out', 'r5_0.png'), H=520)
    print('ok')


if __name__ == '__main__':
    main()
