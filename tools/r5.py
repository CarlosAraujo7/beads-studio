import sys, os, glob, json
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np
from PIL import Image
import cellread as C, outline as O, polish as PL, grid2 as G2, img2tpl as T
REM = os.path.join(os.path.dirname(SP), 'remessas', 'remessa 5')

def pat(idx, tol=26, px=None, mp=None, drop='', crop=None, mode='recolor', keep=(), clear=(), despeckle=True, crop_img=None, post=None, colors=False):
    """padrao com grade (remessa 5): le as celulas, tira o fundo, ajusta o contorno e apara"""
    f = sorted(glob.glob(os.path.join(REM, '*.*')))[idx]
    im = Image.open(f).convert('RGBA')
    if crop_img: im = im.crop(crop_img)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); rgba = np.array(bg).astype(np.uint8)
    g = G2.detect(rgba, px)
    arr = G2.sample(rgba, g, mode=False)[..., :3]
    if crop: arr = arr[crop[0]:crop[1], crop[2]:crop[3]]
    rows = C.letters_bg(arr, tol=tol)
    rows = [''.join('.' if c in drop else (mp or {}).get(c, c) for c in r) for r in rows]
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    if despeckle: rows = O.drop_specks(O.trim(rows), maxsize=2)
    if colors: rows = O.despeckle_colors(rows)
    if post: rows = post(rows)
    if mode == 'recolor': rows = O.recolor_outline(rows)
    elif mode == 'clean': rows = O.clean_k(rows, keep=list(keep))
    return O.trim(rows)


def sprite(idx, mp=None, mode='recolor'):
    """sprite pequeno (1 pixel = 1 conta), fundo transparente"""
    f = sorted(glob.glob(os.path.join(REM, '*.*')))[idx]
    im = Image.open(f).convert('RGBA'); a = np.array(im)
    rows = []
    for y in range(a.shape[0]):
        rows.append(''.join('.' if a[y, x, 3] < 128 else (mp or {}).get(C.nearest(a[y, x, :3]), C.nearest(a[y, x, :3])) for x in range(a.shape[1])))
    rows = O.trim(rows)
    return O.recolor_outline(rows) if mode == 'recolor' else rows

def pat_flood(idx, thr=215, px=None, mp=None, drop='', clear=(), crop=None, mode='recolor', keep=(), crop_img=None, despeckle=True, colors=False, post=None):
    """igual a pat(), mas o fundo e 'claro ligado a borda' (fundos com ruido)"""
    f = sorted(glob.glob(os.path.join(REM, '*.*')))[idx]
    im = Image.open(f).convert('RGBA')
    if crop_img: im = im.crop(crop_img)
    bgc = Image.new('RGBA', im.size, (255, 255, 255, 255)); bgc.alpha_composite(im); rgba = np.array(bgc).astype(np.uint8)
    g = G2.detect(rgba, px)
    arr = G2.sample(rgba, g, mode=False)[..., :3]
    if crop: arr = arr[crop[0]:crop[1], crop[2]:crop[3]]
    rows = C.letters_flood(arr, thr=thr)
    rows = [''.join('.' if c in drop else (mp or {}).get(c, c) for c in r) for r in rows]
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    if despeckle: rows = O.drop_specks(O.trim(rows), maxsize=2)
    if colors: rows = O.despeckle_colors(rows)
    if post: rows = post(rows)
    if mode == 'recolor': rows = O.recolor_outline(rows)
    elif mode == 'clean': rows = O.clean_k(rows, keep=list(keep))
    return O.trim(rows)


def largest(rows):
    """fica so a maior peca (4 vizinhos): tira legendas, marcas d'agua e enfeites soltos"""
    comps = O.components(rows)
    keep = set(comps[0]); h, w = len(rows), len(rows[0])
    return O.trim([''.join(rows[y][x] if (y, x) in keep else '.' for x in range(w)) for y in range(h)])


# ---------- fotos de pecas prontas (fundo branco): grade de contas + cor pela lab ----------
import fitgrid as F, cv2
_PAL = [(T.LETTER[c], np.array(T.rgb2lab(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)))) for c, h in T.PAL]
def lab_letter(rgb, allowed=None, kL=1.0):
    l = np.array(T.rgb2lab(np.array(rgb, float)))
    best = None
    for k, pl in _PAL:
        if allowed and k not in allowed: continue
        d = (kL * (l[0] - pl[0])) ** 2 + (l[1] - pl[1]) ** 2 + (l[2] - pl[2]) ** 2
        if best is None or d < best[0]: best = (d, k)
    return best[1]

def photo(idx, p0, spread=0.25, mp=None, allowed=None, kL=1.0, bgmin=250, bgfn=None, ring=(0.2, 0.42), bbox=None, angles=np.arange(-3, 3.1, 0.5), post=None, minsize=4, tmp='r5_tmp.png', thr_dark=None):
    f = sorted(glob.glob(os.path.join(REM, '*.*')))[idx]
    im = Image.open(f).convert('RGBA'); bgc = Image.new('RGBA', im.size, (255, 255, 255, 255)); bgc.alpha_composite(im)
    path = os.path.join(OUT, tmp); bgc.convert('RGB').save(path)
    a = np.array(bgc.convert('RGB')).astype(int)
    if bbox is None:
        m = (a.min(axis=2) < 244); ys, xs = np.where(m)
        bbox = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(a.shape[1], xs.max() + 6), min(a.shape[0], ys.max() + 6))
    rot, cx, cy, p, ang, arr = F.fit(path, bbox, p0, spread=spread, angles=angles, step=1.0, ring=ring)
    H, W, _ = arr.shape
    white = np.array([[(bgfn(arr[y, x]) if bgfn else arr[y, x].min() >= bgmin) for x in range(W)] for y in range(H)])
    out = np.zeros((H, W), bool); st = [(y, x) for y in range(H) for x in range(W) if (y in (0, H - 1) or x in (0, W - 1)) and white[y, x]]
    for q in st: out[q] = True
    while st:
        y, x = st.pop()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + da, x + db)
            if 0 <= q[0] < H and 0 <= q[1] < W and white[q] and not out[q]: out[q] = True; st.append(q)
    rows = [''.join('.' if out[y, x] else lab_letter(arr[y, x], allowed, kL) for x in range(W)) for y in range(H)]
    if mp: rows = [''.join(mp.get(c, c) for c in r) for r in rows]
    rows = O.trim(rows)
    rows = O.drop_specks(rows, maxsize=minsize)
    if post: rows = post(rows)
    info = dict(p=p, ang=ang, shape=(W, H), bbox=bbox)
    return O.trim(rows), info


# ---------- versao "exata": as cores e o contorno do padrao ficam como estao ----------
_lab_cache = {}
def lab_letter_c(rgb):
    k = tuple(int(round(v / 3.0)) for v in rgb)
    if k not in _lab_cache: _lab_cache[k] = lab_letter(rgb)
    return _lab_cache[k]

def exact(idx, tol=26, thr=None, px=None, crop=None, crop_img=None, clear=(), drop='', post=None, lab=True):
    """padrao com grade, igual ao enviado: so tira o fundo (cor do canto, ou 'claro' ligado a borda) e o que nao e desenho"""
    f = sorted(glob.glob(os.path.join(REM, '*.*')))[idx]
    im = Image.open(f).convert('RGBA')
    if crop_img: im = im.crop(crop_img)
    bgc = Image.new('RGBA', im.size, (255, 255, 255, 255)); bgc.alpha_composite(im); rgba = np.array(bgc).astype(np.uint8)
    g = G2.detect(rgba, px)
    arr = G2.sample(rgba, g, mode=False)[..., :3].astype(float)
    if crop: arr = arr[crop[0]:crop[1], crop[2]:crop[3]]
    H, W, _ = arr.shape
    if thr is None:
        ref = np.median(np.array([arr[0, 0], arr[0, W - 1], arr[H - 1, 0], arr[H - 1, W - 1]]), axis=0)
        same = np.array([[np.linalg.norm(arr[y, x] - ref) < tol for x in range(W)] for y in range(H)])
    else:
        same = np.array([[arr[y, x].min() > thr for x in range(W)] for y in range(H)])
    out = np.zeros((H, W), bool); st = [(y, x) for y in range(H) for x in range(W) if (y in (0, H - 1) or x in (0, W - 1)) and same[y, x]]
    for q in st: out[q] = True
    while st:
        y, x = st.pop()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + da, x + db)
            if 0 <= q[0] < H and 0 <= q[1] < W and same[q] and not out[q]: out[q] = True; st.append(q)
    fn = hue_letter if lab else C.nearest
    rows = [''.join('.' if out[y, x] else fn(arr[y, x]) for x in range(W)) for y in range(H)]
    rows = [''.join('.' if c in drop else c for c in r) for r in rows]
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    rows = O.trim(rows)
    if _PAL120_MODE == '120': rows = despeckle120(rows)
    if post: rows = post(rows)
    return O.trim(rows)

def sprite_exact(idx):
    f = sorted(glob.glob(os.path.join(REM, '*.*')))[idx]
    a = np.array(Image.open(f).convert('RGBA'))
    return O.trim([''.join('.' if a[y, x, 3] < 128 else hue_letter(a[y, x, :3]) for x in range(a.shape[1])) for y in range(a.shape[0])])


# ---------- cor: vizinho mais proximo na paleta, mas respeitando o matiz ----------
import colorsys
from collections import Counter
_PALH = []
for c, h in T.PAL:
    rgb = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)
    hh, ss, vv = colorsys.rgb_to_hsv(*(rgb / 255)); _PALH.append((T.LETTER[c], hh * 360, ss, vv, np.array(T.rgb2lab(rgb))))
def _hd(a, b): d = abs(a - b) % 360; return min(d, 360 - d)
_hue_cache = {}
import palette as _pm; _PAL120_MODE = _pm.MODE
def hue_letter(rgb):
    if _PAL120_MODE == '120': return near120(rgb)
    """cor muito saturada: so vale paleta do mesmo matiz; o resto (cinzas, tons pasteis, pele): vizinho mais proximo em RGB"""
    k = tuple(int(round(v / 3.0)) for v in rgb)
    if k in _hue_cache: return _hue_cache[k]
    rgb = np.array(rgb, float); h, s, v = colorsys.rgb_to_hsv(*(rgb / 255)); h *= 360
    if s >= 0.45 and v >= 0.30:
        lab = np.array(T.rgb2lab(rgb)); cands = []
        if 62 <= h <= 110:           # verde-limao: a paleta nao tem; o verde de verdade fica mais perto que o amarelo
            cands = [p for p in _PALH if 100 <= p[1] <= 175 and p[2] >= 0.25]
        for tol in (22, 38, 60):
            if cands: break
            cands = [p for p in _PALH if p[2] >= 0.25 and _hd(h, p[1]) <= tol]
        out = min(cands or _PALH, key=lambda p: ((lab - p[4]) ** 2).sum())[0]
    else:
        out = C.nearest(rgb)
    _hue_cache[k] = out; return out


# ---------- paleta de 120 cores (BEADPAL=120): vizinho mais próximo por ΔE2000 ----------
import palette as _PAL120
_A_COL = _PAL120.ALL
_A_LET = [c['letter'] for c in _A_COL]
_A_LAB = np.array([T.rgb2lab(np.array([int(c['hex'][i:i + 2], 16) for i in (1, 3, 5)], float)) for c in _A_COL])
_A_NEUTRAL = np.array([c['code'] in ('H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7') for c in _A_COL])
_A_BASE = np.arange(len(_A_COL)) < 24      # as 24 do kit antigo têm hex "conhecido": ganham 1 ΔE de vantagem no empate

def _de2000(l1, L2):
    """ΔE2000 entre uma cor Lab (3,) e várias (n,3)"""
    L1, a1, b1 = l1; L2_, a2, b2 = L2[:, 0], L2[:, 1], L2[:, 2]
    C1 = np.hypot(a1, b1); C2 = np.hypot(a2, b2); Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p = (1 + G) * a1; a2p = (1 + G) * a2
    C1p = np.hypot(a1p, b1); C2p = np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360; h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2_ - L1; dCp = C2p - C1p
    dh = h2p - h1p; dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh)); dh = np.where((C1p * C2p) == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lbp = (L1 + L2_) / 2; Cbp = (C1p + C2p) / 2
    hs = h1p + h2p; hd = np.abs(h1p - h2p)
    hbp = np.where(hd <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)); hbp = np.where((C1p * C2p) == 0, hs, hbp)
    T_ = 1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp)) + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63))
    dth = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)); Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp; Sh = 1 + 0.015 * Cbp * T_; Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))

_near_cache = {}
_A_DARKOK = np.array([c['code'] in ('H7', 'H5', 'G8', 'B15', 'B11', 'H6', 'M12', 'G17', 'F7', 'F10', 'F11', 'C9', 'D15', 'D3', 'C16', 'B12', 'D14', 'D21', 'B17') or T.rgb2lab(np.array([int(c['hex'][i:i + 2], 16) for i in (1, 3, 5)], float))[0] < 38 for c in _A_COL])
# pele: cores claras/médias de matiz quente e pouca saturação (pele de personagem, creme) só viram os tons de pele da paleta —
# senão o ΔE2000 manda "pele" amarelada para A1/H12/M5 (cinza-oliva) e pele escura para M9/G14 (a reclamação do usuário em 2026-10-27)
_SKIN_CODES = ('G1', 'G2', 'G3', 'E1', 'E11', 'E14', 'E15', 'A12', 'G9')
_A_SKIN = np.array([c['code'] in _SKIN_CODES for c in _A_COL])
def is_skin(rgb):
    h, s_, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255)); h *= 360
    return 14 <= h <= 58 and 0.08 <= s_ <= 0.48 and v >= 0.68

# o guarda de pele só vale para personagens com pele (a flag é posta por item: os rN_exfinal chamam skin_for(nome, série) antes de converter);
# em Pokémon, bichos, objetos… o creme/amarelo-pálido é pelo, não pele
SKIN_ON = True
_NOSKIN_SERIES = {'Pokémon', 'Mario', 'Animais', 'Símbolos e objetos', 'Formas e céu', 'Bichinhos', 'Gatos', 'Comidinhas', 'Brincos', 'Duolingo', 'Plants vs Zombies', 'Minions',
                  'Bob Esponja', 'Hello Kitty', 'Studio Ghibli', 'Como Treinar o seu Dragão', 'Looney Tunes', 'Phineas e Ferb', 'Avatar', 'Hora de Aventura', 'Ben 10', 'Halloween',
                  'Stardew Valley', 'Minecraft', 'Angry Birds', 'Sonic', 'Kirby', 'Pou', 'Crash Bandicoot', 'Zootopia', 'Carros', 'Ratatouille', 'Egito Antigo'}
import re as _re
_NOSKIN_NAME = _re.compile(r'Pokébola|Poké Ball|sentado|Togepi|Kanto|Mimikyu|Eevee|Kurama|Pintinho|Galinha|Gato|Panda|Fantasma|Koro-sensei|Cogumelo|Esfera|Bola|Taco|Diamante|Espada|Armadura|Planeta|Lua |Estrela|Coração|Dragonair|Pikachu|Morcego|Crocodilo|Lobo|Unicórnio|Piu-Piu|Patolino|Taz|Perry|Banguela|Stitch|Angel|Hulk|Groot|Pochita|Aku|monstrinho|Slender|Yoshi|Mario|Toad', _re.I)
def skin_for(name, series):
    return series not in _NOSKIN_SERIES and not _NOSKIN_NAME.search(name)

# vivo demais para a paleta estimada: vermelho puro -> F5 (o "r" que o usuário aprovou nas 24 cores); amarelo vivo nunca vira o amarelo-oliva (A1/A3/A15/B1/B18/A8…)
_A_GREENBLACK = np.array([c['code'] in ('B11', 'B15') for c in _A_COL])
_A_YELLOWBAD = np.array([c['code'] in ('A1', 'A3', 'A15', 'B1', 'B18', 'A8', 'H12', 'B13', 'B14', 'B16') for c in _A_COL])

def near120(rgb, allowed=None, dark=False, skin=None):
    """letra (das 120 cores) mais próxima. Cinza/branco/preto de verdade (croma < 7) só viram cinzas H1–H7 (nada de cinza "bege" ou "esverdeado")"""
    if skin is None: skin = SKIN_ON
    k = (tuple(int(round(v / 2.0)) for v in rgb), allowed, dark, skin)
    if k in _near_cache: return _near_cache[k]
    l = np.array(T.rgb2lab(np.array(rgb, float)))
    d = _de2000(l, _A_LAB) - _A_BASE * 1.0
    if np.hypot(l[1], l[2]) < 7: d = np.where(_A_NEUTRAL, d, 1e9)
    elif skin and not dark and is_skin(rgb): d = np.where(_A_SKIN, d, 1e9)
    # quase pretos: cor de contorno vira o PRETO (H7) e não "preto amarelado/esverdeado" (B11/B15/G8), que misturados no mesmo contorno dão um tracejado;
    # entre 22 e 34 de luminosidade B11/B15 só valem se a cor é de fato esverdeada (cabelo marrom escuro não pode virar oliva)
    _L, _C = l[0], float(np.hypot(l[1], l[2]))
    if _L < 22 and _C < 26: _near_cache[k] = 'k'; return 'k'
    if _L < 34 and not (70 <= (np.degrees(np.arctan2(l[2], l[1])) % 360) <= 200 and _C >= 18): d = np.where(_A_GREENBLACK, 1e9, d)
    if not dark:
        h_, s_, v_ = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255)); h_ *= 360
        if s_ >= 0.78 and v_ >= 0.60 and (h_ <= 10 or h_ >= 350): _near_cache[k] = 'r'; return 'r'
        if 38 <= h_ <= 62 and s_ >= 0.50 and v_ >= 0.85: d = np.where(_A_YELLOWBAD, 1e9, d)
    if allowed: d = np.where(np.array([c in allowed for c in _A_LET]), d, 1e9)
    if dark:        # contorno: só cores escuras (L < 38 ou a lista de escuras) e o preto H7 ganha 6 de vantagem
        d = np.where(_A_DARKOK, d, 1e9); d = d - 6.0 * np.array([c == 'k' for c in _A_LET])
    out = _A_LET[int(np.argmin(d))]; _near_cache[k] = out; return out


# ---------- anti-ruído (JPEG): célula isolada que só difere "um pouco" da vizinhança assume a cor da vizinhança ----------
_DEP = None
def despeckle120(rows, T=11.0, minsame=2):
    """com 120 cores o ruído do JPEG vira letras diferentes (Dobby, rostos do Slam Dunk). Uma célula com menos de `minsame` vizinhos (8) da mesma letra
    e cuja cor está a menos de T ΔE2000 da letra mais comum entre os vizinhos passa a ter essa letra. Contornos (k) e cores escuras não mudam."""
    global _DEP
    if _DEP is None:
        _DEP = np.array([_de2000(l, _A_LAB) for l in _A_LAB])
    idx = {c: i for i, c in enumerate(_A_LET)}
    H, W = len(rows), len(rows[0]); g = [list(r) for r in rows]; out = [list(r) for r in rows]
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == '.' or c == 'k': continue
            nb = [g[y + dy][x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and 0 <= y + dy < H and 0 <= x + dx < W and g[y + dy][x + dx] != '.']
            if len(nb) < 3: continue
            same = sum(n == c for n in nb)
            if same >= minsame: continue
            m = Counter(nb).most_common(1)[0][0]
            if m == 'k' or m == c: continue
            if _DEP[idx[c], idx[m]] < T and _A_LAB[idx[c], 0] > 35: out[y][x] = m
    return [''.join(r) for r in out]
