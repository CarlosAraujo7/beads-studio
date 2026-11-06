"""Remessa 31, 2ª versão (revisão pedida pelo dono em 2026-11-06: "a maioria dos moldes saiu ruim"): limpeza dos moldes de ilustração depois do convert6.
O convert6 com K=34 deixava salpicado (tons de luz e sombra espalhados em contas soltas), manchas e azul/marrom escuros virando preto.
`clean(rows)`: (1) conta sem nenhuma vizinha lateral da mesma cor vira a cor mais comum entre as 8 vizinhas, se for parecida (não toca preto nem branco de olho);
(2) cor rara (<= rare contas) vira a cor presente mais parecida; (3) duas cores quase iguais (ΔE < merge) que se encostam viram a mais usada. Só mexe em cor, nunca em forma."""
import os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from palette import ALL
import illus

LAB = {}
for p in ALL:
    h = p['hex'].lstrip('#'); rgb = np.array([[[int(h[i:i + 2], 16) for i in (0, 2, 4)]]], np.float32)
    LAB[p['letter']] = illus._lab(rgb)[0, 0]
CODE = {p['letter']: p['code'] for p in ALL}
BLACK = {l for l, c in CODE.items() if c in ('H7', 'H6')}


def de(a, b):
    return float(np.linalg.norm(LAB[a] - LAB[b]))


def despeck(rows, maxde=34.0, iters=3, keep=()):
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    for _ in range(iters):
        ch = []
        for y in range(H):
            for x in range(W):
                c = g[y][x]
                if c == '.' or c in BLACK or c in keep: continue
                n4 = [g[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W]
                if c in n4: continue
                n8 = Counter(g[v][u] for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1)
                             if (v, u) != (y, x) and 0 <= v < H and 0 <= u < W and g[v][u] != '.' and g[v][u] not in BLACK)
                if not n8: continue
                best, cnt = n8.most_common(1)[0]
                if cnt >= 3 and de(c, best) < maxde: ch.append((y, x, best))
        if not ch: break
        for y, x, b in ch: g[y][x] = b
    return [''.join(r) for r in g]


def rare(rows, n=3, maxde=22.0, keep=()):
    cnt = Counter(c for r in rows for c in r if c != '.')
    pres = [c for c in cnt if cnt[c] > n]
    mp = {}
    for c in cnt:
        if cnt[c] <= n and c not in BLACK and c not in keep and pres:
            b = min(pres, key=lambda p: de(c, p))
            if de(c, b) < maxde: mp[c] = b
    return [''.join(mp.get(c, c) for c in r) for r in rows]


def merge(rows, thr=9.0, keep=()):
    cnt = Counter(c for r in rows for c in r if c != '.')
    H, W = len(rows), len(rows[0])
    adj = Counter()
    for y in range(H):
        for x in range(W):
            a = rows[y][x]
            for v, u in ((y + 1, x), (y, x + 1)):
                if v < H and u < W:
                    b = rows[v][u]
                    if a != b and a != '.' and b != '.': adj[tuple(sorted((a, b)))] += 1
    mp = {}
    for (a, b), k in sorted(adj.items(), key=lambda t: -t[1]):
        if a in BLACK or b in BLACK or a in keep or b in keep: continue
        a2, b2 = mp.get(a, a), mp.get(b, b)
        if a2 == b2 or de(a2, b2) >= thr: continue
        big, small = (a2, b2) if cnt[a2] >= cnt[b2] else (b2, a2)
        mp[small] = big
        for k_ in list(mp):
            if mp[k_] == small: mp[k_] = big
    return [''.join(mp.get(c, c) for c in r) for r in rows]


def clean(rows, keep=(), merge_thr=9.0, rare_n=3, speck_de=34.0):
    r = merge(rows, merge_thr, keep)
    r = despeck(r, speck_de, keep=keep)
    r = rare(r, rare_n, keep=keep)
    r = despeck(r, speck_de, keep=keep)
    return r


def mode_smooth(rows, need=5, maxde=22.0, iters=2, keep=()):
    """filtro de MAIORIA 3x3 entre tons parecidos: conta (que não é preto) vira a cor que tem >= need das 8 vizinhas, se essa cor for parecida (ΔE < maxde).
    Tira o salpicado de luz e sombra sem apagar faixas largas nem detalhes de cor bem diferente (olho, boca, estampa)."""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    for _ in range(iters):
        ch = []
        for y in range(H):
            for x in range(W):
                c = g[y][x]
                if c == '.' or c in BLACK or c in keep: continue
                n8 = Counter(g[v][u] for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1)
                             if (v, u) != (y, x) and 0 <= v < H and 0 <= u < W)
                best, cnt = n8.most_common(1)[0]
                if best != c and best != '.' and best not in BLACK and cnt >= need and de(c, best) < maxde: ch.append((y, x, best))
        if not ch: break
        for y, x, b in ch: g[y][x] = b
    return [''.join(r) for r in g]


def strong(rows, keep=()):
    return despeck(mode_smooth(merge(rows, 7.0, keep), keep=keep), keep=keep)


def reduce_colors(rows, n=12, keep=(), protect_de=30.0):
    """junta a cor MENOS usada com a mais parecida das outras (ΔE), até sobrarem n cores; preto e branco nunca somem; uma cor pequena mas muito diferente de
    todas as outras (olho, boca, estampa: ΔE >= protect_de da mais parecida) fica."""
    cnt = Counter(c for r in rows for c in r if c != '.')
    mp = {}
    cols = set(cnt)
    WHITE = {l for l, c in CODE.items() if c == 'H2'}
    while len(cols) > n:
        cand = sorted((c for c in cols if c not in BLACK and c not in WHITE and c not in keep), key=lambda c: cnt[c])
        done = False
        for c in cand:
            others = [o for o in cols if o != c]
            b = min(others, key=lambda o: de(c, o))
            if de(c, b) >= protect_de: continue
            mp[c] = b; cnt[b] += cnt[c]; cols.discard(c)
            for k in list(mp):
                if mp[k] == c: mp[k] = b
            done = True; break
        if not done: break
    return [''.join(mp.get(c, c) for c in r) for r in rows]


def tidy(rows, n=12, keep=()):
    return despeck(mode_smooth(reduce_colors(rows, n, keep), need=4, maxde=26.0, keep=keep), keep=keep)


def lone_black(rows, need=5, box=None, iters=2):
    """conta preta SEM vizinha preta de lado, cercada (>= need das 8 vizinhas) por uma mesma cor, vira essa cor: os pontinhos dos fios de cabelo finos sobre o rosto
    e o cabelo. box = (l0, l1, c0, c1) inclusivo, para só mexer numa região (o rosto). Rode ANTES de carimbar os olhos."""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    l0, l1, c0, c1 = box or (0, H - 1, 0, W - 1)
    for _ in range(iters):
        ch = []
        for y in range(max(0, l0), min(H, l1 + 1)):
            for x in range(max(0, c0), min(W, c1 + 1)):
                if g[y][x] not in BLACK: continue
                n4 = [g[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W]
                if any(c in BLACK for c in n4) or '.' in n4 or len(n4) < 4: continue
                n8 = Counter(g[v][u] for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1) if (v, u) != (y, x) and 0 <= v < H and 0 <= u < W)
                b, k = n8.most_common(1)[0]
                if b != '.' and b not in BLACK and k >= need: ch.append((y, x, b))
        if not ch: break
        for y, x, b in ch: g[y][x] = b
    return [''.join(r) for r in g]
