"""Folha de ROSTOS da remessa 31 com a ARTE ALINHADA (lê data/final33_raw_120.json e tools/out/r31_geom/*.npz que o r31_exfinal.py grava; não reconverte).
Para cada molde com rosto: a arte recortada exatamente nas contas do molde (com a grade e a régua de linha/coluna) | o molde com o código de cada conta | o molde a 50% sobre a arte.
    python tools/r31_faces2.py [trecho do nome ...] [--px 18] [--per 6] [--tag nome] [--all] [--rows 0,28]
Por padrão só os moldes com "chibi" ou "desenho" no nome (--all = todos); o recorte é o terço de cima do molde, ou o das linhas dadas em --rows a,b (a inclusive, b exclusivo) para olhar mais embaixo.
Também lista os moldes com a conta H1 (transparente) perto do rosto: H1 no branco do olho ou em rosto branco é erro (usar H2). Saída: tools/out/r31f2_<tag>_N.png"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import r31_exfinal as X
import r31_eyes as EY
from palette import ALL

HEX = {c['letter']: c['hex'] for c in ALL}; CODE = {c['letter']: c['code'] for c in ALL}
H1 = next(c['letter'] for c in ALL if c['code'] == 'H1')
try:
    FNT = ImageFont.truetype('arial.ttf', 8); FB = ImageFont.truetype('arialbd.ttf', 12)
except Exception:
    FNT = FB = ImageFont.load_default()


def art_crop(G, rows, r0, r1, c0, c1, px):
    """a arte nas contas (linhas r0..r1-1, colunas c0..c1-1) do molde final, ampliada para px por conta"""
    dy, dx, sc = EY.offset(G['rows'], rows)
    cw, ch = G['w'] / G['nw'], G['h'] / G['nh']
    def pix(r, c): return G['x0'] + (c + dx + G['left'] - 1) * cw, G['y0'] + (r + dy + G['top'] - 1) * ch
    xa, ya = pix(r0, c0); xb, yb = pix(r1, c1)
    # a imagem original (já com a caixa e a rotação do conversor) = G['raw'] recortada em (x0, y0): G['raw'] é a região da figura; as coordenadas acima são relativas à imagem recortada pela caixa
    full = X.R.illus._load(X.F[G['idx']], G['box'] if G['box'][0] >= 0 else None) if not G.get('rotate') else np.array(Image.open(X.rotated31(G['idx'], G['rotate'])).convert('RGB'))
    if G['box'][0] >= 0 and G.get('rotate'): full = full[G['box'][1]:G['box'][3], G['box'][0]:G['box'][2]]
    im = Image.fromarray(full)
    return im.crop((int(round(xa)), int(round(ya)), int(round(xb)), int(round(yb)))).resize(((c1 - c0) * px, (r1 - r0) * px), Image.LANCZOS), sc


def panel(name, rows, G, px, rr=None):
    H, W = len(rows), len(rows[0])
    r0, r1 = rr if rr else (0, max(14, int(round(H * 0.5))))
    r1 = min(r1, H); c0, c1 = 0, W
    art, sc = art_crop(G, rows, r0, r1, c0, c1, px)
    w, h = (c1 - c0) * px, (r1 - r0) * px
    pad = 16; lab = 14
    im = Image.new('RGB', (3 * w + 4 * pad, h + 2 * lab + 12), (40, 40, 46)); d = ImageDraw.Draw(im)
    d.text((4, 0), (name[:70] + f'  {W}x{H}' + ('  ALINHAMENTO RUIM %d%%' % int(sc * 100) if sc < 0.9 else '')).encode('ascii', 'replace').decode(), fill=(255, 230, 80), font=FB)
    top = lab + 12
    im.paste(art, (pad, top))
    for k in range(r1 - r0 + 1): d.line([(pad, top + k * px), (pad + w, top + k * px)], fill=(255, 0, 255), width=1)
    for k in range(c1 - c0 + 1): d.line([(pad + k * px, top), (pad + k * px, top + h)], fill=(255, 0, 255), width=1)
    ox = 2 * pad + w
    mold = Image.new('RGB', (w, h), (98, 70, 140)); md = ImageDraw.Draw(mold); mask = Image.new('L', (w, h), 0); kd = ImageDraw.Draw(mask)
    for y in range(r0, r1):
        for x in range(c0, c1):
            ch_ = rows[y][x]; X0 = (x - c0) * px; Y0 = (y - r0) * px
            if ch_ == '.': continue
            md.rectangle([X0, Y0, X0 + px - 2, Y0 + px - 2], fill=HEX[ch_]); kd.rectangle([X0, Y0, X0 + px - 1, Y0 + px - 1], fill=120)
            lum = int(HEX[ch_][1:3], 16) * .3 + int(HEX[ch_][3:5], 16) * .59 + int(HEX[ch_][5:7], 16) * .11
            md.text((X0 + 1, Y0 + px // 3), CODE[ch_], fill=(0, 0, 0) if lum > 120 else (255, 255, 255), font=FNT)
            if ch_ == H1: md.rectangle([X0, Y0, X0 + px - 2, Y0 + px - 2], outline=(255, 0, 255))
    im.paste(mold, (ox, top))
    ov = art.copy(); ov.paste(mold, (0, 0), mask)
    im.paste(ov, (3 * pad + 2 * w, top))
    for y in range(r0, r1):
        d.text((2, top + (y - r0) * px + 2), str(y), fill=(255, 255, 0), font=FNT); d.text((ox - pad + 2, top + (y - r0) * px + 2), str(y), fill=(255, 255, 0), font=FNT)
    for x in range(c0, c1):
        d.text((pad + (x - c0) * px + 1, lab - 2 + 2), str(x), fill=(255, 255, 0), font=FNT); d.text((ox + (x - c0) * px + 1, lab - 2 + 2), str(x), fill=(255, 255, 0), font=FNT)
    return im


def main():
    a = sys.argv[1:]; px = 18; per = 6; tag = 'f'; rr = None
    for opt in ('--px', '--per', '--tag', '--rows'):
        if opt in a:
            k = a.index(opt); v = a[k + 1]; del a[k:k + 2]
            if opt == '--px': px = int(v)
            elif opt == '--per': per = int(v)
            elif opt == '--tag': tag = v
            else: rr = tuple(int(t) for t in v.split(','))
    allm = '--all' in a; a = [x for x in a if x not in ('--all', '--rev2')]
    usecat = '--cat' in a; a = [x for x in a if x != '--cat']          # --cat = as linhas ATUAIS do catálogo (com as edições dele), não as da conversão
    if usecat:
        import tplfile
        raw_ = json.load(open(os.path.join(HERE, 'data', 'final33_raw_120.json'), encoding='utf-8')); fin_ = json.load(open(os.path.join(HERE, 'data', 'final33_120.json'), encoding='utf-8'))
        cat_ = {x[0]: y[0] for x, y in zip(raw_, fin_)}
        byc = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
        if '--rev2' in sys.argv: byc.update(json.load(open(os.path.join(HERE, 'data', 'r31_rev2_new.json'), encoding='utf-8')))
        v2n = {x[0] for x in json.load(open(os.path.join(HERE, 'data', 'r31v2_raw_120.json'), encoding='utf-8'))} if os.path.exists(os.path.join(HERE, 'data', 'r31v2_raw_120.json')) else set()
        V2FOLHA = ('trio', 'lápis de cor')
    data = {x[0]: x for x in json.load(open(os.path.join(HERE, 'data', ('r31v2_raw_120.json' if os.environ.get('R31V2') == '1' else 'final33_raw_120.json')), encoding='utf-8'))}
    panels = []
    for n, g, idx, fn, grp in X.CFG:
        if usecat:
            if cat_.get(n) not in byc: continue
            X.GEOM_DIR = os.path.join(X.OUT, 'r31v2_geom' if any(k in n for k in V2FOLHA) else 'r31_geom')
            if not os.path.exists(X.geom_path(n)): continue
        elif n not in data or not os.path.exists(X.geom_path(n)): continue
        if a and not any(t.lower() in n.lower() for t in a): continue
        if not a and not allm and not ('chibi' in n.lower() or 'desenho' in n.lower()): continue
        G = X.load_geom(n); G['idx'] = idx
        panels.append((n, panel(f'{idx}: {n}', byc[cat_[n]] if usecat else data[n][2], G, px, rr)))
    for f in os.listdir(X.OUT):
        if f.startswith(f'r31f2_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    for k in range(0, len(panels), per):
        grp = [p for _, p in panels[k:k + per]]
        Wt = max(p.width for p in grp) + 8; Ht = sum(p.height + 6 for p in grp) + 6
        sh = Image.new('RGB', (Wt, Ht), (24, 24, 28)); y = 6
        for p in grp: sh.paste(p, (4, y)); y += p.height + 6
        sh.save(os.path.join(X.OUT, f'r31f2_{tag}_{k // per}.png'))
    print(len(panels), 'rostos,', (len(panels) + per - 1) // per, 'folhas')


if __name__ == '__main__':
    main()
