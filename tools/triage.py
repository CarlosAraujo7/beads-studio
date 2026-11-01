"""Folha de triagem: para cada imagem de uma remessa mostra  [imagem original | conversão automática fiel | molde mais parecido do catálogo + nota].
Serve para decidir, olhando, se a imagem JÁ está no catálogo (nota alta e mesmo desenho) ou se falta.

uso (na raiz do projeto):  python tools/triage.py N [inicio fim] [--por-folha 18]
     -> tools/out/triage_N_<k>.png      (o número na miniatura é o índice da imagem na pasta)
"""
import os, sys, glob, json
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
N = int(sys.argv[1]); os.environ['REMNUM'] = str(N)
import numpy as np
from PIL import Image, ImageDraw
import r6, tplfile, layoutsim as L
ROOT = os.path.dirname(SP)
cat = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
files = sorted(f for f in glob.glob(os.path.join(ROOT, 'remessas', f'remessa {N}', '*')) if os.path.isfile(f))
a = [int(x) for x in sys.argv[2:4] if x.isdigit()]
lo, hi = (a[0], a[1]) if len(a) == 2 else (0, len(files))
PER = 18
T = 150
HEX = {k: '#' + v for k, v in L._HEX.items()}


def render(rows, size=T):
    img = Image.new('RGB', (size, size), (64, 64, 70))
    if not rows: return img
    h, w = len(rows), max(len(r) for r in rows)
    cs = max(1, size // max(h, w)); d = ImageDraw.Draw(img)
    ox = (size - w * cs) // 2; oy = (size - h * cs) // 2
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in HEX:
                if cs >= 4: d.ellipse([ox + x * cs, oy + y * cs, ox + (x + 1) * cs - 1, oy + (y + 1) * cs - 1], fill=HEX[c])
                else: d.rectangle([ox + x * cs, oy + y * cs, ox + (x + 1) * cs - 1, oy + (y + 1) * cs - 1], fill=HEX[c])
    return img


def src(path):
    try:
        im = Image.open(path).convert('RGB'); im.thumbnail((T, T)); bg = Image.new('RGB', (T, T), (64, 64, 70))
        bg.paste(im, ((T - im.width) // 2, (T - im.height) // 2)); return bg
    except Exception:
        return Image.new('RGB', (T, T), (90, 30, 30))


results = []
tiles = []
for i in range(lo, hi):
    try:
        rows = r6.exact6(i)
    except Exception as e:
        rows = []
    if rows and len(rows) * len(rows[0]) < 6: rows = []
    top = L.best(rows, cat, 1)[0] if rows else (0.0, '-')
    tmpl = next((t for t in cat if t['name'] == top[1]), None)
    results.append({'idx': i, 'arquivo': os.path.basename(files[i]), 'nota': round(top[0], 2), 'parecido': top[1], 'tam': (len(rows[0]), len(rows)) if rows else None})
    tiles.append((i, src(files[i]), render(rows), render(tmpl['rows']) if tmpl else Image.new('RGB', (T, T), (64, 64, 70)), top))
    print(i, results[-1]['tam'], top[0].__round__(2), top[1][:30], flush=True)
cols, rws = 3, 6
for k in range(0, len(tiles), PER):
    chunk = tiles[k:k + PER]
    W = cols * (3 * T + 14) + 10; H = ((len(chunk) + cols - 1) // cols) * (T + 22) + 10
    sheet = Image.new('RGB', (W, H), (30, 30, 34)); d = ImageDraw.Draw(sheet)
    for j, (i, s, c, m, top) in enumerate(chunk):
        x = 10 + (j % cols) * (3 * T + 14); y = 10 + (j // cols) * (T + 22)
        sheet.paste(s, (x, y + 18)); sheet.paste(c, (x + T + 2, y + 18)); sheet.paste(m, (x + 2 * T + 4, y + 18))
        col = (120, 255, 120) if top[0] >= 0.85 else ((255, 230, 90) if top[0] >= 0.72 else (255, 120, 120))
        d.text((x, y + 2), f'#{i}', fill=(255, 255, 0)); d.text((x + T + 2, y + 2), 'conversão', fill=(180, 180, 180))
        d.text((x + 2 * T + 4, y + 2), f'{top[0]:.2f} {top[1][:22]}', fill=col)
    sheet.save(os.path.join(SP, 'out', f'triage_{N}_{k // PER}.png'))
json.dump(results, open(os.path.join(SP, 'out', f'triage_{N}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
