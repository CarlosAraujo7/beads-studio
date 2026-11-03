"""convert5: ilustração -> molde com REGIÕES LISAS (2026-10-30, para melhorar os rostos que o usuário reprovou; veja CLAUDE.md §7.16).
Diferença para illus.convert4: o convert4 faz a MÉDIA de cada janela e só depois acha a letra mais próxima das 120, então perto das bordas e em degradês saem tons misturados ("pontilhado": cabelo laranja
com 5 tons, pele manchada). Aqui a imagem é QUANTIZADA ANTES (k-means em Lab em ~K cores, mais alguns centros extras para cores raras: íris, lábios, brilho) e cada conta pega a cor MAIS COMUM da janela
(maioria), com o contorno escuro ainda ganhando quando >= dark_frac da janela é preto. Cada centro vira UMA letra (r5.near120), então tons parecidos nunca se separam. No fim, 1 passada tira
conta isolada cuja cor é parecida (ΔE < smooth_de) com a da vizinhança. Mesma máscara, mesmo tamanho e mesmos parâmetros de fundo do convert4 (thr, bg, tol, seal, peel, plates, pale_skin...).
uso: illus5.convert5(path, size=50, K=18, ...) -> linhas do molde (já cortadas)."""
import os, sys, colorsys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, cv2
import illus, r5, outline as O
from palette import ALL

_LET_LAB = None


def _letter_lab():
    global _LET_LAB
    if _LET_LAB is None:
        _LET_LAB = {c['letter']: illus._lab(np.array([int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], np.float64)) for c in ALL}
    return _LET_LAB


def _nearest(lab_pix, cen, chunk=60000):
    out = np.empty(len(lab_pix), np.int32); dist = np.empty(len(lab_pix), np.float32)
    for a in range(0, len(lab_pix), chunk):
        d = np.linalg.norm(lab_pix[a:a + chunk, None, :] - cen[None, :, :], axis=2)
        out[a:a + chunk] = d.argmin(axis=1); dist[a:a + chunk] = d.min(axis=1)
    return out, dist


def _centers(lab_pix, K, rare_thr, rare_n, min_blob, seed=3):
    cv2.setRNGSeed(seed)
    pts = lab_pix if len(lab_pix) <= 200000 else lab_pix[np.random.RandomState(seed).choice(len(lab_pix), 200000, replace=False)]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.3)
    _, _, cen = cv2.kmeans(pts.astype(np.float32), K, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    cen = cen.astype(np.float64)
    for _ in range(rare_n):                                   # cores raras e pequenas (íris, brilho do olho, lábio) que o k-means funde com a vizinha
        _, dist = _nearest(lab_pix, cen)
        far = dist > rare_thr
        if far.sum() < min_blob: break
        seedpt = lab_pix[np.argmax(dist)]
        close = lab_pix[np.linalg.norm(lab_pix - seedpt, axis=1) < rare_thr * 0.8]
        if len(close) < min_blob * 0.4: break
        cen = np.vstack([cen, close.mean(axis=0)])
    return cen


def convert5(path=None, size=50, rgb=None, box=None, thr=205, bg='auto', refs=None, tol=45, white_outside=None, mask=None, plates=None, K=18, over=8, dark_frac=0.28, black_L=13.0, dark_L=34.0, cover=0.5,
             sat=1.2, contrast=1.05, sharp=0.3, skin_safe=True, pale_skin=False, seal=None, peel=0.0, rare_thr=16.0, rare_n=6, min_blob=None, smooth_de=22.0, trace=None, post=None, pre_blur=0, hatch=0, warm_white=0, holes_bg=0.0, center_map=None, hl_gain=0.0):
    if rgb is None: rgb = illus._load(path, box)
    if mask is not None: m = mask(rgb)
    else:
        if bg == 'auto':
            edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
        if bg == 'flat': m = illus.flat_bg(rgb, refs, tol)
        elif bg == 'none': m = np.zeros(rgb.shape[:2], bool)
        else: m = illus.sticker_bg(rgb, thr, white_outside)
    if plates:
        ys, xs = np.nonzero(~m); size = illus.size_for_plates(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, plates)
    if seal is None: seal = 0.6 if bg == 'white' else 0.0
    if peel or seal:
        ys, xs = np.nonzero(~m); ppb = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / float(size)
        if peel: m = illus.peel_white(rgb, m, peel * max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / 50.0)
        if seal: m = illus.seal_leaks(m, seal * ppb)
    if holes_bg:                     # buracos de BRANCO PURO fechados dentro da figura (fundo entre pernas/asas) também são fundo; área mínima em contas
        import beadclean
        ys, xs = np.nonzero(~m); ppb = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / float(size if not plates else max(size, 1))
        hb = holes_bg if isinstance(holes_bg, (tuple, list)) else (holes_bg, 3.0)          # (área mínima, distância máxima ao fundo de fora), em contas de 1 placa
        ppb1 = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / 50.0
        m = beadclean.enclosed_bg(rgb, m, hb[0] * ppb1 * ppb1, maxd=hb[1] * ppb1)
    raw0 = rgb.copy()
    if pre_blur:                     # tira o hachurado/ruído de ilustração rabiscada: filtro bilateral (suaviza as áreas e mantém as bordas) `pre_blur` vezes
        for _ in range(int(pre_blur)): rgb = cv2.bilateralFilter(rgb, 9, 40, 9)
    if hatch:                        # mediana em janela `hatch` (ímpar): apaga traços finos (hachura/fios) de até ~hatch/2 px
        rgb = cv2.medianBlur(rgb, int(hatch) | 1)
    rgb = illus.enhance(rgb, sat, contrast, sharp, skin_safe)
    ys, xs = np.nonzero(~m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgbc = rgb[y0:y1, x0:x1]; rawc = raw0[y0:y1, x0:x1]; fg = (~m[y0:y1, x0:x1]).astype(np.float32)
    h, w = fg.shape
    s = min(1.0, size / max(w, h)); nw, nh = max(1, round(w * s)), max(1, round(h * s))
    bw, bh = nw * over, nh * over
    fgb = cv2.resize(fg, (bw, bh), interpolation=cv2.INTER_AREA)
    col = cv2.resize(rgbc.astype(np.float32) * fg[..., None], (bw, bh), interpolation=cv2.INTER_AREA) / np.maximum(fgb[..., None], 1e-3)
    colr = cv2.resize(rawc.astype(np.float32) * fg[..., None], (bw, bh), interpolation=cv2.INTER_AREA) / np.maximum(fgb[..., None], 1e-3)
    isfg = fgb > 0.5
    lab = illus._lab(col)
    pix = lab[isfg]
    cen = _centers(pix, K, rare_thr, rare_n, min_blob or max(12, int(0.0006 * len(pix))))
    lid, _ = _nearest(pix, cen)
    lmap = np.full((bh, bw), -1, np.int32); lmap[isfg] = lid
    nC = len(cen)
    # letra de cada centro: cor RGB média dos pixels do centro (enhance) -> near120 (escuros: dark=True)
    cols = col[isfg]
    letters = []; black = []
    for k in range(nC):
        sel = lid == k
        mean = tuple(float(v) for v in cols[sel].mean(axis=0)) if sel.any() else (0.0, 0.0, 0.0)
        Lc = cen[k][0]
        if pale_skin and r5.SKIN_ON and sel.any():
            raw_m = colr[isfg][sel].mean(axis=0); hh, ss, vv = colorsys.rgb_to_hsv(*(raw_m / 255.0)); hh *= 360
            if 8 <= hh <= 62 and 0.03 <= ss <= 0.40 and vv >= 0.88: letters.append(illus._nearest_pale(raw_m)); black.append(False); continue
        letters.append(r5.near120(mean, dark=True) if Lc < dark_L else r5.near120(mean)); black.append(Lc < black_L)
    if center_map:                   # troca por centro de cor (molde a molde): center_map(rgb médio, L, letra, é preto?) -> letra nova ou None (fica)
        for k in range(nC):
            sel = lid == k
            mrgb = tuple(float(v) for v in cols[sel].mean(axis=0)) if sel.any() else (0.0, 0.0, 0.0)
            nl = center_map(mrgb, float(cen[k][0]), letters[k], black[k])
            if nl: letters[k] = nl; black[k] = False
    black = np.array(black)
    if trace is not None:            # diagnóstico: (centro, cor média RGB, L, letra, é preto?, nº de pixels)
        for k in range(nC):
            sel = lid == k
            trace.append((k, tuple(int(v) for v in (cols[sel].mean(axis=0) if sel.any() else (0, 0, 0))), round(float(cen[k][0]), 1), letters[k], bool(black[k]), int(sel.sum())))
    def blocks(a): return a.reshape(nh, over, nw, over, *a.shape[2:])
    counts = np.stack([blocks(lmap == k).sum(axis=(1, 3)) for k in range(nC)], axis=-1)        # (nh, nw, nC)
    nfg = counts.sum(axis=2)
    nblack = counts[:, :, black].sum(axis=2) if black.any() else np.zeros_like(nfg)
    blk_letters = [letters[k] for k in range(nC) if black[k]]
    blk_letter = max(set(blk_letters), key=lambda l: sum(counts[:, :, k].sum() for k in range(nC) if black[k] and letters[k] == l)) if blk_letters else 'k'
    grid = [['.'] * nw for _ in range(nh)]
    for y in range(nh):
        for x in range(nw):
            if nfg[y, x] < cover * over * over: continue
            if nblack[y, x] >= dark_frac * nfg[y, x]: grid[y][x] = blk_letter; continue
            c = counts[y, x].copy(); c[black] = 0
            if c.sum() == 0: grid[y][x] = blk_letter; continue
            # soma por LETRA (centros diferentes que viram a mesma letra somam juntos)
            tot = {}
            for k in np.nonzero(c)[0]: tot[letters[k]] = tot.get(letters[k], 0) + ((c[k] * (1.0 + hl_gain * min(1.0, max(0.0, (float(cen[k][0]) - 20.0) / 60.0)))) if hl_gain else c[k])
            grid[y][x] = max(tot, key=tot.get)
    if warm_white:                   # rosto quase branco que o k-means juntou com o branco de verdade: conta branca cuja cor original é quente (R-B >= warm_white) vira o tom de pele mais claro
        wt = isfg.astype(np.float32)[..., None]
        sumc = (colr * wt).reshape(nh, over, nw, over, 3).sum(axis=(1, 3)); sumw = np.maximum(wt.reshape(nh, over, nw, over, 1).sum(axis=(1, 3)), 1e-3)
        mc = sumc / sumw
        for y in range(nh):
            for x in range(nw):
                if grid[y][x] in ('w', 'i') and mc[y, x, 0] - mc[y, x, 2] >= warm_white and mc[y, x, 0] >= 225: grid[y][x] = illus._nearest_pale(mc[y, x])
    # suavização: conta isolada de cor parecida com a vizinhança vira a da vizinhança (nunca mexe no contorno preto)
    if smooth_de:
        LL = _letter_lab(); g2 = [r[:] for r in grid]
        for y in range(nh):
            for x in range(nw):
                c = grid[y][x]
                if c == '.' or c == blk_letter: continue
                nb = [grid[yy][xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1)) if 0 <= yy < nh and 0 <= xx < nw]
                if c in nb: continue
                cand = [n for n in nb if n != '.' and n != blk_letter]
                if len(cand) < 3: continue
                M = max(set(cand), key=cand.count)
                if cand.count(M) >= 3 and np.linalg.norm(LL[c] - LL[M]) < smooth_de: g2[y][x] = M
        grid = g2
    rows = O.trim([''.join(r) for r in grid])
    if post: rows = post(rows)
    return rows
