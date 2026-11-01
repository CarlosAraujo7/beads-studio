"""Remessa 24 (79 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r24_exfinal.py [filtro...] [--grupo graf|ill|foto] [--merge] [--H 520]
   -> data/final26_120.json (1 placa) + data/final26_multi_120.json (só o pôster de Attack on Titan, em 4 placas).
Pedido do usuário (2026-10-31): o arquivo 4ddc40174219462c5cb2e950408c4b34 (idx 25) sai SÓ em 4 placas; todo o resto em 1 placa, sem irmão grande (o que passa de 50 é reduzido com shrink 'bias').
Rostos em 1 placa (CLAUDE.md §4.8): olhos discretos e sem boca desenhada, salvo traço simples. Gráficos de pixel continuam cópia exata (o que passa de 50 é reduzido). Reaproveita os auxiliares do r22_exfinal.py."""
import os, sys, json
os.environ['REMNUM'] = '24'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np
import cv2
import r5, r6, outline as O, illus, shrink, loose
import r22_exfinal as R
import weak_cm as WC
import r23_exfinal as R23
import palette as P
from palette import sfx
from PIL import Image
E = r6.exact6
lg = R.lg
F = r6.FILES
CH, WH, ST, NONE = R23.CH, R.WH, R.ST, R.NONE
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
    """tira k COLUNAS: as que menos diferem da vizinha (nunca duas seguidas). Mantém as contas nítidas: o shrink por janela, numa redução pequena (54 -> 50), mistura cores e borra."""
    W = len(rows[0]); cols = [''.join(r[x] for r in rows) for x in range(W)]
    cost = [(sum(a != b for a, b in zip(cols[x], cols[x + 1])), x) for x in range(W - 1)]
    out = set()
    for _, x in sorted(cost):
        if len(out) == k: break
        if x - 1 in out or x + 1 in out or x in out: continue
        out.add(x)
    return [''.join(c for x, c in enumerate(r) if x not in out) for r in rows]


def fit50(rows):
    """redução até 1,3x: tira linhas e colunas inteiras; acima disso, shrink 'bias' (a janela é inevitável)"""
    h, w = len(rows), len(rows[0]); big = max(h, w)
    if big <= 50: return rows
    if big / 50.0 > 1.3: return shrink.shrink(rows, 50, 'bias', empty_at=0.6)
    nw, nh = shrink.target_size(w, h, 50)
    rows = _drop_lines(rows, w - nw)
    tr = [''.join(c) for c in zip(*rows)]
    tr = _drop_lines(tr, h - nh)
    return [''.join(c) for c in zip(*tr)]


def fin(rows):
    """fecha o molde: sem contas soltas, reduzido a 1 placa e sem bordas vazias"""
    rows = fit50(rows)
    if loose.loose_count(rows): rows = loose.fix_loose(rows)
    return O.trim(rows)


def bg_at(i, fx, fy):
    im = np.array(Image.open(F[i]).convert('RGB')); h, w = im.shape[:2]
    y, x = int(fy * h), int(fx * w)
    return tuple(int(v) for v in np.median(im[max(0, y - 6):y + 6, max(0, x - 6):x + 6].reshape(-1, 3), axis=0))


def G(i, **kw):
    post = kw.pop('post2', None)
    def f():
        r = E(i, **kw)
        if post: r = post(r)
        return fin(r)
    return f


def ball(k):
    def f():
        return fin(R.cached('c72', lambda: sorted(R.comps(E(72), 7), key=lambda r: 0))[k])
    return f


def _balls():
    """as 7 esferas, na ordem de leitura da folha (2 por linha)"""
    rows = E(72)
    m = np.array([[c != '.' for c in r] for r in rows], np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = sorted(range(1, n), key=lambda i: -st[i][4])[:7]
    H = len(rows)
    big.sort(key=lambda i: (round(cen[i][1] / (H / 4.0)), cen[i][0]))
    return [O.trim([''.join(c if lab[y, x] == i else '.' for x, c in enumerate(r)) for y, r in enumerate(rows)]) for i in big]


CFG = [
 ('Sukuna (Jujutsu Kaisen, pixel, corpo inteiro)', 'Jujutsu Kaisen', 0, G(0, post=lg)),
 ('Thor (pixel)', 'Marvel', 1, G(1, post=lg)),
 ('Visão (pixel, voando)', 'Marvel', 2, G(2, post=lg)),
 ('Sub-Zero (Mortal Kombat, pixel)', 'Mortal Kombat', 4, G(4, crop=(2, 46, 2, 30), clear=[(0, 4, 0, 4)], ref=(198, 254, 102), tol=45, allbg=True, colmap=[((42, 66, 246), 45, L['D3']), ((114, 174, 250), 45, 'b')], post=pieces(30))),
 ('Astronauta com foguete e estrela (pixel)', 'Outros', 5, G(5)),
 ('Ban (Nanatsu no Taizai, pixel)', 'Nanatsu no Taizai', 6, G(6, post=lg)),
 ('Meliodas (Nanatsu no Taizai, pixel)', 'Nanatsu no Taizai', 8, G(8, post=lg)),
 ('Carro de corrida vermelho (pixel)', 'Outros', 9, G(9)),
 ('Hulkbuster (Marvel, gráfico)', 'Marvel', 10, G(10, post=lg)),
 ('Carnificina (Marvel, gráfico)', 'Marvel', 11, G(11)),
 ('Goku Super Saiyajin Blue (aura, pixel)', 'Dragon Ball', 12, G(12, post=lg)),
 ('Lanterna Verde (pixel, corpo inteiro)', 'DC Comics', 14, G(14, post=lg, post2=lambda r: holes(r, 4, keep=[(12, 24, 8, 22)]))),
 ('Mera Mera no Mi (One Piece, pixel)', 'One Piece', 15, G(15, post=lg)),
 ('Shenlong (Dragon Ball, chibi, pixel)', 'Dragon Ball', 16, G(16, post=lg, post2=lambda r: holes(r, 4))),
 ('Goku Instinto Superior (pixel, corpo inteiro)', 'Dragon Ball', 17, G(17, post=lg, post2=lambda r: holes(r, 4, keep=[(0, 24, 0, 99)]))),
 ('Doutor Destino (Marvel, gráfico)', 'Marvel', 18, G(18, colmap=[((18, 92, 6), 26, L['B8']), ((6, 150, 6), 34, L['B4'])], post=lg)),
 ('Red (Pokémon, treinador, pixel)', 'Pokémon', 20, G(20, post=lg)),
 ('Going Merry (One Piece, gráfico)', 'One Piece', 21, G(21, thr=185, post=lg)),
 ('Porta aberta com olhos (pixel)', 'Outros', 22, G(22)),
 ('Dragão vermelho voando (pixel)', 'Outros', 24, G(24)),
 ('Motoqueiro Fantasma (Marvel, gráfico)', 'Marvel', 28, G(28, crop=(1, 27, 1, 23), thr=225, post=lg)),
 ('Mago de chapéu roxo (pixel)', 'Outros', 29, G(29, colmap=[((78, 54, 180), 46, 'u')])),
 ('Power Ranger verde (pixel, corpo inteiro)', 'Power Rangers', 30, G(30, crop=(2, 46, 2, 30), ref=(66, 174, 114), tol=30, colmap=[((222, 222, 30), 45, 'y')], post=lg)),
 ('Zoom (DC, pixel)', 'DC Comics', 33, G(33)),
 ('Meliodas com espada (Nanatsu no Taizai, pixel)', 'Nanatsu no Taizai', 34, G(34, post=lg)),
 ('Titã Bestial (Attack on Titan, pixel)', 'Attack on Titan', 35, G(35, colmap=[((78, 42, 18), 34, L['F10']), ((42, 18, 6), 18, L['F11'])], post=lg)),
 ('Cetro da Sailor Moon (pixel)', 'Sailor Moon', 37, G(37)),
 ('Wolverine (Marvel, gráfico)', 'Marvel', 38, G(38, post=lg)),
 ('Power Ranger azul (pixel, corpo inteiro)', 'Power Rangers', 39, G(39, crop=(2, 46, 2, 30), ref=(66, 78, 246), tol=30, colmap=[((66, 78, 246), 50, L['D3']), ((30, 54, 210), 30, L['D3'])], post=lg)),
 ('Shenlong (cabeça, gráfico)', 'Dragon Ball', 41, G(41, post=lg)),
 ('Omni-Man (Invencível, pixel)', 'Invencível', 44, G(44, ref=bg_at(44, 0.05, 0.05), tol=40, post=lg)),
 ('Hulk (Marvel, pixel, corpo inteiro)', 'Marvel', 45, G(45, clear=[(33, 35, 21, 32)], post=lg)),
 ('Spawn (gráfico)', 'Spawn', 46, G(46, post=lg)),
 ('Game Boy fofo (pixel)', 'Outros', 47, G(47)),
 ('Batman (pixel, capa)', 'DC Comics', 48, G(48, achro=190, post=lg)),
 ('Dragão vermelho com orbe azul (pixel)', 'Outros', 51, G(51, post=lg)),
 ('Homem-Aranha de Ferro (gráfico)', 'Marvel', 52, G(52, post=lg)),
 ('Whis (Dragon Ball, pixel)', 'Dragon Ball', 53, G(53, post=lg)),
 ('Insectoide (Ben 10, pixel)', 'Ben 10', 54, G(54, post=lg, post2=lambda r: holes(r, 4, keep=[(0, 99, 22, 42)]))),
 ('Spawn (pixel)', 'Spawn', 55, G(55, post=lg)),
 ('Detetive de lupa (pixel)', 'Outros', 56, G(56, post=lg, post2=lambda r: holes(r, 5, keep=[(0, 40, 0, 12)]))),
 ('Shovel Knight (gráfico)', 'Shovel Knight', 57, G(57)),
 ('Pipoca de óculos 3D (pixel)', 'Outros', 58, G(58)),
 ('Soldada da Tropa de Exploração (Attack on Titan, pixel)', 'Attack on Titan', 59, G(59, ref=(30, 174, 78), tol=62, colmap=[((60, 32, 26), 28, L['F10'])], post=lg)),
 ('Robô fofo azul (pixel)', 'Outros', 60, G(60)),
 ('Power Ranger rosa (pixel, corpo inteiro)', 'Power Rangers', 63, G(63, crop=(2, 46, 2, 30), clear=[(0, 4, 0, 4)], ref=(102, 254, 114), tol=45, allbg=True, post=pieces(30), colmap=[((246, 90, 150), 45, L['E6']), ((222, 54, 120), 34, L['E5'])])),
 ('Hulkbuster (Marvel, pixel, ação)', 'Marvel', 65, G(65, post=lg, post2=lambda r: holes(r, 6))),
 ('Flash Reverso (DC, pixel)', 'DC Comics', 66, G(66, post=lg)),
 ('Titã Colossal (Attack on Titan, pixel)', 'Attack on Titan', 68, G(68, post=lg)),
 ('Dante (Devil May Cry, pixel)', 'Devil May Cry', 70, G(70, post=lg)),
 ('Quatro Braços (Ben 10, pixel)', 'Ben 10', 71, G(71, post=lg, post2=lambda r: holes(r, 2, keep=[(10, 34, 15, 48)]))),
 ('Steve (Minecraft, gráfico)', 'Minecraft', 73, G(73, clear=[(0, 0, 0, 29)], post=lg)),
 ('Aquático (Ben 10, pixel)', 'Ben 10', 74, G(74, post=lg)),
 ('Hidan (Naruto, pixel)', 'Naruto', 75, G(75, post=lg)),
 ('Demônio vermelho de chifres (pixel)', 'Outros', 78, G(78, post=lg)),
 ('Thousand Sunny (One Piece, gráfico)', 'One Piece', 61, G(61, px=dict(px=18.79, py=18.78, ox=30.0, oy=62.5, W=36, H=37), mode=True, ref=(190, 234, 246), tol=26, allbg=True, clear=[(3, 7, 25, 35)], post=lg)),
 ('Coraline (contas redondas)', 'Coraline', 50, G(50, px=23.2, mode=True, thr=205, post=lg)),
]
CFG = [c + ('graf',) for c in CFG]
for _k in range(7):
    CFG.append((f'Esfera do Dragão de {_k + 1} estrela{"s" if _k else ""} (pixel)', 'Dragon Ball', 72, (lambda k=_k: fin(R.cached('c72b', _balls)[k])), 'graf'))

ILL = [
 ('Jack Sparrow (Piratas do Caribe, chibi, adesivo)', 'Piratas do Caribe', 3, dict(CH, thr=178, K=36, dark_frac=0.3, black_L=10.0, pale_skin=False, warm_white=0, smooth_de=12.0)),
 ('John Wick com cachorro (chibi)', 'John Wick', 7, dict(CH, dark_frac=0.42)),
 ('Pennywise de capa amarela (chibi)', 'It: A Coisa', 13, dict(CH, bg='flat', tol=30, dark_frac=0.36, smooth_de=14.0)),
 ('Jon Snow (Game of Thrones, retrato)', 'Game of Thrones', 19, dict(CH, thr=205, peel=1.5, dark_frac=0.42)),
 ('Kon (Bleach, corpo inteiro)', 'Bleach', 23, dict(CH, pale_skin=False, warm_white=0)),
 ('Cavaleiro da Lua de terno (Marvel, chibi)', 'Marvel', 26, dict(CH, bg='flat', tol=28, pale_skin=False, warm_white=0)),
 ('Chucky (chibi)', 'Brinquedo Assassino', 27, dict(CH, dark_frac=0.42)),
 ('Hannibal Lecter (chibi)', 'O Silêncio dos Inocentes', 32, dict(CH, dark_frac=0.36, center_map=None)),
 ('Cavaleiro da Lua (Marvel, chibi)', 'Marvel', 36, dict(CH, bg='flat', tol=28, pale_skin=False, warm_white=0)),
 ('Red Hood (DC, chibi)', 'DC Comics', 40, dict(CH, dark_frac=0.45, black_L=8.0)),
 ('Titã Colossal e Eren (Attack on Titan, chibi)', 'Attack on Titan', 42, dict(CH, **NONE, K=36, dark_frac=0.2, black_L=14.0, pale_skin=False, warm_white=0, center_map=None)),
 ('Freddie Mercury (Queen, chibi)', 'Queen', 43, dict(CH, dark_frac=0.36, center_map=WC.CM_NEUT)),
 ('Xenomorfo (Alien, chibi)', 'Alien', 49, dict(CH, pale_skin=False, warm_white=0, dark_frac=0.5, black_L=7.0, K=30)),
 ('Pennywise (chibi, corpo inteiro)', 'It: A Coisa', 62, dict(CH, dark_frac=0.45, pale_skin=False, warm_white=0, center_map=WC.CM_NEUT)),
 ('Hellboy (chibi)', 'Hellboy', 64, dict(CH, pale_skin=False, warm_white=0, dark_frac=0.42)),
 ('Cavaleiro da Lua azul (Marvel, chibi)', 'Marvel', 67, dict(CH, pale_skin=False, warm_white=0, smooth_de=14.0, dark_frac=0.36)),
 ('Doutor Estranho (Marvel, chibi, adesivo)', 'Marvel', 69, dict(CH, thr=205, peel=2.0, dark_frac=0.4)),
 ('John Wick e cachorro (chibi, adesivo)', 'John Wick', 76, dict(CH, thr=190, post=pieces(30))),
 ('John Wick (retrato, adesivo)', 'John Wick', 77, dict(CH, thr=190)),
]

def foto31():
    import photo7 as P7
    import colorsys
    def bg(c):
        h, sat, v = colorsys.rgb_to_hsv(*(np.array(c, float) / 255.0))
        return v > 0.32 and sat < 0.38                                      # pedra cinza-bege; conta preta é escura, chama é saturada
    pal = [((30, 28, 30), 'k'), ((70, 68, 74), L['H6']), ((225, 222, 228), L['H1']), ((150, 150, 158), L['H3']), ((241, 195, 70), 'y'), ((240, 135, 50), 'o'), ((222, 45, 35), L['F4'])]
    r = P7.convert(24, 31, 11.5, 0.1, (90, 10, 620, 620), bg=bg, pal=pal, minsize=8)
    return fin(lg(r))


NOSKIN = ('Kon', 'Cavaleiro da Lua', 'Xenomorfo', 'Hellboy', 'Pennywise de capa')
for _n, _g, _i, _kw in ILL:
    CFG.append((_n, _g, _i, (lambda i=_i, kw=_kw, sk=not any(k in _n for k in NOSKIN): fin(R.ill(i, kw, skin=sk))), 'ill'))

CFG.append(('Motoqueiro Fantasma (foto de peça pronta)', 'Marvel', 31, foto31, 'foto'))

TOUCH = {
 'Kon (Bleach, corpo inteiro)': [(7, 11, ['k', 'k']), (7, 18, ['k', 'k'])],
 'Pennywise (chibi, corpo inteiro)': [(19, 8, ['wwwwww     wwwww', 'wwwwww     wwwww', 'wwwwww     wwwww', 'wwwwww     wwwww', ]),
                                      (19, 8, ['kkkk', 'ykky', 'wyyw']), (19, 18, ['kkkk', 'ykky', 'wyyw']), (16, 19, ['r', 'r', 'r']), (25, 16, ['w'])],
 'Hellboy (chibi)': [(20, 12, ['rrrrrr', 'rrrrrr', 'rrrrrr', 'rrrrrr', 'rrrrrr']), (20, 27, ['rrrrrr', 'rrrrrr', 'rrrrrr', 'rrrrrr', 'rrrrrr']),
                     (20, 13, ['ykky', 'ykky', 'kyyk']), (20, 28, ['ykky', 'ykky', 'kyyk'])],
 'Hulk (Marvel, pixel, corpo inteiro)': [(32, 21, ['kLLLLVVk..', 'kLLLLLVVk', 'kLLkLkLVk', 'kkkkkkkkk'])],
}


def touched(n, r):
    if n not in TOUCH: return r
    g = [list(x) for x in r]
    for y0, x0, lines in TOUCH[n]:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c != ' ': g[y0 + j][x0 + i] = c
    r = [''.join(x) for x in g]
    return loose.fix_loose(r) if loose.loose_count(r) else r


POSTER = ('Attack on Titan (pôster)', 'Attack on Titan', 25)
POSTER_KW = dict(K=56, bg='flat', tol=34, seal=0.0, pale_skin=False, warm_white=0, sat=1.3, smooth_de=8.0, rare_n=6)
POSTER_BIG = dict(dark_frac=0.3, black_L=10.0)


def poster():
    return R.ill(25, dict(POSTER_KW, bigkw=POSTER_BIG, noclean=True), plates=4, skin=False)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--H' in sys.argv: args.remove(sys.argv[sys.argv.index('--H') + 1])
    grupo = None
    if '--grupo' in sys.argv:
        grupo = sys.argv[sys.argv.index('--grupo') + 1]; args = [a for a in args if a != grupo]
    one = []; multi = []; sheet = []
    for n, g, idx, fn, grp in CFG:
        if grupo and grp != grupo: continue
        if args and not any(a.lower() in n.lower() for a in args): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = touched(n, fn()); one.append((n, g, r)); sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    if (not grupo or grupo == 'poster') and (not args or any(a.lower() in POSTER[0].lower() for a in args)):
        r = poster(); multi.append((POSTER[0], POSTER[1], r, {'plates': R.plates_of(r)})); sheet.append((f'25: {POSTER[0]} {len(r[0])}x{len(r)}', R.source_img(25), r))
    print(len(one), 'moldes de 1 placa,', len(multi), 'de 4 placas')
    tag = (grupo or 'all') + ('_f' if args else '')
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r24_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r24_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    for fname, new_ in (('final26', one), ('final26_multi', multi)):
        if not new_ or not ('--merge' in sys.argv or (not args and not grupo)): continue
        pth = os.path.join(SP, 'data', fname + sfx() + '.json')
        old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) and (args or grupo) else []
        by = {x[0]: list(x) for x in new_}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok')
