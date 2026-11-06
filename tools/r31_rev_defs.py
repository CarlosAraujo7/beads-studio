"""Definições da revisão da remessa 31 (tools/r31_rev.py), pedida pelo dono em 2026-11-06 ("a maioria dos moldes saiu ruim... veja como está em relação à imagem original e ajuste").
Todos os moldes de ilustração e de folha recebem primeiro o filtro r31v2.strong (junta tons quase iguais, maioria 3x3 entre tons parecidos, tira conta solta: o salpicado de
luz e sombra some e as faixas largas, os olhos e as estampas ficam); depois, os retoques por molde (coordenadas = linhas do molde do catálogo, lidas em tools/r31_faces2.py).
Gráficos e pixel art (cópia fiel) não entram."""
import os, json
from r31_rev import REV, eyes, E4L, E4R, E3L, E3R, E2, E2B, D
import r31v2 as V

HERE = os.path.dirname(os.path.abspath(__file__))
_raw = json.load(open(os.path.join(D, 'final33_raw_120.json'), encoding='utf-8'))
_fin = json.load(open(os.path.join(D, 'final33_120.json'), encoding='utf-8'))
CATNAME = {a[0]: b[0] for a, b in zip(_raw, _fin)}          # nome do CFG -> nome no catálogo (", versão 2")


def _groups():
    import r31_exfinal as X
    return {n: g for n, s, i, f, g in X.CFG}


GRP = _groups()
STRONG = ('fn', V.strong)
for _n, _g in GRP.items():
    if _g in ('ill', 'folha') and _n in CATNAME:
        REV[CATNAME[_n]] = dict(ops=[STRONG])

# as 3 folhas de figuras encostadas: reconvertidas com a máscara pelo contorno da imagem inteira (OMF), sem o pedaço do vizinho nem as manchas de tinta
for _n in ('Kayano em cima de um Koro-sensei verde (Assassination Classroom, chibi, trio)', 'Nagisa em cima de um Koro-sensei amarelo (Assassination Classroom, chibi, trio)',
           'Karma em cima de um Koro-sensei vermelho (Assassination Classroom, chibi, trio)', 'Kayano em cima de um Koro-sensei listrado (Assassination Classroom, chibi, lápis de cor)',
           'Nagisa em cima de um Koro-sensei amarelo (Assassination Classroom, chibi, lápis de cor)', 'Karma em cima de um Koro-sensei branco (Assassination Classroom, chibi, lápis de cor)',
           'Lutadora loira (WWE, estilo Meninas Superpoderosas, trio)', 'Becky Lynch (WWE, estilo Meninas Superpoderosas, trio)', 'Paige (WWE, estilo Meninas Superpoderosas, trio)'):
    REV[CATNAME[_n]]['v2'] = True


def more(name, ops, leg=None):
    """acrescenta retoques depois do filtro (nome do CFG ou do catálogo)"""
    t = REV[CATNAME.get(name, name)]
    t['ops'] = t['ops'] + list(ops)
    if leg: t.setdefault('leg', {}).update(leg)


LEG = {'K': 'H7', 'W': 'H2', 'H': 'H2', 'E': 'E11', 'S': 'E14'}

# ---------------------------------------------------------------- rostos
# Nagisa (faca na boca): olhos de susto da arte = círculo branco de aro preto grosso com a pupila preta no meio
_O5 = [' KKK ', 'KWWWK', 'KWKWK', 'KWWWK', ' KKK ']
more('Nagisa Shiota (Assassination Classroom, chibi, faca na boca)', [('block', 16, 8, _O5), ('block', 16, 18, _O5)], LEG)

# Trunks: olhos azuis de pálpebra preta (linhas 18-21), os dois olhando para a direita, como na arte
_TE = ['KKK', 'WDH', 'WMM', ' LL']
more('Trunks (Dragon Ball, chibi, cartão lilás)', [('map', 17, 22, 5, 16, {'H7': 'E11', 'H2': 'E11', 'H3': 'E11', 'H4': 'E11', 'D9': 'E11', 'E2': 'E11'}),
                                                   ('block', 18, 6, _TE), ('block', 18, 13, _TE)], dict(LEG, D='C9', M='C8', L='C7'))
# Nagisa (capa): olhos de 2 contas, branco por fora e íris azul por dentro; sem as manchas caramelo do rosto
more('Nagisa Shiota (Assassination Classroom, chibi, capa)', [('map', 12, 15, 5, 14, {'M9': 'E11', 'H4': 'E11'}),
    ('block', 11, 6, ['KK', 'WD', 'WL']), ('block', 11, 12, ['KK', 'DW', 'LW'])], dict(LEG, D='C9', L='C7'))
# Kayano: olhos castanho-âmbar com o brilho embaixo à esquerda; a boca aberta (marrom) sai (§4.8)
more('Kaede Kayano (Assassination Classroom, chibi)', [('map', 10, 13, 5, 13, {'M9': 'E11'}),
    ('block', 9, 6, ['KK', 'DM', 'HL']), ('block', 9, 11, ['KK', 'DM', 'HL'])], dict(LEG, D='G8', M='F11', L='A13'))
# Garota de olhos vermelhos (Akame ga Kill, fundo preto): olhos redondos de aro preto grosso e íris magenta com brilho; o rosto sem H1 (transparente) e sem o sorriso de dentes
_RE = [' KKK ', 'KMMWK', 'KMLMK', 'KMMMK', ' KKK ']
more('Garota de cabelo laranja e olhos vermelhos (Akame ga Kill, chibi, fundo preto)', [
    ('map', 22, 28, 5, 27, {'H1': 'E1', 'H2': 'E1', 'H3': 'E1', 'H4': 'E1'}), ('map', 23, 28, 12, 19, {'H7': 'E1'}),
    ('paint', 29, 31, 6, 26), ('block', 24, 7, _RE), ('block', 24, 20, _RE)], dict(LEG, M='F7', L='E4', E='E1'))
# Garota verde-menta: olhos castanhos grandes (o direito um pouco mais alto, rosto de 3/4)
more('Garota de cabelo verde-menta e fones de gato (chibi)', [
    ('map', 19, 23, 8, 13, {'H7': 'E11', 'H2': 'E11', 'H3': 'E11', 'H6': 'E11', 'M9': 'E11', 'F11': 'E11', 'G8': 'E11'}),
    ('map', 18, 22, 20, 25, {'H7': 'E11', 'H2': 'E11', 'H3': 'E11', 'H6': 'E11', 'M9': 'E11', 'F11': 'E11', 'G8': 'E11'}),
    ('block', 19, 9, E4L()), ('block', 18, 21, E4R())], dict(LEG, D='G8', M='F11', L='A13'))
# Sarada: os óculos vermelhos grandes da arte e os olhos pretos com o brilho em coração
_SL = [' RRRRRRRR ', 'RSSKKKKSSR', 'RSKKKWKKSR', 'RSKKKKKKSR', 'RSKKKKKKSR', 'RSSKKKKSSR', 'RSSSSSSSSR', ' RRRRRRRR ']
more('Sarada Uchiha (Naruto, chibi)', [('block', 20, 3, _SL), ('block', 20, 15, _SL), ('block', 22, 13, ['RR'])], dict(LEG, R='F8', S='E11'))
# Lutadora loira (estilo Meninas Superpoderosas): olhos enormes de pupila preta, aro azul-petróleo embaixo e brilho branco grande em cima à direita; boca aberta sai
_PPG = [' KKKK ', 'KCKKWK', 'KKKWWK', 'KKKKKK', 'KCCCCK', ' KKKK ']
more('Lutadora loira de cabelo ondulado (WWE, chibi, estilo Meninas Superpoderosas)', [
    ('paint', 14, 16, 11, 15), ('block', 9, 7, _PPG), ('block', 9, 15, _PPG)], dict(LEG, C='C11', E='G2'))
# Annie: olhos azuis no modelo da Rei, rosto sem as manchas cinza e caramelo
more('Annie Leonhart (Attack on Titan, chibi)', [
    ('map', 13, 17, 5, 18, {'H7': 'E11', 'H2': 'E11', 'H3': 'E11', 'H4': 'E11', 'D16': 'E11', 'M9': 'E11'}),
    ('block', 13, 6, E4L()), ('block', 13, 13, E4R())], dict(LEG, D='C9', M='C8', L='C2'))
# Seth Rollins: olhos grandes de pupila preta, íris roxa e brilho, branco em volta (a arte é de olhos enormes)
_SR = ['KKKKKK', 'WDKKHW', 'WDKKKW', 'WMDDMW', ' WWWW ']
more('Seth Rollins (WWE, chibi)', [
    ('map', 17, 21, 4, 25, {'H2': 'E14', 'H3': 'E14', 'M9': 'E14', 'D6': 'E14', 'E7': 'E14'}),
    ('block', 17, 5, _SR), ('block', 17, 19, _SR)], dict(LEG, D='D7', M='D6', E='E14'))


# ---------------------------------------------------------------- repintar uma região pela ARTE (cor mediana do miolo de cada conta), só com as contas dadas
def art_fill(name, r0, r1, c0, c1, codes, keep_empty=True, dark=None):
    """r1/c1 inclusivos. codes = códigos permitidos; a cor de cada conta é a da arte alinhada (geometria da conversão, tools/out/r31_geom); conta vazia fica vazia.
    dark = (L, código): conta da arte com claridade L* abaixo disso vira esse código direto (traço preto fino que a mediana clareia)."""
    import numpy as np
    import r31_exfinal as X, r31_eyes as EY
    from r31_probe import art_color
    from palette import ALL
    import illus
    L = {p['code']: p['letter'] for p in ALL}
    lab = {}
    for c in codes:
        h = next(p['hex'] for p in ALL if p['code'] == c).lstrip('#')
        lab[c] = illus._lab(np.array([[[int(h[i:i + 2], 16) for i in (0, 2, 4)]]], np.float32))[0, 0]
    cfg = next((k for k, v in CATNAME.items() if v == name), name)

    def f(rows):
        G = X.load_geom(cfg); ctx = EY.Ctx(rows, G, X.P, X.L, X.LAB)
        g = [list(r) for r in rows]
        for y in range(max(0, r0), min(len(g), r1 + 1)):
            for x in range(max(0, c0), min(len(g[0]), c1 + 1)):
                if keep_empty and g[y][x] == '.': continue
                col = art_color(ctx, y, x)
                if col is None: continue
                q = illus._lab(np.array([[col]], np.float32))[0, 0]
                if dark and q[0] < dark[0]: g[y][x] = L[dark[1]]; continue
                best = min(codes, key=lambda c: float(np.linalg.norm(lab[c] - q)))
                g[y][x] = L[best]
        return [''.join(r) for r in g]
    return ('fn', f)


def reconv(name, **kw):
    """reconverte o molde pelo I() da remessa 31 com outras opções (máscara de fundo); grava a geometria nova (as folhas de leitura passam a valer para ela)"""
    def f():
        import r31_exfinal as X
        cfg = next((k for k, v in CATNAME.items() if v == name), name)
        idx = next(i for n, s, i, fn, g in X.CFG if n == cfg)
        X.P.CUR[0] = cfg; X.r5.SKIN_ON = False
        return X.post31(cfg, X.I(idx, **kw)())
    return f


def redo(name, **kw):
    REV[CATNAME.get(name, name)]['reconv'] = reconv(CATNAME.get(name, name), **kw)


# Chi-Chi: o fundo rosa do cartão é quase a cor da pele e a máscara 'flat' abria um buraco no rosto: fundo pelo contorno escuro
redo('Chi-Chi (Dragon Ball, chibi, cartão rosa)', mask=__import__('r31_exfinal').OM(dark=100))
# Armin: olhos grandes cinza-oliva com pálpebra grossa e brilho à esquerda
_A5L = ['KKKKK', 'KDHDD', 'WDMMD', 'WMMLM', ' LLL ']
_A5R = ['KKKKK', 'DHDDK', 'DMMDW', 'MLMMW', ' LLL ']
more('Armin Arlert (Attack on Titan, chibi, polegar para cima)', [('block', 14, 6, _A5L), ('block', 14, 18, _A5R)], dict(LEG, D='H5', M='H4', L='M6', E='G3'))
# Mikasa: olhos cinza-castanhos semicerrados (o cabelo cobre o lado direito do rosto na arte, por isso o rosto é estreito)
more('Mikasa Ackerman (Attack on Titan, chibi)', [('block', 17, 10, ['KKK', 'DHM', 'LMM']), ('block', 18, 18, ['KKKK', 'DHMM', ' LLL'])], dict(LEG, D='G8', M='G14', L='H3'))
# Sasha: olhos âmbar com brilho; boca aberta fora
more('Sasha Braus (Attack on Titan, chibi, comendo)', [('paint', 16, 19, 9, 14), ('map', 12, 15, 9, 18, {'H7': 'E11', 'H2': 'E11', 'G1': 'E11', 'G9': 'E11'}), ('block', 12, 10, E3L), ('block', 12, 15, E4R())], dict(LEG, D='G8', M='F11', L='A13'))
# Chi-Chi (reconvertida): olhos pretos enormes da arte com 2 brilhos, cílios; sem o caramelo em volta e sem a boca aberta
_CC = [' KKKK ', 'KKHKKK', 'KKKKKK', 'KKKKHK', 'KKKKKK', ' KKKK ']
more('Chi-Chi (Dragon Ball, chibi, cartão rosa)', [('map', 19, 28, 5, 17, {'M9': 'E11', 'E12': 'E11', 'H7': 'E11', 'F2': 'E11'}),
    ('map', 26, 26, 4, 19, {}), ('block', 20, 4, _CC), ('block', 20, 13, _CC), ('block', 28, 6, ['EE', 'EE']), ('block', 28, 15, ['EE'])],
    dict(LEG, E='E11'))
# Erwin: olhos azul-acinzentados grandes (linhas 14-17), sem os pedaços cinza e caramelo
more('Erwin Smith (Attack on Titan, chibi)', [('map', 14, 17, 4, 18, {'H2': 'E14', 'H3': 'E14', 'H4': 'E14', 'M9': 'E14', 'G14': 'E14', 'G7': 'E14'}),
    ('block', 14, 5, E4L()), ('block', 14, 14, E4R())], dict(LEG, D='H5', M='C9', L='C2', E='E14'))
# Eren de cabelo preso: olhos cinza-azulados com olheiras (linhas 19-22), o direito um pouco mais caído
more('Eren Yeager (Attack on Titan, chibi, cabelo preso)', [('map', 19, 22, 4, 17, {'H7': 'E11', 'H2': 'E11', 'H4': 'E11', 'M9': 'E11', 'G17': 'E11', 'G8': 'E11'}),
    ('block', 19, 5, E4L()), ('block', 19, 13, E4R())], dict(LEG, D='H5', M='C14', L='H3'))
