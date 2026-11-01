"""10ª revisão (2026-11-01, CLAUDE.md §7.32): 12 moldes da remessa 26 que ele listou. Base = o que está no catálogo (Zero e Estelar têm ajustes dele). Grava só por retoque.gravar.
  BEADPAL=120 python tools/rev10.py sheet "nome" r0 r1 c0 c1 [célula]   leitura: arte com a grade do molde | molde, em tools/out/r10s.png, e o molde em texto
  BEADPAL=120 python tools/rev10.py [trecho...] [--H n]                 prévia tools/out/r10_N.png (arte | antes | depois)
  BEADPAL=120 python tools/rev10.py --apply"""
import os, sys
os.environ['REMNUM'] = '26'; os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numpy as np
import r26_exfinal as X
import r5, loose, outline as O, retoque, palette as P, shrink, tplfile
import facetools as FT
from tplfile import parse
from PIL import Image, ImageDraw
R = X.R; L = {c['code']: c['letter'] for c in P.ALL}; LAB = shrink.LAB
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}
OUT = os.path.join(HERE, 'out')
T = os.path.join(ROOT, 'templates.js')
# nome: (imagem, recorte da folha)
SRC = {'Seiya de Pégaso (foto de peça pronta, WOW)': (0, None), 'Seiya de Pégaso (chibi, adesivo)': (36, None), 'Hyoga de Cisne (pixel, corpo inteiro, versão 2)': (13, (150, 0, 290, 200)),
       'Shiryu de Dragão (pixel, corpo inteiro, armadura verde)': (13, (290, 0, 439, 200)), 'Ikki de Fênix (pixel, corrente vermelha)': (13, (170, 195, 439, 395)),
       'Seiya de Pégaso (pixel, corpo inteiro, versão 3)': (13, (0, 195, 170, 395)), 'Zero (Code Geass, foto de chaveiro)': (2, None), 'Maga de cabelo castanho e fogo (pixel)': (41, None),
       'Estelar (Jovens Titãs, gráfico)': (5, None), 'Ciborgue (Jovens Titãs, gráfico)': (40, None), 'Maka Albarn (Soul Eater, chibi)': (42, None), 'Diablo (Tensura, chibi, pixel)': (34, None)}


def raw_of(n):
    i, box = SRC[n]
    im = np.array(R.source_img(i, box))
    return im


def sheet(n, rows, r0, r1, c0, c1, cell=22, out=None):
    raw = raw_of(n)
    ox, oy, cw, ch = FT.align(raw, rows, verbose=True)
    r1 = min(r1, len(rows) - 1); c1 = min(c1, len(rows[0]) - 1)
    W, H = (c1 - c0 + 1) * cell, (r1 - r0 + 1) * cell
    crop = Image.fromarray(raw).crop((int(ox + c0 * cw), int(oy + r0 * ch), int(ox + (c1 + 1) * cw), int(oy + (r1 + 1) * ch))).resize((W, H), Image.NEAREST)
    m = Image.new('RGB', (W, H), (98, 70, 140)); d = ImageDraw.Draw(m)
    for y in range(r0, r1 + 1):
        for x in range(c0, c1 + 1):
            c = rows[y][x]
            if c != '.': d.rectangle(((x - c0) * cell, (y - r0) * cell, (x - c0 + 1) * cell - 1, (y - r0 + 1) * cell - 1), fill=HEX[c])
    for im in (crop, m):
        d = ImageDraw.Draw(im)
        for x in range(c0, c1 + 2): d.line([((x - c0) * cell, 0), ((x - c0) * cell, H)], fill=(255, 255, 255))
        for y in range(r0, r1 + 2): d.line([(0, (y - r0) * cell), (W, (y - r0) * cell)], fill=(255, 255, 255))
        for x in range(c0, c1 + 1): d.text(((x - c0) * cell + 2, 1), str(x), fill=(255, 255, 0))
        for y in range(r0, r1 + 1): d.text((1, (y - r0) * cell + 2), str(y), fill=(0, 255, 255))
    S = Image.new('RGB', (W * 2 + 10, H), (40, 40, 44)); S.paste(crop, (0, 0)); S.paste(m, (W + 10, 0))
    S.save(out or os.path.join(OUT, 'r10s.png'))
    print(n, len(rows[0]), len(rows)); print('     ' + ''.join(str(x % 10) for x in range(c0, c1 + 1)))
    print('\n'.join('%3d  %s' % (y, rows[y][c0:c1 + 1]) for y in range(r0, r1 + 1)))
    return S


def put(rows, blocks):
    g = [list(x) for x in rows]
    for y0, x0, lines in blocks:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c != ' ': g[y0 + j][x0 + i] = c
    return [''.join(x) for x in g]


FIX = {}


def fix(name):
    def d(fn): FIX[name] = fn; return fn
    return d


def recolor(rows, m):
    return [''.join(m.get(c, c) for c in r) for r in rows]


def clear_cells(rows, cells):
    g = [list(r) for r in rows]
    for y, x in cells: g[y][x] = '.'
    return [''.join(r) for r in g]


def calm(rows, keep=''):
    """conta isolada: se 3 ou 4 vizinhos têm a mesma cor e ela é outra, vira a dos vizinhos. O contorno e as letras em keep não mudam"""
    H, W = len(rows), len(rows[0]); g = [list(r) for r in rows]
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = rows[y][x]
            if c in '.k' or c in keep: continue
            nb = [rows[y + 1][x], rows[y - 1][x], rows[y][x + 1], rows[y][x - 1]]
            for v in set(nb):
                if v not in '.k' and v != c and nb.count(v) >= 3: g[y][x] = v
    return [''.join(r) for r in g]


def edge_dark(rows, letters, skip=lambda y, x: False):
    """o contorno da arte é preto: conta escura que encosta no vazio vira k"""
    H, W = len(rows), len(rows[0]); g = [list(r) for r in rows]
    for y in range(H):
        for x in range(W):
            if rows[y][x] not in letters or skip(y, x): continue
            if any(not (0 <= v < H and 0 <= u < W) or rows[v][u] == '.' for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1))): g[y][x] = 'k'
    return [''.join(r) for r in g]


@fix('Seiya de Pégaso (foto de peça pronta, WOW)')
def seiya_foto(r):
    """o fundo escuro da foto engoliu as contas pretas e cortou a perna: da linha 33 para baixo ela foi lida conta a conta na foto ampliada (coxa, dobra com o dourado, canela e ponta do pé)"""
    g = [list(l) for l in r]
    for y in range(33, len(g)):
        for x in range(24, len(g[0])): g[y][x] = '.'
    r = [''.join(l) for l in g]
    return put(r, [(33, 26, ['kkllmliik']), (34, 28, ['klmiiik']), (35, 27, ['kkkmlilk']), (36, 26, ['kakklmlk']), (37, 26, ['kyakllk']), (38, 27, ['kaylk']), (39, 27, ['klilk']), (40, 28, ['kllik']), (41, 29, ['kliik']), (42, 30, ['kkiik']), (43, 32, ['kk'])])


@fix('Seiya de Pégaso (chibi, adesivo)')
def seiya_chibi(r):
    """o pé direito estava cortado: a ponta branca da bota saiu junto com o halo do adesivo. Lida na arte (1 conta = 9,15 px): 1 linha e 1 coluna a mais"""
    W = len(r[0]) + 1
    r = [l.ljust(W, '.') for l in r] + ['.' * W]
    return put(r, [(43, 29, ['ww']), (44, 30, ['wwk']), (45, 31, ['mwk'])])


@fix('Hyoga de Cisne (pixel, corpo inteiro, versão 2)')
def hyoga(r):
    """como no anime: armadura branca e azul-gelo (estava azul-marinho) e cabelo loiro (o laranja saiu); o azul escuro da borda virou contorno preto; rosto lido na arte: um olho azul, a franja cobre o outro"""
    hair = {'a': 'A', 'Ò': 'a', 'Ô': 'a', 'o': 'a', 'Õ': 'a', 'Ö': 'a', 'B': 'A', 'Ø': 'a', 'V': 'a', 'Q': 'a', 'n': 'a', 'Ü': 'a', 'Ù': 'a', 'd': 'a'}
    armor = {'!': '3', '&': '3', '/': '3', '3': 'b', 'b': '1', '1': 'e', '2': '1', '#': '1', 'c': '1', '5': 'e', '9': '1', 'e': '7', '*': 'e', ';': 'e', '8': 'e', '$': 'e', '%': 'b', 'u': 'b', 'v': 'e', '4': '3'}
    HAIR = lambda y, x: y <= 6 and x >= 12
    r = edge_dark(r, set('!&/Ùd m Þ Ø4u'.replace(' ', '')), HAIR)
    out = []
    for y, l in enumerate(r):
        out.append(''.join(hair.get(c, c) if HAIR(y, x) and c not in '!&b7w3' else armor.get(c, c) for x, c in enumerate(l)))
    out = calm(out, keep='sw')
    return put(out, [(9, 13, ['kk']), (10, 12, ['ysswbsj']), (11, 12, ['yysskss']), (12, 12, ['aaysssk']), (13, 12, ['ayaÑk'])])


@fix('Shiryu de Dragão (pixel, corpo inteiro, armadura verde)')
def shiryu(r):
    """armadura verde, como no anime (a arte é azul), com contorno preto; pele bege clara; os vãos brancos entre o braço, o cabelo e as pernas são fundo e saem; rosto simples, de frente"""
    r = clear_cells(r, [(26, 7), (26, 8), (27, 8), (26, 12), (27, 12), (24, 13), (25, 13), (26, 13), (9, 23), (10, 23), (11, 22), (11, 23)])
    r = edge_dark(r, set('!&/ÙdmÞØ'))
    m = {'!': 'h', '&': 'h', '/': 'h', '3': 'h', 'b': 'f', '9': 'f', '%': 'h', '#': 'f', 'c': 'f', '5': 'f', '2': 'f', '1': 'g', '$': 'g', ';': 'g', 'x': 'g', '+': 'g', 'e': 'g', '7': 'R', '*': 'g', '8': 'g',
         'Ô': 's', 'Ñ': 's', 'Ã': 's', 'q': 's', 'Ò': 'Ñ', 'Õ': 'Ñ', 'n': 'Ñ', 'Ö': 'Ñ', 'Ì': 'k', 'Þ': 'k', 'Ø': 'k', 'V': 'k', 'Q': 'k', 'Ü': 'Ñ'}
    r = calm(recolor(r, m), keep='s')
    return put(r, [(9, 16, ['kkkkkkk']), (10, 16, ['ksssssk']), (11, 16, ['kskssks'[:6] + 'k']), (12, 17, ['kÑssk'])])


@fix('Ikki de Fênix (pixel, corrente vermelha)')
def ikki(r):
    """rosto pequeno, de 3/4: 1 olho de 1 conta sob a franja; pele bege clara"""
    return put(r, [(9, 34, ['Ñssk']), (10, 34, ['skss'[:3] + 'k']), (11, 34, ['ssk'])])


@fix('Seiya de Pégaso (pixel, corpo inteiro, versão 3)')
def seiya3(r):
    """a tiara na arte é uma tira fina dourada: o verde-oliva saiu, da testa e das botas"""
    def green(c): return c != '.' and LAB[c][1] < -4 and LAB[c][2] > 8
    r = [''.join(('y' if LAB[c][0] > 55 else 'a') if green(c) else c for c in l) for l in r]
    return put(r, [(5, 22, ['a']), (6, 22, ['a']), (7, 23, ['a']), (8, 24, ['ak']), (9, 24, ['yak']), (10, 24, ['yak']), (11, 25, ['ak'])])


@fix('Zero (Code Geass, foto de chaveiro)')
def zero(r):
    """não é chaveiro: o cinza da borda e dos panos era reflexo nas contas pretas da foto e vira preto; o contorno perde 1 camada onde estava duplo; sem pontas de 1 conta"""
    GR = {'m', 'd', 'l', 'Ù', 'W', 'Ø', 'i'}
    H, W = len(r), len(r[0]); g = [list(l) for l in r]
    seen = set(); st = [(y, x) for y in range(H) for x in range(W) if g[y][x] == '.']; seen.update(st)
    while st:
        y, x = st.pop()
        for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= v < H and 0 <= u < W and (v, u) not in seen and g[v][u] in GR:
                seen.add((v, u)); g[v][u] = 'k'; st.append((v, u))
    for y in range(H):
        for x in range(W):
            if g[y][x] in ('m', 'd', 'Ù'): g[y][x] = 'k'
    def out(y, x, a): return not (0 <= y < H and 0 <= x < W) or a[y][x] == '.'
    a = [l[:] for l in g]
    for y in range(H):
        for x in range(W):
            if a[y][x] != 'k': continue
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if out(y + dy, x + dx, a) and 0 <= y - dy < H and 0 <= x - dx < W and a[y - dy][x - dx] == 'k' and (0 <= y - 2 * dy < H and 0 <= x - 2 * dx < W and a[y - 2 * dy][x - 2 * dx] != '.'):
                    g[y][x] = '.'
    for _ in range(2):
        a = [l[:] for l in g]
        for y in range(H):
            for x in range(W):
                if a[y][x] == 'k' and sum(not out(y + dy, x + dx, a) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1: g[y][x] = '.'
    r = X.lg(O.trim([''.join(l) for l in g]))
    return put(r, [(13, 3, ['k']), (13, 25, ['k']), (13, 28, ['k']), (15, 6, ['k']), (30, 0, ['r']), (31, 0, ['r']), (31, 9, ['k'])])         # reflexos soltos na borda


@fix('Maga de cabelo castanho e fogo (pixel)')
def maga(r):
    """lido na arte: pálpebra preta, branco e íris azul de 1 conta em cada olho, rosto liso que afina no queixo, sem boca"""
    return put(r, [(9, 13, ['kkkÑkkk']), (10, 12, ['kw9}}}9k']), (11, 13, ['}}}}}}k']), (12, 14, ['Ñ}}}Ñk']), (13, 14, ['Ñ}}Ñ'])])


@fix('Estelar (Jovens Titãs, gráfico)')
def estelar(r):
    """a papada: faltava a linha do maxilar. Na arte o queixo afina e o pescoço aparece ao lado dele; boca de 2 contas, como na arte. Os olhos ficam como ele ajustou"""
    return put(r, [(8, 23, ['É']), (9, 23, ['Ñ']), (10, 21, ['ÉÉ']), (11, 18, ['ÑÑkÑÑÑk'])])


@fix('Ciborgue (Jovens Titãs, gráfico)')
def ciborgue(r):
    """lido na arte: contorno no lado esquerdo do rosto, olho branco e olho vermelho na faixa escura, lábio claro, e o sorriso é a linha preta sobre os dentes brancos"""
    return put(r, [(3, 16, ['kÒÒkkikÕ&krk']), (4, 16, ['kÒÒÒaaaaÒÒlk']), (5, 17, ['kÒÒÒÒkkkkÒk']), (6, 16, ['kÒÒkÒlwwwlkk'])])


@fix('Maka Albarn (Soul Eater, chibi)')
def maka(r):
    """olhos: pálpebra preta em cima e o verde-oliva da arte, do mesmo tamanho"""
    return put(r, [(10, 21, ['kkk']), (11, 16, ['kkk']), (11, 21, ['JJV']), (12, 16, ['JJV']), (12, 21, ['JPs']), (13, 16, ['JPs'])])


@fix('Diablo (Tensura, chibi, pixel)')
def diablo(r):
    """os dois olhos na mesma altura, dentro do rosto, como na arte"""
    return put(r, [(10, 22, ['kqkkq']), (11, 21, ['kyÂÂyk']), (12, 21, ['kyÂÂyÂk']), (13, 21, ['kÂÂÂÂÂ']), (14, 21, ['kÂÂÂÂÂ'])])


def main():
    cat = {t['name']: t for t in parse(T)['items']}
    a = sys.argv[1:]
    if a and a[0] == 'sheet':
        n = next(k for k in SRC if a[1].lower() in k.lower())
        rows = FIX[n](cat[n]['rows']) if '--new' in a and n in FIX else cat[n]['rows']
        sheet(n, rows, int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]) if len(a) > 6 and a[6].isdigit() else 22)
        return
    args = [x for x in a if not x.startswith('--')]
    H = int(a[a.index('--H') + 1]) if '--H' in a else 560
    if '--H' in a: args.remove(str(H))
    new = {}; items = []
    for n, fn in FIX.items():
        if args and not any(x.lower() in n.lower() for x in args): continue
        if n not in cat: print('NÃO ESTÁ NO CATÁLOGO:', n); continue
        r5.SKIN_ON = False
        new[n] = O.trim(fn(cat[n]['rows']))
        items.append((f'{n[:40]} ANTES {len(cat[n]["rows"][0])}x{len(cat[n]["rows"])}', Image.fromarray(raw_of(n)), cat[n]['rows']))
        items.append((f'DEPOIS {len(new[n][0])}x{len(new[n])} soltas {loose.loose_count(new[n])}', None, new[n]))
    if '--apply' in a:
        retoque.gravar({cat[n]['id']: new[n] for n in new}, {cat[n]['id']: cat[n]['rows'] for n in new}); return
    per = 4 if H > 340 else 8
    for f in os.listdir(OUT):
        if f.startswith('r10_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(items), per):
        R.pairsheet(items[k:k + per], os.path.join(OUT, f'r10_{k // per}.png'), H=H)
    print('folhas', (len(items) + per - 1) // per)


if __name__ == '__main__':
    main()
