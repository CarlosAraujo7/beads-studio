"""Olhos no modelo da "Rei Ayanami (chibi, fundo amarelo)" (o que o dono aprovou), MEDIDOS NA ARTE, para os chibis da remessa 31.
Modelo: pálpebra PRETA em cima, íris em 3 tons (escura, média, clara) com 1 conta de brilho BRANCO e o branco (esclera) do lado de fora; o brilho fica do mesmo lado nos dois olhos.
  ['KKKK', 'KDHD', 'WMMM', ' LLL']  (olho esquerdo, 4 contas)  e  ['KKKK', 'DDHK', 'MMMW', 'LLL ']  (direito).

Como acha os olhos (nada é posicionado a olho; --probe de tools/r30_eyesheet.py mede a cor por conta quando é preciso conferir):
  1. a pele do rosto na ARTE (pixels de cor de pele, abertos 0,9 conta; a maior peça na metade de cima da figura) e a casca convexa dela;
  2. dentro da casca, o que é traço escuro ou branco vira "mancha" (fechada 0,42 conta); cada mancha tem a fração de PELE no anel em volta (olho = cercado de pele;
     mecha de cabelo e sobrancelha encostam no cabelo);
  3. o PAR de olhos: mesma altura (até 1,7 conta), afastados (>= 2,6 contas), tamanhos parecidos (razão <= 3,5), simétricos em relação ao eixo do rosto;
  4. os dois olhos viram o modelo com a largura e a altura das manchas (3 a 5 x 3 a 4; rosto pequeno = 2x3 ou 1x2), as 3 cores da íris saem da arte (terços de claridade
     dos pixels de íris perto da mancha) e o olho antigo (as contas de traço/branco/cor dentro da mancha) é apagado para a pele antes do desenho;
     olho fechado (mancha fina e escura, sem íris) vira um arco preto.
Nunca a conta transparente H1 (nem o apelido H12) no olho: brilho e esclera são H2. Se não achar um par seguro, não mexe (o molde fica como o convert6 deixou).
Para um rosto que o detector erra, `stamp_manual` desenha o modelo em posição dada (linha e coluna de cada olho, medidas na folha de rostos) com as cores medidas na arte."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, cv2


def offset(big, small):
    """(dy, dx, fração) em que o molde `small` mais coincide (forma: conta x vazio) com `big` (a saída do convert6)"""
    Hb, Wb, Hs, Ws = len(big), len(big[0]), len(small), len(small[0])
    B = np.array([[c != '.' for c in r] for r in big]); S = np.array([[c != '.' for c in r] for r in small])
    best = (-1.0, 0, 0)
    for dy in range(-4, max(1, Hb - Hs + 1) + 4):
        for dx in range(-4, max(1, Wb - Ws + 1) + 4):
            y0, x0 = max(0, dy), max(0, dx); y1, x1 = min(Hb, dy + Hs), min(Wb, dx + Ws)
            if y1 <= y0 or x1 <= x0: continue
            sc = float((B[y0:y1, x0:x1] == S[y0 - dy:y1 - dy, x0 - dx:x1 - dx]).sum()) / (Hs * Ws)
            if sc > best[0]: best = (sc, dy, dx)
    return best[1], best[2], best[0]


def eye_model(w, h, side):
    """linhas do olho w x h; K pálpebra, D/M/L íris (escura, média, clara), H brilho, W esclera, ' ' = não mexe. Reproduz exatamente os modelos 4x4 e 5x4 da Rei.
    O brilho (H) fica na coluna w-2 nos dois olhos (a luz vem do mesmo lado)."""
    w = max(2, min(5, w)); h = max(3, min(4, h))
    if w == 2: return ['KK', 'DH', 'ML']
    if side == 'L':
        r1 = 'K' + 'D' * (w - 3) + 'H' + 'D'; rm = 'W' + 'M' * (w - 1); rl = ' ' + 'L' * (w - 1)
    else:
        r1 = 'D' * (w - 2) + 'H' + 'K'; rm = 'M' * (w - 1) + 'W'; rl = 'L' * (w - 1) + ' '
    rows = ['K' * w, r1, rm, rl]
    return rows if h == 4 else rows[:3]


def closed_model(w):
    """olho fechado sorrindo: arco preto para cima"""
    w = max(3, min(5, w))
    return {3: [' K ', 'K K'], 4: [' KK ', 'K  K'], 5: [' KKK ', 'K   K']}[w]


def _lab_to_letter(lab, LAB, no=()):
    """letra do kit mais próxima de uma cor Lab (cor de íris: sem a conta transparente H1 nem apelidos)"""
    best = None
    for l, v in LAB.items():
        if l in no: continue
        d = float(np.linalg.norm(np.array(v, float) - np.array(lab, float)))
        if best is None or d < best[0]: best = (d, l)
    return best[1]


class Ctx:
    """arte e geometria de uma conversão, no sistema de contas do molde final: pxx/pyy (coluna, linha do molde -> pixel) e bx/by (pixel -> coluna, linha contínuas do molde)"""
    def __init__(self, rows, G, P, L, LAB):
        import illus
        self.rows, self.G, self.P, self.L, self.LAB = rows, G, P, L, LAB
        self.H, self.W = len(rows), len(rows[0])
        self.raw, self.fg = G['raw'], G['fg']
        self.h, self.w = self.fg.shape; self.nw, self.nh = G['nw'], G['nh']; self.top, self.left = G['top'], G['left']
        self.cw, self.ch = self.w / float(self.nw), self.h / float(self.nh)
        self.dy, self.dx, self.sc = offset(G['rows'], rows)
        self.lab = illus._lab(self.raw.astype(np.float32)); self.Lc = self.lab[..., 0]; self.Cc = np.hypot(self.lab[..., 1], self.lab[..., 2])
        self.ok = self.sc >= 0.85
        self.labs = None

    def bx(self, px): return px / self.cw - (self.dx + self.left - 1)
    def by(self, py): return py / self.ch - (self.dy + self.top - 1)
    def pxx(self, bx): return (bx + self.dx + self.left - 1) * self.cw
    def pyy(self, by): return (by + self.dy + self.top - 1) * self.ch

    def face(self):
        """pele do rosto na arte: (máscara da pele aberta, casca convexa, caixa em contas (fy0, fy1, fx0, fx1)) ou None"""
        A_, B_ = self.lab[..., 1], self.lab[..., 2]
        skin0 = self.fg & (self.Lc > 60) & (self.Lc < 99) & (A_ > -4) & (A_ < 28) & (B_ > 3) & (B_ < 38)
        self.skin0 = skin0
        ko = max(3, int(round(0.9 * self.cw))) | 1
        opened = cv2.morphologyEx(skin0.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ko, ko)))
        nS, labS, stS, cenS = cv2.connectedComponentsWithStats(opened, connectivity=8)
        ysf = np.nonzero(self.fg.any(axis=1))[0]; fig_top, fig_bot = int(ysf.min()), int(ysf.max())
        pick = None
        for i in range(1, nS):
            if cenS[i][1] > fig_top + 0.58 * (fig_bot - fig_top): continue
            if stS[i][4] < 6 * self.cw * self.ch: continue
            if pick is None or stS[i][4] > stS[pick][4]: pick = i
        if pick is None: return None
        face_px = labS == pick
        ysx, xsx = np.nonzero(face_px)
        hull = np.zeros(face_px.shape, np.uint8)
        cv2.fillConvexPoly(hull, cv2.convexHull(np.stack([xsx, ysx], axis=1).astype(np.int32)), 1)
        fy0 = self.by(ysx.min()); fy1 = self.by(ysx.max() + 1); fx0 = self.bx(xsx.min()); fx1 = self.bx(xsx.max() + 1)
        if fx1 - fx0 < 4 or fy1 - fy0 < 4: return None
        return face_px, hull > 0, (fy0, fy1, fx0, fx1)

    def masks(self, face_px):
        sel = face_px & self.fg
        self.skin_lab = np.median(self.lab[sel], axis=0); sL = float(self.skin_lab[0])
        self.dE = np.linalg.norm(self.lab - self.skin_lab, axis=2)
        self.dark = self.Lc < max(42.0, sL - 38.0)
        self.white = (self.Lc > min(96.0, sL + 5.0)) & (self.Cc < 16) & (self.dE > 8)
        self.iris = (self.dE > 26) & ~self.dark & ~self.white

    def skin_letter(self, box):
        """a letra de pele mais comum dentro da caixa do rosto (em contas do molde)"""
        from collections import Counter
        fy0, fy1, fx0, fx1 = box
        cnt = Counter(self.rows[y][x] for y in range(max(0, int(fy0)), min(self.H, int(fy1) + 1)) for x in range(max(0, int(fx0)), min(self.W, int(fx1) + 1)) if self.rows[y][x] in self.P.SKIN)
        return cnt.most_common(1)[0][0] if cnt else None


def find_pair(ctx, minpair=2.6, debug=False, ring_min=0.28, ratio_max=3.5, dy_max=1.7, thick_dark=None):
    """acha o par de olhos: devolve (dict(A, B, fw, fh, box), None) ou (None, motivo)"""
    if not ctx.ok: return None, f'alinhamento {ctx.sc:.0%}'
    f = ctx.face()
    if f is None: return None, 'sem rosto na arte'
    face_px, hull_px, box = f; fy0, fy1, fx0, fx1 = box; fh, fw = fy1 - fy0, fx1 - fx0
    if (face_px & ctx.fg).sum() < 30: return None, 'pele pequena'
    ctx.masks(face_px)
    cw, ch = ctx.cw, ctx.ch
    feat = (ctx.dark | ctx.white) & hull_px & ctx.fg
    k = max(3, int(round(0.42 * cw))) | 1
    closed = cv2.morphologyEx(feat.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, labs, st, cen = cv2.connectedComponentsWithStats(closed, connectivity=8)
    ctx.labs = labs
    comps = []
    for i in range(1, n):
        x, y, bw, bh, area = [int(v) for v in st[i]]
        if area < 0.2 * cw * ch: continue
        cx_b = ctx.bx(x + bw / 2.0); cy_b = ctx.by(y + bh / 2.0); bwb, bhb = bw / cw, bh / ch
        why = None
        if bwb < 0.6 or bhb < 0.6 or bwb > 9.0 or bhb > 8.0: why = 'tamanho'
        elif not (fy0 - 0.05 * fh <= cy_b <= fy0 + 0.95 * fh): why = 'faixa do rosto'
        pad = int(round(0.6 * cw))
        y0_, y1_, x0_, x1_ = max(0, y - pad), min(ctx.h, y + bh + pad), max(0, x - pad), min(ctx.w, x + bw + pad)
        m_loc = (labs[y0_:y1_, x0_:x1_] == i).astype(np.uint8)
        ring = cv2.dilate(m_loc, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1))) > 0
        ring &= (m_loc == 0)
        rs = float((ctx.skin0[y0_:y1_, x0_:x1_] & ring).sum()) / max(1, int(ring.sum()))
        if not why and rs < ring_min: why = f'cercada de pele só {rs:.2f}'
        if debug and why and area >= 0.3 * cw * ch: print(f'      rejeitada ({why}): linha {cy_b:.1f} coluna {cx_b:.1f} tam {bwb:.1f}x{bhb:.1f}')
        if why: continue
        irm = (ctx.iris[y0_:y1_, x0_:x1_] & ring & hull_px[y0_:y1_, x0_:x1_]) | (ctx.iris[y0_:y1_, x0_:x1_] & (m_loc > 0))
        comps.append(dict(i=i, x=x, y=y, bw=bw, bh=bh, area=area, cx=cx_b, cy=cy_b, bwb=bwb, bhb=bhb, rs=rs, irm=irm, irbox=(y0_, y1_, x0_, x1_),
                          ni=int(irm.sum()), nwh=int((ctx.white[y:y + bh, x:x + bw] & (labs[y:y + bh, x:x + bw] == i)).sum())))
    if debug:
        print(f'    [debug] rosto linhas {fy0:.1f}-{fy1:.1f} colunas {fx0:.1f}-{fx1:.1f}; pele Lab {ctx.skin_lab.round(0)}; {len(comps)} candidatas')
        for E in comps: print(f"      cand linha {E['cy']:.1f} coluna {E['cx']:.1f} tam {E['bwb']:.1f}x{E['bhb']:.1f} pele-em-volta {E['rs']:.2f} area {E['area'] / (cw * ch):.1f}")
    best = None
    for a in range(len(comps)):
        for b in range(a + 1, len(comps)):
            A, B = comps[a], comps[b]
            if abs(A['cy'] - B['cy']) > dy_max or abs(A['cx'] - B['cx']) < minpair or abs(A['cx'] - B['cx']) > 0.97 * fw: continue
            ra = max(A['area'], B['area']) / max(1.0, min(A['area'], B['area']))
            if ra > ratio_max: continue
            ccx = 0.5 * (A['cx'] + B['cx']); fcx = 0.5 * (fx0 + fx1)
            sym = 1.0 - min(1.0, abs(ccx - fcx) / (0.5 * fw))
            score = (min(A['area'], B['area']) / (cw * ch)) * (0.35 + 0.65 * sym) / ra
            if best is None or score > best[0]: best = (score, A, B)
    if not best: return None, 'sem par de olhos'
    _, A, B = best
    if A['cx'] > B['cx']: A, B = B, A
    return dict(A=A, B=B, fw=fw, fh=fh, box=box), None


def _iris_legend(ctx, E, no):
    """cores (letras) das 3 faixas de claridade da íris perto do olho E, medidas na arte"""
    L, LAB = ctx.L, ctx.LAB
    leg = {'K': L['H7'], 'H': L['H2'], 'W': L['H2']}
    y0_, y1_, x0_, x1_ = E['irbox']
    ir = E['irm'] & (ctx.dE[y0_:y1_, x0_:x1_] > 18)
    sub = ctx.lab[y0_:y1_, x0_:x1_]
    if ir.sum() >= 6:
        pts = sub[ir]; order = np.argsort(pts[:, 0]); t = len(order)
        dkc = pts[order[:max(1, t // 3)]].mean(axis=0); mdc = pts[order[t // 3:max(t // 3 + 1, 2 * t // 3)]].mean(axis=0) if t >= 3 else pts.mean(axis=0); ltc = pts[order[2 * t // 3:]].mean(axis=0)
        if float(ltc[0] - dkc[0]) < 7: dkc = mdc + np.array([-10.0, 0, 0]); ltc = mdc + np.array([9.0, 0, 0])
        for key, cc in zip('DML', (dkc, mdc, ltc)): leg[key] = _lab_to_letter(cc, LAB, no)
    else:
        leg.update({'D': L['H7'], 'M': L['H5'], 'L': L['H4']})
    return leg


def stamp(ctx, found, verbose=True):
    """desenha o modelo nos dois olhos de `found` (find_pair ou stamp_manual) e apaga o olho antigo; devolve (rows novos, info)"""
    import illus6
    rows = ctx.rows; L, LAB, P = ctx.L, ctx.LAB, ctx.P
    no = {L['H1']} | set(illus6._ALIAS)
    A, B = found['A'], found['B']; fw = found['fw']; box = found['box']
    H, W = ctx.H, ctx.W
    wf = 0.5 * (A['bwb'] + B['bwb']); hf = 0.5 * (A['bhb'] + B['bhb'])
    bw_b = int(round(wf)); bh_b = int(round(hf))
    cy = 0.5 * (A['cy'] + B['cy'])
    closed_eye = (not found.get('manual')) and all(E['ni'] < 0.04 * E['area'] and E['nwh'] < 0.06 * E['area'] and E['bwb'] / max(0.5, E['bhb']) > 1.9 and E['bhb'] <= 2.6 for E in (A, B))
    kind = 'tiny1' if (fw < 9.5 or wf < 1.7) else ('tiny2' if (fw < 13 or wf < 2.6) else 'full')
    if found.get('size'): kind = 'full'; bw_b, bh_b = found['size']
    if found.get('kind'): kind = found['kind']          # 'tiny1' (1x2), 'tiny2' (2x3) ou 'full' (3-5 x 3-4), à mão
    mh = 2 if (closed_eye or kind == 'tiny1') else (3 if kind == 'tiny2' else max(3, min(4, bh_b)))
    mw = 3 if closed_eye else (1 if kind == 'tiny1' else (2 if kind == 'tiny2' else max(3, min(5, bw_b))))
    r0 = found['rows'] if found.get('rows') is not None else int(round(cy - mh / 2.0))
    r0 = max(0, min(H - 2, r0))
    g = [list(r) for r in rows]
    skin = ctx.skin_letter(box) or next(iter(P.SKIN))
    drawn = []
    for side, E in (('L', A), ('R', B)):
        leg = {'K': L['H7']} if closed_eye else _iris_legend(ctx, E, no)
        c0 = int(round(E['cx'] - mw / 2.0)); c0 = max(0, min(W - 2, c0))
        if closed_eye: mdl = closed_model(max(3, bw_b))
        elif kind == 'tiny1': mdl = ['K', 'D']
        elif kind == 'tiny2': mdl = eye_model(2, 3, side)
        else: mdl = eye_model(max(3, bw_b), max(3, min(4, bh_b)), side)
        mm = (ctx.labs == E['i']) if (E.get('i') and ctx.labs is not None) else None
        wm, hm = len(mdl[0]), len(mdl)
        for yy in range(r0 - 1, r0 + hm + 1):                       # apaga o olho antigo: contas da mancha (cobertura >= 35%) na caixa do desenho + 1 de folga que não são pele viram a pele
            for xx in range(c0 - 1, c0 + wm + 1):
                if not (0 <= yy < H and 0 <= xx < W) or g[yy][xx] == '.' or g[yy][xx] in P.SKIN: continue
                if mm is not None:
                    xa, xb = int(ctx.pxx(xx)), int(ctx.pxx(xx + 1)); ya, yb = int(ctx.pyy(yy)), int(ctx.pyy(yy + 1))
                    cov = float(mm[max(0, ya):max(ya + 1, yb), max(0, xa):max(xa + 1, xb)].mean()) if xb > xa and yb > ya else 0.0
                    if cov < 0.35: continue
                g[yy][xx] = skin
        for yy, s in enumerate(mdl):
            for xx, ch_ in enumerate(s):
                if ch_ == ' ': continue
                y, x = r0 + yy, c0 + xx
                if not (0 <= y < H and 0 <= x < W): continue
                v = leg.get(ch_)
                if v is not None: g[y][x] = v
        drawn.append((side, r0, c0, mdl))
    info = dict(pair=[(d[0], d[1], d[2], len(d[3][0]), len(d[3])) for d in drawn], closed=closed_eye, kind=kind)
    if verbose: print('    olhos:', ' | '.join(f'{s} linha {r} coluna {c} {len(m[0])}x{len(m)}' for s, r, c, m in drawn) + (' (fechados)' if closed_eye else ''))
    return [''.join(r) for r in g], info


def auto_eyes(rows, G, P, L, LAB, verbose=True, debug=False, **kw):
    """rows = molde (saída do ill6), G = illus6.LAST_GEOM da conversão. Devolve (rows novos, informações). kw = opções do find_pair (ring_min, ratio_max, dy_max, minpair)"""
    ctx = Ctx(rows, G, P, L, LAB)
    found, why = find_pair(ctx, debug=debug or bool(os.environ.get('DEBUG_EYES')), **kw)
    if not found: return rows, dict(why=why)
    return stamp(ctx, found, verbose=verbose)


def stamp_manual(rows, G, P, L, LAB, rl, cl, rr, cr, w=4, h=4, kind=None, verbose=True):
    """olhos em posição dada: (rl, cl) = canto de cima à esquerda do olho esquerdo, (rr, cr) = o do direito (linhas e colunas do molde, medidas na folha de rostos); w x h = tamanho.
    As cores da íris saem da arte na caixa de cada olho."""
    ctx = Ctx(rows, G, P, L, LAB)
    if not ctx.ok: return rows, dict(why=f'alinhamento {ctx.sc:.0%}')
    f = ctx.face()
    if f is None:          # rosto claro demais para contar como pele pela cor (Alucard): a caixa vem dos olhos dados à mão e a cor de pele é a mediana da arte entre eles
        box = (rl - 3.0, rl + h + 6.0, cl - 3.0, cr + w + 3.0)
        sel = np.zeros(ctx.fg.shape, bool)
        sel[max(0, int(ctx.pyy(rl))):int(ctx.pyy(rl + h + 3)), max(0, int(ctx.pxx(cl))):int(ctx.pxx(cr + w))] = True
        face_px = sel & ctx.fg
        if face_px.sum() < 30: return rows, dict(why='sem rosto na arte')
    else:
        face_px, hull_px, box = f
    ctx.masks(face_px)
    comps = []
    for (r, c) in ((rl, cl), (rr, cr)):
        xa, xb, ya, yb = int(ctx.pxx(c)), int(ctx.pxx(c + w)), int(ctx.pyy(r)), int(ctx.pyy(r + h))
        xa, ya = max(0, xa), max(0, ya); xb, yb = min(ctx.w, max(xb, xa + 1)), min(ctx.h, max(yb, ya + 1))
        irm = ctx.iris[ya:yb, xa:xb] & ctx.fg[ya:yb, xa:xb]
        comps.append(dict(i=0, x=xa, y=ya, bw=xb - xa, bh=yb - ya, area=(xb - xa) * (yb - ya), cx=c + w / 2.0, cy=r + h / 2.0, bwb=float(w), bhb=float(h), irm=irm, irbox=(ya, yb, xa, xb), ni=int(irm.sum()), nwh=0))
    found = dict(A=comps[0], B=comps[1], fw=99.0, fh=99.0, box=box, manual=True, size=(w, h), rows=rl, kind=kind)
    return stamp(ctx, found, verbose=verbose)


def mouth_zone(ctx, rows=None, found=None, width=0.62):
    """zona da BOCA no molde (linha 0, linha 1, coluna 0, coluna 1) ou None. Geométrica: dentro do rosto (a pele da arte, levada ao molde), no centro (`width` da largura do rosto) e
    abaixo da linha dos olhos (3 contas abaixo do olho achado; sem olho achado, 52% da altura do rosto) até 2 contas antes do queixo, tudo que NÃO é pele e não é o vazio é a boca
    (o nariz fica acima; o contorno do queixo, abaixo). A caixa é a menor que cobre essas contas, com 1 de folga em cima e embaixo. Só há zona se sobram >= 3 contas."""
    rows = rows or ctx.rows; P, L = ctx.P, ctx.L
    f = ctx.face()
    if f is None: return None
    face_px, hull_px, (fy0, fy1, fx0, fx1) = f
    H, W = ctx.H, ctx.W
    if found: ey1 = max(found['A']['cy'] + found['A']['bhb'] / 2.0, found['B']['cy'] + found['B']['bhb'] / 2.0)
    else: ey1 = fy0 + 0.52 * (fy1 - fy0)
    r0 = int(ey1 + 2.2); r1 = int(fy1 - 2.0)
    cx = 0.5 * (fx0 + fx1); fw = fx1 - fx0
    cells = []
    for y in range(max(0, r0), min(H - 1, r1) + 1):
        for x in range(max(0, int(fx0)), min(W, int(fx1) + 1)):
            ch = rows[y][x]
            if ch == '.' or ch in P.SKIN: continue
            if abs(x + 0.5 - cx) > 0.5 * width * fw: continue
            # dentro do rosto: o pixel da arte no centro da conta tem de estar na casca da pele
            px_, py_ = int(ctx.pxx(x + 0.5)), int(ctx.pyy(y + 0.5))
            if not (0 <= py_ < ctx.h and 0 <= px_ < ctx.w) or not hull_px[py_, px_]: continue
            cells.append((y, x))
    if len(cells) < 3: return None
    ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
    return (max(0, min(ys) - 1), min(H - 1, max(ys) + 1), max(0, min(xs) - 1), min(W - 1, max(xs) + 1))
