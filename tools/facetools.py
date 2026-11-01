"""Ferramentas para MELHORAR ROSTOS de moldes já no catálogo (pedido do usuário, 2026-10-30: "os personagens ficarem com olhos bem feitos e rosto é o que faz ficar um hama bead bonito").
Fluxo por molde:  src_raw(remessa, idx, box)  ->  align(raw, rows)  ->  sheet(...)  [OLHAR a folha]  ->  escrever o conserto em tools/faces_fix.py  ->  apply_fix(rows, fix)  ->  conferir a comparação.

align(raw, rows)      acha onde cada conta do molde cai na imagem de origem (origem + tamanho da conta), por correlação da silhueta (não depende de como o molde foi convertido).
sheet(...)            folha PNG: recorte da fonte ampliado com a grade do molde (números de coluna/linha do MOLDE) | o mesmo recorte do molde, com a mesma grade.
apply_fix(rows, fix)  aplica blocos de texto / células soltas / troca de cor por região (ver tools/faces_fix.py).
"""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw
import illus
from flat import L2HEX
from palette import ALL

CODE2L = {p['code']: p['letter'] for p in ALL}


def src_path(rem, idx):
    return sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa %s' % rem, '*.*')))[idx]


def src_raw(rem, idx, box=None):
    return illus._load(src_path(rem, idx), box)


def fg_mask(raw, thr=205, bg='auto', tol=45):
    """silhueta da figura na imagem de origem (True = figura)"""
    if bg == 'auto':
        edge = np.concatenate([raw[0], raw[-1], raw[:, 0], raw[:, -1]])
        bg = 'white' if np.median(edge.min(axis=1)) >= 225 else 'flat'
    if bg == 'white': m = illus.sticker_bg(raw, thr, None)
    elif bg == 'flat': m = illus.flat_bg(raw, None, tol)
    else: m = np.zeros(raw.shape[:2], bool)
    return ~m


def align(raw, rows, bg='auto', thr=205, tol=45, verbose=True):
    """devolve (ox, oy, cw, ch): a conta (c, r) do molde cobre na imagem x in [ox+c*cw, ox+(c+1)*cw), y in [oy+r*ch, oy+(r+1)*ch)."""
    fg = fg_mask(raw, thr, bg, tol)
    ys, xs = np.nonzero(fg); X0, X1, Y0, Y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    H, W = len(rows), len(rows[0])
    mol = np.array([[c != '.' for c in r] for r in rows], np.float32)
    fgf = fg.astype(np.float32)
    # integral para somar a silhueta por conta
    I = cv2.integral(fgf)
    best = None
    cw0 = (X1 - X0) / W; ch0 = (Y1 - Y0) / H
    for sx in np.linspace(0.94, 1.12, 10):
        for sy in np.linspace(0.94, 1.12, 10):
            cw, ch = cw0 * sx, ch0 * sy
            for ox in np.arange(X0 - 2.5 * cw0, X0 + 2.5 * cw0 + 1e-6, cw0 / 4):
                for oy in np.arange(Y0 - 2.5 * ch0, Y0 + 2.5 * ch0 + 1e-6, ch0 / 4):
                    xe = ox + np.arange(W + 1) * cw; ye = oy + np.arange(H + 1) * ch
                    xi = np.clip(np.round(xe).astype(int), 0, raw.shape[1]); yi = np.clip(np.round(ye).astype(int), 0, raw.shape[0])
                    S = I[np.ix_(yi[1:], xi[1:])] - I[np.ix_(yi[:-1], xi[1:])] - I[np.ix_(yi[1:], xi[:-1])] + I[np.ix_(yi[:-1], xi[:-1])]
                    area = np.maximum(np.outer(np.diff(yi), np.diff(xi)), 1)
                    cov = (S / area) >= 0.5
                    inter = (cov & (mol > 0)).sum(); uni = (cov | (mol > 0)).sum()
                    sc = inter / max(uni, 1)
                    if best is None or sc > best[0]: best = (sc, ox, oy, cw, ch)
    if verbose: print('align IoU %.3f  ox=%.1f oy=%.1f cw=%.2f ch=%.2f' % best)
    return best[1], best[2], best[3], best[4]


def _crop(raw, geom, r0, r1, c0, c1, cell):
    ox, oy, cw, ch = geom
    x0, y0 = ox + c0 * cw, oy + r0 * ch; x1, y1 = ox + c1 * cw, oy + r1 * ch
    H, W = raw.shape[:2]
    xi0, yi0, xi1, yi1 = int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))
    im = Image.fromarray(raw).crop((xi0, yi0, xi1, yi1))
    # moldura do tamanho certo (se a região sai da imagem, fica branco)
    tw, th = int((c1 - c0) * cell), int((r1 - r0) * cell)
    out = Image.new('RGB', (tw, th), (255, 255, 255))
    sx, sy = tw / (x1 - x0), th / (y1 - y0)
    im2 = im.resize((max(1, int(im.width * sx)), max(1, int(im.height * sy))), Image.LANCZOS)
    out.paste(im2, (int((xi0 - x0) * sx), int((yi0 - y0) * sy)))
    return out


def sheet(raw, rows, geom, region, path, cell=34, title='', letters=False):
    """region = (r0, r1, c0, c1) em contas do molde (r1/c1 exclusivos). Esquerda: fonte; direita: molde. Grade magenta nas fronteiras das contas; números = índices do MOLDE."""
    r0, r1, c0, c1 = region
    src = _crop(raw, geom, r0, r1, c0, c1, cell)
    W = (c1 - c0) * cell; Hh = (r1 - r0) * cell
    mol = Image.new('RGB', (W, Hh), (60, 60, 66)); d = ImageDraw.Draw(mol)
    for j in range(r0, r1):
        for i in range(c0, c1):
            ch = rows[j][i] if 0 <= j < len(rows) and 0 <= i < len(rows[0]) else '.'
            x, y = (i - c0) * cell, (j - r0) * cell
            col = ((200, 200, 205) if (i + j) % 2 == 0 else (225, 225, 228)) if ch == '.' else L2HEX[ch]
            d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=col)
            if letters and ch != '.':
                lum = sum(col) / 3; d.text((x + cell // 2 - 3, y + cell // 2 - 5), ch.encode('ascii', 'replace').decode(), fill=(0, 0, 0) if lum > 120 else (255, 255, 255))
    out = Image.new('RGB', (W * 2 + 40, Hh + 30), (40, 40, 44)); out.paste(src, (30, 24)); out.paste(mol, (W + 36, 24))
    dd = ImageDraw.Draw(out)
    if title: dd.text((30, 4), title, fill=(255, 255, 255))
    for k, ox_ in enumerate((30, W + 36)):
        for i in range(c1 - c0 + 1):
            x = ox_ + i * cell; dd.line((x, 24, x, 24 + Hh), fill=(255, 0, 255) if (c0 + i) % 5 == 0 else (150, 60, 150), width=1)
            if i < c1 - c0 and (c0 + i) % 2 == 0: dd.text((x + 2, 12), str(c0 + i), fill=(255, 255, 0))
        for j in range(r1 - r0 + 1):
            y = 24 + j * cell; dd.line((ox_, y, ox_ + W, y), fill=(255, 0, 255) if (r0 + j) % 5 == 0 else (150, 60, 150), width=1)
            if j < r1 - r0: dd.text((ox_ - 28 if k == 0 else ox_ - 28, y + 2), str(r0 + j), fill=(255, 255, 0))
    out.save(path)
    return out.size


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def letter_of(tok, legend):
    """tok = letra de 1 caractere. Se estiver na legenda do conserto ({char: 'código Pindou'}) vale o código; senão é a própria letra da paleta."""
    if tok in legend: return CODE2L[legend[tok]]
    return tok


def apply_fix(rows, fix):
    """fix = {'legend': {char: código}, 'blocks': [(y0, x0, [linhas...])], 'cells': {(y, x): char}, 'mirror': (a2, lado, y0, y1)?}
       - blocks: ' ' não mexe; '.' esvazia; o resto é cor (legenda ou letra da paleta)
       - cells: contas soltas  - 'sym': [(y0, y1, x_axis2, 'L'|'R')] copia (espelhado) um lado para o outro só nessas linhas, só onde o lado de origem não é vazio"""
    leg = fix.get('legend', {})
    g = [list(r) for r in rows]
    H, W = len(g), len(g[0])
    SKIN0 = ['G1', 'G2', 'G3', 'E1', 'E11', 'E14', 'E15', 'A12', 'G9']
    for y0, y1, x0, x1, frm, to in fix.get('pre_recolor', []):      # igual ao recolor, mas ANTES de desenhar (limpa restos para o desenho novo ficar claro)
        fl = set(CODE2L[c] for c in (SKIN0 if frm == 'skin' else frm)); tl = CODE2L[to] if to in CODE2L else to
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if g[y][x] in fl: g[y][x] = tl
    for y0, x0, lines in fix.get('blocks', []):
        for j, ln in enumerate(lines):
            for i, ch in enumerate(ln):
                if ch == ' ': continue
                y, x = y0 + j, x0 + i
                if not (0 <= y < H and 0 <= x < W): raise ValueError('bloco fora do molde: %s' % ((y, x),))
                g[y][x] = '.' if ch == '.' else letter_of(ch, leg)
    for (y, x), ch in fix.get('cells', {}).items():
        g[y][x] = '.' if ch == '.' else letter_of(ch, leg)
    SKIN = ['G1', 'G2', 'G3', 'E1', 'E11', 'E14', 'E15', 'A12', 'G9']
    for y0, y1, x0, x1, frm, to in fix.get('recolor', []):         # troca as letras `frm` (lista de códigos, ou 'skin') por `to` (código ou letra) dentro do retângulo
        fl = set(CODE2L[c] for c in (SKIN if frm == 'skin' else frm))
        tl = CODE2L[to] if to in CODE2L else to
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if g[y][x] in fl: g[y][x] = tl
    for y0, y1, a2, side, x0, x1 in fix.get('sym', []):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                xm = a2 - x
                if not (0 <= xm < W): continue
                if (side == 'L' and 2 * x < a2) or (side == 'R' and 2 * x > a2):
                    g[y][xm] = g[y][x]
    return [''.join(r) for r in g]


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def variants(rem, idx, base, vlist, path, cur=None, skin=True, scale=9, W=1900, box=None, show_src=True):
    """reconverte a imagem com várias combinações de parâmetros do illus.convert4 e junta numa folha: fonte | molde atual | variantes.
    base = kwargs comuns; vlist = [(rótulo, {kwargs a mais})]. Devolve {rótulo: linhas}."""
    import r5
    from flat import render_flat
    r5.SKIN_ON = skin
    p = src_path(rem, idx); out = {}; items = []
    if cur is not None: items.append(('ATUAL', cur))
    for lab, kw in vlist:
        a = dict(base); a.update(kw)
        if box is not None and 'box' not in a: a['box'] = box
        out[lab] = illus.convert4(p, **a); items.append((lab, out[lab]))
    tmp = path + '.tmp.png'
    render_flat(items, tmp, scale=scale, W=W)
    im = Image.open(tmp)
    if show_src:
        raw = src_raw(rem, idx, box)
        fg = fg_mask(raw); ys, xs = np.nonzero(fg)
        sm = Image.fromarray(raw).crop((max(0, xs.min() - 4), max(0, ys.min() - 4), min(raw.shape[1], xs.max() + 5), min(raw.shape[0], ys.max() + 5)))
        h = (len(items[0][1]) * scale) + 18
        sm = sm.resize((max(1, int(sm.width * h / sm.height)), h), Image.LANCZOS)
        comp = Image.new('RGB', (sm.width + im.width + 8, max(im.height, h + 40)), (60, 60, 66)); comp.paste(sm, (4, 24)); comp.paste(im, (sm.width + 8, 0)); comp.save(path)
    else: im.save(path)
    os.remove(tmp)
    return out
