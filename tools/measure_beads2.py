"""Mede a cor das CONTAS nas 5 fotos SEM TAMPA (paleta 120/foto-contas-sem-tampa-N.jpg, enviadas pelo dono em 2026-11-02 depois de a 1ª leva, com as tampas fechadas, sair com véu azul e reflexo).
Sem a tampa por cima a luz chega direto nas contas; a cor de cada compartimento vale para o código impresso na cartela.
uso:  python tools/measure_beads2.py [N ...] [--out] [--check]    -> imprime a tabela; --check grava tools/out/st_check_N.png (círculos de amostragem sobre a foto); --out grava tools/data/beads_measured2.json
Como funciona:
  * as bandejas são 6 colunas x 4 linhas NA MESMA ORDEM da cartela, mas a ② e a ③ foram fotografadas GIRADAS 180° (a tampa abre para o outro lado): ROT180 inverte a ordem dos códigos;
  * os 4 cantos (ANCHORS: centros dos compartimentos TL, TR, BL, BR, lidos nas fotos) dão os 24 centros por interpolação bilinear (a foto tem uns 2° de giro e pouca perspectiva);
  * em cada compartimento: janela circular de raio RAD; a cor é a mediana da faixa de luminância LO..HI percentis (o piso é furo e sombra entre as contas, o topo é brilho da superfície);
  * a foto NÃO é calibrada (sem referência de cor); balanço de branco pelos adesivos brancos da tampa em wb() é opcional e só olha o MATIZ (não o brilho).
É estimativa de FOTO de celular: o aparelho aplica saturação e contraste próprios."""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

# códigos por bandeja, na ordem da cartela (linha a linha). 1 = 4号, 2 = ②, 3 = ⑤ OLOMI, 4 = ③, 5 = 1号 (mesma numeração de measure_beads.py)
CARDS = {
 1: 'E11 E14 F1 A14 M6 M5  E15 F14 F9 F2 G14 M9  E9 E6 F12 F3 F11 M12  D5 E10 F4 F6 G17 H6',
 2: 'C2 C13 D19 E8 A13 A11  C10 C6 D18 E3 A10 G9  C11 C7 D21 D13 F13 G13  B12 D3 D15 E7 F8 G8',
 3: 'A15 A5 A8 A12 A9 G6  A1 B13 B1 B2 B4 B11  H12 C1 B16 B6 C15 B15  C14 D17 D1 C4 C17 C9',
 4: 'A3 B20 D16 D8 E1 G2  B18 B10 D11 D12 E12 G3  B14 B19 D2 D20 E5 F10  B17 B7 C16 D14 E13 F7',
 5: 'B3 C3 D9 E2 G1 A4  B5 C5 D6 E4 G5 A6  B8 C8 D7 F5 G7 A7  H1 H2 H3 H4 H5 H7',
}
ROT180 = {1: False, 2: True, 3: False, 4: True, 5: False}
# centros dos compartimentos dos 4 cantos (TL, TR, BL, BR) NA FOTO (899x1599), lidos nas fotos
ANCHORS = {
 1: [(152, 748), (730, 723), (160, 1100), (738, 1076)],
 2: [(118, 772), (690, 745), (128, 1110), (695, 1092)],
 3: [(155, 762), (730, 723), (172, 1120), (765, 1080)],
 4: [(98, 662), (718, 638), (112, 1035), (722, 1018)],
 5: [(100, 688), (712, 688), (100, 1060), (715, 1060)],
}
RAD = 38
LO, HI = 50, 85


def path(n): return os.path.join(ROOT, 'paleta 120', 'foto-contas-sem-tampa-%d.jpg' % n)


def centers(n):
    """24 centros (x, y) na ORDEM FÍSICA da foto (esquerda->direita, cima->baixo)"""
    tl, tr, bl, br = [np.array(p, float) for p in ANCHORS[n]]
    return [(1 - c / 5.0) * (1 - r / 3.0) * tl + (c / 5.0) * (1 - r / 3.0) * tr + (1 - c / 5.0) * (r / 3.0) * bl + (c / 5.0) * (r / 3.0) * br for r in range(4) for c in range(6)]


def codes_physical(n):
    """códigos na ordem FÍSICA da foto (invertida nas fotos giradas 180°)"""
    cs = CARDS[n].split()
    return cs[::-1] if ROT180[n] else cs


def window(rgb, c, rad=RAD):
    h, w, _ = rgb.shape
    x0, y0 = max(0, int(c[0] - rad)), max(0, int(c[1] - rad)); x1, y1 = min(w, int(c[0] + rad) + 1), min(h, int(c[1] + rad) + 1)
    sub = rgb[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
    yy, xx = np.mgrid[y0:y1, x0:x1]; inside = ((xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= rad * rad).reshape(-1)
    return sub[inside]


def bead_color(rgb, c, rad=RAD, lo=None, hi=None):
    lo = LO if lo is None else lo; hi = HI if hi is None else hi
    sub = window(rgb, c, rad)
    lum = sub @ np.array([0.299, 0.587, 0.114], np.float32)
    keep = (lum >= np.percentile(lum, lo)) & (lum <= np.percentile(lum, hi))
    return np.median(sub[keep], axis=0)


def measure(n, **kw):
    rgb = np.array(Image.open(path(n)).convert('RGB'))
    return [(code, bead_color(rgb, c, **kw), c) for code, c in zip(codes_physical(n), centers(n))], rgb


def check_image(n, res, rgb):
    im = Image.fromarray(rgb); d = ImageDraw.Draw(im)
    for code, col, c in res:
        d.ellipse([c[0] - RAD, c[1] - RAD, c[0] + RAD, c[1] + RAD], outline=(255, 255, 255), width=2)
        d.rectangle([c[0] - 14, c[1] - 7, c[0] + 14, c[1] + 7], fill=tuple(int(v) for v in col)); d.text((c[0] - 11, c[1] - 6), code, fill=(0, 0, 0))
    a = ANCHORS[n]; xs = [p[0] for p in a]; ys = [p[1] for p in a]
    im.crop((max(0, min(xs) - 110), min(ys) - 110, min(899, max(xs) + 110), max(ys) + 110)).save(os.path.join(OUT, 'st_check_%d.png' % n))


if __name__ == '__main__':
    want = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1, 2, 3, 4, 5]
    allres = {}
    for n in want:
        res, rgb = measure(n)
        print('foto', n, 'giro 180°' if ROT180[n] else '')
        for code, col, c in res: print('   %-4s RGB %-16s centro (%d, %d)' % (code, tuple(int(round(v)) for v in col), c[0], c[1]))
        if '--check' in sys.argv: check_image(n, res, rgb)
        allres[n] = [dict(code=code, rgb=[int(round(v)) for v in col], cx=round(float(c[0])), cy=round(float(c[1]))) for code, col, c in res]
    if '--out' in sys.argv:
        json.dump(allres, open(os.path.join(HERE, 'data', 'beads_measured2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gravado tools/data/beads_measured2.json')
