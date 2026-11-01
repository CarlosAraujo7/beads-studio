"""Revisão de 2026-11-01 (CLAUDE.md §7.30): moldes da remessa 25 que ele listou. Base = o que está no catálogo; só troca o molde se ainda é o que foi lido (retoque.gravar).
  BEADPAL=120 python tools/rev9.py [trecho...]     prévia tools/out/r9_N.png (arte | antes | depois)
  BEADPAL=120 python tools/rev9.py --apply         grava"""
import os, sys, json
os.environ['REMNUM'] = '25'; os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numpy as np, cv2
import r25_exfinal as X
import r5, r6, shrink, loose, outline as O, retoque
import palette as P
from tplfile import parse
from PIL import Image
E = r6.exact6; R = X.R; LAB = shrink.LAB; L = {c['code']: c['letter'] for c in P.ALL}
OUT = os.path.join(HERE, 'out')


def vote(rows, size=50, de=13.0, empty_at=0.6, black=1.0):
    """redução por VOTO EM GRUPO: na janela de cada conta, tons parecidos (ΔLab < de) somam os votos e ganha o grupo maior, com a letra mais comum dele.
    A maioria simples deixa 3 tons de um cabelo perderem para 1 preto; a média borra."""
    H, W = len(rows), max(len(r) for r in rows)
    nw, nh = shrink.target_size(W, H, size)
    out = []
    for j in range(nh):
        y0, y1 = j * H / nh, (j + 1) * H / nh; line = ''
        for i in range(nw):
            x0, x1 = i * W / nw, (i + 1) * W / nw; wt = {}
            for y in range(int(y0), min(H, int(np.ceil(y1)))):
                wy = min(y + 1, y1) - max(y, y0)
                if wy <= 0: continue
                for x in range(int(x0), min(W, int(np.ceil(x1)))):
                    wx = min(x + 1, x1) - max(x, x0)
                    if wx > 0:
                        c = rows[y][x]; wt[c] = wt.get(c, 0) + wx * wy
            if wt.get('.', 0) >= empty_at * (x1 - x0) * (y1 - y0): line += '.'; continue
            cols = sorted(((a, c) for c, a in wt.items() if c != '.'), reverse=True)
            if not cols: line += '.'; continue
            groups = []
            for a, c in cols:
                for g in groups:
                    if np.linalg.norm(LAB[g[1]] - LAB[c]) < de: g[0] += a; break
                else:
                    groups.append([a * (black if LAB[c][0] < 25 else 1.0), c])
            line += max(groups, key=lambda g: g[0])[1]
        out.append(line)
    return O.trim(out)


def del_cols(rows, a, b):
    """tira as colunas a..b-1 inteiras"""
    return [r[:a] + r[b:] for r in rows]


def shift_part(rows, box, dx, dy):
    """move o que está na caixa (r0, r1, c0, c1, exclusivo no fim) de (dx, dy): encurta a lâmina de uma espada tirando o meio dela e mantendo a ponta. Quem já está no destino e não é vazio fica por cima só se a parte movida for vazia ali."""
    r0, r1, c0, c1 = box
    g = [list(r) for r in rows]; H, W = len(g), len(g[0]); part = []
    for y in range(r0, r1):
        for x in range(c0, c1):
            if g[y][x] != '.': part.append((y, x, g[y][x])); g[y][x] = '.'
    for y, x, c in part:
        v, u = y + dy, x + dx
        if 0 <= v < H and 0 <= u < W: g[v][u] = c
    return [''.join(r) for r in g]


def fill_inside(rows, letter='w', pad_bottom=True, k=3):
    """o que é vazio DENTRO do anel da aura (o fundo branco entrava por falhas do anel) vira a cor do miolo"""
    h, w = len(rows), len(rows[0])
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    p = np.zeros((h + 2 * k + 2, w + 2 * k + 2), np.uint8); p[k + 1:h + k + 1, k + 1:w + k + 1] = m
    if pad_bottom: p[h + k + 1:, k + 1:w + k + 1] = 1          # a figura é cortada pela borda de baixo: a borda conta como parede
    c = cv2.morphologyEx(p, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    f = c.copy(); ff = np.zeros((f.shape[0] + 2, f.shape[1] + 2), np.uint8); cv2.floodFill(f, ff, (0, 0), 2)
    ins = (f != 2)[k + 1:h + k + 1, k + 1:w + k + 1]
    return [''.join(letter if (ch == '.' and ins[y, x]) else ch for x, ch in enumerate(r)) for y, r in enumerate(rows)]


def put(rows, blocks):
    g = [list(x) for x in rows]
    for y0, x0, lines in blocks:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c != ' ': g[y0 + j][x0 + i] = c
    return [''.join(x) for x in g]


def done(r):
    r = O.trim(r)
    if loose.loose_count(r): r = loose.fix_loose(r)
    return O.trim(r)


ID = {}   # nome -> (idx da arte, função(rows atuais) -> rows novas)
def fix(name, idx):
    def d(fn): ID[name] = (idx, fn); return fn
    return d


def scale_part(rows, box, cx, cy, sc):
    """reduz o que está na caixa em torno de (cx, cy) na proporção sc (espada menor, mesma forma): cada célula de destino lê a célula de origem correspondente"""
    r0, r1, c0, c1 = box
    g = [list(r) for r in rows]; src = {}
    for y in range(r0, r1):
        for x in range(c0, c1):
            if g[y][x] != '.': src[(y, x)] = g[y][x]; g[y][x] = '.'
    for y in range(r0, r1):
        for x in range(c0, c1):
            u, v = cx + (x - cx) / sc, cy + (y - cy) / sc
            c = src.get((int(round(v)), int(round(u))))
            if c: g[y][x] = c
    return [''.join(r) for r in g]


def clear_box(rows, box, letters=None):
    r0, r1, c0, c1 = box
    return [''.join('.' if (r0 <= y < r1 and c0 <= x < c1 and (letters is None or c in letters)) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]


GRAYS = set('ilm') | {L['H1'], L['H3'], L['H4'], L['H5'], L['H6']}


@fix('Ichigo Vasto Lorde (Bleach, pixel)', 5)
def ichigo(cur):
    n = E(5, post=X.lg)
    n = shift_part(n, (56, 71, 0, 24), 24, -11)          # a lâmina fica mais curta (a ponta anda ao longo dela): de 111 para 87 de largura, a figura cresce
    n = O.trim(n)
    return put(done(vote(n)), [(6, 31, ['wwww']), (7, 31, ['kwkw']), (8, 31, ['wwwk'])])   # a máscara, lida na arte


@fix('Goku Black Rosé (foice, pixel)', 48)
def goku_black(cur):
    n = E(48, post=X.lg)
    n = del_cols(n, 68, 77); n = del_cols(n, 4, 22)      # rastro da foice mais curto dos dois lados, sem as colunas do meio: a figura passa de 1,6x para 1,16x de redução
    n = O.trim(n)
    return put(done(X.fit50(n)), [(20, 25, ['rkÅ}kk}']), (21, 25, ['kk}}wk}'])])   # de lado: olho de longe só 1 conta, o de perto inteiro; sem boca


@fix('Cloud Strife (Final Fantasy VII, pixel)', 9)
def cloud(cur):
    n = E(9, post=X.lg)
    n = scale_part(n, (6, 36, 0, 40), 40, 30, 0.62)      # espada menor, mesma forma (arte 76x55 -> 61x55)
    n = O.trim(n)
    return done(X.fit50(n))


@fix('Ciclope (X-Men, rajada, pixel)', 16)
def ciclope(cur):
    n = E(16, tol=34, post=X.pieces(20))
    n = X.peel_set(n, GRAYS)                             # sombra no chão e halo cinza da rajada
    n = O.trim(n)
    return done(vote(n))


@fix('Motoqueiro Fantasma (moto, pixel)', 28)
def moto(cur):
    n = E(28, crop_img=(0, 0, 750, 512), post=X.lg)
    n = clear_box(n, (26, 46, 11, 27), {L['H1'], L['H2']})   # o fundo cinza-claro preso entre a corrente e o corpo
    return done(vote(n, empty_at=0.55))


@fix('Goku Instinto Superior (aura azul, pixel)', 62)
def ui(cur):
    """só da linha 26 para baixo (roupa e o poder): a cabeça e o alto da aura ficam como estão"""
    n = E(62, colmap=[((214, 41, 9), 40, L['F4'])], post=X.pieces(20))
    v = vote(n)
    best = max(range(0, len(v[0]) - len(cur[0]) + 1), key=lambda d: sum(a == b for y in range(26) for a, b in zip(cur[y], v[y][d:])))
    v = [l[best:best + len(cur[0])] for l in v]
    out = cur[:26]
    for l in v[26:]:
        xs = [x for x, c in enumerate(l) if c != '.']
        a_, b_ = xs[0], xs[-1]
        out.append(''.join(c if c != '.' or not a_ < x < b_ else ('b' if x - a_ <= 2 or b_ - x <= 2 else 'w') for x, c in enumerate(l)))   # o fundo branco entrava por falhas do anel: o miolo é branco, a borda é o anel
    return out


# ---- rostos de My Hero Academia, do Kamui em diante (lidos com tools/r25_sheet.py); olhos discretos, sem dentes (CLAUDE.md §4.8). Só as contas do rosto mudam.
FACES = {
 'Kamui Woods (My Hero Academia, pixel)': (17, [(6, 21, ['kxxÖxxk'])]),
 'Shoto Todoroki (gelo e fogo, pixel)': (18, [(15, 28, ['sk3sk']), (16, 28, ['Òssss']), (17, 29, ['ÒsÒ'])]),
 'Nana Shimura (My Hero Academia, pixel)': (19, [(7, 15, ['kkÐkk']), (8, 14, ['Òsssss']), (9, 14, ['Òsssss']), (10, 15, ['sÒÒsÈ']), (11, 15, ['ÈÒÒÈ'])]),
 'Stain (My Hero Academia, pixel)': (21, [(24, 24, ['sÒÒs'])]),
 'Gran Torino (My Hero Academia, pixel)': (24, [(12, 25, ['Ú'])]),
 'Eijiro Kirishima (My Hero Academia, pixel)': (26, [(14, 15, ['ss']), (15, 13, ['ÒÒÒ'])]),
 'Tokoyami e Dark Shadow (My Hero Academia, pixel)': (27, [(28, 11, ['r'])]),
}
for _n, (_i, _b) in FACES.items():
    ID[_n] = (next(c[2] for c in X.CFG if c[0] == _n), (lambda b=_b: (lambda cur: put(cur, b)))())


def main():
    cur = {t['name']: t['rows'] for t in parse(os.path.join(ROOT, 'templates.js'))['items']}
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    H = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 560
    if '--H' in sys.argv: args.remove(str(H))
    new = {}; items = []
    for n, (idx, fn) in ID.items():
        if args and not any(a.lower() in n.lower() for a in args): continue
        if n not in cur: print('NÃO ESTÁ NO CATÁLOGO', n); continue
        r5.SKIN_ON = False
        new[n] = fn(cur[n])
        items.append((f'{idx} ANTES {n[:34]} {len(cur[n][0])}x{len(cur[n])}', R.source_img(idx), cur[n]))
        items.append((f'DEPOIS {len(new[n][0])}x{len(new[n])}', None, new[n]))
    if '--apply' in sys.argv:
        ids = {t['name']: t['id'] for t in parse(os.path.join(ROOT, 'templates.js'))['items']}
        retoque.gravar({ids[n]: new[n] for n in new}, {ids[n]: cur[n] for n in new}); return
    per = 4 if H > 340 else 8
    for k in range(0, len(items), per):
        R.pairsheet(items[k:k + per], os.path.join(OUT, f'r9_{k // per}.png'), H=H)
    print('folhas', (len(items) + per - 1) // per)


if __name__ == '__main__':
    main()
