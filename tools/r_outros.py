"""Remessas 1-12: imagens que NÃO estavam no catálogo (nunca convertidas, puladas na época, ou cujo molde o usuário excluiu).
Tudo entra na categoria "Outros" (série 'Outros'). Saída: data/final_outros.json  (use: add_templates.py data/final_outros.json --readd).

uso:  python tools/r_outros.py [filtro-de-nome ...]      -> grava o JSON (só sem filtro) e as prévias tools/out/outros_*.png

* gráficos com grade: r6.exact6 (cópia exata; só sai o fundo liso e o que não é desenho)
* fotos de peças prontas: r6.photo6 (grade de contas ajustada na foto) -> APROXIMADO
* itens que já tinham conversão exata guardada (remessas 5-12): tools/data/outros_pool.json  (nome -> linhas)
"""
import os, sys, json, glob
SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
os.environ['REMNUM'] = '1'
sys.path.insert(0, SP)
import r5, r6, outline as O
import photo7 as P7
from photo7 import hsv
from flat import render_flat


def R(n):
    r6.FILES = sorted(glob.glob(os.path.join(ROOT, 'remessas', f'remessa {n}', '*.*')))


def E(rem, idx, **kw):
    R(rem); return r6.exact6(idx, **kw)


def PH(rem, idx, p0, **kw):
    """foto de peça pronta (APROXIMADO): ver photo7.py. CHECK=1 grava tools/out/p7_REM_IDX.png com a grade sobre a foto"""
    if os.environ.get('CHECK'): kw['check'] = f'p7_{rem}_{idx}.png'
    return P7.convert(rem, idx, p0, **kw)


# --- funções de fundo/desenho usadas nas fotos
def pegwhite(c):            # placa/parede/papel claros ou cinza com sombra (baixa saturação, não é preto)
    h, s, v = hsv(c); return s < 0.20 and v >= 0.42
def warm(c):                # madeira, carpete, pele, papelão: matizes quentes com cor
    h, s, v = hsv(c); return (h <= 55 or h >= 335) and s >= 0.20 and v >= 0.22
def wood2(c):               # madeira/papelão em tons avermelhados ou alaranjados, com cor e luz média
    h, s, v = hsv(c); return (h <= 50 or h >= 345) and s >= 0.40 and 0.28 <= v <= 0.88
def perrybg(c, y, x):       # madeira alaranjada (mais avermelhada que as contas laranja), reflexos e sombras (as sombras só do meio para baixo: o chapéu tem a mesma cor)
    h, s, v = hsv(c)
    if 10 <= h <= 30.5 and s >= 0.45 and v >= 0.40: return True
    if h < 10 and s >= 0.60 and v >= 0.30 and y >= 7: return True
    if y >= 7 and (h <= 52 or h >= 345) and s >= 0.30 and 0.30 <= v <= 0.56: return True
    return 10 <= h <= 33 and 0.30 <= s <= 0.60 and v >= 0.85
def woodany(c):
    h, s, v = hsv(c); return wood2(c) or (10 <= h <= 50 and s <= 0.55 and v >= 0.50)
def cloth(c):               # pano/papel claro com sombras
    h, s, v = hsv(c); return s < 0.25 and v >= 0.42
def neutral(c):             # mármore/cinza neutro (as contas brancas têm um leve tom quente)
    h, s, v = hsv(c); return s < 0.075 and v >= 0.50
def lightwood(c):           # madeira clara/mármore/pano: claro e pouco saturado
    h, s, v = hsv(c); return s < 0.20 and v >= 0.62
def marble(c):
    h, s, v = hsv(c); return s < 0.22 and v >= 0.30
def greenonly(c):           # tapete de corte verde
    h, s, v = hsv(c); return 70 <= h <= 175 and s >= 0.18 and v <= 0.75
def paper(c):               # papel/fundo branco puro
    return min(c) >= 240
def skin(c):                # mão/pele + cinzas do fundo
    h, s, v = hsv(c); return ((h <= 55 or h >= 335) and s >= 0.10 and v >= 0.30) or (s < 0.14 and 0.28 <= v <= 0.92)
def stormbg(c, y, x):       # mesa de madeira acinzentada + canto escuro da foto (triângulo abaixo da diagonal); as contas pretas do desenho ficam
    h, s, v = hsv(c)
    if y >= 31: return True
    if v < 0.30 and y > 25.5 + 0.727 * x: return True
    return s < 0.12 and 0.40 <= v <= 0.72
def pegboardgray(c):        # placa branca com pinos: cinza neutro
    h, s, v = hsv(c); return s < 0.065 and v >= 0.45
def purplebg(c):            # fundo roxo (as argolas de metal ficam fora pela caixa)
    h, s, v = hsv(c); return 245 <= h <= 295 and s >= 0.28 and 0.40 <= v <= 0.95
def natsubg(c):             # placa transparente + carpete escuro (a cabeleira é rosa-choque: não pode ser tratada como fundo)
    h, s, v = hsv(c)
    return (s < 0.20 and v >= 0.36) or (0.2 <= v <= 0.55 and 10 <= h <= 45 and s < 0.6)
def ulqbg(c):               # madeira alaranjada sob a placa (a peça tem tons de bege/cinza-escuro: só os matizes quentes bem saturados são madeira)
    h, s, v = hsv(c)
    return (h <= 50 or h >= 335) and 0.25 <= s <= 0.75 and 0.35 <= v <= 0.85
def snakebg(c):             # madeira clara/mesa sob a placa transparente
    h, s, v = hsv(c); return 10 <= h <= 45 and s <= 0.45 and v >= 0.45
def card(c):                # papelão laranja
    h, s, v = hsv(c); return 22 <= h <= 52 and s >= 0.50 and 0.30 <= v <= 0.90


def groups(rows, gap=2):
    """separa peças que estão numa mesma imagem: contas a até `gap` células de distância ficam juntas. Devolve [(cy, cx, linhas)], de cima p/ baixo e esquerda p/ direita"""
    H, W = len(rows), len(rows[0])
    cells = [(y, x) for y in range(H) for x in range(W) if rows[y][x] != '.']
    par = {c: c for c in cells}
    def find(c):
        while par[c] != c: par[c] = par[par[c]]; c = par[c]
        return c
    S = set(cells)
    for (y, x) in cells:
        for dy in range(-gap, gap + 1):
            for dx in range(-gap, gap + 1):
                q = (y + dy, x + dx)
                if q in S: par[find(q)] = find((y, x))
    comp = {}
    for c in cells: comp.setdefault(find(c), []).append(c)
    out = []
    for cs in comp.values():
        ys = [c[0] for c in cs]; xs = [c[1] for c in cs]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sub = [''.join(rows[y][x] if (y, x) in set(cs) else '.' for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
        out.append(((y0 + y1) / 2, (x0 + x1) / 2, sub))
    return out


def kanto(rows):
    """as 8 insígnias da imagem: 3 em cima, 2 no meio (laterais), 3 embaixo -> ordenadas em leitura; devolve dict posição->linhas"""
    g = groups(rows, 2)
    g.sort(key=lambda t: (round(t[0] / 12), t[1]))
    return [t[2] for t in g]


def fill_holes(rows):
    """células vazias totalmente cercadas pelo desenho (não ligadas à borda) ganham a cor mais comum dos vizinhos — buracos criados por linhas da grade do JPEG"""
    H, W = len(rows), len(rows[0]); out = set(); st = []
    for y in range(H):
        for x in range(W):
            if (y in (0, H - 1) or x in (0, W - 1)) and rows[y][x] == '.': out.add((y, x)); st.append((y, x))
    while st:
        y, x = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + dy, x + dx)
            if 0 <= q[0] < H and 0 <= q[1] < W and q not in out and rows[q[0]][q[1]] == '.': out.add(q); st.append(q)
    g = [list(r) for r in rows]
    for _ in range(3):
        for y in range(H):
            for x in range(W):
                if g[y][x] == '.' and (y, x) not in out:
                    from collections import Counter
                    c = Counter(g[y + dy][x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))
                                if 0 <= y + dy < H and 0 <= x + dx < W and g[y + dy][x + dx] != '.')
                    if c: g[y][x] = c.most_common(1)[0][0]
    return [''.join(r) for r in g]

import palette as _P
# letras do cinza do fundo/grade da folha: H5 (e, com 120 cores, os cinzas escuros vizinhos H6/G17/M12)
_GREYGRID = {ord(c['letter']): '.' for c in _P.ALL if c['code'] in (('H5',) if _P.MODE == '24' else ('H5', 'H6', 'G17', 'M12'))}
_EEVEE = []
def eeveelutions():
    """folha 84x80 com as 9 evoluções do Eevee (gráfico com grade, remessa 5 img 7): converte tudo e separa os 9 sprites (leitura: cima->baixo, esq->dir)"""
    if not _EEVEE:
        rows = E(5, 7, px=dict(px=8.525, py=8.52, ox=0.9, oy=1.1, W=85, H=81), ref=(89, 89, 89), tol=14, mode=True, dist=20)
        H, W = len(rows), len(rows[0]); xb = [0, 28, 56, W]; yb = [0, 27, 54, H]     # 3x3 fixo (os pontinhos soltos da grade ligam os sprites entre si)
        for j in range(3):
            for i in range(3):
                part = [r[xb[i]:xb[i + 1]] for r in rows[yb[j]:yb[j + 1]]]
                if (j, i) != (1, 1): part = [r.translate(_GREYGRID) for r in part]       # cinza do fundo/grade (só o Umbreon tem corpo cinza-escuro)
                _EEVEE.append(fill_holes(O.drop_specks(O.trim(part), maxsize=5)))
    return _EEVEE

POOL = json.load(open(os.path.join(SP, 'data', 'outros_pool.json'), encoding='utf-8'))
def pool(name): return POOL[name]

# a regra geral manda teal escuro para ciano; o ciano da paleta é bem mais claro -> verde escuro
TEAL = [((54, 118, 120), 40, 'h'), ((42, 82, 81), 30, 'h')]
# cabelo marrom muito escuro (65,37,33) cairia em preto junto com o contorno -> marrom
HAIR = [((65, 37, 33), 20, 'n')]

CFG = [
 # ---------- gráficos com grade (cópia exata)
 ('Pintinho', lambda: E(1, 15)),
 ('Pokébola (pixel)', lambda: E(1, 26)),
 ('Batman (chibi)', lambda: E(1, 17)),
 ('Smiley do Red John', lambda: E(1, 31)),
 ('Flash (chibi, pixel)', lambda: E(1, 32, darkbg=30)),
 ('Dragonair', lambda: E(2, 17)),
 ('Luffy (chibi, pixel)', lambda: E(2, 18)),
 ('Pikachu na Poké Ball', lambda: E(2, 39)),
 ('Gato siamês (chibi)', lambda: E(2, 37, crop_img=(48, 35, 752, 737), mode=True, tol=60, ref=(255, 255, 255), px=dict(px=24.25, py=24.2, ox=0, oy=0, W=29, H=29))),
 ('Menino pescador de chapéu de palha', lambda: E(4, 3, ref=(217, 217, 217), tol=12, post=lambda r: O.trim([x for x in r if set(x) != {'w'}]))),
 ('Kazuma (KonoSuba, versão 2)', lambda: E(3, 2, crop_img=(14, 14, 552, 806), colmap=TEAL)),
 ('Kakashi (chibi)', lambda: E(3, 15)),
 ('Naruto (chibi, pixel)', lambda: E(3, 22)),
 ('Mona Lisa', lambda: E(12, 12, ref=(0, 255, 0), tol=1)),
 ('Asas da Liberdade (gráfico azul e branco)', lambda: E(1, 12, ref=(226, 222, 212), tol=30, crop=(1, 35, 0, 34), colmap=[((214, 205, 196), 10, 'w'), ((52, 53, 48), 10, 'd'), ((6, 48, 73), 20, 'b')])),
]
KANTO_NAMES = ['Insígnia da Terra (Kanto)', 'Insígnia da Pedra (Kanto)', 'Insígnia da Cascata (Kanto)', 'Insígnia do Vulcão (Kanto)',
               'Insígnia do Trovão (Kanto)', 'Insígnia do Pântano (Kanto)', 'Insígnia da Alma (Kanto)', 'Insígnia do Arco-íris (Kanto)']
KANTO_ORDER = [0, 1, 2, 3, 4, 5, 6, 7]      # posição na leitura (cima->baixo, esq->dir) -> nome acima; confira no resumo impresso
for i, n in enumerate(KANTO_NAMES):
    CFG.append((n, (lambda i=i: kanto(E(2, 25))[KANTO_ORDER[i]])))

def _quad(rows, y0, y1, x0, x1):
    return O.trim([r[x0:x1] for r in rows[y0:y1]])

_KEY = []
def keychains():
    """foto com 2 chaveiros (remessa 2 img 9): converte, apaga as argolas e a parte de cima, separa esquerdo/direito"""
    if not _KEY:
        rows = PH(2, 9, 18.1, spread=0.06, bg=purplebg, pal=[
            ((16, 9, 19), 'k'), ((146, 132, 214), 'v'), ((170, 175, 214), 'v'), ((182, 13, 36), 'r'), ((131, 11, 32), 'r'), ((199, 174, 161), 's'),
            ((161, 151, 149), 'm'), ((34, 29, 52), 'k'), ((60, 48, 83), 'u'), ((114, 106, 135), 'm')], clear=[(0, 14, 0, 40)])
        _KEY.extend([O.trim([r[:16] for r in rows]), O.trim([r[17:] for r in rows])])
    return _KEY

_H4 = []
def hero4():
    """foto com 4 heróis chibi (img 29 da remessa 1): converte tudo, apaga a marca d'água e separa pelos quadrantes"""
    if not _H4:
        rows = PH(1, 29, 8.8, spread=0.06, bg=pegwhite, pal=[
            ((50, 20, 41), 'k'), ((60, 40, 56), 'k'), ((89, 73, 88), 'd'), ((127, 21, 39), 'r'), ((163, 139, 32), 'a'), ((51, 71, 130), 'b'),
            ((94, 170, 141), 'g'), ((121, 121, 124), 'm'), ((179, 155, 109), 's'), ((187, 191, 183), 'l')])
        rows = [''.join('.' if (22 <= y <= 30 and 16 <= x <= 22) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]       # logotipo da marca d'água entre os 4
        h, w = len(rows), len(rows[0]); ym = 28; xm = 22
        _H4.extend([_quad(rows, 0, ym, 0, xm), _quad(rows, 0, ym, xm, w), _quad(rows, ym, h, 0, xm), _quad(rows, ym, h, xm, w)])
    return _H4

EEVEE_NAMES = ['Eevee (sentado)', 'Jolteon (sentado)', 'Flareon (sentado)', 'Vaporeon (sentado)', 'Umbreon (sentado)', 'Espeon (sentado)',
               'Leafeon (sentado)', 'Glaceon (sentado)', 'Sylveon (sentado)']
for i, n in enumerate(EEVEE_NAMES):
    CFG.append((n, (lambda i=i: eeveelutions()[i])))

# ---------- fotos de peças prontas (aproximado): grade de contas ajustada na foto + paleta de cores escolhida olhando a foto
CFG += [
 ('Capitão América (chibi, foto)', lambda: PH(1, 24, 17.5, spread=0.08, bg=pegwhite, pal=[
     ((26, 26, 30), 'k'), ((64, 47, 47), 'k'), ((13, 87, 145), 'b'), ((29, 109, 165), 'b'), ((18, 59, 98), 'b'), ((148, 24, 26), 'r'),
     ((140, 95, 73), 't'), ((171, 176, 185), 'w'), ((120, 130, 154), 'w')])),
 ('Togepi (foto, papelão)', lambda: PH(2, 35, 19.5, spread=0.06, bbox=(130, 300, 590, 800), bg=card, pal=[
     ((210, 195, 155), 's'), ((198, 214, 226), 'w'), ((17, 16, 11), 'k'), ((40, 38, 34), 'k'), ((24, 124, 202), 'b'), ((176, 52, 47), 'r'),
     ((164, 139, 107), 's'), ((97, 84, 57), 'k'), ((146, 170, 196), 'w')])),
 ('Hulk (chibi, foto)', lambda: hero4()[0]),
 ('Gavião Arqueiro (chibi, foto)', lambda: hero4()[1]),
 ('Homem de Ferro (chibi, foto)', lambda: hero4()[2]),
 ('Capitão América (chibi, foto 2)', lambda: hero4()[3]),
 ('Pantera Cor-de-Rosa (foto)', lambda: PH(3, 29, 42.4, spread=0.06, bg=woodany, flood=False, pal=[
     ((234, 155, 210), 'p'), ((207, 138, 163), 'p'), ((224, 247, 254), 'w'), ((219, 200, 85), 'y'), ((51, 45, 56), 'k'), ((194, 48, 116), 'r')])),
 ('Perry, o Ornitorrinco (foto)', lambda: PH(4, 6, 63, spread=0.06, bg=perrybg, flood=False, pal=[
     ((81, 175, 164), 'g'), ((71, 158, 139), 'g'), ((104, 194, 181), 'g'), ((105, 178, 161), 'g'), ((251, 180, 87), 'o'), ((245, 167, 72), 'o'),
     ((62, 41, 45), 'k'), ((213, 203, 183), 'w'), ((69, 92, 80), 'h'), ((130, 138, 76), 'g'), ((111, 131, 98), 'g'), ((105, 120, 107), 'h')])),
 ('Monstrinho marrom (foto)', lambda: PH(2, 38, 47.5, spread=0.06, bg=lightwood, pal=[
     ((36, 42, 55), 'k'), ((52, 55, 69), 'k'), ((80, 74, 76), 'k'), ((96, 93, 101), 'k'), ((133, 107, 105), 'n'), ((148, 133, 128), 'n'),
     ((212, 204, 210), 'q'), ((187, 169, 173), 'q')])),
 ('Stitch (foto, na mão)', lambda: PH(3, 5, 46.8, spread=0.06, bbox=(130, 350, 1030, 1160), bg=skin, pal=[
     ((91, 138, 179), 'b'), ((11, 9, 7), 'k'), ((36, 20, 18), 'k'), ((164, 209, 205), 'e'), ((134, 113, 153), 'u'), ((13, 42, 107), 'b'), ((84, 79, 71), 'd')])),
 ('Yami Yugi (foto, contas grandes)', lambda: PH(3, 34, 53.7, spread=0.06, bg=cloth, pal=[
     ((31, 21, 17), 'k'), ((80, 41, 34), 'k'), ((201, 156, 10), 'y'), ((157, 102, 9), 'a'), ((161, 114, 68), 't'), ((111, 57, 72), 'p'),
     ((161, 74, 118), 'p'), ((186, 128, 155), 'p'), ((14, 28, 73), 'b')])),
 ('Natsu Dragneel (chibi, foto)', lambda: PH(6, 11, 43, spread=0.06, bg=natsubg, pal=[
     ((28, 22, 21), 'k'), ((57, 41, 36), 'k'), ((177, 43, 94), 'r'), ((134, 31, 61), 'r'), ((217, 63, 131), 'p'), ((102, 71, 58), 'n'), ((132, 105, 98), 'n'),
     ((191, 148, 121), 's'), ((181, 184, 182), 'w'), ((141, 140, 138), 'm'), ((222, 187, 157), 's'), ((165, 133, 71), 'a')])),
 ('Ulquiorra (foto, corpo inteiro)', lambda: PH(3, 32, 19.4, spread=0.05, bg=ulqbg, flood=True, clear=[(0, 36, 0, 8)], pal=[
     ((28, 20, 16), 'k'), ((47, 33, 26), 'k'), ((64, 45, 34), 'k'), ((74, 59, 49), 'd'), ((90, 79, 68), 'd'), ((234, 222, 209), 'w'), ((202, 181, 162), 'w'),
     ((116, 63, 31), 'a'), ((137, 123, 113), 'm'), ((167, 152, 140), 'l'), ((168, 33, 53), 'r'), ((197, 122, 61), 'a')])),
 ('Chaveiro chibi de cabelo vermelho', lambda: keychains()[0]),
 ('Chaveiro chibi de cabelo lilás', lambda: keychains()[1]),
 ('Caveira de Luffy (foto)', lambda: PH(4, 1, 27.8, spread=0.06, bg=neutral, pal=[
     ((28, 27, 28), 'k'), ((46, 41, 39), 'k'), ((70, 67, 65), 'k'), ((209, 146, 44), 'a'), ((187, 75, 46), 'r'), ((203, 192, 172), 'w'), ((172, 169, 161), 'w'),
     ((155, 122, 39), 'a')])),
 ('Togepi (foto, fundo branco)', lambda: PH(5, 43, 42.5, spread=0.06, bg=paper, pal=[
     ((215, 193, 130), 's'), ((209, 203, 203), 'w'), ((60, 53, 48), 'k'), ((189, 39, 49), 'r'), ((76, 171, 199), 'c'), ((169, 181, 192), 'w'),
     ((126, 104, 67), 's'), ((182, 148, 103), 's'), ((162, 147, 148), 'w')])),
 ('Bob Esponja (foto)', lambda: PH(5, 21, 13.2, spread=0.08, bg=paper, pal=[
     ((231, 190, 33), 'y'), ((74, 67, 47), 'k'), ((36, 31, 25), 'k'), ((140, 88, 52), 'n'), ((188, 145, 34), 'a'), ((220, 185, 101), 'y'),
     ((173, 120, 88), 't'), ((192, 184, 180), 'w'), ((31, 111, 165), 'b')])),
]

# ---------- conversões exatas já feitas antes (remessas 5-12), guardadas em data/outros_pool.json
for n in POOL:
    CFG.append((n, (lambda n=n: pool(n))))

if __name__ == '__main__':
    only = sys.argv[1:]
    out = []; items = []
    for n, fn in CFG:
        if only and not any(o in n for o in only): continue
        try:
            __import__('r5').SKIN_ON = __import__('r5').skin_for(n, 'Outros')
            r = fn(); out.append((n, 'Outros', r)); items.append((f'{n[:26]} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(out), 'templates')
    if not only: json.dump(out, open(os.path.join(SP, 'data', 'final_outros' + __import__('palette').sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'outros_{k // 12}' + __import__('palette').sfx() + '.png'), scale=8, W=1900)
