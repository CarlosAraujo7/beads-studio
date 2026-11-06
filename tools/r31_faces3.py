"""Folha de ROSTOS de TODOS os moldes de ilustração da remessa 31 (lê data/final33_raw_120.json e tools/out/r31_geom/*.npz; não reconverte): para cada molde, o rosto da ARTE
(recortado exatamente nas contas do molde) | o rosto do MOLDE, sem códigos, lado a lado. É a folha que pega boca aberta, dentes, olho sumido, olho grande demais e conta H1
(transparente, marcada em magenta) em rosto branco, que o no_mouth31 e o auto_eyes deixam passar em silêncio.
    python tools/r31_faces3.py [trecho do nome ...] [--px 9] [--per 21] [--cols 3] [--tag nome] [--all]
Por padrão só os moldes dos grupos 'ill' e 'folha' (os gráficos são cópia fiel e não têm geometria). O recorte é a caixa do rosto (a pele na arte) com 3 contas de folga;
sem rosto achado, o terço de cima. O título leva o nº da imagem, o nome curto, o tamanho do molde e `boca?N` = contas de cor de boca na metade de baixo do rosto.
Saída: tools/out/r31f3_<tag>_N.png"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import r31_exfinal as X
import r31_eyes as EY
import r31_faces2 as F2
import r31_mouths as MO
from palette import ALL

HEX = {c['letter']: c['hex'] for c in ALL}
H1 = next(c['letter'] for c in ALL if c['code'] == 'H1')
try:
    FNT = ImageFont.truetype('arial.ttf', 10); FB = ImageFont.truetype('arialbd.ttf', 11)
except Exception:
    FNT = FB = ImageFont.load_default()


def head_box(ctx, rows):
    H, W = len(rows), len(rows[0])
    f = ctx.face() if ctx.ok else None
    if f:
        fy0, fy1, fx0, fx1 = f[2]
        return max(0, int(fy0) - 3), min(H, int(fy1) + 4), max(0, int(fx0) - 3), min(W, int(fx1) + 4), f[2]
    ys = [y for y in range(H) if any(c != '.' for c in rows[y])]
    top = ys[0] if ys else 0
    return top, min(H, top + max(10, int(0.4 * (len(ys) or H)))), 0, W, None


def panel(name, rows, G, px):
    ctx = EY.Ctx(rows, G, X.P, X.L, X.LAB)
    r0, r1, c0, c1, fb = head_box(ctx, rows)
    nm = 0
    if fb and ctx.ok:
        nm = MO.count_mouthy(rows, fb)[0]
    art, sc = F2.art_crop(G, rows, r0, r1, c0, c1, px)
    w, h = (c1 - c0) * px, (r1 - r0) * px
    mold = Image.new('RGB', (w, h), (98, 70, 140)); md = ImageDraw.Draw(mold)
    for y in range(r0, r1):
        for x in range(c0, c1):
            ch_ = rows[y][x]
            if ch_ == '.': continue
            X0 = (x - c0) * px; Y0 = (y - r0) * px
            md.rectangle([X0, Y0, X0 + px - 1, Y0 + px - 1], fill=HEX[ch_])
            if ch_ == H1: md.rectangle([X0, Y0, X0 + px - 1, Y0 + px - 1], outline=(255, 0, 255))
    pad = 6
    im = Image.new('RGB', (2 * w + 3 * pad, h + 16), (40, 40, 46)); d = ImageDraw.Draw(im)
    d.text((3, 1), (f'{name[:46]} {len(rows[0])}x{len(rows)} boca?{nm}' + ('' if sc >= 0.9 else f' ALINH {sc:.0%}')).encode('ascii', 'replace').decode(), fill=(255, 230, 80) if nm < 8 else (255, 140, 140), font=FNT)
    im.paste(art, (pad, 16)); im.paste(mold, (2 * pad + w, 16))
    return im


def main():
    a = sys.argv[1:]; px = 9; per = 21; cols = 3; tag = 'a'
    for opt in ('--px', '--per', '--cols', '--tag'):
        if opt in a:
            k = a.index(opt); v = a[k + 1]; del a[k:k + 2]
            if opt == '--px': px = int(v)
            elif opt == '--per': per = int(v)
            elif opt == '--cols': cols = int(v)
            else: tag = v
    allm = '--all' in a; a = [x for x in a if x != '--all']
    data = {x[0]: x for x in json.load(open(os.path.join(HERE, 'data', ('r31v2_raw_120.json' if os.environ.get('R31V2') == '1' else 'final33_raw_120.json')), encoding='utf-8'))}
    panels = []
    for n, g, idx, fn, grp in X.CFG:
        if n not in data or not os.path.exists(X.geom_path(n)): continue
        if grp in ('graf', 'foto'): continue
        if a and not any(t.lower() in n.lower() for t in a): continue
        G = X.load_geom(n); G['idx'] = idx
        try: panels.append(panel(f'{idx}: {n}', data[n][2], G, px))
        except Exception as e: print('ERRO', n, repr(e))
    for f in os.listdir(X.OUT):
        if f.startswith(f'r31f3_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    for k in range(0, len(panels), per):
        grp = panels[k:k + per]; rws = [grp[i:i + cols] for i in range(0, len(grp), cols)]
        Wt = max(sum(p.width for p in r) + 8 * (len(r) - 1) for r in rws) + 12; Ht = sum(max(p.height for p in r) + 6 for r in rws) + 8
        sh = Image.new('RGB', (Wt, Ht), (24, 24, 28)); y = 6
        for r in rws:
            x = 6
            for p in r: sh.paste(p, (x, y)); x += p.width + 8
            y += max(p.height for p in r) + 6
        sh.save(os.path.join(X.OUT, f'r31f3_{tag}_{k // per}.png'))
    print(len(panels), 'rostos,', (len(panels) + per - 1) // per, 'folhas')


if __name__ == '__main__':
    main()
