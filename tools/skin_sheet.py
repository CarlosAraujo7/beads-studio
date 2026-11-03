"""FOLHAS DE ROSTOS (2026-11-03): recorta o ROSTO de cada molde (a maior região de pele pela cor ANTIGA da letra) e põe lado a lado ANTES (paleta antiga) | AGORA (cores de hoje) | PROPOSTA (mapa dado),
para o dono conferir a cor de pele de cada personagem. SÓ LÊ o catálogo; grava só imagens em tools/out/.
uso:  python tools/skin_sheet.py ids.txt|--all [--map arquivo.json] [--out prefixo] [--per 28] [--scale 5]
Importado por skin_align.py (`face_box`, `render_row`)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import remap_cores as RC, palette_tone as PT, tplfile
import skin_scan as SS

OLDP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.OLD}
NEWP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.NEW}
F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 11)
BG = (236, 236, 236)


def skin_comp(rows, min_area=14):
    """a maior região (8 vizinhos) de contas de pele clara (cor antiga) do molde: devolve (caixa y0,y1,x0,x1, área) ou None"""
    h, w = len(rows), len(rows[0]); g = np.array([list(r) for r in rows])
    m = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            c = g[y, x]
            if c != '.' and SS._SK.get(c): m[y, x] = True
    best = None
    for cells in SS.comps(m, 8):
        if len(cells) >= min_area and (best is None or len(cells) > best[1]): best = (cells, len(cells))
    if best is None: return None
    ys = [c[0] for c in best[0]]; xs = [c[1] for c in best[0]]
    return (min(ys), max(ys), min(xs), max(xs), best[1])


def face_box(rows, pad=3, maxside=30):
    sc = skin_comp(rows)
    if sc is None: return None
    y0, y1, x0, x1, a = sc; h, w = len(rows), len(rows[0])
    y0 = max(0, y0 - pad); y1 = min(h - 1, y1 + pad); x0 = max(0, x0 - pad); x1 = min(w - 1, x1 + pad)
    if y1 - y0 + 1 > maxside: c = (y0 + y1) // 2; y0 = max(0, c - maxside // 2); y1 = min(h - 1, y0 + maxside - 1)
    if x1 - x0 + 1 > maxside: c = (x0 + x1) // 2; x0 = max(0, c - maxside // 2); x1 = min(w - 1, x0 + maxside - 1)
    return y0, y1, x0, x1


def crop(rows, box):
    y0, y1, x0, x1 = box
    return [r[x0:x1 + 1] for r in rows[y0:y1 + 1]]


def render_row(rows, mapping, scale=5, box=None):
    """devolve (antes, agora, proposta) como imagens do mesmo recorte"""
    box = box or face_box(rows)
    if box is None: box = (0, len(rows) - 1, 0, len(rows[0]) - 1)
    cr = crop(rows, box); new = [''.join(mapping.get(c, c) if c != '.' else '.' for c in r) for r in cr]
    return RC.draw(cr, OLDP, scale, BG), RC.draw(cr, NEWP, scale, BG), RC.draw(new, NEWP, scale, BG)


def sheet(items, mapping_of, out, per=28, scale=5, cols=4, title=''):
    d = tplfile.parse(os.path.join(ROOT, 'templates.js')); by = {t['id']: t for t in d['items']}
    pages = [items[i:i + per] for i in range(0, len(items), per)]
    for pi, page in enumerate(pages):
        tiles = []
        for iid in page:
            t = by[iid]; a, b, c = render_row(t['rows'], mapping_of(t))
            tiles.append((t['name'], a, b, c))
        cw = max(x[1].width * 3 + 30 for x in tiles) + 10; ch = max(x[1].height for x in tiles) + 22
        rows_n = (len(tiles) + cols - 1) // cols
        im = Image.new('RGB', (cols * cw, rows_n * ch + 20), (250, 248, 244)); dr = ImageDraw.Draw(im)
        dr.text((4, 3), (title or 'ANTES | AGORA | PROPOSTA') + '   (pág. %d de %d)' % (pi + 1, len(pages)), fill=(20, 20, 20), font=F)
        for k, (nm, a, b, c) in enumerate(tiles):
            X = (k % cols) * cw; Y = 20 + (k // cols) * ch
            dr.text((X + 3, Y + 1), nm[:48], fill=(20, 20, 20), font=F)
            im.paste(a, (X + 3, Y + 16)); im.paste(b, (X + 3 + a.width + 8, Y + 16)); im.paste(c, (X + 3 + a.width * 2 + 16, Y + 16))
        im.save('%s_%d.png' % (out, pi)); print('%s_%d.png' % (out, pi), im.size, len(tiles), 'moldes')


if __name__ == '__main__':
    a = sys.argv[1:]
    d = tplfile.parse(os.path.join(ROOT, 'templates.js'))
    if '--all' in a:
        ids = [t['id'] for t in d['items'] if skin_comp(t['rows'])]
    else:
        ids = [l.strip() for l in open(a[0], encoding='utf-8') if l.strip()]
    mp = json.load(open(a[a.index('--map') + 1], encoding='utf-8')) if '--map' in a else {}
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(HERE, 'out', 'skin_sheet')
    per = int(a[a.index('--per') + 1]) if '--per' in a else 28
    sc = int(a[a.index('--scale') + 1]) if '--scale' in a else 5
    sheet(ids, lambda t: mp.get(t['id'], {}), out, per=per, scale=sc)
