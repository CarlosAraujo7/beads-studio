"""Gera `projetos3d.js` — PROJETOS DE BEADS EM 3D DE ENCAIXE (peças planas com dentes/fendas que se encaixam), a partir das fotos da `remessa 3D N` do usuário.

Um projeto = peças planas (cada uma é uma grade de contas, como um molde) + onde cada peça vai no objeto montado + passo a passo:
  {id, name, desc, level, view:[rx, ry], pieces:[{name, qty, rows, note?}], parts:[{piece:i, face, at:[X,Y,Z]}], steps:[...]}
  * `parts` tem UMA entrada por peça física (peça com qty 4 aparece 4 vezes); o gerador confere `qty == nº de parts`;
  * face = como a peça é vista DE FORA no objeto: front/back/right/left/top/bottom; `at` = [X,Y,Z] da célula local (0,0) no mundo (células; Y para baixo):
      front (X+cx, Y+cy, Z) · back (X-cx, Y+cy, Z) · right (X, Y+cy, Z-cx) · left (X, Y+cy, Z+cx) · top (X+cx, Y, Z+cy) · bottom (X+cx, Y, Z-cy)
    (cx, cy = coluna e linha da célula na peça). Peças de 1 conta de espessura: o plano passa pelo meio da célula;
  * letras = as da paleta (TPL_LEGEND do templates.js): w branco, k preto, R lima claro (B13), h verde escuro (B8), Ì marrom escuro (F11)…

As peças são LIDAS DAS FOTOS (grade desenhada por cima da foto ampliada: tools/gridview.py) — conferir contra a foto antes de montar.

uso:  python tools/make_3d.py     -> grava projetos3d.js na raiz (confere tamanhos e quantidades)
"""
import os, sys, json
SP = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SP)
sys.path.insert(0, SP)
from palette import HEX_BY_LETTER


def _cell_world(f, at, cx, cy):   # o mesmo mapeamento do app (cellWorld em index.html)
    X, Y, Z = at
    return {'front': (X + cx, Y + cy, Z), 'back': (X - cx, Y + cy, Z), 'right': (X, Y + cy, Z - cx), 'left': (X, Y + cy, Z + cx),
            'top': (X + cx, Y, Z + cy), 'bottom': (X + cx, Y, Z - cy)}[f]


def check_disjoint(p):
    """projetos de painéis que se cruzam (árvore de Natal): nenhuma conta do espaço pode ser de duas peças"""
    from boxsolve import rotate
    seen = {}
    for pt in p['parts']:
        rows = rotate(p['pieces'][pt['piece']]['rows'], pt.get('rot', 0))
        for cy, r in enumerate(rows):
            for cx, ch in enumerate(r):
                if ch == '.': continue
                c = _cell_world(pt['face'], pt['at'], cx, cy)
                assert c not in seen, (p['id'], 'conta em dobro', c, p['pieces'][pt['piece']]['name'], 'e', seen[c])
                seen[c] = p['pieces'][pt['piece']]['name']
    print(f"  painéis sem sobreposição: {len(seen)} contas no espaço")


def check_box(p):
    """projeto-caixa ('box': {'dims': [W,H,D], 'skip': [peças fora da caixa, ex.: asas]}): as partes têm que cobrir a casca W×H×D EXATAMENTE uma vez"""
    from boxsolve import rotate, shell
    W, H, D = p['box']['dims']; S = shell(W, H, D); seen = {}; extras = 0
    for pt in p['parts']:
        if pt['piece'] in p['box'].get('skip', []): continue
        rows = rotate(p['pieces'][pt['piece']]['rows'], pt.get('rot', 0))
        for cy, r in enumerate(rows):
            for cx, ch in enumerate(r):
                if ch == '.': continue
                c = _cell_world(pt['face'], pt['at'], cx, cy)
                if not (0 <= c[0] < W and 0 <= c[1] < H and 0 <= c[2] < D): extras += 1; continue      # orelhas, asas…: fora da caixa
                if c not in S and pt['piece'] in p['box'].get('inner_ok', []): extras += 1; continue     # haste do laço: entra pelo furo da tampa
                assert c in S, (p['id'], 'conta dentro da caixa mas fora da casca', c, p['pieces'][pt['piece']]['name'])
                assert c not in seen, (p['id'], 'conta em dobro', c, p['pieces'][pt['piece']]['name'], 'e', seen[c])
                seen[c] = p['pieces'][pt['piece']]['name']
    miss = S - set(seen)
    assert not miss, (p['id'], 'faltam', len(miss), sorted(miss)[:6])
    print(f"  caixa {W}×{H}×{D}: casca de {len(S)} contas coberta exatamente uma vez" + (f" (+{extras} contas fora da caixa: orelhas etc.)" if extras else ''))


def pieces_ok(p):
    for pc in p['pieces']:
        assert len({len(r) for r in pc['rows']}) == 1, (p['id'], pc['name'], 'linhas desiguais')
        for ch in ''.join(pc['rows']): assert ch == '.' or ch in HEX_BY_LETTER, (p['id'], ch)
    if p.get('box'): check_box(p)
    if p.get('disjoint'): check_disjoint(p)
    cnt = {}
    for pt in p['parts']: cnt[pt['piece']] = cnt.get(pt['piece'], 0) + 1
    for i, pc in enumerate(p['pieces']): assert cnt.get(i, 0) == pc['qty'], (p['id'], pc['name'], 'qty', pc['qty'], 'partes', cnt.get(i, 0))


# ---------- Maçã verde cortada (encaixe cruzado) — foto 5ae842cf (PicCollage), peças lidas a 15,2 px por conta ----------
MACA_A = [  # metade COM talo e folha, fenda por BAIXO (coluna central, linhas 8-13 vazia)
    '.........hh..',
    '.....n..hhh..',
    '.....nnhh....',
    '..RRR.nhRRR..',
    '.RwwwRnRwwwR.',
    'RwwwwwwwwwwwR',
    'RwwwwwwwwwwwR',
    'RwwwkwwwkwwwR',
    'Rwwwkw.wkwwwR',
    'Rwwwkw.wkwwwR',
    '.Rwwww.wwwwR.',
    '.Rwwww.wwwwR.',
    '..RRww.wwRR..',
    '....RR.RR....',
]
MACA_B = [  # metade SEM talo, fenda por CIMA (coluna central, linhas 0-5 vazia)
    '..RRR...RRR..',
    '.RwwwR.RwwwR.',
    'Rwwwww.wwwwwR',
    'Rwwwkw.wkwwwR',
    'Rwwwkw.wkwwwR',
    'Rwwwkw.wkwwwR',
    'RwwwwwwwwwwwR',
    '.RwwwwwwwwwR.',
    '.RwwwwwwwwwR.',
    '..RRwwRwwRR..',
    '....RR.RR....',
]
maca = {
    'id': 'maca-verde-encaixe', 'name': 'Maçã verde cortada (2 peças de encaixe)', 'level': 'Fácil', 'view': [-14, -38],
    'desc': 'Duas metades de maçã, cada uma com uma fenda no meio: uma fenda vem de baixo, a outra vem de cima. Elas se cruzam em ângulo reto e a maçã fica em pé sozinha, com talo e folha. Peças lidas da foto: confira antes de montar.',
    'pieces': [{'name': 'Metade com talo (fenda por baixo)', 'qty': 1, 'rows': MACA_A, 'note': 'talo e folha em cima'},
               {'name': 'Metade lisa (fenda por cima)', 'qty': 1, 'rows': MACA_B}],
    'parts': [{'piece': 0, 'face': 'front', 'at': [0, 0, 0]},
              {'piece': 1, 'face': 'right', 'at': [6, 3, 6]}],              # a linha 0 da metade lisa fica na linha 3 da outra (o talo ocupa as 3 primeiras)
    'steps': ['Monte as duas metades (cada uma 13 contas de largura). A da folha tem a fenda aberta embaixo; a outra, em cima.',
              'Passe o ferro em cada metade (papel de forno por cima), vire e passe do outro lado. Deixe esfriar sob um peso.',
              'Encaixe: desça a metade lisa pela fenda de cima até as duas fendas se cruzarem — uma metade fica de frente, a outra de lado.',
              'Se ficar solto, uma gotinha de cola na linha onde as metades se cruzam.'],
}


# ---------- Camarão em camadas — foto 32e0fc4b (peças 1-6 numeradas + folha), lidas a ~17,2 px por conta com tools/readcells.py ----------
# As peças são CAMADAS HORIZONTAIS empilhadas de cima (1) para baixo (6), com a folha embaixo: a ordem vem da numeração da foto e da altura do olho
# (peça 4) na foto de lado (≈ 58% da altura do corpo = 4ª de 6 camadas). Frente do camarão = esquerda (olhos na coluna 1 da cabeça).
SHR_CRISTA = ['.o.', 'ooo', 'oo.', '.o.']
SHR_DORSO = [  # 11 largura × 18 comprimento: listra rosa nas costas, 3 pontas brancas na cauda, patinhas dos lados (simétrica)
    '....ooo....', '....o]o....', '...oo]oo...', '...oo]oo...', '....o]o....', '....o]o....', '....o]o....', '.....].....',
    '...o]]]o...', '..o]o]o]o..', '.w]wo]ow]w.', 'wow.]]].wow', 'wo..o]o..ow', 'wo..wow..ow', '.w..wow..w.', '.w..www..w.',
    '.....w.....', '.....w.....']
SHR_CORPO = ['..oooooo.', 'ooooooooo', 'ooooooooo', 'ooooooooo', '..oooooo.']
SHR_CABECA = ['....owww.', '...ooo...', '.koooooo.', 'oooooooo.', '.oooooooo', 'oooooooo.', '.koooooo.', '...ooo...', '....owww.']
SHR_BARRIGA = ['.....oooww..', '.ooooo..ooww', 'ooooooo.....', 'oooooooo....', 'ooooooo.....', '.ooooo..ooww', '.....oooww..']
SHR_BASE = ['.ooo.', 'ooooo', 'ooooo', 'ooooo', '.ooo.']
SHR_FOLHA = ['...RRh....', '..RRRh.h..', '.RRRh..hR.', 'RRRRh.hRRR', 'RRRRh.hRRR', 'RRRRhhRRRR', 'RRRRRhRRRR', 'RRRRRRRRR.', '.RRRRRRRR.', '..RRRRRR..', '...RRRR...']
camarao = {
    'id': 'camarao-camadas', 'name': 'Camarão em camadas (7 peças)', 'level': 'Médio', 'view': [-36, 32], 'thick': 5,
    'desc': 'Camarão montado em camadas: 6 peças planas empilhadas de cima para baixo (a 1 é a crista, a 2 o dorso com a listra rosa e as três pontas brancas da cauda, a 4 a cabeça com os dois olhos pretos) sobre uma folha de vitória-régia. As peças e as cores foram lidas da foto; a ORDEM das camadas vem da numeração da foto e da altura do olho: confira ao empilhar.',
    'pieces': [{'name': 'Crista (topo)', 'qty': 1, 'rows': SHR_CRISTA, 'note': 'foto nº 1'},
               {'name': 'Dorso e cauda (listra rosa)', 'qty': 1, 'rows': SHR_DORSO, 'note': 'foto nº 2: a cauda (3 pontas brancas) fica para trás'},
               {'name': 'Corpo oval', 'qty': 1, 'rows': SHR_CORPO, 'note': 'foto nº 3'},
               {'name': 'Cabeça com olhos', 'qty': 1, 'rows': SHR_CABECA, 'note': 'foto nº 4: os 2 olhos pretos ficam na frente; as 3 brancas de cada lado são as patinhas'},
               {'name': 'Barriga com patas', 'qty': 1, 'rows': SHR_BARRIGA, 'note': 'foto nº 5'},
               {'name': 'Base redonda', 'qty': 1, 'rows': SHR_BASE, 'note': 'foto nº 6'},
               {'name': 'Folha (vitória-régia)', 'qty': 1, 'rows': SHR_FOLHA, 'note': 'a fenda escura fica na frente'}],
    'parts': [{'piece': 0, 'face': 'top', 'at': [3, 0, 4]},
              {'piece': 1, 'face': 'top', 'at': [0, 1, 0], 'rot': 3},
              {'piece': 2, 'face': 'top', 'at': [2, 2, 3]},
              {'piece': 3, 'face': 'top', 'at': [0, 3, 1]},
              {'piece': 4, 'face': 'top', 'at': [0, 4, 2]},
              {'piece': 5, 'face': 'top', 'at': [2, 5, 3]},
              {'piece': 6, 'face': 'top', 'at': [-1, 6, 0]}],
    'steps': ['Monte as 7 peças separadas, uma de cada. Cada uma é uma camada plana; passe o ferro em cada uma dos dois lados e deixe esfriar sob um peso.',
              'Na peça 2 (dorso e cauda) gire de lado: a ponta estreita com a listra rosa é a FRENTE e as três pontas brancas são a cauda, para trás.',
              'Empilhe de baixo para cima: folha, 6, 5, 4 (cabeça: os olhos pretos viram para a frente), 3, 2 e, por último, a crista 1 um pouco atrás da cabeça. Cole uma camada na outra.',
              'As camadas vistas de lado mostram as patinhas brancas saindo dos lados (peças 2, 4 e 5).'],
}


# ---------- Cubo Abelha (caixa 7×7×10 de encaixe) — foto cdd5403c, peças lidas a ~23 px por conta com tools/readcells.py ----------
# Conferido com tools/boxsolve.py: as 6 peças somam 290 contas = casca de uma caixa 7×7×10 e cobrem cada posição UMA vez (dente de uma peça = vão da vizinha).
# Cores: y amarelo (A4), D laranja claro/pêssego (A10), t âmbar translúcido (G5), k preto, c azul-claro (C5), w asas translúcidas.
BEE_FRENTE = ['yy.y.yy', '.kyyyk.', 'yyyyyyy', '.kyyyk.', 'kcyDDck', '.cDDDc.', 'DD.D.DD']
BEE_TRAS = ['tt.t.tt', '.ttktt.', 'tkktkkt', '.ttktt.', 'tkktkkt', '.ttktt.', 'tt.t.tt']
BEE_LAT_B = ['..y.y.y.y.', 'yyyyytytyt', '.yyyytyty.', 'kkyyytykyt', '.kyDDkDky.', 'kkDDDkDkDk', '..D.D.D.D.']
BEE_LAT_D = ['.y.y.y.y..', 'tytytyyyyy', '.ytytyyyy.', 'tykytyyykk', '.ykDkDDyk.', 'kDkDkDDDkk', '.D.D.D.D..']
BEE_TOPO = ['..y.y..', 'yyyyyyy', '.yyyyy.', 'yyyyyyy', '.yyyyy.', 'ttktktt', '.DyyyD.', 'ttktktt', '.DyyyD.', '..t.t..']
BEE_BASE = ['..y.y..', 'yyyyyyy', '.DyyyD.', 'DDyyyDD', '.DyyyD.', 'kkkkkkk', '.DyyyD.', 'kkkkkkk', '.DyyyD.', '..t.t..']
BEE_ASA = ['....ww.', '..wwwww', '.ww..ww', 'ww..ww.', 'ww.ww..', '.www...']
BEE_ASA_ESP = [r[::-1] for r in BEE_ASA]
abelha = {
    'id': 'abelha-cubo', 'name': 'Cubo Abelha (6 peças + 2 asas)', 'level': 'Difícil', 'view': [-30, -30], 'box': {'dims': [7, 7, 10], 'skip': [6, 7]},
    'desc': 'Cubo de abelha de 7×7×10 contas feito de 6 peças planas com dentes que se intercalam: os dentes de uma peça entram nos vãos da vizinha, sem sobrar nem faltar conta (conferido: 290 contas na casca). A frente tem os olhos (preto e azul-claro), a traseira é de âmbar translúcido com listras pretas, e as duas asas são de contas translúcidas. As peças foram lidas da foto; a posição das asas é aproximada.',
    'pieces': [{'name': 'Frente (olhos)', 'qty': 1, 'rows': BEE_FRENTE, 'note': 'dentes em cima (amarelos) e embaixo (laranja claro)'},
               {'name': 'Traseira (âmbar e preto)', 'qty': 1, 'rows': BEE_TRAS},
               {'name': 'Lateral esquerda', 'qty': 1, 'rows': BEE_LAT_D, 'note': 'a frente fica do lado direito da peça'},
               {'name': 'Lateral direita', 'qty': 1, 'rows': BEE_LAT_B, 'note': 'a frente fica do lado esquerdo da peça'},
               {'name': 'Tampa de cima', 'qty': 1, 'rows': BEE_TOPO, 'note': 'a fileira de baixo (dentes âmbar) fica na traseira'},
               {'name': 'Base', 'qty': 1, 'rows': BEE_BASE, 'note': 'a fileira de baixo (dentes âmbar) fica na traseira'},
               {'name': 'Asa direita', 'qty': 1, 'rows': BEE_ASA, 'note': 'contas translúcidas'},
               {'name': 'Asa esquerda', 'qty': 1, 'rows': BEE_ASA_ESP, 'note': 'contas translúcidas (espelho da outra)'}],
    'parts': [{'piece': 0, 'face': 'front', 'at': [0, 0, 9]},
              {'piece': 1, 'face': 'back', 'at': [6, 0, 0]},
              {'piece': 2, 'face': 'left', 'at': [0, 0, 0]},
              {'piece': 3, 'face': 'right', 'at': [6, 0, 9]},
              {'piece': 4, 'face': 'top', 'at': [0, 0, 0], 'rot': 2},
              {'piece': 5, 'face': 'bottom', 'at': [0, 6, 9]},
              {'piece': 6, 'face': 'top', 'at': [6, -1, 2]},
              {'piece': 7, 'face': 'top', 'at': [-6, -1, 2]}],
    'steps': ['Monte as 8 peças separadas (6 do cubo + 2 asas) e passe o ferro em cada uma, dos dois lados. Cada peça é uma parede plana com dentes nas bordas.',
              'Os dentes alternam de propósito: onde uma parede tem dente, a vizinha tem vão. Comece pela base e erga as quatro paredes (frente com os olhos de um lado, traseira de âmbar do outro).',
              'Feche com a tampa de cima: a fileira de dentes âmbar fica do lado da traseira. Se ficar frouxo, uma gota de cola nos cantos.',
              'Prenda as duas asas na parte de cima, uma de cada lado.'],
}


# ---------- Cubo Stitch (caixa 9×6×9 de encaixe, com orelhas) — foto c83bf166, peças lidas a ~12,2 px por conta com tools/readcells.py ----------
# Conferido com tools/boxsolve.py + check_box: 40+40 (laterais) + 61+61 (tampos) + 44 (traseira) + 44 (frente sem orelhas) = 290 = casca de 9×6×9.
# Cores: c turquesa (C5), | rosa (E10), k preto, w branco, & azul-escuro (D3).
ST_FRENTE = ['c.........c', '|c.......c|', '||c.....c||', '||c.....c||', '||cc...cc||', '.ccccccccc.', '..kkccckk..', '..kwcccwk..', '.ckwc&cwkc.', '.ccc...ccc.']
ST_TRAS = ['ccc...ccc', 'ccccccccc', '.ccc&ccc.', '.cc&&&cc.', 'ccccccccc', 'ccc...ccc']
ST_LATERAL = ['..cc..', 'cccccc', 'cccccc', '.cccc.', '.cccc.', '.cccc.', 'cccccc', 'cccccc', '..cc..']
ST_TAMPA = ['...ccc...', '.ccccccc.', '.ccccccc.', 'ccccccccc', 'ccccccccc', 'ccccccccc', '.ccccccc.', '.ccccccc.', '...ccc...']
stitch = {
    'id': 'stitch-cubo', 'name': 'Cubo Stitch (6 peças)', 'level': 'Médio', 'view': [-28, -30], 'box': {'dims': [9, 6, 9], 'skip': []},
    'desc': 'Cubo do Stitch de 9×6×9 contas, de peças planas com dentes que se intercalam (conferido: as 6 peças cobrem as 290 contas da casca sem sobrar nem faltar). A frente tem os olhos (preto e branco), o narizinho azul-escuro e as duas orelhas rosa que sobem acima da tampa; a traseira tem a marca azul-escura. As duas laterais são iguais, os dois tampos também. Peças lidas da foto.',
    'pieces': [{'name': 'Frente com orelhas e olhos', 'qty': 1, 'rows': ST_FRENTE, 'note': 'as orelhas sobem acima da tampa'},
               {'name': 'Traseira (marca azul)', 'qty': 1, 'rows': ST_TRAS},
               {'name': 'Lateral', 'qty': 2, 'rows': ST_LATERAL, 'note': 'duas iguais'},
               {'name': 'Tampo (cima e baixo)', 'qty': 2, 'rows': ST_TAMPA, 'note': 'dois iguais'}],
    'parts': [{'piece': 0, 'face': 'front', 'at': [-1, -4, 8]},
              {'piece': 1, 'face': 'back', 'at': [8, 0, 0]},
              {'piece': 2, 'face': 'left', 'at': [0, 0, 0], 'rot': 1},
              {'piece': 2, 'face': 'right', 'at': [8, 0, 8], 'rot': 1},
              {'piece': 3, 'face': 'top', 'at': [0, 0, 0]},
              {'piece': 3, 'face': 'bottom', 'at': [0, 5, 8]}],
    'steps': ['Monte as 6 peças (a lateral e o tampo são feitos 2 vezes) e passe o ferro em cada uma, dos dois lados. A frente é a única com as orelhas rosa.',
              'Os dentes alternam de propósito: onde uma parede tem dente, a vizinha tem vão. Comece por um tampo (será a base) e erga a frente, a traseira e as duas laterais.',
              'Feche com o outro tampo. As orelhas da frente ficam para cima, uma em cada canto. Se ficar frouxo, uma gota de cola nos cantos.'],
}


# ---------- Cubo Presente (caixa 7×7×7 de encaixe, com laço) — foto c4c8f01e, peças lidas ampliadas 8× (foto de baixa resolução e em ângulo) ----------
# Conferido com tools/boxsolve.py + check_box: 41+41 (faces A) + 39+39 (paredes B) + 29 (face de baixo) + 29 (face de cima, com a haste do laço) = 218 = casca de 7×7×7.
# Cores: r vermelho (F5), q rosa claro (E2, a fita), p rosa (E4, o laço).
GF_A = ['.rr.rr.', 'rrrqrrr', 'rrrqrrr', '.qqqqq.', 'rrrqrrr', 'rrrqrrr', '.rr.rr.']
GF_B = ['rrr.rrr', '.rrqrr.', '.rrqrr.', 'qqqqqqq', '.rrqrr.', '.rrqrr.', 'rrr.rrr']
GF_C = ['...q...', '.rrqrr.', '.rrqrr.', 'qqqqqqq', '.rrqrr.', '.rrqrr.', '...q...']
GF_D = ['...q...', '.rrqrr.', '.rrqrr.', 'qqq.qqq', '.rrqrr.', '.rrqrr.', '...q...']
GF_LACO = ['.p...p.', '.pp.pp.', 'ppppppp', '...p...', '...p...']
presente = {
    'id': 'presente-cubo', 'name': 'Cubo Presente com laço (7 peças)', 'level': 'Médio', 'view': [-30, -32], 'box': {'dims': [7, 7, 7], 'skip': [], 'inner_ok': [4]},
    'desc': 'Caixinha de presente de 7×7×7 contas, vermelha com fita rosa em cruz, de peças planas com dentes que se intercalam (conferido: as 6 faces cobrem as 218 contas da casca sem sobrar nem faltar). A tampa tem um furo no centro, onde entra a haste do laço rosa. Peças lidas de uma foto pequena e em ângulo: confira antes de montar.',
    'pieces': [{'name': 'Face com cruz (frente e trás)', 'qty': 2, 'rows': GF_A, 'note': 'duas iguais'},
               {'name': 'Parede com fita atravessada (lados)', 'qty': 2, 'rows': GF_B, 'note': 'duas iguais'},
               {'name': 'Face de baixo', 'qty': 1, 'rows': GF_C},
               {'name': 'Tampa (furo no centro)', 'qty': 1, 'rows': GF_D, 'note': 'o furo do centro recebe a haste do laço'},
               {'name': 'Laço', 'qty': 1, 'rows': GF_LACO, 'note': 'a haste de 2 contas desce pelo furo da tampa'}],
    'parts': [{'piece': 0, 'face': 'front', 'at': [0, 0, 6]},
              {'piece': 0, 'face': 'back', 'at': [6, 0, 0]},
              {'piece': 1, 'face': 'left', 'at': [0, 0, 0]},
              {'piece': 1, 'face': 'right', 'at': [6, 0, 6]},
              {'piece': 3, 'face': 'top', 'at': [0, 0, 0]},
              {'piece': 2, 'face': 'bottom', 'at': [0, 6, 6]},
              {'piece': 4, 'face': 'front', 'at': [0, -3, 3]}],
    'steps': ['Monte as 5 peças (a face com cruz e a parede são feitas 2 vezes) e passe o ferro em cada uma, dos dois lados.',
              'Os dentes alternam de propósito: onde uma parede tem dente, a vizinha tem vão. Comece pela face de baixo e erga as quatro paredes, alternando as que têm a fita atravessada com as que têm a cruz.',
              'Feche com a tampa e, por último, encaixe a haste do laço no furo do centro.'],
}


PROJECTS = [maca, camarao, abelha, stitch, presente]

# projetos da remessa 3D 2 (gráficos limpos): bloco de grama e abelha do Minecraft, árvore de Natal de encaixe
from r3d2_projects import R3D2
PROJECTS += R3D2

# remessa 3D 3: Minion (gráfico VitrumUP)
from r3d3_projects import R3D3
PROJECTS += R3D3

# cubos GERADOS a partir de moldes do catálogo (tools/cube3d.py + tools/make_cubes.py): mesma junta de dentes alternados dos cubos lidos das fotos
from make_cubes import cubes
for _c in cubes():
    _c.pop('_shell', None); PROJECTS.append(_c)


if __name__ == '__main__':
    for p in PROJECTS:
        pieces_ok(p)
        n = sum(sum(1 for r in pc['rows'] for ch in r if ch != '.') * pc['qty'] for pc in p['pieces'])
        print(f"{p['name']}: {sum(pc['qty'] for pc in p['pieces'])} peças, {n} contas")
    out = ['// Projetos de beads em 3D de ENCAIXE (peças planas que se encaixam). GERADO por tools/make_3d.py — veja o cabeçalho de lá para o formato.',
           'window.PROJECTS3D = [']
    for p in PROJECTS: out.append(json.dumps(p, ensure_ascii=False) + ',')
    out.append('];')
    open(os.path.join(ROOT, 'projetos3d.js'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('gravado projetos3d.js')
