"""Definições da 2ª rodada da revisão da remessa 31 (tools/r31_rev2.py): só os moldes das capturas dele (menos o Piccolo) e todos os de Eyeshield 21.
Coordenadas = linhas ATUAIS do catálogo (depois da gravação dele das 08:49), lidas em `python tools/r31_faces2.py --cat "nome" --rows a,b`."""
import os, json
from r31_rev2 import REV, D
from r31_rev import E4L, E4R, E3L, E3R
import r31v2 as V

_raw = json.load(open(os.path.join(D, 'final33_raw_120.json'), encoding='utf-8'))
_fin = json.load(open(os.path.join(D, 'final33_120.json'), encoding='utf-8'))
CATNAME = {a[0]: b[0] for a, b in zip(_raw, _fin)}
LEG = {'K': 'H7', 'W': 'H2', 'H': 'H2', 'E': 'E11', 'S': 'E14'}
LONE = ('fn', V.lone_black)
CLEAN = ('fn', lambda r: V.despeck(V.mode_smooth(r, need=5, maxde=24.0)))


def fix(name, ops, leg=None, base=(LONE, CLEAN)):
    n = CATNAME.get(name, name)
    REV[n] = dict(ops=list(base) + list(ops), leg=dict(LEG, **(leg or {})))


def O5(c1, c2=None):
    """olho redondo de 5x5 da arte de Akame ga Kill: preto com brilho branco em cima e a metade de baixo colorida"""
    c2 = c2 or c1
    return [' KKK ', 'KKHKK', 'K' + c1 + 'H' + c1 + 'K', 'K' + c2 * 3 + 'K', ' KKK ']


# ================================================================ Akame ga Kill
fix('Garota de cabelo laranja e olhos vermelhos (Akame ga Kill, chibi, fundo preto)', [('block', 24, 7, O5('M', 'L')), ('block', 24, 18, O5('M', 'L'))], dict(M='F7', L='E4'))
fix('Mine (Akame ga Kill, chibi, fundo preto)', [('paint', 25, 30, 12, 30), ('block', 21, 9, O5('M', 'L')), ('block', 21, 26, O5('M', 'L'))], dict(M='E13', L='E4'))
fix('Tatsumi (Akame ga Kill, chibi, fundo preto)', [('block', 23, 6, O5('G', 'L')), ('block', 23, 19, O5('G', 'L'))], dict(G='B5', L='B3'))
fix('Akame (Akame ga Kill, chibi)', [('block', 14, 8, ['KKK', 'MHM', ' L ']), ('block', 14, 13, ['KKK', 'MHM', ' L '])], dict(M='F5', L='F8'))
fix('Akame (Akame ga Kill, chibi, fundo preto)', [('map', 17, 30, 3, 25, {'A1': 'E1', 'G8': 'E1', 'H2': 'E1', 'H3': 'E1'}),
    ('block', 22, 2, O5('M', 'L')), ('block', 22, 18, O5('M', 'L'))], dict(M='F5', L='F8'))
fix('Leone (Akame ga Kill, chibi, fundo preto)', [('map', 21, 30, 9, 29, {'M9': 'E1', 'M5': 'E1', 'G9': 'E1', 'B11': 'E1', 'H2': 'E1', 'A1': 'E1'}),
    ('paint', 27, 30, 11, 26), ('block', 22, 7, O5('M', 'L')), ('block', 22, 23, O5('M', 'L'))], dict(M='M5', L='B11'))
_EYE7 = [' KKKKK ', 'KKKKKKK', 'KKHHKKK', 'KMHMMMK', 'KMMMMMK', 'KLLLLLK', ' KKKKK ']
# Esdeath (fundo preto): o alto do quepe era a conta H1 (transparente): vira cinza claro e branco; olhos azuis enormes e redondos da arte
fix('Esdeath (Akame ga Kill, chibi, fundo preto)', [('map', 0, 12, 0, 44, {'H1': 'H3'}), ('map', 0, 5, 0, 44, {'H3': 'H2'}),
    ('map', 20, 30, 4, 34, {'H2': 'E1', 'G1': 'E1', 'G17': 'E1'}), ('block', 22, 6, _EYE7), ('block', 22, 23, _EYE7)], dict(M='C8', L='C3'))
# Esdeath (chapéu branco): o chapéu era H1 (transparente): vira branco H2 (a sombra cinza fica); olho azul à mostra
fix('Esdeath (Akame ga Kill, chibi, chapéu branco)', [('map', 0, 22, 0, 44, {'H1': 'H2'}),
    ('block', 13, 9, ['  KKKKKKKK  ', ' KKKKWWKKKK ', 'KKKKKWWKKKKK', 'KKWWWWWWWWKK', 'KKWWWWWWWWKK', 'KKKKKWWKKKKK', ' KKKKWWKKKK ', '  KKKKKKKK  ']),
    ('block', 17, 24, ['KKKK', 'KDHD', 'DMMM', ' LLL'])], dict(D='C9', M='C8', L='C3'))


# olhos GRANDES de chibi (a arte de Attack on Titan e de muitos chibis tem olhos de 6-7 contas): pálpebra preta, íris escura -> média -> clara, brilho branco
def BE7(): return [' KKKKK ', 'KKDDDKK', 'KDHDDDK', 'KDDDDDK', 'KMMMMMK', ' KLLLK ']
def BE6(): return [' KKKK ', 'KDHDDK', 'KDDDDK', 'KMMMMK', ' LLLL ']
def BEW7(): return ['KKKKKKK', 'WDDHDDW', 'WDDDDMW', ' MMLMM ', '  LLL  ']          # com o branco dos lados (olho de 3/4, Mikasa)


# ================================================================ Attack on Titan
fix('Armin Arlert (Attack on Titan, chibi, polegar para cima)', [('block', 13, 5, BE7()), ('block', 13, 16, BE7())], dict(D='H5', M='H4', L='M6', E='G3'))
fix('Erwin Smith (Attack on Titan, chibi)', [('block', 14, 3, BE6()), ('block', 14, 12, BE6())], dict(D='C9', M='C8', L='C2'))
fix('Annie Leonhart (Attack on Titan, chibi)', [('block', 13, 5, BE6()), ('block', 13, 13, BE6())], dict(D='C9', M='C8', L='C2'))
fix('Mikasa Ackerman (Attack on Titan, chibi)', [('map', 15, 23, 7, 28, {'G1': 'E1', 'A1': 'E1', 'M9': 'E1', 'G8': 'E1', 'H3': 'E1', 'F1': 'E1'}),
    ('block', 16, 8, BEW7()), ('block', 17, 20, BEW7())], dict(D='G8', M='G14', L='H3'))
def BE5(): return [' KKK ', 'KDHDK', 'KDDDK', 'KMMMK', ' LLL ']


fix('Sasha Braus (Attack on Titan, chibi, comendo)', [('map', 12, 20, 8, 22, {'A1': 'E1', 'H2': 'E1', 'H7': 'E1', 'M9': 'E1'}), ('paint', 16, 20, 10, 16),
    ('block', 12, 9, BE5()), ('block', 12, 17, BE5())], dict(D='G8', M='F11', L='A13'))
fix('Eren Yeager (Attack on Titan, chibi, cabelo preso)', [('map', 19, 24, 4, 21, {'H7': 'E1', 'H2': 'E1', 'H4': 'E1', 'M9': 'E1', 'C14': 'E1', 'C3': 'E1', 'H5': 'E1'}),
    ('block', 19, 5, BE6()), ('block', 19, 14, BE6())], dict(D='H5', M='C14', L='H3', E='E1'))
fix('Annie Leonhart (Attack on Titan, chibi, forma de titã)', [
    ('block', 16, 6, ['PKKKKKP', 'PKDHDKP', 'PDDDDDP', 'PDMMMDP', 'PPLLLPP', ' PPPPP ']),
    ('block', 16, 17, ['PKKKKKP', 'PKDHDKP', 'PDDDDDP', 'PDMMMDP', 'PPLLLPP', ' PPPPP '])], dict(P='E13', D='C9', M='C8', L='C3'))
fix('Eren Yeager (Attack on Titan, chibi, forma de titã)', [('block', 15, 7, ['KKKKK', 'KGWGK', 'KKKKK']), ('block', 15, 18, ['KKKKK', 'KGWGK', 'KKKKK'])], dict(G='B3'))
fix('Titã Colossal (Attack on Titan, chibi, fundo de vapor)', [('set', {(15, 17): 'H2', (17, 4): 'H2'})])
_SPIRAL = [' KKKK ', 'KWWWWK', 'KWMMWK', 'KWMKWK', 'KWWWWK', ' KKKK ']
fix('Titã Colossal (Attack on Titan, chibi, vapor)', [('block', 21, 5, _SPIRAL), ('block', 21, 13, _SPIRAL)], dict(M='H4'))
fix('Titã Colossal (Attack on Titan, em círculo)', [('block', 19, 13, [' KKKK ', 'KKWWKK', ' KKKK ']), ('block', 19, 23, [' KKKK ', 'KKWWKK', ' KKKK '])])
fix('Eren Yeager (Attack on Titan, chibi, tropa de exploração)', [('map', 15, 21, 4, 23, {'H7': 'E1', 'H6': 'E1', 'A1': 'E1', 'H5': 'E1'}),
    ('block', 15, 5, BE6()), ('block', 15, 16, BE6())], dict(D='H5', M='C14', L='H3', E='E1'))
_TE7 = ['  KKK  ', ' WWWWW ', 'WWDDDWW', 'WWDKDWW', 'WWDHDWW', ' WWWWW ', '  KKK  ']
fix('Eren Yeager (Attack on Titan, chibi, titã, folha)', [('block', 15, 4, _TE7), ('block', 15, 13, _TE7)], dict(D='C14'))
fix('Reiner Braun (Attack on Titan, chibi, Titã Blindado, folha)', [('block', 17, 4, ['KKKKKK', 'KWWDWK', 'KKKKKK']), ('block', 17, 16, ['KKKKKK', 'KWDWWK', 'KKKKKK'])], dict(D='H5'))
fix('Titã Colossal (Attack on Titan, chibi, folha)', [('map', 0, 8, 0, 23, {'H1': 'H2'}), ('block', 18, 5, ['KKKKK', 'KWDWK', 'KKKKK']), ('block', 18, 12, ['KKKKK', 'KWDWK', 'KKKKK'])], dict(D='C14'))
fix('Zeke Yeager (Attack on Titan, chibi, Titã Bestial, folha)', [('map', 0, 10, 0, 13, {'H1': 'H2'}), ('block', 15, 10, ['KKKKK', 'KKAKK', 'KKKKK']), ('block', 15, 19, ['KKKKK', 'KKAKK', 'KKKKK'])], dict(A='A13'))


# ================================================================ Dragon Ball
fix('Kuririn (Dragon Ball, chibi, cartão amarelo)', [('set', {(6, 11): 'G7', (6, 13): 'G7', (6, 15): 'G7', (8, 12): 'G7', (8, 14): 'G7'})])
fix('Trunks (Dragon Ball, chibi, cartão lilás)', [('map', 4, 18, 0, 26, {'H4': 'D6', 'H5': 'D7', 'H3': 'D9'})])
fix('Chi-Chi (Dragon Ball, chibi, cartão rosa)', [])
fix('Grande Saiyaman (Dragon Ball, chibi)', [])
_VL = ['KK   ', 'KKKKK', 'WWHKK', 'WWKKK']
_VR = ['   KK', 'KKKKK', 'KKHWW', 'KKKWW']
fix('Vegeta (Dragon Ball, chibi, cartão azul)', [('map', 22, 25, 5, 18, {'M9': 'E14', 'H2': 'E14'}), ('block', 22, 6, _VL), ('block', 22, 13, _VR)])
fix('Vegeta (Dragon Ball, chibi, cartão azul estrelado)', [('map', 24, 27, 4, 20, {'G8': 'G2', 'E11': 'G2'}), ('block', 24, 5, _VL), ('block', 24, 15, _VR)])
fix('Freeza (Dragon Ball, chibi, cartão marrom)', [('map', 15, 25, 3, 20, {'M9': 'A1', 'M6': 'A1', 'M5': 'A1'}),
    ('block', 19, 6, ['KK  ', 'KKKK', 'WRKK']), ('block', 19, 13, ['  KK', 'KKKK', 'KKRW'])], dict(R='F5'))
fix('Majin Boo (Dragon Ball, chibi, cartão rosa)', [('paint', 19, 25, 9, 26), ('block', 15, 10, ['KKK', 'KHK', 'KKK', 'KKK']), ('block', 15, 20, ['KKK', 'KHK', 'KKK', 'KKK'])])
_GL = [' KKK ', 'KWWWK', 'KWWKK', 'KWWKK', 'KWWWK', ' KKK ']
fix('Goku (Dragon Ball, chibi, cartão azul)', [('paint', 19, 23, 14, 23), ('block', 14, 12, _GL), ('block', 14, 19, _GL)])
fix('Gohan (Dragon Ball, chibi, cartão roxo)', [('block', 15, 7, ['KEEEEKKEEEEK', 'EKKKEEEEKKKE', 'EKKKKEEKKKKE', 'EKHKKEEKHKKE', 'EKKKKEEKKKKE', 'EEKKEEEEKKEE', ' EEEEEEEEEE '])], dict(E='E14'))
fix('Androide 17 (Dragon Ball, chibi, cartão laranja)', [('block', 21, 8, E4L()), ('block', 21, 15, E4R())], dict(D='C9', M='C8', L='C2'))


# ================================================================ Naruto
_SH5 = [' KKK ', 'KRRRK', 'KRKRK', 'KRRRK', ' KKK ']          # Sharingan: íris vermelha com a pupila preta
fix('Itachi Uchiha (Naruto, chibi, gorro de Natal)', [('map', 0, 20, 0, 43, {'H1': 'H2'}), ('block', 21, 19, _SH5), ('block', 21, 29, _SH5)], dict(R='F5'))
fix('Madara Uchiha (Naruto, chibi, Seis Caminhos)', [('block', 19, 17, ['KKKK', 'KDHD', 'KDDD']), ('block', 19, 26, ['KKKK', 'DHDK', 'DDDK'])], dict(D='D7'))
_SGL = [' RRRRR ', 'RKKKKKR', 'RESSSER', 'RESKSER', 'REESEER', ' RRRRR ']
fix('Sarada Uchiha (Naruto, chibi, fundo rosa)', [('map', 15, 24, 13, 33, {'M9': 'E11', 'G14': 'E11', 'F14': 'E11'}), ('block', 16, 15, _SGL), ('block', 16, 25, _SGL), ('block', 17, 22, ['RRR'])], dict(R='F8', S='F5', E='E11'))
fix('Boruto Uzumaki (Naruto, chibi, fundo rosa)', [('map', 14, 18, 11, 23, {'H5': 'E1', 'H4': 'E1', 'C9': 'E1', 'M9': 'E1', 'H7': 'E1'}),
    ('block', 16, 12, [' KKK', 'K   ']), ('block', 15, 18, E4R())], dict(D='C9', M='C8', L='C2'))
fix('Sasuke Uchiha (Naruto, chibi, manto escuro e katana)', [])
fix('Sasuke Uchiha (Naruto, chibi, katana e faixa na testa)', [])
fix('Sarada Uchiha (Naruto, chibi)', [])
fix('Sakura Haruno (Naruto, corpo inteiro, vestido vermelho)', [('map', 2, 6, 3, 10, {'M9': 'E1', 'F11': 'E1', 'F9': 'E1'}),
    ('set', {(3, 5): 'H7', (3, 8): 'H7', (4, 5): 'B7', (4, 8): 'B7'})])
fix('Sakura Haruno (Naruto, corpo inteiro, roupa branca e vermelha)', [('map', 4, 8, 6, 13, {'E7': 'E1', 'F7': 'E1'}),
    ('set', {(5, 7): 'H7', (5, 11): 'H7', (6, 7): 'B7', (6, 11): 'B7', (4, 9): 'F7'})])


def redo(name, **kw):
    """reconverte pelo I() da remessa 31 com outra máscara (fundo da cor da pele vazava o rosto); grava a geometria nova em tools/out/r31_geom"""
    n = CATNAME.get(name, name)
    cfg = next((k for k, v in CATNAME.items() if v == n), n)

    def f():
        cp = os.path.join(D, 'r31_rev2_reconv.json')          # a conversão NÃO é reproduzível conta a conta: a 1ª reconversão fica guardada e os retoques valem sobre ela
        cache = json.load(open(cp, encoding='utf-8')) if os.path.exists(cp) else {}
        if n in cache: return cache[n]
        rows = g()
        cache[n] = rows; json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
        return rows

    def g():
        import r31_exfinal as X, numpy as np, cv2
        np.random.seed(31); cv2.setRNGSeed(31)          # o k-means do conversor é aleatório: semente fixa = a mesma conversão a cada build (as posições dos retoques valem)
        idx = next(i for nn, ss, i, fn, g in X.CFG if nn == cfg)
        X.P.CUR[0] = cfg; X.r5.SKIN_ON = False
        r = X.I(idx, **kw)()
        return X.h1_small(cfg, X.h1_face(cfg, r))          # só a regra do H1; os olhos, bocas e retoques da 1ª versão estavam na grade antiga
    REV[n]['reconv'] = f


import r31_exfinal as _X
redo('Sarada Uchiha (Naruto, chibi, fundo rosa)', mask=_X.OM(dark=100))


# ================================================================ Genéricos, Hunter x Hunter
fix('Garoto de cabelo verde e casaco verde (chibi, fones vermelhos)', [('block', 12, 7, ['KKKK', 'KDHD', 'DMMM', ' LLL'])], dict(D='B15', M='B12', L='B3'))
fix('Garota de cabelo verde-menta e fones de gato (chibi)', [('map', 17, 23, 12, 29, {'A1': 'E1', 'F11': 'E1', 'G5': 'E1', 'F1': 'E1', 'M9': 'E1'}),
    ('block', 18, 14, BE5()), ('block', 18, 24, BE5())], dict(D='G8', M='F11', L='A13', E='E1'))
fix('Hisoka (Hunter x Hunter, chibi, sentado com carta)', [('map', 19, 24, 9, 26, {'G5': 'E1', 'M9': 'E1', 'H2': 'E1'}),
    ('block', 20, 10, ['KKKK ', 'KAHAK', ' KKK ']), ('block', 21, 20, [' KKKK', 'KAHAK', ' KKK ']), ('set', {(23, 12): 'F5', (24, 24): 'B7'})], dict(A='A13'))
fix('Lutador de pele azul, bermuda vermelha e katana (chibi)', [('paint', 21, 25, 5, 17),
    ('block', 16, 6, ['KKKK ', 'KWWKK', 'KWHKK']), ('block', 16, 13, [' KKKK', 'KKWWK', 'KKHWK'])])
_AE = ['KKKKKK', 'KRRRRK', 'RRKHRR', 'RRKKRR', ' RRRR ']
fix('Alucard (Hellsing, chibi, copo de sangue)', [('map', 17, 23, 10, 32, {'H2': 'E11', 'H3': 'E11', 'G8': 'E11', 'F5': 'E11'}),
    ('block', 17, 11, _AE), ('block', 17, 21, _AE)], dict(R='F5'))
fix('Alucard (Hellsing, chibi, pistolas e morcegos)', [('map', 11, 14, 19, 29, {'M9': 'E11', 'H2': 'E11'}),
    ('block', 12, 20, ['KKK', 'RHR']), ('block', 12, 25, ['KKK', 'RHR'])], dict(R='F5'))
fix('Medalhão dourado com a letra P', [('map', 0, 49, 0, 49, {'H1': 'H3', 'D2': 'D9'})])
fix('Motoqueiro Fantasma (Marvel, chibi)', [('block', 18, 13, ['KKKK', 'KOOK', 'KKKK']), ('block', 18, 22, ['KKKK', 'KOOK', 'KKKK'])], dict(O='A7'))
fix('All Might (My Hero Academia, chibi, forma magra)', [('block', 16, 8, ['KKKKKK', 'KKCHKK']), ('block', 16, 16, ['KKKKKK', 'KKCHKK'])], dict(C='C11'))
_JX = [' KKKK ', 'KPKKPK', 'KPKHPK', 'KPPPPK', ' KKKK ']
fix('Jinx (Arcane, chibi)', [('map', 15, 21, 12, 32, {'H6': 'E1', 'H7': 'E1', 'D2': 'E1', 'H2': 'E1', 'D7': 'E1', 'G1': 'E1', 'H3': 'E1', 'E4': 'E1'}),
    ('block', 16, 14, _JX), ('block', 16, 24, _JX)], dict(P='E13'))
fix('Hyakkimaru (Dororo, chibi)', [('map', 15, 18, 17, 26, {'M9': 'E11', 'H7': 'E11', 'G8': 'E11'}),
    ('block', 16, 18, ['KKK', 'DHM']), ('block', 16, 23, ['KKK', 'DHM'])], dict(D='G8', M='F11'))
fix('Lelouch Lamperouge (Code Geass, chibi, gorro de Natal)', [('map', 20, 27, 25, 35, {'F7': 'E11', 'H7': 'E11', 'G8': 'E11'}),
    ('block', 21, 15, ['KKKKK', 'KDDDK', 'KDHDK', 'KMMMK', ' KKK ']), ('block', 21, 27, ['KKKKK', 'KRRRK', 'KRHRK', 'KRRRK', ' KKK '])], dict(D='D7', M='D6', R='F7'))
_ZB = ['  KK  ', ' KOOK ', 'KOKKOK', 'KOKHOK', ' KOOK ', '  KK  ']
fix('Zatch Bell (Zatch Bell!, chibi)', [('map', 9, 14, 11, 27, {'H2': 'E1', 'G5': 'E1', 'G13': 'E1', 'A3': 'E1', 'A1': 'E1'}),
    ('block', 9, 12, _ZB), ('block', 9, 20, _ZB)], dict(O='A7'))


# ================================================================ Eyeshield 21: arte de mangá com hachura; reconvertidos com mais suavização (hatch = mediana que apaga o traço fino da hachura)
_STR = __import__('r31v2').strong
_C = dict(hatch=5, pre_blur=3, line_L=30, t_line=0.14, post=_STR)
_CM = dict(hatch=7, pre_blur=4, line_L=28, t_line=0.18, post=_STR)          # os 3 desenhos de mangá colorido (Sena correndo)
for _n in ('Sena Kobayakawa (Eyeshield 21, desenho, correndo com a bola)', 'Sena Kobayakawa (Eyeshield 21, desenho, capacete verde)',
           'Sena Kobayakawa (Eyeshield 21, desenho, correndo de capacete)'):
    REV.setdefault(_n, dict(ops=[], leg=dict(LEG))); redo(_n, **_CM)
for _n in ('Taro Raimon, o Monta (Eyeshield 21, chibi, medalha)', 'Taro Raimon, o Monta (Eyeshield 21, chibi, de fundo transparente)',
           'Sena Kobayakawa (Eyeshield 21, chibi, correndo)', 'Hiruma Yoichi (Eyeshield 21, chibi, metralhadora)', 'Hiruma Yoichi (Eyeshield 21, chibi, bola)',
           'Suzuna Taki (Eyeshield 21, chibi, pompons e asas)'):
    REV.setdefault(_n, dict(ops=[], leg=dict(LEG))); redo(_n, **_C)
for _cfg, _ser, _idx, _fn, _g in _X.CFG:
    if _idx in (7, 40) and _cfg in CATNAME:
        _n = CATNAME[_cfg]; _b = _fn.box
        _kw = dict(_C, thr=222 if _idx == 7 else 240, skin=('Cerberus' not in _cfg))
        REV.setdefault(_n, dict(ops=[], leg=dict(LEG))); redo(_n, box=_b, **_kw)
# rostos de Eyeshield 21 (coordenadas = linhas da reconversão; lidas com r31_faces2.py --cat --rev2 e r31_dumpnew.py --rev2)
REV['Sena Kobayakawa (Eyeshield 21, chibi, correndo)']['ops'] += [('map', 28, 33, 18, 30, {'H2': 'E11', 'H4': 'E11', 'H7': 'E11'}),
    ('paint', 31, 35, 17, 28), ('block', 27, 14, ['KKKKKK', 'WWWKKK', 'WWKHKK', 'WWKKKK', ' WWWW ']), ('block', 28, 25, ['KKKKK', 'KKKWW', 'KHKWW', 'KKKWW', ' WWW '])]
REV['Sena Kobayakawa (Eyeshield 21, chibi, correndo)']['leg'].update(D='G8', M='F11')
REV['Suzuna Taki (Eyeshield 21, chibi, pompons e asas)']['ops'] += [('map', 12, 22, 17, 35, {'H2': 'G3', 'H6': 'G3', 'C8': 'G3', 'H3': 'G3', 'A1': 'G3'}), ('paint', 18, 22, 21, 28),
    ('block', 13, 18, [' KKKK ', 'KKDDDK', 'WDHDDK', 'WDDDMK', ' MMLL ']), ('block', 13, 29, [' KKKK ', 'KDDDKK', 'KDDHDW', 'KMDDDW', ' LLMM '])]
REV['Suzuna Taki (Eyeshield 21, chibi, pompons e asas)']['leg'].update(D='C9', M='C8', L='C2')
REV['Hiruma Yoichi (Eyeshield 21, chibi, bola)']['ops'] += [('map', 17, 20, 5, 21, {'H2': 'E1', 'H3': 'E1', 'H4': 'E1', 'H7': 'E1'}), ('paint', 21, 24, 8, 18),
    ('block', 17, 6, ['KKKK', 'WWGK', ' KKK']), ('block', 17, 15, ['KKKK', 'KGWW', 'KKK '])]
REV['Hiruma Yoichi (Eyeshield 21, chibi, bola)']['leg'].update(G='B12')
REV['Hiruma Yoichi (Eyeshield 21, chibi, metralhadora)']['ops'] += [('map', 20, 23, 3, 18, {'H2': 'E11', 'H3': 'E11', 'H5': 'E11', 'H7': 'E11'}), ('paint', 23, 27, 6, 15),
    ('block', 20, 4, ['KKKK', 'WWGK', ' KKK']), ('block', 20, 12, ['KKKK', 'KGWW', 'KKK '])]
REV['Hiruma Yoichi (Eyeshield 21, chibi, metralhadora)']['leg'].update(G='B12')
def _add(n, ops, **leg):
    REV[n]['ops'] += ops; REV[n]['leg'].update(leg)


_add('Taro Raimon, o Monta (Eyeshield 21, chibi, medalha)', [('map', 27, 33, 19, 34, {'H2': 'E14', 'H3': 'E14', 'H5': 'E14', 'H7': 'E14', 'M9': 'E14', 'A12': 'E14'}),
    ('paint', 34, 38, 27, 38), ('block', 27, 19, BE6()), ('block', 27, 28, BE6())], D='G8', M='F11', L='A13', E='E14')
_add('Sena Kobayakawa (Eyeshield 21, chibi, de capacete verde, folha 3)', [('map', 26, 31, 9, 23, {'H2': 'A1', 'H3': 'A1', 'H1': 'A1', 'H6': 'A1', 'H4': 'A1', 'M9': 'A1', 'G8': 'A1'}),
    ('paint', 32, 34, 13, 21), ('block', 26, 10, BE5()), ('block', 26, 18, BE5())], D='G8', M='F11', L='A13', E='A1')
_add('Taro Raimon, o Monta (Eyeshield 21, chibi, de fundo transparente)', [('paint', 20, 24, 18, 30)])
_add('Mamori Anezaki (Eyeshield 21, chibi, vassoura, folha 3)', [('map', 14, 18, 16, 30, {'H2': 'E11', 'H7': 'E11', 'C9': 'E11', 'H3': 'E11', 'M9': 'E11'}),
    ('paint', 19, 22, 20, 27), ('block', 14, 17, BE5()), ('block', 14, 25, BE5())], D='C9', M='C8', L='C2')
_add('Suzuna Taki (Eyeshield 21, chibi, patins, folha 3)', [('paint', 14, 19, 13, 22)])


# ================================================================ WWE
fix('John Cena (WWE, chibi)', [('map', 15, 27, 6, 23, {'G1': 'E11', 'M12': 'E11', 'H5': 'E11', 'D16': 'E11'}), ('paint', 22, 25, 10, 19),
    ('block', 16, 7, BE6()), ('block', 16, 17, BE6())], dict(D='C9', M='C8', L='C2'))
_PPGE = ['  KKKK  ', ' KKKKKK ', 'KKWWKKKK', 'KKWWKKKK', 'KKKKKKKK', 'PKKKKKKP', ' PPPPPP ']
fix('Lutadora de cabelo preto (WWE, chibi, estilo Meninas Superpoderosas)', [('paint', 17, 21, 13, 20), ('block', 10, 6, _PPGE), ('block', 10, 18, _PPGE)], dict(P='D13'))
for _n in ('Lutadora de cabelo preto e cinturão (WWE, desenho)', 'Lutadora de cabelo escuro e botas (WWE, desenho)', 'Lutadora loira (WWE, estilo Meninas Superpoderosas, trio)',
           'Becky Lynch (WWE, estilo Meninas Superpoderosas, trio)', 'Paige (WWE, estilo Meninas Superpoderosas, trio)'):
    fix(_n, [])
