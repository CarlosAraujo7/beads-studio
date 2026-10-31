"""Consertos dos moldes FRACOS das remessas 22/23 (pedido do usuário, 2026-10-31: "refazer fracos antes"; veja CLAUDE.md §7.19).
Cada molde tem uma lista de operações aplicada DEPOIS da conversão (`illus5.convert5` + limpezas de `r22_exfinal.ill`), pelos ganchos `fix=` (1 placa) e `fixg=` (irmão grande) do CFG:
  ('wipe', r0, r1, c0, c1)            apaga as contas do retângulo (inclusive); coordenadas do molde de 1 PLACA (no irmão grande são escaladas pelas dimensões)
  ('wipe', r0, r1, c0, c1, 'neutral') apaga SÓ as contas neutras (preto/branco/cinza: `NEUT`); poupa o fogo/pele (restos de texto em katakana junto de chamas)
  ('put', {(lin, col): letra})        contas soltas, só no molde de 1 placa
  ('blocks', [(lin, col, ['texto', ...])], legend)   blocos de letras (' ' não mexe, '.' esvazia; um caractere da `legend` vira o código Pindou) só no de 1 placa
  ('recolor', r0, r1, c0, c1, [letras de], letra para)  troca de cor num retângulo (os dois tamanhos, escalado)
  ('soften', (r0, r1, c0, c1), letra, min_pale)   conta PRETA do INTERIOR (sem vazio em volta) cercada por >= min_pale vizinhas claras (w i l x) vira `letra` (cinza claro `l`): traço fino entre mechas de cabelo
                                      branco virava pontinho preto (Emilia, Jiraiya, Toshiro); olho e contorno externo não mudam (vizinhança de pele / encosta no vazio)
  ('func', fn)                        fn(g, sx, sy) altera a grade (lista de listas) no lugar; sx, sy = escala do molde em relação ao de 1 placa (1.0 no de 1 placa): desenhos geométricos (círculo de transmutação)
  ('smooth', região, letras, passes)  tira conta ISOLADA (< 2 vizinhas iguais nas 8) das `letras` quando >= 3 vizinhas (também das `letras`) são de uma letra só: cabelo/fogo/aura com pontilhado
  ('desat', região, letras_de|None, letras_para[, viés de luminosidade])   cada conta das `letras_de` vira a das `letras_para` de luminosidade mais próxima (azul-acinzentado do cabelo prateado -> cinzas H)
  ('ramp', região, fonte, letras_de|None, rampa, passes)   relê a cor média (sem o contorno escuro) da fonte nas contas `letras_de` e escolhe a letra mais próxima SÓ dentro da `rampa` (lista de letras):
                                      degradê de fogo/gelo/energia com poucos degraus; depois `smooth` nas letras da rampa
  ('clean', params)                   beadclean.clean (pontas de 1 conta, halo, cor avulsa na borda) no molde todo
  ('frame', grossura, [letras de fora p/ dentro], letra_do_fundo, margem)   moldura de quadro em volta e fundo liso atrás da figura
  ('eye', região, fonte, rgb_da_íris, tol, modelo, letras, minpx)   acha as MANCHAS da cor da íris na fonte (dentro da região, em contas), pega o centro de cada uma e CARIMBA o `modelo`
                                      (lista de textos; ' ' = não mexe; I = íris, J = íris clara, P = pupila, H = brilho + as letras comuns k/w) centrado ali. Os olhos ficam na posição certa sem eu ler a grade.
  ('stamp', (lin, col), modelo, letras[, espelhar])   carimba o modelo com o CENTRO em (lin, col) (decimais, em contas do 1-placa: a conta n ocupa [n, n+1)); no irmão grande o modelo dobra de tamanho
  ('lg',)                              mantém só a maior peça e apara (tira o que ficou solto depois do wipe)
  ('boost', (r0, r1, c0, c1), (remessa, idx, box), regras [, kw do align])   RELÊ a fonte célula a célula na região com limiar menor: cada regra = {'rgb': (r,g,b), 'tol': 80, 'frac': 0.12, 'letter': 'r'} (a cor "conta" se
                                      está a `tol` de distância RGB do alvo; a conta ganha a letra se ≥ `frac` da janela é daquela cor; 1ª regra que vale ganha) ou {'black': 60, ...} (max(R,G,B) < 60).
                                      Serve para íris pequenas (olho vermelho do Alucard, lente laranja, olho âmbar da C.C.) que o voto por maioria do convert5 apaga. Vale nos dois tamanhos (região escalada).
`fx('chave', big)` devolve a função para o CFG. A dimensão do molde de 1 placa para a qual as coordenadas valem fica em `BASE[chave]` (conferida: se mudar, o conserto avisa)."""
import numpy as np
import cv2
import outline as O
import palette as P

NEUT = set('kwilmdhMZ') | {c['letter'] for c in P.ALL if c['code'] in ('H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11')}
CODE2L = {c['code']: c['letter'] for c in P.ALL}

FIX = {}      # chave -> (dimensões base (W, H) do molde de 1 placa, [operações])


def _scale(r0, r1, c0, c1, W, H, Wb, Hb):
    if (W, H) == (Wb, Hb): return r0, r1, c0, c1
    sy, sx = H / float(Hb), W / float(Wb)
    return int(np.floor(r0 * sy)), int(np.ceil((r1 + 1) * sy)) - 1, int(np.floor(c0 * sx)), int(np.ceil((c1 + 1) * sx)) - 1


def apply(rows, ops, base, big=False):
    g = [list(r) for r in rows]; H, W = len(g), len(g[0]); Wb, Hb = base
    if not big and (W, H) != (Wb, Hb): print('  AVISO: molde %dx%d, o conserto foi escrito para %dx%d' % (W, H, Wb, Hb))
    for op in ops:
        k = op[0]
        if k == 'wipe':
            r0, r1, c0, c1 = _scale(op[1], op[2], op[3], op[4], W, H, Wb, Hb)
            only = op[5] if len(op) > 5 else None
            for y in range(max(0, r0), min(H, r1 + 1)):
                for x in range(max(0, c0), min(W, c1 + 1)):
                    if g[y][x] == '.': continue
                    if only == 'neutral' and g[y][x] not in NEUT: continue
                    g[y][x] = '.'
        elif k == 'func':
            op[1](g, W / float(Wb), H / float(Hb))
        elif k == 'recolor':
            r0, r1, c0, c1 = _scale(op[1], op[2], op[3], op[4], W, H, Wb, Hb)
            frm = set(op[5]); to = op[6]
            for y in range(max(0, r0), min(H, r1 + 1)):
                for x in range(max(0, c0), min(W, c1 + 1)):
                    if g[y][x] in frm: g[y][x] = to
        elif k == 'soften':
            (r0, r1, c0, c1), to, mp = op[1], op[2], op[3]
            r0, r1, c0, c1 = _scale(r0, r1, c0, c1, W, H, Wb, Hb)
            pale = set('wilxM') | {CODE2L[c] for c in ('H1', 'H2', 'H3', 'D9')}
            old = [r[:] for r in g]
            for y in range(max(0, r0), min(H, r1 + 1)):
                for x in range(max(0, c0), min(W, c1 + 1)):
                    if old[y][x] != 'k': continue
                    nb = [old[yy][xx] if 0 <= yy < H and 0 <= xx < W else '.' for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1) if (yy, xx) != (y, x)]
                    if '.' in nb: continue
                    if sum(1 for c in nb if c in pale) >= mp: g[y][x] = to
        elif k == 'smooth':
            (r0, r1, c0, c1), letters = _scale(op[1][0], op[1][1], op[1][2], op[1][3], W, H, Wb, Hb), (set(op[2]) if op[2] is not None else None); passes = op[3] if len(op) > 3 else 2
            _smooth(g, r0, r1, c0, c1, letters, passes)
        elif k == 'desat':
            r0, r1, c0, c1 = _scale(op[1][0], op[1][1], op[1][2], op[1][3], W, H, Wb, Hb)
            _desat(g, r0, r1, c0, c1, (set(op[2]) if op[2] is not None else None), list(op[3]), op[4] if len(op) > 4 else 0.0)
        elif k == 'ramp':
            _ramp(g, op, W, H, Wb, Hb)
        elif k == 'clean':
            import beadclean
            kw = op[1] if len(op) > 1 else {}
            g = [list(r) for r in beadclean.clean([''.join(r) for r in g], **kw)]; H, W = len(g), len(g[0])
        elif k == 'frame':
            g = _frame(g, op[1], op[2], op[3], op[4] if len(op) > 4 else 1, big); H, W = len(g), len(g[0])
        elif k == 'eye':
            _eye(g, op, W, H, Wb, Hb)
        elif k == 'stamp':
            _stamp(g, op, W, H, Wb, Hb)
        elif k == 'boost':
            _boost(g, op, W, H, Wb, Hb)
        elif k == 'lg':
            g = [list(r) for r in _largest([''.join(r) for r in g])]; H, W = len(g), len(g[0])
        elif big: continue
        elif k == 'put':
            for (y, x), ch in op[1].items():
                if 0 <= y < H and 0 <= x < W: g[y][x] = ch
        elif k == 'blocks':
            leg = op[2] if len(op) > 2 else {}
            for y0, x0, lines in op[1]:
                for j, ln in enumerate(lines):
                    for i, ch in enumerate(ln):
                        if ch == ' ': continue
                        y, x = y0 + j, x0 + i
                        if not (0 <= y < H and 0 <= x < W): raise ValueError('bloco fora do molde: %s' % ((y, x),))
                        g[y][x] = '.' if ch == '.' else (CODE2L[leg[ch]] if ch in leg else ch)
    return [''.join(r) for r in g]


_RAW = {}; _GEO = {}


def _boost(g, op, W, H, Wb, Hb):
    """relê a fonte conta a conta na região. Regra {'rgb'|'black', 'tol', 'frac', 'letter'[, 'minpx']}: com `minpx` ('auto' = 0,4 conta) só vale o que pertence a uma MANCHA conexa da cor com pelo menos
    esse nº de pixels (íris de verdade; ignora pixels soltos de sombra de cabelo/pele com cor parecida)"""
    import facetools as FT
    (r0, r1, c0, c1), src, rules = op[1], op[2], op[3]
    akw = op[4] if len(op) > 4 else {}
    if src not in _RAW: _RAW[src] = FT.src_raw(*src)
    raw = _RAW[src]
    key = (src, W, H)
    if key not in _GEO: _GEO[key] = FT.align(raw, [''.join(r) for r in g], verbose=False, **akw)
    ox, oy, cw, ch = _GEO[key]
    r0, r1, c0, c1 = _scale(r0, r1, c0, c1, W, H, Wb, Hb)
    r0, c0 = max(0, r0), max(0, c0); r1, c1 = min(H - 1, r1), min(W - 1, c1)
    rf = raw.astype(np.int32)
    ya0, yb0 = int(oy + r0 * ch), int(oy + (r1 + 1) * ch); xa0, xb0 = int(ox + c0 * cw), int(ox + (c1 + 1) * cw)
    ya0, xa0 = max(0, ya0), max(0, xa0)
    sub = rf[ya0:yb0, xa0:xb0]
    masks = {}
    for i, rule in enumerate(rules):
        if 'minpx' not in rule or sub.size == 0: continue
        m = (sub.max(axis=2) < rule['black']) if 'black' in rule else (np.linalg.norm(sub - np.array(rule['rgb']), axis=2) < rule.get('tol', 80))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
        need = (0.4 * cw * ch) if rule['minpx'] == 'auto' else rule['minpx']
        keep = np.zeros(n, bool)
        if n > 1: keep[1:] = st[1:, 4] >= need
        masks[i] = keep[lab]
    for y in range(r0, r1 + 1):
        for x in range(c0, c1 + 1):
            ya, yb = int(oy + y * ch), int(oy + (y + 1) * ch); xa, xb = int(ox + x * cw), int(ox + (x + 1) * cw)
            win = rf[max(0, ya):max(0, yb), max(0, xa):max(0, xb)]
            if win.size == 0: continue
            pix = win.reshape(-1, 3)
            for i, rule in enumerate(rules):
                if i in masks:
                    mm = masks[i][max(0, ya) - ya0:max(0, yb) - ya0, max(0, xa) - xa0:max(0, xb) - xa0]
                    hit = mm.reshape(-1) if mm.size else np.zeros(1, bool)
                elif 'black' in rule: hit = (pix.max(axis=1) < rule['black'])
                else: hit = (np.linalg.norm(pix - np.array(rule['rgb']), axis=1) < rule.get('tol', 80))
                if hit.mean() >= rule['frac']:
                    if g[y][x] != '.' or rule.get('fill'): g[y][x] = rule['letter']
                    break



def _lab_of_letter():
    import illus
    return {c['letter']: illus._lab(np.array([int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)) for c in P.ALL}


def _smooth(g, r0, r1, c0, c1, letters, passes=2):
    from collections import Counter
    H, W = len(g), len(g[0])
    for _ in range(passes):
        old = [r[:] for r in g]
        for y in range(max(0, r0), min(H, r1 + 1)):
            for x in range(max(0, c0), min(W, c1 + 1)):
                c = old[y][x]
                if c == '.' or (letters is not None and c not in letters): continue
                nb = [old[yy][xx] for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2) if (yy, xx) != (y, x) and 0 <= yy < H and 0 <= xx < W and old[yy][xx] != '.' and (letters is None or old[yy][xx] in letters)]
                if len(nb) < 4 or sum(1 for n in nb if n == c) >= 2: continue
                top, cnt = Counter(nb).most_common(1)[0]
                if top != c and cnt >= 3: g[y][x] = top


def _bluish_letters():
    import colorsys
    out = set()
    for c in P.ALL:
        r, g_, b = [int(c['hex'].lstrip('#')[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        h, s_, v = colorsys.rgb_to_hsv(r, g_, b)
        if 190 <= h * 360 <= 275 and s_ >= 0.08 and v >= 0.35: out.add(c['letter'])
    return out


def _desat(g, r0, r1, c0, c1, frm, to, bias=0.0):
    LL = _lab_of_letter()
    if frm is None: frm = _bluish_letters()
    for y in range(max(0, r0), min(len(g), r1 + 1)):
        for x in range(max(0, c0), min(len(g[0]), c1 + 1)):
            c = g[y][x]
            if c in frm: g[y][x] = min(to, key=lambda t: abs(LL[t][0] - (LL[c][0] + bias)))


def _ramp(g, op, W, H, Wb, Hb):
    import facetools as FT, illus
    (r0, r1, c0, c1), src, frm, ramp = op[1], op[2], op[3], list(op[4]); passes = op[5] if len(op) > 5 else 1
    frm = set(frm) if frm else None
    r0, r1, c0, c1 = _scale(r0, r1, c0, c1, W, H, Wb, Hb)
    if src not in _RAW: _RAW[src] = FT.src_raw(*src)
    raw = _RAW[src]; key = (src, W, H)
    if key not in _GEO: _GEO[key] = FT.align(raw, [''.join(r) for r in g], verbose=False)
    ox, oy, cw, ch = _GEO[key]; LL = _lab_of_letter()
    for y in range(max(0, r0), min(H, r1 + 1)):
        for x in range(max(0, c0), min(W, c1 + 1)):
            if g[y][x] == '.' or (frm and g[y][x] not in frm): continue
            win = raw[int(oy + y * ch):int(oy + (y + 1) * ch), int(ox + x * cw):int(ox + (x + 1) * cw)].reshape(-1, 3).astype(float)
            if not len(win): continue
            lit = win[(win.max(axis=1) >= 90) & (win.min(axis=1) < 232)]          # sem o contorno escuro e sem o branco do fundo (o halo do antisserrilhado clareava o fogo)
            if len(lit) < 0.2 * len(win): continue
            lab = illus._lab(lit.mean(axis=0))
            g[y][x] = min(ramp, key=lambda t: float(np.linalg.norm(LL[t] - lab)))
    if passes: _smooth(g, r0, r1, c0, c1, set(ramp), passes)


def _frame(g, thick, layers, bg, margin, big):
    """moldura de quadro: `thick` contas de grossura (letras de fora para dentro em `layers`, repetidas por camada) + `margin` contas de fundo `bg` entre a moldura e a figura;
    o fundo também preenche os vãos da figura (cantos do escudo). No irmão grande a grossura e a margem dobram."""
    H, W = len(g), len(g[0]); k = 2 if big else 1
    t = thick * k; m = margin * k; pad = t + m
    nh, nw = H + 2 * pad, W + 2 * pad
    out = [['.'] * nw for _ in range(nh)]
    for y in range(nh):
        for x in range(nw):
            d = min(y, x, nh - 1 - y, nw - 1 - x)
            if d < t: out[y][x] = layers[min(d // k, len(layers) - 1)]
            else: out[y][x] = bg
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.': out[y + pad][x + pad] = g[y][x]
    return out


def _stamp_at(g, cy, cx, tmpl, letters, k=1, dy=0, dx=0, flip=False):
    """carimba `tmpl` (lista de textos; ' ' = não mexe) com o centro em (cy, cx) em unidades de conta (a conta n ocupa [n, n+1)); k = ampliação do modelo (irmão grande = 2)"""
    H, W = len(g), len(g[0])
    t = [row[::-1] for row in tmpl] if flip else list(tmpl)
    if k > 1: t = [''.join(ch * k for ch in row) for row in t for _ in range(k)]
    th, tw = len(t), max(len(r) for r in t)
    y0 = int(round(cy - th / 2.0)) + dy; x0 = int(round(cx - tw / 2.0)) + dx
    for j, row in enumerate(t):
        for i, chx in enumerate(row):
            if chx == ' ': continue
            y, x = y0 + j, x0 + i
            if 0 <= y < H and 0 <= x < W: g[y][x] = letters.get(chx, chx)


def _eye(g, op, W, H, Wb, Hb):
    import facetools as FT
    (r0, r1, c0, c1), src, rgb, tol, tmpl, letters = op[1], op[2], op[3], op[4], op[5], op[6]
    minpx = op[7] if len(op) > 7 else 'auto'
    flip = op[8] if len(op) > 8 else ()                  # índices (0 = o mais à esquerda) dos olhos que devem sair ESPELHADOS (brilho do outro lado)
    top = op[9] if len(op) > 9 else 0                    # só as `top` maiores manchas (sobrancelha e sombra da mesma cor da íris ficam de fora)
    dy = op[10] if len(op) > 10 else 0; dx = op[11] if len(op) > 11 else 0      # deslocamento do carimbo em contas (no grande, em contas do 1-placa: dobram)
    if src not in _RAW: _RAW[src] = FT.src_raw(*src)
    raw = _RAW[src]; key = (src, W, H)
    if key not in _GEO: _GEO[key] = FT.align(raw, [''.join(r) for r in g], verbose=False)
    ox, oy, cw, ch = _GEO[key]
    k = max(1, int(round((W / float(Wb) + H / float(Hb)) / 2.0)))
    r0, r1, c0, c1 = _scale(r0, r1, c0, c1, W, H, Wb, Hb)
    r0, c0 = max(0, r0), max(0, c0); r1, c1 = min(H - 1, r1), min(W - 1, c1)
    ya0, yb0, xa0, xb0 = max(0, int(oy + r0 * ch)), int(oy + (r1 + 1) * ch), max(0, int(ox + c0 * cw)), int(ox + (c1 + 1) * cw)
    sub = raw[ya0:yb0, xa0:xb0].astype(np.int32)
    m = (np.linalg.norm(sub - np.array(rgb), axis=2) < tol).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    need = (0.5 * cw * ch) if minpx == 'auto' else minpx * k * k
    cand = [(st[i][4], cen[i][0], cen[i][1]) for i in range(1, n) if st[i][4] >= need]
    if top: cand = sorted(cand, reverse=True)[:top]
    blobs = sorted([(cx_, cy_) for _, cx_, cy_ in cand])
    for k_, (cx, cy) in enumerate(blobs):
        _stamp_at(g, (cy + ya0 - oy) / ch, (cx + xa0 - ox) / cw, tmpl, letters, k, dy * k, dx * k, k_ in flip)
    return len(blobs)


def _stamp(g, op, W, H, Wb, Hb):
    """('stamp', (linha, coluna) do CENTRO em contas do 1-placa (decimais valem), modelo, letras[, espelhar]) : olho/boca desenhado à mão no ponto certo, nos dois tamanhos"""
    (cy, cx), tmpl, letters = op[1], op[2], op[3]
    flip = op[4] if len(op) > 4 else False
    sx, sy = W / float(Wb), H / float(Hb); k = max(1, int(round((sx + sy) / 2.0)))
    _stamp_at(g, cy * sy, cx * sx, tmpl, letters, k, 0, 0, flip)



def _largest(rows):
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1: return rows
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return O.trim([''.join(c if lab[y, x] == big else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)])


def fx(key, big=False):
    """gancho para o CFG: função(linhas) -> linhas. Lê FIX[key] só na hora de usar (dá para editar o dicionário sem recarregar)."""
    def f(rows):
        if key not in FIX: return rows
        base, ops = FIX[key]
        return apply(rows, ops, base, big)
    return f


# ---------------------------------------------------------------- Inazuma Eleven (folha 66 da remessa 22): restos do texto em katakana que o strip_text deixou colados no desenho
FIX['gouenji'] = ((44, 49), [
    ('wipe', 11, 11, 0, 5), ('wipe', 12, 13, 0, 6), ('wipe', 14, 17, 0, 5), ('wipe', 18, 19, 0, 7),      # "ファイア" (a coluna 6 é o contorno do cabelo)
    ('wipe', 20, 27, 0, 8, 'neutral'), ('wipe', 28, 30, 0, 8), ('wipe', 27, 29, 12, 13),
    ('wipe', 6, 20, 32, 43),                                                                            # "トルネード" (o cabelo termina na coluna 30)
    ('wipe', 21, 27, 38, 43, 'neutral'),
    ('lg',)])
FIX['fubuki'] = ((46, 42), [
    ('wipe', 3, 9, 11, 16, 'neutral'), ('wipe', 21, 25, 41, 45, 'neutral'),
    ('recolor', 9, 24, 21, 36, ['w', 'i'], CODE2L['E11']),                                    # o rosto é pele clara (253,235,225), não branco
    ('blocks', [(15, 22, [' kk ', 'kEkk', 'kEkk', 'kEkk', ' kk ']),                           # olho esquerdo: dourado com pupila em fenda
                (16, 29, [' kkk ', 'kEkEk', 'kEkEk', 'kEkEk', ' kkk '])]),                    # olho direito
    ('lg',)])
FIX['mugen'] = ((47, 47), [
    ('wipe', 37, 46, 0, 9, 'neutral'), ('wipe', 41, 46, 0, 46), ('lg',)])
FIX['kazemaru'] = ((50, 40), [
    ('wipe', 20, 29, 32, 42, 'neutral'), ('wipe', 30, 37, 7, 17, 'neutral'), ('lg',)])


# ---------------------------------------------------------------- Alucard (remessa 23)
FIX['alucard_sentado'] = ((36, 49), [
    ('boost', (16, 25, 10, 27), (23, 4, None), [{'rgb': (210, 15, 15), 'tol': 120, 'frac': 0.06, 'letter': 'r'}])])

FIX['alucard_pistolas'] = ((45, 50), [
    ('blocks', [(16, 16, [' kkkk ', 'koowyk', 'koywyk', 'kywwwk', 'kwywwk', ' kkkk ']),         # lente esquerda: aro preto, laranja em cima à esquerda e riscos amarelos
                (16, 26, [' kkkk ', 'koowyk', 'koywyk', 'kywwwk', 'kwywwk', ' kkkk ']),         # lente direita
                (23, 20, [' kkkkk ', 'kwwwwwk', ' kwwwk '])])])                                  # sorriso de dentes
FIX['alucard_adesivo'] = ((49, 44), [
    ('blocks', [(14, 19, ['kkkk', 'wRkw', ' kk ']), (14, 26, ['kkkk', 'wkRw', ' kk ']),             # olhos: pálpebra preta, esclera nas pontas, íris laranja-avermelhada, pupila
                (17, 20, ['kkkkkkkkk']), (18, 21, ['wwwwwww']), (19, 21, ['kwkkkwk'])],             # sorriso com as duas presas
     {'R': 'F4'})])

# ---------------------------------------------------------------- Emilia (remessa 23): cabelo/vestido brancos com traços finos que viravam pontos pretos
FIX['emilia'] = ((34, 50), [
    ('soften', (0, 49, 0, 33), 'l', 5),
    ('boost', (13, 24, 11, 27), (23, 12, None), [{'rgb': (125, 85, 185), 'tol': 90, 'frac': 0.07, 'letter': '?'}])])

# ---------------------------------------------------------------- Toshiro e Jiraiya (remessa 22): cabelo branco com traços finos
FIX['toshiro'] = ((37, 50), [('soften', (0, 49, 0, 36), 'l', 5)])
FIX['jiraiya'] = ((33, 48), [('soften', (0, 47, 0, 32), 'l', 5)])

# ---------------------------------------------------------------- C.C. (remessa 23): olhos âmbar grandes que o contorno preto e a pupila engoliam
_AMB = [{'rgb': (225, 170, 60), 'tol': 70, 'frac': 0.18, 'letter': 'a'}, {'rgb': (120, 75, 35), 'tol': 60, 'frac': 0.22, 'letter': 'n'},
        {'rgb': (255, 255, 255), 'tol': 25, 'frac': 0.50, 'letter': 'w'}]
FIX['cc_chibi'] = ((49, 48), [('boost', (15, 21, 12, 34), (23, 14, None), _AMB)])

# ---------------------------------------------------------------- Hibari (remessa 23): rosto branco sem olhos (os olhos são finos e cinza-azulados sob a franja preta)
FIX['hibari'] = ((29, 49), [('blocks', [(14, 15, ['kkkkk', 'wmkmk', ' mkm ']), (15, 8, ['wwkk', 'wmkk'])])])

# ---------------------------------------------------------------- Shikamaru (remessa 22): olhos de pálpebra pesada que o contorno e a fumaça pretos engoliam
FIX['shikamaru'] = ((37, 50), [
    ('blocks', [(14, 13, [' kkkk', 'wkkk ']), (15, 19, ['kkkk']), (16, 19, ['kkkkk']), (17, 19, ['wkkk '])])])

# ---------------------------------------------------------------- Muzan e Itachi (remessa 22): figura preta com olhos vermelhos pequenos
_RED = [{'rgb': (205, 30, 40), 'tol': 75, 'frac': 0.25, 'letter': 'r'}]
FIX['muzan'] = ((39, 50), [('boost', (19, 22, 14, 25), (22, 24, None), _RED)])
FIX['itachi_corvos'] = ((28, 49), [('boost', (17, 22, 12, 20), (22, 50, None), _RED)])
FIX['itachi_corvo'] = ((31, 50), [('boost', (23, 28, 13, 22), (22, 70, None), _RED), ('boost', (8, 13, 13, 27), (22, 70, None), _RED)])


# ---------------------------------------------------------------- Luva de Roy Mustang (remessa 23): o círculo de transmutação virava uma mancha rosa
def _luva_circle(g, sx, sy):
    import math
    brown = CODE2L['F11']
    H, W = len(g), len(g[0])
    cy, cx = 11.0 * sy, 33.0 * sx; R = 6.0 * (sx + sy) / 2

    def put(y, x):
        y, x = int(round(y)), int(round(x))
        if 0 <= y < H and 0 <= x < W and g[y][x] != '.': g[y][x] = brown
    n = int(60 * (sx + sy) / 2)
    big = (sx + sy) / 2 > 1.5                                               # no molde de 1 placa o círculo tem 13 contas de diâmetro: só o aro externo e a estrela (com 2 aros virava um disco marrom)
    for i in range(n):                                                     # aro externo (1 conta) e, no grande, o aro interno do anel de glifos
        a = 2 * math.pi * i / n
        for rr in ((R, R * 0.80) if big else (R,)):
            put(cy + rr * math.sin(a), cx + rr * math.cos(a))
    kr = 0.68 if big else 0.55
    pts = [(cy + R * kr * math.sin(math.radians(-90 + 72 * k)), cx + R * kr * math.cos(math.radians(-90 + 72 * k))) for k in range(5)]
    for k in range(5):                                                     # estrela de 5 pontas (cada vértice liga ao 2º seguinte)
        (y0, x0), (y1, x1) = pts[k], pts[(k + 2) % 5]
        m = int(max(abs(y1 - y0), abs(x1 - x0)) * 2) + 1
        for j in range(m + 1): put(y0 + (y1 - y0) * j / m, x0 + (x1 - x0) * j / m)


FIX['luva'] = ((47, 47), [('func', _luva_circle)])

# ---------------------------------------------------------------- Yuuto Kidou (remessa 22): as duas lentes redondas dos óculos viravam uma faixa preta
_GOGGLE = [' kkk ', 'kdwdk', 'kdddk', 'kdddk', ' kkk ']
FIX['kidou'] = ((43, 46), [('blocks', [(21, 10, _GOGGLE), (20, 19, _GOGGLE)])])
