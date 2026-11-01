"""Remessa 26 (54 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r26_exfinal.py [filtro...] [--merge] [--H 520]
   -> data/final28_120.json (tudo em 1 placa, sem irmão grande).
Quase tudo é sprite/gráfico com grade: cópia exata; o que passa de 50 é reduzido: até 1,3x tira linhas e colunas inteiras; acima, voto por grupos de tons (vote, CLAUDE.md §7.30).
Espada e rajada longas perdem o MEIO antes da redução: sobra placa para a figura. Rostos em 1 placa (§4.8): olhos discretos, sem boca desenhada. Reaproveita os auxiliares do r22_exfinal.py."""
import os, sys, json
os.environ['REMNUM'] = '26'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np
import cv2
import r5, r6, outline as O, illus, shrink, loose
import r22_exfinal as R
import palette as P
from palette import sfx
from PIL import Image
E = r6.exact6
lg = R.lg
F = r6.FILES
L = {c['code']: c['letter'] for c in P.ALL}
LAB = shrink.LAB
GRAYS = set('ilmd') | {L['H1'], L['H3'], L['H4'], L['H5'], L['H6']}
C5 = dict(K=36, dark_frac=0.25, black_L=12.0, thr=240, pale_skin=False, warm_white=0, seal=0.0, smooth_de=10.0)


def holes(rows, minsz=4, letter='w', keep=()):
    """esvazia os brancos FECHADOS (vãos de fundo) com >= minsz contas; keep = retângulos (r0, r1, c0, c1) onde o branco é do desenho"""
    m = np.array([[c == letter for c in r] for r in rows], np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
    g = [list(r) for r in rows]
    for i in range(1, n):
        if st[i][4] < minsz: continue
        cy, cx = st[i][1] + st[i][3] / 2.0, st[i][0] + st[i][2] / 2.0
        if any(a <= cy <= b and c <= cx <= d for a, b, c, d in keep): continue
        ys, xs = np.nonzero(lab == i)
        for y, x in zip(ys, xs): g[y][x] = '.'
    return [''.join(r) for r in g]


def pieces(minsz):
    """mantém as peças (8 vizinhos) com pelo menos minsz contas: figura em partes fica, marca d'água e assinatura saem"""
    def f(rows):
        m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        return O.trim([''.join(c if st[lab[y, x]][4] >= minsz else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)])
    return f


def _drop_lines(rows, k):
    """tira k COLUNAS: as que menos diferem da vizinha (nunca duas seguidas)"""
    W = len(rows[0]); cols = [''.join(r[x] for r in rows) for x in range(W)]
    cost = [(sum(a != b for a, b in zip(cols[x], cols[x + 1])), x) for x in range(W - 1)]
    out = set()
    for _, x in sorted(cost):
        if len(out) == k: break
        if x - 1 in out or x + 1 in out or x in out: continue
        out.add(x)
    return [''.join(c for x, c in enumerate(r) if x not in out) for r in rows]


def vote(rows, size=50, de=13.0, empty_at=0.6):
    """voto em grupo: na janela de cada conta, tons parecidos (ΔLab < de) somam os votos e ganha o grupo maior, com a letra mais comum dele. A maioria simples deixa 3 tons de um cabelo perderem para 1 preto; a média borra."""
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
                else: groups.append([a, c])
            line += max(groups, key=lambda g: g[0])[1]
        out.append(line)
    return O.trim(out)


def fit50(rows):
    h, w = len(rows), len(rows[0]); big = max(h, w)
    if big <= 50: return rows
    if big / 50.0 > 1.3: return vote(rows)
    nw, nh = shrink.target_size(w, h, 50)
    rows = _drop_lines(rows, w - nw)
    tr = [''.join(c) for c in zip(*rows)]
    tr = _drop_lines(tr, h - nh)
    return [''.join(c) for c in zip(*tr)]


def fin(rows):
    rows = fit50(O.trim(rows))
    if loose.loose_count(rows): rows = loose.fix_loose(rows)
    return O.trim(rows)


def peel_set(rows, letters, r0=0):
    """tira as letras ligadas ao lado de fora, até encostar em outra cor; r0 = só da linha r0 para baixo"""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    st = [(y, x) for y in range(H) for x in range(W) if g[y][x] == '.' or y in (0, H - 1) or x in (0, W - 1)]
    seen = set(st)
    while st:
        y, x = st.pop()
        if g[y][x] in letters and y >= r0: g[y][x] = '.'
        if g[y][x] != '.': continue
        for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= v < H and 0 <= u < W and (v, u) not in seen:
                seen.add((v, u)); st.append((v, u))
    return O.trim([''.join(r) for r in g])


def pale(rows):
    """halo claro de adesivo: contas claras e sem cor ligadas ao lado de fora"""
    return peel_set(rows, {c for c in LAB if LAB[c][0] >= 72 and (LAB[c][1] ** 2 + LAB[c][2] ** 2) ** .5 < 30})


def near_letters(rgb, de):
    lab = illus._lab(np.array(rgb, float))
    return {c for c in LAB if np.linalg.norm(LAB[c] - lab) < de}


def clearb(*boxes):
    def f(rows):
        return [''.join('.' if any(a <= y < b and c <= x < d for a, b, c, d in boxes) else ch for x, ch in enumerate(r)) for y, r in enumerate(rows)]
    return f


def delc(a, b):
    """tira as colunas a..b-1 (o meio de uma lâmina ou rajada)"""
    return lambda rows: [r[:a] + r[b:] for r in rows]


def chain(*fs):
    def f(rows):
        for g in fs: rows = g(rows)
        return rows
    return f


def squeeze(a, b):
    """tira uma coluna sim, outra não, entre a e b: asa mais estreita, sem cortar a ponta; sobra placa para a figura"""
    return lambda rows: [''.join(c for x, c in enumerate(r) if not (a <= x < b and (x - a) % 2)) for r in rows]


def maka42():
    """a assinatura fica por cima da capa: cada coluna do retângulo copia a cor de cima (metade de cima) e a de baixo (metade de baixo)"""
    im = np.array(Image.open(F[42]).convert('RGB'))
    x0, y0, x1, y1 = 340, 400, 572, 456; mid = (y0 + y1) // 2
    for x in range(x0, x1):
        im[y0:mid, x] = im[y0 - 3, x]; im[mid:y1, x] = im[y1 + 3, x]
    tmp = os.path.join(OUT, '_r26_42.png'); Image.fromarray(im).save(tmp)
    old = F[42]; F[42] = tmp
    try: r = E(42, thr=248, post=lg)
    finally: F[42] = old
    return fin(holes(r, 30))


def seiya25():
    r = R.ill(25, dict(C5, thr=205, dark_frac=0.3), clear=[(0, 180, 110, 200)], skin=False)
    r = [''.join('.' if (36 <= y <= 42 and x <= 24 and c == 'w') else c for x, c in enumerate(l)) for y, l in enumerate(r)]
    return fin(lg(r))


PX25 = 4.0


def G(i, **kw):
    post = kw.pop('post2', None)
    def f():
        r = E(i, **kw)
        if post: r = post(r)
        return fin(r)
    return f


def comp(idx, kw, k, n, rowh, post=None):
    """k-ésima das n maiores peças de uma folha, em ordem de leitura"""
    def f():
        r = R.cached(f'cp{idx}', lambda: _sheet(idx, kw, n, rowh))[k]
        return fin(post(r) if post else r)
    return f


def _sheet(idx, kw, n, rowh):
    rows = E(idx, **kw)
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    k, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = sorted(range(1, k), key=lambda i: -st[i][4])[:n]
    big.sort(key=lambda i: (int(cen[i][1] // rowh), cen[i][0]))
    return [O.trim([''.join(c if lab[y, x] == i else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)]) for i in big]


def ill(idx, kw, box=None, clear=(), skin=False):
    def f():
        return fin(lg(R.ill(idx, dict(C5, **kw), box=box, clear=clear, skin=skin)))
    return f


CFG = [
 ('Seiya de Pégaso (foto de peça pronta, WOW)', 'Cavaleiros do Zodíaco', 0, G(0, darkbg=62, post=lg, post2=chain(lambda r: peel_set(r, {L['H5'], L['H6'], 'd'}), clearb((0, 19, 33, 60))))),
 ('Camus de Aquário (pixel, rajada)', 'Cavaleiros do Zodíaco', 1, G(1, post2=chain(clearb((0, 5, 0, 99), (49, 60, 0, 99)), delc(36, 59), pieces(8)))),
 ('Zero (Code Geass, foto de chaveiro)', 'Code Geass', 2, G(2, grad=16, post2=chain(clearb((0, 13, 0, 99)), lg))),
 ('Zero Two (Darling in the Franxx, gráfico)', 'Darling in the Franxx', 3, G(3, post=lg)),
 ('Allen Walker (D.Gray-man, gráfico, olho vermelho)', 'D.Gray-man', 4, G(4, post=lg)),
 ('Estelar (Jovens Titãs, gráfico)', 'Jovens Titãs', 5, G(5, colmap=[((46, 228, 10), 40, L['B4'])], post=pieces(20))),
 ('Ravena (Jovens Titãs, gráfico)', 'Jovens Titãs', 7, G(7, crop_img=(0, 180, 640, 1020), post=pieces(20))),
 ('Rimuru Lorde Demônio (Tensura, chibi, pixel)', 'Tensura (Slime)', 8, G(8, post=lg, post2=lambda r: peel_set(r, near_letters((170, 95, 150), 22)))),
 ('Mutano (Jovens Titãs, gráfico)', 'Jovens Titãs', 9, G(9, post=lg)),
 ('Goku e Vegeta Blue (pixel)', 'Dragon Ball', 10, G(10, thr=210, post=pieces(40), post2=pale)),
 ('Grell Sutcliff (Black Butler, gráfico)', 'Black Butler', 11, G(11, post=lg)),
 ('Figura de manto preto e máscara de bico (gráfico)', 'Genéricos', 12, G(12, post=lg)),
 ('Robin (Jovens Titãs, gráfico)', 'Jovens Titãs', 14, G(14, post=lg)),
 ('Zero (Mega Man X, pixel)', 'Mega Man', 15, G(15, post=pieces(20))),
 ('Maga Negra (Yu-Gi-Oh, pixel)', 'Yu-Gi-Oh', 16, G(16, post=lg)),
 ('Goku na Nuvem Voadora (pixel)', 'Dragon Ball', 17, G(17, post=lg, post2=delc(0, 54))),
 ('Tousen Kaname (Bleach, chibi, gráfico)', 'Bleach', 18, G(18, post=lg)),
 ('Princesa Peach brava (gráfico)', 'Mario', 19, G(19, achro=150, post=lg)),
 ('Grimmjow (Bleach, gráfico)', 'Bleach', 20, G(20, px=dict(px=5.48, py=5.44, ox=0.90, oy=1.10, W=43, H=56), mode=True, thr=205, clear=[(0, 24, 34, 43)], post=lg)),
 ('Koro-sensei com coração (gráfico, versão 2)', 'Assassination Classroom', 22, G(22, post=lg)),
 ('Tanjiro Kamado (chibi, gráfico)', 'Demon Slayer', 23, G(23, achro=120, post=lg)),
 ('Ippo Makunouchi (Hajime no Ippo, pixel, guarda)', 'Hajime no Ippo', 24, G(24, allbg=True, post=lg, post2=lambda r: peel_set(r, {'k'}, len(r) - 12))),
 ('Seiya de Pégaso (gráfico, soco)', 'Cavaleiros do Zodíaco', 25, seiya25),
 ('Orochimaru (Naruto, chibi, gráfico)', 'Naruto', 26, G(26, post=lg, post2=pale)),
 ('Maka Albarn (Soul Eater, foice, pixel)', 'Soul Eater', 27, G(27, tol=30, allbg=True, post=lg, post2=lambda r: peel_set(r, GRAYS, len(r) - 8))),
 ('Brasão da Tropa Estacionária (Attack on Titan, gráfico)', 'Attack on Titan', 28, G(28, post=lg)),
 ('Koro-sensei de capelo (gráfico)', 'Assassination Classroom', 29, G(29, post2=chain(clearb((0, 25, 0, 24)), lg))),
 ('Mega Man X (armadura Ultimate, pixel)', 'Mega Man', 30, G(30, post=lg)),
 ('Maga Negra (Yu-Gi-Oh, chibi, adesivo)', 'Yu-Gi-Oh', 31, G(31, post=lg, post2=pale)),
 ('Hyoga de Cisne (pixel, rajada)', 'Cavaleiros do Zodíaco', 32, G(32, post2=chain(clearb((0, 10, 0, 99), (50, 60, 0, 99)), delc(8, 31), pieces(8)))),
 ('Guerreiro de cabelo cacheado e camiseta branca (pixel)', 'Genéricos', 33, G(33, post=pieces(6))),
 ('Diablo (Tensura, chibi, pixel)', 'Tensura (Slime)', 34, G(34, post=lg, post2=chain(lambda r: peel_set(r, near_letters((170, 95, 150), 22)), squeeze(0, 42), squeeze(62, 102)))),
 ('Ippo Makunouchi (Hajime no Ippo, pixel, peek-a-boo)', 'Hajime no Ippo', 35, G(35, post=lg)),
 ('Seiya de Pégaso (chibi, adesivo)', 'Cavaleiros do Zodíaco', 36, G(36, grad=18, post=pieces(60), post2=pale)),
 ('Brasão da Polícia Militar (Attack on Titan, gráfico)', 'Attack on Titan', 37, G(37, post=lg)),
 ('Guerreira de armadura azul e lança-broca (pixel)', 'Genéricos', 38, G(38, post=lg)),
 ('Mago de cabelo escuro e fogo (pixel)', 'Genéricos', 39, G(39, post=pieces(8))),
 ('Ciborgue (Jovens Titãs, gráfico)', 'Jovens Titãs', 40, G(40, allbg=True, post=lg)),
 ('Maga de cabelo castanho e fogo (pixel)', 'Genéricos', 41, G(41, tol=34, post=pieces(6))),
 ('Maka Albarn (Soul Eater, chibi)', 'Soul Eater', 42, maka42),
 ('Ryuk (Death Note, pixel)', 'Death Note', 43, G(43, allbg=True, post=lg)),
 ('Umaru-chan (Himouto! Umaru-chan, gráfico)', 'Himouto! Umaru-chan', 44, G(44, crop_img=(90, 551, 1060, 1500), thr=225, post=lg, post2=lambda r: pale([l[1:-1] for l in r[1:]]))),
 ('Dragão Branco de Olhos Azuis (gráfico)', 'Yu-Gi-Oh', 45, G(45, crop_img=(47, 574, 1000, 1632), achro=195, post=lg)),
 ('Caveira alada vermelha e branca (gráfico)', 'Genéricos', 46, G(46, px=dict(px=24.02, py=24.02, ox=23.50, oy=0.20, W=49, H=85), mode=True, thr=205, post=pieces(50))),
 ('Ichigo Kurosaki (Bleach, pixel, Zangetsu)', 'Bleach', 47, G(47, post=lg, post2=delc(4, 20))),
 ('Bruxa de cabelo rosa (pixel)', 'Genéricos', 48, G(48, post=pieces(10))),
 ('Zenitsu dormindo (Demon Slayer, gráfico)', 'Demon Slayer', 49, G(49, achro=150, post=lg)),
 ('Guerreiro de capacete dourado (chibi, pixel)', 'Genéricos', 50, G(50, crop_img=(0, 60, 480, 518), thr=225, post=lg)),
 ('Piccolo (Dragon Ball, pixel)', 'Dragon Ball', 51, G(51, post=lg)),
 ('Brasão da Tropa de Treinamento (Attack on Titan, gráfico)', 'Attack on Titan', 52, G(52, post=lg)),
 ('Fusão de Goku e Vegeta (pixel)', 'Dragon Ball', 53, G(53, post=pieces(30), post2=lambda r: holes(r, 8))),
]
CFG = [c + ('graf',) for c in CFG]
for _k, _n in enumerate(['Allen Walker (D.Gray-man, pixel, braço de garra)', 'Allen Walker (D.Gray-man, pixel, capa)', 'Allen Walker (D.Gray-man, pixel, de frente)']):
    CFG.append((_n, 'D.Gray-man', 6, comp(6, {}, _k, 3, 46.0, pale), 'folha'))
for _k, _n in enumerate(['Shun de Andrômeda (pixel, corrente)', 'Hyoga de Cisne (pixel, corpo inteiro, versão 2)', 'Shiryu de Dragão (pixel, corpo inteiro, armadura verde)', 'Seiya de Pégaso (pixel, corpo inteiro, versão 3)', 'Ikki de Fênix (pixel, corrente vermelha)']):
    CFG.append((_n, 'Cavaleiros do Zodíaco', 13, comp(13, {}, _k, 5, 56.0, (lambda r: holes(pale(r), 10)) if _k in (0, 4) else pale), 'folha'))
_S21 = [('Chibi roxo de chapéu (tokusatsu)', (80, 21, 160, 163)), ('Herói azul e dourado (tokusatsu, chibi)', (172, 3, 272, 163)),
        ('Herói branco e vermelho (tokusatsu, chibi)', (279, 3, 369, 163)), ('Herói preto e laranja (tokusatsu, chibi)', (377, 10, 476, 163)),
        ('Figura de vestido vermelho (tokusatsu, chibi)', (488, 12, 570, 163)), ('Cavaleiro prateado de capa (tokusatsu, chibi)', (90, 176, 172, 336)),
        ('Dama loira de óculos (tokusatsu, chibi)', (176, 205, 266, 336)), ('Robô marrom (tokusatsu, chibi)', (275, 178, 388, 336)),
        ('Gata preta com bastão (tokusatsu, chibi)', (396, 197, 468, 336)), ('Mago de cartola (tokusatsu, chibi)', (478, 180, 568, 336))]
_C21 = [(109, 63, 143, 96), (169, 54, 201, 92), (283, 124, 320, 161), (440, 60, 476, 96), (511, 60, 545, 94), (113, 302, 151, 336), (201, 300, 239, 336), (285, 183, 317, 216), (407, 302, 443, 337), (478, 233, 510, 270)]
G21 = dict(px=2.78, py=2.78, ox=0.38, oy=1.38, W=244, H=126)


def sheet21():
    """as plaquinhas com o número ficam por cima das figuras: repinta a área delas pela vizinhança ANTES de ler a grade"""
    im = np.array(Image.open(F[21]).convert('RGB'))
    m = np.zeros(im.shape[:2], np.uint8)
    for x0, y0, x1, y1 in _C21: m[y0 - 2:y1 + 2, x0 - 2:x1 + 2] = 255
    im = cv2.inpaint(im, m, 5, cv2.INPAINT_TELEA)
    tmp = os.path.join(OUT, '_r26_21.png'); Image.fromarray(im).save(tmp)
    old = F[21]; F[21] = tmp
    try: return E(21, px=G21, ref=(0, 255, 0), tol=1)
    finally: F[21] = old


def part21(box, post=None):
    """convert5 na imagem já sem as plaquinhas: o voto por tons limpa o ruído do JPEG, que a leitura pela grade (pixel de 2,78) deixava"""
    def f():
        R.cached('s21', sheet21)
        old = F[21]; F[21] = os.path.join(OUT, '_r26_21.png')
        try: r = R.ill(21, dict(C5, dark_frac=0.3, K=28), box=box, skin=False)
        finally: F[21] = old
        return fin(lg(post(r) if post else r))
    return f


_P21 = {'Gata preta': lambda r: peel_set(r, GRAYS, int(len(r) * 0.7)), 'Robô marrom': lambda r: [''.join('.' if (y < 10 and x < 15 and LAB[c][0] < 62 and (LAB[c][1] ** 2 + LAB[c][2] ** 2) ** .5 < 12 if c != '.' else False) else c for x, c in enumerate(l)) for y, l in enumerate(r)]}       # o que sobrou da plaquinha repintada
for _n, _b in _S21:
    CFG.append((_n, 'Genéricos', 21, part21(_b, next((v for k, v in _P21.items() if k in _n), None)), 'folha'))

# rostos da fusão, lidos na arte: de perfil, um olho só; boca aberta = 2 contas e um ponto vermelho (CLAUDE.md §4.8)
TOUCH = {
 'Fusão de Goku e Vegeta (pixel)': [(8, 13, ['ss   wk']), (9, 14, ['s   kk']), (10, 17, ['s']), (11, 16, ['rks']), (12, 16, ['sk']),
                                    (10, 32, ['kw']), (11, 32, ['ss s']), (12, 32, ['skrs']), (13, 33, ['ks'])],
}


def touched(n, r):
    if n not in TOUCH: return r
    g = [list(x) for x in r]
    for y0, x0, lines in TOUCH[n]:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c != ' ': g[y0 + j][x0 + i] = c
    return [''.join(x) for x in g]


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--H' in sys.argv: args.remove(sys.argv[sys.argv.index('--H') + 1])
    one = []; sheet = []
    for n, g, idx, fn, grp in CFG:
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = touched(n, fn()); one.append((n, g, r)); sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa')
    tag = 'all' + ('_f' if args else '')
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r26_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r26_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and ('--merge' in sys.argv or not args):
        pth = os.path.join(SP, 'data', 'final28' + sfx() + '.json')
        old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) and args else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok')
