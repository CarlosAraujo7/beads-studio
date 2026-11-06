"""Folha de OLHOS da remessa 31 (lê data/final33_raw_120.json e tools/out/r31_geom/*.npz; não reconverte): uma janela em volta do par de olhos (achado pelo detector na arte
alinhada ao molde) ou, quando ele não acha, em volta do rosto. Três painéis por molde, com régua de linha/coluna do molde:
    ARTE (grade das contas)  |  MOLDE como está  |  PRÉVIA do modelo da Rei carimbado pelo detector (só quando achou o par)
Serve para decidir, molde a molde, entre deixar como o convert6 fez, carimbar o par achado ('auto') ou dar a posição à mão (EYES31 no r31_exfinal.py).
    python tools/r31_eyecheck.py [trecho do nome ...] [--px 12] [--per 8] [--tag nome] [--all] [--only found|failed] [--grow 5] [--codes]
Janela: 3 contas de folga em volta do par e `--grow` contas a mais embaixo (para ver a boca). H1 (transparente) fica marcada em magenta. Saída: tools/out/r31ec_<tag>_N.png"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import r31_exfinal as X
import r31_eyes as EY
import r31_faces2 as F2
from palette import ALL

HEX = {c['letter']: c['hex'] for c in ALL}; CODE = {c['letter']: c['code'] for c in ALL}
H1 = next(c['letter'] for c in ALL if c['code'] == 'H1')
try:
    FNT = ImageFont.truetype('arial.ttf', 8); FB = ImageFont.truetype('arialbd.ttf', 11)
except Exception:
    FNT = FB = ImageFont.load_default()


def draw_mold(rows, r0, r1, c0, c1, px, codes):
    w, h = (c1 - c0) * px, (r1 - r0) * px
    mold = Image.new('RGB', (w, h), (98, 70, 140)); md = ImageDraw.Draw(mold)
    for y in range(r0, r1):
        for x in range(c0, c1):
            ch_ = rows[y][x]; X0 = (x - c0) * px; Y0 = (y - r0) * px
            if ch_ == '.': continue
            md.rectangle([X0, Y0, X0 + px - 2, Y0 + px - 2], fill=HEX[ch_])
            if codes:
                lum = int(HEX[ch_][1:3], 16) * .3 + int(HEX[ch_][3:5], 16) * .59 + int(HEX[ch_][5:7], 16) * .11
                md.text((X0 + 1, Y0 + px // 3), CODE[ch_], fill=(0, 0, 0) if lum > 120 else (255, 255, 255), font=FNT)
            if ch_ == H1: md.rectangle([X0, Y0, X0 + px - 2, Y0 + px - 2], outline=(255, 0, 255))
    return mold


def panel(name, rows, G, px, grow, codes):
    ctx = EY.Ctx(rows, G, X.P, X.L, X.LAB)
    H, W = len(rows), len(rows[0])
    found, why = EY.find_pair(ctx)
    prev = None
    if found:
        A, B = found['A'], found['B']
        cy = 0.5 * (A['cy'] + B['cy']); wb = 0.5 * (A['bwb'] + B['bwb']); hb = 0.5 * (A['bhb'] + B['bhb'])
        c0 = int(A['cx'] - wb / 2 - 3); c1 = int(B['cx'] + wb / 2 + 4); r0 = int(cy - hb / 2 - 3); r1 = int(cy + hb / 2 + 2 + grow)
        title = f"olhos linha {cy - hb / 2:.0f}, colunas {A['cx']:.0f} e {B['cx']:.0f} (tam {wb:.1f}x{hb:.1f})"
        try: prev, info = EY.stamp(ctx, found, verbose=False)
        except Exception as e: prev = None; title += f' (prévia falhou: {e!r})'
    else:
        f = ctx.face() if ctx.ok else None
        if f:
            fy0, fy1, fx0, fx1 = f[2]; r0, r1, c0, c1 = int(fy0) - 1, int(fy1) + 2, int(fx0) - 1, int(fx1) + 2
        else:
            r0, r1, c0, c1 = 0, int(H * 0.45), 0, W
        title = f'SEM PAR: {why}'
    r0 = max(0, r0); c0 = max(0, c0); r1 = min(H, max(r1, r0 + 6)); c1 = min(W, max(c1, c0 + 8))
    art, sc = F2.art_crop(G, rows, r0, r1, c0, c1, px)
    w, h = (c1 - c0) * px, (r1 - r0) * px
    pad = 12; lab = 12; npan = 3 if prev else 2
    im = Image.new('RGB', (npan * w + (npan + 1) * pad, h + lab + 14), (40, 40, 46)); d = ImageDraw.Draw(im)
    d.text((3, 0), (f'{name[:40]}  {title}').encode('ascii', 'replace').decode(), fill=(255, 230, 80) if found else (255, 120, 120), font=FB)
    top = lab + 4
    im.paste(art, (pad, top))
    xs = [pad]
    im.paste(draw_mold(rows, r0, r1, c0, c1, px, codes), (2 * pad + w, top)); xs.append(2 * pad + w)
    if prev: im.paste(draw_mold(prev, r0, r1, c0, c1, px, codes), (3 * pad + 2 * w, top)); xs.append(3 * pad + 2 * w)
    for k in range(r1 - r0 + 1): d.line([(pad, top + k * px), (pad + w, top + k * px)], fill=(255, 0, 255), width=1)
    for k in range(c1 - c0 + 1): d.line([(pad + k * px, top), (pad + k * px, top + h)], fill=(255, 0, 255), width=1)
    for x0_ in xs:
        for y in range(r0, r1):
            if (y - r0) % 2 == 0: d.text((x0_ - pad + 1, top + (y - r0) * px + 1), str(y), fill=(255, 255, 0), font=FNT)
        for x in range(c0, c1):
            if (x - c0) % 2 == 0: d.text((x0_ + (x - c0) * px + 1, top - 10), str(x), fill=(255, 255, 0), font=FNT)
    return im, bool(found)


def main():
    a = sys.argv[1:]; px = 12; per = 8; tag = 'e'; only = None; grow = 5
    for opt in ('--px', '--per', '--tag', '--only', '--grow'):
        if opt in a:
            k = a.index(opt); v = a[k + 1]; del a[k:k + 2]
            if opt == '--px': px = int(v)
            elif opt == '--per': per = int(v)
            elif opt == '--tag': tag = v
            elif opt == '--only': only = v
            else: grow = int(v)
    codes = '--codes' in a; allm = '--all' in a; a = [x for x in a if x not in ('--all', '--codes')]
    data = {x[0]: x for x in json.load(open(os.path.join(HERE, 'data', ('r31v2_raw_120.json' if os.environ.get('R31V2') == '1' else 'final33_raw_120.json')), encoding='utf-8'))}
    panels = []; nf = nfail = 0
    for n, g, idx, fn, grp in X.CFG:
        if n not in data or not os.path.exists(X.geom_path(n)): continue
        if a and not any(t.lower() in n.lower() for t in a): continue
        if not a and not allm and not ('chibi' in n.lower() or 'desenho' in n.lower()): continue
        G = X.load_geom(n); G['idx'] = idx
        try:
            im, ok = panel(f'{idx}: {n}', data[n][2], G, px, grow, codes)
        except Exception as e:
            print('ERRO', n, repr(e)); continue
        if only == 'found' and not ok: continue
        if only == 'failed' and ok: continue
        panels.append(im); nf += ok; nfail += (not ok)
    for f in os.listdir(X.OUT):
        if f.startswith(f'r31ec_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    cols = 2
    for k in range(0, len(panels), per):
        grp = panels[k:k + per]; rws = [grp[i:i + cols] for i in range(0, len(grp), cols)]
        Wt = max(sum(p.width for p in r) + 8 * (len(r) - 1) for r in rws) + 12; Ht = sum(max(p.height for p in r) + 8 for r in rws) + 8
        sh = Image.new('RGB', (Wt, Ht), (24, 24, 28)); y = 6
        for r in rws:
            x = 6
            for p in r: sh.paste(p, (x, y)); x += p.width + 8
            y += max(p.height for p in r) + 8
        sh.save(os.path.join(X.OUT, f'r31ec_{tag}_{k // per}.png'))
    print(len(panels), 'painéis,', (len(panels) + per - 1) // per, 'folhas;', nf, 'com par achado,', nfail, 'sem par')


if __name__ == '__main__':
    main()
