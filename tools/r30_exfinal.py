"""Remessa 30 (153 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r30_exfinal.py [filtro...] [--grupo ill|cdz|folha] [--merge] [--H 520] [--tag nome]
   -> data/final32_120.json (tudo em 1 placa). Reaproveita a remessa 29 (r29_exfinal.py: convert6 com contorno preto primeiro, sem boca, retoques de olhos) e troca a lista de arquivos.
Classes (CLAUDE.md §4.1 e §4.8): todas são ILUSTRAÇÕES (chibis, adesivos, cartões) = adaptação em 1 placa pelo illus6.convert6 (padrão do dono desde 2026-11-04:
"bordas pretas nos moldes, ajuda a delimitar"), olhos discretos e sem boca desenhada.
Folhas com vários personagens: 5 (Dan Da Dan, 5), 37 (4 Pokémon iniciais), 60 (2 chibis), 101 (Eyeshield 21, 9), 112 (Seras e Alucard), 132 (9 Eeveelutions),
133 (9 adesivos de Eeveelutions), 142 (5 chibis deitados), 148 (Eyeshield 21, 8). 122 (Rukawa e Sakuragi) e 130 (Killua e Gon) ficam inteiras (as figuras se tocam).
Repetidas por MD5 (entram, pedido do dono): 27 e 34 (remessa 16), 32 (remessa 18), 79 (remessa 15); a 30 é cópia byte a byte da 29 da mesma remessa e fica de fora.
Fundos: branco = padrão (thr 240); cor lisa = bg='flat'; cartões, adesivos com borda colorida e fundos estampados = outline_mask (o fundo é o que fica fora do contorno escuro);
cena / interface de jogo = grabCut (grab())."""
import os, sys, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r29_exfinal as P
from r29_exfinal import r5, R, L, LAB, OUT, F, fin, lg, np, cv2, Image, tplfile, sfx
F[:] = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa 30', '*.*')))          # F é a mesma lista de r6.FILES e R.F
P.SKIN6 = {}          # sementes de pele por nome (convert6); as da remessa 29 não valem aqui
P.TOUCH6 = {}         # retoques à mão por nome (preenchidos depois de olhar as folhas: TOUCH30)
CDZ = 'Cavaleiros do Zodíaco'
CH6 = dict(P.CH)
OM = P.outline_mask
SKIN30 = {}           # nome -> dict(face_seeds=[(l, c)], face_box=(l0, l1, c0, c1), ...) (pele da cor da armadura etc.)
MOUTH30 = {}          # nome -> zona de boca (l0, l1, c0, c1) no molde final do convert6, ou None = não mexe


def inpaint30(idx, boxes):
    """texto por cima do desenho: repinta pela vizinhança (cv2.inpaint) numa cópia temporária; boxes = retângulos ou função(imagem) -> máscara; devolve o caminho (prefixo _r30_)"""
    tmp = os.path.join(OUT, f'_r30_{idx}.png')
    if not os.path.exists(tmp) or os.path.getmtime(tmp) < os.path.getmtime(__file__):
        im = np.array(Image.open(F[idx]).convert('RGB'))
        if callable(boxes): m = boxes(im).astype(np.uint8) * 255
        else:
            m = np.zeros(im.shape[:2], np.uint8)
            for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = 255
        Image.fromarray(cv2.inpaint(im, m, 5, cv2.INPAINT_TELEA)).save(tmp)
    return tmp


def yellow_bg(ref=(232, 186, 48), tol=72, line=9):
    """fundo de UMA cor com riscos finos claros por cima (Walter: amarelo com linhas brancas em espiral): fundo = a cor; o que sobra é aberto (some o risco fino) e fica só a maior peça"""
    def f(rgb):
        m = np.linalg.norm(rgb.astype(np.float32) - np.array(ref, np.float32), axis=2) < tol
        fig = cv2.morphologyEx((~m).astype(np.uint8), cv2.MORPH_OPEN, np.ones((line, line), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(fig, 8)
        if n > 1: fig = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
        return fig == 0
    return f


def floor_shadow(frac=0.22, thr=240):
    """sombra no chão (cinza-claro, pouco colorida) na parte de baixo da imagem também vira fundo, além do branco ligado à borda"""
    import illus
    def f(rgb):
        m = illus.sticker_bg(rgb, thr, None)
        a = rgb.astype(np.int32); mx = a.max(axis=2); mn = a.min(axis=2)
        sh = ((mx - mn) < 28) & (mx > 120) & (mx < 246)
        sh[:int(rgb.shape[0] * (1 - frac))] = False
        return m | sh
    return f


def mouth30(rows):
    """sem boca (§4.8), com os olhos achados pelo _face_eyes: abaixo deles, dentro da casca do rosto, tudo que não é pele e está cercado de pele vira pele
    (mais amplo que o no_mouth da remessa 29, que só pegava cor de boca)"""
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


def no_mouth30(rows):
    r, n = mouth30(rows)
    how = 'abaixo dos olhos'
    if not n:
        r, n = mouth_hole(rows); how = 'buraco na pele'
    if n: print(f'    boca tirada: {n} contas ({how})')
    return r


def grab(rect=None, iters=6):
    """fundo de CENA (sala, interface de jogo): cv2.grabCut a partir de um retângulo em volta da figura (em pixels da imagem já recortada pela caixa)"""
    def f(rgb):
        h, w = rgb.shape[:2]
        r = rect or (int(w * 0.03), int(h * 0.02), int(w * 0.94), int(h * 0.96))
        mask = np.zeros((h, w), np.uint8); bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(np.ascontiguousarray(rgb[..., ::-1]), mask, tuple(int(v) for v in r), bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)
        return ~((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD))
    return f


def I(idx, box=None, skin=True, post=None, clear=(), paint=None, mouth=False, base=None, **kw):
    """ilustração: illus6.convert6 pelo ill6 da remessa 29 (CH6 + kw), depois sem boca (zona MOUTH30[nome] ou a busca automática pelos olhos, §4.8)"""
    def f():
        a = dict(base or CH6); a.update(kw)
        old = F[idx]
        if paint: F[idx] = inpaint30(idx, paint)
        try: r = P.ill6(idx, a, box=box, clear=clear, skin=skin)
        finally: F[idx] = old
        if post: r = post(r)
        nm = P.CUR[0]
        if skin and not mouth and not (nm in MOUTH30 and MOUTH30[nm] is None):
            r = P.paint_mouth6(r, MOUTH30[nm], verbose=True) if MOUTH30.get(nm) else no_mouth30(r)
        return fin(lg(r))
    f.box = box
    return f


def C(idx, post=None, **kw):
    """Cavaleiro: base CHG da remessa 29 (rampa do dourado) + gravação marrom no ouro + maioria nos dourados"""
    def p(rows):
        rows = P.mode_family(P.gold_lines(rows))
        return post(rows) if post else rows
    return I(idx, base=P.CHG, post=p, **kw)


KBSZ = {39: (800, 1250), 99: (800, 1250), 104: (384, 600), 115: (800, 1250), 118: (736, 1150), 136: (800, 1250)}


def KBC(idx):
    """cartões de Kuroko no Basket (nome em cima, fundo de bolas de basquete claras): corta o nome e separa a figura por grabCut"""
    w, h = KBSZ[idx]
    return dict(box=(0, int(h * 0.17), w, h), mask=grab())


H = 'Hellsing'; KB = 'Kuroko no Basket'; SD = 'Slam Dunk'; CG = 'Code Geass'; E21 = 'Eyeshield 21'; BZ = 'Beelzebub'; TS = 'Tensura (Slime)'; WI = 'Wistoria'
GEN = 'Genéricos'; SE = 'Soul Eater'; HX = 'Hunter x Hunter'; KHR = 'Katekyo Hitman Reborn'; OV = 'Overlord'; TR = 'Trigun'; SAO = 'Sword Art Online'
CFG = [
 ('Alluka Zoldyck (Hunter x Hunter, chibi)', HX, 0, I(0, bg='flat', tol=40, peel=1.0), 'ill'),
 ('Sion Glenn (Wistoria, chibi)', WI, 1, I(1, mask=OM()), 'ill'),
 ('Seras Victoria (Hellsing, chibi, braço de sombra)', H, 2, I(2, bg='flat', tol=50), 'ill'),
 ('Kallen Kozuki (Code Geass, chibi, traje de piloto)', CG, 3, I(3), 'ill'),
 ('Jeremiah Gottwald (Code Geass, chibi)', CG, 4, I(4), 'ill'),
 ('Soma Yukihira (Shokugeki no Soma, chibi, adesivo)', 'Shokugeki no Soma', 6, I(6, thr=205, peel=1.0), 'ill'),
 ('Sunraku (Shangri-La Frontier, chibi)', 'Shangri-La Frontier', 7, I(7), 'ill'),
 ('Ram (Re:Zero, chibi, capuz de gato)', 'Re:Zero', 8, I(8, mask=OM()), 'ill'),
 ('Hanamichi Sakuragi (Slam Dunk, chibi, bola de basquete)', SD, 9, I(9), 'ill'),
 ('Colette Loire (Wistoria, chibi)', WI, 10, I(10, mask=OM()), 'ill'),
 ('Shalltear Bloodfallen (Overlord, chibi)', OV, 11, I(11), 'ill'),
 ('Izaya Orihara (Durarara, chibi)', 'Durarara', 12, I(12, mask=OM()), 'ill'),
 ('Cavaleiro de elmo branco e chifre de carneiro (chibi)', CDZ, 13, C(13), 'cdz'),
 ('Hiruma Yoichi (Eyeshield 21, chibi, de diabo)', E21, 14, I(14), 'ill'),
 ('Suzaku Kururugi (Code Geass, chibi)', CG, 15, I(15), 'ill'),
 ('Criatura de cristal azul com tridente (chibi)', GEN, 16, I(16, skin=False), 'ill'),
 ('Oga, Hilda e Baby Beel (Beelzebub, chibi)', BZ, 17, I(17, mask=OM()), 'ill'),
 ('Garota de cabelo rosa e laço branco (chibi, vitrine)', GEN, 18, I(18, box=(180, 50, 600, 790), mask=grab()), 'ill'),
 ('Baby Beel (Beelzebub, chibi, chiclete)', BZ, 19, I(19), 'ill'),
 ('Leorio Paradinight (Hunter x Hunter, chibi)', HX, 20, I(20), 'ill'),
 ('Seijuro Akashi (Kuroko no Basket, chibi, bola)', KB, 21, I(21), 'ill'),
 ('Rin Okumura (Ao no Exorcist, chibi)', 'Ao no Exorcist', 22, I(22), 'ill'),
 ('Hanamichi Sakuragi (Slam Dunk, chibi, Shohoku 10)', SD, 23, I(23, bg='flat', tol=30), 'ill'),
 ('Zero (Code Geass, chibi, capa aberta)', CG, 24, I(24), 'ill'),
 ('Figura encapuzada azul de chifres (chibi)', GEN, 25, I(25), 'ill'),
 ('Mascote do Deimon Devil Bats (Eyeshield 21)', E21, 26, I(26, skin=False), 'ill'),
 ('Lancelot (Code Geass, chibi, mecha)', CG, 27, I(27, skin=False), 'ill'),
 ('Garoto de cabelo vermelho e blazer azul (chibi)', GEN, 28, I(28, mask=OM()), 'ill'),
 ('Bichinho branco de asas de morcego (chibi)', GEN, 29, I(29, skin=False), 'ill'),
 ('Ranga (Tensura, chibi)', TS, 31, I(31, skin=False), 'ill'),
 ('Jaden Yuki (chibi, com Winged Kuriboh)', 'Yu-Gi-Oh', 32, I(32), 'ill'),
 ('Adão (Record of Ragnarok, chibi)', 'Record of Ragnarok', 33, I(33, bg='flat', tol=50, peel=1.0), 'ill'),
 ('Guren (Code Geass, mecha de asas rosas)', CG, 34, I(34, skin=False), 'ill'),
 ('Kumara (Tensura, chibi)', TS, 35, I(35, mask=OM()), 'ill'),
 ('Elfaria (Wistoria, chibi)', WI, 36, I(36, mask=OM()), 'ill'),
 ('Issei Hyoudou (High School DxD, chibi)', 'High School DxD', 38, I(38, thr=190), 'ill'),
 ('Ryota Kise (Kuroko no Basket, chibi, cartão)', KB, 39, I(39, **KBC(39)), 'ill'),
 ('Soei (Tensura, chibi)', TS, 40, I(40, mask=OM()), 'ill'),
 ('Hiruma Yoichi (Eyeshield 21, chibi, bazuca)', E21, 41, I(41, mask=OM()), 'ill'),
 ('Elfo de cabelo verde (Wistoria, chibi)', WI, 42, I(42, mask=OM()), 'ill'),
 ('Pokkle (Hunter x Hunter, chibi)', HX, 43, I(43), 'ill'),
 ('Taiga Kagami (Kuroko no Basket, chibi, bola)', KB, 44, I(44), 'ill'),
 ('Cavaleiro de armadura negra e penas de pavão (chibi)', CDZ, 45, C(45), 'cdz'),
 ('Choso (Jujutsu Kaisen, chibi, adesivo)', 'Jujutsu Kaisen', 46, I(46, mask=OM()), 'ill'),
 ('Velho de cabelo grisalho e foices (chibi)', GEN, 47, I(47), 'ill'),
 ('Mascote do Deimon Devil Bats (Eyeshield 21, voando)', E21, 48, I(48, skin=False), 'ill'),
 ('Aloy montada num Strider (Horizon, chibi)', 'Horizon', 49, I(49, thr=190), 'ill'),
 ('Hanamichi Sakuragi (Slam Dunk, chibi, pensativo)', SD, 50, I(50, thr=228), 'ill'),
 ('Louise (Zero no Tsukaima, chibi)', 'Zero no Tsukaima', 51, I(51), 'ill'),
 ('Garoto loiro de bandana 01 (chibi)', GEN, 52, I(52, mask=grab()), 'ill'),
 ('Koro-sensei (Assassination Classroom, chibi, debochando)', 'Assassination Classroom', 53, I(53, skin=False), 'ill'),
 ('Criatura de capa dos Touros Negros (Black Clover, chibi)', 'Black Clover', 54, I(54, skin=False), 'ill'),
 ('Armadura de Andrômeda (forma de totem, chibi)', CDZ, 55, C(55, skin=False), 'cdz'),
 ("Kanna Kamui (Miss Kobayashi's Dragon Maid, chibi)", "Miss Kobayashi's Dragon Maid", 56, I(56), 'ill'),
 ('Yusuke Urameshi (Yu Yu Hakusho, chibi, cartão)', 'Yu Yu Hakusho', 57, I(57, mask=OM()), 'ill'),
 ('Velho de tapa-olho e barba grisalha (chibi)', GEN, 58, I(58, mask=OM()), 'ill'),
 ('Crona (Soul Eater, chibi, com Ragnarok)', SE, 59, I(59), 'ill'),
 ('Velho de bigode branco e toga (chibi)', GEN, 61, I(61, mask=OM()), 'ill'),
 ('Alexander Anderson (Hellsing, chibi)', H, 62, I(62, bg='flat', tol=50), 'ill'),
 ('Katsuki Bakugo de oni (My Hero Academia, chibi)', 'My Hero Academia', 63, I(63, mask=OM()), 'ill'),
 ('Ryota Kise (Kuroko no Basket, chibi, piscando)', KB, 64, I(64), 'ill'),
 ('Senhor de óculos e avental laranja (chibi)', GEN, 65, I(65, mask=OM()), 'ill'),
 ('Figura de cabelo branco, boné azul e foice (chibi)', GEN, 66, I(66), 'ill'),
 ('Tengu de cabelo branco (chibi)', GEN, 67, I(67, thr=228), 'ill'),
 ('Senhora de óculos rosa e quimono (chibi)', GEN, 68, I(68, bg='flat', tol=30), 'ill'),
 ('Kirito (Sword Art Online, chibi)', SAO, 69, I(69), 'ill'),
 ('Garoto de moicano rosa e uniforme branco (chibi)', GEN, 70, I(70), 'ill'),
 ('Shuna (Tensura, chibi)', TS, 71, I(71, mask=OM()), 'ill'),
 ('Toge Inumaki (Jujutsu Kaisen, chibi)', 'Jujutsu Kaisen', 72, I(72), 'ill'),
 ('Momo Ayase (Dan Da Dan, chibi)', 'Dan Da Dan', 73, I(73, mask=OM(), clear=[(0, 690, 298, 1200), (298, 935, 352, 1058), (298, 1145, 420, 1200)]), 'ill'),
 ('Shizuo Heiwajima (Durarara, chibi)', 'Durarara', 74, I(74), 'ill'),
 ('Demiurge (Overlord, chibi)', OV, 75, I(75, mask=OM()), 'ill'),
 ('Blair (Soul Eater, gata)', SE, 76, I(76, skin=False), 'ill'),
 ('Alucard (Hellsing, chibi, pistolas e capa)', H, 77, I(77, bg='flat', tol=50), 'ill'),
 ('Shion (Tensura, chibi)', TS, 78, I(78, mask=OM()), 'ill'),
 ('Liebe (Black Clover, demônio de Asta, chibi)', 'Black Clover', 79, I(79, skin=False), 'ill'),
 ('Gato preto de joia roxa (Wistoria)', WI, 80, I(80, mask=OM(), skin=False), 'ill'),
 ('Shuten-dōji (Fate/Grand Order, chibi)', 'Fate/Grand Order', 81, I(81, mask=OM()), 'ill'),
 ('Momon (Overlord, chibi)', OV, 82, I(82, mask=OM(), skin=False), 'ill'),
 ('Jogador nº 99 (Eyeshield 21, chibi)', E21, 83, I(83), 'ill'),
 ('Oga carregando Baby Beel e Hilda (Beelzebub, chibi)', BZ, 84, I(84, mask=grab()), 'ill'),
 ('Louise (Zero no Tsukaima, chibi, capa)', 'Zero no Tsukaima', 85, I(85), 'ill'),
 ('Seiko Ayase (Dan Da Dan, chibi, com taco)', 'Dan Da Dan', 86, I(86, mask=OM()), 'ill'),
 ('Eva-01 (Evangelion, chibi, lança)', 'Evangelion', 87, I(87, skin=False), 'ill'),
 ('Hanamichi Sakuragi (Slam Dunk, chibi, mãos nos bolsos)', SD, 88, I(88, thr=228), 'ill'),
 ('Walter C. Dornez (Hellsing, chibi)', H, 89, I(89, mask=yellow_bg()), 'ill'),
 ('Garoto de cabelo verde-água (Wistoria, chibi)', WI, 90, I(90, mask=OM()), 'ill'),
 ('Guerreiro de dentes de tubarão e lança (chibi)', GEN, 91, I(91, mask=grab()), 'ill'),
 ('Maka Albarn (Soul Eater, chibi, livro)', SE, 92, I(92), 'ill'),
 ('Verde (Katekyo Hitman Reborn, chibi)', KHR, 93, I(93), 'ill'),
 ('Tetsuya Kuroko (Kuroko no Basket, chibi, bola)', KB, 94, I(94), 'ill'),
 ('Máquina Vigia (Horizon)', 'Horizon', 95, I(95, thr=220, skin=False), 'ill'),
 ('Garoto com o slime Rimuru (Tensura, chibi)', TS, 96, I(96, mask=OM()), 'ill'),
 ('Soma Yukihira (Shokugeki no Soma, chibi, toalha)', 'Shokugeki no Soma', 97, I(97), 'ill'),
 ('Hisoka (Hunter x Hunter, chibi, cartão)', HX, 98, I(98, mask=OM()), 'ill'),
 ('Tetsuya Kuroko (Kuroko no Basket, chibi, cartão)', KB, 99, I(99, **KBC(99)), 'ill'),
 ('Takumi Aldini (Shokugeki no Soma, chibi)', 'Shokugeki no Soma', 100, I(100, box=(8, 8, 245, 292), bg='flat', tol=40), 'ill'),
 ('Vash, o Estouro (Trigun, chibi, fundo laranja)', TR, 102, I(102, bg='flat', tol=40), 'ill'),
 ('Mephisto Pheles (Ao no Exorcist, chibi)', 'Ao no Exorcist', 103, I(103), 'ill'),
 ('Shintaro Midorima (Kuroko no Basket, chibi, cartão)', KB, 104, I(104, **KBC(104)), 'ill'),
 ('Nicholas D. Wolfwood (Trigun, chibi, pulando)', TR, 105, I(105, thr=220), 'ill'),
 ('Lancelot Albion (Code Geass, mecha)', CG, 106, I(106, skin=False), 'ill'),
 ('Senhor de monóculo e chapéu de pena (chibi)', GEN, 107, I(107, bg='flat', tol=30), 'ill'),
 ('Benimaru (Tensura, chibi)', TS, 108, I(108, thr=235, peel=1.0), 'ill'),
 ('Hans Günsche (Hellsing, chibi)', H, 109, I(109), 'ill'),
 ('Oga, Hilda e Baby Beel de pijama de diabo (Beelzebub)', BZ, 110, I(110), 'ill'),
 ('Villetta Nu (Code Geass, chibi)', CG, 111, I(111), 'ill'),
 ('Oni azul de três olhos com taça de saquê (chibi)', GEN, 113, I(113, mask=grab()), 'ill'),
 ('Lavi (D.Gray-man, chibi)', 'D.Gray-man', 114, I(114), 'ill'),
 ('Taiga Kagami (Kuroko no Basket, chibi, cartão)', KB, 115, I(115, **KBC(115)), 'ill'),
 ('Hilda e Oga abraçados (Beelzebub, chibi)', BZ, 116, I(116, mask=OM()), 'ill'),
 ('Fran (Katekyo Hitman Reborn, chibi, chapéu de sapo)', KHR, 117, I(117, bg='flat', tol=30), 'ill'),
 ('Daiki Aomine (Kuroko no Basket, chibi, cartão)', KB, 118, I(118, **KBC(118)), 'ill'),
 ('Rakshata Chawla (Code Geass, chibi)', CG, 119, I(119), 'ill'),
 ('Asuna (Sword Art Online, chibi)', SAO, 120, I(120), 'ill'),
 ('Hilda (Beelzebub, chibi, sombrinha)', BZ, 121, I(121, mask=floor_shadow()), 'ill'),
 ('Rukawa e Sakuragi (Slam Dunk, chibi, toque de mãos)', SD, 122, I(122), 'ill'),
 ('Lelouch Lamperouge (Code Geass, chibi, uniforme)', CG, 123, I(123), 'ill'),
 ('Tsuna (Katekyo Hitman Reborn, chibi, Hyper)', KHR, 124, I(124), 'ill'),
 ('Maka Albarn (Soul Eater, chibi)', SE, 125, I(125), 'ill'),
 ('Tyki Mikk (D.Gray-man, chibi)', 'D.Gray-man', 126, I(126), 'ill'),
 ('Chibi de faixa nos olhos rindo (adesivo)', GEN, 127, I(127, thr=205, peel=1.0), 'ill'),
 ('Integra Hellsing (Hellsing, chibi)', H, 128, I(128, bg='flat', tol=50), 'ill'),
 ('Kyoya Hibari (Katekyo Hitman Reborn, chibi)', KHR, 129, I(129, box=(130, 50, 470, 590), mask=grab()), 'ill'),
 ('Killua e Gon (Hunter x Hunter, chibi)', HX, 130, I(130), 'ill'),
 ('Hanamichi Sakuragi (Slam Dunk, chibi, fantasia de macaco)', SD, 131, I(131), 'ill'),
 ('Coelho branco de cartola (chibi)', GEN, 134, I(134, skin=False), 'ill'),
 ('Kaiju nº 8 (chibi, punho erguido)', 'Kaiju nº 8', 135, I(135, skin=False), 'ill'),
 ('Atsushi Murasakibara (Kuroko no Basket, chibi, cartão)', KB, 136, I(136, **KBC(136)), 'ill'),
 ('Mecha vermelho de asas verdes e lança (Code Geass)', CG, 137, I(137, skin=False), 'ill'),
 ('Soul Eater Evans (Soul Eater, chibi)', SE, 138, I(138), 'ill'),
 ('Garoto de óculos e cabelo azul-escuro (Wistoria, chibi)', WI, 139, I(139, mask=OM()), 'ill'),
 ('Ryota Miyagi (Slam Dunk, chibi)', SD, 140, I(140), 'ill'),
 ('Death the Kid (Soul Eater, chibi)', SE, 141, I(141), 'ill'),
 ('Shintaro Midorima (Kuroko no Basket, chibi, bola)', KB, 143, I(143), 'ill'),
 ('Sinon (Sword Art Online, chibi)', SAO, 144, I(144), 'ill'),
 ('Garota de rosas azuis e vestido de babados (chibi)', GEN, 145, I(145, mask=grab()), 'ill'),
 ('Vash, o Estouro (Trigun Stampede, chibi)', TR, 146, I(146, mask=grab()), 'ill'),
 ('Nicholas D. Wolfwood (Trigun, chibi, cruz)', TR, 147, I(147), 'ill'),
 ('Asia Argento (High School DxD, chibi)', 'High School DxD', 149, I(149), 'ill'),
 ('Aloy (Horizon, chibi)', 'Horizon', 150, I(150), 'ill'),
 ('Garoto de cabelo vermelho com guitarra (chibi)', GEN, 151, I(151), 'ill'),
 ('Seijuro Akashi (Kuroko no Basket, chibi, jaqueta)', KB, 152, I(152), 'ill'),
]

# ---- folhas com vários personagens (grupo 'folha'): caixas em pixels (peças ligadas do que não é fundo, conferidas olhando: tools/out/abox30_N.png)
BOX132 = [(25, 5, 240, 252), (240, 2, 458, 264), (466, 3, 680, 249), (25, 248, 240, 487), (257, 259, 451, 487), (496, 239, 702, 489), (64, 478, 264, 710), (270, 475, 458, 710), (480, 482, 679, 710)]


def wm132(im):
    """marca d'água "@SeviYummy" (cinza) embaixo à direita de cada figura da folha das evoluções: repintada antes de converter"""
    a = im.astype(np.int32); mx = a.max(axis=2); mn = a.min(axis=2)
    grey = ((mx - mn) < 40) & (mx > 110) & (mx < 215)
    m = np.zeros(im.shape[:2], bool)
    for x0, y0, x1, y1 in BOX132:
        w, h = x1 - x0, y1 - y0
        rx0, ry0 = x0 + int(0.35 * w), y1 - int(0.17 * h)
        m[ry0:y1, rx0:x1] |= grey[ry0:y1, rx0:x1]
    return cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0


FOLHAS = [
 (5, 'Dan Da Dan', {}, [('Turbo Granny (Dan Da Dan, gata maneki-neko, folha)', (95, 40, 305, 228), False),
                                     ('Chibi loiro de máscara e casaco amarelo (Dan Da Dan, folha)', (362, 75, 698, 450), True),
                                     ('Garota de cabelo rosa e caveira (Dan Da Dan, folha)', (20, 233, 405, 575), True),
                                     ('Okarun transformado (Dan Da Dan, chibi, folha)', (50, 560, 400, 912), True),
                                     ('Momo Ayase (Dan Da Dan, chibi, folha)', (345, 445, 698, 848), True)]),
 (37, 'Pokémon', dict(skin=False), [('Pikachu (Pokémon, folha dos iniciais)', (526, 86, 1059, 600), False), ('Squirtle (Pokémon, folha dos iniciais)', (550, 703, 1050, 1174), False),
                                    ('Bulbasaur (Pokémon, folha dos iniciais)', (512, 1276, 1044, 1738), False), ('Charmander (Pokémon, folha dos iniciais)', (600, 1818, 1134, 2320), False)]),
 (60, GEN, {}, [('Chibi de cabelo vermelho com bola de futebol', (96, 47, 563, 625), True), ('Chibi de cabelo branco e máscara de olho roxo', (603, 14, 1102, 637), True)]),
 (101, E21, dict(thr=222), [('Suzuna Taki (Eyeshield 21, chibi, folha)', (4, 5, 362, 346), True), ('Mamori Anezaki (Eyeshield 21, chibi, folha)', (556, 14, 716, 276), True),
                              ('Ryokan Kurita (Eyeshield 21, chibi, folha)', (323, 148, 581, 363), True), ('Hiruma Yoichi (Eyeshield 21, chibi, folha)', (751, 111, 956, 346), True),
                              ('Koji Kuroki (Eyeshield 21, chibi, folha)', (120, 338, 309, 578), True), ('Daikichi Komusubi (Eyeshield 21, chibi, folha)', (370, 411, 556, 589), True),
                              ('Mascote do Deimon Devil Bats (Eyeshield 21, folha)', (525, 278, 810, 502), False), ('Taro Raimon, o Monta (Eyeshield 21, chibi, folha)', (758, 407, 983, 586), True),
                              ('Shozo Togano (Eyeshield 21, chibi, folha)', (588, 514, 750, 722), True)]),
 (112, H, dict(bg='flat', tol=60), [('Seras Victoria (Hellsing, chibi, fundo vermelho)', (57, 31, 481, 711), True), ('Alucard (Hellsing, chibi, fundo vermelho)', (480, 9, 917, 723), True)]),
 (132, 'Pokémon', dict(skin=False, paint=wm132), [('Eevee (Pokémon, chibi, folha das evoluções)', (25, 5, 240, 252), False), ('Vaporeon (Pokémon, chibi, folha das evoluções)', (240, 2, 458, 264), False),
                                     ('Flareon (Pokémon, chibi, folha das evoluções)', (466, 3, 680, 249), False), ('Jolteon (Pokémon, chibi, folha das evoluções)', (25, 248, 240, 487), False),
                                     ('Espeon (Pokémon, chibi, folha das evoluções)', (257, 259, 451, 487), False), ('Umbreon (Pokémon, chibi, folha das evoluções)', (496, 239, 702, 489), False),
                                     ('Glaceon (Pokémon, chibi, folha das evoluções)', (64, 478, 264, 710), False), ('Leafeon (Pokémon, chibi, folha das evoluções)', (270, 475, 458, 710), False),
                                     ('Sylveon (Pokémon, chibi, folha das evoluções)', (480, 482, 679, 710), False)]),
 (133, 'Pokémon', dict(bg='flat', tol=40, peel=1.0, skin=False), [('Sylveon (Pokémon, adesivo)', (35, 30, 240, 261), False), ('Vaporeon (Pokémon, adesivo)', (262, 33, 458, 273), False),
                                     ('Flareon (Pokémon, adesivo)', (466, 35, 696, 264), False), ('Jolteon (Pokémon, adesivo)', (31, 271, 238, 509), False),
                                     ('Eevee (Pokémon, adesivo)', (244, 284, 458, 505), False), ('Glaceon (Pokémon, adesivo)', (473, 280, 703, 517), False),
                                     ('Umbreon (Pokémon, adesivo)', (54, 516, 227, 784), False), ('Leafeon (Pokémon, adesivo)', (273, 512, 449, 786), False),
                                     ('Espeon (Pokémon, adesivo)', (475, 528, 668, 772), False)]),
 (142, GEN, {}, [('Chibi loiro de óculos e jaleco (folha, deitado)', (344, 0, 722, 281), True), ('Chibi de cabelo branco e olhos vermelhos (folha, deitado)', (26, 215, 402, 437), True),
                              ('Chibi de cabelo vermelho e olhos verdes (folha, deitado)', (347, 284, 708, 592), True), ('Chibi de cabelo castanho e mechas laranja (folha, deitado)', (17, 464, 368, 757), True),
                              ('Chibi de cabelo cinza e roupa azul (folha, deitado)', (347, 588, 708, 933), True)]),
 (148, E21, dict(thr=195), [('Cerberus (Eyeshield 21, cachorro, folha 2)', (518, 67, 716, 283), False), ('Sena Kobayakawa (Eyeshield 21, chibi, folha 2)', (759, 9, 1071, 373), True),
                              ('Jogador do Deimon de braços abertos (Eyeshield 21, folha 2)', (219, 195, 508, 494), True), ('Mamori Anezaki (Eyeshield 21, chibi, vassoura, folha 2)', (374, 286, 874, 810), True),
                              ('Hiruma Yoichi (Eyeshield 21, chibi, folha 2)', (821, 336, 1177, 696), True), ('Suzuna Taki (Eyeshield 21, chibi, folha 2)', (22, 473, 395, 988), True),
                              ('Ryokan Kurita (Eyeshield 21, chibi, folha 2)', (368, 706, 676, 1036), True), ('Irmãos Ha-Ha (Eyeshield 21, chibi, folha 2)', (757, 718, 1193, 1005), True)]),
]
EXTRA30 = {          # ajustes por figura das folhas
    'Mamori Anezaki (Eyeshield 21, chibi, vassoura, folha 2)': dict(bg='flat', refs=[(255, 255, 255), (213, 224, 238), (232, 238, 236)], tol=26),          # o disco branco atrás dela (parte do fundo da página) ficava no molde: branco e azul-claro ligados à borda são fundo
}
for _idx, _ser, _kw, _items in FOLHAS:
    for _n, _b, _skin in _items:
        a = dict(_kw); a.setdefault('skin', _skin); a.update(EXTRA30.get(_n, {}))
        if _idx in (101, 148): a.update(pre_blur=1)
        CFG.append((_n, _ser, _idx, I(_idx, box=_b, **a), 'folha'))


# ---------------------------------------------------------------- nomes únicos contra o catálogo de ANTES da remessa (backups/pre-r30.js)
def uniq(items):
    base = os.path.join(HERE, 'backups', 'pre-r30.js')
    d = tplfile.parse(base if os.path.exists(base) else os.path.join(os.path.dirname(HERE), 'templates.js'))
    taken = {t['name'] for t in d['items']} | set(d.get('removed') or [])
    out = []; seen = set()
    for it in items:
        n = it[0]; k = 2
        while n in taken or n in seen: n = P._with_version(it[0], k); k += 1
        if n != it[0]: print(f'  nome ajustado: {it[0]} -> {n}')
        seen.add(n); out.append([n] + list(it[1:]))
    return out


TOUCH30 = {          # retoques à mão no molde final (olhos etc.), mesmo formato do TOUCH6 da remessa 29 (coordenadas do data/final32_raw_120.json)
    # Kurita: os olhos fechados da arte são arcos finos que a conversão perdeu; sem a boca aberta o rosto ficava vazio: dois arcos pretos (olho fechado sorrindo)
    'Ryokan Kurita (Eyeshield 21, chibi, folha)': dict(leg={'k': 'H7', 'e': 'E11'}, ops=[('block', 10, 14, [' kk ', 'keek']), ('block', 10, 24, [' kk ', 'k  k'])]),
    # Rakshata: a sombra do cabelo loiro-oliva caía no verde-oliva B11 (manchas verdes no cabelo): vira caramelo M9, que já é o tom de sombra do cabelo
    'Rakshata Chawla (Code Geass, chibi)': dict(leg={}, ops=[('map', 0, 60, 0, 60, {'B11': 'M9'})]),
}

# BOCA ABERTA que a busca automática não achou (olhos fechados em arco, olhos dentro do cabelo preto): zona (linha 0, linha 1, coluna 0, coluna 1) do molde FINAL em que
# tudo o que não é pele vira a pele do rosto (P.paint_mouth). Medidas sobre as linhas do data/final32_raw_120.json (a conversão não é reproduzível conta a conta):
# aplicadas POR CIMA dele com  python tools/r30_exfinal.py --touch  (e também no fim de cada conversão, por consistência)
POST30 = {
    'Ryokan Kurita (Eyeshield 21, chibi, folha)': (16, 25, 11, 27),
    'Ram (Re:Zero, chibi, capuz de gato)': (22, 26, 13, 21),
    'Taiga Kagami (Kuroko no Basket, chibi, cartão)': (27, 30, 14, 16),
    'Guerreiro de dentes de tubarão e lança (chibi)': (25, 26, 13, 19),
    'Taro Raimon, o Monta (Eyeshield 21, chibi, folha)': (27, 30, 22, 30),
    # achadas na folha de rostos (tools/out/faceqa30_*.png e fg30_*.png): boca aberta, dentes ou língua que sobraram
    'Kallen Kozuki (Code Geass, chibi, traje de piloto)': (23, 25, 18, 21),
    'Hanamichi Sakuragi (Slam Dunk, chibi, bola de basquete)': (18, 21, 10, 20),
    'Garoto de cabelo vermelho e blazer azul (chibi)': (21, 22, 13, 17),
    'Jaden Yuki (chibi, com Winged Kuriboh)': (22, 23, 21, 25),
    'Shuna (Tensura, chibi)': (21, 22, 10, 12),
    'Maka Albarn (Soul Eater, chibi, livro)': (19, 22, 10, 18),
    'Chibi de faixa nos olhos rindo (adesivo)': (20, 26, 8, 16),
    'Sinon (Sword Art Online, chibi)': (23, 23, 15, 17),
    'Chibi de cabelo vermelho com bola de futebol': (28, 31, 12, 17),
    'Hiruma Yoichi (Eyeshield 21, chibi, folha)': (30, 36, 14, 22),
    'Suzuna Taki (Eyeshield 21, chibi, folha 2)': (16, 19, 14, 17),
    'Taiga Kagami (Kuroko no Basket, chibi, bola)': (24, 26, 14, 17),
    'Soul Eater Evans (Soul Eater, chibi)': (22, 25, 12, 20),
    'Koji Kuroki (Eyeshield 21, chibi, folha)': (22, 25, 8, 13),
    'Seras Victoria (Hellsing, chibi, fundo vermelho)': (27, 27, 12, 15),
}


def post30(name, rows):
    z = POST30.get(name)
    return P.paint_mouth(rows, z, verbose=True) if z else rows


def touch_raw():
    """aplica o POST30 por cima do data/final32_raw_120.json (sem reconverter) e regrava o final32_120.json com os nomes únicos"""
    raw = os.path.join(HERE, 'data', 'final32_raw' + sfx() + '.json')
    data = json.load(open(raw, encoding='utf-8'))
    n = 0
    for x in data:
        if x[0] in POST30 or x[0] in TOUCH30:
            print('-', x[0]); new = P.touch6(x[0], post30(x[0], x[2]))
            if new != x[2]: x[2] = new; n += 1
    json.dump(data, open(raw, 'w', encoding='utf-8'), ensure_ascii=False)
    pth = os.path.join(HERE, 'data', 'final32' + sfx() + '.json')
    json.dump(uniq(data), open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print(n, 'moldes retocados; gravado', pth, len(data), 'moldes')


def run(args, grupo):
    one = []; sheet = []
    P.TOUCH6 = TOUCH30; P.SKIN6 = SKIN30
    for n, g, idx, fn, grp in CFG:
        if grupo and grp != grupo: continue
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = False
            P.CUR[0] = n
            print('-', n)
            r = post30(n, P.touch6(n, fn())); one.append((n, g, r))
            sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx, getattr(fn, 'box', None)), r))
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
        P.TOUCH6 = TOUCH30; touch_raw(); sys.exit(0)
    one, sheet = run(args, grupo)
    print(len(one), 'moldes de 1 placa')
    tag = globals().get('_tag') or ((grupo or 'all') + ('_f' if args else ''))
    HH = int(globals().get('_H') or 300)
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r30_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r30_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and ('--merge' in sys.argv or (not args and not grupo)):
        raw = os.path.join(HERE, 'data', 'final32_raw' + sfx() + '.json')          # nomes do CFG (para --merge)
        old_ = json.load(open(raw, encoding='utf-8')) if os.path.exists(raw) and (args or grupo) else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        order = {n: i for i, (n, *_r) in enumerate(CFG)}
        old_ = [x for x in old_ if x[0] in order]
        old_.sort(key=lambda x: order.get(x[0], 10 ** 6))
        json.dump(old_, open(raw, 'w', encoding='utf-8'), ensure_ascii=False)
        pth = os.path.join(HERE, 'data', 'final32' + sfx() + '.json')
        json.dump(uniq(old_), open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravado', pth, len(old_), 'moldes')
    print('ok')
