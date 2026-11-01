"""Fotos de peças prontas (aproximado!): acha a grade de contas (fitgrid), amostra o anel de cada conta, tira o fundo e dá a letra de cada conta
pela cor mais próxima de uma PALETA EXPLÍCITA da foto (centros de cor escolhidos olhando a foto; sem k-means em tempo de execução => reprodutível).

uso em Python:
    import photo7 as P7
    rows = P7.convert(rem, idx, p0, spread=0.08, bbox=None, bg=fn_ou_None, keep=fn_ou_None, pal=[((r,g,b),'k'), ...], minsize=3, clear=[(y0,y1,x0,x1)], post=None)
      bg(rgb)   -> True se a conta é fundo; o fundo é a inundação a partir da borda das contas para as quais bg() é True
      keep(rgb) -> True se a conta é desenho; tudo o que NÃO é desenho vira vazio (lista branca; para fundos parecidos com o desenho)
      pal       -> lista [((r,g,b), letra)]; cada conta de desenho recebe a letra do centro mais próximo (None = regra geral r6.mapc)
      clear     -> regiões (y0,y1,x0,x1) INCLUSIVAS, em coordenadas da grade amostrada (antes de aparar), que viram vazio
uso na linha de comando (explorar uma foto):
    python tools/photo7.py REM IDX P0 SPREAD [x0,y0,x1,y1|-] K [bgname]   -> imprime os K grupos de cor e grava tools/out/p7_REM_IDX.png (grade sobre a foto)
    p0 = passo da contas em pixels (use autocorrelação / contar contas); a grade desenhada na imagem mostra se acertou
"""
import os, sys, glob, colorsys
SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
os.environ.setdefault('REMNUM', '1')
import numpy as np, cv2
from PIL import Image
import r6, fitgrid as F, outline as O


def hsv(c):
    h, s, v = colorsys.rgb_to_hsv(*(np.array(c, float) / 255)); return h * 360, s, v


def cells(rem, idx, p0, spread=0.08, bbox=None, ring=(0.2, 0.42), angles=np.arange(-3, 3.1, 1.0), check=None):
    files = sorted(glob.glob(os.path.join(ROOT, 'remessas', f'remessa {rem}', '*.*')))
    im = Image.open(files[idx]).convert('RGB'); path = os.path.join(OUT, f'p7_tmp_{rem}_{idx}.png'); im.save(path)
    w, h = im.size
    if bbox is None: bbox = (0, 0, w, h)
    rot, cx, cy, p, ang, arr = F.fit(path, bbox, p0, spread=spread, angles=angles, step=1.0, ring=ring)
    if check: F.check(rot, cx, cy, os.path.join(OUT, check), bbox, scale=2.0)
    return np.array(arr)[..., :3].astype(float), dict(p=p, ang=ang)


def mask(arr, bg=None, keep=None, flood=True):
    """bg(c) ou bg(c, y, x) (y, x = posição da conta na grade, p/ regras que dependem do lugar). flood=False: toda conta com bg()=True é fundo
    (use quando o desenho nunca tem a cor do fundo; senão espaços fechados entre braços/pernas ficam como desenho)"""
    H, W, _ = arr.shape
    if keep is not None:
        kpos = keep.__code__.co_argcount >= 3
        return np.array([[not (keep(arr[y, x], y, x) if kpos else keep(arr[y, x])) for x in range(W)] for y in range(H)])
    if bg is None: return np.zeros((H, W), bool)
    pos = bg.__code__.co_argcount >= 3
    isbg = np.array([[bool(bg(arr[y, x], y, x) if pos else bg(arr[y, x])) for x in range(W)] for y in range(H)])
    if not flood: return isbg
    return r6.flood_fn(arr, lambda pq, q: isbg[q])


def letters(arr, out, pal=None):
    H, W, _ = arr.shape
    cen = np.array([c for c, _ in pal], float) if pal else None
    let = [l for _, l in pal] if pal else None
    def pick(c):
        if pal is None: return r6.mapc(tuple(int(v) for v in c))
        return let[int(np.argmin(((cen - c) ** 2).sum(axis=1)))]
    return [''.join('.' if out[y, x] else pick(arr[y, x]) for x in range(W)) for y in range(H)]


def convert(rem, idx, p0, spread=0.08, bbox=None, bg=None, keep=None, pal=None, minsize=3, ring=(0.2, 0.42), clear=(), post=None, check=None, angles=np.arange(-3, 3.1, 1.0), flood=True):
    arr, info = cells(rem, idx, p0, spread, bbox, ring, angles, check)
    out = mask(arr, bg, keep, flood)
    rows = letters(arr, out, pal)
    for (y0, y1, x0, x1) in clear:
        rows = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(r)) for y, r in enumerate(rows)]
    rows = O.drop_specks(O.trim(rows), maxsize=minsize)
    if post: rows = post(rows)
    return O.trim(rows)


def clusters(rem, idx, p0, spread, bbox, K, bg=None, keep=None, ring=(0.2, 0.42)):
    arr, info = cells(rem, idx, p0, spread, bbox, ring, check=f'p7_{rem}_{idx}.png')
    out = mask(arr, bg, keep)
    pts = arr[~out].astype(np.float32)
    cv2.setRNGSeed(7)
    _, lab, cen = cv2.kmeans(pts, K, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5), 5, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab.ravel(), minlength=K)
    print('passo %.2f x %.2f  ang %.1f  grade %dx%d  contas de desenho %d' % (info['p'][0], info['p'][1], info['ang'], arr.shape[1], arr.shape[0], int((~out).sum())))
    for i in np.argsort(-cnt):
        c = tuple(int(v) for v in cen[i]); print(f'  {c} {cnt[i]:4d} -> {r6.mapc(c)}')


if __name__ == '__main__':
    rem, idx, p0, spread = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    bbox = None if sys.argv[5] == '-' else tuple(int(v) for v in sys.argv[5].split(','))
    clusters(rem, idx, p0, spread, bbox, int(sys.argv[6]))
