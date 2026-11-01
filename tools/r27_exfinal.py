"""Remessa 27 (31 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r27_exfinal.py [filtro...] [--grupo graf|foto] [--merge] [--H 520]
   -> data/final29_120.json (tudo em 1 placa). Reaproveita os auxiliares do r26_exfinal.py: o import aponta para a remessa 26 e a lista de arquivos é trocada aqui.
Gráficos = cópia exata; fotos de peça pronta = photo7 com a grade das contas (aproximado, CLAUDE.md §7.4b): keep/bg por foto. Rostos: olhos discretos, sem boca (§4.8)."""
import os, sys, json, glob, colorsys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r26_exfinal as X
from r26_exfinal import r5, r6, O, np, R, G, E, F, L, LAB, OUT, fin, lg, holes, pieces, pale, peel_set, clearb, chain, comp, vote, sfx, C5
import photo7 as P7
import cv2
from PIL import Image
F[:] = sorted(glob.glob(os.path.join(os.path.dirname(HERE), 'remessas', 'remessa 27', '*.*')))          # F é a mesma lista de r6.FILES e R.F


def hsv(c):
    return colorsys.rgb_to_hsv(*(np.array(c, float) / 255.0))


def foto(idx, p0, bbox, keep=None, bg=None, pal=None, spread=0.08, minsize=3, post=None, flood=True):
    def f():
        r = P7.convert(27, idx, p0, spread, bbox, bg=bg, keep=keep, pal=pal, minsize=minsize, flood=flood)
        if post: r = post(r)
        return fin(r)
    return f


def sat(lim, dark=0.3):
    """lista branca: cor viva ou conta bem escura"""
    def k(c):
        h, s, v = hsv(c)
        return s > lim or v < dark
    return k


def satw(lim, dark, white):
    """como sat, e também conta bem clara (a placa/parede fica abaixo de white)"""
    def k(c):
        h, s, v = hsv(c)
        return s > lim or v < dark or c.min() > white
    return k


def ring_read(i, grid, bg, pal=None):
    """render de contas com furo: a cor sai do ANEL de cada conta (o miolo é o fundo ou a sombra e deixava o molde lavado ou escuro). bg(rgb) = é fundo; inunda a partir da borda"""
    def f():
        im = np.array(R.source_img(i)).astype(float); px, py, ox, oy, W, H = grid['px'], grid['py'], grid['ox'], grid['oy'], grid['W'], grid['H']
        yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]; arr = np.zeros((H, W, 3))
        for y in range(H):
            for x in range(W):
                cx, cy = ox + (x + .5) * px, oy + (y + .5) * py
                y0, y1, x0, x1 = max(0, int(cy - px)), int(cy + px), max(0, int(cx - px)), int(cx + px)
                d = np.hypot(xx[y0:y1, x0:x1] - cx, yy[y0:y1, x0:x1] - cy) / px
                sel = (d > .24) & (d < .38)
                arr[y, x] = np.median(im[y0:y1, x0:x1][sel], axis=0) if sel.any() else 255
        isbg = np.array([[bg(arr[y, x]) for x in range(W)] for y in range(H)])
        out = r6.flood_fn(arr, lambda pq, q: isbg[q])
        r = P7.letters(arr, out, pal)
        return fin(lg(O.trim(r)))
    return f


def hue_keep(a, b, smin):
    def k(c):
        h, s, v = hsv(c)
        return a <= h * 360 <= b and s > smin
    return k


def keep_or(*fs):
    return lambda c: any(f(c) for f in fs)


def qilin():
    """fundo creme com grade: fecha a grade e inunda só o de fora; depois convert5 com fundo branco (a nuvem branca fica, porque o contorno preto a protege)"""
    im = np.array(R.source_img(30)); d = np.abs(im.astype(int) - np.array([240, 237, 225])).max(axis=2)
    m = cv2.morphologyEx((d < 20).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab = cv2.connectedComponents(m, connectivity=4); keep = {lab[0, 0], lab[0, -1], lab[-1, 0], lab[-1, -1]} - {0}
    out = im.copy(); out[np.isin(lab, list(keep))] = 255
    tmp = os.path.join(OUT, '_r27_30.png'); Image.fromarray(out).save(tmp)
    old = F[30]; F[30] = tmp
    try: r = R.ill(30, dict(C5, K=40, dark_frac=0.3, black_L=14.0, thr=252), skin=False)
    finally: F[30] = old
    return fin(lg(r))


def lab_of(c):
    return cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float)


def eevee(box, pal):
    """foto das 9 evoluções (5,6 px por conta): a pedra do fundo não tem cor própria; GrabCut separa a figura e cada conta pega a cor mais próxima da paleta DA FIGURA"""
    def f():
        im = np.array(R.source_img(24)); x0, y0, x1, y1 = box; m = 9
        X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), min(im.shape[1], x1 + m), min(im.shape[0], y1 + m)
        rgb = im[Y0:Y1, X0:X1].copy(); bgr = rgb[:, :, ::-1].copy()
        mk = np.zeros(bgr.shape[:2], np.uint8); bgd = np.zeros((1, 65)); fgd = np.zeros((1, 65))
        cv2.grabCut(bgr, mk, (m - 3, m - 3, bgr.shape[1] - 2 * m + 6, bgr.shape[0] - 2 * m + 6), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
        fg = ((mk == 1) | (mk == 3)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
        fg = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.float32)
        W, H = int(round(rgb.shape[1] / 5.6)), int(round(rgb.shape[0] / 5.6))
        sm = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_AREA); fm = cv2.resize(fg, (W, H), interpolation=cv2.INTER_AREA)
        cen = [(lab_of(c), l) for c, l in pal]
        rows = []
        for y in range(H):
            rows.append(''.join('.' if fm[y, x] < 0.45 else min(cen, key=lambda q: float(np.linalg.norm(q[0] - lab_of(sm[y, x]))))[1] for x in range(W)))
        return fin(lg(O.trim(rows)))
    return f


G1 = dict(px=28.24, py=28.24, ox=15.94, oy=8.98, W=25, H=24)
G7 = dict(px=29.28, py=29.30, ox=3.06, oy=3.70, W=25, H=25)
G8 = dict(px=36.32, py=36.46, ox=1.50, oy=19.12, W=28, H=28)
HOT = L['E10']
CFG = [
 ('Pato-real (gráfico)', 'Animais', 1, ring_read(1, G1, lambda c: c.min() > 250)),
 ('Baleia azul (gráfico)', 'Animais', 4, G(4, post=lg)),
 ('Ovelha com sino (gráfico)', 'Animais', 5, G(5, post=lg)),
 ('Sapo verde fofo (contas)', 'Animais', 7, ring_read(7, G7, lambda c: hsv(c)[1] < 0.2 and hsv(c)[2] > 0.6, pal=[((95, 205, 40), 'L'), ((60, 175, 60), 'f'), ((195, 230, 120), 'R'), ((30, 30, 30), 'k'), ((245, 245, 245), 'w'), ((245, 150, 180), 'p')])),
 ('Coruja marrom (contas)', 'Animais', 8, ring_read(8, G8, lambda c: c.min() > 245, pal=[((140, 90, 55), 'n'), ((90, 55, 40), 'Ç'), ((235, 220, 190), 'Ú'), ((30, 30, 32), 'k'), ((85, 90, 100), 'd'), ((250, 215, 40), 'y'), ((205, 165, 120), 'Ô')])),
 ('Esquilo (gráfico)', 'Animais', 9, G(9, crop=(1, 21, 1, 21), post=lg)),
 ('Yoshi (gráfico, fundo verde-escuro)', 'Mario', 10, G(10, post=lg)),
 ('Patinho de borracha (contorno preto)', 'Animais', 13, G(13, post=lg)),
 ('Raposa laranja (gráfico)', 'Animais', 15, G(15, post=lg)),
 ('Patinho amarelo (gráfico)', 'Animais', 16, G(16, post=lg)),
 ('Gatinho de contorno rosa e azul (gráfico)', 'Genéricos', 17, G(17, post=lg)),
 ('Laço rosa (gráfico)', 'Genéricos', 18, G(18, colmap=[((240, 113, 184), 40, HOT)], post=lg)),
 ('Cinnamoroll (Sanrio, gráfico)', 'Hello Kitty', 21, G(21, post=lg)),
 ('Coelhinho branco (gráfico)', 'Animais', 22, G(22, ref=(154, 216, 233), tol=26, allbg=True, bgs=[((254, 254, 254), 8)], post=lg)),
 ('Rosquinha (gráfico)', 'Genéricos', 26, G(26, post=lg)),
 ('Border collie (gráfico)', 'Animais', 27, G(27, crop=(1, 27, 1, 27), ref=(210, 232, 186), tol=20, allbg=True, post=lg)),
 ('Flamingo (gráfico)', 'Animais', 28, G(28, post=lg)),
 ('Unicórnio (contas)', 'Genéricos', 29, G(29, post=lg)),
 ('Cachorrinho branco de lenço rosa (gráfico)', 'Animais', 25, G(25, crop_img=(0, 380, 1152, 1780), px=43.7, mode=True, thr=236, post=lg)),
 ('Qilin verde e dourado (contas)', 'Genéricos', 30, qilin),
]
CFG = [c + ('graf',) for c in CFG]
for _k, _n in enumerate(['Diddy Kong (gráfico)', 'Donkey Kong (gráfico)']):
    CFG.append((_n, 'Donkey Kong', 14, comp(14, {}, _k, 2, 18.0), 'graf'))
_w, _k = 'w', 'k'
FOTOS = [
 ('Sonic (foto de peça pronta)', 'Sonic', 6, foto(6, 36.0, (130, 830, 930, 1530), keep=lambda c: hsv(c)[1] > 0.28 or hsv(c)[2] < 0.25 or c.min() > 232,
    pal=[((25, 80, 190), 'b'), ((245, 245, 245), 'w'), ((30, 30, 30), 'k'), ((80, 170, 60), 'L'), ((215, 165, 120), 'Ñ'), ((235, 190, 50), 'y')])),
 ('Coruja azul (foto de peça pronta)', 'Animais', 19, foto(19, 23.6, (100, 230, 650, 800), keep=satw(0.22, 0.28, 188),
    pal=[((135, 205, 230), '1'), ((25, 130, 190), 'c'), ((240, 240, 240), 'w'), ((30, 30, 30), 'k'), ((235, 200, 40), 'y')])),
 ('Periquito (foto de peça pronta)', 'Animais', 23, foto(23, 24.0, (100, 70, 700, 590), keep=sat(0.3, 0.2))),
]
CFG += [c + ('foto',) for c in FOTOS]
# 3 miniaturas da foto 0: 7 a 9 contas de lado, lidas à mão na foto ampliada
BOB = ['.yyyyy.', '.ykyky.', '.yyyyy.', 'yyyyyyy', '.wwrww.', '.nnnnn.', '..y.y..']
PATRICK = ['...t...', '..ttt..', '.ttttt.', '.tktkt.', 'ttttttt', '.ffxff.', '.xfffx.', '.tt.tt.']
LULA = ['.ggg.', 'ggggg', 'gkgkg', '.ggg.', '.ggg.', 'gÔÔÔg', '.ÔÔÔ.', '.g.g.', 'gg.gg']
PATO20 = ['...yyy..', '..yyyyy.', '..yykyÆ.', '..yyyÆÆÆ', 'y..yyy..', 'yyyyyyy.', 'yyyyyyy.', '.yyyyy..']
CFG += [('Patinho amarelo (foto de peça pronta)', 'Animais', 20, lambda: PATO20, 'foto'), ('Bob Esponja (foto de peça pronta)', 'Bob Esponja', 0, lambda: BOB, 'foto'), ('Patrick (foto de peça pronta)', 'Bob Esponja', 0, lambda: PATRICK, 'foto'), ('Lula Molusco (foto de peça pronta)', 'Bob Esponja', 0, lambda: LULA, 'foto')]
_EB = {'Umbreon': (60, 48, 203, 190), 'Espeon': (212, 52, 381, 192), 'Vaporeon': (385, 55, 532, 198), 'Flareon': (56, 217, 198, 360), 'Eevee': (216, 222, 350, 360), 'Leafeon': (377, 226, 519, 364), 'Glaceon': (47, 391, 185, 533), 'Jolteon': (225, 391, 350, 529), 'Sylveon': (382, 395, 555, 533)}
_EP = {
 'Umbreon': [((88, 82, 78), 'Ù'), ((35, 30, 30), 'k'), ((235, 205, 50), 'y'), ((170, 50, 50), 'r'), ((240, 240, 240), 'w'), ((225, 150, 130), 'Ñ')],
 'Espeon': [((200, 150, 215), '('), ((225, 185, 230), 'v'), ((115, 70, 165), '-'), ((70, 45, 90), '/'), ((205, 45, 60), 'r'), ((245, 245, 245), 'w'), ((245, 180, 195), 'q')],
 'Vaporeon': [((75, 190, 225), 'c'), ((35, 70, 175), '&'), ((245, 235, 235), 'w'), ((235, 205, 70), 'y'), ((30, 30, 40), 'k'), ((245, 180, 190), 'q'), ((140, 225, 235), '0')],
 'Flareon': [((215, 100, 75), 'Æ'), ((70, 45, 40), 'Ì'), ((240, 200, 50), 'y'), ((250, 225, 130), 'j'), ((245, 245, 245), 'w'), ((245, 175, 165), 'q')],
 'Eevee': [((190, 118, 62), 'Ò'), ((105, 65, 45), 'Õ'), ((245, 225, 180), 'Ú'), ((245, 245, 245), 'w'), ((35, 30, 30), 'k'), ((240, 170, 150), 'q')],
 'Leafeon': [((240, 215, 150), 'Ô'), ((70, 170, 80), 'f'), ((170, 225, 150), 'g'), ((120, 75, 45), 'Õ'), ((245, 245, 245), 'w'), ((40, 30, 30), 'k'), ((240, 170, 150), 'q')],
 'Glaceon': [((165, 215, 240), 'e'), ((80, 145, 215), 'b'), ((40, 85, 180), '&'), ((205, 240, 245), '7'), ((30, 30, 40), 'k'), ((245, 245, 245), 'w'), ((245, 175, 195), 'q')],
 'Jolteon': [((245, 215, 40), 'y'), ((250, 235, 170), 'j'), ((245, 245, 240), 'w'), ((105, 70, 150), '-'), ((35, 30, 40), 'k'), ((245, 175, 165), 'q')],
 'Sylveon': [((235, 75, 120), '|'), ((250, 225, 180), 'j'), ((250, 190, 215), 'q'), ((105, 70, 150), '-'), ((175, 130, 205), 'v'), ((170, 215, 240), 'e'), ((245, 245, 245), 'w')],
}
for _n, _b in _EB.items():
    CFG.append((f'{_n} (foto de peça pronta)', 'Pokémon', 24, eevee(_b, _EP[_n]), 'foto'))
def halo(letter, keep=()):
    """a mistura da borda da conta com a pedra vira a cor da pele ou do rosa: fora das regiões em keep, a conta dessa letra pega a cor mais comum das vizinhas"""
    def f(rows):
        H, W = len(rows), len(rows[0]); g = [list(r) for r in rows]
        for y in range(H):
            for x in range(W):
                if rows[y][x] != letter or any(a <= y <= b and c <= x <= d for a, b, c, d in keep): continue
                nb = [rows[v][u] for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)) if 0 <= v < H and 0 <= u < W and rows[v][u] not in ('.', letter)]
                g[y][x] = max(set(nb), key=nb.count) if nb else '.'
        return [''.join(r) for r in g]
    return f


def qilin_eye(r):
    sk = r[17][7]
    g = [list(l) for l in r]
    for y, x0, t in ((14, 9, 'kkkk'), (15, 9, sk + 'fwk'), (16, 9, sk + 'ffk'), (17, 9, sk * 4)):
        for i, c in enumerate(t): g[y][x0 + i] = c
    return [''.join(l) for l in g]


# antes dos retoques: limpeza por molde
POST = {'Umbreon (foto de peça pronta)': halo('Ñ'), 'Vaporeon (foto de peça pronta)': halo('q'), 'Flareon (foto de peça pronta)': halo('q'), 'Eevee (foto de peça pronta)': halo('q'),
        'Leafeon (foto de peça pronta)': halo('q'), 'Glaceon (foto de peça pronta)': halo('q', [(13, 13, 0, 24)]), 'Jolteon (foto de peça pronta)': halo('q'), 'Qilin verde e dourado (contas)': qilin_eye}
# olhos lidos na foto: 2×2 contas com 1 brilho, bochecha embaixo; sem boca (CLAUDE.md §4.8)
TOUCH = {
 'Cachorrinho branco de lenço rosa (gráfico)': [(6, 21, ['.']), (8, 6, ['`']), (9, 6, ['``']), (8, 14, ['`']), (9, 13, ['``'])],
 'Coruja azul (foto de peça pronta)': [(3, 0, ['..11wwww111wwww1....', '..1wwwww111wwwww1...', '..1wwwww111wwwww1...', '..1wkkkwyyywkkkw1...', '..1wwwwwyyywwwww1...', '..1wwwww1y1wwwww1...'])],
 'Sonic (foto de peça pronta)': [(1, 7, ['b']), (5, 13, ['w']), (6, 0, ['.bbbbbbbbbbbbwwwwLk..', 'bbbbbbbbbbbbwwLwwwwkk', '....bbbbbbbbkwwwwkÑÑÑ', '....bbbbbbbbbkÑwwÑÑÑ.', '....bbbbbbbbbbÑÑÑÑÑÑ.', '...bbbbbbbbbbkkÑÑkk..']),
                                 (13, 7, ['bb']), (13, 13, ['b']), (15, 6, ['b'])],
 'Periquito (foto de peça pronta)': [(5, 8, ['k']), (6, 8, ['Ò'])],
 'Umbreon (foto de peça pronta)': [(5, 10, ['y']), (8, 10, ['y']), (10, 5, ['ÙwkÙ']), (11, 5, ['ÙkrÙ']), (12, 5, ['ÑÑÙ']), (10, 13, ['wkÙ']), (11, 13, ['krÙ']), (12, 14, ['ÑÑ']), (13, 14, ['ÙÙ'])],
 'Espeon (foto de peça pronta)': [(10, 7, ['wk']), (11, 7, ['//']), (10, 14, ['wk']), (11, 14, ['//']), (6, 21, ['(']), (7, 19, ['((']), (9, 18, ['((']), (8, 23, ['(']), (9, 23, ['(']), (10, 22, ['(']),
                                  (10, 18, ['.']), (11, 18, ['.']), (12, 18, ['.']), (13, 17, ['..']), (14, 16, ['..']), (15, 16, ['.'])],
 'Vaporeon (foto de peça pronta)': [(11, 10, ['wk']), (12, 9, ['ckk']), (11, 17, ['wk']), (12, 17, ['kk']), (13, 9, ['qq']), (13, 18, ['qq'])],
 'Flareon (foto de peça pronta)': [(0, 0, ['ÆÆ....jyj........ÆÆ..', 'ÆÆÆ...jjj.......ÆÆÆ..', 'ÆÌÌÆ.jjjjy.....ÆÌÌÆ..', 'ÆÌÌÌÆyjjjjyÆ..ÆÌÌÌÆ..', '.ÆÌÌÌÆyyyyyÆÆÆÆÌÌÌÆ..', '.ÆÆÌÌÆÆyyyÆÆÆÆÌÌÆÆ...', '..ÆÆÆÆÆÆÆÆÆÆÆÆÆÆÆ....']),
                                   (9, 3, ['ÆwkÆ']), (10, 3, ['ÆkkÆ']), (9, 10, ['ÆwkÆ']), (10, 10, ['ÆkkÆ']), (11, 3, ['qq']), (11, 12, ['qq'])],
 'Eevee (foto de peça pronta)': [(11, 8, ['wk']), (12, 8, ['kk']), (11, 15, ['wk']), (12, 15, ['kk']), (13, 7, ['qq']), (13, 16, ['qq'])],
 'Leafeon (foto de peça pronta)': [(11, 10, ['wk']), (12, 9, ['Ôkk']), (11, 17, ['wk']), (12, 17, ['kk']), (13, 9, ['qq']), (13, 18, ['qq'])],
 'Glaceon (foto de peça pronta)': [(11, 9, ['wk']), (12, 8, ['ekk']), (11, 16, ['wke']), (12, 15, ['ekke']), (10, 2, ['&']), (11, 2, ['&']), (12, 3, ['&']), (16, 18, ['&'])],
 'Jolteon (foto de peça pronta)': [(11, 7, ['yy']), (11, 15, ['y']), (12, 7, ['wk']), (13, 6, ['ykk']), (12, 14, ['wk']), (13, 14, ['kky']), (14, 6, ['qq']), (14, 15, ['qq'])],
}


def touched(n, r):
    if n in POST: r = POST[n](r)
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
            r5.SKIN_ON = False
            r = touched(n, fn()); one.append((n, g, r)); sheet.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa')
    tag = (grupo or 'all') + ('_f' if args else '')
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for f in os.listdir(OUT):
        if f.startswith(f'r27_{tag}_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(sheet), per):
        R.pairsheet(sheet[k:k + per], os.path.join(OUT, f'r27_{tag}_{k // per}.png'), H=HH)
    print('folhas', (len(sheet) + per - 1) // per)
    if one and ('--merge' in sys.argv or (not args and not grupo)):
        pth = os.path.join(HERE, 'data', 'final29' + sfx() + '.json')
        old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) and (args or grupo) else []
        by = {x[0]: list(x) for x in one}
        old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
        json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok')
