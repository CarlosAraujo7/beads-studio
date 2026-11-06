"""Acha as CAIXAS (em pixels) das figuras de uma folha da remessa 31 (peças ligadas do que não é fundo):
    python tools/r31_boxes.py IDX [--thr 240] [--join 14] [--min 0.002] [--flat r,g,b,tol] [--pad 4]
grava tools/out/abox31_IDX.png (a folha com as caixas numeradas, ampliada para caber em ~1600 px) e imprime as caixas na ordem de leitura (linhas de cima para baixo, esquerda para a direita).
--thr N: o fundo é o "claro ligado à borda" (mín. dos canais >= N); --flat r,g,b,tol: fundo de uma cor; --join N: junta pedaços a até N px (mão, vassoura, sombra);
--min F: peças menores que F da área da imagem são ignoradas (assinatura, marca d'água). Confira SEMPRE olhando a imagem gerada: a caixa de uma figura pode pegar um pedaço da vizinha."""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw
import illus

F = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa 31', '*.*')))


def boxes(idx, thr=240, join=14, min_area=0.002, flat=None, pad=4):
    rgb = illus._load(F[idx])
    if flat: m = illus.flat_bg(rgb, [tuple(flat[:3])], flat[3])
    else: m = illus.background(rgb, thr)
    fg = (~m).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * join + 1, 2 * join + 1))
    comp = cv2.dilate(fg, k)
    n, lab = cv2.connectedComponents(comp, connectivity=8)
    out = []
    for i in range(1, n):
        mm = (lab == i) & (fg > 0)
        if mm.sum() < min_area * fg.size: continue
        ys, xs = np.nonzero(mm)
        out.append((max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad), min(rgb.shape[1], int(xs.max()) + 1 + pad), min(rgb.shape[0], int(ys.max()) + 1 + pad), int(mm.sum())))
    hmed = np.median([b[3] - b[1] for b in out]) if out else 1
    out.sort(key=lambda b: (round(((b[1] + b[3]) / 2) / max(1.0, hmed * 0.9)), b[0]))
    return rgb, out


if __name__ == '__main__':
    argv = sys.argv[1:]
    idx = int(argv[0]); opt = {}
    k = 1
    while k < len(argv):
        a = argv[k]
        if a == '--thr': opt['thr'] = int(argv[k + 1]); k += 2
        elif a == '--join': opt['join'] = int(argv[k + 1]); k += 2
        elif a == '--min': opt['min_area'] = float(argv[k + 1]); k += 2
        elif a == '--pad': opt['pad'] = int(argv[k + 1]); k += 2
        elif a == '--flat': opt['flat'] = [int(v) for v in argv[k + 1].split(',')]; k += 2
        else: k += 1
    rgb, bx = boxes(idx, **opt)
    print(f'{len(bx)} figuras em {os.path.basename(F[idx])} ({rgb.shape[1]}x{rgb.shape[0]})')
    sc = min(1.0, 1600.0 / max(rgb.shape[:2]))
    im = Image.fromarray(rgb).resize((int(rgb.shape[1] * sc), int(rgb.shape[0] * sc)), Image.LANCZOS); d = ImageDraw.Draw(im)
    for j, (x0, y0, x1, y1, a) in enumerate(bx):
        d.rectangle((x0 * sc, y0 * sc, x1 * sc, y1 * sc), outline=(255, 0, 255), width=2); d.text((x0 * sc + 3, y0 * sc + 3), str(j), fill=(255, 0, 0))
        print(f'  {j}: ({x0}, {y0}, {x1}, {y1})   {x1 - x0}x{y1 - y0}  área {a}')
    out = os.path.join(HERE, 'out', f'abox31_{idx}.png'); im.save(out); print('->', out)
