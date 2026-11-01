import sys, os, glob
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import numpy as np
from PIL import Image
import grid2 as G2, img2tpl as T
base = os.path.dirname(SP)
PAL = {c: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for c, h in T.PAL}
LET = {T.LETTER[c]: PAL[c] for c in PAL}
def cells(remessa, idx, crop=None, px=None, mode=False):
    f = sorted(glob.glob(os.path.join(base, 'remessas', f'remessa {remessa}', '*.*')))[idx]
    im = Image.open(f).convert('RGBA')
    if crop: im = im.crop(crop)
    rgba = np.array(im).astype(np.uint8)
    g = G2.detect(rgba, px)
    arr = G2.sample(rgba, g, mode=mode)[..., :3]
    return arr, g
def nearest(c, allowed=None):
    ks = allowed or list(LET)
    return min(ks, key=lambda k: np.linalg.norm(np.array(c, float) - np.array(LET[k], float)))
def letters(arr, allowed=None, bg=lambda c: min(c) > 240):
    H, W, _ = arr.shape
    out = []
    for y in range(H):
        out.append(''.join('.' if bg(arr[y, x]) else nearest(arr[y, x], allowed) for x in range(W)))
    return out
if __name__ == '__main__':
    r = sys.argv[1]; i = int(sys.argv[2]); px = float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
    crop = tuple(int(v) for v in sys.argv[4:8]) if len(sys.argv) > 7 else None
    arr, g = cells(r, i, crop, px)
    print(arr.shape, {k: round(float(v), 2) for k, v in g.items() if np.isscalar(v)})
    rows = letters(arr)
    print('    ' + ''.join(str(x % 10) for x in range(len(rows[0]))))
    for y, row in enumerate(rows): print(f'{y:2d}  {row}')


def letters_flood(arr, allowed=None, thr=240):
    """fundo = celulas quase brancas ligadas a borda (4 vizinhos); brancos de dentro do desenho ficam"""
    H, W, _ = arr.shape
    white = np.array([[min(arr[y, x]) > thr for x in range(W)] for y in range(H)])
    out = np.zeros((H, W), bool)
    st = [(y, x) for y in range(H) for x in range(W) if (y in (0, H - 1) or x in (0, W - 1)) and white[y, x]]
    for p in st: out[p] = True
    while st:
        y, x = st.pop()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + a, x + b)
            if 0 <= q[0] < H and 0 <= q[1] < W and white[q] and not out[q]: out[q] = True; st.append(q)
    return [''.join('.' if out[y, x] else nearest(arr[y, x], allowed) for x in range(W)) for y in range(H)]


def letters_bg(arr, allowed=None, tol=22):
    """fundo = celulas parecidas com a cor do canto, ligadas a borda (4 vizinhos)"""
    H, W, _ = arr.shape
    ref = np.median(np.array([arr[0, 0], arr[0, W - 1], arr[H - 1, 0], arr[H - 1, W - 1]]), axis=0)
    same = np.array([[np.linalg.norm(arr[y, x] - ref) < tol for x in range(W)] for y in range(H)])
    out = np.zeros((H, W), bool)
    st = [(y, x) for y in range(H) for x in range(W) if (y in (0, H - 1) or x in (0, W - 1)) and same[y, x]]
    for p in st: out[p] = True
    while st:
        y, x = st.pop()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + a, x + b)
            if 0 <= q[0] < H and 0 <= q[1] < W and same[q] and not out[q]: out[q] = True; st.append(q)
    return [''.join('.' if out[y, x] else nearest(arr[y, x], allowed) for x in range(W)) for y in range(H)]
