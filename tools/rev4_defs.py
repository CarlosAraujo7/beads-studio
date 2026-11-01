"""Consertos da 4ª revisão (ver rev4.py). Cada fix4 recebe as linhas atuais do catálogo e devolve as novas."""
import numpy as np
import cv2
from rev4 import fix4, flat, blocks, recolor, mirror, L, SRC
import facetools as FT
import outline as O
import loose


def flood_out(rows, letters='w'):
    """vazio entra pelas bordas e atravessa as letras `letters` (fundo branco e margem de adesivo); o branco cercado por contorno fica"""
    H, W = len(rows), len(rows[0]); g = [list(r) for r in rows]
    st = [(y, x) for y in range(H) for x in (0, W - 1)] + [(y, x) for x in range(W) for y in (0, H - 1)]
    seen = set()
    while st:
        y, x = st.pop()
        if (y, x) in seen or not (0 <= y < H and 0 <= x < W): continue
        seen.add((y, x))
        if g[y][x] != '.' and g[y][x] not in letters: continue
        g[y][x] = '.'
        st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return [''.join(r) for r in g]


def flat_fig(name, b, pal, prio=None, out='w', pad=0):
    raw = FT.src_raw(*SRC[name]); geo = FT.align(raw, b, verbose=False)
    return flood_out(flat(raw, geo, len(b[0]), len(b), pal, prio), out)


# ------------------------------------------------------------------ Quatro Braços: 3 olhos laranja em zigue-zague de cada lado, como na arte (o molde ajustado por ele fica igual no resto)
fix4('Quatro Braços (Ben 10, pixel)', lambda b: blocks(b, [(2, 20, ['krokkkork', 'krkokokrk', 'krokkkork'])]))


# ------------------------------------------------------------------ Chucky: cores chapadas da arte (macacão azul, cabelo ruivo, camisa listrada)
CHU = [((255, 255, 255), 'w'), ((22, 8, 8), 'k'), ((249, 208, 186), L['E1']), ((211, 173, 164), L['G3']), ((188, 77, 52), L['F13']), ((215, 100, 60), L['F4']), ((135, 33, 21), L['F8']), ((88, 15, 10), L['F10']),
       ((120, 139, 148), L['D2']), ((85, 100, 115), L['C7']), ((60, 60, 70), L['H6']), ((205, 206, 209), L['H3']), ((200, 40, 40), 'r'), ((90, 160, 130), L['B5']), ((245, 238, 237), 'w'), ((125, 67, 62), L['F10'])]


def chucky(b):
    r = flat_fig('Chucky (chibi)', b, CHU, {'k': 0.5})
    return r


fix4('Chucky (chibi)', chucky)


# ------------------------------------------------------------------ Pennywise de capa amarela: rosto marfim, capa amarela limpa
PCA = [((254, 254, 254), 'w'), ((30, 15, 8), 'k'), ((249, 197, 54), 'y'), ((236, 208, 133), L['A5']), ((200, 150, 60), L['A8']), ((143, 104, 24), L['G6']), ((85, 56, 32), L['F11']), ((236, 230, 223), L['E8']),
       ((192, 186, 182), L['H3']), ((152, 145, 139), L['H4']), ((112, 99, 87), L['H5']), ((169, 61, 67), 'r')]
fix4('Pennywise de capa amarela (chibi)', lambda b: flat_fig('Pennywise de capa amarela (chibi)', b, PCA, {'k': 0.45}))


# ------------------------------------------------------------------ Pennywise corpo inteiro: roupa bege e faixas vermelhas da arte, espelhado
PEN = [((253, 253, 253), 'w'), ((7, 4, 4), 'k'), ((211, 205, 190), L['H12']), ((253, 94, 16), 'o'), ((246, 237, 212), L['A1']), ((232, 10, 12), 'r'), ((146, 143, 137), L['H4']), ((84, 81, 76), L['H6']), ((237, 208, 88), 'y')]


def pen(b):
    raw = FT.src_raw(*SRC['Pennywise (chibi, corpo inteiro)']); geo = FT.align(raw, b, verbose=False)
    r = flat(raw, geo, len(b[0]), len(b), PEN, {'k': 0.4})
    r = [''.join('.' if b[y][x] == '.' else c for x, c in enumerate(l)) for y, l in enumerate(r)]
    return mirror(r, 'L')


fix4('Pennywise (chibi, corpo inteiro)', pen)


# ------------------------------------------------------------------ Jack Sparrow: fundo e margem branca do adesivo saem por inundação; preto só onde é maioria da conta
JAC = [((198, 197, 198), 'w'), ((251, 251, 251), 'w'), ((5, 4, 4), 'k'), ((92, 90, 93), L['H5']), ((125, 127, 132), L['H4']), ((155, 155, 155), L['H4']), ((240, 208, 176), L['G1']), ((208, 164, 121), L['G9']), ((170, 75, 67), L['F13']),
       ((122, 68, 60), L['F10']), ((87, 60, 52), L['F11']), ((55, 65, 72), L['C16']), ((58, 87, 103), L['C16']), ((67, 114, 131), L['C15']), ((157, 130, 98), L['G14'])]
fix4('Jack Sparrow (Piratas do Caribe, chibi, adesivo)', lambda b: flat_fig('Jack Sparrow (Piratas do Caribe, chibi, adesivo)', b, JAC, {'k': 0.65}))


# ====== PARTE 2 ======
import rev4 as _R


# ------------------------------------------------------------------ Trompa: o cabo vira o eixo; meia trompa e meio guarda-chuva com a mesma largura e a mesma altura; o arco é espelhado
def trompa(b):
    import r24_exfinal as X
    left = X._drop_lines([r[:28] for r in b], 4)
    W = len(left[0]); H = len(b); R = W                               # cabo na coluna W
    g = [list(l) + ['.'] * (R + 1) for l in left]
    Y = 25
    for y in range(Y):
        xm = R * (1 - ((Y - y) / float(Y)) ** 2) ** 0.5
        for x in range(1, int(round(xm)) + 1): g[y][W + x] = 'y'
    ribs = [0, 8, 16, R]
    for x in range(1, R + 1):
        if not any(abs(x - q) <= 1 or abs(x - (q + 8)) <= 0 for q in ribs) and x % 8 in (3, 4, 5): continue
        g[Y][W + x] = 'y'
    for q in ribs: g[Y + 1][W + q] = 'y'
    for y in range(H):
        if y <= 44: g[y][W] = 'y'
    for y in range(21, H):                                            # arco de baixo: o azul à esquerda, o mesmo desenho em amarelo-claro à direita
        for x in range(W):
            if g[y][x] == '3': g[y][2 * W - x] = 'j'
    # gancho do cabo
    for yy, xs in ((45, [0]), (46, [0, 2, 3]), (47, [0, 1, 2]), (48, [1])):
        for dx in xs: g[yy][W + dx] = 'y'
    return [''.join(r) for r in g]


fix4('Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)', trompa)


# ------------------------------------------------------------------ Vergonha (Divertida Mente 2; era "Criatura roxa"): os códigos do gráfico são MARD; as letras do kit com o mesmo código saíam pálidas: agora a cor mais próxima da AMOSTRA de cada código
_VERG = str.maketrans({'>': L['D21'], '(': L['D13'], '+': L['D5'], '_': L['E5'], '?': L['D14']})
fix4('Criatura roxa (pixel, gráfico)', lambda b: [r.translate(_VERG) for r in b], rename='Vergonha (Divertida Mente, gráfico)')


# ------------------------------------------------------------------ Dante: rosto mais claro e dois olhos azuis discretos; mechas do cabelo em cinza médio, para o rosto aparecer
def dante(b):
    r = recolor(b, 3, 10, 0, 24, ['d'], 'm')
    G = {'Ð': 'G2'}
    return blocks(r, [(11, 7, ['Ðdkkkwkkk wl']), (12, 7, ['ÐÐwb!ÐÐwb!ÐÐ']), (13, 8, [' ÐÐÐÐÐÐÐÐÐ'])])


fix4('Dante (Devil May Cry, pixel)', dante)


# ------------------------------------------------------------------ Omni-Man e Sukuna: leitura no tamanho nativo com as cores da arte; depois a redução que mais guarda detalhe
def _om(b):
    import r24_exfinal as X, r5
    r5.SKIN_ON = False
    OM = dict(ref=(138, 30, 54), tol=34, dist=8, colmap=[((219, 52, 115), 40, L['E10']), ((193, 62, 121), 22, L['E10']), ((143, 23, 95), 26, L['E7']), ((87, 5, 91), 28, L['D14']), ((55, 4, 56), 24, L['D15']), ((7, 9, 38), 22, 'k'), ((186, 134, 133), 26, L['G5']),
                                                  ((233, 194, 168), 22, L['G1']), ((246, 240, 224), 18, 'w'), ((104, 76, 102), 24, L['D21']), ((34, 42, 73), 20, L['C16']), ((40, 154, 212), 50, 'c')])
    nat = X.E(44, post=X.lg, **OM)
    import shrink
    w, h = len(nat[0]), len(nat); nw, nh = shrink.target_size(w, h, 50)
    t = X._drop_lines(nat, w - nw)
    t = [''.join(c) for c in zip(*t)]; t = X._drop_lines(t, h - nh)
    return [''.join(c) for c in zip(*t)]


fix4('Omni-Man (Invencível, pixel)', _om)


def _su(b):
    import r24_exfinal as X, r5, shrink
    r5.SKIN_ON = False
    SU = dict(dist=8, colmap=[((15, 13, 28), 14, L['D15']), ((36, 31, 50), 14, L['D15']), ((56, 57, 85), 18, L['C16']), ((243, 184, 166), 22, L['G2']), ((173, 115, 115), 26, L['G5']), ((197, 151, 148), 24, L['E2']), ((131, 92, 98), 20, L['G7']),
                               ((96, 51, 63), 18, L['F7']), ((80, 35, 20), 18, L['F10']), ((141, 52, 65), 24, L['F13'])])
    return shrink.shrink(X.E(0, post=X.lg, **SU), 50, 'plain', empty_at=0.6)


fix4('Sukuna (Jujutsu Kaisen, pixel, corpo inteiro)', _su)


# ------------------------------------------------------------------ Paiges: rosto oval, afinando no queixo; sem dentes: a boca é um traço
s_, n_, w_, r_ = 's', 'n', 'w', 'r'
fix4('Paige (WWE, com cinturão)', lambda b: blocks(b, [(4, 11, ['kkksssskkkk']), (5, 11, ['kkssssskkkk']), (6, 11, ['kssssssskkk']), (7, 11, ['kkkkssskkkk']), (8, 11, ['ksnwssnwskk']),
                                                     (9, 11, ['kssssssssk ']), (10, 11, ['kssssssssk ']), (11, 11, ['kksssssskkk']), (12, 11, ['kksssrrskkk']), (13, 11, ['kkkssssskkk']), (14, 11, ['kkkkFsskkkk'])], {}))
fix4('Paige (WWE, top roxo)', lambda b: blocks(b, [(5, 8, ['kksssssk']), (6, 8, ['skkkssskk']), (7, 8, ['snwssnwk']), (8, 8, ['ssssssss']), (9, 8, ['ssssssss']), (10, 8, ['kssrrrss']), (11, 8, ['kkssssskk']), (12, 8, ['kkFsskkk'])]))
fix4('Paige (WWE, erguendo o cinturão)', lambda b: blocks(b, [(9, 11, ['kssssk']), (10, 10, ['kkkskkk']), (11, 10, ['snwsnws']), (12, 10, ['sssssss']), (13, 10, ['ksssrrs']), (14, 10, ['kssssss']), (15, 10, ['kksssk'])]))
fix4('Paige (WWE, com cinturão) (grande)', lambda b: recolor(recolor(recolor(b, 14, 14, 20, 25, ['w'], 's'), 16, 16, 18, 24, [']'], 's'), 15, 15, 17, 24, ['r'], 'r'))
fix4('Paige (WWE, top roxo) (grande)', lambda b: recolor(b, 18, 18, 18, 26, ['^'], 's'))
fix4('Paige (WWE, erguendo o cinturão) (grande)', lambda b: recolor(b, 26, 26, 22, 30, ['^'], 's'))
_R.SRC.update({n + ' (grande)': _R.SRC[n] for n in ('Paige (WWE, com cinturão)', 'Paige (WWE, top roxo)', 'Paige (WWE, erguendo o cinturão)')})


# ====== PARTE 3 ======
_base = dict(_R.FIX4)


def then(name, fn):
    f0 = _base[name]
    _R.FIX4[name] = lambda b: fn(f0(b))


# Chucky: olhos sem o azul, com 1 brilho; tênis vermelhos com sola clara
def _chu(r):
    r = recolor(r, 18, 21, 15, 33, [L['D2'], L['C7']], 'w')
    r = blocks(r, [(19, 20, ['w']), (19, 28, ['w'])])
    r = recolor(r, 45, 49, 0, 41, [L['F10'], L['F8']], 'r')
    return recolor(r, 45, 49, 0, 41, [L['G3']], 'i')


then('Chucky (chibi)', _chu)


# Pennywise de capa: olhos redondos, lágrimas vermelhas e nariz rosa
def _cap(r):
    return blocks(r, [(18, 8, [' k ', 'kkk', ' k ']), (18, 16, [' k ', 'kkk', ' k ']), (15, 9, ['r', 'r']), (21, 9, ['r', 'r', 'r']), (15, 17, ['r', 'r']), (21, 17, ['r', 'r', 'r']), (22, 13, ['p'])])


then('Pennywise de capa amarela (chibi)', _cap)


# Pennywise corpo inteiro: corpo com menos pontos pretos; rosto desenhado antes de espelhar (olho amarelo com pupila, traço vermelho, nariz e sorriso de 1 traço)
def pen2(b):
    raw = FT.src_raw(*SRC['Pennywise (chibi, corpo inteiro)']); geo = FT.align(raw, b, verbose=False)
    r = flat(raw, geo, len(b[0]), len(b), PEN, {'k': 0.6})
    r = [''.join('.' if b[y][x] == '.' else c for x, c in enumerate(l)) for y, l in enumerate(r)]
    r = recolor(r, 0, 9, 0, 99, ['k'], 'o')
    r = recolor(r, 10, 24, 5, 23, ['k', 'r', 'y', 'o'], 'w')
    r = blocks(r, [(14, 10, ['r', 'r', 'r']), (17, 7, ['kkk  ', ' kkkk']), (19, 8, ['yykk', 'yykw', ' yy ']), (22, 13, ['  r']), (23, 11, ['r', ' rrrr'])])
    return mirror(r, 'L', 28)


_R.FIX4['Pennywise (chibi, corpo inteiro)'] = pen2


# Trompa: o arco só abaixo da cúpula
def _tr(b):
    r = _base['Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)'](b)
    W = 24; g = [list(l) for l in r]
    for y in range(21, 27):
        for x in range(W + 1, len(g[0])):
            if g[y][x] == 'j': g[y][x] = 'y'
    return [''.join(l) for l in g]


_R.FIX4['Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)'] = _tr


# Omni-Man: rosto limpo (pele de um tom, sobrancelha, olho azul, bigode)
then('Omni-Man (Invencível, pixel)', lambda r: blocks(r, [(3, 15, ['!']), (3, 25, ['!']), (4, 14, ['kttttttktttttk'[:13]]), (5, 14, ['kkkkttÉttkkkk']), (6, 14, ['ktwctÉÉtcwttk'[:13]]), (7, 14, ['ktttttÉttttt k'[:13]]), (8, 17, ['tkkkkktt'[:7]])]))


# Sukuna: rosto de 3/4 lido da arte: 4 olhos vermelhos e tatuagem; boca é um traço, sem dentes
then('Sukuna (Jujutsu Kaisen, pixel, corpo inteiro)', lambda r: blocks(r, [(6, 19, ['ÐÐÐÐkÐ']), (7, 20, ['kkÐkk']), (8, 20, ['ÐkrÐrk']), (9, 20, ['ÐÐÐÐÐk']), (10, 20, ['krkÐkr']), (11, 20, ['ÐÐÐÐÐ']), (12, 20, ['ÐÐÐÐÐ']), (13, 20, ['ÐkkkÐ']), (14, 20, ['ÐÐÐÐÐ'])]))


# Paige com cinturão (grande): sem o branco que sobrava na boca
then('Paige (WWE, com cinturão) (grande)', lambda r: recolor(r, 13, 16, 14, 30, ['w', ']'], 's'))
