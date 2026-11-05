"""Folha de LEITURA de rosto da remessa 30 ALINHADA com a grade do convert6, para moldes que JÁ ESTÃO no catálogo:
esquerda = a arte recortada exatamente nas contas do molde, com a grade e a régua; direita = o molde do CATÁLOGO (ou o de data/r30_rev_new.json com --new) com o código de cada conta.
  BEADPAL=120 python tools/r30_eyesheet.py "nome|r0|r1|c0|c1" ... [--new] [--px 26] [--tag nome]          (r1/c1 exclusivos)
A geometria vem de uma reconversão pelo mesmo fn() do CFG (illus6.LAST_GEOM); as cores da reconversão não importam (o k-means muda um pouco a cada execução):
o molde do catálogo é posto sobre a saída do convert6 pelo deslocamento de maior coincidência de contas. Molde que ele girou ou redesenhou no app pode não alinhar (o título avisa).
Saída: tools/out/r30e_<tag>_N.png (1 por molde)."""
import os, sys, json
os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tplfile
from palette import ALL

HEX = {c['letter']: c['hex'] for c in ALL}; CODE = {c['letter']: c['code'] for c in ALL}
PROBE = False


def offset(big, small):
    """(dy, dx, fração) em que o molde `small` mais coincide (forma: conta x vazio) com a saída `big` do convert6"""
    Hb, Wb, Hs, Ws = len(big), len(big[0]), len(small), len(small[0])
    B = np.array([list(r) for r in big]) != '.'; S = np.array([list(r) for r in small]) != '.'
    best = (-1.0, 0, 0)
    for dy in range(-3, max(1, Hb - Hs + 1) + 3):
        for dx in range(-3, max(1, Wb - Ws + 1) + 3):
            y0, x0 = max(0, dy), max(0, dx); y1, x1 = min(Hb, dy + Hs), min(Wb, dx + Ws)
            if y1 <= y0 or x1 <= x0: continue
            sb = B[y0:y1, x0:x1]; ss = S[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
            sc = float((sb == ss).sum()) / (Hs * Ws)
            if sc > best[0]: best = (sc, dy, dx)
    return best[1], best[2], best[0]


def sheet(X, cat, name, r0, r1, c0, c1, px, out, raw=None):
    """raw = linhas originais da conversão (data/final32_raw_120.json): se ele girou/espelhou o molde no app, a arte é girada igual (r30_revsheet.best_tf)"""
    import illus6
    n, g, idx, fn, grp = next(c for c in X.CFG if c[0] == name or name.lower() in c[0].lower())
    X.P.CUR[0] = n
    fn()
    G = dict(illus6.LAST_GEOM)
    rows = cat[n]
    k_rot, flip = 0, False
    if raw is not None and n in raw and (len(raw[n]), len(raw[n][0])) != (len(rows), len(rows[0])) or (raw and n in raw and raw[n] != rows):
        import r30_revsheet as RS
        tf, tsc = RS.best_tf(raw[n], rows)
        if tsc > 0.5: k_rot, flip = tf[1], tf[2]
    a_ = np.array([list(r) for r in rows])
    if flip: a_ = a_[:, ::-1]
    a_ = np.rot90(a_, -k_rot)
    rows0 = [''.join(r) for r in a_]                 # o molde na orientação da conversão
    dy, dx, sc = offset(G['rows'], rows0)
    box = getattr(fn, 'box', None)
    src = X.R.illus._load(X.F[idx], box)
    cw, ch = G['w'] / G['nw'], G['h'] / G['nh']
    def pix(r, c):
        return G['x0'] + (c + dx + G['left'] - 1) * cw, G['y0'] + (r + dy + G['top'] - 1) * ch
    H0, W0 = len(rows0), len(rows0[0])
    xa, ya = pix(0, 0); xb, yb = pix(H0, W0)
    S = Image.fromarray(src)
    full = np.array(S.crop((int(round(xa)), int(round(ya)), int(round(xb)), int(round(yb)))).resize((W0 * px, H0 * px), Image.LANCZOS))
    full = np.rot90(full, k_rot)
    if flip: full = full[:, ::-1]
    full = np.ascontiguousarray(full)
    r1 = min(r1, len(rows)); c1 = min(c1, len(rows[0]))
    W, H = (c1 - c0) * px, (r1 - r0) * px
    crop = Image.fromarray(full[r0 * px:r1 * px, c0 * px:c1 * px])
    pad = 26
    im = Image.new('RGB', (3 * W + 4 * pad, H + 2 * pad + 18), (40, 40, 46)); d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype('arial.ttf', max(9, px // 3)); fb = ImageFont.truetype('arialbd.ttf', 13)
    except Exception:
        fnt = fb = ImageFont.load_default()
    d.text((4, 2), f'{n}  {len(rows[0])}x{len(rows)}  (alinhamento {sc:.0%})' + ('  ALINHAMENTO RUIM' if sc < 0.9 else '') + (f'  [girado por ele: rot {k_rot}{" espelhado" if flip else ""}]' if k_rot or flip else ''), fill=(255, 230, 80), font=fb)
    top = pad + 18
    im.paste(crop, (pad, top))
    for k in range(r1 - r0 + 1): d.line([(pad, top + k * px), (pad + W, top + k * px)], fill=(255, 0, 255), width=1)
    for k in range(c1 - c0 + 1): d.line([(pad + k * px, top), (pad + k * px, top + H)], fill=(255, 0, 255), width=1)
    ox = 2 * pad + W
    for y in range(r0, r1):
        for x in range(c0, c1):
            chr_ = rows[y][x]; Xx, Yy = ox + (x - c0) * px, top + (y - r0) * px
            if chr_ == '.': d.rectangle([Xx, Yy, Xx + px - 1, Yy + px - 1], outline=(70, 70, 76)); continue
            hx = HEX[chr_]; d.rectangle([Xx, Yy, Xx + px - 2, Yy + px - 2], fill=hx)
            lum = int(hx[1:3], 16) * .3 + int(hx[3:5], 16) * .59 + int(hx[5:7], 16) * .11
            d.text((Xx + 2, Yy + px // 3), CODE[chr_], fill=(0, 0, 0) if lum > 120 else (255, 255, 255), font=fnt)
    for y in range(r0, r1):
        d.text((3, top + (y - r0) * px + px // 3), str(y), fill=(255, 255, 0), font=fnt)
        d.text((ox - pad + 3, top + (y - r0) * px + px // 3), str(y), fill=(255, 255, 0), font=fnt)
    for x in range(c0, c1):
        d.text((pad + (x - c0) * px + px // 4, 24), str(x), fill=(255, 255, 0), font=fnt)
        d.text((ox + (x - c0) * px + px // 4, 24), str(x), fill=(255, 255, 0), font=fnt)
    # 3º painel: o molde a 50% por cima da arte (confere o alinhamento)
    ov = crop.copy(); od = ImageDraw.Draw(ov)
    mold = Image.new('RGB', (W, H), (0, 0, 0)); md = ImageDraw.Draw(mold)
    mask = Image.new('L', (W, H), 0); kd = ImageDraw.Draw(mask)
    for y in range(r0, r1):
        for x in range(c0, c1):
            chr_ = rows[y][x]
            if chr_ == '.': continue
            md.rectangle([(x - c0) * px, (y - r0) * px, (x - c0) * px + px - 1, (y - r0) * px + px - 1], fill=HEX[chr_])
            kd.rectangle([(x - c0) * px, (y - r0) * px, (x - c0) * px + px - 1, (y - r0) * px + px - 1], fill=120)
    ov.paste(mold, (0, 0), mask)
    o3 = 3 * pad + 2 * W
    im.paste(ov, (o3, top))
    for k in range(r1 - r0 + 1): d.line([(o3, top + k * px), (o3 + W, top + k * px)], fill=(255, 0, 255), width=1)
    for k in range(c1 - c0 + 1): d.line([(o3 + k * px, top), (o3 + k * px, top + H)], fill=(255, 0, 255), width=1)
    for x in range(c0, c1): d.text((o3 + (x - c0) * px + px // 4, 24), str(x), fill=(255, 255, 0), font=fnt)
    im.save(out)
    if PROBE:                                  # cor da arte por conta (mediana do miolo) e a conta mais próxima
        import r5
        print(f'{n}: cor da arte por conta (linhas {r0}-{r1 - 1}, colunas {c0}-{c1 - 1})')
        print('     ' + ''.join(f'{x:>16}' for x in range(c0, c1)))
        for y in range(r0, r1):
            line = []
            for x in range(c0, c1):
                q = full[y * px + px // 4:y * px + 3 * px // 4 + 1, x * px + px // 4:x * px + 3 * px // 4 + 1].reshape(-1, 3)
                if not len(q): line.append(' ' * 16); continue
                m = np.median(q, axis=0).astype(int)
                code = CODE[r5.near120(tuple(int(v) for v in m))]
                line.append(f' {m[0]:3d},{m[1]:3d},{m[2]:3d} {code:<3}')
            print(f'{y:>4} ' + ''.join(line))
    return sc


if __name__ == '__main__':
    import r30_exfinal as X
    X.P.TOUCH6 = X.TOUCH30; X.P.SKIN6 = X.SKIN30
    a = sys.argv[1:]; px = 26; tag = 'e'
    if '--px' in a: k = a.index('--px'); px = int(a[k + 1]); del a[k:k + 2]
    if '--tag' in a: k = a.index('--tag'); tag = a[k + 1]; del a[k:k + 2]
    use_new = '--new' in a; a = [x for x in a if x != '--new']
    if '--probe' in a: PROBE = True; a = [x for x in a if x != '--probe']
    cat = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    if use_new:
        for nm, r in json.load(open(os.path.join(HERE, 'data', 'r30_rev_new.json'), encoding='utf-8')).items(): cat[nm] = r
    raw = json.load(open(os.path.join(HERE, 'data', 'final32_raw_120.json'), encoding='utf-8'))
    if isinstance(raw, list): raw = {r[0] if not isinstance(r, dict) else r['name']: (r[2] if not isinstance(r, dict) else r['rows']) for r in raw}
    for f in os.listdir(os.path.join(HERE, 'out')):
        if f.startswith(f'r30e_{tag}_') and f.endswith('.png'): os.remove(os.path.join(HERE, 'out', f))
    for k, spec in enumerate(a):
        nm, *lim = spec.split('|')
        full = next((c[0] for c in X.CFG if c[0] == nm), None) or next(c[0] for c in X.CFG if nm.lower() in c[0].lower())
        if full not in cat:
            full2 = next((c for c in cat if c.startswith(full[:-1])), None)
            if not full2: print('não está no catálogo:', full); continue
        r0, r1, c0, c1 = (int(v) for v in lim)
        sc = sheet(X, cat, full, r0, r1, c0, c1, px, os.path.join(HERE, 'out', f'r30e_{tag}_{k}.png'), raw=raw)
        print(f'{k}: {full} alinhamento {sc:.0%}')


def art_cells(X, cat, name, raw=None, px=12):
    """cor da arte por conta do molde do catálogo (mediana do miolo de cada conta), já girada como ele deixou o molde: matriz H x W x 3"""
    import illus6
    n, g, idx, fn, grp = next(c for c in X.CFG if c[0] == name or name.lower() in c[0].lower())
    X.P.CUR[0] = n
    fn()
    G = dict(illus6.LAST_GEOM)
    rows = cat[n]
    k_rot, flip = 0, False
    if raw and n in raw and raw[n] != rows:
        import r30_revsheet as RS
        tf, tsc = RS.best_tf(raw[n], rows)
        if tsc > 0.5: k_rot, flip = tf[1], tf[2]
    a_ = np.array([list(r) for r in rows])
    if flip: a_ = a_[:, ::-1]
    a_ = np.rot90(a_, -k_rot)
    rows0 = [''.join(r) for r in a_]
    dy, dx, sc = offset(G['rows'], rows0)
    src = X.R.illus._load(X.F[idx], getattr(fn, 'box', None))
    cw, ch = G['w'] / G['nw'], G['h'] / G['nh']
    H0, W0 = len(rows0), len(rows0[0])
    xa = G['x0'] + (dx + G['left'] - 1) * cw; ya = G['y0'] + (dy + G['top'] - 1) * ch
    xb = xa + W0 * cw; yb = ya + H0 * ch
    full = np.array(Image.fromarray(src).crop((int(round(xa)), int(round(ya)), int(round(xb)), int(round(yb)))).resize((W0 * px, H0 * px), Image.LANCZOS))
    full = np.rot90(full, k_rot)
    if flip: full = full[:, ::-1]
    H, W = len(rows), len(rows[0])
    out = np.zeros((H, W, 3), int)
    for y in range(H):
        for x in range(W):
            q = full[y * px + px // 4:y * px + 3 * px // 4 + 1, x * px + px // 4:x * px + 3 * px // 4 + 1].reshape(-1, 3)
            out[y, x] = np.median(q, axis=0)
    return out, sc
