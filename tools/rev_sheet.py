"""Folhas de LEITURA de rosto de VÁRIOS moldes do catálogo numa imagem só (revisão de 2026-10-31, CLAUDE.md §7.20).
Cada painel = recorte da FONTE com a grade das contas do molde | o molde com a mesma grade e números de linha/coluna (como `faces_sheets.py`, mas lê o molde ATUAL do `templates.js`).
uso: python tools/rev_sheet.py TAG [--cell 18] [--big] [--W 1900] "nome|r0,r1,c0,c1" ["nome2|r0,r1,c0,c1" ...]
     (nome = trecho único do nome; região em contas do molde: linhas r0..r1-1, colunas c0..c1-1; sem região = molde inteiro)  ->  tools/out/rev_TAG.png
A fonte vem de `data/rev_src.json` (nome -> [remessa, índice, caixa]; gerado por `tools/rev_src_build.py`); molde sem fonte conhecida sai só com o molde."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw
import facetools as FT
from tplfile import parse
from flat import L2HEX

OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
GEO = os.path.join(HERE, 'data', 'rev_geo.json')


def load_src():
    p = os.path.join(HERE, 'data', 'rev_src.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def mold_panel(rows, region, cell, title):
    r0, r1, c0, c1 = region
    W = (c1 - c0) * cell; Hh = (r1 - r0) * cell
    mol = Image.new('RGB', (W, Hh), (60, 60, 66)); d = ImageDraw.Draw(mol)
    for j in range(r0, r1):
        for i in range(c0, c1):
            ch = rows[j][i] if 0 <= j < len(rows) and 0 <= i < len(rows[0]) else '.'
            x, y = (i - c0) * cell, (j - r0) * cell
            col = ((200, 200, 205) if (i + j) % 2 == 0 else (225, 225, 228)) if ch == '.' else L2HEX[ch]
            d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=col)
    out = Image.new('RGB', (W + 30, Hh + 24), (40, 40, 44)); out.paste(mol, (30, 24))
    dd = ImageDraw.Draw(out); dd.text((30, 2), title, fill=(255, 255, 255))
    for i in range(c1 - c0 + 1):
        x = 30 + i * cell; dd.line((x, 24, x, 24 + Hh), fill=(255, 0, 255) if (c0 + i) % 5 == 0 else (150, 60, 150), width=1)
        if i < c1 - c0 and (c0 + i) % 2 == 0: dd.text((x + 2, 12), str(c0 + i), fill=(255, 255, 0))
    for j in range(r1 - r0 + 1):
        y = 24 + j * cell; dd.line((30, y, 30 + W, y), fill=(255, 0, 255) if (r0 + j) % 5 == 0 else (150, 60, 150), width=1)
        if j < r1 - r0: dd.text((2, y + 2), str(r0 + j), fill=(255, 255, 0))
    return out


def panel(name, rows, region, cell, src):
    """imagem com [fonte com grade | molde com grade]; sem fonte, só o molde"""
    r0, r1, c0, c1 = region
    title = '%s %dx%d' % (name[:44], len(rows[0]), len(rows))
    mol = mold_panel(rows, region, cell, title)
    if not src: return mol
    rem, idx, box = src
    raw = FT.src_raw(rem, idx, tuple(box) if box else None)
    geo = json.load(open(GEO, encoding='utf-8')) if os.path.exists(GEO) else {}
    key = '%s|%dx%d' % (name, len(rows[0]), len(rows))
    if key in geo: g = tuple(geo[key])
    else:
        g = FT.align(raw, rows, verbose=False); geo[key] = list(g)
        json.dump(geo, open(GEO, 'w', encoding='utf-8'))
    tmp = os.path.join(OUT, '_rev_tmp.png')
    FT.sheet(raw, rows, g, region, tmp, cell=cell, title='')
    im = Image.open(tmp).convert('RGB')
    w = im.width // 2
    srcp = im.crop((0, 0, w, im.height))
    comp = Image.new('RGB', (srcp.width + mol.width + 6, max(srcp.height, mol.height)), (40, 40, 44))
    comp.paste(srcp, (0, 0)); comp.paste(mol, (srcp.width + 6, 0))
    ImageDraw.Draw(comp).text((4, 2), title, fill=(255, 255, 255))
    return comp


def main():
    a = sys.argv[1:]
    tag = a[0]; a = a[1:]
    def opt(k, d, cast=int):
        if k in a:
            i = a.index(k); v = cast(a[i + 1]); del a[i:i + 2]; return v
        return d
    cell = opt('--cell', 18); Wmax = opt('--W', 1900)
    big = '--big' in a
    if big: a.remove('--big')
    use_new = '--new' in a
    if use_new: a.remove('--new')
    newrows = json.load(open(os.path.join(HERE, 'data', 'rev_new.json'), encoding='utf-8')) if use_new and os.path.exists(os.path.join(HERE, 'data', 'rev_new.json')) else {}
    cur = parse(os.path.join(ROOT, 'templates.js')); items = cur['items']
    src = load_src()
    panels = []
    for spec in a:
        nm, _, rg = spec.partition('|')
        hit = [t for t in items if nm.lower() in t['name'].lower() and (t['name'].endswith('(grande)') == big)]
        if len(hit) != 1:
            exact = [t for t in hit if t['name'].lower() == nm.lower()]
            if len(exact) == 1: hit = exact
            else: print('AMBÍGUO/NÃO ACHEI "%s": %s' % (nm, [t['name'] for t in hit][:5])); continue
        t = hit[0]; rows = newrows.get(t['name'], t['rows'])
        region = tuple(int(v) for v in rg.split(',')) if rg else (0, len(rows), 0, len(rows[0]))
        region = (max(0, region[0]), min(len(rows), region[1]), max(0, region[2]), min(len(rows[0]), region[3]))
        base = t['name'].replace(' (grande)', '')
        panels.append(panel(t['name'], rows, region, cell, src.get(base)))
    # empacota em linhas
    pad = 8; x = pad; y = pad; rowh = 0; pos = []
    for p in panels:
        if x + p.width + pad > Wmax: x = pad; y += rowh + pad; rowh = 0
        pos.append((x, y)); x += p.width + pad; rowh = max(rowh, p.height)
    sheet = Image.new('RGB', (Wmax, y + rowh + pad), (30, 30, 34))
    for p, (px, py) in zip(panels, pos): sheet.paste(p, (px, py))
    path = os.path.join(OUT, 'rev_%s.png' % tag); sheet.save(path); print(path, sheet.size)


if __name__ == '__main__':
    main()
