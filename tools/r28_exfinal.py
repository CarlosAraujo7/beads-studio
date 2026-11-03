"""Remessa 28 (138 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r28_exfinal.py [filtro...] [--grupo facil|num|folha|...] [--merge] [--H 520]
   -> data/final30_120.json (tudo em 1 placa, sem irmão grande). Reaproveita os auxiliares do r26_exfinal.py: o import aponta para a remessa 26 e a lista de arquivos é trocada aqui.
Quase tudo é gráfico em malha ou pixel art: molde 100% FIEL à imagem (CLAUDE.md §4.1; sem retoque de rosto). O que passa de 50 é reduzido para 1 placa (fit50: até 1,3x tira linhas e colunas inteiras;
acima, voto por grupos de tons). Gráficos com número escrito em cada quadradinho: grade pela régua e conferência pela legenda (§7.37, tools/legend_check.py).
Fora: 102 e 122 (arquivos byte a byte iguais a 101 e 121) e 115 (PNG transparente sem desenho, o mesmo da remessa 18)."""
import os, sys, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r26_exfinal as X
from r26_exfinal import r5, r6, O, np, R, G, E, F, L, LAB, OUT, fin, lg, holes, pieces, pale, peel_set, clearb, chain, comp, vote, sfx, C5, delc
import cv2
from PIL import Image
F[:] = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa 28', '*.*')))          # F é a mesma lista de r6.FILES e R.F


def P4(i, **kw):
    """gráfico com pontinhos soltos (marca d'água, JPEG): mantém só as peças com pelo menos 4 contas"""
    kw.setdefault('post', pieces(4))
    return G(i, **kw)


def rowfix(y, bad):
    """marca d'água escrita por cima do desenho numa linha: cada conta com uma das letras `bad` copia a conta de baixo (ou a de cima; vazio se as duas são vazias)"""
    def f(rows):
        g = [list(r) for r in rows]
        for x, c in enumerate(g[y]):
            if c in bad:
                below = g[y + 1][x] if y + 1 < len(g) else '.'
                above = g[y - 1][x] if y > 0 else '.'
                g[y][x] = below if below != '.' else above
        return [''.join(r) for r in g]
    return f


def SK(f):
    """liga a trava de pele só nesta conversão (o run() a desliga): gráfico de captura com textura de ponto-cruz no rosto, onde o creme vira branco e creme salpicados"""
    def g():
        r5.SKIN_ON = True
        return f()
    return g


def NG(idx, grid, ruler=False, **kw):
    """gráfico com régua numerada e legenda: grade de autogrid.py (cobre a imagem toda), cor dominante da célula (o número escrito dentro é minoria), só a maior peça.
    ruler=True: a régua e a faixa do nome são coloridas (verde-água): a cor mais comum nas 2 primeiras linhas/colunas e nas 3 últimas linhas entra como fundo extra"""
    def f():
        k = dict(kw)
        if ruler:
            from collections import Counter
            arr = r6.load_cells(idx, px=grid, mode=True)
            border = np.concatenate([arr[0:2].reshape(-1, 3), arr[:, 0:2].reshape(-1, 3), arr[-3:].reshape(-1, 3)])
            q = Counter(tuple(int(v) // 8 * 8 + 4 for v in c) for c in border if min(c) < 245)
            k['bgs'] = [(q.most_common(1)[0][0], 26), ((255, 255, 255), 14)]          # a régua colorida e o branco do papel saem por inundação a partir da borda
        k.setdefault('post', lg)
        return G(idx, px=grid, mode=True, **k)()
    return f



def jujuba_face(rows):
    """a Princesa Jujuba em ponto-cruz: as células do rosto têm o fio escuro do "x" e saem cinza-rosado (croma < 7 = cinza no near120); o rosto da imagem é rosa-claro: cinzas claros do rosto viram E15 e o branco E11"""
    g = [list(r) for r in rows]
    for y in range(12, min(30, len(g))):
        for x in range(11, min(23, len(g[y]))):
            c = g[y][x]
            if c in (L['H3'], L['H1'], L['H4']): g[y][x] = L['E15']
            elif c == L['H2']: g[y][x] = L['E11']
    return [''.join(r) for r in g]


def PG(idx, grid, legend, name, fix=None):
    """gráfico em códigos MARD com legenda: a cor de cada célula é a da AMOSTRA da legenda (o mesmo código é outra cor no kit Pindou, CLAUDE.md §7.29), a contagem é conferida com a legenda (§7.37)"""
    def f():
        old = R.kit_letter

        def kl(c, col):
            if c == 'H2': return ('w',)
            return R.nearest_letter(col)
        R.kit_letter = kl
        try: return fin(R.pix_graph(idx, grid, legend, name=name, fix=fix))
        finally: R.kit_letter = old
    return f


def TG(idx, grid, legend, name, fix=None):
    """gráfico com o CÓDIGO escrito em cada célula e todos os códigos no kit: célula não branca = cor mais próxima das amostras da legenda; branca COM texto = conta H2; branca SEM texto = vazio
    (o fundo branco ligado à borda não sabe separar as duas, §7.37); cada código vira a letra do próprio kit"""
    def f():
        import cv2
        codes = [t.split(':') for t in legend.split()]
        nonwhite = [(c, int(n)) for c, n in codes if c != 'H2']
        rgb = np.array(R.source_img(idx)).astype(np.uint8)
        sw = R.legend_swatches(idx, int(grid['oy'] + grid['H'] * grid['py'] + 35), len(nonwhite))
        cls = [(c, np.array(col, float)) for (c, _), col in zip(nonwhite, sw)] + [('H2', np.array([255., 255., 255.]))]
        arr = r6.load_cells(idx, px=grid, mode=True)
        lab = R.illus._lab(arr); cl = np.stack([R.illus._lab(c[1]) for c in cls])
        d = np.linalg.norm(lab[:, :, None, :] - cl[None, None, :, :], axis=3); order = np.argsort(d, axis=2)
        white = (order[:, :, 0] == len(cls) - 1) | (arr.min(axis=2) > 250)
        H, W = grid['H'], grid['W']; px, py, ox, oy = grid['px'], grid['py'], grid['ox'], grid['oy']

        def has_text(y, x, m=0.12):
            sub = rgb[int(round(oy + (y + m) * py)):int(round(oy + (y + 1 - m) * py)), int(round(ox + (x + m) * px)):int(round(ox + (x + 1 - m) * px))]
            if sub.size == 0: return False
            g = cv2.cvtColor(sub, cv2.COLOR_RGB2GRAY).astype(np.float32); h, w = g.shape
            b = max(2, min(h, w) // 7)
            bg = np.median(np.concatenate([g[:b].ravel(), g[-b:].ravel(), g[:, :b].ravel(), g[:, -b:].ravel()]))
            return float(np.abs(g - bg).max()) >= 45
        rows = []; got = {}
        for y in range(H):
            line = ''
            for x in range(W):
                if fix and (y, x) in fix: code = fix[(y, x)]
                elif white[y, x]: code = 'H2' if has_text(y, x) else None
                else: code = cls[order[y, x, 0]][0]
                if code is None: line += '.'; continue
                got[code] = got.get(code, 0) + 1; line += L[code]
            rows.append(line)
        diff = [f'{c}:{got.get(c, 0)}/{n}' for c, n in codes if got.get(c, 0) != int(n)]
        print(f'  [{name}] {W}x{H}  contagens {"IGUAIS à legenda" if not diff else "DIFERENTES (obtido/legenda): " + " ".join(diff)}')
        return fin(rows)
    return f


def _cb(rows):
    W = len(rows[0]); out = []; cur = []
    for x in range(W):
        if all(r[x] == '.' for r in rows):
            if cur: out.append(cur); cur = []
        else: cur.append(x)
    if cur: out.append(cur)
    return [O.trim([''.join(r[x] for x in xs) for r in rows]) for xs in out]


def _rb(rows):
    out = []; cur = []
    for r in rows:
        if all(c == '.' for c in r):
            if cur: out.append(cur); cur = []
        else: cur.append(r)
    if cur: out.append(cur)
    return [O.trim(b) for b in out]


_FOLHA = {}


def FOLHA(key, idx, kw, k, post=None):
    """folha de várias figuras: converte a imagem inteira uma vez e devolve a figura k (linhas vazias separam as faixas, colunas vazias separam as figuras da faixa)"""
    def f():
        if key not in _FOLHA:
            r = E(idx, **kw); figs = []
            for band in _rb(r): figs += _cb(band)
            _FOLHA[key] = figs
        r = _FOLHA[key][k]
        if post: r = post(r)
        return fin(r)
    return f


_ALIEN = {}


def ALIEN(k, clear=None):
    """folha de 8 alienígenas sobre fundo azul-escuro (imagem 101): converte a folha inteira, separa as peças ligadas (as 8 maiores; os espirais da marca d'água e a faixa do rodapé saem) e devolve a k-ésima na ordem de leitura"""
    def f():
        import cv2
        if not _ALIEN:
            r = E(101, px=dict(px=11.26, py=11.26, ox=6.64, oy=11.24, W=142, H=94), mode=True, ref=(28, 25, 90), tol=34)
            m = np.array([[c != '.' for c in row] for row in r], np.uint8)
            n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
            pcs = [i for i in range(1, n) if st[i][4] >= 100 and st[i][2] < 40 and st[i][3] < 40]
            pcs.sort(key=lambda i: (int(cen[i][1] // 40), cen[i][0]))
            for j, i in enumerate(pcs):
                x0, y0, w, h = [int(v) for v in st[i][:4]]
                _ALIEN[j] = [''.join(r[y][x] if lab[y, x] == i else '.' for x in range(x0, x0 + w)) for y in range(y0, y0 + h)]
        r = _ALIEN[k]
        if clear:
            y0, y1, x0, x1 = clear
            r = [''.join('.' if (y0 <= y <= y1 and x0 <= x <= x1) else c for x, c in enumerate(row)) for y, row in enumerate(r)]
        return fin(r)
    return f


def unframe(rows):
    """captura do editor de gráficos: a moldura e a régua (cor D16) formam as primeiras linhas e colunas e impedem a inundação do branco de partir da borda; tira-as e depois tira o branco ligado à borda"""
    ruler = L['D16']; g = [list(r) for r in rows]

    def edge(line): return sum(1 for ch in line if ch == ruler) >= 0.8 * len(line)
    changed = True
    while changed and len(g) > 3 and len(g[0]) > 3:
        changed = False
        if edge(g[0]): g.pop(0); changed = True
        elif edge(g[-1]): g.pop(); changed = True
        elif edge([r[0] for r in g]): [r.pop(0) for r in g]; changed = True
        elif edge([r[-1] for r in g]): [r.pop() for r in g]; changed = True
    return peel_set([''.join(r) for r in g], {L['H2']})


def S113(k):
    """a imagem 113 tem 2 desenhos empilhados sobre papel quadriculado: converte inteira e devolve o bloco k (separados por linhas vazias)"""
    def f():
        r = E(113, crop_img=(78, 58, 1010, 1901), px=dict(px=26.055, py=26.181, ox=19.34, oy=10.33, W=35, H=70), mode=True)
        blocks = []; cur = []
        for row in r:
            if set(row) == {'.'}:
                if cur: blocks.append(cur); cur = []
            else: cur.append(row)
        if cur: blocks.append(cur)
        return fin(O.trim(blocks[k]))
    return f

CFG = [
 # ---- gráficos em malha que a passada automática leu direto: (nome, série, índice, conversão, grupo)
 ('Patrick Estrela assustado (pixel)', 'Bob Esponja', 0, G(0, ref=(100, 152, 214), tol=40, bgs=[((214, 207, 177), 40)], allbg=True), 'facil'),
 ('Shikamaru (chibi, pixel)', 'Naruto', 1, G(1, post=lg), 'facil'),
 ('Gato de Cheshire (pixel)', 'Disney', 2, G(2, post=lg), 'facil'),
 ('Om Nom (Cut the Rope, pixel)', 'Cut the Rope', 3, G(3, post=lg), 'facil'),
 ('Heisenberg (Breaking Bad, chibi, pixel)', 'Breaking Bad', 4, G(4, post=lg), 'facil'),
 ('Porquinho rei de capa vermelha (pixel)', 'Animais', 5, G(5, post=lg), 'facil'),
 ('Jax (The Amazing Digital Circus, pixel)', 'The Amazing Digital Circus', 6, G(6, achro=190, post=lg), 'facil'),
 ('BMO (Hora de Aventura, pixel)', 'Hora de Aventura', 8, P4(8), 'facil'),
 ('Olaf (Frozen, pixel)', 'Disney', 9, P4(9), 'facil'),
 ('Pou assustado (pixel)', 'Pou', 10, G(10, post=lg), 'facil'),
 ('Jinx (Arcane, chibi, pixel)', 'Arcane', 12, P4(12), 'facil'),
 ('Capitão América e escudo (pixel)', 'Marvel', 13, G(13, post=lg), 'facil'),
 ('Mario Guaxinim voando (pixel)', 'Mario', 14, G(14, post=lg), 'facil'),
 ('OVNI e vaca (pixel)', 'Genéricos', 18, G(18, post=lg), 'facil'),
 ('Chibi de cabelo preto e correntes (pixel)', 'Genéricos', 19, G(19, post=lg), 'facil'),
 ('Mark Grayson (Invencível, pixel)', 'Invencível', 20, G(20, post=lg), 'facil'),
 ('Rick Sanchez (Rick and Morty, pixel)', 'Rick and Morty', 21, P4(21), 'facil'),
 ('Narval fofo (pixel)', 'Animais', 22, G(22, post=lg), 'facil'),
 ('Luigi (pixel)', 'Mario', 24, G(24, post=lg), 'facil'),
 ('All Might (pixel)', 'My Hero Academia', 25, G(25, post=lg), 'facil'),
 ('Totoro de guarda-chuva (pixel)', 'Studio Ghibli', 27, P4(27), 'facil'),
 ('Itachi Uchiha (pixel)', 'Naruto', 28, P4(28), 'facil'),
 ('Mão do Homem de Ferro (pixel)', 'Marvel', 30, G(30, post=lg), 'facil'),
 ('Brian Griffin (Family Guy, pixel)', 'Family Guy', 31, G(31, post=lg), 'facil'),
 ('Plankton (pixel)', 'Bob Esponja', 32, G(32, post=pieces(4), post2=rowfix(18, set('!v%/b3&e'))), 'facil'),
 ('Chibi de cabelo preto e terno (pixel)', 'Genéricos', 34, G(34, post=lg), 'facil'),
 ('Pantera Cor-de-Rosa (pixel)', 'Pantera Cor-de-Rosa', 35, G(35, post=lg), 'facil'),
 ('Naruto com Rasengan (pixel)', 'Naruto', 36, G(36, post=lg), 'facil'),
 ('Porquinho rei de capa vermelha (pixel, versão 2)', 'Animais', 37, G(37, post=lg), 'facil'),
 ('Homer Simpson com rosquinha (pixel)', 'Os Simpsons', 38, P4(38), 'facil'),
 ('Majin Buu (pixel)', 'Dragon Ball', 40, G(40, post=lg), 'facil'),
 ('Obelix (pixel)', 'Asterix', 41, G(41, post=lg), 'facil'),
 ('Peppermint Butler (Hora de Aventura, pixel)', 'Hora de Aventura', 42, G(42, post=lg), 'facil'),
 ('Kirby (pixel)', 'Kirby', 43, G(43, post=lg), 'facil'),
 ('Power (Chainsaw Man, chibi, pixel)', 'Chainsaw Man', 45, G(45, post=lg), 'facil'),
 ('Woody Woodpecker (pixel)', 'Pica-Pau', 48, G(48, post=lg), 'facil'),
 ('Dinossauro verde fofo (pixel)', 'Animais', 49, G(49, post=lg), 'facil'),
 ('Chibi de cabelo roxo e robe (pixel)', 'Genéricos', 50, P4(50), 'facil'),
 ('Coelhinho de terno e gravata vermelha (pixel)', 'Animais', 52, G(52, post=lg), 'facil'),
 ('Logo dos Caça-Fantasmas (pixel)', 'Ghostbusters', 53, G(53, post=lg), 'facil'),
 ('Angel Devil (Chainsaw Man, chibi, pixel)', 'Chainsaw Man', 54, G(54, post=lg), 'facil'),
 ('Fred Flintstone (pixel)', 'Os Flintstones', 55, G(55, post=lg), 'facil'),
 ('Jerry (Tom e Jerry, pixel)', 'Tom e Jerry', 56, P4(56), 'facil'),
 ('Finn (Hora de Aventura, pixel)', 'Hora de Aventura', 59, G(59, post=lg), 'facil'),
 ('Pompompurin (Sanrio, pixel)', 'Hello Kitty', 60, G(60, post=lg), 'facil'),
 ('Trafalgar Law (chibi, pixel)', 'One Piece', 61, P4(61), 'facil'),
 ('Bob Esponja zombeteiro (pixel)', 'Bob Esponja', 63, G(63, post=lg), 'facil'),
 ('Fionna (Hora de Aventura, pixel)', 'Hora de Aventura', 65, G(65, post=lg), 'facil'),
 ('Fionna (Hora de Aventura, chibi, pixel)', 'Hora de Aventura', 66, G(66, post=lg, post2=clearb((34, 36, 17, 23))), 'facil'),
 ('Smurf azul-escuro (pixel)', 'Os Smurfs', 68, G(68, post=lg), 'facil'),
 ('Jake dentro do morango (Hora de Aventura, pixel)', 'Hora de Aventura', 69, G(69, post=lg), 'facil'),
 ('Tree Trunks (Hora de Aventura, pixel)', 'Hora de Aventura', 73, G(73, post=lg), 'facil'),
 ('Gatinho cinza com balão (pixel)', 'Animais', 74, G(74, post=lg), 'facil'),
 ('Princesa Jujuba (Hora de Aventura, pixel)', 'Hora de Aventura', 75, G(75, post=lg), 'facil'),
 ('San (Princesa Mononoke, chibi, pixel)', 'Studio Ghibli', 76, G(76, post=lg), 'facil'),
 ('Tanjiro Kamado (pixel)', 'Demon Slayer', 78, G(78, post=lg), 'facil'),
 ('Nezuko Kamado (chibi, pixel)', 'Demon Slayer', 80, P4(80), 'facil'),
 ('Raposa rosa (pixel)', 'Animais', 81, P4(81), 'facil'),
 ('Tengen Uzui (pixel)', 'Demon Slayer', 83, G(83, post=lg), 'facil'),
 ('Pato Donald (rosto, pixel)', 'Disney', 84, G(84, post=lg), 'facil'),
 ('Power (Chainsaw Man, chibi, pixel, versão 2)', 'Chainsaw Man', 86, G(86, post=lg), 'facil'),
 ('Chibi de cabelo espetado e faixa branca (pixel)', 'Genéricos', 87, G(87, crop_img=(30, 0, 340, 604), ref=(255, 255, 255), tol=14, post=lg), 'facil'),
 ('Chibi de capuz branco e olhos rosados (pixel)', 'Genéricos', 90, G(90, post=lg), 'facil'),
 ('Gumball Watterson (pixel)', 'O Incrível Mundo de Gumball', 92, G(92, post=lg), 'facil'),
 ('Rock Lee (pixel)', 'Naruto', 93, P4(93), 'facil'),
 ('Shota Aizawa (My Hero Academia, chibi, pixel)', 'My Hero Academia', 94, P4(94), 'facil'),
 ('Doutor Estranho (pixel)', 'Marvel', 95, G(95, thr=240, post=lg), 'facil'),
 ('Papai Smurf (pixel)', 'Os Smurfs', 96, G(96, post=lg), 'facil'),
 ('Loki (pixel)', 'Marvel', 97, P4(97), 'facil'),
 ('Chibi loiro de óculos e jaleco (pixel)', 'Genéricos', 98, G(98, post=lg), 'facil'),
 ('Marceline (Hora de Aventura, chapéu e baixo, pixel)', 'Hora de Aventura', 99, G(99, post=lg), 'facil'),
 ('Sailor Moon sentada na lua (pixel)', 'Sailor Moon', 100, P4(100), 'facil'),
 ('Gato com fantasia de tubarão (pixel)', 'Animais', 106, G(106, post=lg), 'facil'),
 ('Pusheen na rosquinha (pixel)', 'Pusheen', 107, G(107, post=lg), 'facil'),
 ('Gunter (Hora de Aventura, pixel)', 'Hora de Aventura', 108, G(108, post=lg), 'facil'),
 ('Princesa Chama (Hora de Aventura, pixel)', 'Hora de Aventura', 109, P4(109), 'facil'),
 ('Himiko Toga (pixel)', 'My Hero Academia', 110, P4(110), 'facil'),
 ('Izuku Midoriya (chibi, pixel)', 'My Hero Academia', 117, P4(117), 'facil'),
 ('Sol e lua de chapéu de bobo (pixel)', 'Genéricos', 118, G(118, post=lg), 'facil'),
 ('Shoto Todoroki (chibi, pixel)', 'My Hero Academia', 119, P4(119), 'facil'),
 ('Katsuki Bakugo (chibi, pixel)', 'My Hero Academia', 125, P4(125), 'facil'),
 ('Mitsuri Kanroji (chibi, pixel)', 'Demon Slayer', 127, G(127, post=lg), 'facil'),
 ('Smurfette (pixel)', 'Os Smurfs', 129, G(129, post=lg), 'facil'),
 ('Naruto Modo Barião (pixel)', 'Naruto', 130, P4(130), 'facil'),
 ('Lumpy Space Princess (Hora de Aventura, pixel)', 'Hora de Aventura', 131, G(131, post=lg), 'facil'),
 ('Tio Patinhas (pixel)', 'Disney', 132, G(132, post=lg), 'facil'),
 ('Asterix (pixel)', 'Asterix', 133, P4(133), 'facil'),
 ('Fionna e Cake (Hora de Aventura, pixel)', 'Hora de Aventura', 135, P4(135), 'facil'),

 # ---- gráficos com régua e legenda (grupo 'num')
 ('Chibi de cabelo verde-oliva e jaleco branco (gráfico)', 'Genéricos', 15, NG(15, dict(px=21.999, py=21.997, ox=21.66, oy=21.65, W=23, H=30)), 'num'),
 ('Armin Arlert (Attack on Titan, chibi, gráfico)', 'Attack on Titan', 17, NG(17, dict(px=21.78, py=21.837, ox=20.93, oy=20.85, W=22, H=40)), 'num'),
 ('Chibi loira de maria-chiquinhas e uniforme azul (gráfico)', 'Genéricos', 26, NG(26, dict(px=21.997, py=22.0, ox=21.66, oy=21.66, W=37, H=34)), 'num'),
 ('Chibi de cabelo azul-claro e blazer azul-marinho (gráfico)', 'Genéricos', 29, NG(29, dict(px=22.077, py=21.997, ox=20.59, oy=21.63, W=21, H=30)), 'num'),
 ('Chibi de cabelo verde-água e máscara roxa (gráfico)', 'Genéricos', 51, NG(51, dict(px=21.998, py=21.998, ox=21.66, oy=21.65, W=24, H=33)), 'num'),
 ('Satoru Gojo (Jujutsu Kaisen, chibi, gráfico)', 'Jujutsu Kaisen', 77, NG(77, dict(px=21.998, py=21.997, ox=21.67, oy=21.69, W=23, H=32)), 'num'),
 ('Chibi de cabelo preto e quimono azul (gráfico)', 'Genéricos', 82, NG(82, dict(px=21.998, py=21.998, ox=21.59, oy=21.59, W=21, H=34)), 'num'),
 ('Nobara Kugisaki (Jujutsu Kaisen, chibi, gráfico)', 'Jujutsu Kaisen', 88, NG(88, dict(px=22.002, py=21.997, ox=21.95, oy=21.61, W=21, H=30)), 'num'),
 ('Panda (Jujutsu Kaisen, gráfico)', 'Jujutsu Kaisen', 121, NG(121, dict(px=22.0, py=21.999, ox=21.94, oy=21.69, W=29, H=32)), 'num'),
 ('Yuji Itadori (Jujutsu Kaisen, chibi, gráfico)', 'Jujutsu Kaisen', 123, NG(123, dict(px=21.997, py=21.999, ox=21.63, oy=21.65, W=23, H=31)), 'num'),
 ('Kohaku (Dr. Stone, chibi, gráfico)', 'Dr. Stone', 16, NG(16, dict(px=17.001, py=17.001, ox=0.07, oy=16.14, W=22, H=38), ruler=True), 'num'),
 ('Suika (Dr. Stone, chibi, gráfico)', 'Dr. Stone', 72, NG(72, dict(px=20.003, py=20.0, ox=18.11, oy=0.65, W=22, H=32), ruler=True), 'num'),
 ('Ishigami Senku (Dr. Stone, chibi, gráfico)', 'Dr. Stone', 89, NG(89, dict(px=20.001, py=19.998, ox=18.42, oy=0.65, W=21, H=34), ruler=True), 'num'),
 ('Asagiri Gen (Dr. Stone, chibi, gráfico)', 'Dr. Stone', 105, NG(105, dict(px=20.001, py=19.996, ox=18.18, oy=0.59, W=19, H=34), ruler=True), 'num'),
 ('Star-Lord (Guardiões da Galáxia, chibi, gráfico)', 'Marvel', 124, NG(124, dict(px=24.003, py=23.997, ox=22.16, oy=1.61, W=21, H=28), ruler=True), 'num'),
 ('Gaara (Naruto, chibi com ursinho, gráfico)', 'Naruto', 62, SK(NG(62, dict(px=7.998, py=7.997, ox=7.77, oy=7.77, W=55, H=65))), 'num'),
 ('Logo do Batman (gráfico)', 'DC Comics', 126, NG(126, dict(px=30.001, py=30.0, ox=28.2, oy=28.2, W=39, H=35)), 'num'),
 ('Jake (Hora de Aventura, ponto-cruz)', 'Hora de Aventura', 128, NG(128, dict(px=16.003, py=16.062, ox=7.22, oy=6.68, W=31, H=27)), 'num'),
 ('Finn (Hora de Aventura, ponto-cruz)', 'Hora de Aventura', 67, NG(67, dict(px=16.002, py=16.039, ox=7.18, oy=6.8, W=30, H=40)), 'num'),

 # ---- o que faltava (2026-11-03): pixel art sem linhas (passo nativo medido por pixsize/autogrid_crop) e gráficos com grade
 ('Garota de cabelo castanho e suéter rosa (pixel)', 'Genéricos', 114, G(114, crop_img=(100, 0, 1060, 1850), px=dict(px=35.0, py=34.859, ox=14.72, oy=18.77, W=27, H=53), mode=True, post=lg), 'resto'),
 ('Guerreiro nativo de cocar colorido (pixel)', 'Genéricos', 136, G(136, crop_img=(50, 150, 310, 490), px=dict(px=8.546, py=8.543, ox=4.38, oy=5.68, W=30, H=39), mode=True, post=lg), 'resto'),
 ('Espantalho de chapéu preto e cachecol roxo (pixel)', 'Genéricos', 137, G(137, crop_img=(118, 25, 328, 421), px=dict(px=11.7, py=11.776, ox=10.92, oy=9.11, W=17, H=33), mode=True, ref=(160, 194, 110), tol=34, allbg=True, post=lg), 'resto'),
 ('Soldado de camuflagem verde com fuzil (pixel)', 'Genéricos', 116, G(116, crop_img=(0, 20, 1152, 1920), px=dict(px=58.498, py=59.337, ox=39.75, oy=1.74, W=19, H=32), mode=True, post=lg), 'resto'),
 ('Chibi loira de chapéu azul-marinho (gráfico)', 'Genéricos', 120, G(120, crop_img=(50, 0, 587, 822), px=dict(px=26.852, py=26.846, ox=0.0, oy=23.02, W=20, H=30), mode=True, post=lg), 'resto'),
 ('Princesa Jujuba (Hora de Aventura, ponto-cruz)', 'Hora de Aventura', 11, G(11, crop_img=(0, 12, 226, 474), px=dict(px=6.352, py=6.4, ox=6.18, oy=0.17, W=35, H=72), mode=True, dist=24, post=lg, post2=jujuba_face), 'resto'),
 ('Smurf de óculos (pixel)', 'Os Smurfs', 47, G(47, crop_img=(4, 68, 546, 882), px=dict(px=11.099, py=11.099, ox=6.07, oy=1.97, W=48, H=73), mode=True, post=lg), 'resto'),
 ('Barney Rubble (Os Flintstones, pixel)', 'Os Flintstones', 64, G(64, crop_img=(0, 54, 540, 816), px=dict(px=19.232, py=19.249, ox=18.14, oy=17.69, W=27, H=39), mode=True, post=lg), 'resto'),
 ('Naruto (chibi, ponto-cruz)', 'Naruto', 79, G(79, crop_img=(0, 0, 736, 1100), px=dict(px=19.271, py=19.255, ox=1.72, oy=5.24, W=38, H=57), mode=True, post=lg), 'resto'),
 ('Cobra de capuz listrado (pixel)', 'Animais', 113, S113(0), 'resto'),
 ('Macaco marrom de barba (pixel)', 'Animais', 113, S113(1), 'resto'),
 ('Chibi loiro de olhos azuis e jaqueta marrom (Attack on Titan, gráfico)', 'Attack on Titan', 85, G(85, crop_img=(0, 0, 640, 832), px=dict(px=23.108, py=23.147, ox=19.28, oy=19.97, W=27, H=35), mode=True, post=lg, post2=unframe), 'resto'),
 ('Hange Zoë (Attack on Titan, chibi, gráfico)', 'Attack on Titan', 103, G(103, crop_img=(0, 0, 640, 794), px=dict(px=19.361, py=19.366, ox=13.65, oy=16.09, W=32, H=40), mode=True, colmap=[((75, 39, 33), 14, L['G8']), ((50, 25, 14), 14, L['G8'])], post=lg, post2=unframe), 'resto'),
 ('Annie Leonhart (Attack on Titan, chibi, gráfico)', 'Attack on Titan', 112, G(112, crop_img=(0, 0, 400, 444), px=dict(px=12.669, py=12.67, ox=10.26, oy=11.77, W=31, H=34), mode=True, post=lg, post2=unframe), 'resto'),
 ('Marin Kitagawa (My Dress-Up Darling, chibi, gráfico)', 'My Dress-Up Darling', 91, G(91, crop_img=(0, 400, 520, 1083), px=dict(px=23.216, py=23.198, ox=19.04, oy=9.94, W=22, H=29), mode=True, post=lg), 'resto'),
 ('Frieren, Fern e Stark (cabeças empilhadas, gráfico)', 'Frieren', 111, G(111, crop_img=(0, 60, 1179, 1230), px=dict(px=21.375, py=21.398, ox=11.66, oy=11.3, W=55, H=54), mode=True, ref=(205, 204, 210), tol=14, bgs=[((133, 141, 218), 30)], allbg=True, post=lg), 'resto'),
 ('Gato branco dentro de um baú (gráfico, Mard 1023)', 'Genéricos', 71, G(71, px=dict(px=31.404, py=31.4, ox=23.21, oy=47.55, W=36, H=36), mode=True, ref=(200, 225, 245), tol=30, bgs=[((242, 240, 241), 24), ((255, 255, 255), 24)], post=lg), 'resto'),
 ('Criatura branca de contorno preto (gráfico, Mard-120)', 'Genéricos', 134, TG(134, dict(px=34.299, py=34.308, ox=141.83, oy=146.97, W=26, H=33), 'A13:1 E11:11 F10:6 G3:6 G5:1 G9:31 H2:295 H7:122', 'Criatura branca'), 'resto'),
 ('Harry Potter (chibi, pixel, folha)', 'Harry Potter', 104, G(104, crop_img=(30, 90, 235, 345), px=dict(px=13.428, py=13.402, ox=8.11, oy=3.17, W=15, H=19), mode=True, thr=225, post=lg), 'resto'),
 ('Rony Weasley (chibi, pixel)', 'Harry Potter', 104, G(104, crop_img=(275, 90, 460, 345), px=dict(px=13.716, py=13.837, ox=9.76, oy=8.12, W=13, H=18), mode=True, thr=225, post=lg), 'resto'),
 ('Hermione Granger (chibi, pixel, folha)', 'Harry Potter', 104, G(104, crop_img=(495, 95, 720, 335), px=dict(px=13.379, py=13.408, ox=10.76, oy=12.58, W=16, H=17), mode=True, thr=225, post=lg), 'resto'),
 ('Hagrid (chibi, pixel, folha)', 'Harry Potter', 104, G(104, crop_img=(25, 415, 255, 655), px=dict(px=12.99, py=13.002, ox=9.61, oy=7.5, W=17, H=18), mode=True, thr=225, post=lg), 'resto'),
 ('Professora McGonagall (chibi, pixel)', 'Harry Potter', 104, G(104, crop_img=(280, 395, 495, 655), px=dict(px=11.499, py=11.502, ox=7.15, oy=7.86, W=18, H=22), mode=True, thr=225, post=lg), 'resto'),
 ('Dumbledore (chibi, pixel, folha)', 'Harry Potter', 104, G(104, crop_img=(525, 415, 730, 655), px=dict(px=11.465, py=11.499, ox=9.79, oy=10.18, W=17, H=20), mode=True, thr=225, post=lg, post2=R.fill_between), 'resto'),
 ('Draco Malfoy (chibi, pixel)', 'Harry Potter', 104, G(104, crop_img=(50, 730, 240, 970), px=dict(px=13.386, py=13.397, ox=0.34, oy=6.56, W=14, H=17), mode=True, thr=225, post=lg), 'resto'),
 ('Severo Snape (chibi, pixel, folha)', 'Harry Potter', 104, G(104, crop_img=(290, 730, 490, 970), px=dict(px=13.001, py=12.999, ox=8.05, oy=12.44, W=15, H=18), mode=True, thr=225, post=lg), 'resto'),
 ('Chibi de pele azul-esverdeada e capa verde (Harry Potter, pixel)', 'Harry Potter', 104, G(104, crop_img=(525, 740, 710, 970), px=dict(px=13.714, py=12.822, ox=13.58, oy=12.75, W=12, H=17), mode=True, thr=225, post=lg), 'resto'),
 ('Alienígena verde de antenas (pixel)', 'Genéricos', 101, ALIEN(0, clear=(18, 23, 13, 21)), 'resto'),
 ('Alienígena amarelo de um olho só (pixel)', 'Genéricos', 101, ALIEN(1), 'resto'),
 ('Alienígena laranja de três olhos (pixel)', 'Genéricos', 101, ALIEN(2), 'resto'),
 ('Alienígena vermelho de antenas (pixel)', 'Genéricos', 101, ALIEN(3), 'resto'),
 ('Alienígena verde-água de cauda comprida (pixel)', 'Genéricos', 101, ALIEN(4), 'resto'),
 ('Serpente alienígena azul (pixel)', 'Genéricos', 101, ALIEN(5), 'resto'),
 ('Alienígena roxo de olhos grandes (pixel)', 'Genéricos', 101, ALIEN(6), 'resto'),
 ('Alienígena rosa de braços finos (pixel)', 'Genéricos', 101, ALIEN(7), 'resto'),
 ('Chibi de cabelo vermelho e uniforme escuro (gráfico)', 'Genéricos', 70, PG(70, dict(px=14.719, py=14.713, ox=13.88, oy=13.51, W=48, H=48), 'C12:6 D10:2 F6:2 F8:16 F9:6 F10:6 F11:27 F12:3 F14:4 F15:115 F16:43 F25:12 G3:2 G8:76 G14:22 G17:7 H2:1867 H3:14 H5:7 H6:28 H7:29 H11:2 H19:4 M7:2 M15:2', 'Chibi de cabelo vermelho', fix={(15, 21): 'F12', (15, 23): 'F12', (15, 25): 'F12', (36, 21): 'H19', (37, 21): 'H19'}), 'resto'),
]


def run(args, grupo, out_name='final30'):
    one = []; sheet = []
    for n, g, idx, fn, grp in CFG:
        if grupo and grp != grupo: continue
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = False
            r = fn(); one.append((n, g, r)); sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    return one, sheet


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--H' in sys.argv: args.remove(sys.argv[sys.argv.index('--H') + 1])
    grupo = None
    if '--grupo' in sys.argv:
        grupo = sys.argv[sys.argv.index('--grupo') + 1]; args = [a for a in args if a != grupo]
    one, sheet = run(args, grupo)
    print(len(one), 'moldes de 1 placa')
    tag = (grupo or 'all') + ('_f' if args else '')
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r28_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r28_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and ('--merge' in sys.argv or (not args and not grupo)):
        pth = os.path.join(HERE, 'data', 'final30' + sfx() + '.json')
        old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) and (args or grupo) else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok')
