"""Mede a cor das CONTAS de cada compartimento das 5 bandejas fotografadas (paleta 120/foto-contas-N.jpg, enviadas pelo dono em 2026-11-02, depois de ele dizer que a cor impressa na cartela NÃO é a da conta).
Cada bandeja tem 24 compartimentos (6 colunas x 4 linhas) NA MESMA ORDEM da cartela; o código de cada um é o da cartela.
uso:  python tools/measure_beads.py [N ...] [--out]    -> imprime a tabela, grava tools/out/beads_N.png (centros e janelas) e, com --out, tools/data/beads_measured.json
Como mede: os 4 cantos da bandeja (ANCHORS, lidos nas fotos) dão os 24 centros por interpolação; em cada compartimento a janela central (raio ~40 px) fica só com a faixa de luminância entre os percentis 50 e 92 (a metade escura é furo e sombra entre as contas, o topo é reflexo da tampa) e a cor é a mediana dela. O papel branco da cartela, na mesma foto, dá o balanço de branco (canal x 255/papel) em calibrate_beads.py. É estimativa de FOTO."""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

# códigos por ARQUIVO (a ordem dos anexos): 1 = cartela 4号, 2 = ②, 3 = ⑤ OLOMI, 4 = ③, 5 = 1号. O hexágono verde-escuro da ② impresso "B13" é o B12.
CARDS = {
 1: 'E11 E14 F1 A14 M6 M5  E15 F14 F9 F2 G14 M9  E9 E6 F12 F3 F11 M12  D5 E10 F4 F6 G17 H6',
 2: 'C2 C13 D19 E8 A13 A11  C10 C6 D18 E3 A10 G9  C11 C7 D21 D13 F13 G13  B12 D3 D15 E7 F8 G8',
 3: 'A15 A5 A8 A12 A9 G6  A1 B13 B1 B2 B4 B11  H12 C1 B16 B6 C15 B15  C14 D17 D1 C4 C17 C9',
 4: 'A3 B20 D16 D8 E1 G2  B18 B10 D11 D12 E12 G3  B14 B19 D2 D20 E5 F10  B17 B7 C16 D14 E13 F7',
 5: 'B3 C3 D9 E2 G1 A4  B5 C5 D6 E4 G5 A6  B8 C8 D7 F5 G7 A7  H1 H2 H3 H4 H5 H7',
}
# centros dos 4 compartimentos dos cantos (TL, TR, BL, BR) em cada foto (899x1599), lidos nas fotos
ANCHORS = {
 1: [(95, 468), (788, 462), (82, 895), (782, 900)],
 2: [(102, 416), (790, 412), (90, 838), (790, 840)],
 3: [(82, 460), (780, 458), (80, 880), (780, 882)],
 4: [(128, 448), (768, 445), (122, 868), (770, 870)],
 5: [(118, 530), (815, 525), (112, 972), (815, 975)],
}
# caixa do papel branco da cartela (abaixo da bandeja) em cada foto
PAPER = {1: (275, 1030, 705, 1460), 2: (178, 1020, 792, 1455), 3: (105, 1018, 700, 1500), 4: (125, 1040, 752, 1535), 5: (245, 1090, 675, 1550)}


LO, HI = 50, 92          # faixa de luminância usada: tira os furos e as SOMBRAS entre as contas (a pilha na bandeja é mais escura que a superfície de uma conta fundida) e o reflexo da tampa


def centers(n):
    tl, tr, bl, br = [np.array(p, float) for p in ANCHORS[n]]
    return [(1 - c / 5.0) * (1 - r / 3.0) * tl + (c / 5.0) * (1 - r / 3.0) * tr + (1 - c / 5.0) * (r / 3.0) * bl + (c / 5.0) * (r / 3.0) * br for r in range(4) for c in range(6)]


def bead_color(rgb, c, rad=40):
    h, w, _ = rgb.shape
    x0, y0 = max(0, int(c[0] - rad)), max(0, int(c[1] - rad)); x1, y1 = min(w, int(c[0] + rad)), min(h, int(c[1] + rad))
    sub = rgb[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
    yy, xx = np.mgrid[y0:y1, x0:x1]; inside = ((xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= rad * rad).reshape(-1)
    sub = sub[inside]
    lum = sub @ np.array([0.299, 0.587, 0.114], np.float32)
    keep = (lum >= np.percentile(lum, LO)) & (lum <= np.percentile(lum, HI))
    return np.median(sub[keep], axis=0)


def paper_rgb(rgb, box):
    x0, y0, x1, y1 = box
    sub = rgb[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
    lab = cv2.cvtColor(sub.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    L = lab[:, 0]; chroma = np.hypot(lab[:, 1] - 128, lab[:, 2] - 128)
    sel = (L > np.percentile(L, 75)) & (chroma < 14)
    return np.median(sub[sel], axis=0) if sel.sum() > 200 else np.median(sub[L > np.percentile(L, 85)], axis=0)


def measure(n):
    rgb = np.array(Image.open(os.path.join(ROOT, 'paleta 120', 'foto-contas-%d.jpg' % n)).convert('RGB'))
    codes = CARDS[n].split(); cs = centers(n)
    res = []; im = Image.fromarray(rgb); dr = ImageDraw.Draw(im)
    for code, c in zip(codes, cs):
        col = bead_color(rgb, c)
        res.append(dict(code=code, rgb=[int(round(v)) for v in col], cx=round(float(c[0])), cy=round(float(c[1]))))
        dr.ellipse([c[0] - 40, c[1] - 40, c[0] + 40, c[1] + 40], outline=(255, 255, 255), width=2); dr.text((c[0] - 12, c[1] - 6), code, fill=(255, 255, 255))
    dr.rectangle(PAPER[n], outline=(0, 255, 255), width=3)
    im.save(os.path.join(OUT, 'beads_%d.png' % n))
    return dict(n=n, papel_rgb=[int(round(v)) for v in paper_rgb(rgb, PAPER[n])]), res


if __name__ == '__main__':
    want = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1, 2, 3, 4, 5]
    allres = {}
    for n in want:
        info, res = measure(n)
        print('foto', n, info)
        for r in res: print('   %-4s RGB %-16s centro (%d, %d)' % (r['code'], tuple(r['rgb']), r['cx'], r['cy']))
        allres[n] = dict(info=info, cores=res)
    if '--out' in sys.argv:
        json.dump(allres, open(os.path.join(HERE, 'data', 'beads_measured.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gravado tools/data/beads_measured.json')
