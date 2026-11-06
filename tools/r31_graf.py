"""Remessa 31: gráficos, pixel art, ponto-cruz e fotos de peça pronta = cópia 100% FIEL (CLAUDE.md §4.1). Importado pelo r31_exfinal.py (items(X) devolve as entradas do CFG).
O número escrito em cada quadradinho é o GABARITO da conta (pedido do dono, §7.37): nos gráficos MARD com código em cada célula (Sanji 38, Optimus Prime 125) cada célula é lida pelo
OCR (RapidOCR, o modelo já vem no pacote; célula por célula, com o texto separado do fundo pelo desvio da cor dominante) e a atribuição final respeita EXATAMENTE as contagens por
código impressas na legenda (algoritmo húngaro: custo = distância de cor ao modelo do código, bônus se o OCR leu aquele código, multa se leu outro da legenda).
Cada código vira a conta do kit mais parecida com a COR do gráfico (o mesmo código MARD é outra cor no kit Pindou, §7.29)."""
import os, sys, re, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image

_ENG = []


def _engine():
    if not _ENG:
        import logging; logging.disable(logging.CRITICAL)
        from rapidocr import RapidOCR
        _ENG.append(RapidOCR())
    return _ENG[0]


_CONF = {'O': '0', 'D': '0', 'Q': '0', 'I': '1', 'L': '1', '|': '1', 'S': '5', 'B': '8', 'Z': '2', 'G': '6', 'T': '1'}


def canon(t):
    t = re.sub(r'[^A-Za-z0-9|]', '', t).upper()
    return ''.join(_CONF.get(ch, ch) for ch in t)


def cell_text(im, grid, r, c, S=10, margin=1.6):
    """texto da célula (r, c): o que se desvia da cor dominante vira tinta escura sobre fundo claro, ampliado e lido pelo OCR (só reconhecimento)"""
    x0 = grid['ox'] + c * grid['px']; y0 = grid['oy'] + r * grid['py']
    xa, xb = int(round(x0 + margin)), int(round(x0 + grid['px'] - margin)); ya, yb = int(round(y0 + margin)), int(round(y0 + grid['py'] - margin))
    if yb <= ya or xb <= xa: return ''
    sub = im[ya:yb, xa:xb].astype(np.float32)
    q = (sub // 12).reshape(-1, 3).astype(int); keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True)
    dom = sub.reshape(-1, 3)[keys == vals[np.argmax(cnt)]].mean(axis=0)
    d = np.linalg.norm(sub - dom, axis=2); d = d / max(40.0, d.max())
    g = (255 * (1 - np.clip(d, 0, 1))).astype(np.uint8)
    g = cv2.resize(g, (g.shape[1] * S, g.shape[0] * S), interpolation=cv2.INTER_CUBIC)
    g = np.pad(g, ((10, 10), (16, 16)), constant_values=255)
    res = _engine()(cv2.cvtColor(g, cv2.COLOR_GRAY2RGB), use_det=False, use_cls=False, use_rec=True)
    return ''.join(res.txts) if res.txts else ''


def _lab2rgb(lab):
    """inverso do illus._lab (Lab D65 padrão) -> RGB 0-255"""
    L, a, b = [float(v) for v in lab]
    fy = (L + 16.0) / 116.0; fx = fy + a / 500.0; fz = fy - b / 200.0
    def finv(t): return t ** 3 if t ** 3 > 0.008856 else (t - 16.0 / 116.0) / 7.787
    xyz = np.array([finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883])
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    lin = np.clip(np.linalg.inv(M) @ xyz, 0.0, 1.0)
    c = np.where(lin > 0.0031308, 1.055 * lin ** (1 / 2.4) - 0.055, 12.92 * lin)
    return tuple(int(round(float(np.clip(v, 0, 1)) * 255)) for v in c)


def mard_graph(X, idx, grid, legend, name='', chips=None, fix=None, verbose=True, dbg=None, iters=3):
    """gráfico com código em cada célula e legenda 'COD:n' (a mesma da tools/legend_check.py). Devolve as linhas (sem reduzir: o fin() do r31_exfinal reduz para 1 placa).
    Cada célula é um dos códigos da legenda ou VAZIA; a atribuição é a de custo mínimo (algoritmo húngaro) com a CAPACIDADE de cada código = a contagem impressa e a de vazio = o resto
    da grade. O modelo de cor de cada código começa nas células que o OCR leu certo (mediana) ou, se nenhuma, na cor da amostra da legenda, e é refeito a cada rodada."""
    import r6, illus, r5
    from scipy.optimize import linear_sum_assignment
    im = np.array(X.R.source_img(idx)).astype(np.uint8)
    arr = r6.load_cells(idx, px=grid, mode=True)
    H, W, _ = arr.shape
    codes = [t.split(':') for t in legend.split()]; want = collections.OrderedDict((c, int(n)) for c, n in codes)
    lex = list(want); total = sum(want.values()); ncell = H * W
    canon_lex = collections.defaultdict(list)
    for c in lex: canon_lex[canon(c)].append(c)
    texts = {(r, c): cell_text(im, grid, r, c) for r in range(H) for c in range(W)}

    def match(t):
        ct = canon(t)
        if ct in canon_lex and len(canon_lex[ct]) == 1: return canon_lex[ct][0]
        return None
    prov = {k: match(t) for k, t in texts.items()}
    lab = illus._lab(arr.astype(np.float32)).reshape(-1, 3)
    keys = [(r, c) for r in range(H) for c in range(W)]
    model = {}
    for code in lex:
        pts = [lab[i] for i, k in enumerate(keys) if prov[k] == code]
        if len(pts) >= 3: model[code] = np.median(np.array(pts), axis=0)
    if chips is None:
        try:
            sw = X.R.legend_swatches(idx, int(grid['oy'] + grid['H'] * grid['py'] + 35), len(lex)); chips = dict(zip(lex, sw)) if len(sw) == len(lex) else {}
        except Exception: chips = {}
    for code in lex:
        if code not in model and code in chips: model[code] = illus._lab(np.array(chips[code], np.float32).reshape(1, 1, 3)).reshape(3)
    lightc = [i for i, k in enumerate(keys) if prov[k] is None and arr[k].min() >= 200]
    model['.'] = np.median(lab[lightc], axis=0) if lightc else illus._lab(np.array([255, 255, 255], np.float32).reshape(1, 1, 3)).reshape(3)
    cap = dict(want); cap['.'] = ncell - total
    if cap['.'] < 0: print('  AVISO: a legenda soma mais contas do que a grade tem'); cap['.'] = 0
    names = [c for c in lex if c in model] + ['.']
    assign = None; D = None
    for it in range(iters):
        cols = []
        for c in names: cols += [c] * cap[c]
        D = np.stack([np.linalg.norm(lab - model[c], axis=1) for c in names], axis=1)        # célula x código
        Dc = D.copy()
        for i, k in enumerate(keys):
            pk = prov[k]
            if pk in names:
                Dc[i, :] += 5.0; Dc[i, names.index(pk)] -= 12.0                           # o OCR leu esse código: bônus nele e multa nos outros
        if len(cols) < ncell:
            extra = ncell - len(cols); cols += ['.'] * extra
        elif len(cols) > ncell:
            cols = cols[:ncell]
        cost = np.stack([Dc[:, names.index(c)] for c in cols], axis=1)
        ri, cj_ = linear_sum_assignment(cost)
        assign = {keys[i]: cols[j] for i, j in zip(ri, cj_)}
        for c in names:
            pts = [lab[i] for i, k in enumerate(keys) if assign[k] == c]
            if pts and c != '.': model[c] = np.median(np.array(pts), axis=0)
    got = {k: v for k, v in assign.items() if v != '.'}
    for (lin, col), code in (fix or {}).items():
        if code == '.': got.pop((lin, col), None)
        else: got[(lin, col)] = code
    cnt = collections.Counter(got.values())
    diff = [f'{c}:{cnt.get(c, 0)}/{n}' for c, n in want.items() if cnt.get(c, 0) != n]
    nearest = {k: names[int(np.argmin(D[i]))] for i, k in enumerate(keys)}
    sus = [(k, prov[k], got.get(k, '.'), texts[k]) for k in keys if prov[k] is not None and prov[k] != got.get(k, '.')]
    off = [k for k in keys if got.get(k, '.') != nearest[k]]
    miss = [c for c in lex if c not in model]
    if verbose:
        print(f'  [{name}] {W}x{H} células; {len(got)} contas (legenda {total}); OCR certo em {sum(1 for v in prov.values() if v)} células; {len(sus)} onde o OCR leu um código e a atribuição pôs outro; {len(off)} células fora do código de cor mais próximo; contagens '
              + ('IGUAIS à legenda' if not diff else 'DIFERENTES (obtido/legenda): ' + ' '.join(diff)) + (f'; sem modelo de cor: {miss}' if miss else ''))
    if dbg is not None: dbg.update(got=got, sus=sus, texts=texts, prov=prov, model=model, want=want, diff=diff, off=off, nearest=nearest, names=names)
    letters = {}
    for code in lex:
        if code not in model: continue
        letters[code] = r5.near120(_lab2rgb(model[code]), skin=False)
    if verbose: print('    código→letra:', ' '.join(f'{c}={letters[c]}' for c in lex if c in letters))
    return [''.join(letters[got[(r, c)]] if (r, c) in got and got[(r, c)] in letters else '.' for c in range(W)) for r in range(H)]


def drop(letter_codes):
    """remove da molde as contas dessas letras (código do kit: 'H1'): fundo que vazou para dentro da figura"""
    def f(rows, L=None):
        from palette import ALL
        let = {c['letter'] for c in ALL if c['code'] in letter_codes}
        import outline as O
        return O.trim([''.join('.' if ch in let else ch for ch in r) for r in rows])
    return f

# cores das amostras das legendas (RGB), lidas nas bordas de cada ficha (o código escrito no meio não entra)
CHIPS38 = {'A5': (252, 226, 78), 'A7': (254, 148, 55), 'A8': (246, 222, 67), 'A12': (252, 190, 161), 'A13': (253, 204, 68), 'A20': (253, 214, 80), 'C29': (51, 71, 131), 'D10': (52, 27, 80), 'E7': (154, 5, 86), 'F3': (245, 74, 67), 'F7': (151, 26, 56), 'F11': (90, 34, 33), 'F19': (192, 69, 76), 'F20': (205, 147, 146), 'G7': (162, 110, 76), 'G8': (112, 62, 49), 'G9': (237, 189, 142), 'G11': (217, 205, 163), 'G14': (138, 101, 79), 'G21': (194, 145, 109), 'H7': (2, 2, 2), 'H14': (215, 222, 222), 'M1': (205, 214, 204), 'M4': (225, 208, 188), 'M9': (164, 134, 102)}
CHIPS125 = {'A26': (216, 187, 93), 'C6': (102, 160, 205), 'C10': (99, 181, 204), 'C20': (68, 126, 175), 'F8': (149, 30, 53), 'F15': (167, 58, 74), 'H3': (180, 180, 180), 'H7': (5, 3, 6), 'H10': (234, 229, 233), 'H20': (151, 155, 158)}


def items(X):
    """entradas do CFG (nome, série, índice, função, grupo) dos gráficos e fotos"""
    P = X.P; E = P.E; fin = X.fin; lg = X.lg; O = P.O
    out = []
    H1 = drop(('H1',)); H2 = drop(('H2',))

    def add(idx, name, serie, fn, grp='graf'): out.append((name, serie, idx, fn, grp))

    def G(i, **kw):
        post2 = kw.pop('post2', None)
        def f():
            kw2 = dict(kw); kw2.setdefault('mode', True)
            r = E(i, **kw2)
            if post2: r = post2(r)
            return fin(r)
        return f

    def M(i, grid, legend, chips=None, post2=None):
        def f():
            r = mard_graph(X, i, grid, legend, name=P.CUR[0], chips=chips)
            r = lg(r)
            if post2: r = post2(r)
            return fin(r)
        return f

    add(11, 'Chihiro (A Viagem de Chihiro, pixel)', 'Studio Ghibli', G(11, post=lg))
    add(19, 'Jessie (Toy Story, pixel)', 'Toy Story', G(19, post=lg))
    add(43, 'Grogu (Star Wars, pixel)', 'Star Wars', G(43, post=lg))
    add(45, 'Escudo da Sonserina (Harry Potter, pixel, cinza)', 'Harry Potter', G(45, post=lg))
    add(49, 'Escudo da Corvinal (Harry Potter, ponto-cruz)', 'Harry Potter', G(49, post=lg))
    add(60, 'Ceifador com foice (pixel, ponto-cruz)', 'Halloween', G(60, px=dict(px=44.40, py=44.40, ox=43.96, oy=45.01, W=25, H=28), post=lg))
    add(63, 'Edwiges (Harry Potter, pixel)', 'Harry Potter', G(63, post=lg))
    add(88, 'Escudo da Lufa-Lufa (Harry Potter, ponto-cruz)', 'Harry Potter', G(88, post=lg))
    add(96, 'Escudo da Sonserina (Harry Potter, ponto-cruz)', 'Harry Potter', G(96, post=lg))
    add(100, 'Garota de cabelo rosa e fones de ouvido (pixel)', 'Genéricos', G(100, post=lg))
    add(110, 'Frasco de poção roxa (ponto-cruz)', 'Genéricos', G(110, px=dict(px=18.02, py=18.03, ox=283.57, oy=690.31, W=24, H=28), mode=False, ring=(0.28, 0.48), post=lg))          # o símbolo de cada célula (quadradinho branco, ponto, estrela) fica no centro: amostra só o anel
    add(131, 'Escudo da Grifinória (Harry Potter, ponto-cruz)', 'Harry Potter', G(131, post=lg, post2=H2))          # 2 contas brancas soltas de brilho do fundo
    add(137, 'Woody (Toy Story, pixel)', 'Toy Story', G(137, crop_img=(0, 34, 829, 1098), ref=(215, 215, 215), tol=22, post=lg, post2=H1))          # a legenda diz 339 contas; 1 célula cinza do fundo vazava (H1)
    add(139, 'Buzz Lightyear (Toy Story, pixel)', 'Toy Story', G(139, crop_img=(0, 19, 564, 545), ref=(215, 215, 215), tol=22, post=lg, post2=H1))          # a legenda diz 356 contas
    add(80, 'Sakura Haruno (Naruto, pixel, em ação)', 'Naruto', G(80, px=dict(px=14.00, py=14.00, ox=13.10, oy=13.10, W=63, H=62), clear=[(57, 62, 50, 62)], colmap=[((96, 12, 23), 34, X.L['F7'])], post=lg))          # sprite "Ninja Pixel" (61x61 contas de 14 px): a marca do site (canto de baixo à direita) sai; acima de 50, o fin() tira linhas e colunas inteiras (fit50); o vinho da roupa (96,12,23) não existe no kit: o near120 dava o marrom G8, e o dono já reprovou carmim escuro virando marrom, então vai para o vinho F7
    add(38, 'Sanji (One Piece, pixel, perna em chamas)', 'One Piece',
        M(38, dict(px=13.92, py=13.84, ox=12.40, oy=51.89, W=51, H=49), 'A5:15 A7:45 A8:22 A12:8 A13:30 A20:13 C29:11 D10:82 E7:133 F3:42 F7:21 F11:111 F19:2 F20:9 G7:10 G8:23 G9:8 G11:51 G14:64 G21:4 H7:177 H14:1 M1:2 M4:1 M9:9', CHIPS38))
    add(125, 'Optimus Prime (Transformers, pixel)', 'Transformers',
        M(125, dict(px=16.92, py=16.91, ox=11.21, oy=13.90, W=42, H=53), 'A26:16 C6:26 C10:54 C20:314 F8:22 F15:184 H3:27 H7:606 H10:115 H20:20', CHIPS125))
    return out
