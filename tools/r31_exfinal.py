"""Remessa 31 (144 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r31_exfinal.py [filtro...] [--grupo ill|folha|graf|foto] [--merge] [--H 520] [--tag nome]
   -> data/final33_raw_120.json (nomes do CFG) e data/final33_120.json (nomes únicos, o que vai para o add_templates). Tudo em 1 placa.
Cópia adaptada do r30_exfinal.py: reaproveita a remessa 29 (r29_exfinal.py: convert6 com contorno preto primeiro, sem boca, retoques de olhos).
Classes (CLAUDE.md §4.1 e §4.8): ~20 gráficos / pixel art / ponto-cruz = cópia 100% fiel (grupo 'graf': o gráfico é copiado conta por conta, só saem fundo, régua e legenda);
o resto são ILUSTRAÇÕES (chibis, cartões, adesivos, fotos de lutadores) = adaptação em 1 placa pelo illus6.convert6 (padrão do dono: contorno preto primeiro), olhos discretos e sem boca.
Folhas com vários personagens (grupo 'folha'): 7 (Eyeshield 21, 8), 40 (2 jogadores), 42 e 84 (trio de Assassination Classroom em cima do Koro-sensei), 47 (3 lutadoras estilo Meninas
Superpoderosas), 51 (6 lutadores WWE), 86 (4 titãs chibi). Ficaram de fora: 8 (arquivo idêntico ao 7, byte a byte), 72 (capa de mangá com 8 personagens) e 104 (colagem de páginas de mangá).
Repetida por MD5 (entra, pedido do dono): 54 (remessa 30), com nome ", versão 2" (veja uniq()).
Fundos: branco = padrão (mask=KM(white)); cor lisa = bg='flat' (KM(flat)); fundo preto (Akame ga Kill) = flat com refs pretos; cena / arena / foto = grabCut (grab()); cartão com enfeites
e figura contornada = outline_mask. KM() mantém só a peça maior da máscara (enfeites soltos, estrelinhas e assinaturas não entram na caixa que define a escala da figura)."""
import os, sys, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r29_exfinal as P
from r29_exfinal import r5, R, L, LAB, OUT, F, fin, lg, np, cv2, Image, tplfile, sfx
import illus
F[:] = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa 31', '*.*')))          # F é a mesma lista de r6.FILES e R.F
P.SKIN6 = {}          # sementes de pele por nome (convert6); as da remessa 29 não valem aqui
P.TOUCH6 = {}         # retoques à mão por nome (preenchidos depois de olhar as folhas: TOUCH31)
CH6 = dict(P.CH)
FIEL = os.environ.get('R31FIEL') == '1'          # regra de 2026-11-06 (topo do CLAUDE.md): segue o desenho, sem tirar a boca nem carimbar olhos; grava tools/data/r31fiel_raw_120.json
KW_FIEL = {}          # nome -> opções a mais da conversão no modo FIEL (máscara, hachura): consertos de CONVERSÃO, não de rosto
V2 = os.environ.get('R31V2') == '1'          # 2ª versão (revisão de 2026-11-06): arte mais suavizada, tons coerentes e limpeza de contas soltas (tools/r31v2.py); grava data/r31v2_raw_120.json
if V2: CH6.update(pre_blur=3, tone_de=30, smooth_de=12)
OM = P.outline_mask
SKIN31 = {}           # nome -> dict(face_seeds=[(l, c)], face_box=(l0, l1, c0, c1), ...) (pele da cor da armadura etc.)
MOUTH31 = {}          # nome -> zona de boca (l0, l1, c0, c1) no molde final do convert6, ou None = não mexe


# ---------------------------------------------------------------- máscaras de fundo (True = fundo)
def white(thr=240):
    """fundo claro (mín. dos canais >= thr) ligado à borda; thr menor também come halos lilás e cinza muito claros"""
    return lambda rgb: illus.sticker_bg(rgb, thr, None)


def flat(refs=None, tol=45, bridge=5):
    """fundo de uma ou mais cores lisas ligado à borda (refs None = mediana da borda). `bridge` = tamanho da dilatação que atravessa a faixa de transição (anti-aliasing) entre duas
    cores de fundo vizinhas (vermelho e amarelo do cartão da imagem 9): sem ela o miolo amarelo ficava de fora da inundação."""
    def f(rgb):
        H, W, _ = rgb.shape
        rr = refs
        if rr is None:
            edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(float)
            rr = [tuple(np.median(edge, axis=0))]
        near = np.zeros((H, W), bool)
        for r in rr: near |= np.linalg.norm(rgb.astype(float) - np.array(r, float), axis=2) < tol
        dil = cv2.dilate(near.astype(np.uint8), np.ones((bridge, bridge), np.uint8)) if bridge else near.astype(np.uint8)
        n, lab = cv2.connectedComponents(dil, connectivity=4)
        ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
        return np.isin(lab, list(ids)) & near
    return f


def hue_bg(h0, h1, smin=0.15, vmin=0.4, white=232):
    """fundo = matiz entre h0 e h1 (graus) com saturação >= smin e valor >= vmin (o oval azul atrás da lutadora), mais o branco quase puro (papel e riscos claros); onde quer que estejam"""
    def f(rgb):
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV_FULL)
        hh = hsv[..., 0].astype(float) * 360.0 / 256.0; ss = hsv[..., 1] / 255.0; vv = hsv[..., 2] / 255.0
        return ((hh >= h0) & (hh <= h1) & (ss >= smin) & (vv >= vmin)) | (rgb.min(axis=2) >= white)
    return f


def floor_shadow(frac=0.22, thr=240):
    """sombra no chão (cinza-claro, pouco colorida) na parte de baixo da imagem também vira fundo, além do branco ligado à borda (foto de estúdio, render com sombra)"""
    def f(rgb):
        m = illus.sticker_bg(rgb, thr, None)
        a = rgb.astype(np.int32); mx = a.max(axis=2); mn = a.min(axis=2)
        sh = ((mx - mn) < 28) & (mx > 120) & (mx < 246)
        sh[:int(rgb.shape[0] * (1 - frac))] = False
        return m | sh
    return f


def sat_bg(smax=0.2, vmin=0.0):
    """fundo = o que tem pouca cor (cinza, branco, preto de página de mangá): saturação <= smax. Para um personagem colorido colado numa colagem de páginas em preto e branco"""
    def f(rgb):
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV_FULL)
        return (hsv[..., 1] / 255.0 <= smax) & (hsv[..., 2] / 255.0 >= vmin)
    return f


def either(*fs):
    """união de máscaras de fundo: é fundo o que qualquer uma delas diz que é"""
    def g(rgb):
        m = fs[0](rgb)
        for f in fs[1:]: m = m | f(rgb)
        return m
    return g


def KM(f, close=0.012):
    """só a peça maior da figura: o que não é fundo é fechado (close = fração do maior lado) e só o maior componente fica; o resto (estrelinhas, respingos, assinatura, enfeites do
    cartão) vira fundo. Sem isto uma estrelinha no canto do cartão entra na caixa da figura e a figura encolhe."""
    def g(rgb):
        m = f(rgb); fg = (~m).astype(np.uint8)
        h, w = fg.shape; k = max(3, int(round(close * max(h, w)))) | 1
        cl = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(cl, connectivity=8)
        if n <= 2: return m
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        return ~((lab == big) & (fg > 0))
    return g


def OMF(idx, box, dark=95, close=7, cut=(), holes=0):
    """máscara pelo contorno (outline_mask) calculada na imagem INTEIRA e depois recortada pela caixa: numa folha em que as figuras se encostam, a caixa cortava o contorno
    (a bola do Koro-sensei) e a inundação entrava na figura. cut = retângulos (x0, y0, x1, y1, em pixels da imagem inteira) que viram fundo (pedaço do vizinho)."""
    def f(rgb):
        im = illus._load(F[idx])
        m = OM(dark, close)(np.pad(im, ((6, 6), (6, 6), (0, 0)), constant_values=255))[6:-6, 6:-6]
        for x0, y0, x1, y1 in cut: m[y0:y1, x0:x1] = True
        if holes:          # branco fechado grande (fundo preso entre cabelo e enfeite) também é fundo; olho e dente são pequenos
            wt = (im.min(axis=2) > 232).astype(np.uint8) & (~m).astype(np.uint8)
            n, lab, st, _ = cv2.connectedComponentsWithStats(wt, connectivity=4)
            for i in range(1, n):
                if st[i, cv2.CC_STAT_AREA] >= holes: m[lab == i] = True
        x0, y0, x1, y1 = box
        return m[y0:y1, x0:x1]
    return f


def grab(rect=None, iters=6):
    """fundo de CENA (arena, sala, foto de estúdio): cv2.grabCut a partir de um retângulo em volta da figura (em pixels da imagem já recortada pela caixa)"""
    def f(rgb):
        h, w = rgb.shape[:2]
        r = rect or (int(w * 0.03), int(h * 0.02), int(w * 0.94), int(h * 0.96))
        mask = np.zeros((h, w), np.uint8); bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(np.ascontiguousarray(rgb[..., ::-1]), mask, tuple(int(v) for v in r), bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)
        return ~((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD))
    return f


def inpaint31(idx, boxes, tag='p'):
    """texto/assinatura por cima do desenho: repinta pela vizinhança (cv2.inpaint) numa cópia temporária; boxes = retângulos (x0, y0, x1, y1) ou função(imagem) -> máscara; devolve o caminho"""
    tmp = os.path.join(OUT, f'_r31{tag}_{idx}.png')
    if not os.path.exists(tmp) or os.path.getmtime(tmp) < os.path.getmtime(__file__):
        im = np.array(illus._load(F[idx]))
        if callable(boxes): m = boxes(im).astype(np.uint8) * 255
        else:
            m = np.zeros(im.shape[:2], np.uint8)
            for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = 255
        Image.fromarray(cv2.inpaint(im, m, 5, cv2.INPAINT_TELEA)).save(tmp)
    return tmp


def rotated31(idx, k):
    """cópia da imagem girada k x 90 graus no sentido horário (a figura está deitada na imagem)"""
    tmp = os.path.join(OUT, f'_r31r{k}_{idx}.png')          # o nome leva o nº de giros (senão duas variantes dividiam o mesmo arquivo)
    if not os.path.exists(tmp) or os.path.getmtime(tmp) < os.path.getmtime(__file__):
        im = Image.fromarray(illus._load(F[idx])); im.rotate(-90 * k, expand=True).save(tmp)
    return tmp


def mouth30(rows):
    """sem boca (§4.8), com os olhos achados pelo _face_eyes: abaixo deles, dentro da casca do rosto, tudo que não é pele e está cercado de pele vira pele"""
    from collections import Counter
    face, hull, eyes = P._face_eyes(rows)
    if face is None or eyes is None: return rows, 0
    H, W = len(rows), len(rows[0])
    ys, xs = np.nonzero(face); fy1 = ys.max()
    ey, ex0, ex1 = eyes
    g = [list(r) for r in rows]; n = 0
    for _ in range(6):
        todo = []
        for y in range(ey + 1, min(H, fy1 + 2)):
            for x in range(max(0, ex0 - 1), min(W, ex1 + 2)):
                c = g[y][x]
                if c == '.' or c in P.SKIN or not hull[y, x]: continue
                nb = [(v, u) for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= v < H and 0 <= u < W]
                if any(g[v][u] == '.' for v, u in nb): continue
                ns = sum(1 for v, u in nb if g[v][u] in P.SKIN)
                ns8 = sum(1 for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1) if (v, u) != (y, x) and 0 <= v < H and 0 <= u < W and g[v][u] in P.SKIN)
                dark = LAB[c][0] < 52
                if (not dark and (ns >= 2 or (ns >= 1 and ns8 >= 4))) or (dark and ns >= 3): todo.append((y, x))
        if not todo: break
        for y, x in todo:
            cnt = Counter(g[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1)) if 0 <= v < H and 0 <= u < W and g[v][u] in P.SKIN)
            if cnt: g[y][x] = cnt.most_common(1)[0][0]; n += 1
    return [''.join(r) for r in g], n


def mouth_hole(rows):
    """sem olhos achados: o "buraco" na pele (peça que não é pele, cercada só de pele) mais baixo e centralizado do rosto, abaixo da metade dele, vira pele"""
    from collections import Counter
    import scipy.ndimage as ndi
    face, hull, eyes = P._face_eyes(rows)
    if face is None: return rows, 0
    H, W = len(rows), len(rows[0])
    ys, xs = np.nonzero(face); fy0, fy1, fx0, fx1 = ys.min(), ys.max(), xs.min(), xs.max()
    fh, fw = fy1 - fy0 + 1, fx1 - fx0 + 1; cx = (fx0 + fx1) / 2.0
    skin = np.array([[c in P.SKIN for c in r] for r in rows]); ne = np.array([[c != '.' for c in r] for r in rows])
    lab, n = ndi.label(hull & ~skin & ne)
    best = None
    for i in range(1, n + 1):
        hy, hx = np.nonzero(lab == i)
        touch = False
        for y, x in zip(hy, hx):
            for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if not (0 <= v < H and 0 <= u < W) or not hull[v, u] or not ne[v, u] or (not skin[v, u] and lab[v, u] != i): touch = True; break
            if touch: break
        if touch: continue
        my, mx_ = hy.mean(), hx.mean()
        if abs(mx_ - cx) > max(2.0, 0.2 * fw) or my < fy0 + 0.5 * fh or len(hy) > 0.15 * face.sum(): continue
        if best is None or my > best[0]: best = (my, i, len(hy))
    if not best: return rows, 0
    g = [list(r) for r in rows]
    for y, x in zip(*np.nonzero(lab == best[1])):
        cnt = Counter(rows[v][u] for v, u in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1)) if 0 <= v < H and 0 <= u < W and skin[v, u])
        if cnt: g[y][x] = cnt.most_common(1)[0][0]
    return [''.join(r) for r in g], best[2]


def no_mouth31(rows):
    r, n = mouth30(rows)
    how = 'abaixo dos olhos'
    if not n:
        r, n = mouth_hole(rows); how = 'buraco na pele'
    if n: print(f'    boca tirada: {n} contas ({how})')
    return r


EYE_INFO = {}         # nome -> informação dos olhos medidos (r31_eyes.auto_eyes)
GEOM_DIR = os.path.join(OUT, 'r31fiel_geom' if FIEL else 'r31v2_geom' if V2 else 'r31_geom')


def geom_path(nm):
    import re
    return os.path.join(GEOM_DIR, re.sub(r'[^a-z0-9]+', '_', nm.lower())[:80] + '.npz')


def save_geom(nm, G, idx, box, rotate):
    """grava (npz comprimido, descartável) a saída do convert6 e a arte alinhada: rows do convert6, a imagem recortada (raw), a máscara da figura (fg) e os números da grade"""
    os.makedirs(GEOM_DIR, exist_ok=True)
    np.savez_compressed(geom_path(nm), raw=G['raw'], fg=G['fg'], rows=np.array(G['rows']), idx=idx, box=np.array(box if box else (-1, -1, -1, -1)), rotate=rotate,
                        **{k: G[k] for k in ('x0', 'y0', 'w', 'h', 'nw', 'nh', 'top', 'left')})


def load_geom(nm):
    z = np.load(geom_path(nm), allow_pickle=False)
    G = {k: int(z[k]) for k in ('x0', 'y0', 'w', 'h', 'nw', 'nh', 'top', 'left')}
    G.update(raw=z['raw'], fg=z['fg'], rows=[str(r) for r in z['rows']], idx=int(z['idx']), box=tuple(int(v) for v in z['box']), rotate=int(z['rotate']))
    return G


def I(idx, box=None, skin=True, post=None, clear=(), paint=None, mouth=False, base=None, rotate=0, km=True, eyes=None, **kw):
    """ilustração: illus6.convert6 pelo ill6 da remessa 29 (CH6 + kw), depois sem boca (zona MOUTH31[nome] ou a busca automática pelos olhos, §4.8).
    Sem `mask`: fundo claro ligado à borda (thr) ou, com bg='flat', cor lisa (refs/tol); KM() descarta enfeites soltos. rotate = giros de 90 graus no sentido horário antes de converter."""
    def f():
        a = dict(base or CH6); a.update(kw)
        if FIEL: a.update(KW_FIEL.get(P.CUR[0], {}))
        if 'mask' in a:
            if km: a['mask'] = KM(a['mask'])
        elif a.get('bg') != 'none':
            m0 = flat(a.get('refs'), a.get('tol', 45)) if a.get('bg') == 'flat' else white(a.get('thr', 240))
            a['mask'] = KM(m0) if km else m0
        old = F[idx]
        if rotate: F[idx] = rotated31(idx, rotate)
        if paint: F[idx] = inpaint31(idx, paint, 'p' if not rotate else 'q')
        try: r = P.ill6(idx, a, box=box, clear=clear, skin=skin)
        finally: F[idx] = old
        nm = P.CUR[0]
        import illus6
        save_geom(nm, dict(illus6.LAST_GEOM), idx, box, rotate)          # geometria da conversão (para as folhas de rostos alinhadas e para testar o detector de olhos sem reconverter)
        if eyes:          # olhos no modelo da Rei, medidos na arte (r31_eyes.py), aplicados na hora (padrão: NÃO; o carimbo é decidido molde a molde em EYES31 e aplicado por cima do JSON)
            import illus6, r31_eyes as EY
            r, info = EY.auto_eyes(r, dict(illus6.LAST_GEOM), P, L, LAB); EYE_INFO[nm] = info
            if not info.get('pair'): print('    olhos: não achei (%s)' % info.get('why'))
        if post: r = post(r)
        if V2:
            import r31v2; r = r31v2.clean(r)
        if skin and not mouth and not FIEL and not (nm in MOUTH31 and MOUTH31[nm] is None):
            r = P.paint_mouth6(r, MOUTH31[nm], verbose=True) if MOUTH31.get(nm) else no_mouth31(r)
        return fin(lg(r))
    f.box = box; f.rot = rotate
    return f


# ---------------------------------------------------------------- nomes (séries = nome da categoria na galeria; as novas viram categoria nova)
AOT = 'Attack on Titan'; AC = 'Assassination Classroom'; E21 = 'Eyeshield 21'; DB = 'Dragon Ball'; NAR = 'Naruto'; WWE = 'WWE'; AK = 'Akame ga Kill'; HEL = 'Hellsing'; BEN = 'Ben 10'
AB = 'Angry Birds'; HP = 'Harry Potter'; GEN = 'Genéricos'; TOY = 'Toy Story'; KB = 'Kuroko no Basket'; OP = 'One Piece'; MHA = 'My Hero Academia'; PP = 'Meninas Superpoderosas'
CFG = []


def add(idx, name, serie, grp='ill', **kw):
    CFG.append((name, serie, idx, I(idx, **kw), grp))


def carpet_feet(rows):
    """restos de carpete (marrom escuro, marrom-acinzentado) nas 12 últimas linhas, entre e ao lado das botas: viram vazio (o bege M9 dos rebites das botas fica); depois só a maior peça"""
    H = len(rows)
    bad = {L[c] for c in ('F11', 'G8', 'G17', 'M5', 'M6')}
    g = [''.join('.' if (y >= H - 12 and c in bad) else c for c in r) for y, r in enumerate(rows)]
    return lg(g)


# ---- ilustrações de uma figura
add(0, 'Heatblast (Ben 10, chibi)', BEN, bg='flat', tol=45, paint=[(240, 620, 340, 730)], skin=False)
add(1, 'Anya Forger (Spy x Family, chibi, manto da Akatsuki)', 'Spy x Family', mask=P.grad_mask(6))
add(2, 'Sena Kobayakawa (Eyeshield 21, desenho, correndo com a bola)', E21)
add(3, 'Kuririn (Dragon Ball, chibi, cartão amarelo)', DB, bg='flat', tol=50)
add(4, 'Alienígena de chef de avental branco (Ben 10, chibi)', BEN, bg='flat', tol=45, skin=False)
add(5, 'Nagisa Shiota (Assassination Classroom, chibi, faca na boca)', AC, bg='flat', refs=[(255, 255, 255), (55, 150, 225)], tol=50)          # o adesivo tem um contorno azul grosso: branco e azul-do-contorno são fundo
add(6, 'Armin Arlert (Attack on Titan, chibi, polegar para cima)', AOT, bg='flat', tol=40)
add(9, 'Garoto de cabelo verde e casaco verde (chibi, fones vermelhos)', GEN, bg='flat', refs=[(139, 33, 33), (235, 220, 125)], tol=40)
add(10, 'Garota de cabelo laranja e olhos vermelhos (Akame ga Kill, chibi, fundo preto)', AK, bg='flat', refs=[(0, 0, 0)], tol=30)
add(12, 'Lutador de máscara de palhaço e crista laranja (Lucha Libre, chibi)', WWE)
add(13, 'Rey Mysterio (WWE, chibi, máscara preta)', WWE)
add(14, 'Lutadora loira de cabelo ondulado (WWE, chibi, estilo Meninas Superpoderosas)', WWE, mask=grab())
add(15, 'Erwin Smith (Attack on Titan, chibi)', AOT, bg='flat', tol=75)
add(16, 'Trunks (Dragon Ball, chibi, cartão lilás)', DB, mask=grab())
add(17, 'Garota de cabelo verde-menta e fones de gato (chibi)', GEN, thr=205, peel=1.0)
add(18, 'Titã Colossal (Attack on Titan, chibi, fundo de vapor)', AOT, mask=grab(), skin=False)
add(20, 'Rei Porco (Angry Birds)', AB, skin=False)
add(21, 'Sarada Uchiha (Naruto, chibi)', NAR)
add(22, 'Sasuke Uchiha (Naruto, chibi, katana e faixa na testa)', NAR, clear=[(640, 0, 736, 90)])
add(23, 'Nagisa Shiota (Assassination Classroom, chibi, capa)', AC)
add(24, 'Kaede Kayano (Assassination Classroom, chibi)', AC)
add(25, 'Criatura de pétalas vermelhas e olhos verdes (chibi)', BEN, bg='flat', tol=45, skin=False)
add(26, 'Sarada Uchiha (Naruto, chibi, fundo rosa)', NAR, bg='flat', refs=[(245, 71, 106), (250, 200, 215)], tol=45)          # o contorno rosa-claro do adesivo também é fundo
add(27, 'Grande Saiyaman (Dragon Ball, chibi)', DB)
add(28, 'Paige (WWE, foto, com o cinturão)', WWE, mask=grab())
add(29, 'John Cena (WWE, chibi)', WWE)
add(30, 'Roman Reigns (WWE, chibi, arena)', WWE, mask=grab())
add(31, 'Piccolo (Dragon Ball, chibi, cartão verde)', DB, bg='flat', tol=50, skin=False)
add(32, 'Lutador de máscara verde e amarela (Lucha Libre, chibi)', WWE)
add(33, 'Hanamichi Sakuragi (Slam Dunk, chibi, fundo vermelho)', 'Slam Dunk', box=(270, 470, 920, 1660), mask=grab())
add(34, 'Alucard (Hellsing, chibi, copo de sangue)', HEL)
add(35, 'Alienígena roxo de tentáculos e raios (chibi)', BEN, bg='flat', tol=45, skin=False)
add(36, 'Annie Leonhart (Attack on Titan, chibi)', AOT)
add(37, 'Seth Rollins (WWE, chibi)', WWE, mask=OM())
add(39, 'Eren Yeager (Attack on Titan, chibi, forma de titã)', AOT, skin=False)
add(41, 'Godzilla (chibi, sopro atômico rosa)', 'Godzilla', skin=False)
add(44, 'Akame (Akame ga Kill, chibi)', AK)
add(46, 'Passarinho vermelho de laço amarelo (Angry Birds)', AB, skin=False)
add(48, 'Garota de cabelo prateado e gorro preto (chibi, fundo estrelado)', GEN, bg='flat', tol=70)
add(50, 'Boruto Uzumaki (Naruto, chibi, fundo rosa)', NAR, mask=OM())
add(52, 'Jinx (Arcane, chibi)', 'Arcane')
add(53, 'Mikasa Ackerman (Attack on Titan, chibi)', AOT, mask=OM(dark=120))          # o círculo cinza atrás dela não é desenho
add(54, 'Koro-sensei (Assassination Classroom, chibi, debochando)', AC, skin=False)
add(55, 'Lutador de capuz e tatuagens (WWE, chibi)', WWE)
add(56, 'Omnitrix (Ben 10, emblema)', BEN, skin=False)
add(57, 'Titã Colossal (Attack on Titan, chibi, vapor)', AOT, skin=False)
add(58, 'Lutadora de cabelo preto e cinturão (WWE, desenho)', WWE, mask=hue_bg(175, 225))          # o oval azul atrás dela sai pelo matiz
add(59, 'Sena Kobayakawa (Eyeshield 21, desenho, capacete verde)', E21)
add(61, 'Annie Leonhart (Attack on Titan, chibi, forma de titã)', AOT)
add(62, 'Hisoka (Hunter x Hunter, chibi, sentado com carta)', 'Hunter x Hunter', bg='flat', tol=45)
add(64, 'Chuck (Angry Birds, pássaro amarelo)', AB, skin=False)
add(65, 'Lutadora de cabelo preto (WWE, chibi, estilo Meninas Superpoderosas)', WWE, mask=grab())
add(66, 'Chi-Chi (Dragon Ball, chibi, cartão rosa)', DB, bg='flat', tol=45)
add(67, 'Vegeta (Dragon Ball, chibi, cartão azul)', DB, bg='flat', tol=50)
add(68, 'Alucard (Hellsing, chibi, pistolas e morcegos)', HEL)
add(69, 'Passarinho azul (Angry Birds)', AB, skin=False)
add(70, 'Sakura Haruno (Naruto, corpo inteiro, vestido vermelho)', NAR)
add(71, 'Sakura Haruno (Naruto, corpo inteiro, roupa branca e vermelha)', NAR)
add(73, 'Lutadora de cabelo escuro e botas (WWE, desenho)', WWE, bg='flat', tol=45)
add(74, 'Taro Raimon, o Monta (Eyeshield 21, chibi, medalha)', E21)
add(75, 'Mine (Akame ga Kill, chibi, fundo preto)', AK, bg='flat', refs=[(0, 0, 0)], tol=30)
add(76, 'Eren Yeager (Attack on Titan, chibi, cabelo preso)', AOT)
add(77, 'Tatsumi (Akame ga Kill, chibi, fundo preto)', AK, bg='flat', refs=[(0, 0, 0)], tol=30)
add(78, 'Hal (Angry Birds, tucano)', AB, skin=False)
add(79, 'Freeza (Dragon Ball, chibi, cartão marrom)', DB, box=(150, 420, 580, 1230), mask=OM(dark=95), skin=False, line_L=50.0, line_C=45.0, t_line=0.07)          # o traço do Freeza é marrom-arroxeado (croma alto): limite de traço mais largo
add(81, 'Paige (WWE, chibi, foto de peça de contas pronta)', WWE, bg='flat', tol=70, refs=[(160, 135, 105), (120, 100, 75)], eyes=False, skin=False, K=44, smooth_de=10.0,
    post=lambda r: carpet_feet(r))          # FOTO de peça pronta sobre carpete (~54x98 contas): leitura aproximada pela ilustração (convert6), sem a regra de pele (o rosto é BRANCO, não bege); o carpete que sobra junto dos pés sai
add(82, 'Alienígena de cabeça em chamas verdes (Ben 10, chibi)', BEN, skin=False)
add(83, 'Sasha Braus (Attack on Titan, chibi, comendo)', AOT)
add(85, 'Karma Akabane (Assassination Classroom, chibi, orelhas de gato)', AC)
add(87, 'Paige (WWE, foto, em pé)', WWE, box=(330, 90, 700, 1010), mask=floor_shadow(0.6, 235))          # a sombra cinza do chão (degradê do estúdio) não é desenho
add(89, 'Sena Kobayakawa (Eyeshield 21, chibi, correndo)', E21)
add(90, 'Medalhão dourado com a letra P', GEN, skin=False)
add(91, 'Hiruma Yoichi (Eyeshield 21, chibi, metralhadora)', E21)
add(92, 'Brock Lesnar (WWE, desenho)', WWE)
add(94, 'Itachi Uchiha (Naruto, chibi, gorro de Natal)', NAR)
add(95, 'Tetsuya Kuroko (Kuroko no Basket, chibi, sentado)', KB)
add(97, 'Criatura azul de capuz de cristal (chibi)', BEN, bg='flat', tol=45, skin=False)
add(98, 'Madara Uchiha (Naruto, chibi, Seis Caminhos)', NAR)
add(99, 'Garota de cabelo laranja e gorro de Natal (chibi, fones)', GEN)
add(101, 'Majin Boo (Dragon Ball, chibi, cartão rosa)', DB, mask=OM(dark=100), skin=False)          # o corpo rosa é parecido com o fundo rosa: o fundo é o que fica fora do contorno escuro
add(102, 'Garoto de cabelo laranja e capa azul (Assassination Classroom, chibi)', AC)
add(103, 'Sasuke Uchiha (Naruto, chibi, manto escuro e katana)', NAR)
add(105, 'Bomba (Angry Birds, pássaro preto)', AB, skin=False)
add(106, 'Koro-sensei (Assassination Classroom, adesivo, com cartas)', AC, thr=205, peel=1.0, skin=False)
add(107, 'Hyakkimaru (Dororo, chibi)', 'Dororo')
add(108, 'Lutadora loira (WWE, chibi, estilo Meninas Superpoderosas, fundo colorido)', WWE, mask=grab())
add(109, 'Paige (WWE, foto, traje verde)', WWE, mask=either(floor_shadow(0.6, 225), grab()))
add(111, 'Akame (Akame ga Kill, chibi, fundo preto)', AK, bg='flat', refs=[(0, 0, 0)], tol=30)
add(112, 'Lutador de pele azul, bermuda vermelha e katana (chibi)', GEN, skin=False)
add(113, 'Tetsuya Kuroko (Kuroko no Basket, chibi, uniforme azul)', KB)
add(114, 'Karma Akabane (Assassination Classroom, chibi, capa)', AC)
add(115, 'Alienígena de cartola cinza e olhos verdes (Ben 10, vetor)', BEN, skin=False)
add(116, 'Titã Colossal (Attack on Titan, em círculo)', AOT, skin=False)
add(117, 'Lelouch Lamperouge (Code Geass, chibi, gorro de Natal)', 'Code Geass')
add(118, 'Vegeta (Dragon Ball, chibi, cartão azul estrelado)', DB, bg='flat', tol=45)
add(119, 'Zatch Bell (Zatch Bell!, chibi)', 'Zatch Bell!')
add(120, 'Goku (Dragon Ball, chibi, cartão azul)', DB, bg='flat', tol=45)
add(121, 'Lutador de cabelo espetado e jaqueta preta (WWE, chibi)', WWE)
add(122, 'Gohan (Dragon Ball, chibi, cartão roxo)', DB, bg='flat', tol=50)
add(123, 'Hiruma Yoichi (Eyeshield 21, chibi, bola)', E21)
add(124, 'Androide 17 (Dragon Ball, chibi, cartão laranja)', DB, bg='flat', tol=50)
add(126, 'Motoqueiro Fantasma (Marvel, chibi)', 'Marvel', mask=either(P.grad_mask(8), P.color_mask((100, 100, 130), 32, [((70, 70, 72), 12)])), skin=False)          # o brilho azul-violeta do fundo, também dentro da corrente
add(127, 'Homem de cabelo vermelho e terno escuro (chibi, fundo vermelho e branco)', GEN, mask=grab())
add(128, 'Eren Yeager (Attack on Titan, chibi, tropa de exploração)', AOT, box=(40, 190, 660, 1190), mask=OM(dark=110))          # a cena (casas, nuvens) e o titã pequeno do canto ficam fora
add(129, 'Esdeath (Akame ga Kill, chibi, fundo preto)', AK, bg='flat', refs=[(0, 0, 0)], tol=30)
add(130, 'Alucard (Hellsing, chibi, bolsa de sangue)', HEL)
add(132, 'All Might (My Hero Academia, chibi, forma magra)', MHA)
add(133, 'Rey Mysterio (WWE, chibi, máscara branca e vermelha)', WWE)
add(134, 'Esdeath (Akame ga Kill, chibi, chapéu branco)', AK, thr=225)
add(135, 'Leone (Akame ga Kill, chibi, fundo preto)', AK, bg='flat', refs=[(0, 0, 0)], tol=30, rotate=1)
add(136, 'Lutador de máscara azul-clara (Lucha Libre, chibi)', WWE)
add(138, 'Nami (One Piece, chibi, cartão rosa)', OP, bg='flat', tol=45)
add(140, 'Godzilla (chibi, sopro azul)', 'Godzilla', skin=False)
add(141, 'Taro Raimon, o Monta (Eyeshield 21, chibi, de fundo transparente)', E21)
add(142, 'Suzuna Taki (Eyeshield 21, chibi, pompons e asas)', E21)
add(143, 'Sena Kobayakawa (Eyeshield 21, desenho, correndo de capacete)', E21)

# ---- folhas com vários personagens (grupo 'folha'): caixas em pixels (tools/r31_boxes.py, conferidas olhando tools/out/abox31_N.png)
FOLHAS = [
 # idx, série, kw da folha, [(nome, caixa, skin, kw extra)]
 (7, E21, dict(thr=222), [('Cerberus (Eyeshield 21, cachorro, folha 3)', (424, 56, 586, 233), False, {}),
                          ('Jogador de cabelo preto espetado e nº 16 (Eyeshield 21, chibi, folha 3)', (161, 161, 413, 407), True, {}),
                          ('Sena Kobayakawa (Eyeshield 21, chibi, de capacete verde, folha 3)', (625, 6, 885, 307), True, {}),
                          ('Hiruma Yoichi (Eyeshield 21, chibi, metralhadora, folha 3)', (681, 279, 978, 575), True, {}),
                          ('Suzuna Taki (Eyeshield 21, chibi, patins, folha 3)', (9, 393, 319, 820), True, {}),
                          ('Mamori Anezaki (Eyeshield 21, chibi, vassoura, folha 3)', (306, 238, 724, 668), True, {}),
                          ('Ryokan Kurita (Eyeshield 21, chibi, com Komusubi, folha 3)', (300, 588, 557, 861), True, {}),
                          ('Irmãos Ha-Ha (Eyeshield 21, chibi, folha 3)', (632, 600, 992, 838), True, {})]),
 (40, E21, dict(thr=240), [('Jogador de uniforme azul nº 41 (futebol americano, chibi)', (60, 60, 310, 620), True, {}),
                           ('Jogador de uniforme azul-gelo (futebol americano, chibi)', (385, 60, 640, 620), True, {})]),
 (51, WWE, dict(), [('Goldberg (WWE, desenho)', (125, 2, 352, 435), True, {}), ('Roman Reigns (WWE, desenho)', (402, 0, 660, 436), True, {}),
                    ('Dean Ambrose (WWE, desenho)', (85, 442, 330, 876), True, {}), ('Brock Lesnar (WWE, desenho, sem camisa)', (374, 440, 669, 878), True, {}),
                    ('Rey Mysterio (WWE, desenho, calça 619)', (122, 873, 350, 1308), True, {}), ('Seth Rollins (WWE, desenho)', (429, 878, 624, 1308), True, {})]),
 (86, AOT, dict(skin=False), [('Eren Yeager (Attack on Titan, chibi, titã, folha)', (10, 261, 207, 566), False, {}), ('Reiner Braun (Attack on Titan, chibi, Titã Blindado, folha)', (226, 285, 385, 564), False, {}),
                              ('Titã Colossal (Attack on Titan, chibi, folha)', (427, 239, 587, 571), False, {}), ('Zeke Yeager (Attack on Titan, chibi, Titã Bestial, folha)', (592, 282, 823, 574), False, {})]),
 (42, AC, dict(mask=OM()), [('Kayano em cima de um Koro-sensei verde (Assassination Classroom, chibi, trio)', (15, 10, 168, 352), True, dict(mask=OMF(42, (15, 10, 168, 352), cut=[(160, 160, 168, 352)], holes=300)) if V2 else {}),
                            ('Nagisa em cima de um Koro-sensei amarelo (Assassination Classroom, chibi, trio)', (160, 40, 335, 352) if V2 else (170, 40, 335, 372), True, dict(mask=OMF(42, (160, 40, 335, 352), cut=[(160, 200, 166, 352), (322, 200, 335, 352), (298, 168, 335, 216)], holes=300)) if V2 else {}),
                            ('Karma em cima de um Koro-sensei vermelho (Assassination Classroom, chibi, trio)', (316, 25, 495, 352) if V2 else (320, 30, 492, 372), True, dict(mask=OMF(42, (316, 25, 495, 352), cut=[(470, 168, 495, 222)], holes=300)) if V2 else {})]),
 (84, AC, dict(mask=OM()), [('Kayano em cima de um Koro-sensei listrado (Assassination Classroom, chibi, lápis de cor)', (30, 15, 350, 670) if V2 else (35, 15, 355, 695), True, dict(mask=OMF(84, (30, 15, 350, 670), cut=[(336, 300, 350, 670), (322, 318, 350, 402)], holes=600)) if V2 else {}),
                            ('Nagisa em cima de um Koro-sensei amarelo (Assassination Classroom, chibi, lápis de cor)', (330, 100, 628, 670) if V2 else (325, 105, 630, 695), True, dict(mask=OMF(84, (330, 100, 628, 670), cut=[(590, 315, 628, 402), (330, 390, 340, 670)], holes=600)) if V2 else {}),
                            ('Karma em cima de um Koro-sensei branco (Assassination Classroom, chibi, lápis de cor)', (605, 95, 935, 670) if V2 else (600, 95, 935, 695), True, dict(mask=OMF(84, (605, 95, 935, 670), cut=[(896, 330, 935, 410), (605, 390, 618, 670)])) if V2 else {})]),
 (47, WWE, dict(mask=OM()), [('Lutadora loira (WWE, estilo Meninas Superpoderosas, trio)', (0, 125, 345, 470), True, dict(mask=OMF(47, (0, 125, 345, 470), cut=[(290, 125, 345, 212)])) if V2 else {}), ('Becky Lynch (WWE, estilo Meninas Superpoderosas, trio)', (285, 25, 605, 420), True, dict(mask=OMF(47, (285, 25, 605, 420), cut=[(285, 232, 332, 420), (572, 130, 605, 420)])) if V2 else {}),
                             ('Paige (WWE, estilo Meninas Superpoderosas, trio)', (555, 105, 862, 485), True, dict(mask=OMF(47, (555, 105, 862, 485), cut=[(555, 105, 585, 215)])) if V2 else {})]),
]
for _idx, _ser, _kw, _items in FOLHAS:
    for _n, _b, _skin, _ex in _items:
        a = dict(_kw); a.update(_ex); a.setdefault('skin', _skin)
        CFG.append((_n, _ser, _idx, I(_idx, box=_b, **a), 'folha'))


# ---------------------------------------------------------------- gráficos / pixel art / ponto-cruz: cópia fiel (grupo 'graf') e foto de peça pronta ('foto'): preenchidos em r31_graf.py
try:
    import r31_graf as GR31
    CFG += GR31.items(sys.modules[__name__])
except ImportError:
    pass


# ---------------------------------------------------------------- nomes únicos contra o catálogo de ANTES da remessa (backups/pre-r31.js)
def uniq(items):
    base = os.path.join(HERE, 'backups', 'pre-r31.js')
    d = tplfile.parse(base if os.path.exists(base) else os.path.join(os.path.dirname(HERE), 'templates.js'))
    taken = {t['name'] for t in d['items']} | set(d.get('removed') or [])
    out = []; seen = set()
    for it in items:
        n = it[0]; k = 2
        while n in taken or n in seen: n = P._with_version(it[0], k); k += 1
        if n != it[0]: print(f'  nome ajustado: {it[0]} -> {n}')
        seen.add(n); out.append([n] + list(it[1:]))
    return out


EYES31 = {n: 'auto' for n in (          # rostos em que o par achado pelo detector CONFERE com a arte (olhos abertos, sem óculos, mecha, máscara nem piscada): olho no modelo da Rei, medido na arte
    'Armin Arlert (Attack on Titan, chibi, polegar para cima)', 'Erwin Smith (Attack on Titan, chibi)', 'Nagisa Shiota (Assassination Classroom, chibi, capa)',
    'Kaede Kayano (Assassination Classroom, chibi)', 'Roman Reigns (WWE, chibi, arena)', 'Annie Leonhart (Attack on Titan, chibi)', 'Eren Yeager (Attack on Titan, chibi, cabelo preso)',
    'Karma Akabane (Assassination Classroom, chibi, orelhas de gato)', 'Tetsuya Kuroko (Kuroko no Basket, chibi, sentado)', 'Garoto de cabelo laranja e capa azul (Assassination Classroom, chibi)',
    'Hiruma Yoichi (Eyeshield 21, chibi, bola)', 'Androide 17 (Dragon Ball, chibi, cartão laranja)', 'Eren Yeager (Attack on Titan, chibi, tropa de exploração)',
    'Jogador de cabelo preto espetado e nº 16 (Eyeshield 21, chibi, folha 3)', 'Mamori Anezaki (Eyeshield 21, chibi, vassoura, folha 3)')}
_EYES31_DOC = "nome -> 'auto'"          # (o formato: nome -> 'auto' = par do detector; ou (linha_esq, col_esq, linha_dir, col_dir, largura, altura) medidos na folha de rostos, r31_eyecheck.py)

EYES31.update({          # olhos à mão: (linha_esq, col_esq, linha_dir, col_dir, largura, altura[, 'tiny2']) = canto de cima à esquerda de cada olho, medidos com tools/r31_probe.py (cor da arte por conta)
    'Trunks (Dragon Ball, chibi, cartão lilás)': (18, 6, 18, 13, 3, 4),                    # íris azul embaixo do branco do olho (olhando para baixo)
    'Androide 17 (Dragon Ball, chibi, cartão laranja)': (21, 8, 21, 16, 3, 4),            # olhos azuis grandes de cílio grosso
    'Alucard (Hellsing, chibi, bolsa de sangue)': (9, 7, 9, 12, 2, 3, 'tiny2'),          # íris vermelho-laranja de 2 contas
})

def eyes31(name, rows):
    """aplica o modelo de olho da Rei (EYES31) por cima do molde, usando a geometria salva da conversão (data tools/out/r31_geom)"""
    spec = EYES31.get(name)
    if not spec or not os.path.exists(geom_path(name)): return rows
    import r31_eyes as EY
    G = load_geom(name)
    if spec == 'auto': new, info = EY.auto_eyes(rows, G, P, L, LAB, verbose=True)
    else: new, info = EY.stamp_manual(rows, G, P, L, LAB, *spec, verbose=True)
    if info.get('why'): print('    olhos (%s): NÃO aplicado: %s' % (name, info['why']))
    return new


TOUCH31 = {          # retoques à mão no molde final (olhos etc.), mesmo formato do TOUCH6 da remessa 29 (coordenadas do data/final33_raw_120.json)
    # Sasuke (katana): o convert6 perdeu os dois olhos. Medidos na arte (r31_probe.py): olho esquerdo vermelho (Sharingan) em 2x2 nas linhas 14-15, colunas 5-6; olho direito cinza com ondas (Rinnegan) em 3x2, colunas 12-14
    'Sasuke Uchiha (Naruto, chibi, katana e faixa na testa)': dict(leg={'W': 'H2', 'F': 'F5', 'G': 'F8', 'L': 'H4', 'M': 'H5'}, ops=[('block', 14, 5, ['WF', 'GF']), ('block', 14, 12, ['LML', 'MLM'])]),
    # Hisoka: olhos estreitos de íris dourada (G5): o esquerdo nas linhas 20-21 (colunas 13-15), o direito, mais baixo (cabeça inclinada), nas linhas 22-23 (colunas 20-22)
    'Hisoka (Hunter x Hunter, chibi, sentado com carta)': dict(leg={'k': 'H7', 'A': 'G5', 'W': 'H2'}, ops=[('block', 20, 14, ['k']), ('block', 21, 13, ['AAW']), ('block', 22, 21, ['kk']), ('block', 23, 20, ['AWW'])]),
    # Goldberg: as duas contas escuras sob a sobrancelha (medidas na arte: linha 5, colunas 14 e 16) com o castanho do meio
    'Goldberg (WWE, desenho)': dict(leg={'k': 'H7', 'F': 'F11'}, ops=[('block', 5, 14, ['kFk'])]),
    # Nami: a conversão perdeu os dois olhos (pele e cabelo alaranjados). Medidos na arte ampliada com régua: olho aberto (castanho-alaranjado, brilho no alto à esquerda) nas linhas 11-13, colunas 19-22;
    # olho piscando (arco com cílio) nas linhas 13-14, colunas 13-15
    'Nami (One Piece, chibi, cartão rosa)': dict(leg={'K': 'H7', 'W': 'H2', 'H': 'H2', 'D': 'G8', 'M': 'F10', 'L': 'G5'}, ops=[('block', 11, 19, ['KKKK', 'WHDK', 'WMDL']), ('block', 13, 13, [' K ', 'K K'])]),
    # dentes do sorriso largo que a zona automática não pegou (§4.8: sem dentes em 1 placa)
    'Tatsumi (Akame ga Kill, chibi, fundo preto)': dict(leg={}, ops=[('map', 29, 32, 10, 21, {'M9': 'G1', 'H2': 'G1', 'H3': 'G1'})]),
    'Leone (Akame ga Kill, chibi, fundo preto)': dict(leg={}, ops=[('map', 30, 33, 14, 29, {'M9': 'E11', 'H1': 'E11', 'H4': 'E11'})]),
}

# BOCA ABERTA que a busca automática não achou: zona (linha 0, linha 1, coluna 0, coluna 1) do molde FINAL em que tudo o que não é pele vira a pele do rosto (P.paint_mouth).
# Aplicadas POR CIMA do data/final33_raw_120.json com  python tools/r31_exfinal.py --touch  (a conversão não é reproduzível conta a conta: nunca reconverter para retocar)
POST31 = {
    'Kuririn (Dragon Ball, chibi, cartão amarelo)': (19, 25, 5, 20),          # boca aberta com língua
    'Akame (Akame ga Kill, chibi, fundo preto)': (26, 32, 7, 18),          # sorriso de dentes
    'Hiruma Yoichi (Eyeshield 21, chibi, bola)': (21, 23, 8, 16),          # sorriso de dentes
    'Lutadora de cabelo preto (WWE, chibi, estilo Meninas Superpoderosas)': (14, 19, 14, 21),          # boca aberta
    'Nami (One Piece, chibi, cartão rosa)': (16, 17, 16, 20),          # sorriso aberto rosa
    'Goku (Dragon Ball, chibi, cartão azul)': (20, 22, 18, 22),          # boca aberta com língua (F12)
    'Hiruma Yoichi (Eyeshield 21, chibi, metralhadora)': (28, 30, 7, 12),          # dentes
    'Lelouch Lamperouge (Code Geass, chibi, gorro de Natal)': (26, 28, 24, 29),          # boca aberta com língua
    'Jinx (Arcane, chibi)': (22, 23, 17, 22),          # boca aberta gritando
    'Brock Lesnar (WWE, desenho, sem camisa)': (8, 9, 14, 18),          # grito, dentes
    'Suzuna Taki (Eyeshield 21, chibi, patins, folha 3)': (17, 19, 13, 17),          # boca aberta com língua
    'Suzuna Taki (Eyeshield 21, chibi, pompons e asas)': (20, 23, 22, 25),          # boca aberta com língua
}


H1_FORCE = {'Rey Mysterio (WWE, chibi, máscara branca e vermelha)': 24}          # a máscara branca é o rosto dele: todo H1 até esta linha vira o branco H2


def h1_small(name, rows):
    """o branco do olho, o dente e o brilho são H2 (a conta transparente H1 nunca): grupo pequeno de H1 (até 6 contas) encostado em conta escura na parte de CIMA da figura
    (metade de cima nos chibis, terço de cima nos desenhos) vira H2; H1 em roupa, cabelo e armadura grandes (sombra clara de branco ou metal) fica como está"""
    H1 = L['H1']; H2 = L['H2']
    H, W = len(rows), len(rows[0])
    fig = [y for y in range(H) if any(c != '.' for c in rows[y])]
    top, bot = fig[0], fig[-1]; fh = bot - top + 1
    chibiish = any(k in name.lower() for k in ('chibi', 'folha', 'trio', 'círculo'))
    lim = top + (0.50 if chibiish else 0.32) * fh
    m = np.array([[c == H1 for c in r] for r in rows], np.uint8)
    n_, lab_, st_, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    g = [list(r) for r in rows]; k = 0
    lim_force = H1_FORCE.get(name)
    for i in range(1, n_):
        ys, xs = np.nonzero(lab_ == i)
        if lim_force is not None and ys.min() <= lim_force:
            for y, x in zip(ys, xs):
                if y <= lim_force: g[y][x] = H2; k += 1
            continue
        if len(ys) > 6 or ys.min() > lim: continue
        dark = any(0 <= v < H and 0 <= u < W and rows[v][u] not in ('.', H1) and LAB[rows[v][u]][0] < 45 for y, x in zip(ys, xs) for v in (y - 1, y, y + 1) for u in (x - 1, x, x + 1))
        if dark:
            for y, x in zip(ys, xs): g[y][x] = H2; k += 1
    if k: print(f'    H1 -> H2 (branco de olho, dente ou máscara): {k} contas')
    return [''.join(r) for r in g]


def h1_face(name, rows):
    """regra do dono: NUNCA a conta transparente (H1) no branco do olho nem em rosto branco. Dentro do rosto (a casca da pele, medida na arte) toda H1 vira o branco H2.
    Fora do rosto a H1 fica: em roupa, cabelo e metal branco ela é a sombra clara (378 moldes do catálogo a usam assim)."""
    if not os.path.exists(geom_path(name)): return rows
    try:
        import r31_eyes as EY
        G = load_geom(name); ctx = EY.Ctx(rows, G, P, L, LAB)
        if not ctx.ok: return rows
        f = ctx.face()
        if f is None: return rows
        face_px, hull_px, box = f
        H1 = L['H1']; H2 = L['H2']; n = 0
        g = [list(r) for r in rows]
        fy0, fy1, fx0, fx1 = box; fh = fy1 - fy0
        band0, band1 = fy0 + 0.30 * fh, fy0 + 0.80 * fh          # faixa dos olhos no rosto
        def dark_near(y, x):
            for v in (y - 1, y, y + 1):
                for u in (x - 1, x, x + 1):
                    if (v, u) != (y, x) and 0 <= v < ctx.H and 0 <= u < ctx.W and rows[v][u] != '.' and LAB[rows[v][u]][0] < 45: return True
            return False
        for y in range(ctx.H):
            for x in range(ctx.W):
                if g[y][x] != H1: continue
                px_, py_ = int(ctx.pxx(x + 0.5)), int(ctx.pyy(y + 0.5))
                in_hull = 0 <= py_ < ctx.h and 0 <= px_ < ctx.w and hull_px[py_, px_]
                eye_white = band0 <= y <= band1 and fx0 - 2 <= x <= fx1 + 2 and dark_near(y, x)          # branco do olho: H1 ao lado de uma conta escura (pálpebra, pupila) na faixa dos olhos
                if in_hull or eye_white: g[y][x] = H2; n += 1
        if n: print(f'    H1 -> H2 no rosto: {n} contas')
        return [''.join(r) for r in g]
    except Exception as e:
        print('    h1_face falhou:', repr(e)); return rows


def post31(name, rows):
    rows = eyes31(name, rows)
    z = POST31.get(name)
    rows = P.paint_mouth(rows, z, verbose=True) if z else rows
    return h1_small(name, h1_face(name, rows))


def touch_raw():
    """aplica o POST31 e o TOUCH31 por cima do data/final33_raw_120.json (sem reconverter) e regrava o final33_120.json com os nomes únicos"""
    raw = os.path.join(HERE, 'data', ('r31v2_raw' if V2 else 'final33_raw') + sfx() + '.json')
    data = json.load(open(raw, encoding='utf-8'))
    n = 0
    grp = {c[0]: c[4] for c in CFG}
    for x in data:
        if grp.get(x[0]) in ('graf', 'foto'): continue          # cópia fiel de gráfico: nada é retocado
        print('-', x[0]); new = P.touch6(x[0], post31(x[0], x[2]))
        if new != x[2]: x[2] = new; n += 1
    json.dump(data, open(raw, 'w', encoding='utf-8'), ensure_ascii=False)
    if V2: print(n, 'moldes retocados; gravado', raw); return
    pth = os.path.join(HERE, 'data', 'final33' + sfx() + '.json')
    json.dump(uniq(data), open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print(n, 'moldes retocados; gravado', pth, len(data), 'moldes')


if V2:          # os retoques e zonas da 1ª versão estão nas coordenadas da grade antiga: refeitos em R31V2_* depois de olhar
    import r31v2_defs as V2D
    POST31.clear(); POST31.update(V2D.POST); TOUCH31.clear(); TOUCH31.update(V2D.TOUCH)
    EYES31 = {k: v for k, v in EYES31.items() if v == 'auto'}; EYES31.update(V2D.EYES)
    for _k in [k for k in EYES31 if k in V2D.NOEYES]: del EYES31[_k]
    H1_FORCE.clear(); H1_FORCE.update(V2D.H1_FORCE)


def run(args, grupo):
    one = []; sheet = []
    P.TOUCH6 = TOUCH31; P.SKIN6 = SKIN31
    for n, g, idx, fn, grp in CFG:
        if grupo and grp != grupo: continue
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = False
            P.CUR[0] = n
            print('-', n)
            r = P.touch6(n, fn())
            if grp not in ('graf', 'foto'): r = post31(n, r)          # gráfico / pixel art / foto de peça = cópia fiel: nada de olho, boca nem H1 por cima
            one.append((n, g, r))
            src = R.source_img(idx, getattr(fn, 'box', None))
            if getattr(fn, 'rot', 0): src = src.rotate(-90 * fn.rot, expand=True)
            sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', src, r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    return one, sheet


if __name__ == '__main__':
    argv = sys.argv[1:]
    for opt in ('--H', '--grupo', '--tag'):
        if opt in argv: k = argv.index(opt); globals()['_' + opt[2:]] = argv[k + 1]; del argv[k:k + 2]
    args = [a for a in argv if not a.startswith('--')]
    grupo = globals().get('_grupo')
    if '--touch' in sys.argv:
        P.TOUCH6 = TOUCH31; touch_raw(); sys.exit(0)
    one, sheet = run(args, grupo)
    print(len(one), 'moldes de 1 placa')
    tag = globals().get('_tag') or ((grupo or 'all') + ('_f' if args else ''))
    HH = int(globals().get('_H') or 300)
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r31_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r31_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and ('--merge' in sys.argv or (not args and not grupo)):
        raw = os.path.join(HERE, 'data', ('r31v2_raw' if V2 else 'final33_raw') + sfx() + '.json')          # nomes do CFG (para --merge)
        old_ = json.load(open(raw, encoding='utf-8')) if os.path.exists(raw) and (args or grupo) else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        order = {n: i for i, (n, *_r) in enumerate(CFG)}
        old_ = [x for x in old_ if x[0] in order]
        old_.sort(key=lambda x: order.get(x[0], 10 ** 6))
        json.dump(old_, open(raw, 'w', encoding='utf-8'), ensure_ascii=False)
        if not V2:
            pth = os.path.join(HERE, 'data', 'final33' + sfx() + '.json')
            json.dump(uniq(old_), open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravado', raw if V2 else pth, len(old_), 'moldes')
    print('ok')
