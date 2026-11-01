"""Recolore o "Okarun transformado" de 768 contas (id kaiju-de-juba-branca-chibi, 25x50; remessa 16 idx 17) a pedido do usuário (2026-10-30):
cabelo CREME com os DESTAQUES VERMELHOS das pontas e das mechas como no original, franja cinza, rosto de pele, traje preto, olhos vermelhos, óculos brancos.
A FORMA (máscara e contornos pretos) é a mesma do molde atual: este script repete a conversão `illus.convert4` (mesma janela por conta) e só troca a regra de COR das contas que não são contorno:
 - decide por classe dos pixels claros da janela (imagem ORIGINAL, sem realce): vermelho vivo, vermelho escuro, creme, cinza, pele, branco;
 - o vermelho fino (3-4 px de uma conta de ~16 px) é "puxado": basta ~RED_T da parte clara ser vermelha para a conta virar vermelha (senão a média rosada apagava as mechas);
 - a trava de pele do near120 fica DESLIGADA (ela mandava o creme para bege-rosado).
uso:  BEADPAL=120 python tools/okarun_recolor.py     -> tools/out/okarun_recolor.png (fonte | atual | novo) e data/okarun768_120.json
"""
import os, sys, json, glob
os.environ['REMNUM'] = '16'
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numpy as np, cv2
import r5, illus, outline as O, tplfile
from flat import render_flat

RED_T = 0.032          # fração (dos pontos claros da janela) de vermelho vivo para a conta virar vermelha
EDGE_RED = 0.26        # contorno com >= 16% de vermelho vivo (e < 55% de preto) vira vermelho
EDGE_DRED = 0.40
DRED_T = 0.30         # vermelho escuro (asas/aura): fração maior, para não pintar contornos
SRC = sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa 16', '*.*')))[17]


def classify(px):
    """classe de cada pixel (N,3) da imagem original: R vermelho vivo, D vermelho escuro, c creme, g cinza, s pele, w branco, k preto, ? outro"""
    r, g, b = px[:, 0].astype(int), px[:, 1].astype(int), px[:, 2].astype(int)
    mx = px.max(axis=1).astype(int); mn = px.min(axis=1).astype(int)
    out = np.full(len(px), '?', dtype='<U1')
    out[(mx < 70)] = 'k'
    out[(r > 235) & (g > 235) & (b > 235)] = 'w'
    out[(mx - mn < 22) & (mx > 120) & (mx < 215)] = 'g'
    out[(r > 200) & (g > 165) & (g < 215) & (b > 140) & (b < 205) & (r - b > 25) & (g - b < 45)] = 's'
    out[(r > 205) & (g > 195) & (b > 150) & (b < 228) & (mx - mn < 62) & (g - b > 8)] = 'c'
    out[(r > 90) & (r < 175) & (g < 62) & (b < 72) & (r - g > 55)] = 'D'
    out[(r > 150) & (g < 95) & (b < 95) & (r - g > 85)] = 'R'
    return out


def build(red_t=RED_T, dred_t=DRED_T, verbose=False):
    r5.SKIN_ON = False
    rgb0 = illus._load(SRC, None)
    edge = np.concatenate([rgb0[0], rgb0[-1], rgb0[:, 0], rgb0[:, -1]])
    bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
    m = illus.sticker_bg(rgb0, 205, None) if bg == 'white' else illus.flat_bg(rgb0, None, 45)
    ys, xs = np.nonzero(~m); ppb = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) / 50.0
    m = illus.seal_leaks(m, 0.6 * ppb)                       # = seal padrão do fundo branco (convert4)
    rgb = illus.enhance(rgb0, 1.2, 1.1, 0.5, True)           # realce padrão (só para as contas de contorno e a média do resto)
    over = 8; size = 50; dark_L = 28.0; dark_frac = 0.17; cover = 0.5
    ys, xs = np.nonzero(~m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgbc = rgb[y0:y1, x0:x1]; raw = rgb0[y0:y1, x0:x1]; fg = (~m[y0:y1, x0:x1]).astype(np.float32)
    h, w = fg.shape
    s = min(1.0, size / max(w, h)); nw, nh = max(1, round(w * s)), max(1, round(h * s))
    bw, bh = nw * over, nh * over
    fgb = cv2.resize(fg, (bw, bh), interpolation=cv2.INTER_AREA)
    col = cv2.resize(rgbc.astype(np.float32) * fg[..., None], (bw, bh), interpolation=cv2.INTER_AREA) / np.maximum(fgb[..., None], 1e-3)
    colr = cv2.resize(raw.astype(np.float32) * fg[..., None], (bw, bh), interpolation=cv2.INTER_AREA) / np.maximum(fgb[..., None], 1e-3)
    L = illus._lab(col)[..., 0]
    isfg = fgb > 0.5; dark = isfg & (L < dark_L)
    def blocks(a): return a.reshape(nh, over, nw, over, *a.shape[2:])
    nfg = blocks(isfg.astype(np.float32)).sum(axis=(1, 3)); ndk = blocks(dark.astype(np.float32)).sum(axis=(1, 3))
    isfg_b = blocks(isfg); cb = blocks(col); crb = blocks(colr); fb = blocks((isfg & ~dark).astype(np.float32)); db = blocks(dark.astype(np.float32))
    mean_dk = (cb * db[..., None]).sum(axis=(1, 3)) / np.maximum(db.sum(axis=(1, 3))[..., None], 1)
    rows = []; stat = {}
    for y in range(nh):
        r = ''
        for x in range(nw):
            if nfg[y, x] < cover * over * over: r += '.'; continue
            if ndk[y, x] >= dark_frac * nfg[y, x] or nfg[y, x] - ndk[y, x] < 1:
                # conta de CONTORNO. Na fonte a linha vermelha vem encostada no traço preto: se a janela tem vermelho vivo suficiente (EDGE_RED) e o preto não domina, a conta é vermelha
                allpx = crb[y, :, x, :][isfg_b[y, :, x, :]]
                if len(allpx):
                    cla = classify(allpx); fr_all = {k: (cla == k).sum() / len(allpx) for k in 'RDk'}
                    if fr_all['R'] >= EDGE_RED and fr_all['k'] < 0.55:
                        r += r5.near120(tuple(float(v) for v in allpx[cla == 'R'].mean(axis=0))); continue
                    if fr_all['D'] >= EDGE_DRED and fr_all['k'] < 0.55:
                        r += r5.near120(tuple(float(v) for v in allpx[cla == 'D'].mean(axis=0))); continue
                r += r5.near120(tuple(float(v) for v in mean_dk[y, x]), dark=True); continue
            sel = fb[y, :, x, :] > 0                                   # pontos claros da janela (over x over)
            px = crb[y, :, x, :][sel]                                  # cor ORIGINAL desses pontos
            if len(px) == 0: r += '.'; continue
            cl = classify(px); n = len(px)
            fr = {k: (cl == k).sum() / n for k in 'RDcgswk?'}
            if fr['R'] >= red_t: letter = r5.near120(tuple(float(v) for v in px[cl == 'R'].mean(axis=0)))
            elif fr['D'] >= dred_t: letter = r5.near120(tuple(float(v) for v in px[cl == 'D'].mean(axis=0)))
            else:
                # sem vermelho: a cor da CLASSE dominante (creme/cinza/pele/branco), não a média misturada com o vermelho fino
                dom = max('cgsw', key=lambda k: fr[k])
                if fr[dom] >= 0.3: letter = r5.near120(tuple(float(v) for v in px[cl == dom].mean(axis=0)))
                else: letter = r5.near120(tuple(float(v) for v in px.mean(axis=0)))
            r += letter
            stat[(y, x)] = (round(fr['R'], 2), round(fr['D'], 2), round(fr['c'], 2))
        rows.append(r)
    return O.trim(rows)


if __name__ == '__main__':
    cat = next(x for x in tplfile.parse(os.path.join(ROOT, 'templates.js'))['items'] if x['id'] == 'kaiju-de-juba-branca-chibi')['rows']
    new = build()
    print(len(new[0]), len(new), '| atual', len(cat[0]), len(cat))
    render_flat([('ATUAL', cat), ('NOVO', new)], os.path.join(HERE, 'out', 'okarun_recolor.png'), scale=14, W=1100)
    from PIL import Image
    a = Image.open(os.path.join(HERE, 'out', 'okarun_recolor.png')); src = Image.open(SRC).convert('RGB'); src = src.resize((int(src.width * a.height / src.height), a.height))
    cmp_ = Image.new('RGB', (src.width + a.width, a.height), (60, 60, 66)); cmp_.paste(src, (0, 0)); cmp_.paste(a, (src.width, 0)); cmp_.save(os.path.join(HERE, 'out', 'okarun_cmp.png'))
    json.dump(new, open(os.path.join(HERE, 'out', 'okarun_new.json'), 'w'))
