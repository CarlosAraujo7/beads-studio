"""convert6: ilustração -> molde em ESTILO PIXEL ART: o CONTORNO PRETO primeiro, as cores depois, sem achatar os degradês (2026-11-04).
Pedido do dono, olhando a remessa 29 feita pelo convert5: "uma enorme quantidade ficou simplória, um personagem que tem uma grande quantidade de cores, aí você resumiu em uma
cor no cabelo, um preto na roupa e é isso, sem detalhes", "aconteceu muito o excesso de homogeneidade de cores" e "veja casos onde ajuda muito delimitar o desenho primeiro com
uma linha de contorno preto e a partir daí começar a montar o desenho".

Por que o convert5 achatava: (a) o traço preto da arte tem 2-6 px e cada conta cobre 15-25 px, então o traço some no voto da conta (ou vira mancha quando dark_frac é baixo);
(b) k-means com poucos grupos + near120 juntam luz, base e sombra do cabelo na MESMA conta; (c) a suavização final (smooth_de 22) apagava as contas de luz/sombra isoladas;
(d) o traço preto entrava na média e sujava as cores vizinhas.

O que este faz:
  1. máscara da figura (as mesmas opções do convert5: thr, bg, tol, refs, mask, peel, seal, holes_bg);
  2. TRAÇO da arte em resolução cheia: pixels escuros (e quase neutros ou bem escuros) FINOS; as áreas escuras grandes (cabelo/roupa preta) saem do traço por abertura morfológica e viram COR;
  3. grade das contas com 1 conta de folga em volta (o contorno de fora entra nela);
  4. LINHAS de 1 conta: fração de traço por conta + supressão de não-máximos (a conta vira linha quando é crista em alguma direção e passa do limiar), sem pontos soltos;
  5. CORES: k-means em Lab com MAIS grupos (K 32+) só nos pixels que não são traço; cada conta pega o grupo de maior peso; cada grupo vira uma conta do kit (near120 com as
     travas de pele/vermelho/amarelo e o center_map do molde); dois grupos VIZINHOS bem diferentes (ΔE >= split_de) nunca viram a mesma conta: o menor ganha a 2ª conta mais
     parecida que mantém a ordem de claridade (preserva luz, base e sombra);
  6. linha interna: preta quando separa regiões diferentes; dentro de UMA região (mecha de cabelo, dobra de roupa) vira um tom ESCURO da própria cor (inner='shade');
  7. CONTORNO DE FORA: o anel de contas logo fora da silhueta vira preto, menos onde a borda já é escura (sem contorno duplo);
  8. limpeza leve: só conta isolada QUASE igual à vizinhança (smooth_de 7) muda; buraquinhos de 1-3 contas fechados.
uso: rows = convert6(rgb=imagem_RGB, size=50, **opções)  (a imagem já recortada/limpa; devolve as linhas do molde)."""
import os, sys, colorsys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, cv2
import illus, illus5, r5, outline as O
from palette import ALL

_LL = None
_HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in ALL}
_ALIAS = {c['letter'] for c in ALL if c.get('alias')}
_CODE = {c['letter']: c['code'] for c in ALL}
_SKIN_L = {c['letter'] for c in ALL if c['code'] in ('E11', 'E14', 'E15', 'E1', 'G1', 'G2', 'G3', 'A9', 'A12', 'F1', 'F14', 'E8', 'G9')}
BLACK = next(c['letter'] for c in ALL if c['code'] == 'H7')


def LL():
    global _LL
    if _LL is None: _LL = illus5._letter_lab()
    return _LL


def build_mask(rgb, thr=205, bg='auto', refs=None, tol=45, white_outside=None, mask=None, peel=0.0, seal=None, holes_bg=0.0, size=50):
    """True = fundo. Mesma lógica do illus5.convert5 (sem placas)."""
    if mask is not None: m = mask(rgb)
    else:
        if bg == 'auto':
            edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
        if bg == 'flat': m = illus.flat_bg(rgb, refs, tol)
        elif bg == 'none': m = np.zeros(rgb.shape[:2], bool)
        else: m = illus.sticker_bg(rgb, thr, white_outside)
    if seal is None: seal = 0.6 if bg == 'white' else 0.0
    if peel or seal:
        ys, xs = np.nonzero(~m); big = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
        if peel: m = illus.peel_white(rgb, m, peel * big / 50.0)
        if seal: m = illus.seal_leaks(m, seal * big / float(size))
    if holes_bg:
        import beadclean
        ys, xs = np.nonzero(~m); ppb1 = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / 50.0
        hb = holes_bg if isinstance(holes_bg, (tuple, list)) else (holes_bg, 3.0)
        m = beadclean.enclosed_bg(rgb, m, hb[0] * ppb1 * ppb1, maxd=hb[1] * ppb1)
    return m


def _shift(a, dy, dx, fill=0.0):
    out = np.full_like(a, fill)
    H, W = a.shape
    ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy))
    xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
    out[ys, xs] = a[yd, xd]
    return out


def _alts(lab, n=10):
    """letras do kit mais próximas de uma cor Lab (sem os apelidos, como H12 = A1)"""
    ll = LL()
    cand = [(float(np.linalg.norm(v - lab)), l) for l, v in ll.items() if l not in _ALIAS]
    cand.sort()
    return cand[:n]


def convert6(rgb, size=50, K=34, line_L=38.0, line_C=26.0, area_k=0.42, t_line=0.10, t_strong=0.34, inner='shade', outline=True,
             split_de=11.0, smooth_de=7.0, sat=1.05, contrast=1.0, sharp=0.15, tone_de=22.0, tone_iters=2, skin_safe=True, pale_skin=False, dark_L=34.0, center_map=None,
             rare_thr=16.0, rare_n=8, pre_blur=0, hatch=0, keep_line_frac=0.0, trace=None, shade_min=2, shade_de=36.0, drop_short=3, face_clean=True, face_clean_max=2, pale_hues=((8, 62),), line_src='raw',
             face_seeds=None, face_box=None, face_tol=36, face_main='E11', face_shadow='E14', face_dark=6.0, face_absorb=(), **maskkw):
    m = build_mask(rgb, size=size, **maskkw)
    ys, xs = np.nonzero(~m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    raw = rgb[y0:y1, x0:x1].copy(); fg = ~m[y0:y1, x0:x1]
    img = raw.copy()
    if pre_blur:
        for _ in range(int(pre_blur)): img = cv2.bilateralFilter(img, 9, 40, 9)
    if hatch: img = cv2.medianBlur(img, int(hatch) | 1)
    h, w = fg.shape
    inner_size = size - 2 if outline else size
    ppb = max(w, h) / float(inner_size)
    nw, nh = max(1, int(round(w / ppb))), max(1, int(round(h / ppb)))
    # ---- 2. traço da arte (em resolução cheia, sem realce: o realce de contraste engrossa o escuro)
    lab0 = illus._lab((raw if line_src == 'raw' else img).astype(np.float32))          # o traço vem da imagem ORIGINAL: a suavização (pre_blur) tira o ruído das cores mas apagava o traço fino dos olhos
    L0 = lab0[..., 0]; C0 = np.hypot(lab0[..., 1], lab0[..., 2])
    dark = fg & (L0 < line_L) & ((C0 < line_C) | (L0 < line_L - 14))
    k = max(3, int(round(area_k * ppb))) | 1
    area = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
    area = cv2.dilate(area.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    thin = dark & ~area
    # ---- índice da conta de cada pixel
    cy = np.minimum((np.arange(h) * nh / h).astype(int), nh - 1); cx = np.minimum((np.arange(w) * nw / w).astype(int), nw - 1)
    cell = (cy[:, None] * nw + cx[None, :])
    ncell = nh * nw
    n_all = np.bincount(cell.ravel(), minlength=ncell).astype(np.float64)
    n_fg = np.bincount(cell.ravel(), weights=fg.ravel().astype(np.float64), minlength=ncell)
    n_thin = np.bincount(cell.ravel(), weights=thin.ravel().astype(np.float64), minlength=ncell)
    cover = (n_fg / np.maximum(n_all, 1)).reshape(nh, nw)
    lf = (n_thin / np.maximum(n_all, 1)).reshape(nh, nw)
    # ---- 5. cores: k-means só nos pixels de cor (não traço)
    col = illus.enhance(img, sat, contrast, sharp, skin_safe) if (sat != 1 or contrast != 1 or sharp) else img
    labc = illus._lab(col.astype(np.float32))
    fill = fg & ~thin
    pix = labc[fill]
    cen = illus5._centers(pix, K, rare_thr, rare_n, max(12, int(0.0004 * len(pix))))
    lid, _ = illus5._nearest(pix, cen)
    nC = len(cen)
    cols = col[fill].astype(np.float64); raws = raw[fill].astype(np.float64)
    letters = []; csize = np.bincount(lid, minlength=nC)
    for kk in range(nC):
        sel = lid == kk
        mean = tuple(float(v) for v in cols[sel].mean(axis=0)) if sel.any() else (0.0, 0.0, 0.0)
        Lc = cen[kk][0]
        let = None
        if pale_skin and r5.SKIN_ON and sel.any():
            rm = raws[sel].mean(axis=0); hh, ss, vv = colorsys.rgb_to_hsv(*(rm / 255.0)); hh *= 360
            if any(lo <= hh <= hi for lo, hi in pale_hues) and 0.03 <= ss <= 0.40 and vv >= 0.88: let = illus._nearest_pale(rm)
        if let is None: let = r5.near120(mean, dark=True) if Lc < dark_L else r5.near120(mean)
        if center_map:
            nl = center_map(mean, float(Lc), let, False)
            if nl: let = nl
        letters.append(let)
    # voto por conta
    lidmap = np.full(fill.shape, -1, np.int32); lidmap[fill] = lid
    flat_cell = cell[fill]
    hist = np.bincount(flat_cell * nC + lid, minlength=ncell * nC).reshape(ncell, nC)
    win = hist.argmax(axis=1).reshape(nh, nw); nfill = hist.sum(axis=1).reshape(nh, nw)
    inside = cover >= 0.5
    # ---- 4. linhas de 1 conta (crista da fração de traço)
    cand = inside & (lf >= t_line)
    ridge = np.zeros_like(cand)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = _shift(lf, dy, dx); b = _shift(lf, -dy, -dx)
        ridge |= (lf >= a) & (lf >= b) & ((lf > a) | (lf > b))
    line = cand & (ridge | (lf >= t_strong))
    if keep_line_frac: line |= inside & (lf >= keep_line_frac)
    nb = sum(_shift(line.astype(np.float32), dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    line &= (nb > 0) | (lf >= t_strong)                     # ponto solto de traço some (fica só se o traço é forte: pupila, ponto do olho)
    line |= inside & (nfill < 0.15 * n_all.reshape(nh, nw))   # conta quase toda traço
    if drop_short:                                           # traço curto (<= drop_short contas) no meio de UMA cor: é risco de mecha/dobra, não contorno; vira cor
        nl, lab_l, st_l, _ = cv2.connectedComponentsWithStats(line.astype(np.uint8), connectivity=8)
        for i_ in range(1, nl):
            if st_l[i_][4] > drop_short: continue
            yy, xx = np.nonzero(lab_l == i_)
            if any(lf[y_, x_] >= t_strong for y_, x_ in zip(yy, xx)): continue
            ring = set()
            for y_, x_ in zip(yy, xx):
                for v, u in ((y_ - 1, x_), (y_ + 1, x_), (y_, x_ - 1), (y_, x_ + 1)):
                    if 0 <= v < nh and 0 <= u < nw and not line[v, u]:
                        if not inside[v, u]: ring.add('.')
                        elif nfill[v, u] > 0: ring.add(win[v, u])
            if '.' in ring or len(ring) == 0: continue
            if len({id(None)} | ring) and max(float(np.linalg.norm(cen[a_] - cen[b_])) for a_ in ring for b_ in ring) < 16:
                for y_, x_ in zip(yy, xx): line[y_, x_] = False
    # ---- 5b. preservar luz/base/sombra: grupos vizinhos bem diferentes nunca na mesma conta
    def recount():
        cl = {}
        for y in range(nh):
            for x in range(nw):
                if not inside[y, x] or line[y, x]: continue
                a_ = win[y, x]
                for v, u in ((y + 1, x), (y, x + 1)):
                    if v < nh and u < nw and inside[v, u] and not line[v, u]:
                        b_ = win[v, u]
                        if a_ != b_ and letters[a_] == letters[b_]:
                            key = (min(a_, b_), max(a_, b_)); cl[key] = cl.get(key, 0) + 1
        return cl
    cells_of = np.bincount(win[inside & ~line].ravel(), minlength=nC)
    for _ in range(3):
        pairs = recount()
        changed = False
        for (a_, b_), cnt in sorted(pairs.items(), key=lambda t: -t[1]):
            if letters[a_] != letters[b_]: continue
            d = float(np.linalg.norm(cen[a_] - cen[b_]))
            if d < split_de: continue
            small, other = (a_, b_) if cells_of[a_] <= cells_of[b_] else (b_, a_)
            best = _alts(cen[small], 12); d0 = best[0][0]
            dl = cen[small][0] - cen[other][0]
            for dd, l in best:
                if l == letters[other] or dd > d0 * 1.6 + 5: continue
                if abs(dl) > 4 and np.sign(LL()[l][0] - LL()[letters[other]][0]) != np.sign(dl): continue
                if letters[small] in _SKIN_L and r5.SKIN_ON and l not in _SKIN_L: continue
                letters[small] = l; changed = True; break
        if not changed: break
    if face_clean:                                           # rosto limpo: risco CURTO (1-2 contas: nariz, marca de bochecha) no meio da pele vira pele; contorno de olho (traço maior) fica
        nl_, lab_l_, st_l_, _ = cv2.connectedComponentsWithStats(line.astype(np.uint8), connectivity=8)
        small_ = np.zeros_like(line)
        for i_ in range(1, nl_):
            if st_l_[i_][4] <= face_clean_max: small_ |= (lab_l_ == i_)
        for _ in range(2):
            rm = []
            for y in range(nh):
                for x in range(nw):
                    if not line[y, x] or not small_[y, x] or lf[y, x] >= t_strong * 1.4: continue
                    nbl = [letters[win[v, u]] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1))
                           if 0 <= v < nh and 0 <= u < nw and inside[v, u] and not line[v, u] and nfill[v, u] > 0]
                    if len(nbl) >= 3 and sum(1 for l in nbl if l in _SKIN_L) >= 0.75 * len(nbl): rm.append((y, x))
            for y, x in rm:
                line[y, x] = False
                if nfill[y, x] == 0:                         # conta só de traço: pega a cor de pele vizinha mais comum
                    nbw = [win[v, u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < nh and 0 <= u < nw and inside[v, u] and not line[v, u] and letters[win[v, u]] in _SKIN_L]
                    if nbw: win[y, x] = max(set(nbw), key=nbw.count)
            if not rm: break
    if trace is not None:
        for kk in range(nC): trace.append((kk, tuple(int(v) for v in cen[kk]), letters[kk], _CODE[letters[kk]], int(csize[kk])))
    # ---- grade final (com folga de 1 conta em volta)
    G = [['.'] * (nw + 2) for _ in range(nh + 2)]
    for y in range(nh):
        for x in range(nw):
            if not inside[y, x]: continue
            G[y + 1][x + 1] = BLACK if line[y, x] else letters[win[y, x]]
    ll = LL()
    # ---- 6. linha interna dentro de UMA região vira tom escuro da própria cor
    if inner == 'shade':
        G2 = [r[:] for r in G]
        for y in range(1, nh + 1):
            for x in range(1, nw + 1):
                if G[y][x] != BLACK or not line[y - 1, x - 1]: continue
                nbs = [G[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1))
                       if G[v][u] not in ('.', BLACK)]
                if len(nbs) < shade_min: continue              # cercada de linhas: fica preta
                if any(G[v][u] == '.' for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))): continue   # contorno de fora: sempre preto
                base = max(set(nbs), key=nbs.count)
                if max(float(np.linalg.norm(ll[a] - ll[base])) for a in nbs) > shade_de: continue   # separa regiões diferentes: preta
                Lb = ll[base][0]
                if Lb < 40: continue                           # região já escura: a linha preta não aparece mesmo
                tgt = np.array([Lb - 30, ll[base][1] * 0.95, ll[base][2] * 0.95])
                cand_ = [(float(np.linalg.norm(v - tgt)), l) for l, v in ll.items() if l not in _ALIAS and v[0] < Lb - 14]
                if cand_: G2[y][x] = min(cand_)[1]
        G = G2
    # ---- 7b. tons coerentes: cada conta vira, entre os tons PARECIDOS (ΔE < tone_de) que já estão na janela 3x3, o mais perto da média deles; tira o salpicado e mantém
    #          os degradês (luz/base/sombra continuam: só some o tom solto que não acompanha a vizinhança). Cores bem diferentes (olho, brilho, contorno) não entram na conta.
    for _ in range(int(tone_iters)):
        G2 = [r[:] for r in G]
        for y in range(1, nh + 1):
            for x in range(1, nw + 1):
                c = G[y][x]
                if c in ('.', BLACK): continue
                wts = {}
                for v in (y - 1, y, y + 1):
                    for u in (x - 1, x, x + 1):
                        d = G[v][u]
                        if d in ('.', BLACK) or float(np.linalg.norm(ll[d] - ll[c])) >= tone_de: continue
                        wts[d] = wts.get(d, 0) + (2 if (v == y and u == x) else 1)
                if sum(wts.values()) < 5: continue
                avg = sum(ll[d] * n for d, n in wts.items()) / sum(wts.values())
                G2[y][x] = min(wts, key=lambda d: float(np.linalg.norm(ll[d] - avg)))
        G = G2
    # ---- 8. limpeza leve: conta isolada quase igual à vizinhança
    if smooth_de:
        G2 = [r[:] for r in G]
        for y in range(1, nh + 1):
            for x in range(1, nw + 1):
                c = G[y][x]
                if c in ('.', BLACK): continue
                nbs = [G[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if G[v][u] not in ('.', BLACK)]
                if c in nbs or len(nbs) < 3: continue
                M = max(set(nbs), key=nbs.count)
                if nbs.count(M) >= 3 and float(np.linalg.norm(ll[c] - ll[M])) < smooth_de: G2[y][x] = M
        G = G2
    # ---- 7. contorno de fora
    if outline:
        H2, W2 = nh + 2, nw + 2
        G2 = [r[:] for r in G]
        for y in range(H2):
            for x in range(W2):
                if G[y][x] != '.': continue
                nb4 = [G[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H2 and 0 <= u < W2 and G[v][u] != '.']
                if not nb4: continue
                if all(ll[c][0] < 32 for c in nb4): continue      # a borda já é escura: não dobra o contorno
                G2[y][x] = BLACK
        G = G2
    # geometria da última conversão (folhas de leitura alinhadas com a grade: conta (linha, coluna) do molde final -> pixel da imagem recebida)
    H2_, W2_ = len(G), len(G[0])
    LAST_GEOM.clear(); LAST_GEOM.update(x0=int(x0), y0=int(y0), w=int(w), h=int(h), nw=int(nw), nh=int(nh),
                                         top=next((y for y in range(H2_) if any(c != '.' for c in G[y])), 0),
                                         left=next((x for x in range(W2_) if any(G[y][x] != '.' for y in range(H2_))), 0))
    # ---- 9. rosto pintado da cor da armadura (opcional): sementes no rosto -> pele bege
    if face_seeds:
        G = _face_skin6(G, face_seeds, face_box, face_tol, _LET[face_main], _LET[face_shadow] if face_shadow else None, face_dark, raw, fg, nh, nw,
                        absorb={_LET[c] for c in face_absorb})
    rows = O.trim([''.join(r) for r in G])
    LAST_GEOM['rows'] = rows; LAST_GEOM['raw'] = raw; LAST_GEOM['fg'] = fg
    return rows


_LET = {c['code']: c['letter'] for c in ALL}
LAST_GEOM = {}


def _face_skin6(G, seeds, box, tol, main, shadow, dark_d, raw, fg, nh, nw, clean_max=2, absorb=frozenset()):
    """Rosto que saiu da cor da armadura (Cavaleiros de rosto amarelo-claro ou salmão ao lado do ouro; pedido do dono, 2026-11-04).
    `seeds` = contas (linha, coluna do molde final) no meio do rosto/da pele. Em cada uma, o pixel da arte mais parecido com a cor típica da conta (sem traço)
    vira semente de uma inundação NA ARTE com faixa FIXA `tol` em volta da cor dela (o traço escuro e as cores diferentes seguram: olho, cabelo, armadura).
    As contas com >= 45% de pixels inundados (e dentro de `box`, se dado) viram a pele `main`; as mais escuras que a média do rosto em `dark_d` (L) viram `shadow`.
    Risco preto curto (até `clean_max` contas) cercado de pele vira pele (nariz, marca de bochecha); os olhos (traço maior) ficam."""
    H2, W2 = len(G), len(G[0])
    top = next((y for y in range(H2) if any(c != '.' for c in G[y])), 0)
    left = next((x for x in range(W2) if any(G[y][x] != '.' for y in range(H2))), 0)
    h, w = fg.shape
    img = cv2.GaussianBlur(raw, (3, 3), 0)
    lab = illus._lab(raw.astype(np.float32))
    m = np.zeros((h + 2, w + 2), np.uint8)
    flags = 8 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    for r, c in seeds:
        yi, xi = r + top - 1, c + left - 1
        ya, yb = int(yi * h / nh), max(int(yi * h / nh) + 1, int((yi + 1) * h / nh))
        xa, xb = int(xi * w / nw), max(int(xi * w / nw) + 1, int((xi + 1) * w / nw))
        blk = lab[ya:yb, xa:xb]; ok = fg[ya:yb, xa:xb] & (blk[..., 0] > 50)
        if not ok.any(): continue
        med = np.median(blk[ok], axis=0)
        d = np.linalg.norm(blk - med, axis=2); d[~ok] = 1e9
        py, px = np.unravel_index(int(np.argmin(d)), d.shape)
        cv2.floodFill(img, m, (int(xa + px), int(ya + py)), (0, 0, 0), (tol,) * 3, (tol,) * 3, flags)
    face = (m[1:-1, 1:-1] > 0) & fg
    if os.environ.get('FACE_DEBUG'):                         # FACE_DEBUG=arquivo.png: a arte com o rosto inundado em vermelho (para conferir as sementes)
        dbg = raw.copy(); dbg[face] = (0.45 * dbg[face] + 0.55 * np.array([255, 0, 0])).astype(np.uint8)
        cv2.imwrite(os.environ['FACE_DEBUG'], cv2.cvtColor(cv2.resize(dbg, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST), cv2.COLOR_RGB2BGR))
    if not face.any(): return G
    cy = np.minimum((np.arange(h) * nh / h).astype(int), nh - 1); cx = np.minimum((np.arange(w) * nw / w).astype(int), nw - 1)
    cell = (cy[:, None] * nw + cx[None, :]).ravel()
    n_all = np.bincount(cell, minlength=nh * nw).astype(np.float64)
    fw = face.ravel().astype(np.float64)
    n_face = np.bincount(cell, weights=fw, minlength=nh * nw)
    cov = (n_face / np.maximum(n_all, 1)).reshape(nh, nw)
    cellL = (np.bincount(cell, weights=lab[..., 0].ravel() * fw, minlength=nh * nw) / np.maximum(n_face, 1)).reshape(nh, nw)
    meanL = float(lab[..., 0][face].mean())
    r0, r1, c0, c1 = box if box else (-10 ** 6, 10 ** 6, -10 ** 6, 10 ** 6)
    out = [r_[:] for r_ in G]; changed = []
    for yi in range(nh):
        for xi in range(nw):
            gy, gx = yi + 1, xi + 1
            if cov[yi, xi] < 0.45 or G[gy][gx] in ('.', BLACK): continue
            if not (r0 <= gy - top <= r1 and c0 <= gx - left <= c1): continue
            out[gy][gx] = shadow if (shadow and cellL[yi, xi] < meanL - dark_d) else main
            changed.append((gy, gx))
    if absorb and changed:                                   # mistura da borda do rosto (ex.: oliva entre a pele e o cabelo preto) encostada na pele nova: vira a sombra da pele
        skin = {main, shadow}
        for _ in range(2):
            for gy in range(1, H2 - 1):
                for gx in range(1, W2 - 1):
                    if out[gy][gx] not in absorb or not (r0 <= gy - top <= r1 and c0 <= gx - left <= c1): continue
                    if any(out[v][u] in skin for v, u in ((gy - 1, gx), (gy + 1, gx), (gy, gx - 1), (gy, gx + 1))): out[gy][gx] = shadow or main; changed.append((gy, gx))
    if clean_max and changed:
        skin = {main, shadow}
        y0, y1 = min(p[0] for p in changed), max(p[0] for p in changed)
        x0, x1 = min(p[1] for p in changed), max(p[1] for p in changed)
        seen = set()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if out[y][x] != BLACK or (y, x) in seen: continue
                comp = []; st = [(y, x)]; seen.add((y, x))
                while st:
                    a, b = st.pop(); comp.append((a, b))
                    for v in (a - 1, a, a + 1):
                        for u in (b - 1, b, b + 1):
                            if (v, u) not in seen and 0 <= v < H2 and 0 <= u < W2 and out[v][u] == BLACK: seen.add((v, u)); st.append((v, u))
                if len(comp) > clean_max: continue
                cs = set(comp)
                nb = [out[v][u] for a, b in comp for v in (a - 1, a, a + 1) for u in (b - 1, b, b + 1) if (v, u) not in cs and 0 <= v < H2 and 0 <= u < W2]
                if nb and sum(1 for c_ in nb if c_ in skin) >= 0.75 * len(nb):
                    for a, b in comp: out[a][b] = main
    return out
