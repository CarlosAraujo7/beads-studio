"""Consertos da 3ª revisão (ver rev3.py). Um fix3 por molde. Princípio: LER a arte (flat), não carimbar olho inventado."""
import numpy as np
from collections import Counter
from rev3 import fix3, flat, blocks, L
import facetools as FT
import palette as P
import weak_fix as WF
import loose

HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}


def region(rows, new, r0, r1, c0, c1):
    """copia `new` para `rows` só no retângulo (inclusive) e só onde `rows` não é vazio: a silhueta não muda"""
    g = [list(r) for r in rows]
    for y in range(max(0, r0), min(len(g), r1 + 1)):
        for x in range(max(0, c0), min(len(g[0]), c1 + 1)):
            if g[y][x] != '.': g[y][x] = new[y][x]
    return [''.join(r) for r in g]


def face(rows, src, pal, boxes, prio=None):
    """relê da fonte só os retângulos `boxes`, com a paleta chapada `pal`"""
    raw = FT.src_raw(*src); geo = FT.align(raw, rows, verbose=False)
    new = flat(raw, geo, len(rows[0]), len(rows), pal, prio)
    for b in boxes: rows = region(rows, new, *b)
    return rows


def recolor(rows, r0, r1, c0, c1, frm, to):
    g = [list(r) for r in rows]
    for y in range(max(0, r0), min(len(g), r1 + 1)):
        for x in range(max(0, c0), min(len(g[0]), c1 + 1)):
            if g[y][x] in frm: g[y][x] = to
    return [''.join(r) for r in g]


def despeck(rows, letter, into, need=3):
    """conta `letter` sem nenhuma vizinha igual (4 lados) e com >= need vizinhas `into` vira `into` (risco de chuva, brilho solto)"""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    for y in range(H):
        for x in range(W):
            if rows[y][x] != letter: continue
            nb = [rows[yy][xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < H and 0 <= xx < W]
            if letter not in nb and nb.count(into) >= need: g[y][x] = into
    return [''.join(r) for r in g]


# ------------------------------------------------------------------ brasões: ponto-cruz de 26x33 células; cada célula é relida só com as 3 cores daquele brasão, moldura igual à aprovada
BOX = {'Grifinória': (25, 12, 240, 280), 'Lufa-Lufa': (323, 13, 537, 280), 'Sonserina': (26, 430, 240, 700), 'Corvinal': (323, 430, 537, 700)}
SRC = {'Grifinória': [(240, 55, 30), (240, 200, 15), (225, 228, 230)],
       'Lufa-Lufa': [(15, 28, 15), (240, 195, 15), (225, 228, 230)],
       'Sonserina': [(12, 120, 85), (165, 172, 172), (238, 238, 236)],
       'Corvinal': [(25, 65, 140), (135, 212, 225), (240, 240, 238)]}
CREST_TOUCH = {'Sonserina': [(9, 6, ['ii']), (10, 5, ['ii']), (11, 6, ['i'])],                 # língua bifurcada (traço fino)
               'Corvinal': [(25, 18, ['i']), (26, 10, ['ii'])],                                # garra e ponta da asa
               'Lufa-Lufa': [(6, 9, ['i']), (7, 5, ['i']), (8, 5, ['i']), (9, 6, ['i']), (11, 8, ['iii']), (9, 11, ['ii'])]}   # contorno fino da cabeça do texugo
CREST_PRIO = {'Lufa-Lufa': 0.26}


def crest(house):
    def fn(b):
        raw = FT.src_raw(20, 11)
        inner = [r[4:-4] for r in b[4:-4]]                                  # sem a moldura (3 + 1 de margem)
        H, W = len(inner), len(inner[0])
        cnt = Counter(c for r in inner for c in r if c not in '.' and c != L['H12'])
        tops = [l for l, _ in cnt.most_common(3)]
        x0, y0, x1, y1 = BOX[house]; geo = (float(x0), float(y0), (x1 - x0) / float(W), (y1 - y0) / float(H))
        pal = []
        for rgb in SRC[house]:
            pal.append((rgb, min(tops, key=lambda t: sum((a - c) ** 2 for a, c in zip(HEX[t], rgb)))))
        pal.append(((255, 255, 255), '.'))
        new = flat(raw, geo, W, H, pal, {tops[2]: CREST_PRIO[house]} if house in CREST_PRIO else None)
        BG = ('.', L['H12']); edge = pal[0][1]; white = pal[2][1]
        def _at_edge(y, x):
            return any(not (0 <= yy < H and 0 <= xx < W) or inner[yy][xx] in BG for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)))
        new = [''.join(inner[y][x] if inner[y][x] in BG else (edge if c == '.' or (c == white and _at_edge(y, x)) else c) for x, c in enumerate(r)) for y, r in enumerate(new)]
        if house in CREST_TOUCH: new = blocks(new, CREST_TOUCH[house])
        g = [list(r) for r in new]
        for y in range(H):
            for x in range(W):
                if g[y][x] == L['H12']: g[y][x] = '.'
        out = WF._frame(g, 3, [L['F10'], L['G6'], L['G13']], L['H12'], 1, False)
        return [''.join(r) for r in out]
    return fn


for _h in BOX:
    fix3('Brasão da %s (escudo)' % _h, crest(_h), (20, 11, tuple(BOX[_h])))


# ------------------------------------------------------------------ logo: sem fundo preto; só o azul, o amarelo e os arcos finos
def trompa(b):
    raw = FT.src_raw(22, 30)
    m = raw.max(axis=2) > 70
    ys, xs = np.nonzero(m); w = xs.max() + 1 - xs.min(); h = ys.max() + 1 - ys.min()
    S = max(w, h) / 50.0; W = int(np.ceil(w / S)); H = int(np.ceil(h / S))
    geo = (float(xs.min()), float(ys.min()), S, S)
    pal = [((26, 26, 28), '.'), ((5, 80, 170), '4'), ((60, 130, 200), '3'), ((255, 240, 0), 'y'), ((250, 240, 170), 'j')]
    return flat(raw, geo, W, H, pal, {'y': 0.34, '4': 0.34, 'j': 0.12, '3': 0.12})


fix3('Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)', trompa, (22, 30, None))


# ------------------------------------------------------------------ casal da ilustração: cores chapadas da arte, contorno preto só onde há traço
def casal_ilus(b):
    raw = FT.src_raw(22, 19)
    geo = FT.align(raw, b, verbose=False)
    pal = [((255, 255, 255), '.'), ((15, 15, 15), 'k'), ((242, 236, 95), L['A15']), ((255, 250, 110), L['A15']), ((245, 196, 145), L['A12']), ((236, 226, 196), L['H12']), ((142, 138, 50), L['B1']), ((62, 62, 62), L['H6']), ((90, 60, 30), L['G7'])]
    return flat(raw, geo, len(b[0]), len(b), pal, {'k': 0.3})


fix3('Casal sob o guarda-chuva amarelo (How I Met Your Mother, ilustração)', casal_ilus, (22, 19, None))


# ------------------------------------------------------------------ casal na chuva: formas chapadas, céu liso; olhos só com o ponto preto
def casal_chuva(b):
    raw = FT.src_raw(22, 11)
    geo = (0.0, 0.0, raw.shape[1] / float(len(b[0])), raw.shape[0] / float(len(b)))
    pal = [((125, 165, 215), 'b'), ((15, 15, 18), 'k'), ((245, 220, 10), 'y'), ((190, 120, 5), 'a'), ((250, 195, 170), L['A12']), ((125, 45, 35), L['F8']), ((215, 160, 100), L['G9']), ((250, 248, 248), 'w'), ((150, 150, 150), 'm'), ((150, 80, 50), L['G6'])]
    r = flat(raw, geo, len(b[0]), len(b), pal, {'k': 0.42})
    r = despeck(r, 'w', 'b', 2)
    return blocks(r, [(22, 7, ['kkkkkkk', ' FFFFF', ' FkFkF', ' FFFFF', ' FFFF', '  FF']),
                      (25, 24, ['FF', 'FkFk', 'FFFF', 'FFF', ' FF', ' FF', ' FF'])], {'F': 'A12'})


fix3('Casal sob o guarda-chuva amarelo na chuva (How I Met Your Mother)', casal_chuva, (22, 11, None))


# ------------------------------------------------------------------ Sanemi: o verde vivo B3 saltava; íris no verde-petróleo escuro B7
def sanemi(b):
    return recolor(b, 15, 19, 14, 32, ['g'], L['B7'])


fix3('Sanemi Shinazugawa (Demon Slayer, chibi, adesivo)', sanemi, (22, 94, None))


# ------------------------------------------------------------------ Goku: releitura chapada; preto só onde ele é MAIORIA da conta (a anterior era traço fino engrossado)
GOKU = [((15, 15, 20), 'k'), ((240, 242, 248), 'w'), ((190, 198, 215), 'i'), ((120, 135, 175), L['D17']), ((248, 205, 170), L['G2']), ((222, 150, 112), 't'), ((240, 120, 40), 'o'), ((190, 60, 30), L['F13']), ((35, 70, 125), L['C16']), ((170, 120, 215), L['D18'])]


def peel_white(rows, n=2):
    # tira o halo branco de adesivo: branco que encosta no vazio, n passadas
    for _ in range(n):
        g = [list(r) for r in rows]; H, W = len(g), len(g[0])
        for y in range(H):
            for x in range(W):
                if rows[y][x] in 'wi':
                    nb = [rows[yy][xx] if 0 <= yy < H and 0 <= xx < W else '.' for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))]
                    if '.' in nb: g[y][x] = '.'
        rows = [''.join(r) for r in g]
    return rows


def goku(b):
    raw = FT.src_raw(22, 55); geo = FT.align(raw, b, verbose=False)
    new = flat(raw, geo, len(b[0]), len(b), GOKU, {'k': 0.42})
    r = peel_white(region(b, new, 0, len(b) - 1, 0, len(b[0]) - 1), 2)
    return blocks(r, [(19, 9, ['GGGGGGGGGG', 'kkGGGGGGkk', 'GkkkGGkkkG', 'GwikGGkiwG', 'GGGGGtGGGG', 'GGGGkkGGGG', 'GGGGGGGGGG'])], {'G': 'G2'})


fix3('Goku (Instinto Superior, chibi, adesivo)', goku, (22, 55, None))


# ------------------------------------------------------------------ Alucard adesivo: a partir do molde de antes da revisão, com o rosto LIDO da arte
ALU = [((12, 12, 14), 'k'), ((255, 228, 210), L['E11']), ((245, 180, 160), L['E1']), ((235, 70, 25), L['F4']), ((205, 15, 20), 'r'), ((255, 255, 255), 'w')]


def alucard(b):
    from tplfile import parse
    import os
    pre = {t['name']: t['rows'] for t in parse(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups', 'pre-rev.js'))['items']}
    base = pre['Alucard (Hellsing, chibi, adesivo)']
    return blocks(base, [(13, 16, ['kkk}kkkkkkk}kkk', '}kkkk}}k}}kkkk}', '}wAAA}}}}}AAAw}', '}}AkA}}}}}AkA}}', '}}}}}}}}}}}}}}}', '}}}kkkkkkkkk}}}', '}}}}wwwwwww}}}}', 'k}}}}kkkkk}}}}k'])], {'A': 'F4'})


fix3('Alucard (Hellsing, chibi, adesivo)', alucard, (23, 36, None))


# ------------------------------------------------------------------ Stark, Beatrice, Emilia: olhos MENORES (no máximo 4x3-4), lidos da posição da arte
def stark(b):
    r = recolor(b, 15, 18, 6, 12, ['k', 'w', 'r'], '}')
    r = recolor(r, 15, 18, 16, 21, ['k', 'w', 'r'], '}')
    return blocks(r, [(15, 7, ['rrkkk']), (16, 7, ['}wrkw']), (17, 7, ['}}rr}']),
                      (15, 16, ['kkkkr']), (16, 16, ['wrkw}']), (17, 16, ['}rr}}'])])


fix3('Stark (Frieren, chibi)', stark, (23, 34, None))


def beatrice(b):
    r = recolor(b, 16, 21, 15, 21, ['k', 'b', 'c', 'w', 'e', L['E15']], L['E14'])
    r = recolor(r, 16, 21, 26, 32, ['k', 'b', 'c', 'w', 'e', L['E15']], L['E14'])
    return blocks(r, [(18, 16, ['kkkk', 'bbwb', 'bccb', ' bb ']), (17, 27, ['kkkk', 'bbwb', 'bccb', ' bb '])])


fix3('Beatrice (Re:Zero, chibi)', beatrice, (23, 3, None))


def emilia(b):
    r = recolor(b, 14, 18, 12, 17, ['k', 'u', 'v', 'w'], '}')
    r = recolor(r, 13, 17, 20, 24, ['k', 'u', 'v', 'w'], '}')
    v, u = L['D6'], L['D7']
    return blocks(r, [(15, 13, ['kkkk', 'uuwu', 'uvvu', ' uu ']), (14, 21, ['kkkk', 'uuwu', 'uvvu', ' uu '])])


fix3('Emilia (Re:Zero, chibi, adesivo)', emilia, (23, 12, None))


# ------------------------------------------------------------------ Yu Yu Hakusho: olhos pequenos desenhados nas posições medidas na arte (' ' não mexe)
fix3('Yusuke Urameshi (Yu Yu Hakusho, pose)', lambda b: blocks(b, [
    (15, 11, ['}wÕkw}}wÕkw}', '}}ÕÕ}}}}ÕÕ}}', '}}}}}}}}}}}']), (19, 16, ['}   }'])]), (22, 38, None))
fix3('Kazuma Kuwabara (Yu Yu Hakusho, espada espiritual)', lambda b: blocks(b, [
    (10, 16, ['kkkk}kkkk', '}wk}}}kw}'])]), (22, 45, None))
_RO = lambda i: [' kk ', 'kw%sk' % i, 'k%s%sk' % (i, i), ' kk ']
fix3('Koenma (Yu Yu Hakusho, chibi)', lambda b: blocks(recolor(recolor(b, 19, 22, 6, 10, ['k', 'w', 'n'], L['E11']), 19, 22, 13, 17, ['k', 'w', 'n'], L['E11']), [
    (19, 6, _RO('n')), (19, 13, _RO('n'))]), (22, 96, None))
fix3('Yusuke Urameshi (Yu Yu Hakusho, chibi, folha)', lambda b: blocks(b, [(15, 0, [
    ' kkookookkkkookooÉÉkk ',
    ' kkoookookkookooo@@kkk',
    ' k@ookkkkookkkkoo@@kkk',
    ' k@oowÉÉwoowÉÉwoo@@kkk',
    ' kkoowÉkwoowkÉwoo@@kk ',
    '  koooÉÉooooÉÉooo@kk  ',
    '   kooooookkooooo@kk  ',
    '    kookkkkkkkkko@k   ',
    '     kowwkwwkwwok     '])], {'@': 'E1'}), (22, 16, (30, 20, 185, 325)))
fix3('Keiko Yukimura (Yu Yu Hakusho, chibi, folha)', lambda b: blocks(recolor(b, 17, 21, 9, 12, ['k', 'w', L['F8']], L['A12']), [
    (17, 9, ['kkkk', 'kÉÉk', 'wÉÉÉ', 'wÉwÉ', 'FÉÉF']), (18, 17, ['ÉÉ ', 'ÉÉw', 'ÉwÉ', 'ÉÉF']), (24, 16, ['ÉF'])], {'F': 'A12'}), (22, 16, (245, 15, 420, 325)))
fix3('Kazuma Kuwabara (Yu Yu Hakusho, chibi, folha)', lambda b: blocks(b, [
    (15, 10, ['kkFFFFFFFkk', 'FkkkFFFkkkF', 'wwkwFFFwkww', 'FFFFFFFFFFF'])], {'F': 'A12'}), (22, 16, (20, 345, 180, 670)))
fix3('Hiei (Yu Yu Hakusho, chibi, folha)', lambda b: blocks(b, [
    (20, 9, ['wwwwwww']), (21, 7, ['www     www']),
    (22, 7, ['kkkkkkkkkkkk', ' wwrk  krww ', ' wwrr  rrww ', 'kkkkkDDkkkkk', 'DDDDDDDDDDDD'])], {'D': 'A10'}), (22, 16, (240, 330, 425, 660)))
fix3('Yu Yu Hakusho (quarteto em círculo)', lambda b: blocks(b, [
    (8, 14, ['@kkk@}kkk@', '}wk}}}}kw}']),
    (25, 26, ['kkkk', '}fk}', '}}}}']), (24, 31, ['kkk', 'fk}', '}}}']),
    (37, 13, ['kkkk', 'wnkw', '}nn}']), (37, 18, ['kkkk', 'wnkw', '}nn}'])], {'@': 'E1'}), (22, 51, None))
