"""Ilustração (desenho SEM grade de contas, ex.: adesivo/sticker com fundo branco) -> molde de até N contas, com a paleta ativa (BEADPAL=120).

    import illus
    rows = illus.convert(path, size=50)                    # molde cabendo em 50x50
    parts = illus.split(path, n=10, size=50)               # várias figuras numa imagem: devolve [rows, ...] em ordem de leitura

Método: tira o fundo (claro ligado à borda; a borda branca do adesivo some junto), recorta a figura e, para cada conta, olha a janela
correspondente da imagem grande: se boa parte é contorno escuro a conta é do contorno; senão recebe a letra mais próxima (ΔE2000, 120 cores)
da cor MÉDIA dos pontos claros. Não é cópia exata: é uma redução do desenho, então confira olhando.
"""
import os, sys, colorsys
import numpy as np
import cv2
from PIL import Image
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import r5, shrink, outline as O


def _load(path, box=None):
    im = Image.open(path).convert('RGBA')
    if box: im = im.crop(box)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    return np.array(bg.convert('RGB'))


def background(rgb, thr=205):
    """True onde é fundo: claro (mín. dos canais >= thr) e ligado à borda. thr baixo (205) atravessa a linha cinza fina do adesivo
    e leva junto a borda branca dele; o miolo claro do desenho fica, porque o contorno escuro do desenho o isola"""
    H, W, _ = rgb.shape
    light = (rgb.min(axis=2) >= thr).astype(np.uint8)
    n, lab = cv2.connectedComponents(light, connectivity=4)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
    return np.isin(lab, list(edge)) & (light > 0)


def peel_sticker(rgb, bg):
    """adesivo com contorno externo PRETO + faixa branca + contorno do desenho (Echidna): depois de tirar o fundo, descasca de fora para dentro
    a primeira camada escura fina e a faixa branca seguinte. Só age se achar exatamente esse padrão (escuro nos primeiros pixels, depois >= 75% de branco)."""
    fg = (~bg).astype(np.uint8)
    dist = cv2.distanceTransform(fg, cv2.DIST_L2, 3)
    H, W = fg.shape; dmax = int(0.07 * max(H, W))
    white = rgb.min(axis=2) >= 225; dark = rgb.max(axis=2) < 90
    frac_w = []; frac_d = []
    for d in range(0, dmax):
        m = (dist > d) & (dist <= d + 1)
        n = m.sum()
        frac_w.append(white[m].mean() if n else 0); frac_d.append(dark[m].mean() if n else 0)
    if not frac_d or max(frac_d[:4]) < 0.5: return bg
    d0 = int(np.argmax(frac_d[:4]))
    run = None
    for d in range(d0 + 1, dmax - 2):
        if all(frac_w[d + k] > 0.75 for k in range(3)):
            e = d + 3
            while e < dmax and frac_w[e] > 0.75: e += 1
            run = (d, e); break
    if run is None: return bg
    return bg | (dist <= run[1] + 1)


def _lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


_PALE_SKIN = None
def _pale_skin_letters():
    global _PALE_SKIN
    if _PALE_SKIN is None:
        from palette import ALL
        _PALE_SKIN = frozenset(c['letter'] for c in ALL if c['code'] in ('E14', 'E11', 'E15', 'E1'))
    return _PALE_SKIN


def _nearest_pale(rgb):
    """tom de pele claro (E14/E11/E15/E1) mais próximo por ΔE2000 — não passa pelo near120 porque o croma < 7 o restringiria aos cinzas"""
    pale = _pale_skin_letters()
    d = r5._de2000(np.array(r5.T.rgb2lab(np.array(rgb, float))), r5._A_LAB)
    d = np.where(np.array([c in pale for c in r5._A_LET]), d, 1e9)
    return r5._A_LET[int(np.argmin(d))]


def _cells(rgb, mask_bg, size, over=8, dark_L=32.0, dark_frac=0.30, cover=0.5, trace=None, rgb_raw=None, pale_skin=False, dark_map=None):
    """reduz a figura (sem o fundo) para até size x size contas: cada conta olha uma janela over x over da imagem grande.
    - conta vazia se menos de `cover` da janela é figura;
    - 'contorno': se >= dark_frac dos pontos são escuros (L < dark_L) a conta é do contorno (cor = média dos escuros -> letra mais próxima, com preferência pelo preto);
    - senão: cor média dos pontos NÃO escuros -> letra mais próxima (ΔE2000, 120 cores)."""
    ys, xs = np.nonzero(~mask_bg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = rgb[y0:y1, x0:x1]; fg = (~mask_bg[y0:y1, x0:x1]).astype(np.float32)
    h, w = fg.shape
    s = min(1.0, size / max(w, h)); nw, nh = max(1, round(w * s)), max(1, round(h * s))
    bw, bh = nw * over, nh * over
    fgb = cv2.resize(fg, (bw, bh), interpolation=cv2.INTER_AREA)
    col = cv2.resize(rgb.astype(np.float32) * fg[..., None], (bw, bh), interpolation=cv2.INTER_AREA) / np.maximum(fgb[..., None], 1e-3)
    L = _lab(col)[..., 0]
    isfg = fgb > 0.5
    dark = isfg & (L < dark_L)
    def blocks(a): return a.reshape(nh, over, nw, over, *a.shape[2:])
    nfg = blocks(isfg.astype(np.float32)).sum(axis=(1, 3)); ndk = blocks(dark.astype(np.float32)).sum(axis=(1, 3))
    cb = blocks(col); fb = blocks((isfg & ~dark).astype(np.float32)); db = blocks(dark.astype(np.float32))
    mean_lit = (cb * fb[..., None]).sum(axis=(1, 3)) / np.maximum(fb.sum(axis=(1, 3))[..., None], 1)
    mean_dk = (cb * db[..., None]).sum(axis=(1, 3)) / np.maximum(db.sum(axis=(1, 3))[..., None], 1)
    raw_lit = None
    if pale_skin and rgb_raw is not None and r5.SKIN_ON:
        # rosto claro de chibi (252,237,233): o croma é < 7 e o ΔE2000 o manda para o BRANCO. Com pale_skin=True, conta CLARA de matiz quente (8-62°, S 0,03-0,40, V >= 0,88)
        # na imagem ORIGINAL vira o tom de pele mais claro (E14/E11/E15/E1). Ligue só nas imagens em que o cabelo/roupa não é creme (senão fica bege).
        rawc = rgb_raw[y0:y1, x0:x1].astype(np.float32)
        colr = cv2.resize(rawc * fg[..., None], (bw, bh), interpolation=cv2.INTER_AREA) / np.maximum(fgb[..., None], 1e-3)
        cbr = blocks(colr); raw_lit = (cbr * fb[..., None]).sum(axis=(1, 3)) / np.maximum(fb.sum(axis=(1, 3))[..., None], 1)
    rows = []
    for y in range(nh):
        r = ''
        for x in range(nw):
            if nfg[y, x] < cover * over * over: r += '.'; continue
            if ndk[y, x] >= dark_frac * nfg[y, x] or nfg[y, x] - ndk[y, x] < 1:
                mdk = tuple(float(v) for v in mean_dk[y, x]); l0 = r5.near120(mdk, dark=True)
                if dark_map:           # rampa de cinzas (darkramp.py): o escuro que não é contorno (corpo azul-petróleo, cabelo azulado...) vira H5 em vez de H7
                    l1 = dark_map(mdk, float(_lab(np.array([[mdk]], np.float32))[0, 0, 0]), l0, False)
                    if l1: l0 = l1
                r += l0
            else:
                if raw_lit is not None:
                    _h, _s, _v = colorsys.rgb_to_hsv(*(raw_lit[y, x] / 255.0)); _h *= 360
                    if 8 <= _h <= 62 and 0.03 <= _s <= 0.40 and _v >= 0.88:
                        r += _nearest_pale(raw_lit[y, x]); continue
                r += r5.near120(tuple(float(v) for v in mean_lit[y, x]))
        rows.append(r)
    if trace is not None: trace.update(rows0=list(rows), lit=mean_lit, dk=mean_dk, nfg=nfg, ndk=ndk)    # diagnóstico (colorcheck.py)
    return O.trim(rows)


def sticker_bg(rgb, thr=205, white_outside=None):
    """white_outside=(rx, ry): além do fundo, todo branco (>= 240) FORA da elipse central (raios rx, ry = fração da largura/altura) também é fundo
    — para adesivos cujo desenho tem furos brancos fechados (a fumaça do Subaru) que a inundação a partir da borda não alcança"""
    m = peel_sticker(rgb, background(rgb, thr))
    if white_outside:
        H, W = m.shape; yy, xx = np.mgrid[0:H, 0:W]
        out = ((xx - W / 2) / (white_outside[0] * W)) ** 2 + ((yy - H / 2) / (white_outside[1] * H)) ** 2 > 1
        m = m | ((rgb.min(axis=2) >= 240) & out)
    return m


def convert(path, size=50, box=None, thr=205, white_outside=None, **kw):
    rgb = _load(path, box)
    return _cells(rgb, sticker_bg(rgb, thr, white_outside), size, **kw)


def split(path, n, size=50, thr=205, join=14, min_area=0.004):
    """separa as figuras de uma imagem (adesivos soltos): junta pedaços a até `join` px, ordena em leitura (linhas de cima p/ baixo)"""
    rgb = _load(path)
    mask = background(rgb, thr); fg = (~mask).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * join + 1, 2 * join + 1))
    comp = cv2.dilate(fg, k)
    cnt, lab = cv2.connectedComponents(comp, connectivity=8)
    boxes = []
    for i in range(1, cnt):
        m = (lab == i) & (fg > 0)
        if m.sum() < min_area * fg.size: continue
        ys, xs = np.nonzero(m); boxes.append((ys.min(), ys.max() + 1, xs.min(), xs.max() + 1))
    if len(boxes) != n: raise SystemExit(f'esperava {n} figuras e achei {len(boxes)}: ajuste join/min_area')
    # ordem de leitura: agrupa por linha (centro vertical próximo) e ordena por x
    boxes.sort(key=lambda b: (b[0] + b[1]) / 2)
    rows_, cur = [], [boxes[0]]
    for b in boxes[1:]:
        if abs((b[0] + b[1]) / 2 - np.mean([(c[0] + c[1]) / 2 for c in cur])) < 0.5 * max(b[1] - b[0], cur[0][1] - cur[0][0]): cur.append(b)
        else: rows_.append(cur); cur = [b]
    rows_.append(cur)
    ordered = [b for r in rows_ for b in sorted(r, key=lambda b: b[2])]
    out = []
    for (y0, y1, x0, x1) in ordered:
        pad = 2
        sub = rgb[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
        out.append(_cells(sub, sticker_bg(sub, thr), size))
    return out


# ---------------------------------------------------------------------------------------------------------------------------------
# Método 2 (ilustrações de cartoon, cores chapadas): quantiza as cores da figura em K grupos (k-means em Lab), dá a cada grupo a letra mais
# próxima das 120 e, para cada conta, escolhe a letra que MAIS aparece na janela (moda), com prioridade ao contorno escuro. Mantém as regiões
# de cor limpas (o método 1 faz a média e mistura tons: cabelo amarelo + contorno preto viravam "bege sujo").
# ---------------------------------------------------------------------------------------------------------------------------------
def flat_bg(rgb, refs=None, tol=38):
    """fundo de cor chapada/degradê: pixels a menos de `tol` (RGB) de uma cor de referência e LIGADOS à borda da imagem.
    refs=None -> usa a mediana dos pixels da borda. refs = lista de (r,g,b) para fundos com mais de uma cor (céu + nuvem)."""
    H, W, _ = rgb.shape
    if refs is None:
        edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(float)
        refs = [tuple(np.median(edge, axis=0))]
    near = np.zeros((H, W), bool)
    for r in refs: near |= np.linalg.norm(rgb.astype(float) - np.array(r, float), axis=2) < tol
    n, lab = cv2.connectedComponents(near.astype(np.uint8), connectivity=4)
    edge_ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
    return np.isin(lab, list(edge_ids)) & near


def _cells_q(rgb, mask_bg, size, K=14, over=8, dark_L=34.0, dark_frac=0.30, cover=0.5, seed=7, sat=1.0, thick=0.0):
    ys, xs = np.nonzero(~mask_bg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = rgb[y0:y1, x0:x1]; fg = (~mask_bg[y0:y1, x0:x1]).astype(np.float32)
    h, w = fg.shape
    s_ = min(1.0, size / max(w, h)); nw, nh = max(1, round(w * s_)), max(1, round(h * s_))
    bw, bh = nw * over, nh * over
    if thick:
        # o traço fino do contorno (1-3 px na imagem grande) some quando 17 px viram 1 conta: engrossa os pontos escuros em ~`thick` conta antes de reduzir
        ppb = max(w / nw, h / nh); rad = int(round(thick * ppb))
        if rad >= 1:
            Lfull = _lab(rgb.astype(np.float32))[..., 0]
            dk = ((Lfull < dark_L) & (fg > 0)).astype(np.uint8)
            dk = cv2.dilate(dk, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1)))
            rgb = rgb.copy(); rgb[(dk > 0) & (fg > 0)] = (30, 30, 34)
    col = cv2.resize(rgb, (bw, bh), interpolation=cv2.INTER_AREA).astype(np.float32)
    fgb = cv2.resize(fg, (bw, bh), interpolation=cv2.INTER_AREA) > 0.5
    lab = _lab(col)
    pts = lab[fgb]
    if len(pts) > 60000: pts = pts[np.random.RandomState(seed).choice(len(pts), 60000, replace=False)]
    k = min(K, max(2, len(pts) // 50))
    cv2.setRNGSeed(seed)
    _, _, cen = cv2.kmeans(pts.astype(np.float32), k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    # centros de Lab -> RGB -> letra
    def lab2rgb(c):
        fy = (c[0] + 16) / 116; fx = fy + c[1] / 500; fz = fy - c[2] / 200
        f = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
        xyz = np.array([f(fx) * 0.95047, f(fy), f(fz) * 1.08883])
        M = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]))
        v = M @ xyz; v = np.where(v > 0.0031308, 1.055 * np.abs(v) ** (1 / 2.4) - 0.055, 12.92 * v)
        return np.clip(v * 255, 0, 255)
    letters = []; isdark = []
    for c in cen:
        rgbc = lab2rgb(c); d = c[0] < dark_L
        letters.append(r5.near120(tuple(float(v) for v in rgbc), dark=d)); isdark.append(d)
    uniq = sorted(set(letters)); lid = {l: i for i, l in enumerate(uniq)}
    ldark = np.array([any(isdark[i] for i in range(k) if letters[i] == l) for l in uniq])
    d2 = ((lab.reshape(-1, 1, 3) - cen.reshape(1, k, 3)) ** 2).sum(axis=2)
    near = d2.argmin(axis=1).reshape(bh, bw)
    lut = np.array([lid[letters[i]] for i in range(k)])
    idx = lut[near]; idx[~fgb] = -1
    nL = len(uniq)
    cnt = np.zeros((nh, nw, nL), np.float32)
    for li in range(nL):
        cnt[..., li] = (idx == li).reshape(nh, over, nw, over).sum(axis=(1, 3))
    nfg = cnt.sum(axis=2); ndk = cnt[..., ldark].sum(axis=2) if ldark.any() else np.zeros((nh, nw))
    rows = []
    for y in range(nh):
        r = ''
        for x in range(nw):
            if nfg[y, x] < cover * over * over: r += '.'; continue
            if ldark.any() and ndk[y, x] >= dark_frac * nfg[y, x]:
                c = np.where(ldark, cnt[y, x], -1); r += uniq[int(c.argmax())]
            else:
                c = np.where(ldark, -1, cnt[y, x]); r += uniq[int(c.argmax())] if c.max() > 0 else uniq[int(cnt[y, x].argmax())]
        rows.append(r)
    return O.trim(rows)


def convert2(path, size=50, box=None, thr=205, bg='auto', refs=None, tol=45, white_outside=None, **kw):
    """bg='auto' (borda clara -> 'white', senão 'flat') | 'white' (adesivo/fundo claro) | 'flat' (fundo de cor chapada/degradê ligado à borda; refs/tol) | 'none' (a imagem inteira é figura)"""
    rgb = _load(path, box)
    if bg == 'auto':
        edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
        bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
    if bg == 'flat': m = flat_bg(rgb, refs, tol)
    elif bg == 'none': m = np.zeros(rgb.shape[:2], bool)
    else: m = sticker_bg(rgb, thr, white_outside)
    return _cells_q(rgb, m, size, **kw)


# ---------------------------------------------------------------------------------------------------------------------------------
# Método 3 (o melhor para rostos): redução por ÁREA direto para o tamanho final (cada conta = média da sua região, com saturação/contraste
# realçados e nitidez antes), letra mais próxima nas 120 (ΔE2000, guardas de pele/preto) e depois REDUÇÃO DE PALETA: só ficam as `ncolors`
# letras mais usadas (o preto H7 sempre fica); as outras viram a mais parecida entre as que ficaram. Menos cores = molde mais limpo e
# mais fácil de montar (e some o ruído de tons vizinhos).
# ---------------------------------------------------------------------------------------------------------------------------------
def reduce_palette(rows, ncolors=16, keep='k'):
    from collections import Counter
    cnt = Counter(c for r in rows for c in r if c != '.')
    keepers = set(keep) & set(cnt)
    for l, _ in cnt.most_common():
        if len(keepers) >= ncolors: break
        keepers.add(l)
    if len(keepers) == len(cnt): return rows
    idx = {c['letter']: i for i, c in enumerate(r5._A_COL)}
    out = []
    for r in rows:
        row = ''
        for c in r:
            if c == '.' or c in keepers: row += c; continue
            d = r5._de2000(r5._A_LAB[idx[c]], r5._A_LAB[[idx[k] for k in keepers]])
            row += list(keepers)[int(np.argmin(d))]
        out.append(row)
    return out


def convert3(path, size=50, box=None, thr=205, bg='auto', refs=None, tol=45, white_outside=None, sat=1.25, contrast=1.15, sharp=0.6, ncolors=16, cover=0.5, mask=None):
    rgb = _load(path, box)
    if mask is not None: m = mask(rgb)
    else:
        if bg == 'auto':
            edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
        if bg == 'flat': m = flat_bg(rgb, refs, tol)
        elif bg == 'none': m = np.zeros(rgb.shape[:2], bool)
        else: m = sticker_bg(rgb, thr, white_outside)
    ys, xs = np.nonzero(~m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = rgb[y0:y1, x0:x1]; fg = (~m[y0:y1, x0:x1]).astype(np.float32)
    h, w = fg.shape; s_ = min(1.0, size / max(w, h)); nw, nh = max(1, round(w * s_)), max(1, round(h * s_))
    img = rgb.copy()
    if sharp:
        blur = cv2.GaussianBlur(img, (0, 0), max(1.0, 0.012 * max(w, h)))
        img = np.clip(img.astype(np.float32) * (1 + sharp) - blur.astype(np.float32) * sharp, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32); hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
    img = np.clip((cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) - 128) * contrast + 128, 0, 255)
    num = cv2.resize(img * fg[..., None], (nw, nh), interpolation=cv2.INTER_AREA); den = cv2.resize(fg, (nw, nh), interpolation=cv2.INTER_AREA)
    col = num / np.maximum(den[..., None], 1e-3)
    rows = [''.join('.' if den[y, x] < cover else r5.near120(tuple(float(v) for v in col[y, x])) for x in range(nw)) for y in range(nh)]
    rows = O.trim(rows)
    return O.trim(reduce_palette(rows, ncolors)) if ncolors else rows


# ---------------------------------------------------------------------------------------------------------------------------------
# Método 4 (padrão para a remessa 14): método 1 (média só dos pontos CLAROS da janela + contorno escuro quando >= dark_frac da janela é escuro,
# o que evita o "oliva" de amarelo+preto) com realce de saturação/contraste/nitidez antes e redução de paleta depois.
# ---------------------------------------------------------------------------------------------------------------------------------
def enhance(rgb, sat=1.2, contrast=1.1, sharp=0.5, skin_safe=True):
    """realce antes de reduzir. skin_safe: tons de PELE (matiz 8-52, saturação 0,10-0,55, claro) NÃO ganham saturação — com o realce a pele clara virava
    laranja (Shiryu, 2026-10-27) e ia para os tons A12/G9 em vez de G1/G2/E1. Pele CLARA de matiz quente (matiz 14-60, saturação 0,045-0,38, V >= 0,70) volta à cor
    original no fim (sem contraste/nitidez): o realce a deixava branca (rosto do Himmel, 2026-10-28)."""
    h, w = rgb.shape[:2]; img = rgb.copy()
    if sharp:
        blur = cv2.GaussianBlur(img, (0, 0), max(1.0, 0.012 * max(w, h)))
        img = np.clip(img.astype(np.float32) * (1 + sharp) - blur.astype(np.float32) * sharp, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)       # H 0-180, S/V 0-255
    boost = np.full(hsv.shape[:2], sat, np.float32)
    if skin_safe:
        hh = hsv[..., 0] * 2; ss = hsv[..., 1] / 255; vv = hsv[..., 2] / 255
        skin = (hh >= 8) & (hh <= 52) & (ss >= 0.10) & (ss <= 0.55) & (vv >= 0.62)
        boost[skin] = 1.0
    hsv[..., 1] = np.clip(hsv[..., 1] * boost, 0, 255)
    out = np.clip((cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) - 128) * contrast + 128, 0, 255).astype(np.uint8)
    if skin_safe:
        # pele CLARA (rosto de chibi: 245,238,222) não passa pelo realce: o contraste a empurrava para o branco puro (croma < 7 -> só os cinzas) e o rosto virava branco
        o = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32); hh = o[..., 0] * 2; ss = o[..., 1] / 255; vv = o[..., 2] / 255
        pale = (hh >= 14) & (hh <= 60) & (ss >= 0.045) & (ss <= 0.38) & (vv >= 0.70)
        out[pale] = rgb[pale]
    return out


def size_for_plates(w, h, plates, plate=50):
    """maior lado (em contas) para a figura w x h caber em `plates` placas: 1 -> 50; 2 -> lado curto <= 50 e lado longo <= 100; 3 -> longo <= 150 e curto <= 50;
    4 -> 100 (2x2). Nunca amplia além do tamanho da imagem."""
    lo, hi = min(w, h), max(w, h)
    if plates <= 1: return plate
    if plates == 2: return int(min(2 * plate, plate * hi / lo))
    if plates == 3: return int(min(3 * plate, plate * hi / lo))
    return 2 * plate


def style_defaults(name, kw, big=False):
    """padrões por tipo de desenho: CHIBI (rosto pequeno, olhos de 1-2 contas) usa dark_frac baixo para os olhos/boca virarem contas pretas legíveis
    (2026-10-28: Killua, Rem, Jaden). Só vale se o item não definir dark_frac."""
    kw = dict(kw)
    if 'dark_frac' not in kw and 'chibi' in name.lower(): kw['dark_frac'] = 0.20 if big else 0.17
    return kw


def peel_white(rgb, m, r):
    """tira a BORDA BRANCA de adesivo: pixels quase brancos (min(R,G,B) >= 225) a até r px do fundo viram fundo (peel = largura da borda em contas)"""
    r = int(round(r))
    if r < 1: return m
    near = cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
    return m | (near & (rgb.min(axis=2) >= 225))


def seal_leaks(m, width):
    """fecha 'vazamentos' do fundo: canais de fundo mais estreitos que `width` px que entram na figura (traço de contorno com falha: o branco de DENTRO do desenho
    era inundado e virava buraco transparente). Abertura morfológica do fundo; cada pedaço removido só é preenchido se a 'boca' dele para o fundo restante for curta
    (<= 3 larguras: um canal/bolsão). Um fosso fino em volta da figura inteira (boca longa: borda branca do Sharingan) continua sendo fundo."""
    r = int(round(width / 2.0))
    if r < 1: return m
    pad = r + 2
    mp = np.pad(m, pad, constant_values=True).astype(np.uint8)
    mo = cv2.morphologyEx(mp, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    n, lab = cv2.connectedComponents(mo, connectivity=4)
    keep = (lab == lab[0, 0]).astype(np.uint8)                        # fundo de verdade (ligado à moldura)
    removed = ((mp > 0) & (keep == 0)).astype(np.uint8)               # fundo que a abertura tirou
    nr, rl = cv2.connectedComponents(removed, connectivity=4)
    near_keep = cv2.dilate(keep, np.ones((3, 3), np.uint8)) > 0
    out = keep.copy()
    ysf, xsf = np.nonzero(mp == 0); fga = len(ysf); fh, fw = ysf.max() - ysf.min() + 1, xsf.max() - xsf.min() + 1
    for i in range(1, nr):
        comp = rl == i
        mouth = int((comp & near_keep).sum()); a_ = int(comp.sum())
        yy, xx = np.nonzero(comp); ch, cw = yy.max() - yy.min() + 1, xx.max() - xx.min() + 1
        # só preenche bolsões/canais de verdade: boca curta, até 10% da figura e que não abraçam a figura toda (o anel branco do Sharingan é um fosso, não um buraco)
        if mouth > 3 * max(width, 2) or a_ > 0.10 * fga or (cw > 0.8 * fw and ch > 0.8 * fh): out[comp] = 1
    return (out > 0)[pad:-pad, pad:-pad]


def convert4(path, size=50, box=None, thr=205, bg='auto', refs=None, tol=45, white_outside=None, mask=None, ncolors=14, sat=1.2, contrast=1.1, sharp=0.5,
             dark_L=30.0, dark_frac=0.22, cover=0.5, over=8, plates=None, skin_safe=True, trace=None, pale_skin=False, seal=None, peel=0.0):
    rgb = _load(path, box)
    if mask is not None: m = mask(rgb)
    else:
        if bg == 'auto':
            edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
        if bg == 'flat': m = flat_bg(rgb, refs, tol)
        elif bg == 'none': m = np.zeros(rgb.shape[:2], bool)
        else: m = sticker_bg(rgb, thr, white_outside)
    if plates:
        ys, xs = np.nonzero(~m); size = size_for_plates(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, plates)
    if seal is None: seal = 0.6 if bg == 'white' else 0.0         # fundo branco: fecha os vazamentos de até ~0,6 conta (branco de dentro do desenho que virava buraco)
    if peel or seal:
        ys, xs = np.nonzero(~m); ppb = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / float(size)       # pixels da imagem por conta
        if peel: m = peel_white(rgb, m, peel * max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / 50.0)   # peel em contas de uma placa de 50 (a borda do adesivo tem a mesma espessura em px em qualquer tamanho)
        if seal: m = seal_leaks(m, seal * ppb)
    raw0 = rgb.copy()
    if trace is not None: trace.update(raw=raw0, mask=m, size=size)
    rgb = enhance(rgb, sat, contrast, sharp, skin_safe)
    rows = _cells(rgb, m, size, over=over, dark_L=dark_L, dark_frac=dark_frac, cover=cover, trace=trace, rgb_raw=trace['raw'] if trace is not None else raw0, pale_skin=pale_skin)
    return O.trim(reduce_palette(rows, ncolors)) if ncolors else rows
