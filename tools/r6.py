import sys, os, glob, colorsys
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np
from PIL import Image
import r5, outline as O, grid2 as G2, cellread as C
REM6 = os.path.join(os.path.dirname(SP), 'remessas', 'remessa ' + os.environ.get('REMNUM', '6'))
FILES = sorted(glob.glob(os.path.join(REM6, '*.*')))

def mapc(rgb):
    """mesma regra do hue_letter, com ajustes: cinzas so entre os cinzas; claros com um pouco de cor (pele, lavanda, verde-claro) por Lab;
    verde-agua vivo aceita paleta ate 30 graus de matiz; dourado claro so ambar/amarelo/laranja"""
    if r5._PAL120_MODE == '120': return r5.near120(tuple(float(v) for v in rgb))     # BEADPAL=120: vizinho mais próximo nas 120 cores (ΔE2000)
    r, g, b = [float(v) for v in rgb]
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); h *= 360
    if s < 0.08:
        return r5.lab_letter((r, g, b), allowed='wilmdk')
    if v >= 0.70 and s < 0.45:
        return r5.lab_letter((r, g, b))
    if s >= 0.45 and v >= 0.80 and 28 <= h <= 50:
        return r5.lab_letter((r, g, b), allowed='ayo')
    if s >= 0.45 and v >= 0.85 and 140 <= h <= 200:      # verde-agua vivo: o mais proximo pode ser o mint (ate 30 graus)
        lab = np.array(r5.T.rgb2lab(np.array([r, g, b])))
        cands = [p for p in r5._PALH if p[2] >= 0.25 and r5._hd(h, p[1]) <= 30]
        if cands: return min(cands, key=lambda p: ((lab - p[4]) ** 2).sum())[0]
    if 200 <= h <= 235 and s >= 0.35 and v >= 0.30:      # azul acinzentado: fica no azul, nao no roxo
        return 'b' if v >= 0.45 else r5.hue_letter((r, g, b))
    if 250 <= h <= 330 and 0.20 <= s < 0.45 and v < 0.70:      # malva / roxo apagado: roxo ou lavanda, nao cinza
        return r5.lab_letter((r, g, b), allowed='uvx')
    return r5.hue_letter((r, g, b))

def snap(arr, dist=16):
    """funde as cores quase iguais (ruido de JPEG) na mais comum do grupo"""
    H, W, _ = arr.shape
    from collections import Counter
    cnt = Counter(tuple(int(v) for v in arr[y, x]) for y in range(H) for x in range(W))
    reps = []; where = {}
    for c, n in cnt.most_common():
        for rc in reps:
            if sum((a - b) ** 2 for a, b in zip(c, rc)) ** 0.5 <= dist: where[c] = rc; break
        else:
            reps.append(c); where[c] = c
    out = arr.copy()
    for y in range(H):
        for x in range(W): out[y, x] = where[tuple(int(v) for v in arr[y, x])]
    return out

def load_cells(idx, px=None, crop=None, crop_img=None, mode=False, ring=None):
    im = Image.open(FILES[idx]).convert('RGBA')
    if crop_img: im = im.crop(crop_img)
    bgc = Image.new('RGBA', im.size, (255, 255, 255, 255)); bgc.alpha_composite(im); rgba = np.array(bgc).astype(np.uint8)
    g = px if isinstance(px, dict) else G2.detect(rgba, px)
    arr = G2.sample(rgba, g, mode=mode, ring=ring)[..., :3].astype(float)
    if crop: arr = arr[crop[0]:crop[1], crop[2]:crop[3]]
    return arr

def flood_bg(arr, tol=26, thr=None, ref=None, seeds=None):
    H, W, _ = arr.shape
    if thr is None:
        if ref is None: ref = np.median(np.array([arr[0, 0], arr[0, W - 1], arr[H - 1, 0], arr[H - 1, W - 1]]), axis=0)
        same = np.linalg.norm(arr - np.array(ref, float), axis=2) < tol
    else:
        same = arr.min(axis=2) > thr
    out = np.zeros((H, W), bool)
    st = [(y, x) for y in range(H) for x in range(W) if (y in (0, H - 1) or x in (0, W - 1)) and same[y, x]]
    for q in st: out[q] = True
    while st:
        y, x = st.pop()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + da, x + db)
            if 0 <= q[0] < H and 0 <= q[1] < W and same[q] and not out[q]: out[q] = True; st.append(q)
    return out

def flood_fn(arr, same_fn):
    H, W, _ = arr.shape
    out = np.zeros((H, W), bool)
    st = [(y, x) for y in range(H) for x in range(W) if (y in (0, H - 1) or x in (0, W - 1)) and same_fn(None, (y, x))]
    for q in st: out[q] = True
    while st:
        y, x = st.pop()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + da, x + db)
            if 0 <= q[0] < H and 0 <= q[1] < W and not out[q] and same_fn((y, x), q): out[q] = True; st.append(q)
    return out

def exact6(idx, tol=26, thr=None, px=None, crop=None, crop_img=None, clear=(), drop='', post=None, ref=None, dist=16, bgs=None, allbg=False, mode=False, ring=None, achro=None, grad=None, darkbg=None, colmap=()):
    """padrao com grade, igual ao enviado: so tira o fundo e o que nao e desenho. bgs = lista de (ref,tol) extras para tirar fundos"""
    arr = load_cells(idx, px, crop, crop_img, mode, ring)
    H, W, _ = arr.shape
    if achro is not None:      # fundo xadrez/cinza claro sem cor: cinza-claro ligado a borda
        mx = arr.max(axis=2); mn = arr.min(axis=2); ok = ((mx - mn) <= 10) & (mn > achro)
        out = flood_fn(arr, lambda p, q: ok[q])
    elif grad is not None:     # fundo em degrade: vai passando de celula em celula enquanto a cor muda pouco
        out = flood_fn(arr, lambda p, q: p is None or np.linalg.norm(arr[q] - arr[p]) < grad)
    elif darkbg is not None:   # fundo escuro (furos do pegboard)
        ok = arr.max(axis=2) < darkbg
        out = flood_fn(arr, lambda p, q: ok[q])
    else:
        out = flood_bg(arr, tol, thr, ref)
    for (rf, tl) in (bgs or []):
        out |= flood_bg(arr, tl, None, rf)
    if allbg:      # buracos do desenho que tem a cor do fundo tambem ficam vazios
        rf = ref if ref is not None else np.median(np.array([arr[0, 0], arr[0, W - 1], arr[H - 1, 0], arr[H - 1, W - 1]]), axis=0)
        out |= np.linalg.norm(arr - np.array(rf, float), axis=2) < tol
    arr = snap(arr, dist)
    def pick(c):
        for (rgb, tl, letter) in colmap:       # (também em 120 cores: são decisões aprovadas — pele oliva do Akagi -> marrom, vermelho puro -> F5…)
            if sum((a - b) ** 2 for a, b in zip(c, rgb)) ** 0.5 <= tl: return letter
        return mapc(c)
    rows = [''.join('.' if out[y, x] else pick(arr[y, x]) for x in range(W)) for y in range(H)]
    rows = [''.join('.' if c in drop else c for c in r) for r in rows]
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    rows = O.trim(rows)
    if r5._PAL120_MODE == '120': rows = r5.despeckle120(rows)       # só em 120 cores
    if post: rows = post(rows)
    return O.trim(rows)

def sprite6(idx):
    a = np.array(Image.open(FILES[idx]).convert('RGBA'))
    return O.trim([''.join('.' if a[y, x, 3] < 128 else mapc(a[y, x, :3]) for x in range(a.shape[1])) for y in range(a.shape[0])])


def ring_render(idx, px=None, dark=40, ann_max=12, colmap=(), dist=18, clear=(), post=None):
    """render de contas redondas sobre pegboard escuro: furo vazio = anel cinza, conta preta = anel preto"""
    im = Image.open(FILES[idx]).convert('RGB'); a = np.array(im).astype(float)
    rgba = np.array(im.convert('RGBA')); g = G2.detect(rgba, px)
    pxx, pyy, ox, oy, W, H = g['px'], g['py'], g['ox'], g['oy'], int(g['W']), int(g['H'])
    body = G2.sample(rgba, g, ring=(0.15, 0.42))[..., :3].astype(float)
    def ann(bx, by):
        cx = ox + (bx + .5) * pxx; cy = oy + (by + .5) * pyy
        ys, xs = np.mgrid[int(cy - 7):int(cy + 8), int(cx - 7):int(cx + 8)]
        ok = (ys >= 0) & (ys < a.shape[0]) & (xs >= 0) & (xs < a.shape[1])
        d = np.hypot((xs - cx) / pxx, (ys - cy) / pyy); sel = ok & (d >= 0.33) & (d <= 0.43)
        return a[ys[sel], xs[sel]].max(axis=1).mean() if sel.any() else 0
    snp = snap(body, dist)
    def pick(c):
        for (rgb, tl, letter) in colmap:       # (também em 120 cores: são decisões aprovadas — pele oliva do Akagi -> marrom, vermelho puro -> F5…)
            if sum((u - v) ** 2 for u, v in zip(c, rgb)) ** 0.5 <= tl: return letter
        return mapc(c)
    rows = []
    for by in range(H):
        r = ''
        for bx in range(W):
            if body[by, bx].max() < dark:
                r += 'k' if ann(bx, by) < ann_max else '.'
            else:
                r += pick(snp[by, bx])
        rows.append(r)
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    rows = O.trim(rows)
    if post: rows = post(rows)
    return O.trim(rows)


import fitgrid as F, cv2
def photo6(idx, p0, spread=0.25, bgfn=None, ring=(0.2, 0.42), bbox=None, angles=np.arange(-3, 3.1, 0.5), minsize=4, post=None, dist=22, colmap=(), tmp='r6_tmp.png', check=None, clear=(), keepbg=False, mapper=None):
    """foto de peca pronta: acha a grade de contas, amostra o anel de cada conta e tira o fundo (bgfn) ligado a borda"""
    im = Image.open(FILES[idx]).convert('RGB'); path = os.path.join(OUT, tmp); im.save(path)
    w, h = im.size
    if bbox is None: bbox = (0, 0, w, h)
    rot, cx, cy, p, ang, arr = F.fit(path, bbox, p0, spread=spread, angles=angles, step=1.0, ring=ring)
    if check: F.check(rot, cx, cy, os.path.join(OUT, check), bbox, scale=2.0)
    arr = np.array(arr)[..., :3].astype(float)
    H, W, _ = arr.shape
    isbg = np.array([[bool(bgfn(arr[y, x])) if bgfn else False for x in range(W)] for y in range(H)])
    out = flood_fn(arr, lambda pq, q: isbg[q]) if bgfn else np.zeros((H, W), bool)
    if keepbg: out = isbg
    snp = snap(arr, dist)
    def pick(c):
        for (rgb, tl, letter) in colmap:       # (também em 120 cores: são decisões aprovadas — pele oliva do Akagi -> marrom, vermelho puro -> F5…)
            if sum((u - v) ** 2 for u, v in zip(c, rgb)) ** 0.5 <= tl: return letter
        if mapper:
            m = mapper(c)
            if m: return m
        return mapc(c)
    rows = [''.join('.' if out[y, x] else pick(snp[y, x]) for x in range(W)) for y in range(H)]
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    rows = O.drop_specks(O.trim(rows), maxsize=minsize)
    if post: rows = post(rows)
    return O.trim(rows), dict(p=p, ang=ang, shape=(W, H))
