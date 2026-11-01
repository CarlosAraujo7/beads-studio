"""Caixa do desenho e tamanho NATIVO do pixel de um sprite SEM grade (pixel art ampliada, JPEG): passo e fase por pente de bordas dentro da caixa do desenho.

uso:  python tools/pixsize.py REMESSA IDX [lo hi]      (índice = posição na lista ordenada da pasta `remessa N`, como em src_sheet.py; passo procurado entre lo e hi px, padrão 2..40)
Imprime a caixa (pixels que diferem do fundo em mais de 40), o passo em x e y, a fase e uma sugestão de `px=dict(...)` já com W,H cobrindo a caixa.
CUIDADOS (remessa 22): (1) o pente pode cair no DOBRO do passo (Bepo: 36,7 em vez de 8,5; Dabi: 32 era certo, mas 16 também pontuou): limite `hi` e CONFIRA olhando as linhas de grade
que o próprio sprite mostra, ou meça as transições preto/branco ao longo de uma linha (os intervalos entre elas são múltiplos do pixel); (2) sprite com assinatura do autor: a assinatura sai
como peça solta (r5.largest); (3) o fundo pode ter degradê: use tol=45 no exact6, não thr."""
import sys, os, glob
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def comb(d, lo, hi):
    L = len(d); best = None
    for s in np.arange(lo, hi, 0.02):
        n = int(L / s)
        if n < 4: break
        for o in np.arange(0, s, 0.2):
            ks = np.arange(n)
            on = np.round(o + ks * s).astype(int); mid = np.round(o + (ks + 0.5) * s).astype(int)
            ok = (on < L) & (mid < L)
            sc = d[on[ok]].mean() - d[mid[ok]].mean()
            if best is None or sc > best[0]: best = (sc, s, o)
    return best


def main():
    rem = int(sys.argv[1]); i = int(sys.argv[2]); lo = float(sys.argv[3]) if len(sys.argv) > 3 else 2; hi = float(sys.argv[4]) if len(sys.argv) > 4 else 40
    files = sorted(glob.glob(os.path.join(ROOT, 'remessas', f'remessa {rem}', '*')))
    im = Image.open(files[i]).convert('RGB'); a = np.array(im).astype(float); h, w, _ = a.shape
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]); bgc = np.median(edge, axis=0)
    diff = np.abs(a - bgc).sum(axis=2) > 40
    ys, xs = np.nonzero(diff)
    x0, x1 = np.percentile(xs, [0.3, 99.7]).astype(int); y0, y1 = np.percentile(ys, [0.3, 99.7]).astype(int)
    print(f'{i}: imagem {w}x{h}, fundo {bgc.astype(int).tolist()}, caixa do desenho x {x0}..{x1} y {y0}..{y1} ({x1-x0+1}x{y1-y0+1})')
    sub = a[y0:y1 + 1, x0:x1 + 1].mean(axis=2)
    dx = np.abs(np.diff(sub, axis=1)).sum(axis=0); dy = np.abs(np.diff(sub, axis=0)).sum(axis=1)
    bx = comb(dx, lo, hi); by = comb(dy, lo, hi)
    print(f'  passo x {bx[1]:.2f} (fase {bx[2]:.1f}, score {bx[0]:.0f})   passo y {by[1]:.2f} (fase {by[2]:.1f}, score {by[0]:.0f})')
    print(f'  contas estimadas: {(x1-x0+1)/bx[1]:.1f} x {(y1-y0+1)/by[1]:.1f}')
    ox = x0 + bx[2] + 0.5; oy = y0 + by[2] + 0.5          # uma fronteira de célula (vale módulo o passo)
    print(f'  grade: px=dict(px={bx[1]:.2f}, py={by[1]:.2f}, ox={ox % bx[1]:.2f}, oy={oy % by[1]:.2f}, W={int((w - ox % bx[1]) / bx[1] + 0.5)}, H={int((h - oy % by[1]) / by[1] + 0.5)})   # cobre a imagem toda')


main()
