"""Remessa 22 (100 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r22_exfinal.py [filtro...] [--grupo nome]   -> data/final24_120.json (1 placa) + data/final24_multi_120.json ("(grande)")
Grupos: pix (gráficos pixiecraft com legenda: células lidas e mapeadas SÓ para os códigos da legenda do próprio gráfico, conferindo as contagens impressas), graf (gráficos limpos),
senapapa (renders de contas redondas), spr (sprites sem grade), foto (fotos de peça pronta), folha (folhas divididas), ill (ilustrações, illus5.convert5).
Pedido do usuário (2026-10-30): repetidas entram (nome "(versão 2)" quando colidir); não checar duplicata de arte contra o catálogo."""
import os, sys, json
os.environ.setdefault('REMNUM', '22')      # r23_exfinal.py importa este arquivo com REMNUM=23
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np, cv2
from PIL import Image, ImageDraw
import r5, r6, outline as O, illus, illus5, beadclean, loose
import palette as P
import weak_cm as WC
import weak_fix as WF
from palette import sfx, ALL
E = r6.exact6
F = r6.FILES
_BYCODE = {c['code']: c for c in ALL}


def lg(rows): return r5.largest(rows)


def keep(n):
    """mantém só as peças com pelo menos n contas"""
    def f(rows):
        m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
        k, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        return O.trim([''.join(c if c != '.' and st[lab[y, x]][4] >= n else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)])
    return f


def cut(y0=None, y1=None, x0=None, x1=None, then=None):
    """recorta linhas/colunas DEPOIS da conversão"""
    def f(rows):
        r = O.trim([s[x0:x1] for s in rows[y0:y1]])
        return then(r) if then else r
    return f


def put(rows, cells):
    g = [list(r) for r in rows]
    for (y, x), c in cells.items():
        if 0 <= y < len(g) and 0 <= x < len(g[0]): g[y][x] = c
    return [''.join(r) for r in g]


# ---------------------------------------------------------------- gráficos pixiecraft (Divertida Mente etc.): legenda impressa "CÓDIGO:contas"
def legend_swatches(idx, y_from, n_expected):
    """cor de cada amostra da legenda (na ordem de leitura), sem a amostra branca H2 (sem preenchimento): blocos cheios depois de uma abertura morfológica (o texto fino e a marca d'água somem)"""
    rgb = np.array(source_img(idx)).astype(np.uint8)[y_from:]
    mask = ((255 - cv2.GaussianBlur(rgb, (5, 5), 0).min(axis=2)) > 9).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))
    k, lab, st, cen = cv2.connectedComponentsWithStats(mask, connectivity=4)
    comps = [i for i in range(1, k) if st[i][4] > 700]
    comps.sort(key=lambda i: cen[i][1])
    bands, cur = [], []
    for i in comps:
        if cur and cen[i][1] - cen[cur[-1]][1] > 40: bands.append(cur); cur = []
        cur.append(i)
    if cur: bands.append(cur)
    order = [i for band in bands for i in sorted(band, key=lambda i: cen[i][0])]
    cols = []
    for i in order:
        x0, y0, bw, bh = [int(v) for v in st[i][:4]]
        nsub = max(1, int(round(bw / float(bh))))          # amostras coladas formam um bloco só: divide pela largura/altura
        for j in range(nsub):
            xa = x0 + int(j * bw / nsub); xb = x0 + int((j + 1) * bw / nsub)
            sel = (lab[y0:y0 + bh, xa:xb] == i)
            pix = rgb[y0:y0 + bh, xa:xb][sel]
            cols.append(np.median(pix, axis=0))
    if len(cols) != n_expected: print(f'  AVISO: {len(cols)} amostras na legenda, esperadas {n_expected}')
    return cols


def kit_letter(code, rgb):
    """letra do kit: o código exato quando ele existe; senão a cor do kit mais próxima da cor da amostra (Lab, só neutros para neutros)"""
    if code in _BYCODE: return _BYCODE[code]['letter'], 0.0
    lab = illus._lab(np.array(rgb, float))
    best = None
    for c in ALL:
        h = np.array([int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
        d = float(np.linalg.norm(illus._lab(h) - lab))
        if best is None or d < best[0]: best = (d, c['letter'], c['code'])
    return best[1], best[0], best[2]


def nearest_letter(rgb):
    """letra do kit mais próxima de uma cor (gráficos em códigos MARD: o mesmo código é outra cor no kit Pindou)"""
    lab = illus._lab(np.array(rgb, float))
    return (min(ALL, key=lambda c: float(np.linalg.norm(illus._lab(np.array([int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)) - lab)))['letter'],)


def ring_cells(idx, grid, lo=0.10, hi=0.30):
    """cor de cada célula pela MEDIANA da moldura da célula (a faixa entre lo e hi do passo a partir da borda): o código escrito no centro (texto branco numa célula preta chegava a dominar a
    amostra central e a célula virava "branca" = fundo) não entra; as linhas da grade, que ficam na própria borda, também não"""
    im = np.array(Image.open(F[idx]).convert('RGB')).astype(np.float32)
    px, py, ox, oy, W, H = grid['px'], grid['py'], grid['ox'], grid['oy'], int(grid['W']), int(grid['H'])
    out = np.zeros((H, W, 3), np.float32)
    h_, w_, _ = im.shape
    for y in range(H):
        for x in range(W):
            x0 = ox + x * px; y0 = oy + y * py
            xa, xb = int(x0), int(x0 + px) + 1; ya, yb = int(y0), int(y0 + py) + 1
            sub = im[max(0, ya):min(h_, yb), max(0, xa):min(w_, xb)]
            if sub.size == 0: out[y, x] = 255; continue
            hh, ww = sub.shape[:2]
            yy, xx = np.mgrid[0:hh, 0:ww]
            d = np.minimum(np.minimum(xx + (xa - x0), (x0 + px) - (xa + xx)) / px, np.minimum(yy + (ya - y0), (y0 + py) - (ya + yy)) / py)
            sel = (d >= lo) & (d <= hi)
            out[y, x] = np.median(sub[sel], axis=0) if sel.any() else np.median(sub.reshape(-1, 3), axis=0)
    return out.astype(np.float64)


def pix_graph(idx, grid, legend, thr=225, verbose=True, name='', fix=None, kit=False, ring=False):
    """lê cada célula (cor dominante: ignora o código escrito dentro e a marca d'água), tira o fundo branco ligado à borda e classifica a célula na cor MAIS PRÓXIMA entre as amostras da
    legenda do próprio gráfico. Confere as contagens por código com as impressas e avisa as diferenças. Cada código vira a letra do kit (o próprio código quando o kit o tem; senão o mais próximo)."""
    codes = [t.split(':') for t in legend.split()]
    nonwhite = [(c, int(n)) for c, n in codes if c != 'H2']
    if kit:        # todos os códigos existem no kit (gráfico em códigos Pindou): a cor de cada um é a do próprio kit, sem ler a legenda
        sw = [np.array([int(_BYCODE[c]['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float) for c, _ in nonwhite]
    else:
        sw = legend_swatches(idx, int(grid['oy'] + grid['H'] * grid['py'] + 35), len(nonwhite))
    cls = []                                   # (código, contagem, letra do kit, cor da amostra)
    for (c, n), col in zip(nonwhite, sw): cls.append((c, n, kit_letter(c, col)[0], col))
    for c, n in codes:
        if c == 'H2': cls.append((c, int(n), _BYCODE['H2']['letter'], np.array([255.0, 255.0, 255.0])))
    arr = ring_cells(idx, grid) if ring else r6.load_cells(idx, px=grid, mode=True)
    H, W, _ = arr.shape
    same = arr.min(axis=2) > thr
    bg = r6.flood_fn(arr, lambda p, q: same[q])
    lab = illus._lab(arr); cl = np.stack([illus._lab(np.array(c[3], float)) for c in cls])
    d = np.linalg.norm(lab[:, :, None, :] - cl[None, None, :, :], axis=3)
    pick = d.argmin(axis=2)
    for (y, x), code in (fix or {}).items():             # correções pontuais (buraco branco dentro do cabelo; célula clareada pela marca d'água): (linha, coluna) a partir de 0
        if code == '.': bg[y, x] = True
        else: bg[y, x] = False; pick[y, x] = [c[0] for c in cls].index(code)
    rows = [''.join('.' if bg[y, x] else cls[pick[y, x]][2] for x in range(W)) for y in range(H)]
    if verbose:
        got = {}
        for y in range(H):
            for x in range(W):
                if not bg[y, x]: got[cls[pick[y, x]][0]] = got.get(cls[pick[y, x]][0], 0) + 1
        diff = [f'{c}:{got.get(c, 0)}/{n}' for c, n, _, _ in cls if got.get(c, 0) != n]
        print(f'  [{name}] {W}x{H}  contagens {"IGUAIS à legenda" if not diff else "DIFERENTES (obtido/legenda): " + " ".join(diff)}')
        print('    código→letra:', ' '.join(f'{c}={l}' + ('' if c in _BYCODE else '*') for c, n, l, _ in cls), ' (* = fora do kit: cor mais proxima)')
    return O.trim(rows)


PIX = [
 # idx, nome, série, grade ajustada por tools/gridfit-style (pente de bordas), legenda impressa
 (14, 'Ansiedade (Divertida Mente, gráfico)', 'Divertida Mente', dict(px=16.12, py=16.15, ox=15.08, oy=15.51, W=20, H=27), 'F6:67 F13:52 A7:48 F11:46 H7:38 F18:26 A26:19 H2:15 F10:14 A22:12 G4:7'),
 (27, 'Nojinho (Divertida Mente, gráfico)', 'Divertida Mente', dict(px=26.50, py=26.55, ox=25.55, oy=26.27, W=18, H=24), 'B9:115 B8:55 B16:47 B5:37 B15:23 H2:8 D14:5 D18:3 M2:2'),
 (97, 'Tristeza (Divertida Mente, gráfico)', 'Divertida Mente', dict(px=27.31, py=27.35, ox=26.27, oy=26.99, W=18, H=23), 'D4:99 C8:65 C4:38 H2:30 C3:24 D3:21 C7:17 D2:8 C5:2 C24:2'),
 (82, 'Raiva (Divertida Mente, gráfico)', 'Divertida Mente', dict(px=19.65, py=19.73, ox=18.81, oy=19.21, W=16, H=24), 'F11:54 F8:37 A18:33 F4:31 G8:30 F6:26 F18:22 H3:18 H10:18 A26:12 H4:10 A17:10 H11:6 H2:4 F23:2'),
 (35, 'Criatura roxa (pixel, gráfico)', 'Outros', dict(px=16.24, py=16.31, ox=15.45, oy=15.71, W=19, H=22), 'D10:92 D5:50 D20:46 D12:43 E7:27 D14:21 H7:5 D21:4 H2:4 E6:3 E22:2 D19:2 E3:2 E2:1'),
]
PIXFIX = {14: {(3, 16): '.', (3, 17): '.', (6, 2): '.', (5, 11): 'A7'}}     # Ansiedade: 3 vãos brancos do cabelo (não são contas H2) e 1 A7 clareada pela marca d'água (vira G4 sem isto)
CFG = []
for _i, _n, _g, _grid, _leg in PIX:
    CFG.append((_n, _g, _i, (lambda i=_i, gr=_grid, lg_=_leg, n=_n: pix_graph(i, gr, lg_, name=n, fix=PIXFIX.get(i))), 'pix'))


# ---------------------------------------------------------------- gráficos limpos (grade medida; os rótulos/legenda fora do desenho viram fundo branco)
def GR(idx, px, py, ox, oy, **kw):
    """grade forçada (passo e fase medidos por ajuste de pente de bordas, conferidos na sobreposição) cobrindo a imagem toda; cor dominante da célula; fundo branco ligado à borda; só a maior peça"""
    w, h = Image.open(F[idx]).size
    ox %= px; oy %= py
    a = dict(px=dict(px=px, py=py, ox=ox, oy=oy, W=int((w - ox) / px + 0.5), H=int((h - oy) / py + 0.5)), mode=True, thr=225, post=lg)
    if 'tol' in kw or 'ref' in kw: a.pop('thr')          # fundo colorido: cor do canto com tolerância
    a.update(kw)
    return E(idx, **a)


def comps(rows, n, by_x=False, by_y=False):
    """as n maiores peças, na ordem de leitura (by_x: da esquerda para a direita; by_y: de cima para baixo)"""
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    k, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = sorted(range(1, k), key=lambda i: -st[i][4])[:n]
    H = len(rows)
    big.sort(key=(lambda i: cen[i][0]) if by_x else (lambda i: cen[i][1]) if by_y else (lambda i: (round(cen[i][1] / (H / 2.2)), cen[i][0])))
    return [O.trim([''.join(c if lab[y, x] == i else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)]) for i in big]


_C = {}
def cached(key, fn):
    if key not in _C: _C[key] = fn()
    return _C[key]


CFG += [
 ('Killua Zoldyck (chibi, gráfico)', 'Hunter x Hunter', 4, lambda: GR(4, 10.61, 10.65, 31.40, 42.20), 'graf'),
 ('Going Merry (ponto cruz, gráfico)', 'One Piece', 26, lambda: GR(26, 15.33, 15.33, 52.0, 51.7), 'graf'),
 ('Red Dead Redemption II (pôster, pixel)', 'Red Dead Redemption', 46, lambda: E(46, ref=(0, 255, 0), tol=1, post=lg), 'graf'),
 ('Peashooter de gelo (Plants vs Zombies, gráfico)', 'Plants vs Zombies', 52, lambda: pix_graph(52, dict(px=29.27, py=29.23, ox=45.00, oy=17.40, W=22, H=22), 'H7:11 H2:5 D4:73 C5:24 C4:91 C2:14 B18:7 B17:11 B15:45 B8:3 B5:16', name='Peashooter de gelo'), 'graf'),
 ('Nezuko Kamado (pixel, gráfico)', 'Demon Slayer', 60, lambda: E(60, post=lg), 'graf'),
 ('Chibi de cabelo cinza e olhos amarelos (pixel, gráfico)', 'Outros', 68, lambda: E(68, achro=205, post=lg), 'graf'),
 ('Choso (Jujutsu Kaisen, chibi, gráfico)', 'Jujutsu Kaisen', 78, lambda: GR(78, 22.62, 22.63, 22.40, 0.0), 'graf'),
 ('Suguru Geto (chibi, pixel, gráfico)', 'Jujutsu Kaisen', 86, lambda: GR(86, 12.76, 12.81, 12.60, 11.40), 'graf'),
 ('Eustass Kid (One Piece, pixel)', 'One Piece', 89, lambda: E(89, post=lg), 'graf'),
]


# ---------------------------------------------------------------- renders de contas redondas (Senapapa "One Piece V2": 250x250, marca d'água cinza-clara, logos, anel cinza nas contas brancas)
def _comb(d, lo, hi, step=0.02):
    L = len(d); best = None
    for s in np.arange(lo, hi, step):
        n = int(L / s)
        if n < 4: break
        ks = np.arange(n)
        for o in np.arange(0, s, 0.15):
            on = np.round(o + ks * s).astype(int); mid = np.round(o + (ks + 0.5) * s).astype(int)
            ok = (on < L) & (mid < L)
            sc = d[on[ok]].mean() - d[mid[ok]].mean()
            if best is None or sc > best[0]: best = (sc, s, o)
    return best


def _ring_closed(gray, cx, cy, s, T=205, r0=0.38, r1=0.50, nang=32):
    """fração dos ângulos em que o aro da conta (raio 0,38-0,50 do passo) tem um pixel cinza < T: conta BRANCA de verdade tem o círculo inteiro (0,7-0,95 no Ace); célula vazia encostada
    em contas escuras só pega os pontos de tangência dos vizinhos (<= 0,47) e o halo do contorno (0,25-0,62)"""
    h, w = gray.shape
    ang = np.linspace(0, 2 * np.pi, nang, endpoint=False)[:, None]; rr = np.linspace(r0, r1, 5)[None, :]
    px = np.rint(cx + rr * s * np.cos(ang)).astype(int); py = np.rint(cy + rr * s * np.sin(ang)).astype(int)
    ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
    v = np.where(ok, gray[np.clip(py, 0, h - 1), np.clip(px, 0, w - 1)], 999.0)
    return float((v.min(axis=1) < T).mean())


def bead_render(idx, pitch=(6.4, 9.6), close=5, white_ring=0.22, solid=205, verbose=True, name='', box=None, clear=(), closed=0.65, body=True):
    """figura = maior mancha colorida/escura (a marca d'água e o texto soltos ficam de fora); rede de contas ajustada por pente de bordas dentro da figura; cada célula: centro colorido/escuro = conta
    (cor pela mediana do centro); centro quase branco = conta BRANCA só se o anel em volta é mais escuro que o centro (anel cinza da conta), senão vazio"""
    rgb = np.array(source_img(idx)).astype(np.float32)
    for (cx0, cy0, cx1, cy1) in clear: rgb[cy0:cy1, cx0:cx1] = 255.0          # logo "ONE PIECE V2", nome em kanji e carimbo do autor: fora
    h, w, _ = rgb.shape
    mn = rgb.min(axis=2); mx = rgb.max(axis=2); sat = (mx - mn) / np.maximum(mx, 1)
    m0 = (((255 - mn) > 70) | (sat > 0.28)).astype(np.uint8)
    if box: mm = np.zeros_like(m0); mm[box[1]:box[3], box[0]:box[2]] = m0[box[1]:box[3], box[0]:box[2]]; m0 = mm
    m = cv2.morphologyEx(m0, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    k, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x0, y0, bw, bh = [int(v) for v in st[big][:4]]
    gray = rgb.mean(axis=2)
    pad = 4
    xa, xb, ya, yb = max(0, x0 - pad), min(w, x0 + bw + pad), max(0, y0 - pad), min(h, y0 + bh + pad)
    sub = gray[ya:yb, xa:xb]
    dx = np.percentile(np.abs(np.diff(sub, axis=1)), 65, axis=0); dy = np.percentile(np.abs(np.diff(sub, axis=0)), 65, axis=1)
    bx = _comb(dx, *pitch); by = _comb(dy, *pitch)
    sx, ox = bx[1], bx[2] + xa + 0.5; sy, oy = by[1], by[2] + ya + 0.5
    # a rede cobre a figura: primeira linha/coluna cuja célula toca a caixa
    i0 = int(np.floor((x0 - ox) / sx)); j0 = int(np.floor((y0 - oy) / sy))
    i1 = int(np.ceil((x0 + bw - ox) / sx)); j1 = int(np.ceil((y0 + bh - oy) / sy))
    yy, xx = np.mgrid[0:h, 0:w]
    rows = []
    for j in range(j0, j1):
        r = ''
        for i in range(i0, i1):
            cx = ox + (i + 0.5) * sx; cy = oy + (j + 0.5) * sy
            d = np.hypot(xx - cx, yy - cy)
            sel = (d >= 0.26 * sx) & (d <= 0.50 * sx)                    # ANEL da conta (o centro é o furo: o brilho dele enganava o teste e punha contas brancas dentro do preto)
            ann = rgb[sel]
            if len(ann) == 0: r += '.'; continue
            g = ann.mean(axis=1)
            keepm = g >= np.percentile(g, 12)                           # tira o fio escuro do contorno da conta (minoria) para ler a cor do corpo
            c = np.median(ann[keepm], axis=0)
            csat = (c.max() - c.min()) / max(c.max(), 1)
            if body:                     # cor = CORPO da conta (raio 0,16-0,40, sem o brilho nem o fio): o aro cinza do contorno escurecia a pele clara (237,221,210 virava 175,167,160 = cinza; rosto da Beatrice)
                bb = rgb[(d >= 0.16 * sx) & (d <= 0.40 * sx)]
                if len(bb):
                    gb = bb.mean(axis=1); pick = bb[(gb >= np.percentile(gb, 10)) & (gb <= np.percentile(gb, 92))]
                    cb = np.median(pick, axis=0) if len(pick) else c
                else: cb = c
            else: cb = c
            if c.min() < solid or csat > 0.18: r += r5.near120(tuple(cb))
            else:                                                        # claro: conta BRANCA (o fio do contorno aparece no anel) ou vazio (anel só de papel)
                white = float(np.mean(g < 205)) > white_ring and (not closed or _ring_closed(gray, cx, cy, sx) >= closed)      # conta branca: o contorno cinza dela fecha o aro INTEIRO; o halo de fora só pega um lado
                r += r5.near120(tuple(cb)) if white else '.'
        rows.append(r)
    rows = O.trim(rows)
    if verbose: print(f'  [{name}] passo {sx:.2f}x{sy:.2f}  figura {bw}x{bh}px  -> {len(rows[0])}x{len(rows)} contas')
    return rows



SEN = [
 (8, 'Barba Branca (Edward Newgate, One Piece V2, contas redondas)', [(58, 0, 250, 36), (170, 36, 250, 76), (205, 136, 250, 176)]),
 (23, 'Kaido (One Piece V2, contas redondas)', [(0, 0, 36, 36), (0, 228, 85, 250), (170, 228, 250, 250)]),
 (33, 'Shanks (One Piece V2, contas redondas)', [(165, 0, 250, 44), (0, 222, 72, 250), (200, 214, 250, 250)]),
 (37, 'Sabo (One Piece V2, contas redondas)', [(205, 0, 250, 40), (168, 196, 250, 240), (0, 224, 70, 250)]),
 (47, 'Trafalgar Law (One Piece V2, contas redondas)', [(166, 4, 250, 48), (198, 204, 250, 245), (0, 226, 178, 250)]),
 (64, 'Portgas D. Ace (One Piece V2, contas redondas)', [(205, 0, 250, 42), (164, 196, 250, 238), (0, 228, 190, 250)]),
 (65, 'Barba Negra (One Piece V2, contas redondas)', [(205, 0, 250, 40), (188, 48, 250, 96), (168, 214, 250, 238)]),
 (84, 'Mr. 2 Bon Clay (One Piece V2, contas redondas)', [(0, 0, 44, 40), (105, 0, 250, 22), (0, 186, 82, 226)]),
]
for _i, _n, _clr in SEN:
    CFG.append((_n, 'One Piece', _i, (lambda i=_i, n=_n, c=_clr: lg(bead_render(i, name=n, clear=c))), 'senapapa'))


def sil_keep(rows, k=3, bg='w'):
    """figura branca por dentro (Bepo, criaturas de contorno): o branco do desenho é igual ao do fundo, e um vão de 1 conta no contorno deixaria o fundo entrar. Fecha a silhueta
    (fechamento k×k das contas que não são `bg` + preencher buracos) e só tira o branco de FORA dela; o branco de dentro continua sendo conta branca"""
    H, W = len(rows), len(rows[0])
    m = np.array([[c != bg and c != '.' for c in r] for r in rows], np.uint8)
    mc = cv2.morphologyEx(np.pad(m, 2), cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    ff = mc.copy(); cv2.floodFill(ff, None, (0, 0), 2)
    inside = (ff != 2)[2:-2, 2:-2]
    return O.trim([''.join(c if inside[y, x] and c != '.' else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)])


def fill_between(rows, bg='w', miss='interp'):
    """branco entre o primeiro e o último ponto NÃO branco de cada linha vira conta branca (o resto do fundo vira vazio); linha só de branco no meio da figura herda a extensão da vizinha de cima"""
    ext = []
    for r in rows:
        idx = [i for i, c in enumerate(r) if c != bg and c != '.']
        ext.append((idx[0], idx[-1]) if idx else None)
    first = next(i for i, e in enumerate(ext) if e); last = max(i for i, e in enumerate(ext) if e)
    out = []
    for y, r in enumerate(rows):
        if y < first or y > last: out.append('.' * len(r)); continue
        e = ext[y] or ext[y - 1]
        out.append(''.join('.' if x < e[0] or x > e[1] else ('w' if c == bg else c) for x, c in enumerate(r)))
    return O.trim(out)


# ---------------------------------------------------------------- sprites sem grade (pixel nativo medido por pente de bordas; a assinatura "A" do autor sai como peça solta) e gráfico das 3 criaturas
CFG += [
 ('Doflamingo (One Piece, pixel)', 'One Piece', 18, lambda: GR(18, 17.10, 17.10, 237.90, 491.80, tol=45), 'spr'),
 ('Sanji (One Piece, perna em chamas, pixel)', 'One Piece', 59, lambda: GR(59, 16.98, 17.08, 256.92, 491.02, tol=45), 'spr'),
 ('Barba Branca (One Piece, chibi, pixel)', 'One Piece', 85, lambda: GR(85, 16.32, 16.34, 212.98, 498.16, tol=45), 'spr'),
 ('Bepo (One Piece, pixel)', 'One Piece', 98, lambda: lg(fill_between(GR(98, 8.50, 8.50, 126.80, 135.40, ref=(0, 255, 0), tol=1, post=None))), 'spr'),
 ('Hawks (My Hero Academia, pixel)', 'My Hero Academia', 25, lambda: GR(25, 14.46, 14.52, 60.24, 21.78), 'spr'),
 ('Hawks (My Hero Academia, chibi, gráfico)', 'My Hero Academia', 83, lambda: GR(83, 17.08, 17.06, 51.50, 34.44), 'spr'),
 ('Dabi (My Hero Academia, chibi, pixel)', 'My Hero Academia', 32, lambda: GR(32, 32.0, 32.04, 0.0, 0.0), 'spr'),
 ('Lula (estilo Mario, pixel)', 'Política', 43, lambda: GR(43, 27.62, 27.64, 257.90, 70.06), 'spr'),
]
for _k, _n in enumerate(['Dratini (pixel)', 'Dragonair (pixel)', 'Dragonite (pixel)']):
    CFG.append((_n, 'Pokémon', 58, (lambda k=_k: cached('c58', lambda: comps(sil_keep(E(58, ref=(0, 255, 0), tol=1)), 3, by_y=True))[k]), 'spr'))


# ---------------------------------------------------------------- ilustrações (illus5.convert5): 1 placa (lado maior 50) + irmão "(grande)" de 2-4 placas onde mais contas ajudam
def CM_BLOND(rgb, L, letter, is_black):
    """cluster de cor amarela/loira (matiz 40-66°, saturação >= 0,30): a trava de pele do near120 (e o pale_skin) mandavam o cabelo loiro para tom de pele; aqui vai para o amarelo mais próximo"""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); h *= 360
    if 40 <= h <= 66 and sat >= 0.30 and v >= 0.62: return r5.near120(tuple(rgb), skin=False)
    return None


_D14 = next(c['letter'] for c in ALL if c['code'] == 'D14'); _D21 = next(c['letter'] for c in ALL if c['code'] == 'D21')


def CM_PURPLE(rgb, L, letter, is_black):
    """cluster ROXO escuro (matiz 255-335, saturação >= 0,20, L entre 14 e 50): cabelo da Yoruichi virava vinho (F7/F11) e o manto do Kaido virava preto; o roxo mais escuro do kit é D14 (L 37), depois D21"""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); h *= 360
    if 262 <= h <= 335 and sat >= 0.25 and 14 <= L <= 50: return _D14 if L < 32 else _D21
    return None


def CM_BV(rgb, L, letter, is_black):
    """azul-violeta forte e escuro (manto do Kaido: matiz 240-262, saturação >= 0,45): vai para o roxo escuro D14 em vez de virar contorno preto"""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); h *= 360
    if 238 <= h <= 262 and sat >= 0.45 and 6 <= L <= 50: return _D14
    return None


def CM_ALL(rgb, L, letter, is_black):
    return CM_BLOND(rgb, L, letter, is_black) or CM_PURPLE(rgb, L, letter, is_black)


CH = dict(K=24, dark_frac=0.25, black_L=12.0, thr=240, pale_skin=True, warm_white=7, seal=0.0, center_map=CM_ALL)       # chibi com contorno: branco quase puro é fundo; dark_frac 0,25 (o 0,40 dos Cavaleiros engolia olhos/sobrancelhas/sorriso finos: testado 0,40/0,28/0,22 em 6 imagens)
BIG = dict(dark_frac=0.25, black_L=14.0)                                                          # nos grandes o contorno pesa menos (olhos/boca ganham espaço)
WH = dict(pale_skin=False, warm_white=0, noclean=True)                                           # cabelo/roupa BRANCOS: não pode virar tom de pele, e a limpeza de bordas apagava as pontas claras
ST = dict(peel=1.0)                                                                               # adesivo com borda branca grossa
NONE = dict(bg='none')                                                                            # cena inteira (fundo faz parte do desenho)


def strip_text(rgb, big_frac=0.25, min_area=12, debug=None, protect=()):
    """tira o TEXTO em katakana das figurinhas (letras vazadas: contorno preto com miolo branco, soltas em volta do personagem). Critério GEOMÉTRICO: o contorno do personagem é a(s)
    maior(es) peça(s) escura(s); a silhueta preenchida dele é "dentro" (olhos, boca e detalhes ficam lá dentro); qualquer outra peça escura cujo centro cai FORA da silhueta é letra.
    As letras apagadas são repintadas com cv2.inpaint (não viram buraco branco na chama); letra que encosta no contorno forma uma peça só com ele e fica (resíduo pequeno)"""
    f = rgb.astype(np.float32); mx = f.max(axis=2)
    ink = (mx < 125).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(ink, connectivity=8)
    areas = st[:, 4].copy(); areas[0] = 0
    big = float(areas.max())
    H, W = ink.shape
    inside = np.zeros((H, W), np.uint8)
    for i in range(1, n):
        if areas[i] >= big_frac * big:
            comp = (lab == i).astype(np.uint8)
            inv = (1 - comp).copy(); ff = np.zeros((H + 2, W + 2), np.uint8)
            cv2.floodFill(inv, ff, (0, 0), 2)                # o que o flood de fora não alcança é miolo do contorno
            inside |= ((inv != 2)).astype(np.uint8)
    kill = np.zeros((H, W), bool)
    for i in range(1, n):
        if areas[i] < min_area or areas[i] >= big_frac * big: continue
        cx, cy = int(cen[i][0]), int(cen[i][1])
        if not inside[min(H - 1, cy), min(W - 1, cx)]: kill |= (lab == i)
    for (px0, py0, px1, py1) in protect: kill[max(0, py0):max(0, py1), max(0, px0):max(0, px1)] = False      # rosto: olho/boca/sobrancelha são peças escuras "soltas" e o contorno com falha os deixava "fora" (Gouenji ficou sem olhos)
    if debug is not None: debug.append(kill.copy())
    km = cv2.dilate(kill.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.uint8)
    # miolo branco das letras vira fundo: preenche os buracos brancos cercados pelas letras apagadas
    return cv2.inpaint(rgb, km, 3, cv2.INPAINT_TELEA)


def kill_shadow(rgb, frac=0.80):
    """sombra no chão de um render 3D sobre fundo branco (Po chutando): pixels cinza NEUTRO (max-min < 14, 120 < max < 232) nos últimos 20% da altura viram branco (o preto dos pés e o branco do pelo ficam)"""
    out = rgb.copy(); y0 = int(rgb.shape[0] * frac)
    sub = out[y0:]; mx = sub.max(axis=2).astype(np.int32); mn = sub.min(axis=2).astype(np.int32)
    sub[((mx - mn) < 14) & (mx > 120) & (mx < 232)] = 255
    return out


def ill(idx, kw, plates=None, box=None, size=50, skin=True, clear=()):
    """igual ao ill() da remessa 20: convert5 + limpeza de bordas (beadclean) + buraquinhos + maior peça; fix/fixg = retoque à mão do molde de 1 placa / grande"""
    a = dict(kw); a.update(size=size)
    clear = tuple(clear) + tuple(a.pop('clear', ()))
    bigkw = a.pop('bigkw', None)
    fix = a.get('fixg' if plates else 'fix'); a.pop('fixg', None); a.pop('fix', None)
    drop_edge = a.pop('drop_edge', ''); lone = a.pop('lone_dark', False); noclean = a.pop('noclean', False); post2 = a.pop('post2', None); notext = a.pop('notext', False); noshadow = a.pop('noshadow', False)
    r5.SKIN_ON = skin
    if plates:
        a['plates'] = plates; a.update(BIG if not bigkw else bigkw)
    rgb = illus._load(F[idx], box).copy()
    ox, oy = (box[0], box[1]) if box else (0, 0)
    for x0, y0, x1, y1 in clear: rgb[max(0, y0 - oy):max(0, y1 - oy), max(0, x0 - ox):max(0, x1 - ox)] = 255
    if notext:
        pr = [(x0 - ox, y0 - oy, x1 - ox, y1 - oy) for x0, y0, x1, y1 in (notext.get('protect', ()) if isinstance(notext, dict) else ())]      # retângulos em pixels da imagem inteira
        rgb = strip_text(rgb, protect=pr)
    if noshadow: rgb = kill_shadow(rgb)
    rows = illus5.convert5(rgb=rgb, **a)
    if drop_edge: rows = beadclean.drop_edge(rows, drop_edge)
    if lone: rows = beadclean.lone_dark(rows)
    rows = loose.fill_pinholes(rows if noclean else beadclean.clean(rows))[0]
    rows = rows if a.get('post') else lg(rows)
    if post2: rows = lg(post2(rows))
    if fix:
        rows = fix(rows)
        if loose.loose_count(rows): rows = loose.fix_loose(rows)
    return rows


_PALE = ''.join(c['letter'] for c in ALL if c['code'] in ('E14', 'E11', 'E15', 'E1', 'G1', 'E2'))


def drop_text(rows, neutral='kwilmdhM' + _PALE, maxsize=1500):
    """figurinhas com o nome do golpe em katakana (contorno preto + miolo branco): componente conexo SÓ de letras neutras (preto/branco/cinza) é texto e sai; o texto que encosta no desenho fica"""
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    k, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep_ids = set()
    for i in range(1, k):
        letters = {rows[y][x] for y, x in zip(*np.nonzero(lab == i))}
        if not (letters <= set(neutral)) or st[i][4] > maxsize: keep_ids.add(i)
    return O.trim([''.join(c if c != '.' and lab[y, x] in keep_ids else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)])


# (nome, série, índice, kwargs do convert5, placas do irmão grande (None = sem irmão), caixa em pixels (None = imagem toda))
ILL = [
 ('Toshiro Hitsugaya (Bleach, chibi, katana)', 'Bleach', 0, dict(CH, **WH, fix=WF.fx('toshiro'), fixg=WF.fx('toshiro', True)), 4, None),
 ('Emblema do Sol dos Chapéus de Palha (One Piece)', 'One Piece', 1, dict(CH), 4, None),
 ('Shikamaru Nara (Naruto, chibi, fumaça)', 'Naruto', 2, dict(CH, holes_bg=(1.0, 6.0), center_map=WC.combo(WC.smoke(), CM_ALL), fix=WF.fx('shikamaru'), fixg=WF.fx('shikamaru', True)), 4, (0, 450, 1200, 2133)),
 ('Sukuna (Jujutsu Kaisen, chibi, adesivo)', 'Jujutsu Kaisen', 3, dict(CH, **ST), 4, None),
 ('Endou Mamoru (Inazuma Eleven, mão de fogo)', 'Inazuma Eleven', 5, dict(CH), 4, None),
 ('Mulher do guarda-chuva amarelo (How I Met Your Mother)', 'How I Met Your Mother', 6, dict(CH), 4, None),
 ('Kento Nanami (Jujutsu Kaisen, chibi, correndo)', 'Jujutsu Kaisen', 7, dict(CH), 4, None),
 ('Kento Nanami (Jujutsu Kaisen, chibi, sentado)', 'Jujutsu Kaisen', 10, dict(CH), 4, None),
 ('Casal sob o guarda-chuva amarelo na chuva (How I Met Your Mother)', 'How I Met Your Mother', 11, dict(CH, **NONE), 4, None),
 ('Dabi (My Hero Academia, chibi)', 'My Hero Academia', 12, dict(CH), 4, None),
 ('Kento Nanami (Jujutsu Kaisen, chibi, braços cruzados)', 'Jujutsu Kaisen', 13, dict(CH), 4, None),
 ('Quebra-cabeça do Milênio (ilustração)', 'Yu-Gi-Oh', 15, dict(CH, holes_bg=(1.5, 8.0)), 4, None),
 ('Casal sob o guarda-chuva amarelo (How I Met Your Mother, ilustração)', 'How I Met Your Mother', 19, dict(CH), 4, None),
 ('Ryuk (Death Note, chibi)', 'Death Note', 20, dict(CH), 4, None),
 ('Endeavor (My Hero Academia, chibi, adesivo)', 'My Hero Academia', 21, dict(CH, **ST), 4, None),
 ('Shoto Todoroki (My Hero Academia, chibi, adesivo)', 'My Hero Academia', 22, dict(CH, **WH, peel=2.0), 4, None),
 ('Muzan Kibutsuji (Demon Slayer, chibi)', 'Demon Slayer', 24, dict(CH, fix=WF.fx('muzan'), fixg=WF.fx('muzan', True)), 4, None),
 ('Naruto (Modo Sábio dos Seis Caminhos, chibi)', 'Naruto', 28, dict(CH), 4, None),
 ('Saitama (One Punch Man, chibi)', 'One Punch Man', 29, dict(CH), 4, None),
 ('Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)', 'How I Met Your Mother', 30, dict(CH, bg='flat', tol=40), 4, None),
 ('Guerreiro verde de túnica vermelha (corpo inteiro)', 'Outros', 31, dict(CH), 4, None),
 ('Quebra-cabeça do Milênio (contorno)', 'Yu-Gi-Oh', 34, dict(CH), 4, None),
 ('Ikkaku Madarame (Bleach, chibi, lança)', 'Bleach', 36, dict(CH), 4, None),
 ('Yusuke Urameshi (Yu Yu Hakusho, pose)', 'Yu Yu Hakusho', 38, dict(CH), 4, None),
 ('Sasuke e a cobra de Orochimaru (Naruto, chibi)', 'Naruto', 39, dict(CH), 4, None),
 ('Obanai Iguro (Demon Slayer, chibi, adesivo)', 'Demon Slayer', 40, dict(CH, **ST), 4, None),
 ('Nezuko Kamado (Demon Slayer, chibi, corações)', 'Demon Slayer', 41, dict(CH), 4, None),
 ('Nezuko Kamado (Demon Slayer, chibi, bambu)', 'Demon Slayer', 42, dict(CH), 4, None),
 ('Nezuko Kamado (Demon Slayer, adesivo, máscara de raposa)', 'Demon Slayer', 44, dict(CH, **ST), 4, None),
 ('Kazuma Kuwabara (Yu Yu Hakusho, espada espiritual)', 'Yu Yu Hakusho', 45, dict(CH), 4, None),
 ('Kisuke Urahara (Bleach, chibi)', 'Bleach', 48, dict(CH), 4, None),
 ('Broly (Dragon Ball, chibi)', 'Dragon Ball', 49, dict(CH), 4, None),
 ('Itachi Uchiha (Naruto, chibi, corvos)', 'Naruto', 50, dict(CH, fix=WF.fx('itachi_corvos'), fixg=WF.fx('itachi_corvos', True)), 4, None),
 ('Yu Yu Hakusho (quarteto em círculo)', 'Yu Yu Hakusho', 51, dict(CH, bg='white', thr=240), 4, None),
 ('Chibi de roupa listrada verde e roxa sobre uma tábua', 'Outros', 53, dict(CH), 4, None),
 ('Going Merry (ilustração)', 'One Piece', 54, dict(CH, seal=1.0), 4, None),
 ('Goku (Instinto Superior, chibi, adesivo)', 'Dragon Ball', 55, dict(CH, **ST, **WH, clear=[(0, 1200, 736, 1308), (380, 1170, 736, 1200)]), 4, None),
 ('Naruto (Modo Baryon, chibi)', 'Naruto', 56, dict(CH), 4, None),
 ('Bartholomew Kuma (One Piece, chibi)', 'One Piece', 57, dict(CH, thr=226), 4, None),
 ('Casal sob o guarda-chuva amarelo (How I Met Your Mother, pintura)', 'How I Met Your Mother', 61, dict(CH, **NONE), 4, None),
 ('Yoruichi Shihouin (Bleach, chibi, agachada)', 'Bleach', 62, dict(CH), 4, None),
 ('Suguru Geto (Jujutsu Kaisen, chibi)', 'Jujutsu Kaisen', 63, dict(CH, **WH, dark_frac=0.20), 4, None),
 ('Yoruichi Shihouin (Bleach, chibi, gata)', 'Bleach', 67, dict(CH), 4, None),
 ('Kenpachi Zaraki (Bleach, chibi)', 'Bleach', 69, dict(CH), 4, None),
 ('Itachi Uchiha (Naruto, chibi, com o corvo)', 'Naruto', 70, dict(CH, fix=WF.fx('itachi_corvo'), fixg=WF.fx('itachi_corvo', True)), 4, None),
 ('Barney Stinson (How I Met Your Mother, de terno)', 'How I Met Your Mother', 71, dict(CH, bg='flat', tol=30, clear=[(0, 1400, 400, 1623), (700, 1560, 1200, 1623)]), 4, None),
 ('Silhuetas sob o guarda-chuva amarelo (How I Met Your Mother)', 'How I Met Your Mother', 72, dict(CH, **NONE), 2, None),
 ('Might Guy (Naruto, oitavo portão)', 'Naruto', 73, dict(CH), 4, None),
 ('Monkey D. Garp (One Piece, chibi)', 'One Piece', 74, dict(CH), 4, None),
 ('Casal dançando (La La Land)', 'La La Land', 75, dict(CH), 4, None),
 ('Goku Black Rosé (Dragon Ball, chibi)', 'Dragon Ball', 76, dict(CH, **WH), 4, None),
 ('Casal dançando à noite (La La Land)', 'La La Land', 77, dict(CH, **NONE), 4, None),
 ('Jiraiya (Naruto, chibi, modo sábio)', 'Naruto', 79, dict(CH, **WH, fix=WF.fx('jiraiya'), fixg=WF.fx('jiraiya', True)), 4, None),
 ('Barney Stinson (How I Met Your Mother, sinal de paz)', 'How I Met Your Mother', 80, dict(CH, **ST), 4, None),
 ('Thousand Sunny (ilustração)', 'One Piece', 81, dict(CH, seal=1.0), 4, None),
 ('Yuuto Kidou (Inazuma Eleven, chibi, explosão)', 'Inazuma Eleven', 87, dict(CH), 4, None),
 ('Kaido (One Piece, chibi)', 'One Piece', 88, dict(CH, black_L=4.0, dark_frac=0.40, K=30, center_map=lambda *a: CM_BV(*a) or CM_BLOND(*a)), 4, None),
 ('Endeavor (My Hero Academia, rosto em chamas)', 'My Hero Academia', 90, dict(CH), 4, None),
 ('Jushiro Ukitake (Bleach, chibi)', 'Bleach', 91, dict(CH, **WH), 4, None),
 ('Dracule Mihawk (One Piece, chibi)', 'One Piece', 92, dict(CH, thr=226), 4, None),
 ('Gohan (Dragon Ball, chibi)', 'Dragon Ball', 93, dict(CH), 4, None),
 ('Sanemi Shinazugawa (Demon Slayer, chibi, adesivo)', 'Demon Slayer', 94, dict(CH, **ST, **WH), 4, None),
 ('Hinata Hyuga (Naruto, chibi, chamas azuis)', 'Naruto', 95, dict(CH), 4, None),
 ('Koenma (Yu Yu Hakusho, chibi)', 'Yu Yu Hakusho', 96, dict(CH), 4, None),
 # folhas com vários personagens (caixas em pixels lidas com régua)
 ('Yusuke Urameshi (Yu Yu Hakusho, chibi, folha)', 'Yu Yu Hakusho', 16, dict(CH), 4, (30, 20, 185, 325)),
 ('Keiko Yukimura (Yu Yu Hakusho, chibi, folha)', 'Yu Yu Hakusho', 16, dict(CH), 4, (245, 15, 420, 325)),
 ('Kazuma Kuwabara (Yu Yu Hakusho, chibi, folha)', 'Yu Yu Hakusho', 16, dict(CH), 4, (20, 345, 180, 670)),
 ('Hiei (Yu Yu Hakusho, chibi, folha)', 'Yu Yu Hakusho', 16, dict(CH), 4, (240, 330, 425, 660)),
 ('Gouenji Shuuya (Inazuma Eleven, Fire Tornado)', 'Inazuma Eleven', 66, dict(CH, **WH, notext=dict(protect=[(85, 45, 240, 195)]), post2=drop_text, center_map=WC.combo(WC.CM_NEUT, CM_ALL), fix=WF.fx('gouenji'), fixg=WF.fx('gouenji', True)), 4, (30, 40, 262, 282)),
 ('Endou Mamoru (Inazuma Eleven, punho gigante)', 'Inazuma Eleven', 66, dict(CH, notext=dict(protect=[(395, 60, 535, 190)]), post2=drop_text, center_map=WC.combo(WC.CM_BROWN, CM_ALL)), 4, (275, 35, 560, 232)),
 ('Fubuki Shirou (Inazuma Eleven, Eternal Blizzard)', 'Inazuma Eleven', 66, dict(CH, **WH, notext=dict(protect=[(640, 60, 800, 205)]), post2=drop_text, center_map=WC.combo(WC.CM_NEUT, CM_ALL), fix=WF.fx('fubuki'), fixg=WF.fx('fubuki', True)), 4, (555, 40, 825, 270)),
 ('Jogador de cabelo verde-escuro e faixa vermelha (Inazuma Eleven, Heat Tackle)', 'Inazuma Eleven', 66, dict(CH, notext=dict(protect=[(195, 305, 330, 440)]), post2=drop_text), 4, (140, 290, 365, 520)),
 ('Endou Mamoru (Inazuma Eleven, God Hand)', 'Inazuma Eleven', 66, dict(CH, notext=dict(protect=[(550, 285, 665, 415)]), post2=drop_text, center_map=WC.combo(WC.CM_BROWN, CM_ALL)), 4, (430, 285, 660, 500)),
 ('Ichirouta Kazemaru (Inazuma Eleven, Shippuu Dash)', 'Inazuma Eleven', 66, dict(CH, notext=dict(protect=[(50, 580, 255, 700)]), post2=drop_text, fix=WF.fx('kazemaru'), fixg=WF.fx('kazemaru', True)), 4, (40, 570, 260, 745)),
 ('Yuuto Kidou (Inazuma Eleven, óculos e capa)', 'Inazuma Eleven', 66, dict(CH, notext=dict(protect=[(335, 525, 535, 660)]), post2=drop_text, center_map=WC.combo(WC.CM_BROWN, CM_ALL), fix=WF.fx('kidou'), fixg=WF.fx('kidou', True)), 4, (310, 520, 540, 780)),
 ('Endou Mamoru (Inazuma Eleven, Mugen the Hand)', 'Inazuma Eleven', 66, dict(CH, notext=dict(protect=[(645, 540, 790, 640)]), post2=drop_text, center_map=WC.combo(WC.CM_BROWN, CM_ALL), fix=WF.fx('mugen'), fixg=WF.fx('mugen', True)), 4, (580, 530, 800, 770)),
]


NOSKIN = ('Emblema', 'Sunny', 'Merry', 'Quebra', 'logo', 'Trompa', 'Silhuetas', 'Guerreiro', 'Ryuk', 'listrada', 'pintura')
def _skin(n): return not any(k in n for k in NOSKIN)


for _n, _g, _i, _kw, _pl, _box in ILL:
    CFG.append((_n, _g, _i, (lambda i=_i, kw=_kw, b=_box, sk=_skin(_n): ill(i, kw, box=b, skin=sk)), 'ill', _pl, _box, _kw))


# ---------------------------------------------------------------- fotos de peça pronta (APROXIMADO: grade de contas por fitgrid, centro de cada conta pela cor mais próxima de uma paleta explícita)
def photo(idx, p0, spread, bbox, bgc, tol, groups, **kw):
    """photo7.convert com fundo = tom global `bgc` (tol); groups = centros de cor [(rgb, letra ou None=near120)] lidos com photo7.py (K grupos)"""
    import photo7 as P7
    pal = [(c, (l or r5.near120(c))) for c, l in groups]
    bgc = np.array(bgc, float)
    return P7.convert(22, idx, p0, spread, bbox, bg=(lambda c: float(np.linalg.norm(np.array(c) - bgc)) < tol), pal=pal, **kw)


PH99 = [((223, 187, 153), None), ((239, 206, 167), None), ((200, 151, 102), None), ((211, 171, 131), None), ((41, 36, 40), 'k'), ((16, 35, 116), None), ((24, 40, 70), 'k'),
        ((148, 83, 43), None), ((243, 183, 109), None), ((175, 110, 72), None), ((92, 57, 48), None), ((37, 101, 47), None), ((110, 100, 81), None), ((192, 14, 17), None)]
CFG += [
 ('Chaveiro de chapéu e faixa verde e amarela (foto de peça pronta)', 'Política', 99, lambda: lg(photo(99, 9.9, 0.06, (85, 200, 325, 465), (233, 199, 166), 46, PH99)), 'foto'),
]


# ---------------------------------------------------------------- folha de conferência: fonte | molde (fundo roxo: o branco das contas aparece)
def pairsheet(items, path, H=300, W=1900, purple=True, ruler=0):
    """items = [(título, imagem de origem (PIL) ou None, linhas do molde)]"""
    L2 = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in ALL}
    tiles = []
    for t, src, rows in items:
        sc = max(2, min(10, H // len(rows)))
        h = len(rows) * sc; w = len(rows[0]) * sc
        mol = Image.new('RGB', (w, h), (98, 70, 140) if purple else (200, 200, 205)); d = ImageDraw.Draw(mol)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.': d.rectangle((x * sc, y * sc, x * sc + sc - 1, y * sc + sc - 1), fill=L2[ch])
        if ruler:
            for k in range(0, len(rows[0]), ruler): d.line([(k * sc, 0), (k * sc, h)], fill=(255, 255, 255), width=1); d.text((k * sc + 1, 0), str(k), fill=(255, 255, 0))
            for k in range(0, len(rows), ruler): d.line([(0, k * sc), (w, k * sc)], fill=(255, 255, 255), width=1); d.text((1, k * sc + 1), str(k), fill=(255, 255, 0))
        if src is not None:
            s2 = src.resize((max(1, round(src.width * h / src.height)), h), Image.LANCZOS)
        else:
            s2 = None
        tiles.append((t, s2, mol))
    pad = 12; x = pad; y = pad; rowh = 0; pos = []
    for t, s2, mol in tiles:
        w = (s2.width + 6 if s2 else 0) + mol.width
        if x + w + pad > W: x = pad; y += rowh + pad; rowh = 0
        pos.append((x, y)); x += w + pad; rowh = max(rowh, mol.height + 16)
    sheet = Image.new('RGB', (W, y + rowh + pad), (60, 60, 66)); dr = ImageDraw.Draw(sheet)
    for (t, s2, mol), (x, y) in zip(tiles, pos):
        dr.text((x, y), t[:70].encode('ascii', 'replace').decode(), fill=(255, 255, 0))
        if s2: sheet.paste(s2, (x, y + 14)); sheet.paste(mol, (x + s2.width + 6, y + 14))
        else: sheet.paste(mol, (x, y + 14))
    sheet.save(path)


def source_img(idx, box=None):
    im = Image.open(F[idx]).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    return im.crop(box) if box else im


def plates_of(rows):
    return -(-max(len(x) for x in rows) // 50) * -(-len(rows) // 50)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--H' in sys.argv: args.remove(sys.argv[sys.argv.index('--H') + 1])
    grupo = None
    if '--grupo' in sys.argv:
        grupo = sys.argv[sys.argv.index('--grupo') + 1]; args = [a for a in args if a != grupo]
    one = []; multi = []; sheet_items = []; big_items = []
    for it in CFG:
        n, g, idx, fn, grp = it[:5]
        if grupo and grp != grupo: continue
        if args and not any(a in n for a in args): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = fn(); one.append((n, g, r)); sheet_items.append((f'{idx}: {n} {len(r[0])}x{len(r)}', source_img(idx, it[6] if len(it) > 6 else None), r))
            if grp == 'ill' and it[5] and '--nobig' not in sys.argv:       # irmão grande (2-4 placas)
                b = ill(idx, it[7], plates=it[5], box=it[6], skin=_skin(n))
                multi.append((n + ' (grande)', g, b, {'plates': plates_of(b)})); big_items.append((f'{idx}: {n} (grande) {len(b[0])}x{len(b)}', source_img(idx, it[6]), b))
            elif plates_of(r) > 1: multi.append((n + ' (grande)', g, r, {'plates': plates_of(r)}))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa,', len(multi), 'grandes')
    tag = (grupo or 'all') + ('_f' if args else '')
    rl = 5 if '--rule' in sys.argv else 0
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for k in range(0, len(sheet_items), per):
        pairsheet(sheet_items[k:k + per], os.path.join(OUT, f'r22_{tag}_{k // per}.png'), ruler=rl, H=HH)
    print('folhas', (len(sheet_items) + per - 1) // per)
    for k in range(0, len(big_items), 4):
        pairsheet(big_items[k:k + 4], os.path.join(OUT, f'r22_{tag}_big{k // 4}.png'), H=560)
    if big_items: print('folhas grandes', (len(big_items) + 3) // 4)
    if '--merge' in sys.argv:        # troca/acrescenta só estes moldes nos JSONs já gravados (retoques e reconversões parciais)
        for fn, new_ in (('final24', one), ('final24_multi', multi)):
            if not new_: continue
            pth = os.path.join(SP, 'data', fn + sfx() + '.json')
            old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) else []
            by = {x[0]: list(x) for x in new_}
            old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
            json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
        print('mesclado em final24 / final24_multi')
    if not args and not grupo:
        json.dump(one, open(os.path.join(SP, 'data', 'final24' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(multi, open(os.path.join(SP, 'data', 'final24_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravados final24 / final24_multi')
