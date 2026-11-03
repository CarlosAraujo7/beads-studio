"""Acha a GRADE de um gráfico de contas (passo, fase e extensão) pelas linhas, para gráficos com número/código escrito em cada quadradinho, onde o detector do r6 lê metade do passo.
uso:  python tools/autogrid.py ARQUIVO [--roi x0,y0,x1,y1] [--out ov.png] [--pmin 6] [--pmax 60]
Imprime  px=dict(px=…, py=…, ox=…, oy=…, W=…, H=…)  pronto para colar no E(...). IMPORTANTE: a extensão INCLUI a régua numerada (as linhas passam por ela); a régua é branca e sai como fundo na conversão,
mas confira SEMPRE a sobreposição (--out): a 1ª e a última linha/coluna têm que cair nas linhas do gráfico (CLAUDE.md §7.37: o molde da planta verde perdeu a última coluna por causa disso).
Como funciona: perfil = percentil 65 do |gradiente| de cada coluna (ou linha) na faixa central da imagem; (passo, fase) maximizam a média nas linhas MENOS a média nos pontos médios;
a extensão é a maior sequência de linhas consecutivas com força ≥ 35% da mediana."""
import os, sys, argparse
import numpy as np
from PIL import Image, ImageDraw


def prof(g, axis):
    d = np.abs(np.diff(g, axis=1)) if axis == 'x' else np.abs(np.diff(g, axis=0))
    p = np.percentile(d, 65, axis=0 if axis == 'x' else 1)
    return np.convolve(np.pad(p, 1, mode='edge'), np.ones(3) / 3.0, mode='valid')          # junta as duas bordas de uma linha grossa numa só (sem viés de fase)


def first_period(p, pmin, pmax):
    """menor período FORTE do perfil (autocorrelação): linhas grossas a cada 5 células criam picos em múltiplos, o que vale é o primeiro"""
    q = p - p.mean(); n = len(q)
    f = np.fft.rfft(q, 2 * n); ac = np.fft.irfft(f * np.conj(f))[:n]
    if ac[0] <= 0: return None
    ac = ac / ac[0]
    cand = [l for l in range(max(2, int(pmin)), min(n - 1, int(pmax * 1.2))) if ac[l] > ac[l - 1] and ac[l] >= ac[l + 1] and ac[l] > 0.08]
    if not cand: return None
    mx = max(ac[l] for l in cand)
    for l in cand:
        if ac[l] >= 0.55 * mx:
            a, b, c = ac[l - 1], ac[l], ac[l + 1]
            return l + 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else float(l)
    return None


def fit_axis(p, pmin, pmax):
    """(passo, fase) por pente de bordas; p[i] = força da borda entre i e i+1 (linha em i+1)"""
    n = len(p); xs = np.arange(n) + 1.0
    best = None
    for P in np.arange(pmin, pmax, 0.04):
        ph = np.arange(0, P, 0.5)
        k = np.arange(0, int(n / P) + 2)
        pos = ph[:, None] + P * k[None, :]
        ok = pos < n
        v = np.interp(np.clip(pos, 0, n - 1), xs, p) * ok
        m = np.interp(np.clip(pos + P / 2, 0, n - 1), xs, p) * ok
        cnt = ok.sum(axis=1)
        if cnt.min() < 5: continue
        sc = (v.sum(axis=1) - m.sum(axis=1)) / cnt
        j = int(np.argmax(sc))
        if best is None or sc[j] > best[0]: best = (float(sc[j]), float(P), float(ph[j]))
    return best


def refine(p, P0, ph0):
    """afina o passo e a fase em volta do melhor ponto (passo 0,004 / fase 0,1)"""
    n = len(p); xs = np.arange(n) + 1.0; best = None
    for P in np.arange(P0 - 0.12, P0 + 0.12, 0.004):
        for ph in np.arange(ph0 - 1.5, ph0 + 1.5, 0.1):
            k = np.arange(0, int(n / P) + 2); pos = ph + P * k; pos = pos[(pos >= 0) & (pos < n)]
            if len(pos) < 5: continue
            sc = np.interp(pos, xs, p).mean() - np.interp(np.clip(pos + P / 2, 0, n - 1), xs, p).mean()
            if best is None or sc > best[0]: best = (sc, P, ph)
    return best


def phase_fold(g, axis, P, band, bins=None):
    """fase da linha da grade: perfil de brilho MÉDIO (as cores e o texto das células se anulam ao longo de muitas células; a linha é coerente) dobrado módulo o passo; a saliência (clara ou escura) é a linha"""
    a, b = band
    m = np.abs(np.diff(g[a:b, :], axis=1)).mean(axis=0) if axis == 'x' else np.abs(np.diff(g[:, a:b], axis=0)).mean(axis=1)
    m = np.append(m, m[-1])
    n = len(m); P = float(P)
    nb = bins or max(8, int(round(P * 2)))
    idx = ((np.arange(n) % P) / P * nb).astype(int) % nb
    fold = np.array([m[idx == k].mean() if (idx == k).any() else np.nan for k in range(nb)])
    fold = np.where(np.isnan(fold), np.nanmedian(fold), fold)
    sm = np.convolve(np.pad(fold, 2, mode='wrap'), np.ones(3) / 3.0, mode='valid')[1:-1]
    dev = np.abs(sm - np.median(sm))
    k = int(np.argmax(dev))
    # centro da saliência: média ponderada em volta do pico (a linha tem 1-3 px)
    w = np.arange(k - 2, k + 3); vals = np.array([dev[i % nb] for i in w]); c = float((w * vals).sum() / max(vals.sum(), 1e-9))
    return (c + 0.5) / nb * P % P


def fit_fold(g, axis, P0, band):
    """afina passo E fase juntos: o passo que deixa mais NÍTIDA a saliência da linha no perfil médio dobrado (o passo do pente erra uns 0,5% e a fase sai borrada); devolve (passo, fase)"""
    a, b = band
    m = g[a:b, :].mean(axis=0) if axis == 'x' else g[:, a:b].mean(axis=1)
    n = len(m); best = None
    for P in np.arange(P0 * 0.985, P0 * 1.015, P0 * 0.0004):
        nb = max(8, int(round(P * 2)))
        idx = ((np.arange(n) % P) / P * nb).astype(int) % nb
        cnt = np.bincount(idx, minlength=nb).astype(float); sm = np.bincount(idx, weights=m, minlength=nb)
        fold = np.where(cnt > 0, sm / np.maximum(cnt, 1), np.nan)
        fold = np.where(np.isnan(fold), np.nanmedian(fold), fold)
        sm3 = np.convolve(np.pad(fold, 2, mode='wrap'), np.ones(3) / 3.0, mode='valid')[1:-1]
        dev = np.abs(sm3 - np.median(sm3)); sc = float(dev.max() / (np.median(dev) + 1.0))
        if best is None or sc > best[0]: best = (sc, P)
    P = best[1]
    return P, phase_fold(g, axis, P, band)


def extent(g, axis, P, ph, band):
    """maior sequência de linhas consecutivas com força >= 35% da mediana; devolve (índice da 1ª linha, nº de linhas, posição da 1ª linha)"""
    d = np.abs(np.diff(g, axis=1)) if axis == 'x' else np.abs(np.diff(g, axis=0))
    n = d.shape[1] if axis == 'x' else d.shape[0]
    ks = np.arange(0, int((n - ph) / P) + 1); pos = ph + P * ks
    s = []
    for x in pos:
        i = int(round(x)); i0, i1 = max(0, i - 1), min(n, i + 2)
        a, b = band
        col = d[a:b, i0:i1].max(axis=1) if axis == 'x' else d[i0:i1, a:b].max(axis=0)
        s.append(float(np.median(col)))
    s = np.array(s); thr = 0.35 * np.median(s[s > 0]) if (s > 0).any() else 1
    ok = s >= thr
    best = (0, 0, 0); cur = None
    for i, v in enumerate(ok):
        if v and cur is None: cur = i
        if (not v or i == len(ok) - 1) and cur is not None:
            end = i if v else i - 1
            if end - cur + 1 > best[1]: best = (cur, end - cur + 1, pos[cur])
            cur = None
    return best


def autogrid(path, roi=None, pmin=6, pmax=60):
    im = Image.open(path).convert('RGB'); g = np.array(im.convert('L')).astype(np.float32)
    H_, W_ = g.shape
    if roi: x0, y0, x1, y1 = roi
    else: x0, y0, x1, y1 = int(W_ * 0.15), int(H_ * 0.15), int(W_ * 0.8), int(H_ * 0.8)
    sub = g[y0:y1, x0:x1]
    def axis_fit(p):
        p0 = first_period(p, pmin, pmax)
        return fit_axis(p, p0 * 0.95, p0 * 1.05) if p0 else fit_axis(p, pmin, pmax)
    px_ = axis_fit(prof(sub, 'x')); py_ = axis_fit(prof(sub, 'y'))
    rx = refine(prof(sub, 'x'), px_[1], px_[2]); ry = refine(prof(sub, 'y'), py_[1], py_[2])
    Px, phx = rx[1], rx[2] + x0 - 0.0 + 1.0 - 1.0; Py, phy = ry[1], ry[2] + y0
    # fase global: a primeira linha dentro da imagem inteira
    phx = (phx % Px); phy = (phy % Py)
    band_y = (max(0, y0), min(H_, y1)); band_x = (max(0, x0), min(W_, x1))
    # fase = posição da linha mais próxima da origem; a grade cobre a IMAGEM TODA (régua e legenda viram fundo ou peça pequena na conversão; use post=lg)
    ox = phase_fold(g, 'x', Px, band_y); oy = phase_fold(g, 'y', Py, band_x)
    Wc = int((W_ - ox) / Px + 0.5); Hc = int((H_ - oy) / Py + 0.5)
    return dict(px=round(Px, 3), py=round(Py, 3), ox=round(ox, 2), oy=round(oy, 2), W=Wc, H=Hc, score=(round(px_[0], 1), round(py_[0], 1)), size=(W_, H_))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--roi'); ap.add_argument('--out'); ap.add_argument('--pmin', type=float, default=6); ap.add_argument('--pmax', type=float, default=60)
    a = ap.parse_args()
    roi = tuple(int(v) for v in a.roi.split(',')) if a.roi else None
    r = autogrid(a.file, roi, a.pmin, a.pmax)
    print("px=dict(px=%(px)s, py=%(py)s, ox=%(ox)s, oy=%(oy)s, W=%(W)s, H=%(H)s)   # score x/y %(score)s, imagem %(size)s" % r)
    if a.out:
        im = Image.open(a.file).convert('RGB'); d = ImageDraw.Draw(im)
        for i in range(r['W'] + 1): d.line([(r['ox'] + i * r['px'], r['oy']), (r['ox'] + i * r['px'], r['oy'] + r['H'] * r['py'])], fill=(255, 0, 255), width=1)
        for j in range(r['H'] + 1): d.line([(r['ox'], r['oy'] + j * r['py']), (r['ox'] + r['W'] * r['px'], r['oy'] + j * r['py'])], fill=(255, 0, 255), width=1)
        im.save(a.out); print('sobreposição:', a.out)
