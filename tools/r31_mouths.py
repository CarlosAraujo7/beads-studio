"""Triagem de BOCAS da remessa 31 (lê data/final33_raw_120.json e tools/out/r31_geom/*.npz; não reconverte). Para cada molde de ilustração com pele (skin=True), conta as contas "de boca"
(vermelho, rosa, dente branco, marrom-escuro avermelhado; o mesmo critério do no_mouth) que sobram na METADE DE BAIXO do rosto e imprime os moldes ordenados por quantidade.
    python tools/r31_mouths.py [--min 3] [--sheet] [--px 14] [--tag nome]
--sheet gera tools/out/r31m_<tag>_N.png: para cada molde com >= --min contas, a janela do queixo (arte | molde) com régua de linha/coluna para ler a zona da boca (linha 0, linha 1, coluna 0, coluna 1)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import r31_exfinal as X
import r31_eyes as EY
import r31_faces2 as F2
import r31_eyecheck as EC

P = X.P; LAB = X.LAB


def lower_face(ctx):
    f = ctx.face()
    if f is None: return None
    face_px, hull_px, (fy0, fy1, fx0, fx1) = f
    return fy0, fy1, fx0, fx1


def count_mouthy(rows, box):
    fy0, fy1, fx0, fx1 = box
    r0 = int(fy0 + 0.50 * (fy1 - fy0)); r1 = int(fy1) + 1
    n = 0; cells = []
    H, W = len(rows), len(rows[0])
    for y in range(max(0, r0), min(H, r1 + 1)):
        for x in range(max(0, int(fx0)), min(W, int(fx1) + 1)):
            ch = rows[y][x]
            if ch == '.' or ch in P.SKIN or ch == X.L['H7']: continue
            if P._mouthy(ch):
                # só conta se encostada em pele (boca dentro do rosto, não roupa nem cabelo)
                nb = [rows[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W]
                if sum(1 for c in nb if c in P.SKIN) >= 1: n += 1; cells.append((y, x))
    return n, cells, (r0, r1)


def main():
    a = sys.argv[1:]; mn = 3; px = 14; tag = 'm'
    for opt in ('--min', '--px', '--tag'):
        if opt in a:
            k = a.index(opt); v = a[k + 1]; del a[k:k + 2]
            if opt == '--min': mn = int(v)
            elif opt == '--px': px = int(v)
            else: tag = v
    names_f = [x for x in a if not x.startswith('--')]
    data = {x[0]: x for x in json.load(open(os.path.join(HERE, 'data', 'final33_raw_120.json'), encoding='utf-8'))}
    res = []
    for n, g, idx, fn, grp in X.CFG:
        if n not in data or not os.path.exists(X.geom_path(n)): continue
        if names_f and not any(t.lower() in n.lower() for t in names_f): continue
        if not names_f and not ('chibi' in n.lower() or 'desenho' in n.lower()): continue
        G = X.load_geom(n); G['idx'] = idx
        rows = data[n][2]
        ctx = EY.Ctx(rows, G, P, X.L, LAB)
        if not ctx.ok: continue
        box = lower_face(ctx)
        if box is None: continue
        c, cells, (r0, r1) = count_mouthy(rows, box)
        fnd, _w = EY.find_pair(ctx)
        z = EY.mouth_zone(ctx, found=fnd)
        res.append((c, n, idx, box, cells, G, z))
    res.sort(key=lambda t: -t[0])
    print(f'{len(res)} moldes com rosto; contas de boca na metade de baixo do rosto:')
    for c, n, idx, box, cells, G, z in res:
        if c >= 1: print(f'  {c:3d}  {idx:3d}  {n}  zona={z}')
    if '--sheet' in sys.argv:
        panels = []
        for c, n, idx, box, cells, G, z in res:
            if c < mn: continue
            rows = data[n][2]; H, W = len(rows), len(rows[0])
            fy0, fy1, fx0, fx1 = box
            r0 = max(0, int(fy0 + 0.35 * (fy1 - fy0))); r1 = min(H, int(fy1) + 3); c0 = max(0, int(fx0) - 2); c1 = min(W, int(fx1) + 3)
            art, sc = F2.art_crop(G, rows, r0, r1, c0, c1, px)
            mold = EC.draw_mold(rows, r0, r1, c0, c1, px, False)
            w, h = (c1 - c0) * px, (r1 - r0) * px; pad = 12; lab = 12
            im = Image.new('RGB', (2 * w + 3 * pad, h + lab + 16), (40, 40, 46)); d = ImageDraw.Draw(im)
            d.text((3, 0), (f'{idx}: {n[:60]}  boca? {c} contas').encode('ascii', 'replace').decode(), fill=(255, 230, 80), font=EC.FB)
            top = lab + 4
            im.paste(art, (pad, top)); im.paste(mold, (2 * pad + w, top))
            if z:
                zr0, zr1, zc0, zc1 = z
                for ox_ in (pad, 2 * pad + w):
                    d.rectangle([ox_ + (zc0 - c0) * px, top + (zr0 - r0) * px, ox_ + (zc1 + 1 - c0) * px - 1, top + (zr1 + 1 - r0) * px - 1], outline=(0, 255, 255), width=2)
            for k in range(r1 - r0 + 1): d.line([(pad, top + k * px), (pad + w, top + k * px)], fill=(255, 0, 255), width=1)
            for k in range(c1 - c0 + 1): d.line([(pad + k * px, top), (pad + k * px, top + h)], fill=(255, 0, 255), width=1)
            for x0_ in (pad, 2 * pad + w):
                for y in range(r0, r1):
                    if (y - r0) % 2 == 0: d.text((x0_ - pad + 1, top + (y - r0) * px + 1), str(y), fill=(255, 255, 0), font=EC.FNT)
                for x in range(c0, c1):
                    if (x - c0) % 2 == 0: d.text((x0_ + (x - c0) * px + 1, top - 10), str(x), fill=(255, 255, 0), font=EC.FNT)
            panels.append(im)
        for f in os.listdir(X.OUT):
            if f.startswith(f'r31m_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
        per = 8; cols = 2
        for k in range(0, len(panels), per):
            grp = panels[k:k + per]; rws = [grp[i:i + cols] for i in range(0, len(grp), cols)]
            Wt = max(sum(p.width for p in r) + 8 * (len(r) - 1) for r in rws) + 12; Ht = sum(max(p.height for p in r) + 8 for r in rws) + 8
            sh = Image.new('RGB', (Wt, Ht), (24, 24, 28)); y = 6
            for r in rws:
                x = 6
                for p in r: sh.paste(p, (x, y)); x += p.width + 8
                y += max(p.height for p in r) + 8
            sh.save(os.path.join(X.OUT, f'r31m_{tag}_{k // per}.png'))
        print(len(panels), 'painéis,', (len(panels) + per - 1) // per, 'folhas')


if __name__ == '__main__':
    main()
