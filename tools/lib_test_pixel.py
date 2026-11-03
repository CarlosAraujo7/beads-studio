"""TESTE (2026-11-02, pedido do dono: "teste com novas bibliotecas") das bibliotecas `proper-pixel-art` (2.0.0) e `perfect-pixel` (0.1.4) contra a conversão que eu já tenho, em imagens da remessa 28.
Roda no venv ISOLADO do scratchpad (libenv; o Python do sistema não foi tocado):   libenv/Scripts/python.exe tools/lib_test_pixel.py IDX [IDX ...]
Para cada imagem: tamanho que cada biblioteca achou x o tamanho certo da conversão atual (tools/data/final30_120.json, quando existe), e uma folha FONTE | conversão atual | proper-pixel-art | perfect-pixel
com as cores trocadas pela conta mais próxima da paleta de 120 (ΔE2000 pelo nearest_letter do pipeline, só para comparar em cores de contas). NÃO grava nada no catálogo."""
import os, sys, json, glob, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

PAL = json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']
HEXES = [tuple(int(c['hex'][i:i + 2], 16) for i in (1, 3, 5)) for c in PAL]


def lab_arr(rgb):
    a = np.asarray(rgb, np.float32).reshape(-1, 1, 3) / 255.0
    return cv2.cvtColor(a, cv2.COLOR_RGB2LAB).reshape(-1, 3)


PAL_LAB = lab_arr(HEXES)


def to_beads(img, alpha_thr=128):
    """cada pixel -> conta mais próxima (Lab euclidiano; só para o teste); fundo transparente/branco ligado à borda -> vazio"""
    im = img.convert('RGBA'); a = np.array(im); rgb = a[..., :3]; al = a[..., 3]
    h, w = al.shape; lab = lab_arr(rgb.reshape(-1, 3)).reshape(h, w, 3)
    d = ((lab[:, :, None, :] - PAL_LAB[None, None, :, :]) ** 2).sum(-1); idx = d.argmin(-1)
    out = np.zeros((h, w, 3), np.uint8); out[:] = (236, 236, 236)
    for y in range(h):
        for x in range(w):
            if al[y, x] >= alpha_thr: out[y, x] = HEXES[idx[y, x]]
    return Image.fromarray(out)


def white_bg_to_alpha(im, thr=244):
    """tira o branco ligado à borda (a conversão atual também tira o fundo claro ligado à borda)"""
    a = np.array(im.convert('RGB')); h, w, _ = a.shape; mask = (a.min(axis=2) >= thr).astype(np.uint8)
    flood = np.zeros((h + 2, w + 2), np.uint8); m = mask.copy()
    seen = np.zeros((h, w), bool); st = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for x in range(w) for y in (0, h - 1)]
    while st:
        y, x = st.pop()
        if 0 <= y < h and 0 <= x < w and not seen[y, x] and mask[y, x]:
            seen[y, x] = True; st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    al = np.where(seen, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, al]), 'RGBA')


def run_proper(src):
    from proper_pixel_art import pixelate
    t0 = time.time(); r = pixelate(src.convert('RGB')); return r.image, time.time() - t0, getattr(r, 'pixel_width', None)


def run_perfect(src):
    from perfect_pixel import get_perfect_pixel
    t0 = time.time(); w, h, out = get_perfect_pixel(np.array(src.convert('RGB')), sample_method='majority'); return Image.fromarray(np.asarray(out).astype(np.uint8)), time.time() - t0, (w, h)


def main():
    idxs = [int(a) for a in sys.argv[1:] if a.isdigit()]
    files = sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa 28', '*.*')))
    cur = {}
    try:
        for it in json.load(open(os.path.join(HERE, 'data', 'final30_120.json'), encoding='utf-8')): cur[it[0]] = it[2]
    except Exception: pass
    F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 11); Fb = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 12)
    sheets = []
    for i in idxs:
        src = Image.open(files[i]).convert('RGBA'); bg = Image.new('RGBA', src.size, (255, 255, 255, 255)); bg.alpha_composite(src); src = bg.convert('RGB')
        row = [('fonte %dx%d' % src.size, src.resize((min(260, src.width), int(src.height * min(260, src.width) / src.width)), Image.LANCZOS))]
        for name, fn in (('proper-pixel-art', run_proper), ('perfect-pixel', run_perfect)):
            try:
                out, dt, info = fn(src)
                out = white_bg_to_alpha(out)
                beads = to_beads(out)
                S = max(2, int(300 / max(beads.size))); row.append(('%s: %dx%d (%.1fs) %s' % (name, beads.width, beads.height, dt, info if info else ''), beads.resize((beads.width * S, beads.height * S), Image.NEAREST)))
                print('idx %d %-17s -> %dx%d em %.1f s' % (i, name, beads.width, beads.height, dt))
            except Exception as e:
                print('idx %d %-17s ERRO %r' % (i, name, e)); row.append((name + ': ERRO ' + repr(e)[:50], Image.new('RGB', (120, 40), (255, 200, 200))))
        sheets.append((i, row))
    cw = max(sum(im.width for _, im in row) + 14 * len(row) for _, row in sheets); H = sum(max(im.height for _, im in row) + 26 for _, row in sheets)
    sh = Image.new('RGB', (cw, H), (250, 248, 244)); d = ImageDraw.Draw(sh); y = 0
    for i, row in sheets:
        x = 6
        for lab, im in row:
            d.text((x, y + 4), '[%d] %s' % (i, lab), fill=(20, 20, 20), font=F); sh.paste(im, (x, y + 22)); x += im.width + 14
        y += max(im.height for _, im in row) + 26
    out = os.path.join(HERE, 'out', 'lib_test_pixel.png'); sh.save(out); print('folha:', out, sh.size)


if __name__ == '__main__':
    main()
