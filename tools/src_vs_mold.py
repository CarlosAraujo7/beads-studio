"""CONFERE UM MOLDE COM A IMAGEM ORIGINAL (2026-11-03): folha  IMAGEM ORIGINAL | ANTES (paleta antiga) | AGORA (cores de hoje) [| PROPOSTA].
SÓ LÊ (nada é gravado no catálogo). A imagem original é a de `remessas/remessa N` na posição IDX (lista ordenada por nome, igual ao resto do pipeline).
uso:  python tools/src_vs_mold.py REM IDX id-do-molde [--box x0,y0,x1,y1] [--out arq.png] [--H 520] [--v4]
      (--box recorta a imagem original; --v4 acrescenta a proposta de remap_cores.remap4 do próprio molde)"""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import remap_cores as RC, palette_tone as PT, tplfile

OLDP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.OLD}
NEWP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.NEW}
F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)


def source(rem, idx, box=None):
    files = sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa %s' % rem, '*.*')))
    im = Image.open(files[idx]).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    return im.crop(box) if box else im


def main():
    a = [x for x in sys.argv[1:]]
    rem, idx, iid = a[0], int(a[1]), a[2]
    box = tuple(int(v) for v in a[a.index('--box') + 1].split(',')) if '--box' in a else None
    H = int(a[a.index('--H') + 1]) if '--H' in a else 480
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(HERE, 'out', 'svm_%s.png' % iid[:40])
    d = tplfile.parse(os.path.join(ROOT, 'templates.js')); it = next(t for t in d['items'] if t['id'] == iid); rows = it['rows']
    sc = max(2, H // max(len(rows), len(rows[0])))
    tiles = [('IMAGEM ORIGINAL', None)]
    tiles.append(('ANTES (paleta antiga)', RC.draw(rows, OLDP, sc, (236, 236, 236))))
    tiles.append(('AGORA (catálogo)', RC.draw(rows, NEWP, sc, (236, 236, 236))))
    if '--v4' in a:
        m = RC.remap4(rows); nr = [''.join(m.get(c, c) if c != '.' else '.' for c in r) for r in rows]
        tiles.append(('PROPOSTA v4', RC.draw(nr, NEWP, sc, (236, 236, 236))))
    src = source(rem, idx, box); r = H / src.height; src = src.resize((max(1, int(src.width * r)), H), Image.LANCZOS); tiles[0] = ('IMAGEM ORIGINAL', src)
    W = sum(t[1].width for t in tiles) + 20 * (len(tiles) + 1); HH = max(t[1].height for t in tiles) + 40
    sh = Image.new('RGB', (W, HH), (250, 248, 244)); dr = ImageDraw.Draw(sh); x = 20
    for nm, im in tiles:
        dr.text((x, 6), nm, fill=(20, 20, 20), font=F); sh.paste(im, (x, 26)); x += im.width + 20
    sh.save(out); print(out, sh.size, '| molde', len(rows[0]), 'x', len(rows), '| escala', sc)


if __name__ == '__main__':
    main()
