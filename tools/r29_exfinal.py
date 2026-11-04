"""Remessa 29 (106 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r29_exfinal.py [filtro...] [--grupo graf|cdz|ill|folha] [--merge] [--H 520] [--kw k=v,k=v] [--tag nome]
   -> data/final31_120.json (tudo em 1 placa, sem irmão grande). Reaproveita os auxiliares do r26_exfinal.py (que importa o r22_exfinal.py): o import aponta para a remessa 26 e a lista de arquivos é trocada aqui.
Classes (CLAUDE.md §4.1 e §4.8): 9 gráficos em malha / pixel art = cópia 100% fiel (só sai o fundo); o resto são ILUSTRAÇÕES (chibis e adesivos) = adaptação por illus5.convert5 em 1 placa (olhos discretos, sem boca desenhada).
Folhas com vários personagens: 6 (20 de My Hero Academia), 31 (9 de Black Clover), 69 (4 de My Hero Academia em fundo preto), 99 (6 chibis "fofos" de Cavaleiros), 91 (2 Rias); 97 (trio de Dan Da Dan) fica inteiro (as figuras se sobrepõem).
Repetidas por MD5 (entram, pedido do dono): 15, 49, 53, 60, 72, 88, 101, 105 (remessa 14), 61 (remessa 18), 65 (remessa 20); nome que já existe ou foi excluído ganha ", versão N" (veja uniq())."""
import os, sys, json, glob, colorsys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r26_exfinal as X
from r26_exfinal import r5, r6, O, np, R, G, E, F, L, LAB, OUT, fin, lg, holes, pieces, pale, peel_set, clearb, chain, vote, sfx, delc
import cv2
from PIL import Image
import darkramp as DR
import weak_cm as WC
import tplfile
F[:] = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa 29', '*.*')))          # F é a mesma lista de r6.FILES e R.F
CDZ = 'Cavaleiros do Zodíaco'
BG87 = (132, 52, 79)          # vinho do fundo do emblema (87)


# ---------------------------------------------------------------- cores (ganchos do convert5)
def CM_BLOND2(rgb, Lc, letter, is_black):
    """cabelo LOIRO / ouro claro (r23): o amarelo pálido caía na trava de pele do near120 e no pale_skin e virava rosa/pele: vai para o amarelo mais próximo SEM a trava"""
    h, sat, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); h *= 360
    if v >= 0.55 and ((40 <= h <= 66 and sat >= 0.12) or (32 <= h < 40 and sat >= 0.26)): return r5.near120(tuple(rgb), skin=False)
    return None


def CM29(rgb, Lc, letter, is_black): return CM_BLOND2(rgb, Lc, letter, is_black)          # sem o CM_PURPLE do r22: aqui o roxo escuro é a sombra de casaco/cabelo PRETO (Albedo, Mayuri, Megumin, casacos) e virava roxo vivo D14


CH = dict(K=24, dark_frac=0.30, black_L=12.0, thr=240, pale_skin=True, warm_white=7, seal=0.0, center_map=CM29)
KW_OVER = {}          # --kw na linha de comando (testes de variantes)

# ARMADURA DOURADA: o kit não tem dourado escuro; o near120 mandava o dourado de sombra (122,101,5) para o VERDE-OLIVA B11 e o meio-tom para M9/M6 (bege-oliva): a armadura saía salpicada de verde.
# Aqui todo centro dourado vira uma rampa curta de contas do kit pela claridade: amarelo A4 (ou A3 se pálido) -> âmbar G5 -> laranja G6 -> laranja-escuro G13 -> caramelo G7 -> marrom F11 (o contorno preto fica preto).
_GOLD_RAMP = [(78.0, 'A4'), (60.0, 'G5'), (44.0, 'G13'), (20.0, 'F11')]
_GOLD_RAMP6 = [(78.0, 'A4'), (60.0, 'G5'), (44.0, 'G13'), (9.0, 'F11')]          # convert6: a sombra funda do ouro (L 9-20) vira marrom-escuro, não preto (o preto fica só no traço)
GOLDS = {L[c] for c in ('A4', 'A3', 'G5', 'G9', 'G13', 'F11', 'G6', 'G7', 'A11', 'A13')}


def mode_family(rows, fam=None, iters=2, need=5):
    """filtro de MAIORIA 3x3 só entre as letras de uma família (dourados): conta da família vira a letra da família mais comum na janela 3x3 quando ela tem >= need votos;
    tira o salpicado de 2-3 tons do metal sem mexer no contorno, no rosto nem nas outras cores"""
    fam = fam or GOLDS
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    for _ in range(iters):
        g2 = [r[:] for r in g]
        for y in range(H):
            for x in range(W):
                if g[y][x] not in fam: continue
                cnt = {}
                for yy in range(max(0, y - 1), min(H, y + 2)):
                    for xx in range(max(0, x - 1), min(W, x + 2)):
                        c = g[yy][xx]
                        if c in fam: cnt[c] = cnt.get(c, 0) + 1
                best = max(cnt, key=cnt.get)
                if best != g[y][x] and cnt[best] >= need: g2[y][x] = best
        g = g2
    return [''.join(r) for r in g]


def CM_GOLD(rgb, Lc, letter, is_black):
    if is_black: return None
    h, s, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); h *= 360
    if (36 <= h <= 64 and s >= 0.45) or (26 <= h < 36 and s >= 0.62 and Lc >= 38):
        for lo, code in (_GOLD_RAMP6 if ENGINE[0] == 'c6' else _GOLD_RAMP):
            if Lc >= lo: return L['A3'] if (code == 'A4' and s < 0.6) else L[code]
        return None
    if 36 <= h <= 64 and 0.12 <= s < 0.45 and Lc >= 70: return L['A3'] if Lc >= 84 else L['G9']          # dourado pálido (reflexo): amarelo claro, nunca bege-oliva nem pele
    if s < 0.10 and Lc >= 90: return L['H2']                                                                 # reflexo branco da armadura: branco (o pale_skin/warm_white o mandava para pele)
    if 180 <= h <= 215 and s >= 0.35 and 30 <= Lc < 58: return L['C11']                                      # azul-esverdeado médio (cabelo do Camus): o kit não tem petróleo; o near120 dava cinza H5
    return None


def CM_CDZ(rgb, Lc, letter, is_black): return CM_GOLD(rgb, Lc, letter, is_black)


CHG = dict(CH, pale_skin=False, warm_white=0, center_map=CM_CDZ)          # Cavaleiros: rosto pêssego (não precisa do pale_skin) e reflexo branco da armadura não vira pele


def inpainted(idx, boxes):
    """apaga texto por cima do desenho (copyright, marca d'água) repintando os retângulos pela vizinhança (cv2.inpaint) numa cópia temporária da imagem; devolve o caminho"""
    tmp = os.path.join(OUT, f'_r29_{idx}.png')
    if not os.path.exists(tmp) or os.path.getmtime(tmp) < os.path.getmtime(__file__):
        im = np.array(Image.open(F[idx]).convert('RGB'))
        if callable(boxes): m = boxes(im).astype(np.uint8) * 255
        else:
            m = np.zeros(im.shape[:2], np.uint8)
            for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = 255
        Image.fromarray(cv2.inpaint(im, m, 5, cv2.INPAINT_TELEA)).save(tmp)
    return tmp


def outline_mask(dark=95, close=7):
    """fundo = o que fica FORA do contorno escuro fechado da figura (folha de chibis sobre estrelinhas coloridas: o fundo não é liso)"""
    def f(rgb):
        d = (rgb.max(axis=2) < dark).astype(np.uint8)
        d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
        h, w = d.shape
        ff = np.pad(d, 1).copy(); cv2.floodFill(ff, None, (0, 0), 2)
        return (ff[1:-1, 1:-1] == 2)
    return f


SKIN_CODES = ('E11', 'E14', 'E15', 'E1', 'G1', 'G2', 'G3', 'A9', 'A12', 'F1', 'F14', 'E8')
SKIN = {L[c] for c in SKIN_CODES}


def _lab_of(ch): return LAB[ch]


def _mouthy(ch):
    """cor de boca: vermelho/rosa (lábio, língua), branco (dente) ou escuro avermelhado/marrom (interior da boca aberta); o preto puro do contorno fica de fora"""
    Lc, A, B = LAB[ch]
    return Lc > 90 or (A > 12 and Lc < 88) or (Lc < 52 and A > 6)


def _face_eyes(rows):
    """rosto = maior peça de pele (depois de uma ABERTURA 3x3, que corta dedos, pescoço e mechas finas) na parte de cima; casca = envoltória convexa dela (os olhos de chibi
    encostam no cabelo e NÃO são buracos da pele); olhos = manchas dentro da casca e fora da pele (fechadas 3x3: cílio + íris + brilho viram uma só) com conta escura ou colorida,
    de preferência um PAR na mesma altura. Devolve (rosto, casca, (linha de baixo dos olhos, coluna 0, coluna 1) ou None)"""
    import scipy.ndimage as ndi
    H, W = len(rows), len(rows[0])
    skin = np.array([[c in SKIN for c in r] for r in rows])
    core = ndi.binary_opening(skin, structure=np.ones((3, 3), bool))
    lab, n = ndi.label(core)
    best = None
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if ys.mean() > 0.70 * H: continue
        if best is None or len(ys) > best[1]: best = (i, len(ys))
    if not best or best[1] < 12: return None, None, None
    face = lab == best[0]
    ys, xs = np.nonzero(face); fy0, fy1 = ys.min(), ys.max(); fh = fy1 - fy0 + 1
    hull = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(hull, cv2.convexHull(np.stack([xs, ys], axis=1).astype(np.int32)), 1)
    hull = hull.astype(bool)
    nonempty = np.array([[c != '.' for c in r] for r in rows])
    inner = hull & ~skin & nonempty
    il, inn = ndi.label(ndi.binary_closing(inner, structure=np.ones((3, 3), bool)) & hull)
    cand = []
    for j in range(1, inn + 1):
        m = (il == j) & inner
        hy, hx = np.nonzero(m)
        if len(hy) < 2 or len(hy) > 0.30 * best[1] or hy.mean() > fy0 + 0.85 * fh: continue
        cols = [rows[y][x] for y, x in zip(hy, hx)]
        if not any(LAB[c][0] < 50 or (LAB[c][1] ** 2 + LAB[c][2] ** 2) ** .5 > 25 for c in cols): continue
        cand.append((len(hy), hy.mean(), hx.mean(), hy.max(), hx.min(), hx.max()))
    pair = None
    for i in range(len(cand)):
        for k in range(i + 1, len(cand)):
            a_, b_ = cand[i], cand[k]
            if abs(a_[1] - b_[1]) <= 2.5 and abs(a_[2] - b_[2]) >= 4:
                sc = a_[0] + b_[0]
                if pair is None or sc > pair[0]: pair = (sc, a_, b_)
    if pair:
        _, a_, b_ = pair
        return face, hull, (max(a_[3], b_[3]), min(a_[4], b_[4]), max(a_[5], b_[5]))
    return face, hull, None


def no_mouth(rows, verbose=False, zone=None):
    """ILUSTRAÇÃO em 1 placa sem boca (regra do dono, CLAUDE.md §4.8). Acha os olhos (par de manchas escuras/coloridas dentro da casca do rosto) e, ABAIXO deles e dentro da casca,
    troca pela pele vizinha: (1) contas com cor de boca (vermelho, rosa, dente, marrom-escuro) que encostam na pele; (2) contas escuras cercadas pela pele (contorno da boca aberta).
    Sem par de olhos, a zona começa em 72% da altura do rosto. Conta que encosta no vazio nunca muda (contorno de fora)."""
    from collections import Counter
    if zone: return paint_mouth(rows, zone, verbose)
    face, hull, eyes = _face_eyes(rows)
    if face is None: return rows
    H, W = len(rows), len(rows[0])
    ys, xs = np.nonzero(face); fy0, fy1 = ys.min(), ys.max(); fh = fy1 - fy0 + 1
    if zone: ey, y_end, ex0, ex1 = zone[0] - 1, zone[1], zone[2], zone[3]          # zona dada à mão (linha 0, linha 1, coluna 0, coluna 1), inclusiva
    elif eyes: ey, ex0, ex1 = eyes; y_end = fy1 + 1
    else: return rows                                                                    # sem par de olhos seguro: não mexe (a zona sai à mão, mouth_zone=)
    g = [list(r) for r in rows]
    changed = 0
    for it in range(6):
        todo = []
        for y in range(ey + 1, min(H, y_end + 1)):
            for x in range(max(0, ex0), min(W, ex1 + 1)):
                c = g[y][x]
                if c == '.' or c in SKIN or (not zone and not hull[y, x]): continue
                nb = [(v, u) for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W]
                if any(g[v][u] == '.' for v, u in nb): continue
                ns = sum(1 for v, u in nb if g[v][u] in SKIN)
                if (_mouthy(c) and ns >= 1) or (LAB[c][0] < 52 and ns >= 3): todo.append((y, x))
        if not todo: break
        for y, x in todo:
            cnt = Counter(g[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1)) if 0 <= v < H and 0 <= u < W and g[v][u] in SKIN)
            if cnt: g[y][x] = cnt.most_common(1)[0][0]; changed += 1
    if verbose and changed: print(f'    boca tirada: {changed} contas, linhas {ey + 1}-{y_end}, colunas {ex0}-{ex1} ({"zona à mão" if zone else "abaixo dos olhos"})')
    return [''.join(r) for r in g]


CUR = ['']            # nome do molde em conversão (posto pelo run())
_V5 = {}


def v5_size(name):
    """tamanho (W, H) do molde na 1ª versão (convert5), para converter as zonas de boca medidas nela"""
    if not _V5:
        pth = os.path.join(HERE, 'data', 'final31_raw_v5_120.json')
        if os.path.exists(pth):
            for x in json.load(open(pth, encoding='utf-8')): _V5[x[0]] = (len(x[2][0]), len(x[2]))
    return _V5.get(name)


def zone_to_v6(zone, name, rows):
    """zona (linha0, linha1, coluna0, coluna1) medida no molde do convert5 -> a mesma região no molde do convert6 (1 conta de contorno em volta, outra escala), com 1 conta de folga"""
    sz = v5_size(name)
    if not sz: return None
    W5, H5 = sz; W6, H6 = len(rows[0]), len(rows)
    sx = (W6 - 2) / float(W5); sy = (H6 - 2) / float(H5)
    y0, y1, x0, x1 = zone
    return (max(0, int(round(1 + y0 * sy + 0.5))), min(H6 - 1, int(round(1 + (y1 + 1) * sy))), max(0, int(1 + x0 * sx) - 1), min(W6 - 1, int(round(1 + (x1 + 1) * sx))))          # sem folga em cima: a 1ª linha da zona antiga encostava nos olhos (Kirishima perdeu os olhos)


def paint_mouth6(rows, zone, verbose=False):
    """boca no convert6 (zona à mão convertida): dentro do retângulo, cresce a partir da pele: conta com cor de boca (vermelho, rosa, dente, marrom) encostada na pele vira pele, e conta
    ESCURA (contorno da boca) com 3+ vizinhas de pele também; a linha do queixo (pele de um lado só) e o contorno de fora ficam"""
    from collections import Counter
    H, W = len(rows), len(rows[0]); y0, y1, x0, x1 = zone
    g = [list(r) for r in rows]; n = 0
    for _ in range(6):
        todo = []
        for y in range(max(0, y0), min(H, y1 + 1)):
            for x in range(max(0, x0), min(W, x1 + 1)):
                c = g[y][x]
                if c == '.' or c in SKIN: continue
                nb = [(v, u) for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W]
                if any(g[v][u] == '.' for v, u in nb): continue
                ns = sum(1 for v, u in nb if g[v][u] in SKIN)
                ns8 = sum(1 for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1) if (v, u) != (y, x) and 0 <= v < H and 0 <= u < W and g[v][u] in SKIN)
                if (_mouthy(c) and (ns >= 2 or (ns >= 1 and ns8 >= 5))) or (LAB[c][0] < 52 and ns >= 3): todo.append((y, x))          # gola vermelha e linha do queixo (pele de um lado só) ficam
        if not todo: break
        for y, x in todo:
            cnt = Counter(g[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1)) if 0 <= v < H and 0 <= u < W and g[v][u] in SKIN)
            if cnt: g[y][x] = cnt.most_common(1)[0][0]; n += 1
    if verbose: print(f'    boca (zona convertida para o convert6): {n} contas -> pele (linhas {y0}-{y1}, colunas {x0}-{x1})')
    return [''.join(r) for r in g]


def paint_mouth(rows, zone, verbose=False):
    """boca marcada à mão (linha 0, linha 1, coluna 0, coluna 1, inclusivas): no retângulo, toda conta que não é a pele principal do rosto (dentes, lábio, língua, contorno da boca)
    e não encosta no vazio vira a pele principal (a letra de pele mais comum no retângulo aumentado em 2 contas)"""
    from collections import Counter
    H, W = len(rows), len(rows[0]); y0, y1, x0, x1 = zone
    cnt = Counter(rows[y][x] for y in range(max(0, y0 - 2), min(H, y1 + 3)) for x in range(max(0, x0 - 2), min(W, x1 + 3)) if rows[y][x] in SKIN)
    if not cnt: return rows
    sk = cnt.most_common(1)[0][0]
    g = [list(r) for r in rows]; n = 0
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            if g[y][x] in ('.', sk): continue
            if any(rows[v][u] == '.' for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W): continue
            g[y][x] = sk; n += 1
    if verbose: print(f'    boca pintada à mão: {n} contas -> pele {sk} (linhas {y0}-{y1}, colunas {x0}-{x1})')
    return [''.join(r) for r in g]


FACE6 = {}          # retângulos de rosto (linha 0, linha 1, coluna 0, coluna 1) medidos no convert6; os de face_skin(...) no CFG são do convert5
ZONE6 = {}          # zonas de boca à mão medidas no convert6 (idx -> retângulo, ou None = não mexe)

# PELE DA COR DA ARMADURA (retorno do dono, 2026-11-04: "nos cavaleiros do zodíaco, vários estão com a cor da pele igual à cor da armadura"): rosto amarelo-claro (A3)
# ou salmão (G3/G2) ao lado do ouro. Sementes = contas (linha, coluna do molde final do convert6) no meio do rosto/da pele; o convert6 inunda o rosto na arte a partir
# delas e pinta de bege claro (illus6._face_skin6). Aldebaran tem pele morena: bege mais escuro.
SKIN6 = {
    'Cavaleiro de Ouro de cabelo preto (chibi, olhos fechados)': dict(face_seeds=[(27, 15), (30, 18), (25, 24), (23, 11)], face_box=(21, 33, 9, 29), face_absorb=('B11',)),          # bochecha clara perto do olho direito é outra região de cor: semente própria
    'Cavaleiro de Ouro de cabelo loiro espetado (chibi)': dict(face_seeds=[(29, 20), (31, 21)], face_box=(25, 34, 11, 30)),
    'Cavaleiro de Ouro loiro (chibi, joia verde no elmo)': dict(face_seeds=[(30, 19), (32, 20)], face_box=(26, 34, 12, 26)),
    'Hyoga de Cisne (chibi)': dict(face_seeds=[(29, 20), (31, 21)], face_box=(25, 34, 11, 30)),
    'Shiryu de Dragão (chibi, capacete)': dict(face_seeds=[(30, 20), (28, 16), (27, 25)], face_box=(25, 33, 11, 28)),
    'Aiolia de Leão (chibi)': dict(face_seeds=[(30, 20), (32, 19)], face_box=(25, 34, 10, 27)),
    'Aldebaran de Touro (chibi)': dict(face_seeds=[(31, 20), (33, 18)], face_box=(28, 36, 11, 32), face_main='E14', face_shadow='A12'),
    'Cavaleiro de Ouro de cabelo preto comprido (chibi)': dict(face_seeds=[(28, 18), (30, 19)], face_box=(24, 33, 9, 26)),
    'Shiryu de Dragão (chibi)': dict(face_seeds=[(28, 18), (30, 19)], face_box=(24, 33, 10, 26)),
    'Ikki de Fênix (chibi)': dict(face_seeds=[(30, 19), (32, 19)], face_box=(25, 34, 12, 26)),
    'Ikki de Fênix (chibi, elmo)': dict(face_seeds=[(31, 18), (33, 17)], face_box=(26, 35, 11, 23)),
}          # os dois Seiya de corpo inteiro ficam como estão: a pele deles segue a arte e não é da cor da armadura


def FS(idx, rect5, **kw):
    """face_skin com o retângulo certo para o conversor em uso (convert5: rect5; convert6: FACE6[idx], ou nada se ainda não foi medido)"""
    def f(rows):
        rect = rect5 if ENGINE[0] == 'c5' else FACE6.get(idx)
        return face_skin(*rect, **kw)(rows) if rect else rows
    return f


def face_skin(r0, r1, c0, c1, frm=('A3',), to='G1'):
    """rosto desenhado em AMARELO-CLARO na arte (Cavaleiros dourados de pele amarelada): no retângulo do rosto, as contas `frm` viram o bege `to` (pele de verdade, distinta do cabelo loiro)"""
    fl = {L[c] for c in frm}; tl = L[to]
    def f(rows):
        return [''.join(tl if (r0 <= y <= r1 and c0 <= x <= c1 and ch in fl) else ch for x, ch in enumerate(r)) for y, r in enumerate(rows)]
    return f


def grad_mask(step=5, blur=3):
    """fundo em DEGRADÊ: inundação a partir de toda a borda que passa de pixel a pixel enquanto a cor muda menos que `step` (cv2.floodFill com faixa flutuante); o contorno do desenho segura"""
    def f(rgb):
        h, w = rgb.shape[:2]
        img = cv2.GaussianBlur(rgb, (blur, blur), 0) if blur else rgb.copy()
        mask = np.zeros((h + 2, w + 2), np.uint8)
        flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
        seeds = [(x, y) for x in range(0, w, 4) for y in (0, h - 1)] + [(x, y) for y in range(0, h, 4) for x in (0, w - 1)]
        for x, y in seeds:
            if mask[y + 1, x + 1] == 0: cv2.floodFill(img, mask, (x, y), 0, (step,) * 3, (step,) * 3, flags)
        return mask[1:-1, 1:-1] > 0
    return f


def color_mask(ref, tol, refs2=()):
    """fundo de UMA cor (também fechado dentro do desenho, como o miolo de um anel): pixel a menos de `tol` (RGB) da cor `ref` (ou de uma das `refs2`) em qualquer lugar"""
    def f(rgb):
        a = rgb.astype(np.float32); m = np.linalg.norm(a - np.array(ref, np.float32), axis=2) < tol
        for r2, t2 in refs2: m |= np.linalg.norm(a - np.array(r2, np.float32), axis=2) < t2
        return m
    return f


def sample_text(im):
    """marca d'água "SAMPLE" cinza por cima do Draken (78): cinza NEUTRO (max-min < 16) e médio (68 < valor < 222) dentro da faixa do texto vira máscara (dilatada 2 px)"""
    f = im.astype(np.int32); mx = f.max(axis=2); mn = f.min(axis=2)
    m = ((mx - mn) < 16) & (mx > 68) & (mx < 222)
    band = np.zeros_like(m); band[905:1105, 55:895] = True
    m = (m & band).astype(np.uint8)
    return cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0


NO_MOUTH = [True]          # --com-boca na linha de comando desliga (para comparar)
ENGINE = ['c6']            # 'c6' = illus6.convert6 (contorno preto primeiro, mais tons: revisão pedida pelo dono em 2026-11-04); 'c5' = o convert5 da 1ª versão (--c5)
KW6 = {}                   # --kw6 k=v,... (testes do convert6)
_C6_DROP = ('bigkw', 'fix', 'fixg', 'drop_edge', 'lone_dark', 'post2', 'dark_frac', 'black_L', 'warm_white', 'smooth_de', 'noclean', 'trace', 'hl_gain', 'rare_n',
            'min_blob', 'cover', 'over', 'dark_L', 'plates')


def ill6(idx, kw, box=None, clear=(), skin=True):
    """o mesmo preparo da imagem do R.ill (caixa, retângulos apagados, texto, sombra no chão) e depois illus6.convert6 (os parâmetros só do convert5 são ignorados)"""
    import illus6, loose
    a = dict(kw)
    clear = tuple(clear) + tuple(a.pop('clear', ()))
    notext = a.pop('notext', False); noshadow = a.pop('noshadow', False); post = a.pop('post', None)
    for k_ in _C6_DROP: a.pop(k_, None)
    r5.SKIN_ON = skin
    rgb = R.illus._load(F[idx], box).copy()
    ox, oy = (box[0], box[1]) if box else (0, 0)
    for x0, y0, x1, y1 in clear: rgb[max(0, y0 - oy):max(0, y1 - oy), max(0, x0 - ox):max(0, x1 - ox)] = 255
    if notext:
        pr = [(x0 - ox, y0 - oy, x1 - ox, y1 - oy) for x0, y0, x1, y1 in (notext.get('protect', ()) if isinstance(notext, dict) else ())]
        rgb = R.strip_text(rgb, protect=pr)
    if noshadow: rgb = R.kill_shadow(rgb)
    a['K'] = max(int(a.get('K', 34)), 34)
    a['pale_skin'] = bool(skin)          # rosto claro (rosado quase branco) vira pele clara; sem isto o rosto dos Cavaleiros saía BRANCO
    a.update(SKIN6.get(CUR[0], {}))
    a.update(KW6)
    rows = illus6.convert6(rgb=rgb, **a)
    rows = loose.fill_pinholes(rows)[0]
    rows = post(rows) if post else lg(rows)
    return rows


def I(idx, box=None, skin=True, post=None, clear=(), base=None, paint=None, mouth=False, mouth_zone=None, **kw):
    """ilustração: R.ill (convert5 + limpeza de bordas + buraquinhos + maior peça) com CH (ou base) + kw (+ --kw da linha de comando);
    paint = retângulos repintados pela vizinhança antes de converter (texto por cima do desenho); mouth=True mantém a boca (padrão: no_mouth tira, §4.8)"""
    def f():
        a = dict(base or CH); a.update(kw); a.update(KW_OVER)
        old = F[idx]
        if paint: F[idx] = inpainted(idx, paint)
        try: r = ill6(idx, a, box=box, clear=clear, skin=skin) if ENGINE[0] == 'c6' else R.ill(idx, a, box=box, clear=clear, skin=skin)
        finally: F[idx] = old
        if post: r = post(r)
        if NO_MOUTH[0] and not mouth and skin:
            if ENGINE[0] == 'c5': r = no_mouth(r, verbose=True, zone=mouth_zone)
            else:
                z5 = MOUTH.get(CUR[0], mouth_zone)                       # zona medida no convert5 (por nome; ou a do CFG)
                if CUR[0] in MOUTH and MOUTH[CUR[0]] is None: pass         # ali a boca não é boca (cabelo, chocolate): não mexe
                elif z5: z6 = zone_to_v6(z5, CUR[0], r); r = paint_mouth6(r, z6, verbose=True) if z6 else no_mouth(r, verbose=True)
                else: r = no_mouth(r, verbose=True)
        return fin(lg(r))
    f.box = box
    return f


MODE_ON = [True]


def gold_lines(rows):
    """armadura dourada no convert6: risco PRETO de dentro da armadura (sem vazio encostado) cercado só de dourado vira marrom-escuro F11 (gravação no ouro, não risco preto);
    o contorno de fora e os riscos entre o ouro e outra cor (rosto, cabelo, capa) continuam pretos"""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0]); out = [r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] != 'k': continue
            n4 = [g[v][u] if 0 <= v < H and 0 <= u < W else '.' for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))]
            if '.' in n4: continue
            n8 = [g[v][u] for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1) if (v, u) != (y, x) and 0 <= v < H and 0 <= u < W and g[v][u] != 'k']
            if len(n8) >= 3 and sum(1 for c in n8 if c in GOLDS) >= 0.7 * len(n8): out[y][x] = L['F11']
    return [''.join(r) for r in out]


def C(idx, post=None, **kw):
    """Cavaleiro (armadura dourada/colorida): I() com a base CHG + filtro de maioria nos dourados"""
    def p(rows):
        if ENGINE[0] == 'c6': rows = gold_lines(rows)
        if MODE_ON[0]: rows = mode_family(rows)
        return post(rows) if post else rows
    return I(idx, base=CHG, post=p, **kw)


CFG = [
 # ---- gráficos em malha / pixel art: cópia fiel (grupo 'graf')
 ('Nojinho (Divertida Mente, pixel)', 'Divertida Mente', 10, G(10, colmap=[((0, 139, 138), 20, L['B7'])], post=lg), 'graf'),          # cabelo verde-azulado: B7 (turquesa) em vez do C11 (ciano), que deixava o cabelo azul
 ('Garota ruiva de tranças e chapéu marrom (ponto-cruz)', 'Genéricos', 18, G(18, post=lg), 'graf'),
 ('Raiva (Divertida Mente, cabeça em chamas, pixel)', 'Divertida Mente', 20, G(20, post=lg), 'graf'),
 ('Raiva (Divertida Mente, pixel)', 'Divertida Mente', 25, G(25, post=lg), 'graf'),
 ('Minion de dois olhos (pixel)', 'Minions', 29, G(29, post=lg), 'graf'),
 ('Ansiedade (Divertida Mente, pixel)', 'Divertida Mente', 50, G(50, post=lg), 'graf'),
 ('Alegria (Divertida Mente, pixel)', 'Divertida Mente', 66, G(66, post=lg), 'graf'),
 ('Tristeza (Divertida Mente, pixel)', 'Divertida Mente', 74, G(74, post=lg), 'graf'),
 ('Foice e martelo com estrela (gráfico)', 'Política', 100, G(100, post=pieces(4)), 'graf'),

 # ---- Cavaleiros do Zodíaco (grupo 'cdz')
 ('Camus de Aquário (chibi)', CDZ, 0, C(0), 'cdz'),
 ('Cavaleiro de Ouro de cabelo azul (chibi, elmo largo)', CDZ, 1, C(1), 'cdz'),
 ('Armadura de Pégaso (emblema prateado, fundo azul)', CDZ, 3, C(3, skin=False, bg='flat', tol=60, clear=[(0, 690, 40, 736)]), 'cdz'),
 ('Seiya de Pégaso (chibi, elmo)', CDZ, 5, C(5), 'cdz'),
 ('Figura de cabelo escuro e armadura de asas cinzas (chibi)', CDZ, 7, C(7, center_map=DR.ramp(lo=14.0, mid2=26.5, base=CM_CDZ), hl_gain=1.0), 'cdz'),
 ('Aldebaran de Touro (chibi, elmo de chifres)', CDZ, 9, C(9), 'cdz'),
 ('Mu de Áries (chibi, elmo)', CDZ, 12, C(12), 'cdz'),
 ('Cavaleiro de Ouro de cabelo azul-escuro (chibi, joia vermelha)', CDZ, 13, C(13), 'cdz'),
 ('Cavaleiro de Ouro loiro (chibi, elmo de crista)', CDZ, 14, C(14), 'cdz'),
 ('Shun de Andrômeda (chibi, capacete rosa)', CDZ, 15, C(15), 'cdz'),
 ('Mestre Ancião (Dohko, chibi)', CDZ, 19, C(19), 'cdz'),
 ('Aldebaran de Touro (chibi, capa)', CDZ, 21, C(21, mask=outline_mask(), clear=[(470, 580, 700, 640), (430, 650, 700, 712)]), 'cdz'),
 ('Saga de Gêmeos (chibi)', CDZ, 34, C(34), 'cdz'),
 ('Seiya de Sagitário (chibi, asas douradas)', CDZ, 35, C(35), 'cdz'),
 ('Cavaleiro de Ouro de cabelo preto (chibi, olhos fechados)', CDZ, 37, C(37), 'cdz'),
 ('Kiki de Appendix (chibi)', CDZ, 38, C(38), 'cdz'),
 ('Cavaleiro de Ouro de cabelo loiro espetado (chibi)', CDZ, 39, C(39, post=FS(39, (24, 35, 10, 31))), 'cdz'),
 ('Cavaleiro de Ouro loiro (chibi, joia verde no elmo)', CDZ, 43, C(43, post=FS(43, (23, 34, 9, 30))), 'cdz'),
 ('Saga de Gêmeos (chibi, cabelo grisalho, olhos vermelhos)', CDZ, 45, C(45), 'cdz'),
 ('Cavaleiro de armadura prateada e azul (chibi)', CDZ, 46, C(46, mask=outline_mask()), 'cdz'),
 ('Seiya de Pégaso (chibi, capacete)', CDZ, 49, C(49), 'cdz'),
 ('Myu de Papillon (chibi)', CDZ, 51, C(51), 'cdz'),
 ('Hyoga de Cisne (chibi)', CDZ, 53, C(53, post=FS(53, (24, 34, 9, 31))), 'cdz'),
 ('Shion de Áries (chibi, sapuris)', CDZ, 56, C(56, pale_hues=((0, 62), (330, 360))), 'cdz'),          # rosto rosado quase branco (matiz < 8): sem isto saía branco
 ('Mu de Áries (chibi)', CDZ, 57, C(57), 'cdz'),
 ('Ikki de Fênix (chibi)', CDZ, 60, C(60), 'cdz'),
 ('Ikki de Fênix (chibi, elmo)', CDZ, 63, C(63), 'cdz'),
 ('Armadura de Pégaso (objeto, vermelha)', CDZ, 65, C(65, skin=False, mask=outline_mask()), 'cdz'),
 ('Cavaleiro de sapuris cinza-escura (chibi)', CDZ, 71, C(71, center_map=DR.ramp(lo=14.0, mid2=26.5, base=CM_CDZ), hl_gain=1.0), 'cdz'),
 ('Shiryu de Dragão (chibi, capacete)', CDZ, 72, C(72, post=FS(72, (25, 34, 6, 28))), 'cdz'),
 ('Cavaleiro de Ouro de capa roxa (corpo inteiro)', CDZ, 77, C(77, paint=[(76, 514, 380, 548)]), 'cdz'),
 ('Espectro de sapuris roxa e chifres (chibi)', CDZ, 80, C(80), 'cdz'),
 ('Aiolia de Leão (chibi)', CDZ, 82, C(82, post=FS(82, (24, 35, 9, 29))), 'cdz'),
 ('Aldebaran de Touro (chibi)', CDZ, 83, C(83), 'cdz'),
 ('Cavaleiro de Ouro de cabelo preto comprido (chibi)', CDZ, 85, C(85), 'cdz'),
 ('Shiryu de Dragão (chibi)', CDZ, 88, C(88), 'cdz'),
 ('Elmo de Pégaso (adesivo)', CDZ, 89, C(89, skin=False, mask=outline_mask()), 'cdz'),
 ('Seiya de Pégaso (corpo inteiro)', CDZ, 92, C(92, mask=outline_mask()), 'cdz'),
 ('Seiya de Pégaso (soco, fundo dourado)', CDZ, 94, C(94, mask=grad_mask(6)), 'cdz'),
 ('Armadura de Pégaso (objeto, branca)', CDZ, 95, C(95, skin=False), 'cdz'),
 ('Saga de Gêmeos (chibi, sapuris)', CDZ, 98, C(98), 'cdz'),
 ('Shun de Andrômeda (chibi)', CDZ, 101, C(101), 'cdz'),
 ('Mu de Áries (chibi, agachado)', CDZ, 102, C(102, clear=[(405, 452, 612, 511)]), 'cdz'),
 ('Seiya de Sagitário (chibi)', CDZ, 105, C(105), 'cdz'),

 # ---- outras ilustrações (grupo 'ill')
 ('Gato da sorte (maneki-neko, adesivo)', 'Animais', 2, I(2, skin=False, thr=205, peel=1.0, pale_skin=False, warm_white=0), 'ill'),
 ('Akame (Akame ga Kill, chibi)', 'Akame ga Kill', 4, I(4, mask=outline_mask()), 'ill'),
 ('Tatsumaki (One Punch Man, chibi, mãos para a frente)', 'One Punch Man', 8, I(8), 'ill'),
 ('Frieren (chibi, braços abertos)', 'Frieren', 11, I(11, noshadow=True), 'ill'),
 ('Chibi de cabelo vermelho e faixa xadrez (casaco preto)', 'Genéricos', 16, I(16, bg='flat', tol=45, mouth_zone=(27, 28, 14, 19)), 'ill'),
 ('Rem (Re:Zero, chibi, uniforme de empregada)', 'Re:Zero', 17, I(17), 'ill'),
 ('Xenovia Quarta (High School DxD, chibi)', 'High School DxD', 22, I(22), 'ill'),
 ('Kaguya Shinomiya (Kaguya-sama, chibi)', 'Kaguya-sama', 23, I(23), 'ill'),
 ('Chika Fujiwara (Kaguya-sama, chibi)', 'Kaguya-sama', 24, I(24), 'ill'),
 ('Miyuki Shirogane (Kaguya-sama, chibi)', 'Kaguya-sama', 26, I(26), 'ill'),
 ('Aqua (KonoSuba, chibi)', 'KonoSuba', 27, I(27, bg='flat', tol=30), 'ill'),
 ('Obelisco, o Atormentador (Yu-Gi-Oh, chibi)', 'Yu-Gi-Oh', 28, I(28, skin=False), 'ill'),
 ('Bulma (Dragon Ball, chibi)', 'Dragon Ball', 30, I(30, bg='flat', tol=30), 'ill'),
 ('Caveira Invocada (Yu-Gi-Oh, chibi)', 'Yu-Gi-Oh', 32, I(32, skin=False), 'ill'),
 ('Megumin (KonoSuba, chibi)', 'KonoSuba', 33, I(33), 'ill'),
 ('Takemichi Hanagaki (Tokyo Revengers, chibi, adesivo)', 'Tokyo Revengers', 36, I(36, thr=205, peel=1.0), 'ill'),
 ('Albedo (Overlord, chibi)', 'Overlord', 40, I(40), 'ill'),
 ('Ichika Nakano (As Quíntuplas, chibi)', 'As Quíntuplas', 41, I(41), 'ill'),
 ('Chibi loira de laço laranja (casaco preto)', 'Genéricos', 42, I(42, bg='flat', tol=45), 'ill'),
 ('Rei Ayanami (Evangelion, chibi, fundo amarelo)', 'Evangelion', 44, I(44, bg='flat', tol=45), 'ill'),
 ('Itsuki Nakano (As Quíntuplas, chibi)', 'As Quíntuplas', 47, I(47), 'ill'),
 ('Mash Burnedead (Mashle, chibi)', 'Mashle', 48, I(48, bg='flat', tol=30), 'ill'),
 ('Miku Nakano (As Quíntuplas, chibi)', 'As Quíntuplas', 52, I(52), 'ill'),
 ('Frieren (chibi, sentada no baú)', 'Frieren', 54, I(54), 'ill'),
 ('Maga Negra (Yu-Gi-Oh, chibi, estrelas)', 'Yu-Gi-Oh', 55, I(55), 'ill'),
 ('Naofumi Iwatani (The Rising of the Shield Hero, chibi)', 'The Rising of the Shield Hero', 58, I(58, thr=205, peel=1.0), 'ill'),
 ('Akeno Himejima (High School DxD, chibi)', 'High School DxD', 59, I(59), 'ill'),
 ('Dragão Alado de Rá (chibi)', 'Yu-Gi-Oh', 61, I(61, skin=False), 'ill'),
 ('Mayuri Kurotsuchi (Bleach, chibi)', 'Bleach', 62, I(62, bg='flat', tol=40), 'ill'),
 ('Rias Gremory (High School DxD, chibi, fundo rosa)', 'High School DxD', 64, I(64, bg='flat', tol=45), 'ill'),
 ('Bebê Dragão (Yu-Gi-Oh, chibi)', 'Yu-Gi-Oh', 67, I(67, skin=False), 'ill'),
 ('Garoto loiro de roupa preta e capa branca (chibi)', 'Genéricos', 68, I(68), 'ill'),
 ('Grimmjow (Bleach, chibi)', 'Bleach', 70, I(70, bg='flat', tol=45, pale_hues=((8, 34),)), 'ill'),          # a jaqueta e a calça creme (matiz ~43°) caíam no tom de pele (pale_skin): só a pele pêssego vira pele
 ('Rias Gremory (High School DxD, chibi, corpo inteiro)', 'High School DxD', 73, I(73), 'ill'),
 ('Chibi de cabelo azul-claro e brinco (casaco preto)', 'Genéricos', 75, I(75, bg='flat', tol=45), 'ill'),
 ('Figura de elmo vermelho alado e manto branco', 'Genéricos', 76, I(76), 'ill'),
 ('Draken (Tokyo Revengers, chibi)', 'Tokyo Revengers', 78, I(78, paint=sample_text), 'ill'),
 ('Nino Nakano (As Quíntuplas, chibi)', 'As Quíntuplas', 79, I(79), 'ill'),
 ('Marin Kitagawa de orelhas de gato (My Dress-Up Darling, chibi)', 'My Dress-Up Darling', 81, I(81, mouth=True), 'ill'),
 ('Rei Ayanami (Evangelion, chibi, traje de piloto)', 'Evangelion', 84, I(84, mask=outline_mask()), 'ill'),
 ('Yotsuba Nakano (As Quíntuplas, chibi)', 'As Quíntuplas', 86, I(86), 'ill'),
 ('Emblema de asas douradas e sol', 'Genéricos', 87, I(87, skin=False, mask=color_mask(BG87, 58)), 'ill'),
 ('Okarun transformado (Dan Da Dan, chibi, de óculos)', 'Dan Da Dan', 90, I(90, box=(110, 375, 1040, 1675), mask=outline_mask(dark=130), mouth=True), 'ill'),
 ('Rias Gremory (High School DxD, chibi, suéter)', 'High School DxD', 91, I(91, box=(40, 580, 620, 1440), bg='flat', tol=20, peel=1.0), 'ill'),
 ('Rias Gremory (High School DxD, chibi, camisa branca)', 'High School DxD', 91, I(91, box=(610, 600, 1152, 1440), bg='flat', tol=20, peel=1.0), 'ill'),
 ('Garoto de franja preta e fones de ouvido (chibi)', 'Genéricos', 93, I(93), 'ill'),
 ('Sukuna (Jujutsu Kaisen, chibi, trono de caveiras)', 'Jujutsu Kaisen', 96, I(96), 'ill'),
 ('Okarun, Momo e Turbo Granny (Dan Da Dan, adesivo)', 'Dan Da Dan', 97, I(97, thr=205, peel=1.0), 'ill'),
 ('Doutor Destino (Marvel, chibi)', 'Marvel', 103, I(103), 'ill'),
 ('Asuka Langley (Evangelion, chibi)', 'Evangelion', 104, I(104, mask=grad_mask(5), noshadow=True, peel=1.0, clear=[(480, 0, 736, 85)]), 'ill'),
]

# ---- folhas com vários personagens (grupo 'folha'): caixas em pixels lidas com régua (tools/out/ruler29_N.png)
MHA20 = [('Izuku Midoriya', (8, 4, 156, 194)), ('Katsuki Bakugo', (156, 4, 312, 194)), ('Ochaco Uraraka', (312, 4, 456, 194)), ('Shoto Todoroki', (456, 4, 602, 194)), ('Tenya Iida', (602, 4, 736, 194)),
         ('Tsuyu Asui', (4, 194, 158, 376)), ('Eijiro Kirishima', (158, 194, 306, 376)), ('Denki Kaminari', (306, 194, 452, 376)), ('Momo Yaoyorozu', (452, 194, 590, 376)), ('Minoru Mineta', (590, 194, 736, 376)),
         ('All Might', (4, 374, 156, 538)), ('Shota Aizawa', (156, 374, 302, 538)), ('Himiko Toga', (302, 374, 450, 538)), ('Dabi', (450, 374, 592, 538)), ('Tomura Shigaraki', (592, 374, 736, 538)),
         ('Hawks', (4, 538, 152, 736)), ('Endeavor', (152, 538, 300, 736)), ('Mirko', (300, 538, 446, 736)), ('Best Jeanist', (446, 538, 568, 736)), ('Fumikage Tokoyami', (568, 538, 736, 736))]
MOUTH = {          # boca pintada à mão (linha 0, linha 1, coluna 0, coluna 1) onde a busca automática pelos olhos falha; None = não mexe (a "boca" que ela achava era cabelo ou chocolate)
 'Katsuki Bakugo (My Hero Academia, chibi, folha de 20)': (25, 29, 13, 23), 'Izuku Midoriya (My Hero Academia, chibi, folha de 20)': (22, 27, 12, 22), 'All Might (My Hero Academia, chibi, folha de 20)': (22, 26, 12, 24),
 'Himiko Toga (My Hero Academia, chibi, folha de 20)': (24, 28, 16, 24), 'Minoru Mineta (My Hero Academia, chibi, folha de 20)': (27, 30, 9, 17),
 'Mirko (My Hero Academia, chibi, folha de 20)': None, 'Shoto Todoroki (My Hero Academia, chibi, folha de 20)': None,
 'Asta (Black Clover, chibi, espada)': (28, 31, 22, 30), 'Luck Voltia (Black Clover, chibi)': (24, 26, 10, 19),
 'Chibi de cabelo preto comendo doces (Black Clover)': (23, 29, 10, 17),
 'Izuku Midoriya (My Hero Academia, chibi, adesivo em fundo preto)': (18, 19, 9, 13), 'Katsuki Bakugo (My Hero Academia, chibi, adesivo em fundo preto)': (22, 25, 9, 17),
 'Seiya de Pégaso (chibi fofo, folha)': (30, 31, 12, 17), 'Shun de Andrômeda (chibi fofo, folha)': (28, 30, 13, 18),
 # achadas pela busca automática na 1ª versão (2026-11-03): no convert6 a busca não acha os olhos destes, então a zona vai explícita
 'Kiki de Appendix (chibi)': (28, 33, 13, 23), 'Bulma (Dragon Ball, chibi)': (22, 25, 14, 25), 'Ochaco Uraraka (My Hero Academia, chibi, folha de 20)': (20, 25, 5, 24),
 'Eijiro Kirishima (My Hero Academia, chibi, folha de 20)': (22, 30, 6, 20), 'Finral Roulacase (Black Clover, chibi)': (26, 32, 5, 23), 'Grimmjow (Bleach, chibi)': (20, 28, 10, 19),
 'Ochaco Uraraka (My Hero Academia, chibi, adesivo em fundo preto)': (14, 19, 11, 20), 'Nino Nakano (As Quíntuplas, chibi)': (18, 24, 12, 24), 'Kaguya Shinomiya (Kaguya-sama, chibi)': (20, 27, 13, 25),
}


MOUTH6 = {}          # zonas de boca medidas no convert6 (r29_sheet.py); preenchidas depois de olhar as folhas


def mk(n):
    """argumentos de boca da folha: zona à mão, ou mouth=True (não mexe). Os do convert5 (MOUTH) só valem com --c5"""
    if n not in MOUTH: return {}
    return {'mouth': True} if MOUTH[n] is None else {'mouth_zone': MOUTH[n]}


EXTRA6 = {          # ajustes do convert6 por molde da folha
 'Eijiro Kirishima (My Hero Academia, chibi, folha de 20)': dict(line_L=58.0, line_C=45.0, t_line=0.06),          # o traço dos olhos é castanho e fino: com o limite padrão os olhos sumiam
}
for _n, _b in MHA20:
    _nm = f'{_n} (My Hero Academia, chibi, folha de 20)'
    CFG.append((_nm, 'My Hero Academia', 6, I(6, box=_b, thr=205, peel=1.0, pre_blur=3, K=18, smooth_de=26.0, **mk(_nm), **EXTRA6.get(_nm, {})), 'folha'))          # JPEG pequeno (~140 px por figura): suaviza antes
BC9 = [('Asta (Black Clover, chibi, espada)', (4, 0, 250, 255)), ('Yuno (Black Clover, chibi, grimório verde)', (250, 0, 492, 255)), ('Noelle Silva (Black Clover, chibi)', (492, 0, 736, 255)),
       ('Luck Voltia (Black Clover, chibi)', (4, 255, 250, 502)), ('Magna Swing (Black Clover, chibi)', (250, 255, 492, 502)), ('Finral Roulacase (Black Clover, chibi)', (492, 255, 736, 502)),
       ('Chibi de cabelo preto comendo doces (Black Clover)', (4, 502, 250, 736)), ('Chibi de cabelo preto lendo grimório roxo (Black Clover)', (250, 502, 492, 736)), ('Nero (Black Clover, pássaro)', (492, 502, 736, 736))]
for _n, _b in BC9:
    CFG.append((_n, 'Black Clover', 31, I(31, box=_b, thr=205, peel=1.0, pre_blur=3, K=18, smooth_de=26.0, skin=('Nero' not in _n), **mk(_n)), 'folha'))
MHA4 = [('Izuku Midoriya', (40, 30, 352, 565)), ('Katsuki Bakugo', (358, 38, 736, 545)), ('Ochaco Uraraka', (30, 530, 378, 985)), ('Shoto Todoroki', (395, 520, 722, 975))]
for _n, _b in MHA4:
    _nm = f'{_n} (My Hero Academia, chibi, adesivo em fundo preto)'
    CFG.append((_nm, 'My Hero Academia', 69, I(69, box=_b, bg='flat', tol=60, peel=2.0, pre_blur=2, **mk(_nm)), 'folha'))
SS6 = [('Seiya de Pégaso (chibi fofo, folha)', (90, 25, 255, 252)), ('Saori Kido (Athena, chibi fofo)', (270, 40, 468, 245)), ('Shun de Andrômeda (chibi fofo, folha)', (485, 25, 655, 245)),
       ('Shiryu de Dragão (chibi fofo, folha)', (100, 275, 270, 502)), ('Hyoga de Cisne (chibi fofo, folha)', (295, 285, 480, 502)), ('Ikki de Fênix (chibi fofo, folha)', (512, 278, 660, 496))]
for _n, _b in SS6:
    CFG.append((_n, CDZ, 99, I(99, box=_b, mask=outline_mask(), **mk(_n)), 'folha'))


# ---------------------------------------------------------------- nomes únicos: nome que já está no catálogo OU que o dono excluiu ganha ", versão N" (o add_templates pula nome repetido/excluído)
def _with_version(n, k):
    if n.endswith(')'): return n[:-1] + f', versão {k})'
    return n + f' (versão {k})'


def uniq(items):
    # nomes únicos contra o catálogo de ANTES da remessa entrar (backups/pre-r29.js): contra o templates.js atual, os próprios moldes da
    # remessa 29 já existem e todos virariam ", versão 2" (foi o que estragou o final31_120.json e a tela Novos moldes em 2026-11-04)
    base = os.path.join(HERE, 'backups', 'pre-r29.js')
    d = tplfile.parse(base if os.path.exists(base) else os.path.join(os.path.dirname(HERE), 'templates.js'))
    taken = {t['name'] for t in d['items']} | set(d.get('removed') or [])
    out = []; seen = set()
    for it in items:
        n = it[0]; k = 2
        while n in taken or n in seen: n = _with_version(it[0], k); k += 1
        if n != it[0]: print(f'  nome ajustado: {it[0]} -> {n}')
        seen.add(n); out.append([n] + list(it[1:]))
    return out


# RETOQUES À MÃO no molde FINAL do convert6 (retorno do dono, 2026-11-04: olhos de Asuka, Rei de traje de piloto, Frieren no baú, High School DxD menos a Xenovia,
# Chika, Megumin, Izuku e Ochaco do adesivo em fundo preto; tiara dos dois Seiya). Modelo de olho = o da "Rei Ayanami (chibi, fundo amarelo)", que ele achou impecável:
# pálpebra preta em cima, íris em degradê (tom escuro em cima, médio, claro embaixo) e 1-2 contas de brilho branco do mesmo lado nos dois olhos. Coordenadas = molde final
# (tools/r29_eyesheet.py mostra a arte alinhada à grade). ops: ('block', linha, coluna, [linhas de símbolos]) com leg = símbolo -> código ('' = não mexe, '.' = vazio);
# ('sym', l0, l1, a2, 'L'|'R', c0, c1) = copia espelhado o lado mantido nessas linhas (a2 = 2 x eixo; ímpar = eixo entre duas colunas).
_EYE4L = ['KKKK', 'KDHD', 'WMMM', ' LLL']          # olho esquerdo (de quem olha): cílio, íris escura com brilho, íris média com o branco do lado de fora, íris clara
_EYE4R = ['KKKK', 'DDHK', 'MMMW', 'LLL ']          # olho direito: o mesmo, com o canto e o branco do lado de fora à direita (o brilho fica do mesmo lado nos dois)


def eyes(yl, xl, yr, xr, D, M, Lt, skin='E11', tl=_EYE4L, tr=_EYE4R, extra=(), leg=None):
    """retoque de olhos no modelo da Rei de fundo amarelo: (yl, xl) e (yr, xr) = canto de cima à esquerda de cada olho; D/M/Lt = íris escura, média e clara"""
    lg_ = {'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': D, 'M': M, 'L': Lt, 'E': skin}
    lg_.update(leg or {})
    return dict(leg=lg_, ops=[('block', yl, xl, tl), ('block', yr, xr, tr)] + list(extra))


_EYE5L = ['KKKKK', 'KDDHD', 'WMMMM', ' LLLL']      # olho de 5 contas (rosto grande)
_EYE5R = ['KKKKK', 'DDDHK', 'MMMMW', 'LLLL ']
_EYE2 = ['KK', 'DH', 'ML']                          # olho de 2 contas (rosto pequeno, corpo inteiro)
_EYEW = ['KKKK', 'WDDW', 'WDHW', 'WMMW', ' WW ']    # olho redondo de branco grande e íris pequena no meio (estilo My Hero Academia)
_EYE55L = ['KKKKK', 'WDDHD', 'WDDDD', 'WMMMM', ' LLLL']      # olho grande e alto (Seiya): branco do lado de fora, íris 4x4 escura em cima
_EYE55R = ['KKKKK', 'DDDHW', 'DDDDW', 'MMMMW', 'LLLL ']

TOUCH6 = {
    'Asuka Langley (Evangelion, chibi)': eyes(11, 5, 10, 12, 'C9', 'C8', 'C7', skin='E1', extra=[('block', 12, 11, ['E'])]),
    'Rei Ayanami (Evangelion, chibi, traje de piloto)': eyes(15, 7, 15, 15, 'G8', 'F5', 'A14', skin='E1'),
    'Frieren (chibi, sentada no baú)': eyes(13, 14, 11, 22, 'B12', 'B7', 'B3', skin='E11', tl=_EYE5L, tr=_EYE5R),
    'Akeno Himejima (High School DxD, chibi)': eyes(18, 17, 19, 25, 'D21', 'D13', 'D12', skin='E11'),
    'Rias Gremory (High School DxD, chibi, fundo rosa)': eyes(15, 11, 13, 20, 'C8', 'C10', 'C2', skin='E1'),
    'Rias Gremory (High School DxD, chibi, corpo inteiro)': eyes(9, 6, 9, 9, 'C8', 'C10', 'C2', skin='E1', tl=_EYE2, tr=_EYE2, extra=[('block', 11, 8, ['E'])]),
    'Rias Gremory (High School DxD, chibi, suéter)': eyes(12, 10, 12, 18, 'C11', 'B6', 'C2', skin='E11'),
    'Rias Gremory (High School DxD, chibi, camisa branca)': eyes(13, 9, 13, 18, 'C8', 'C7', 'C3', skin='E11'),
    'Chika Fujiwara (Kaguya-sama, chibi)': eyes(14, 6, 15, 15, 'C8', 'C7', 'C3', skin='E11', tl=_EYE5L, tr=_EYE5R, extra=[('block', 19, 17, ['E'])]),
    'Megumin (KonoSuba, chibi)': eyes(17, 18, 19, 28, 'G8', 'F8', 'F5', skin='E11'),
    'Izuku Midoriya (My Hero Academia, chibi, adesivo em fundo preto)': eyes(11, 6, 11, 13, 'B15', 'B12', 'B8', skin='E14', tl=_EYEW, tr=_EYEW),
    'Ochaco Uraraka (My Hero Academia, chibi, adesivo em fundo preto)': eyes(9, 8, 10, 16, 'G8', 'F11', 'G7', skin='E14', tl=_EYEW, tr=_EYEW, extra=[('block', 11, 15, ['E', 'E', 'E'])]),
    # Seiya (pedido do dono: a tiara certinha da versão antiga "armadura de prata", que é simétrica): elmo e tiara espelhados a partir da metade esquerda (a mais limpa)
    # e olhos castanhos novos; o cabelo e o corpo ficam como a arte
    'Seiya de Pégaso (chibi, elmo)': dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F11', 'L': 'F6', 'E': 'E11'}, ops=[
        ('sym', 9, 22, 39, 'L', 0, 19), ('block', 23, 13, _EYE55L), ('block', 24, 12, ['K', 'K', 'K']),          # olho esquerdo com o canto preto de fora
        ('sym', 23, 33, 39, 'L', 0, 19), ('block', 23, 22, _EYE55R),          # rosto espelhado; o direito é carimbado de novo para o brilho ficar do mesmo lado
        ('block', 25, 18, ['EEEE', ' EE ']), ('block', 27, 13, ['E']), ('block', 27, 26, ['E'])]),          # marrom solto entre os olhos e no canto de baixo vira pele
    'Seiya de Pégaso (chibi, capacete)': dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F11', 'L': 'F6', 'G': 'H3', 'E': 'E11'}, ops=[
        ('block', 6, 16, ['WWW'] * 14),                       # tira a crista torta (2 colunas à esquerda do meio)
        ('sym', 0, 13, 39, 'L', 0, 19),                       # chifres, pedras vermelhas e domo iguais dos dois lados
        ('block', 3, 19, ['KK', 'KK'] + ['GG'] * 4 + ['KK'] * 4 + ['GG'] * 6),   # crista no meio do capacete: ponta preta, cinza, emenda preta, cinza
        ('block', 24, 13, _EYE55L), ('block', 25, 12, ['K', 'K', 'K']), ('sym', 24, 31, 39, 'L', 0, 19), ('block', 24, 22, _EYE55R), ('block', 25, 18, ['EEEE'])]),
    # Mayuri (o dono: "irreconhecível"): rosto escuro limpo entre as abas brancas do capuz, olhos amarelos de pálpebra preta e pupila para dentro; sem boca nem dentes (§4.8)
    'Mayuri Kurotsuchi (Bleach, chibi)': dict(leg={'k': 'H7', 'P': 'F7', 'Y': 'A13', 'w': 'H2'}, ops=[('block', 11, 12, [
        ' kkkkkkkkkkk',
        'kPPPPPPPPPPk',
        'wPkkkPPkkkPk',
        'wPYYkPPkYYPk',
        'wPPPPPPPPPPk',
        'wkPPPPPPPPkk',
        ' wkkPPPPkkw ']), ('block', 10, 23, ['k']), ('block', 11, 24, ['k']), ('block', 12, 24, ['w'])]),          # 3 contas vinho que sobravam fora do contorno do rosto
    # Grimmjow (o dono: "cores erradas"): roupa branca já vem do pale_hues no CFG; aqui a sombra do rosto que saía cáqui (M9, parecia sujeira) vira a pele, e a boca com dentes sai (§4.8);
    # a máscara de osso branca na bochecha fica
    'Grimmjow (Bleach, chibi)': dict(leg={'E': 'E14'}, ops=[('map', 11, 26, 9, 24, {'M9': 'E14'}), ('map', 22, 25, 11, 17, {'H3': 'E14', 'H2': 'E14', 'H7': 'E14'})]),
    # Turbo Granny (a gata maneki-neko): a cabeça branca tinha virado bege (o branco quente da arte caía no tom de pele); bigodes cinza; o resto do trio fica
    'Okarun, Momo e Turbo Granny (Dan Da Dan, adesivo)': dict(leg={'g': 'H4'}, ops=[
        ('map', 1, 15, 3, 15, {'E11': 'H2', 'M9': 'H2', 'H5': 'H4'}),
        ('block', 11, 4, ['ggg']), ('block', 12, 5, ['gg']), ('block', 11, 12, ['ggg']), ('block', 12, 12, ['gg'])]),
}


def touch6(name, rows):
    t = TOUCH6.get(name)
    if not t or ENGINE[0] != 'c6': return rows
    g = [list(r) for r in rows]; H, W = len(g), len(g[0]); leg = t.get('leg', {})
    def put(y, x, ch):
        if ch == ' ' or not (0 <= y < H and 0 <= x < W): return
        g[y][x] = '.' if ch == '.' else L[leg[ch]]
    for op in t.get('ops', []):
        if op[0] == 'block':
            _, r0, c0, lines = op
            for dy, s in enumerate(lines):
                for dx, ch in enumerate(s): put(r0 + dy, c0 + dx, ch)
        elif op[0] == 'map':                                  # ('map', l0, l1, c0, c1, {código: código}): troca cores só nesse retângulo
            _, r0, r1, c0, c1, mp = op
            ml = {L[a]: L[b] for a, b in mp.items()}
            for y in range(max(0, r0), min(H, r1 + 1)):
                for x in range(max(0, c0), min(W, c1 + 1)):
                    if g[y][x] in ml: g[y][x] = ml[g[y][x]]
        elif op[0] == 'sym':
            _, r0, r1, a2, side, c0, c1 = op
            for y in range(r0, r1 + 1):
                for x in range(c0, c1 + 1):
                    if (side == 'L' and 2 * x < a2) or (side == 'R' and 2 * x > a2):
                        xm = a2 - x
                        if 0 <= xm < W and 0 <= y < H: g[y][xm] = g[y][x]
    return [''.join(r) for r in g]


def run(args, grupo):
    one = []; sheet = []
    for n, g, idx, fn, grp in CFG:
        if grupo and grp != grupo: continue
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = False
            CUR[0] = n
            print('-', n)
            r = touch6(n, fn()); one.append((n, g, r))
            box = getattr(fn, 'box', None)
            sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx, box), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    return one, sheet


if __name__ == '__main__':
    import ast
    argv = sys.argv[1:]
    for opt in ('--H', '--grupo', '--kw', '--kw6', '--tag'):
        if opt in argv: k = argv.index(opt); globals()['_' + opt[2:]] = argv[k + 1]; del argv[k:k + 2]
    args = [a for a in argv if not a.startswith('--')]
    if '--com-boca' in argv: NO_MOUTH[0] = False
    if '--c5' in argv: ENGINE[0] = 'c5'
    if globals().get('_kw6'):
        for p in globals()['_kw6'].split(','):
            a_, b_ = p.split('='); KW6[a_] = ast.literal_eval(b_)
    grupo = globals().get('_grupo')
    if globals().get('_kw'):
        for p in globals()['_kw'].split(','):
            a_, b_ = p.split('='); KW_OVER[a_] = ast.literal_eval(b_)
    one, sheet = run(args, grupo)
    print(len(one), 'moldes de 1 placa')
    tag = globals().get('_tag') or ((grupo or 'all') + ('_f' if args else ''))
    HH = int(globals().get('_H') or 300)
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r29_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r29_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and not KW_OVER and ('--merge' in sys.argv or (not args and not grupo)):
        raw = os.path.join(HERE, 'data', 'final31_raw' + sfx() + '.json')          # nomes do CFG (para --merge)
        old_ = json.load(open(raw, encoding='utf-8')) if os.path.exists(raw) and (args or grupo) else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        order = {n: i for i, (n, *_r) in enumerate(CFG)}
        old_ = [x for x in old_ if x[0] in order]                                     # tira o que saiu do CFG
        old_.sort(key=lambda x: order.get(x[0], 10 ** 6))
        json.dump(old_, open(raw, 'w', encoding='utf-8'), ensure_ascii=False)
        pth = os.path.join(HERE, 'data', 'final31' + sfx() + '.json')              # o que vai para o add_templates: nomes únicos (", versão N" quando já existe ou foi excluído)
        json.dump(uniq(old_), open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravado', pth, len(old_), 'moldes')
    print('ok')
