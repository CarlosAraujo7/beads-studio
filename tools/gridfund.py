"""Acha o passo VERDADEIRO de um gráfico cujas contas têm pontinho, código ou anel desenhado dentro (remessa 20): grid2.detect costuma travar em 1/2 ou 1/3 do passo.
Método: amostra a grade fina que o detect achou e procura o maior fator k (com a fase certa) em que cada bloco k×k fica de uma cor só, a menos do desenho interno da conta.
  from gridfund import fund ;  g = fund(arquivo, crop_img=None)   -> dict(px, py, ox, oy, W, H, k, score)  (coordenadas relativas ao recorte; serve para r6.exact6(px=g))
Confira sempre olhando o resultado: desenho com blocos grandes de cor lisa pode enganar (por isso k só sobe quando a nota continua alta)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import grid2 as G2


def _load(path, crop_img=None):
    im = Image.open(path).convert('RGBA')
    if crop_img: im = im.crop(crop_img)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    return np.array(bg).astype(np.uint8)


def _score(q, k, fx, fy):
    """fração de células iguais à cor mais comum do bloco k×k, só nos blocos que têm mais de uma cor forte (desenho, não fundo)"""
    H, W = q.shape; good = tot = 0
    for y in range(fy, H - k + 1, k):
        for x in range(fx, W - k + 1, k):
            b = q[y:y + k, x:x + k].ravel()
            v, c = np.unique(b, return_counts=True)
            if len(v) == 1: continue
            good += c.max(); tot += b.size
    return good / tot if tot else 0.0


def fund(path, crop_img=None, kmax=5, need=0.72, force=None):
    rgba = _load(path, crop_img)
    g = G2.detect(rgba, force)
    a = G2.sample(rgba, g, mode=False)[..., :3]
    q = (a // 40).astype(int); q = q[..., 0] * 100 + q[..., 1] * 10 + q[..., 2]
    best = dict(g, k=1, score=1.0)
    for k in range(2, kmax + 1):
        sc, fx, fy = max((_score(q, k, fx, fy), fx, fy) for fx in range(k) for fy in range(k))
        if sc >= need:
            h, w = rgba.shape[:2]
            ox = g['ox'] + fx * g['px']; oy = g['oy'] + fy * g['py']; px = g['px'] * k; py = g['py'] * k
            while ox > 0: ox -= px
            while oy > 0: oy -= py
            best = dict(px=px, py=py, ox=ox, oy=oy, W=int(np.ceil((w - ox) / px)), H=int(np.ceil((h - oy) / py)), k=k, score=sc, q=g.get('q'))
    return best


if __name__ == '__main__':
    import glob
    rem = sys.argv[1]; fs = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa ' + rem, '*.*')))
    for i in [int(a) for a in sys.argv[2:]] or range(len(fs)):
        g = fund(fs[i]); print('%3d k=%d nota %.2f passo %.2f×%.2f fase %.1f,%.1f  %d×%d' % (i, g['k'], g['score'], g['px'], g['py'], g['ox'], g['oy'], g['W'], g['H']), flush=True)
