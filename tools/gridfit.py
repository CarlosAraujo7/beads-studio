"""Ajusta a GRADE de um gráfico de contas (passo, fase) por pente de bordas, para forçar `px=dict(px, py, ox, oy, W, H)` no r6.exact6 quando o detector automático lê o passo
pela metade (código escrito dentro de cada célula, marca d'água, JPEG ruidoso) e o gridlines.py não serve.

uso:  python tools/gridfit.py ARQUIVO W H [--box x0,y0,x1,y1] [--out sobreposicao.png]
  W, H = nº de colunas e linhas da grade (leia os números impressos nas bordas do gráfico).
  --box = caixa aproximada da grade em pixels (recomendado: passo fica a ±6% de (x1-x0)/W e a fase perto de x0/y0). Sem --box procura na faixa central da imagem inteira.
  --out = grava a imagem ampliada 2x com a grade (magenta) por cima: CONFIRA OLHANDO que as linhas caem nas linhas do gráfico.
Saída: px=dict(...) pronto para colar. A fase só vale módulo o passo (use ox % px); para cobrir a imagem toda calcule W = int((largura - ox)/px + 0.5).
Como funciona: perfil = percentil 65 do |gradiente| ao longo do outro eixo (texto dentro das células ocupa poucas linhas; a linha da grade atravessa todas); o (passo, fase)
escolhido maximiza a média do perfil nas linhas MENOS a média nos pontos médios (assim o dobro e a metade do passo perdem). Em gráficos pixiecraft acertou todos; em cross-stitch
(linhas finas, vinheta) o score fica muito baixo (5-8) e não é confiável: meça as linhas grossas/finas à mão (veja CLAUDE.md §7.17)."""
import sys, argparse
import numpy as np
from PIL import Image, ImageDraw


def prof(g, axis, box):
    x0, y0, x1, y1 = box
    sub = g[y0:y1, x0:x1]
    if axis == 'x': return np.percentile(np.abs(np.diff(sub, axis=1)), 65, axis=0), x0
    return np.percentile(np.abs(np.diff(sub, axis=0)), 65, axis=1), y0


def fit(d, base, lo, hi, n, rng, direct=False):
    sm = np.convolve(d, [0.25, 0.5, 0.25], mode='same'); L = len(d)
    ks = np.arange(n + 1); best = None
    for s in np.arange(lo, hi, 0.02):
        for o in np.arange(rng[0], (rng[1] if direct else rng[1] - n * s) + 0.001, 0.15):
            on = np.round(o + ks * s - 0.5 - base).astype(int)
            if on.min() < 0 or on.max() >= L: continue
            mid = np.round(o + (ks[:-1] + 0.5) * s - 0.5 - base).astype(int)
            sc = sm[on].mean() - sm[mid].mean()
            if best is None or sc > best[0]: best = (sc, s, o)
    return best


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('arq'); ap.add_argument('W', type=int); ap.add_argument('H', type=int)
    ap.add_argument('--box'); ap.add_argument('--out'); a = ap.parse_args()
    g = np.array(Image.open(a.arq).convert('L'), dtype=float); h, w = g.shape
    if a.box:
        x0, y0, x1, y1 = [int(float(v)) for v in a.box.split(',')]; pad = 10
        dx, bx = prof(g, 'x', (max(0, x0 - pad), y0, min(w, x1 + pad), y1)); dy, by = prof(g, 'y', (x0, max(0, y0 - pad), x1, min(h, y1 + pad)))
        ex, ey = (x1 - x0) / a.W, (y1 - y0) / a.H
        sx = fit(dx, bx, ex * 0.94, ex * 1.06, a.W, (bx - ex * 0.6, bx + ex * 0.6), True); sy = fit(dy, by, ey * 0.94, ey * 1.06, a.H, (by - ey * 0.6, by + ey * 0.6), True)
    else:
        dx, bx = prof(g, 'x', (0, int(h * 0.15), w, int(h * 0.85))); dy, by = prof(g, 'y', (int(w * 0.15), 0, int(w * 0.85), h))
        sx = fit(dx, bx, 0.75 * w / (a.W + 2), 1.02 * w / a.W, a.W, (0, w)); sy = fit(dy, by, 0.75 * h / (a.H + 2), 1.02 * h / a.H, a.H, (0, h))
    print(f'px={sx[1]:.2f} ox={sx[2]:.2f} (score {sx[0]:.0f})   py={sy[1]:.2f} oy={sy[2]:.2f} (score {sy[0]:.0f})   W={a.W} H={a.H}   img={w}x{h}')
    print(f'px=dict(px={sx[1]:.2f}, py={sy[1]:.2f}, ox={sx[2]:.2f}, oy={sy[2]:.2f}, W={a.W}, H={a.H})')
    if a.out:
        im = Image.open(a.arq).convert('RGB').resize((w * 2, h * 2), Image.LANCZOS); dr = ImageDraw.Draw(im)
        for k in range(a.W + 1):
            xx = (sx[2] + k * sx[1] + 0.5) * 2; dr.line([(xx, 0), (xx, h * 2)], fill=(255, 0, 255), width=1)
        for k in range(a.H + 1):
            yy = (sy[2] + k * sy[1] + 0.5) * 2; dr.line([(0, yy), (w * 2, yy)], fill=(255, 0, 255), width=1)
        im.save(a.out)


main()
