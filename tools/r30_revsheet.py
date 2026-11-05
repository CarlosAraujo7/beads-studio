"""Folha de LEITURA para revisar moldes da remessa 30 que JÁ ESTÃO no catálogo (pedido do dono no chat, 2026-11-05: olhos e rostos dos moldes que ele mandou nas capturas):
arte (recortada como na conversão, girada como ele deixou o molde) | molde ATUAL do catálogo com régua | arte da cabeça ampliada | cabeça do molde ampliada com régua.
  python tools/r30_revsheet.py "trecho do nome" ... [--new] [--tag nome] [--frac 0.45]
--new mostra o resultado de tools/r30_rev.py (data/r30_rev_new.json) em vez do catálogo. Saída: tools/out/r30rev_<tag>_N.png (2 moldes por folha)."""
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tplfile
from palette import ALL
HEX = {p['letter']: p['hex'] for p in ALL}
OUT = os.path.join(HERE, 'out')
try:
    FNT = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 11); FB = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 15)
except Exception:
    FNT = FB = ImageFont.load_default()


def cfg_name(n):
    return re.sub(r', versão \d+\)$', ')', n)


def transforms(rows):
    """as 8 orientações (rotações e espelhos) de um molde, com o nome da operação que leva o original a cada uma"""
    a = np.array([list(r) for r in rows])
    out = []
    for k in range(4):
        b = np.rot90(a, k)
        out.append((('rot', k, False), b)); out.append((('rot', k, True), b[:, ::-1]))
    return out


def best_tf(orig, cur):
    c = np.array([list(r) for r in cur]); best = (('rot', 0, False), -1.0)
    for tf, b in transforms(orig):
        if b.shape != c.shape: continue
        sc = float((b == c).mean())
        if sc > best[1]: best = (tf, sc)
    return best


def apply_tf_img(im, tf):
    _, k, mir = tf
    for _ in range(k): im = im.transpose(Image.ROTATE_90)          # np.rot90 gira no sentido anti-horário; ROTATE_90 do PIL também
    if mir: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


def draw_rows(rows, px, ruler=True, r0=0, r1=None):
    r1 = len(rows) if r1 is None else r1
    W = len(rows[0]); L = 24 if ruler else 0; T = 16 if ruler else 0
    im = Image.new('RGB', (L + W * px, T + (r1 - r0) * px), (40, 40, 48)); d = ImageDraw.Draw(im)
    for y in range(r0, r1):
        if ruler and (y % 2 == 0 or px >= 14): d.text((2, T + (y - r0) * px + max(0, px // 2 - 7)), str(y), fill=(220, 220, 220), font=FNT)
        for x, c in enumerate(rows[y]):
            X, Y = L + x * px, T + (y - r0) * px
            d.rectangle((X, Y, X + px - 1, Y + px - 1), fill=HEX[c] if c != '.' else (92, 70, 140), outline=(66, 66, 76) if px >= 10 else None)
    if ruler:
        for x in range(W):
            if x % 2 == 0 or px >= 14: d.text((L + x * px + 2, 1), str(x), fill=(220, 220, 220), font=FNT)
    return im


def fg_bbox(im):
    a = np.array(im.convert('RGB')).astype(np.int32)
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]); bg = np.median(edge, axis=0)
    m = np.abs(a - bg).sum(axis=2) > 60
    ys, xs = np.nonzero(m)
    if not len(ys): return (0, 0, im.width, im.height)
    return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)


HEADS = [False]          # --heads: só a cabeça (arte | molde com régua), 3 moldes por folha


def block(name, cur, orig, art, frac):
    H, W = len(cur), len(cur[0])
    tf, sc = best_tf(orig, cur) if orig else (('rot', 0, False), 1.0)
    art = apply_tf_img(art, tf)
    x0, y0, x1, y1 = fg_bbox(art)
    art = art.crop((x0, y0, x1, y1))
    HH = 500
    a1 = art.copy(); a1.thumbnail((int(HH * art.width / art.height) + 1, HH))
    px = max(4, min(12, HH // H)); m1 = draw_rows(cur, px)
    hr = max(6, int(round(H * frac)))
    ah = art.crop((0, 0, art.width, max(1, int(art.height * hr / H))))
    pxh = max(10, min(22, 640 // max(W, 1)))
    m2 = draw_rows(cur, pxh, r1=hr)
    ah = ah.resize((max(1, int(ah.width * (m2.height - 16) / ah.height)), m2.height - 16), Image.LANCZOS)
    parts = [ah, m2] if HEADS[0] else [a1, m1, ah, m2]
    Wt = sum(p.width for p in parts) + 12 * len(parts); Ht = max(p.height for p in parts) + 24
    im = Image.new('RGB', (Wt, Ht), (28, 28, 34)); d = ImageDraw.Draw(im)
    d.text((4, 2), f'{name}  {W}x{H}' + (f'  (orientação do original: {tf}, {sc:.0%} igual)' if orig and tf != ('rot', 0, False) else '') + ('' if orig and sc > 0.999 else ('  [AJUSTADO POR ELE]' if orig else '')), fill=(255, 230, 80), font=FB)
    x = 0
    for p in parts: im.paste(p, (x, 24)); x += p.width + 12
    return im


def main():
    import r30_exfinal as X
    argv = sys.argv[1:]; tag = 'f'; frac = 0.45; use_new = '--new' in argv; HEADS[0] = '--heads' in argv
    if '--tag' in argv: k = argv.index('--tag'); tag = argv[k + 1]; del argv[k:k + 2]
    if '--frac' in argv: k = argv.index('--frac'); frac = float(argv[k + 1]); del argv[k:k + 2]
    qs = [a for a in argv if not a.startswith('--')]
    cat = {t['name']: t for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    if use_new:
        pth = os.path.join(HERE, 'data', 'r30_rev_new.json')
        for n, r in json.load(open(pth, encoding='utf-8')).items():
            if n in cat: cat[n] = dict(cat[n], rows=r)
    orig = {x[0]: x[2] for x in json.load(open(os.path.join(HERE, 'data', 'final32_120.json'), encoding='utf-8'))}
    cfg = {n: (idx, getattr(fn, 'box', None)) for n, g, idx, fn, grp in X.CFG}
    blocks = []
    for q in qs:
        hits = [n for n in cat if n == q] or [n for n in cat if q.lower() in n.lower()]
        hits = [n for n in hits if cfg_name(n) in cfg] or hits
        if not hits: print('não achado no catálogo:', q); continue
        n = hits[0]
        cn = cfg_name(n)
        if cn not in cfg: print('sem fonte no CFG da remessa 30:', n); continue
        idx, box = cfg[cn]
        blocks.append(block(n, cat[n]['rows'], orig.get(n), X.R.source_img(idx, box), frac))
    per = 3 if HEADS[0] else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r30rev_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for s in range(0, len(blocks), per):
        part = blocks[s:s + per]
        Wt = max(b.width for b in part); Ht = sum(b.height for b in part) + 8 * len(part)
        sh = Image.new('RGB', (Wt, Ht), (20, 20, 24)); y = 0
        for b in part: sh.paste(b, (0, y)); y += b.height + 8
        sh.save(os.path.join(OUT, f'r30rev_{tag}_{s // per}.png'))
    print(len(blocks), 'moldes,', (len(blocks) + per - 1) // per, 'folhas')


if __name__ == '__main__':
    main()
