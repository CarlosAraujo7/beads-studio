"""Mede a cor de cada círculo/hexágono das 5 cartelas FOTOGRAFADAS do kit de 120 cores (paleta 120/foto-cartela-N.jpeg, enviadas pelo dono em 2026-11-02).
uso:  python tools/measure_cards.py [N ...] [--out]    -> imprime a tabela (código, RGB medido) e grava tools/out/cards_N.png (detecção) e tools/data/cards_measured.json (com --out)
Como mede: a cartela é uma grade de 4 linhas x 6 colunas; os 4 cantos (ANCHORS, lidos nas fotos) dão os 24 centros por interpolação, cada centro é refinado pela cor e de cada forma sai a cor
DOMINANTE do miolo (a letra impressa e o brilho do plástico são minoria). O balanço de branco pelo papel e a calibração com as 24 cores conhecidas do kit antigo (cartela 1) vêm depois (calibrate_cards.py)."""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

# códigos lidos nas fotos, linha a linha, por ARQUIVO (o WhatsApp salvou fora da ordem dos anexos: 1 = cartela 4号, 2 = ②, 3 = ⑤ OLOMI, 4 = ③, 5 = 1号).
# O hexágono verde-escuro da cartela ② está impresso "B13" mas só pode ser o B12 (o único código que sobra; o B13 de verdade é o verde-limão da cartela ⑤)
CARDS = {
 1: 'E11 E14 F1 A14 M6 M5  E15 F14 F9 F2 G14 M9  E9 E6 F12 F3 F11 M12  D5 E10 F4 F6 G17 H6',
 2: 'C2 C13 D19 E8 A13 A11  C10 C6 D18 E3 A10 G9  C11 C7 D21 D13 F13 G13  B12 D3 D15 E7 F8 G8',
 3: 'A15 A5 A8 A12 A9 G6  A1 B13 B1 B2 B4 B11  H12 C1 B16 B6 C15 B15  C14 D17 D1 C4 C17 C9',
 4: 'A3 B20 D16 D8 E1 G2  B18 B10 D11 D12 E12 G3  B14 B19 D2 D20 E5 F10  B17 B7 C16 D14 E13 F7',
 5: 'B3 C3 D9 E2 G1 A4  B5 C5 D6 E4 G5 A6  B8 C8 D7 F5 G7 A7  H1 H2 H3 H4 H5 H7',
}
# caixa aproximada da cartela em cada foto (x0, y0, x1, y1), olhando as fotos
ROI = {1: (45, 310, 810, 990), 2: (25, 530, 890, 1110), 3: (5, 530, 870, 1170), 4: (5, 550, 855, 1215), 5: (95, 500, 815, 1170)}


# centros dos 4 cantos da grade (TL, TR, BL, BR) em cada foto, lidos olhando as fotos; os outros 20 vêm por interpolação e são refinados pela cor
ANCHORS = {
 1: [(143, 467), (713, 458), (135, 808), (727, 803)],
 2: [(115, 608), (748, 597), (108, 1003), (770, 993)],
 3: [(98, 693), (688, 612), (130, 1030), (748, 940)],
 4: [(135, 632), (783, 667), (100, 995), (770, 1035)],
 5: [(160, 640), (665, 665), (137, 945), (655, 975)],
}


def paper_lab(lab, roi):
    x0, y0, x1, y1 = roi
    sub = lab[y0:y1, x0:x1].reshape(-1, 3)
    L = sub[:, 0]; chroma = np.hypot(sub[:, 1] - 128, sub[:, 2] - 128)
    sel = (L > np.percentile(L, 70)) & (chroma < 14)
    pts = sub[sel] if sel.sum() > 500 else sub[L > np.percentile(L, 80)]
    return np.median(pts, axis=0)


def centers(n):
    (tl, tr, bl, br) = [np.array(p, float) for p in ANCHORS[n]]
    out = []
    for r in range(4):
        for c in range(6):
            u, v = c / 5.0, r / 3.0
            out.append((1 - u) * (1 - v) * tl + u * (1 - v) * tr + (1 - u) * v * bl + u * v * br)
    return out


def region_at(rgb, c, rad=34):
    """máscara de um disco em volta do centro previsto; devolve (máscara da forma, centro refinado): a cor dominante do disco manda e a forma é o componente conexo dessa cor"""
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w]
    disc = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= rad * rad
    col, _ = dominant(rgb, disc, erode=0.0)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    cl = cv2.cvtColor(np.uint8([[col]]), cv2.COLOR_RGB2LAB)[0, 0].astype(np.float32)
    win = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= 70 * 70
    sim = ((np.linalg.norm(lab - cl, axis=2) < 16) & win).astype(np.uint8)
    sim = cv2.morphologyEx(sim, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))          # fecha a letra
    k, lb, st, cen = cv2.connectedComponentsWithStats(sim, connectivity=8)
    if k <= 1: return disc, c
    i = 1 + int(np.argmax(st[1:, 4]))
    return lb == i, np.array(cen[i], float)


def dominant(rgb, mask, erode=0.30):
    """cor dominante do miolo da forma: erosão para fugir do contorno em relevo, depois o grupo maior de 2 (a letra e o brilho são a minoria)"""
    ys, xs = np.nonzero(mask)
    r = int(erode * min(np.ptp(xs), np.ptp(ys)) / 2)
    mm = cv2.erode(mask.astype(np.uint8), np.ones((2 * max(r, 1) + 1, 2 * max(r, 1) + 1), np.uint8)).astype(bool)
    px_ = rgb[mm].astype(np.float32)
    if len(px_) < 50: return rgb[mask].mean(axis=0), 0.0
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, lab_, cen = cv2.kmeans(px_, 2, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    big = int(np.argmax(np.bincount(lab_.ravel(), minlength=2)))
    sel = px_[lab_.ravel() == big]
    return np.median(sel, axis=0), float((lab_.ravel() == big).mean())


def measure(n):
    rgb = np.array(Image.open(os.path.join(ROOT, 'paleta 120', 'foto-cartela-%d.jpeg' % n)).convert('RGB'))
    codes = CARDS[n].split()
    res = []; im = Image.fromarray(rgb); dr = ImageDraw.Draw(im)
    for code, c in zip(codes, centers(n)):
        shape, cc = region_at(rgb, c)
        col, frac = dominant(rgb, shape, erode=0.35)
        res.append(dict(code=code, rgb=[int(round(v)) for v in col], frac=round(frac, 2), cx=round(float(cc[0])), cy=round(float(cc[1])), area=int(shape.sum())))
        dr.ellipse([cc[0] - 6, cc[1] - 6, cc[0] + 6, cc[1] + 6], outline=(255, 0, 255), width=3)
        dr.ellipse([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3], outline=(0, 255, 255), width=2)
        dr.text((cc[0] - 12, cc[1] + 30), code, fill=(255, 0, 255))
    # papel (para o balanço de branco): plano linear por canal ajustado nos pixels de papel da região da cartela (a luz não é uniforme); no papel de cada forma = o ganho local
    x0, y0, x1, y1 = ROI[n]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32); pl = paper_lab(lab, ROI[n])
    dd = np.linalg.norm(lab - pl, axis=2); pm = np.zeros(dd.shape, bool); pm[y0:y1, x0:x1] = dd[y0:y1, x0:x1] < 5
    ys_, xs_ = np.nonzero(pm)
    plane = None
    if len(xs_) > 500:
        sel = np.random.RandomState(0).choice(len(xs_), min(len(xs_), 40000), replace=False)
        A = np.stack([np.ones(len(sel)), xs_[sel] / 900.0, ys_[sel] / 1600.0], axis=1)
        plane = [np.linalg.lstsq(A, rgb[ys_[sel], xs_[sel], ch].astype(float), rcond=None)[0] for ch in range(3)]
        for r_ in res:
            r_['papel_local'] = [int(round(float(plane[ch] @ np.array([1.0, r_['cx'] / 900.0, r_['cy'] / 1600.0])))) for ch in range(3)]
    info = dict(n=n, papel_lab=[round(float(v), 1) for v in pl], papel_rgb=[int(round(v)) for v in np.median(rgb[pm], axis=0)] if pm.sum() > 200 else None,
                areas=sorted(r_['area'] for r_ in res)[:3] + sorted(r_['area'] for r_ in res)[-2:])
    im.save(os.path.join(OUT, 'cards_%d.png' % n))
    return info, res


if __name__ == '__main__':
    want = [int(a) for a in sys.argv[1:] if a.isdigit()] or [1, 2, 3, 4, 5]
    allres = {}
    for n in want:
        info, res = measure(n)
        print('foto', n, info)
        for r_ in res: print('   %-4s RGB %-16s dominante %.2f  centro (%d, %d)' % (r_['code'], tuple(r_['rgb']), r_['frac'], r_['cx'], r_['cy']))
        allres[n] = dict(info=info, cores=res)
    if '--out' in sys.argv:
        json.dump(allres, open(os.path.join(HERE, 'data', 'cards_measured.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gravado tools/data/cards_measured.json')
