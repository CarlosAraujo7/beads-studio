"""Remessa 25 (68 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r25_exfinal.py [filtro...] [--grupo graf|folha] [--merge] [--H 520]
   -> data/final27_120.json (tudo em 1 placa, sem irmão grande: pedido do usuário na remessa 24).
Quase tudo é sprite/gráfico de pixel com grade: cópia exata; o que passa de 50 é reduzido (fit50 até 1,3x; acima, shrink 'bias').
Rostos em 1 placa (CLAUDE.md §4.8): olhos discretos e sem boca desenhada, salvo traço simples. Reaproveita os auxiliares do r22_exfinal.py."""
import os, sys, json
os.environ['REMNUM'] = '25'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np
import cv2
import r5, r6, outline as O, illus, shrink, loose
import r22_exfinal as R
import palette as P
from palette import sfx
from PIL import Image
E = r6.exact6
lg = R.lg
F = r6.FILES
L = {c['code']: c['letter'] for c in P.ALL}


def holes(rows, minsz=4, letter='w', keep=()):
    """esvazia os brancos FECHADOS (vãos de fundo entre braço e corpo) com >= minsz contas; keep = retângulos (r0, r1, c0, c1) onde o branco é do desenho"""
    H, W = len(rows), len(rows[0])
    m = np.array([[c == letter for c in r] for r in rows], np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
    g = [list(r) for r in rows]
    for i in range(1, n):
        if st[i][4] < minsz: continue
        cy, cx = st[i][1] + st[i][3] / 2.0, st[i][0] + st[i][2] / 2.0
        if any(a <= cy <= b and c <= cx <= d for a, b, c, d in keep): continue
        ys, xs = np.nonzero(lab == i)
        for y, x in zip(ys, xs): g[y][x] = '.'
    return [''.join(r) for r in g]


def pieces(minsz):
    """mantém as peças (8 vizinhos) com pelo menos minsz contas: figura em partes fica, marca d'água e assinatura saem"""
    def f(rows):
        m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        return O.trim([''.join(c if st[lab[y, x]][4] >= minsz else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)])
    return f


def _drop_lines(rows, k):
    """tira k COLUNAS: as que menos diferem da vizinha (nunca duas seguidas)"""
    W = len(rows[0]); cols = [''.join(r[x] for r in rows) for x in range(W)]
    cost = [(sum(a != b for a, b in zip(cols[x], cols[x + 1])), x) for x in range(W - 1)]
    out = set()
    for _, x in sorted(cost):
        if len(out) == k: break
        if x - 1 in out or x + 1 in out or x in out: continue
        out.add(x)
    return [''.join(c for x, c in enumerate(r) if x not in out) for r in rows]


def fit50(rows):
    h, w = len(rows), len(rows[0]); big = max(h, w)
    if big <= 50: return rows
    if big / 50.0 > 1.3: return shrink.shrink(rows, 50, 'plain', empty_at=0.6)      # maioria simples: o viés para preto do 'bias' apagava os rostos (testado: Kakashi, Cavaleiro, Cloud, Kaneki)
    nw, nh = shrink.target_size(w, h, 50)
    rows = _drop_lines(rows, w - nw)
    tr = [''.join(c) for c in zip(*rows)]
    tr = _drop_lines(tr, h - nh)
    return [''.join(c) for c in zip(*tr)]


def fin(rows):
    rows = fit50(rows)
    if loose.loose_count(rows): rows = loose.fix_loose(rows)
    return O.trim(rows)


LAB = shrink.LAB
SHEET_ROW = {}


def pale(c):
    L_, a, b = LAB[c]
    return L_ >= 72 and (a * a + b * b) ** .5 < 30


def peel(rows):
    """tira o halo claro (adesivo, brilho em volta): contas claras ligadas ao lado de fora, até encostar no contorno"""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    st = [(y, x) for y in range(H) for x in range(W) if g[y][x] == '.' or y in (0, H - 1) or x in (0, W - 1)]
    seen = set(st)
    while st:
        y, x = st.pop()
        if g[y][x] != '.' and pale(g[y][x]): g[y][x] = '.'
        if g[y][x] != '.': continue
        for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= v < H and 0 <= u < W and (v, u) not in seen:
                seen.add((v, u)); st.append((v, u))
    return O.trim([''.join(r) for r in g])


def silhouette(rows, k=9):
    """fundo claro só FORA da silhueta do emblema: o branco de dentro segura as peças juntas"""
    m = np.array([[c == 'k' or c == 'Ù' for c in r] for r in rows], np.uint8)
    c = cv2.morphologyEx(cv2.copyMakeBorder(m, k, k, k, k, cv2.BORDER_CONSTANT, value=0), cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))[k:-k, k:-k]
    f = c.copy(); ff = np.zeros((f.shape[0] + 2, f.shape[1] + 2), np.uint8); cv2.floodFill(f, ff, (0, 0), 2)
    inside = (f != 2)
    return O.trim([''.join(ch if inside[y, x] else '.' for x, ch in enumerate(r)) for y, r in enumerate(rows)])


def drop(letters, r0=0):
    def f(rows):
        return O.trim([''.join('.' if (y >= r0 and c in letters) else c for c in r) for y, r in enumerate(rows)])
    return f


def box_of(rows, box, fill=None):
    """recorta o retângulo (r0, r1, c0, c1, inclusivo); fill = cor das células vazias dentro dele"""
    r0, r1, c0, c1 = box
    r = [l[c0:c1 + 1] for l in rows[r0:r1 + 1]]
    if fill: return O.trim([l.replace('.', fill) for l in r])
    return O.trim(lg(r))


def part(idx, kw, box, fill=None):
    def f():
        return fin(box_of(R.cached(f'sh{idx}', lambda: E(idx, **kw)), box, fill))
    return f


def comp(idx, kw, k, n, rowh):
    """k-ésima das n maiores peças, em ordem de leitura"""
    def f():
        return fin(R.cached(f'cp{idx}', lambda: _sheet(idx, kw, n, rowh))[k])
    return f


def _sheet(idx, kw, n, rowh):
    rows = E(idx, **kw)
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    k, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = sorted(range(1, k), key=lambda i: -st[i][4])[:n]
    big.sort(key=lambda i: (int(cen[i][1] // rowh), cen[i][0]))
    return [O.trim([''.join(c if lab[y, x] == i else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)]) for i in big]


def graph35():
    """os códigos do gráfico são MARD: o B11 dele é oliva e o B11 do kit é quase preto; vale a cor da amostra da legenda. B29 e B32 são verdes-limão vizinhos e ficam separados"""
    old = R.kit_letter
    def kl(c, col):
        if c == 'B29': return (L['B14'],)
        if c == 'H2': return ('w',)
        if c == 'B23': return (L['B11'],)
        return R.nearest_letter(col)
    R.kit_letter = kl
    try: return fin(R.pix_graph(35, dict(px=28.83, py=29.25, ox=7.01, oy=13.50, W=23, H=30), 'A22:8 B11:41 B23:92 B29:68 B32:93 F11:63 F19:4 G6:49 H2:4', name='Planta verde'))
    finally: R.kit_letter = old


def peel_set(rows, letters):
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    st = [(y, x) for y in range(H) for x in range(W) if g[y][x] == '.' or y in (0, H - 1) or x in (0, W - 1)]
    seen = set(st)
    while st:
        y, x = st.pop()
        if g[y][x] in letters: g[y][x] = '.'
        if g[y][x] != '.': continue
        for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= v < H and 0 <= u < W and (v, u) not in seen:
                seen.add((v, u)); st.append((v, u))
    return O.trim([''.join(r) for r in g])


C5 = dict(K=36, dark_frac=0.25, black_L=12.0, thr=240, pale_skin=False, warm_white=0, seal=0.0, smooth_de=10.0)


def deku():
    """a sombra cinza no chão cerca o branco entre as pernas e encosta na luva: pinta a maior mancha cinza de branco ANTES de converter"""
    im = np.array(Image.open(F[50]).convert('RGB')).astype(np.int32)
    gray = ((im.max(axis=2) - im.min(axis=2)) < 16) & (im.mean(axis=2) > 130) & (im.mean(axis=2) < 205)
    n, lab, st, _ = cv2.connectedComponentsWithStats(gray.astype(np.uint8), connectivity=8)
    big = 1 + int(np.argmax(st[1:, 4]))
    im[lab == big] = 255
    tmp = os.path.join(OUT, '_r25_50.png'); Image.fromarray(im.astype(np.uint8)).save(tmp)
    old = F[50]; F[50] = tmp
    try: r = R.ill(50, dict(C5), skin=False)
    finally: F[50] = old
    return fin(lg(r))


def demon42():
    """sem o brilho magenta e a borda de adesivo: com eles, o corpo virava mancha"""
    import colorsys
    HX = {c['letter']: [int(c['hex'].lstrip('#')[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] for c in P.ALL}
    mag = set()
    for c, v in HX.items():
        h, sa, va = colorsys.rgb_to_hsv(*v)
        if (280 <= h * 360 <= 345 and sa > 0.25 and va > 0.5) or LAB[c][0] > 72: mag.add(c)
    r = peel_set(R.ill(42, dict(C5, thr=205, peel=1.0), skin=False), mag)
    return fin(holes(lg(r), 6))


def G(i, **kw):
    post = kw.pop('post2', None)
    def f():
        r = E(i, **kw)
        if post: r = post(r)
        return fin(r)
    return f


CFG = [
 ('Goku Super Saiyajin 4 Limit Breaker (pixel)', 'Dragon Ball', 1, G(1, post=lg, post2=peel)),
 ('Shadow (Sonic, gráfico)', 'Sonic', 2, G(2, post=lg)),
 ('Trunks Super Saiyajin (aura, pixel)', 'Dragon Ball', 3, G(3, colmap=[((15, 255, 254), 50, 'c')], post=lg)),
 ('Mestre Kame (gráfico)', 'Dragon Ball', 4, G(4, colmap=[((211, 124, 79), 26, 't')], post=lg)),
 ('Ichigo Vasto Lorde (Bleach, pixel)', 'Bleach', 5, G(5, post=lg)),
 ('Megumi Fushiguro (Jujutsu Kaisen, pixel)', 'Jujutsu Kaisen', 6, G(6, post=lg)),
 ('Hello Kitty musculosa (gráfico)', 'Hello Kitty', 7, G(7, post=lg)),
 ('Lutador de cabelo preto e gi branco (pixel)', 'Genéricos', 8, G(8, post=lg)),
 ('Cloud Strife (Final Fantasy VII, pixel)', 'Final Fantasy', 9, G(9, post=lg)),
 ('Guarda triângulo (Round 6, gráfico)', 'Round 6', 10, G(10, post=lg)),
 ('Dragão verde de asas lilás (gráfico)', 'Animais', 11, G(11, post=lg)),
 ('Kamui Woods (My Hero Academia, pixel)', 'My Hero Academia', 12, G(12, post=pieces(20))),
 ('Goku Black Rosé (aura roxa, pixel)', 'Dragon Ball', 13, G(13, post=lg)),
 ('Shoto Todoroki (gelo e fogo, pixel)', 'My Hero Academia', 14, G(14, post=pieces(20))),
 ('PlayStation 2 (gráfico)', 'Genéricos', 15, G(15, colmap=[((54, 54, 54), 12, L['H6']), ((39, 39, 39), 8, L['H6'])], dist=8, post=lg)),
 ('Ciclope (X-Men, rajada, pixel)', 'Marvel', 16, G(16, post=pieces(20))),
 ('Gogeta Blue (pixel)', 'Dragon Ball', 17, G(17, post=pieces(10))),
 ('Camaleão verde (gráfico)', 'Animais', 18, G(18, post=pieces(10))),
 ('Super Buu (pixel)', 'Dragon Ball', 19, G(19, post=lg, post2=lambda r: holes(r, 30))),
 ('Nana Shimura (My Hero Academia, pixel)', 'My Hero Academia', 20, G(20, post=lg)),
 ('Jake (Hora de Aventura, gráfico)', 'Hora de Aventura', 21, G(21, post=lg)),
 ('PlayStation 1 (gráfico)', 'Genéricos', 22, G(22, post=lg)),
 ('Katsuki Bakugo (granada, pixel)', 'My Hero Academia', 23, G(23, post=lg, post2=peel)),
 ('Cavaleira de armadura prateada (chibi, pixel)', 'Genéricos', 24, G(24, post=lg)),
 ('Dragão de fogo (gráfico)', 'Animais', 25, G(25, post=lg)),
 ('Banguela e Fúria da Luz (gráfico)', 'Como Treinar o seu Dragão', 26, G(26, post=lg)),
 ('Vault Boy (Fallout, gráfico)', 'Fallout', 27, G(27, post=lg)),
 ('Motoqueiro Fantasma (moto, pixel)', 'Marvel', 28, G(28, crop_img=(0, 0, 750, 512), post=lg)),
 ('Stain (My Hero Academia, pixel)', 'My Hero Academia', 29, G(29, post=lg)),
 ('Yuga Aoyama (My Hero Academia, pixel)', 'My Hero Academia', 31, G(31, post=pieces(20))),
 ('Dragão azul (pixel)', 'Animais', 32, G(32, post=lg)),
 ('Pikachu Yoda (gráfico)', 'Pokémon', 33, G(33, post=lg, post2=peel)),
 ('Mago Negro (Final Fantasy, gráfico)', 'Final Fantasy', 34, G(34, post=lg)),
 ('Endeavor (My Hero Academia, pixel)', 'My Hero Academia', 36, G(36, post=lg)),
 ('Cavaleiro de cabelo preto e espadão (chibi, pixel)', 'Genéricos', 37, G(37, post=lg)),
 ('Cavaleiro de elmo e escudo (pixel)', 'Genéricos', 38, G(38, post=lg)),
 ('Goku Instinto Superior (ataque, gráfico)', 'Dragon Ball', 39, G(39, post=pieces(20))),
 ('Mago grisalho de sobretudo preto (chibi, pixel)', 'Genéricos', 40, G(40, post=lg)),
 ('Golem de pedra (pixel)', 'Genéricos', 41, G(41, post=lg)),
 ('Demônio musculoso de aura roxa (adesivo, pixel)', 'Genéricos', 42, demon42),
 ('Guerreira raposa com cetro (chibi, pixel)', 'Genéricos', 43, G(43, post=lg)),
 ('Gran Torino (My Hero Academia, pixel)', 'My Hero Academia', 44, G(44, post=lg)),
 ('Kakashi (chibi, com livro, pixel)', 'Naruto', 45, G(45, thr=205, post=lg)),
 ('Herói de armadura prateada e azul (pixel)', 'My Hero Academia', 46, G(46, post=lg)),
 ('Eijiro Kirishima (My Hero Academia, pixel)', 'My Hero Academia', 47, G(47, post=lg)),
 ('Goku Black Rosé (foice, pixel)', 'Dragon Ball', 48, G(48, post=lg)),
 ('Dragão verde fofo (gráfico)', 'Animais', 49, G(49, post=lg)),
 ('Deku (ataque, pixel)', 'My Hero Academia', 50, deku),
 ('Atirador de chapéu e bandeira (chibi, pixel)', 'Genéricos', 51, G(51, post=lg)),
 ("Emblema de Assassin's Creed Black Flag (gráfico)", "Assassin's Creed", 52, G(52, crop=(1, 62, 1, 58), ref=(0, 255, 0), tol=1, post2=silhouette)),
 ('Cloud Strife (chibi, pixel)', 'Final Fantasy', 53, G(53, post=lg)),
 ('Goku Super Saiyajin 4 (pixel)', 'Dragon Ball', 55, G(55, post=lg, post2=lambda r: holes(r, 4))),
 ('Naruto Modo Kurama (pixel)', 'Naruto', 56, G(56, crop_img=(0, 0, 720, 1250), post=pieces(10))),
 ('Goku Kaioken (adesivo, pixel)', 'Dragon Ball', 57, G(57, post=lg)),
 ('Tokoyami e Dark Shadow (My Hero Academia, pixel)', 'My Hero Academia', 58, G(58, post=lg)),
 ('Viajante de chapéu pontudo (pixel)', 'Genéricos', 59, G(59, post=lg, post2=drop('o', 40))),
 ('Kaneki de kagune (pixel)', 'Tokyo Ghoul', 60, G(60, post=lg)),
 ('Ned Stark (Game of Thrones, pixel)', 'Game of Thrones', 61, G(61, post=lg)),
 ('Goku Instinto Superior (aura azul, pixel)', 'Dragon Ball', 62, G(62, post=pieces(20))),
 ('Bardock Super Saiyajin (pixel)', 'Dragon Ball', 64, G(64, post=lg)),
 ('Ainz Ooal Gown (Overlord, pixel)', 'Overlord', 65, G(65, post=lg)),
 ('Naruto de 4 caudas (gráfico)', 'Naruto', 66, G(66, post=lg)),
 ('Ceifador de capuz vermelho e tocha (pixel)', 'Genéricos', 67, G(67, post=pieces(10))),
]
CFG = [c + ('graf',) for c in CFG]

SH0 = dict(thr=205, crop=(0, 97, 0, 69))
FOLHA0 = [('Morango (pixel)', 'Genéricos', (0, 9, 0, 8)), ('Cogumelo vermelho (Mario, pixel)', 'Mario', (0, 9, 11, 21)), ('Círculo vermelho com símbolo branco (pixel)', 'Genéricos', (1, 16, 24, 38)), ('Coração costurado (pixel)', 'Genéricos', (2, 10, 40, 48)),
          ('Ás de copas (pixel)', 'Genéricos', (12, 27, 1, 11)), ('Fantasma vermelho (Pac-Man, pixel)', 'Genéricos', (12, 18, 14, 20)), ('Cogumelinho vermelho (pixel)', 'Genéricos', (21, 26, 14, 19)), ('Creeper vermelho (Minecraft, pixel)', 'Minecraft', (19, 26, 23, 30)),
          ('Homem-Aranha (chibi, folha vermelha)', 'Marvel', (14, 28, 37, 47)), ('Pokébola (folha vermelha)', 'Pokémon', (19, 30, 51, 62)), ('Proibido fumar (pixel)', 'Genéricos', (30, 44, 1, 15)), ('Máscara do Homem-Aranha (pixel)', 'Marvel', (29, 43, 19, 33)),
          ('Cachorro de balão (pixel)', 'Genéricos', (31, 50, 36, 59)), ('Guarda quadrado (Round 6, pixel)', 'Round 6', (47, 78, 1, 23)), ('Taça de vinho (pixel)', 'Genéricos', (47, 62, 26, 37)), ('Lábios (pixel)', 'Genéricos', (53, 62, 42, 56)),
          ('Morango pequeno (pixel)', 'Genéricos', (52, 59, 59, 64)), ('Caveira de bandana (pixel)', 'Genéricos', (65, 82, 24, 39)), ('Homem-Aranha de perfil (pixel)', 'Marvel', (65, 95, 43, 67)), ('Joaninha (pixel)', 'Genéricos', (82, 91, 1, 7)),
          ('Relâmpago McQueen (pixel)', 'Carros', (82, 89, 10, 23)), ('Pirulito (pixel)', 'Genéricos', (82, 95, 37, 45)), ('Olho vermelho (pixel)', 'Genéricos', (85, 91, 26, 35)), ('Coração vermelho (pixel)', 'Genéricos', (89, 94, 52, 58))]
for _n, _g, _b in FOLHA0:
    CFG.append((_n, _g, 0, part(0, SH0, _b), 'folha'))
CFG.append(('TNT (Minecraft, pixel)', 'Minecraft', 0, part(0, SH0, (1, 16, 50, 65), 'w'), 'folha'))
SH54 = dict(crop_img=(0, 0, 720, 975), tol=60)
FOLHA54 = [('Bloco de interrogação (Mario, desenhado)', 'Mario'), ('Super Estrela (Mario, desenhada)', 'Mario'), ('Moeda (Mario, desenhada)', 'Mario'), ('Ovo de Yoshi (Mario, desenhado)', 'Mario'), ('Nuvem de Lakitu (Mario, desenhada)', 'Mario'), ('Flor de fogo (Mario, desenhada)', 'Mario')]
FOLHA63 = [('Trevo de 4 folhas (pixel)', 'Genéricos'), ('Caixinha de suco de maçã (pixel)', 'Genéricos'), ('Broto no vaso (pixel)', 'Genéricos'), ('Cobrinha verde (pixel)', 'Animais'), ('Dinossauro verde (pixel, versão 2)', 'Animais'), ('Tartaruguinha verde (pixel)', 'Animais')]
def _paper(rows):
    return peel([''.join('w' if c != '.' and LAB[c][0] >= 62 and (LAB[c][1] ** 2 + LAB[c][2] ** 2) ** .5 < 12 else c for c in r) for r in rows])


def comp54(k):
    return lambda: _paper(comp(54, SH54, k, 6, 19.0)())


for _k, (_n, _g) in enumerate(FOLHA54):
    CFG.append((_n, _g, 54, comp54(_k), 'folha'))
for _k, (_n, _g) in enumerate(FOLHA63):
    CFG.append((_n, _g, 63, comp(63, {}, _k, 6, 16.0), 'folha'))
CFG.append(('Pequeno Príncipe e a raposa (gráfico)', 'O Pequeno Príncipe', 30, G(30, px=dict(px=13.15, py=13.14, ox=12.12, oy=37.94, W=54, H=66), mode=True, ref=(197, 214, 198), tol=16, bgs=[((206, 185, 172), 24)], post=lg), 'graf'))
CFG.append(('Planta verde de olho vermelho (gráfico)', 'Genéricos', 35, graph35, 'graf'))


# rostos que a redução apagou, lidos na arte com tools/r25_sheet.py (olhos discretos, sem boca: CLAUDE.md §4.8). (linha, coluna, [texto]); ' ' não mexe
TOUCH = {
 'Deku (ataque, pixel)': [(15, 18, ['kkkkk']), (16, 18, ['kwwkwk']), (17, 18, ['kwwkwk']), (18, 18, ['gkkkkg']),
                          (15, 24, ['skkkk']), (16, 24, ['swwkwk']), (17, 24, ['swwkws']), (18, 23, ['ssËËËËs']), (19, 23, ['ssssss']), (21, 25, ['s'])],
 'Cavaleiro de cabelo preto e espadão (chibi, pixel)': [(14, 19, ['ÁÁkÁÁ']), (15, 17, ['Á h Á Áh  Á'.replace(' ', 'k')]), (16, 18, ['wMÁÁÁMw']), (17, 18, ['ÁÁÁÁÁÁÁ'])],
 'Goku Black Rosé (foice, pixel)': [(10, 30, ['ÁÁÁ']), (11, 30, ['ÁÁÁ']), (12, 30, ['kkÁÁkÅÁ']), (13, 30, ['ÅÁÁÁÁÉ']), (14, 31, ['ÅÁÁ'])],
}


def touched(n, r):
    if n not in TOUCH: return r
    g = [list(x) for x in r]
    for y0, x0, lines in TOUCH[n]:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c != ' ': g[y0 + j][x0 + i] = c
    return [''.join(x) for x in g]


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--H' in sys.argv: args.remove(sys.argv[sys.argv.index('--H') + 1])
    grupo = None
    if '--grupo' in sys.argv:
        grupo = sys.argv[sys.argv.index('--grupo') + 1]; args = [a for a in args if a != grupo]
    one = []; sheet = []
    for n, g, idx, fn, grp in CFG:
        if grupo and grp != grupo: continue
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = touched(n, fn()); one.append((n, g, r)); sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa')
    tag = (grupo or 'all') + ('_f' if args else '')
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r25_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r25_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and ('--merge' in sys.argv or (not args and not grupo)):
        pth = os.path.join(SP, 'data', 'final27' + sfx() + '.json')
        old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) and (args or grupo) else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok')
