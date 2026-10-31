"""Mapas de cor por CENTRO do k-means (`illus5.convert5(center_map=...)`) para refazer os moldes fracos das remessas 22/23 (2026-10-31, veja CLAUDE.md §7.19).
Cada função recebe (rgb médio do centro, L, letra atual, é preto?) e devolve a letra nova ou None (fica como está).
  CM_BROWN  cabelo/chapéu MARROM escuro que o near120 'dark' mandava para preto (Alucard) ou verde-oliva (Endou 'Mugen the Hand': (96,76,18) virava B17): vai para F11/F10/G13 (os marrons escuros do kit)
  CM_NEUT   cabelo BRANCO/CINZA de matiz quente com pouca saturação (244,233,218): a trava de pele do near120 o pintava de PELE (Gouenji ficou com a cabeça rosa): vai para os cinzas H1-H5
  smoke()   cinza ESCURO neutro (L 14-36: fumaça, corvo, degradê do preto) vira H6 e o preto de verdade (L < 12, o contorno) continua H7: figura PRETA sobre fumaça PRETA (Shikamaru, Itachi com corvo,
            Muzan) virava uma mancha só; com a fumaça um degrau mais clara o contorno do personagem aparece
  CM_ALL    CM_NEUT e depois CM_BROWN (e os dos moldes originais: loiro e roxo, se passados)"""
import colorsys
import numpy as np
import palette as P

_L = {c['code']: c['letter'] for c in P.ALL}
_HEX = {c['code']: np.array([int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float) for c in P.ALL}


def _hsv(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); return h * 360, s, v


def _lab(rgb):
    import illus
    return illus._lab(np.array(rgb, float))


_BROWNS = ['M12', 'F11', 'F10', 'G13', 'G7']
_NEUTS = [('H2', 100.0), ('H1', 91.5), ('H3', 74.8), ('H4', 58.8), ('H5', 41.0)]


def CM_BROWN(rgb, L, letter, is_black):
    h, s, v = _hsv(rgb)
    if is_black or not (14 <= L <= 46): return None
    if not ((h <= 56 or h >= 348) and 0.22 <= s <= (0.92 if 20 <= h <= 56 else 0.72)): return None      # marrom-amarelado (96,76,18) tem s = 0,81 por causa do realce de saturação do convert5
    if h >= 348 or h < 8:                      # avermelhado: só se for bem escuro e apagado (marrom-avermelhado do cabelo), não vermelho de verdade
        if s > 0.55 or L > 36: return None
    lab = _lab(rgb)
    best = min(_BROWNS, key=lambda c: float(np.linalg.norm(_lab(_HEX[c]) - lab)))
    return _L[best]


def CM_NEUT(rgb, L, letter, is_black):
    h, s, v = _hsv(rgb)
    if is_black or v < 0.55 or not (10 <= h <= 62 and s < 0.135): return None
    best = min(_NEUTS, key=lambda t: abs(t[1] - L))
    return _L[best[0]]


def smoke(lo=14.0, hi=36.0, to='H6', max_sat=0.14):
    def f(rgb, L, letter, is_black):
        h, s, v = _hsv(rgb)
        if is_black or not (lo <= L <= hi) or s > max_sat: return None
        return _L[to]
    return f


def combo(*fns):
    def f(rgb, L, letter, is_black):
        for fn in fns:
            r = fn(rgb, L, letter, is_black)
            if r: return r
        return None
    return f


CM_ALL = combo(CM_NEUT, CM_BROWN)
