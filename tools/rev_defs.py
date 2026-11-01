"""Consertos por molde da revisão de 2026-10-31 (ver tools/rev_fix.py e CLAUDE.md §7.20). Cada `fix(nome, ops, bops, conv)` parte do molde de `backups/pre-rev.js`.
Convenções: coordenadas = (linha, coluna) do molde de 1 PLACA; ops de região são escaladas para o irmão "(grande)"; `bops` só no grande, nas coordenadas dele.
Letras: use o código Pindou com `legend` ({'T': 'C15'}) ou a letra da paleta (k preto, w branco, i/l/m/d/h cinzas, s/E11 peles...)."""
import os
from rev_fix import fix, L, HEXL
import weak_fix as WF


# ------------------------------------------------------------------ ajudantes
def eyes(r0, r1, c0, c1, iris=None, letter=None, tol=70, frac=0.18, white=(255, 255, 255), wtol=28, wfrac=0.5, black=0.5, dark=80, wletter='w', extra=()):
    """re-lê os olhos da fonte (região em contas, inclusive): preto onde >= `black` da janela é escuro (pálpebra e pupila), íris (`iris` RGB -> `letter`) onde >= `frac` tem essa cor,
    branco da esclera (`white` RGB, tolerância `wtol`) onde >= `wfrac`. A 1ª regra que vale ganha; `extra` = regras a mais ({'rgb','tol','frac','letter'})."""
    rules = []
    if black: rules.append({'black': dark, 'frac': black, 'letter': 'k'})
    for e in extra: rules.append(e)
    if iris: rules.append({'rgb': iris, 'tol': tol, 'frac': frac, 'letter': letter})
    if white: rules.append({'rgb': white, 'tol': wtol, 'frac': wfrac, 'letter': wletter})
    return ('boost', (r0, r1, c0, c1), None, rules)


# ------------------------------------------------------------------ Bleach
fix('Toshiro Hitsugaya (Bleach, chibi, katana)', ops=[eyes(18, 23, 8, 27, iris=(80, 170, 165), letter='M', white=(236, 233, 223), wfrac=0.45)])
fix('Ikkaku Madarame (Bleach, chibi, lança)', ops=[eyes(11, 16, 12, 31, white=(242, 233, 223), wfrac=0.5)])
fix('Kisuke Urahara (Bleach, chibi)', ops=[eyes(17, 23, 6, 31, iris=(112, 110, 113), letter='m', tol=45, frac=0.35, white=(250, 250, 250), wfrac=0.6)])
fix('Yoruichi Shihouin (Bleach, chibi, gata)', ops=[eyes(17, 22, 7, 27, iris=(252, 232, 100), letter='G', tol=60, frac=0.2, white=(250, 245, 240), wfrac=0.5)])
fix('Jushiro Ukitake (Bleach, chibi)', ops=[eyes(13, 19, 7, 27, white=(255, 255, 255), wtol=30, wfrac=0.12, black=0.45)])


def reread(r0, r1, c0, c1, rules):
    """relê a região da fonte com regras {'rgb'|'black', 'tol', 'frac', 'letter'} (a 1ª que vale ganha); só troca conta que já existe"""
    return ('boost', (r0, r1, c0, c1), None, list(rules))


def rule(rgb, letter, tol=30, frac=0.45): return {'rgb': rgb, 'tol': tol, 'frac': frac, 'letter': letter}


# refinamentos do Bleach (2ª passada, depois de olhar os olhos ampliados)
fix('Toshiro Hitsugaya (Bleach, chibi, katana)', ops=[eyes(18, 23, 8, 27, iris=(80, 170, 165), letter='M', tol=75, frac=0.12, white=(236, 233, 223), wfrac=0.4)])
fix('Ikkaku Madarame (Bleach, chibi, lança)', ops=[eyes(11, 16, 12, 31, iris=(120, 65, 50), letter='n', tol=60, frac=0.2, white=(242, 233, 223), wfrac=0.45)])
fix('Yoruichi Shihouin (Bleach, chibi, agachada)', ops=[eyes(15, 23, 6, 30, iris=(235, 170, 45), letter='a', tol=80, frac=0.12, white=(250, 246, 242), wfrac=0.5)])
fix('Kenpachi Zaraki (Bleach, chibi)', ops=[reread(21, 48, 0, 38, [rule((236, 227, 213), 'w', 24, 0.3), rule((250, 250, 245), 'w', 22, 0.4)])])

# Code Geass
fix('Kallen Stadtfeld (Code Geass, chibi)', ops=[eyes(17, 24, 9, 28, iris=(115, 40, 85), letter=L['D14'], tol=85, frac=0.2, white=(255, 255, 255), wtol=16, wfrac=0.5, black=0.55)])
fix('C.C. (Code Geass, desenho sobre a grade)', ops=[eyes(13, 20, 7, 28, iris=(225, 160, 55), letter='a', tol=85, frac=0.14, white=None, black=0.5)])

# Demon Slayer
fix('Nezuko Kamado (Demon Slayer, chibi, bambu)', ops=[eyes(8, 15, 5, 22, iris=(165, 85, 70), letter=L['F6'], tol=75, frac=0.14, white=(255, 255, 255), wtol=20, wfrac=0.4, black=0.55)])
fix('Sanemi Shinazugawa (Demon Slayer, chibi, adesivo)', ops=[eyes(14, 21, 13, 36, iris=(120, 180, 150), letter='g', tol=75, frac=0.14, white=(250, 250, 250), wtol=20, wfrac=0.5, black=0.55)])
fix('Muzan Kibutsuji (Demon Slayer, chibi)', ops=[
    reread(0, 17, 0, 23, [rule((244, 234, 232), 'w', 30, 0.4), rule((185, 165, 172), 'l', 28, 0.45)]),
    reread(35, 49, 4, 22, [rule((252, 252, 252), 'w', 20, 0.45), rule((200, 195, 205), 'l', 28, 0.45)]),
    reread(17, 24, 3, 22, [rule((205, 30, 45), 'r', 90, 0.2)])])
fix('Obanai Iguro (Demon Slayer, chibi, adesivo)', ops=[
    eyes(13, 21, 15, 36, iris=(230, 160, 40), letter='a', tol=75, frac=0.14, white=(252, 252, 252), wtol=18, wfrac=0.5, black=0.55,
         extra=[{'rgb': (60, 200, 190), 'tol': 80, 'frac': 0.14, 'letter': 'c'}]),
    ('smooth', (28, 47, 0, 47), None, 1)])


def eyes2(regions, iris=None, letter=None, tol=50, frac=0.2, minpx='auto', white=None, wtol=22, wfrac=0.5, wletter='w', black=None, dark=80, extra=()):
    """olhos em regiões APERTADAS (uma por olho; lista de (l0,l1,c0,c1)): íris só onde há uma MANCHA conexa da cor (minpx), esclera branca e pálpebra preta opcionais.
    `extra` = outras regras já prontas (ex.: segunda cor de íris). Devolve a LISTA de ops (use com *)."""
    if isinstance(regions, tuple): regions = [regions]
    ops = []
    for (a, b, c, d) in regions:
        rules = []
        if black: rules.append({'black': dark, 'frac': black, 'letter': 'k'})
        for e in extra: rules.append(dict(e, minpx=e.get('minpx', 'auto')))
        if iris: rules.append({'rgb': iris, 'tol': tol, 'frac': frac, 'letter': letter, 'minpx': minpx})
        if white: rules.append({'rgb': white, 'tol': wtol, 'frac': wfrac, 'letter': wletter})
        ops.append(('boost', (a, b, c, d), None, rules))
    return ops


# 3ª passada: regiões apertadas e manchas conexas (as faixas largas pintavam cabelo e bochecha)
fix('Kallen Stadtfeld (Code Geass, chibi)', ops=eyes2([(18, 23, 9, 15), (18, 23, 21, 27)], iris=(115, 40, 85), letter=L['D14'], tol=55, frac=0.25))
fix('Nezuko Kamado (Demon Slayer, chibi, bambu)', ops=eyes2([(8, 14, 6, 13), (8, 14, 15, 22)], iris=(165, 85, 70), letter=L['F6'], tol=50, frac=0.25))
fix('Sanemi Shinazugawa (Demon Slayer, chibi, adesivo)', ops=eyes2([(14, 20, 13, 20), (15, 21, 23, 31)], iris=(120, 180, 150), letter='g', tol=55, frac=0.25))
fix('Obanai Iguro (Demon Slayer, chibi, adesivo)', ops=[
    *eyes2([(14, 20, 16, 23)], iris=(230, 160, 40), letter='a', tol=60, frac=0.25),
    *eyes2([(14, 21, 27, 34)], iris=(60, 200, 190), letter='c', tol=65, frac=0.25),
    ('smooth', (28, 47, 0, 47), None, 1)])
fix('C.C. (Code Geass, desenho sobre a grade)', ops=eyes2([(14, 19, 8, 15), (14, 19, 19, 26)], iris=(225, 160, 55), letter='a', tol=65, frac=0.2))


# ------------------------------------------------------------------ olhos carimbados no centro da íris detectada na fonte (op 'eye')
T_OVAL = [' I ', 'wII', 'III', ' I ']                                  # olho oval sem contorno (Kallen)
T_B = ['kkkkk', 'kIIwk', 'kIPIk', ' kkk ']                             # olho com contorno preto, íris, pupila e brilho (5x4)
T_B2 = ['kkkkk', 'kwIIk', 'kIPIk', 'kJJJk']                            # mesmo, íris mais clara embaixo (olho grande, sem pálpebra de baixo)
T_S = ['kkkk', 'kIIk', 'kIPk']                                         # olho pequeno (4x3)


def eye(region, rgb, tol, tmpl, letters, minpx='auto', flip=(), top=1, dy=0, dx=0):
    return ('eye', region, None, rgb, tol, tmpl, letters, minpx, flip, top, dy, dx)


fix('Kallen Stadtfeld (Code Geass, chibi)', ops=[
    ('recolor', 18, 25, 10, 16, ['-', 'k', L['F7'], L['F8']], '}'), ('recolor', 18, 25, 21, 27, ['-', 'k', L['F7'], L['F8']], '}'),
    eye((19, 26, 9, 18), (89, 20, 58), 45, T_OVAL, {'I': L['F7']}),
    eye((19, 26, 19, 28), (89, 20, 58), 45, T_OVAL, {'I': L['F7']}),
    ('put', {(26, 17): 'k', (27, 18): 'k', (26, 19): 'k'})])
fix('Nezuko Kamado (Demon Slayer, chibi, bambu)', ops=[
    ('recolor', 9, 16, 8, 13, ['k', L['F10']], '}'), ('recolor', 9, 16, 15, 21, ['k', L['F10']], '}'),
    eye((10, 16, 8, 13), (113, 70, 45), 38, T_B2, {'I': L['F10'], 'J': L['G5'], 'P': 'k', 'w': 'w'}, dy=1),
    eye((10, 16, 16, 21), (113, 70, 45), 38, T_B2, {'I': L['F10'], 'J': L['G5'], 'P': 'k', 'w': 'w'}, dy=1)])
fix('Sanemi Shinazugawa (Demon Slayer, chibi, adesivo)', ops=[
    eye((14, 20, 15, 22), (150, 185, 150), 30, T_B, {'I': 'g', 'P': 'k', 'w': 'w'}),
    eye((15, 21, 24, 31), (150, 185, 150), 30, T_B, {'I': 'g', 'P': 'k', 'w': 'w'})])
fix('C.C. (Code Geass, desenho sobre a grade)', ops=[
    eye((13, 20, 7, 15), (210, 150, 60), 50, T_S, {'I': 'a', 'P': 'k'}),
    eye((13, 20, 18, 27), (210, 150, 60), 50, T_S, {'I': 'a', 'P': 'k'})])
fix('Obanai Iguro (Demon Slayer, chibi, adesivo)', ops=[
    eye((13, 21, 15, 24), (240, 195, 70), 45, T_B, {'I': 'y', 'P': 'k', 'w': 'w'}),
    eye((13, 21, 26, 36), (40, 170, 150), 55, T_B, {'I': 'M', 'P': 'k', 'w': 'w'}),
    ('smooth', (28, 47, 0, 47), None, 1)])


_LEG = {'I': 'B3', 'P': 'H7'}
fix('Sanemi Shinazugawa (Demon Slayer, chibi, adesivo)', ops=[
    ('blocks', [(15, 16, ['kkkk ', 'kIIwk', 'kIPIk', ' kkk ']), (16, 26, [' kkkk', 'kwIIk', 'kIPIk', ' kkk '])], _LEG)])


# ------------------------------------------------------------------ centros medidos na fonte (rev_fix.py blobs) + carimbo
T_OV45 = [' II ', 'wIII', 'IIII', 'IIII', ' II ']                     # olho oval 4x5 (Kallen)
T_B4 = ['kkkk', 'kwIk', 'kIIk', 'kJJk']                                # olho grande 4x4: pálpebra, brilho, íris escura e clara embaixo (Nezuko)
T_B4P = ['kkkk', 'kIIk', 'kPIk', ' kk ']                                # olho 4x4 com pupila (Obanai)

fix('Kallen Stadtfeld (Code Geass, chibi)', ops=[
    ('recolor', 18, 26, 10, 16, ['-', 'k', L['F7'], L['F8']], '}'), ('recolor', 18, 26, 20, 27, ['-', 'k', L['F7'], L['F8']], '}'),
    ('stamp', (22.7, 13.16), T_OV45, {'I': L['F7']}), ('stamp', (22.73, 23.12), T_OV45, {'I': L['F7']}),
    ('put', {(26, 17): 'k', (27, 18): 'k', (26, 19): 'k'})])
fix('Nezuko Kamado (Demon Slayer, chibi, bambu)', ops=[
    ('recolor', 9, 16, 7, 13, ['k', L['F10']], '}'), ('recolor', 9, 16, 14, 20, ['k', L['F10']], '}'),
    ('stamp', (14.5, 9.71), T_B4, {'I': L['F10'], 'J': L['G5']}), ('stamp', (14.5, 16.7), T_B4, {'I': L['F10'], 'J': L['G5']}),
    ('put', {(9, 9): L['F10'], (9, 10): L['F10'], (9, 11): L['F10'], (9, 16): L['F10'], (9, 17): L['F10'], (9, 18): L['F10']})])
fix('Obanai Iguro (Demon Slayer, chibi, adesivo)', ops=[
    ('stamp', (17.55, 19.95), T_B4P, {'I': 'y', 'P': 'k'}), ('stamp', (18.31, 28.66), T_B4P, {'I': L['B6'], 'P': 'k'}),
    ('smooth', (28, 47, 0, 47), None, 1)])


# ------------------------------------------------------------------ reconversão da fonte com parâmetros novos (para os "revisão maior")
_CFG = {}


def _cfg(name):
    """item do CFG (r22/r23) de uma ilustração: (rem, idx, kw, plates, box)"""
    if not _CFG:
        import r22_exfinal as R22
        import r23_exfinal as R23
        for rem, mod in ((22, R22), (23, R23)):
            for it in mod.CFG:
                if it[4] == 'ill': _CFG[it[0]] = (rem, it[2], dict(it[7]), it[5], it[6], mod)
    return _CFG[name]


def reconv(name, skin=None, **over):
    """conv(big) -> linhas: converte de novo a fonte do molde `name` (CFG da remessa) com os parâmetros de `over` por cima dos que ele tinha; 1 placa ou irmão grande (plates do CFG)"""
    def conv(big):
        import r22_exfinal as R22, r5
        rem, idx, kw, plates, box, mod = _cfg(name)
        kw = dict(kw); kw.update(over)
        sk = mod._skin(name) if skin is None else skin
        r5.SKIN_ON = sk
        import glob
        oldF = R22.F
        if rem == 23: R22.F = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'remessas', 'remessa 23', '*.*')))      # o R22 foi importado com REMNUM=22
        try:
            if big: return R22.ill(idx, dict(kw), plates=plates, box=box, skin=sk)
            return R22.ill(idx, kw, box=box, skin=sk)
        finally:
            R22.F = oldF
    return conv


# ------------------------------------------------------------------ Goku Black Rosé e Goku Instinto Superior: base reconvertida mais lisa + rosto desenhado
fix('Goku Black Rosé (Dragon Ball, chibi)',
    conv=reconv('Goku Black Rosé (Dragon Ball, chibi)', K=12, smooth_de=40, dark_frac=0.2),
    ops=[('smooth', (0, 22, 0, 25), None, 2)])
fix('Goku (Instinto Superior, chibi, adesivo)',
    conv=reconv('Goku (Instinto Superior, chibi, adesivo)', K=12, smooth_de=40, dark_frac=0.2),
    ops=[('smooth', (0, 20, 0, 28), None, 2)])


_GB_CLEAN = ['k', 'w', 'm', 'l', 'i', L['F1'], L['F3'], L['F14'], L['E15'], L['F4']]
fix('Goku Black Rosé (Dragon Ball, chibi)',
    conv=reconv('Goku Black Rosé (Dragon Ball, chibi)', K=12, smooth_de=40, dark_frac=0.2),
    ops=[('smooth', (0, 22, 0, 25), None, 2),
         ('recolor', 26, 30, 7, 18, _GB_CLEAN, 's'),
         ('put', {**{(26, c): 'k' for c in (7, 8, 9, 10)}, **{(27, c): 'k' for c in (11, 12, 13, 14)}, **{(26, c): 'k' for c in (15, 16, 17, 18)},
                  (27, 8): 'l', (27, 9): 'm', (27, 10): 'l', (27, 15): 'l', (27, 16): 'm', (27, 17): 'l',
                  (29, 12): 'n', (30, 11): 'k', (30, 12): 'k', (30, 13): 'k'})])
fix('Goku (Instinto Superior, chibi, adesivo)',
    conv=reconv('Goku (Instinto Superior, chibi, adesivo)', K=12, smooth_de=40, dark_frac=0.2),
    ops=[('desat', (0, 19, 0, 28), None, ['w', 'i', 'l'], 26.0), ('smooth', (0, 20, 0, 28), None, 2),
         ('recolor', 20, 25, 9, 18, ['k', '@', '3', L['D11'], 'i', L['F3']], 's'),
         ('put', {(20, 9): 'k', (20, 10): 'k', (21, 11): 'k', (21, 12): 'k', (20, 18): 'k', (20, 17): 'k', (21, 16): 'k', (21, 15): 'k',
                  (22, 10): 'l', (22, 11): 'm', (22, 12): 'l', (22, 15): 'l', (22, 16): 'm', (22, 17): 'l',
                  (24, 12): 'k', (24, 13): 'k', (24, 14): 'k'})])


# ------------------------------------------------------------------ Kratos (pixel, corpo inteiro): a pele marfim saía ROSA (trava de pele) e a redução a 1 placa embaralhava o tronco e o braço
def _kratos_conv(big):
    """leitura exata no passo fino (9,07 px = meio pixel do desenho) com a trava de pele DESLIGADA (marfim/caqui em vez de rosa); o de 1 placa é a redução 'bias' dela, como o add_templates faz"""
    import os
    os.environ.setdefault('REMNUM', '23')
    import r6, r5, shrink, loose
    from PIL import Image
    import glob
    fl = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'remessas', 'remessa 23', '*.*')))
    W, H = Image.open(fl[20]).size
    px, py, ox, oy = 9.07, 9.08, 8.10, 11.70
    r5.SKIN_ON = False
    old = r6.FILES
    r6.FILES = fl                                                  # o r6 pode ter sido carregado com outra remessa (REMNUM do r22)
    try:
        fine = r6.exact6(20, px=dict(px=px, py=py, ox=ox % px, oy=oy % py, W=int((W - ox) / px + 0.5), H=int((H - oy) / py + 0.5)), mode=True, achro=70, post=r5.largest)
    finally:
        r6.FILES = old
    if loose.loose_count(fine): fine = loose.fix_loose(fine)
    if big: return fine
    return loose.fix_loose(shrink.shrink(fine, 50, 'bias', empty_at=0.6))


fix('Kratos (God of War, pixel, corpo inteiro)', conv=_kratos_conv)


# ------------------------------------------------------------------ Frieren cajado (olho direito), Fern (olhos e cabelo), Stark (olhos e corpo)
_FR = {'N': L['B7'], 'g': L['B3'], '@': L['E14']}
fix('Frieren (chibi, cajado)', ops=[
    ('stamp', (20.0, 27.0), [' kkkkk', 'kkNNwk', 'wgkgww', ' w@g@w'], _FR)])
_FERN = {'I': L['D5'], 'J': L['D12'], 'P': 'k', 'S': L['E11']}
fix('Fern (Frieren, chibi, adesivo)', ops=[
    ('smooth', (0, 30, 0, 43), [L['D14'], L['D21'], L['D5'], L['D13'], L['D12']], 2),
    ('stamp', (13.6, 19.4), ['kkkk', 'kIIk', 'kIPk', ' wk '], _FERN),
    ('stamp', (14.6, 26.2), ['kkkk', 'kIIk', 'kIPk', ' wk '], _FERN)])
_STK = {'I': 'r', 'P': 'k', 'S': L['E11']}
fix('Stark (Frieren, chibi)', ops=[
    ('stamp', (17.0, 9.5), ['kkkkk', 'kIwIk', 'kIPIk', ' kkk '], _STK),
    ('stamp', (17.0, 18.5), ['kkkkk', 'kIwIk', 'kIPIk', ' kkk '], _STK),
    ('smooth', (19, 47, 0, 24), None, 2)])


# ------------------------------------------------------------------ mapas de cor por centro (center_map) para as revisões
def _hsvL(rgb, L):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[c / 255.0 for c in rgb]); return h * 360, s, v


def cm_navy(rgb, Lum, letter, is_black):
    """azul-violeta quase preto e saturado (sombras da capa do Kaido: (4,1,27), (6,0,36), (17,3,51)): em vez de preto, o azul-marinho D15; (32,13,90) fica roxo escuro D14"""
    h, s, v = _hsvL(rgb, Lum)
    if 238 <= h <= 292 and s >= 0.78 and Lum <= 30:
        if Lum < 1.5: return None
        return L['D15'] if Lum < 9 else L['D14']
    return None


def _both_cm(*fns):
    def f(*a):
        for fn in fns:
            r = fn(*a)
            if r: return r
        return None
    return f


def _kaido_conv(big):
    import r22_exfinal as R22
    name = 'Kaido (One Piece, chibi)'
    cm = _both_cm(cm_navy, R22.CM_BLOND)
    kw = dict(K=32, dark_frac=0.2, black_L=1.5, smooth_de=10.0, rare_n=8, center_map=cm) if big else dict(K=28, dark_frac=0.4, black_L=1.0, smooth_de=6.0, rare_n=6, center_map=cm)
    return reconv(name, **kw)(big)


fix('Kaido (One Piece, chibi)', conv=_kaido_conv)


# ------------------------------------------------------------------ Mihawk: o rosto sumia no cabelo/chapéu pretos (dark_frac 0,25 engolia a pele) e a espada era um fio
_MH = {'R': 'r', 'S': L['E14']}
fix('Dracule Mihawk (One Piece, chibi)',
    conv=reconv('Dracule Mihawk (One Piece, chibi)', K=26, dark_frac=0.5, black_L=8.0, smooth_de=10.0, rare_n=8),
    ops=[reread(17, 30, 8, 31, [rule((250, 222, 210), L['E14'], 38, 0.42), rule((240, 195, 185), L['E14'], 30, 0.45), {'black': 70, 'frac': 0.5, 'letter': 'k'}]),
         ('stamp', (21.6, 18.3), [' kkkkk ', 'kSRRRSk', 'kSRkRSk', ' kkkkk '], _MH),
         ('stamp', (23.4, 25.4), ['kkkkk', 'SRRSk', ' kkk '], _MH)])


# ------------------------------------------------------------------ Brasões de Hogwarts: tira a coluna-borda do gráfico e o ruído, e põe moldura de quadro marrom
def _crest(name):
    fix(name, ops=[('wipe', 0, 40, 26 if '(escudo)' in name and 'Sonserina' not in name else 27, 40),   # coluna-resto da borda da folha (a última)
                   ('smooth', (0, 40, 0, 40), None, 2),
                   ('clean', dict(halo=False, pale_edge=0)),
                   ('frame', 3, [L['F10'], L['G6'], L['G13']], L['H12'], 1)])


for _n in ('Brasão da Grifinória (escudo)', 'Brasão da Lufa-Lufa (escudo)', 'Brasão da Sonserina (escudo)', 'Brasão da Corvinal (escudo)'):
    _crest(_n)


# ------------------------------------------------------------------ Inazuma Eleven: bordas limpas + degradês nos poderes (ramp relê a fonte e escolhe a letra dentro de uma rampa curta)
FIRE = [L['E11'], L['A11'], L['A4'], L['A6'], L['A7'], L['F4'], L['F13'], L['F8']]
GOLD = [L['E11'], L['A11'], L['G9'], L['A6']]                                  # amarelo-palha da mão/punho (A1/H12 saíam esverdeados)
ICEB = ['w', L['C3'], L['C4'], L['C6'], L['C8']]
BLUEH = [L['C3'], L['C4'], L['C6'], L['C8'], L['C7'], L['C9'], L['D3']]
_CL = ('clean', {})


def _ramp_fix(name, ramp, frm, region, passes=1, extra=()):
    fix(name, ops=[('ramp', region, None, set(frm), list(ramp), passes), *extra, _CL])


_ramp_fix('Endou Mamoru (Inazuma Eleven, mão de fogo)', FIRE, FIRE + [L['A1'], L['A12'], L['A9']], (0, 48, 0, 27))
_ramp_fix('Gouenji Shuuya (Inazuma Eleven, Fire Tornado)', FIRE, FIRE + [L['G6'], L['A13']], (24, 48, 0, 38))
_ramp_fix('Jogador de cabelo verde-escuro e faixa vermelha (Inazuma Eleven, Heat Tackle)', FIRE, FIRE + [L['A13']], (0, 40, 0, 46))
_ramp_fix('Endou Mamoru (Inazuma Eleven, punho gigante)', GOLD, [L['A11'], L['A1'], L['A13'], L['A5'], L['H12'], L['A6'], L['G9'], L['E11']], (0, 32, 0, 22))
_ramp_fix('Endou Mamoru (Inazuma Eleven, God Hand)', GOLD, [L['A11'], L['A1'], L['A13'], L['A5'], L['H12'], L['A6'], L['E11']], (0, 45, 0, 24))
_ramp_fix('Endou Mamoru (Inazuma Eleven, Mugen the Hand)', GOLD, [L['A11'], L['A1'], L['A13'], L['A5'], L['H12'], L['A6']], (0, 40, 0, 45))
_ramp_fix('Fubuki Shirou (Inazuma Eleven, Eternal Blizzard)', ICEB, ICEB + [L['H1'], L['H3']], (0, 41, 0, 20))
_ramp_fix('Ichirouta Kazemaru (Inazuma Eleven, Shippuu Dash)', BLUEH, BLUEH + [L['C16'], L['C17'], L['C5']], (0, 25, 0, 49), 2)
_ramp_fix('Yuuto Kidou (Inazuma Eleven, chibi, explosão)', [L['F8'], L['F13'], L['F4'], L['A7'], L['A6'], L['A4']], [L['F4'], L['F8'], L['F13'], L['A6'], L['A4'], L['A7'], L['F3'], L['F5']], (0, 49, 0, 47))
fix('Yuuto Kidou (Inazuma Eleven, óculos e capa)', ops=[('smooth', (0, 20, 0, 42), None, 2), _CL])


# ------------------------------------------------------------------ Nanami ×3 e Sukuna: o contorno fino azul-marinho (L ~ 15-19) não passava do limiar de "preto" e o rosto/óculos ficavam lavados
_THIN = dict(dark_frac=0.14, black_L=20.0, K=28, smooth_de=14.0)
for _n in ('Kento Nanami (Jujutsu Kaisen, chibi, correndo)', 'Kento Nanami (Jujutsu Kaisen, chibi, sentado)', 'Kento Nanami (Jujutsu Kaisen, chibi, braços cruzados)'):
    fix(_n, conv=reconv(_n, **_THIN))
fix('Sukuna (Jujutsu Kaisen, chibi, adesivo)', conv=reconv('Sukuna (Jujutsu Kaisen, chibi, adesivo)', **_THIN))


_MILD = dict(dark_frac=0.2, black_L=16.0, K=28, smooth_de=14.0)
fix('Kento Nanami (Jujutsu Kaisen, chibi, sentado)', conv=reconv('Kento Nanami (Jujutsu Kaisen, chibi, sentado)', **_MILD))
fix('Kento Nanami (Jujutsu Kaisen, chibi, braços cruzados)', conv=reconv('Kento Nanami (Jujutsu Kaisen, chibi, braços cruzados)', **_MILD),
    ops=[('ramp', (22, 99, 0, 99), None, {'i', 'w'}, ['i', 'l'], 1)])


# ------------------------------------------------------------------ Dabi (olhos), Shoto/Endeavor (borda e chamas), Kuma (rosto), Sunny (bandeira de caveira com chapéu de palha desenhada)
_DB = {'N': L['B7']}
fix('Dabi (My Hero Academia, chibi)', ops=[
    ('stamp', (18.9, 8.6), ['kkkk', 'wNNw', ' kk '], _DB), ('stamp', (18.9, 16.9), ['kkkk', 'wNNw', ' kk '], _DB)])
_FIRE2 = [L['E11'], L['A11'], L['A4'], L['A6'], L['A7'], L['F4'], L['F13'], L['F8']]
fix('Endeavor (My Hero Academia, rosto em chamas)', ops=[('ramp', (0, 47, 0, 33), None, set(_FIRE2) | {L['A12'], L['F3'], L['G5']}, _FIRE2, 1), ('clean', {})])
fix('Shoto Todoroki (My Hero Academia, chibi, adesivo)', ops=[('smooth', (0, 45, 0, 32), None, 1), ('clean', {})])
fix('Endeavor (My Hero Academia, chibi, adesivo)', ops=[('clean', {})])
fix('Bartholomew Kuma (One Piece, chibi)', ops=[('clean', {})])
_SKULL = ['     yyyyy     ',
          '    yyyyyyy    ',
          '   yyyyyyyyy   ',
          '   rrrrrrrrr   ',
          'yyyyyyyyyyyyyyy',
          ' yyyyyyyyyyyyy ',
          '   kkkkkkkkk   ',
          '  kwwwwwwwwwk  ',
          '  kwkkwwwkkwk  ',
          '  kwkkwwwkkwk  ',
          '  kwwwkkkwwwk  ',
          '   kwwwwwwwk   ',
          '   kwkwkwkwk   ',
          '    kkkkkkk    ']
fix('Thousand Sunny (ilustração)', ops=[('stamp', (13.5, 11.5), _SKULL, {'y': 'y', 'r': 'r', 'k': 'k', 'w': 'w'})])


fix('Snorlax de Batman (Pokémon)', conv=reconv('Snorlax de Batman (Pokémon)', K=32, dark_frac=0.2, black_L=10.0, smooth_de=8.0, rare_n=10, sat=1.0))


# ------------------------------------------------------------------ Sukuna: poderes (mão com energia vermelha à esquerda e espírito amaldiçoado à direita) em rampa de vermelhos; o corpo fica como estava
_RED = [L['F7'], L['F8'], L['F5']]
fix('Sukuna (Jujutsu Kaisen, chibi, adesivo)', ops=[
    ('ramp', (20, 34, 0, 11), None, None, _RED, 1),
    ('ramp', (6, 20, 32, 44), None, None, _RED, 1),
    ('clean', {})])


import weak_cm as _WC
CM_BR = _both_cm(_WC.CM_BROWN)                      # cabelo marrom escuro que o near120 mandava para o preto (Alucard)


# ------------------------------------------------------------------ Alucard ×3 (revisões maiores no sentado e no adesivo; a boca do de pistolas)
_AL = {'R': 'r', 'k': 'k', 'w': 'w', 'S': L['E14']}
# pistolas: a boca só tinha um traço preto e uma fileira branca (o rosto é branco): sorriso largo em U com 4 dentes separados e a pele em cinza-gelo
fix('Alucard (Hellsing, chibi, pistolas)', ops=[
    ('recolor', 20, 28, 12, 30, ['w'], L['H1']),
    ('blocks', [(23, 13, ['kkkkkkkkkkkkkkkkk', 'kwkwwkwwkwwkwwkwk', ' kkwkwkwkwkwkwkk ', '   kkkkkkkkkkk   '])])])
# sentado: fios de cabelo (preto de verdade da fonte, sem confundir com o marrom), olhos vermelhos grandes e a mão no queixo
fix('Alucard (Hellsing, chibi, sentado)', ops=[
    ('boost', (0, 17, 0, 35), None, [{'black': 38, 'frac': 0.3, 'letter': 'k'}]),
    ('stamp', (22.3, 15.0), [' kkkk ', 'kRRwRk', 'kRRRRk', ' kkkk '], _AL),
    ('stamp', (19.8, 27.0), ['kkkk', 'kRRk', 'kRRk', ' kk '], _AL)])
# adesivo: rosto com pele clara, olhos vermelhos e sorriso de dentes sob o cabelo preto; casaco vermelho
fix('Alucard (Hellsing, chibi, adesivo)', ops=[
    ('boost', (11, 23, 14, 34), None, [{'rgb': (250, 225, 210), 'tol': 38, 'frac': 0.4, 'letter': L['E14']}, {'rgb': (235, 160, 150), 'tol': 40, 'frac': 0.4, 'letter': L['E1']}]),
    ('boost', (11, 20, 18, 31), None, [{'black': 38, 'frac': 0.5, 'letter': 'k'}]),
    ('stamp', (15.2, 20.8), ['kkkkk', 'kRRRk', 'kRwRk', ' kkk '], _AL),
    ('stamp', (15.1, 27.3), ['kkkkk', 'kRRRk', 'kRwRk', ' kkk '], _AL)])


# ------------------------------------------------------------------ "Chaveiro de chapéu e faixa verde e amarela" = Lula (foto presidencial de chapéu): corpo azul (D3 em vez do D15 arroxeado), faixa verde e amarela, rosto de pele natural, aba creme
fix('Chaveiro de chapéu e faixa verde e amarela (foto de peça pronta)', nobig=True, ops=[
    ('recolor', 15, 26, 3, 20, [L['D15']], L['D3']),
    ('recolor', 14, 25, 3, 20, [L['B17']], L['B8']),
    ('recolor', 14, 25, 3, 20, [L['G17']], 'y'),
    ('recolor', 10, 14, 3, 20, [L['A10']], L['A12']),
    ('recolor', 10, 11, 0, 22, [L['G1']], 'i'),                                 # cabelo branco que aparece sob a aba
    ('recolor', 12, 14, 8, 15, [L['G1']], 'i')])                                # barba branca


# ------------------------------------------------------------------ Beatrice (cabelo amarelo A1 em vez do bege H12; olhos azuis grandes) e Emilia (olhos violeta grandes)
_BEA = {'B': 'b', 'C': 'c', 'k': 'k', 'w': 'w'}
fix('Beatrice (Re:Zero, chibi)', ops=[
    ('recolor', 0, 99, 0, 99, [L['H12']], 'j'),
    ('stamp', (19.2, 17.5), ['kkkkk', 'kBBwB', 'kBCCB', ' BCCe', '  BB '], dict(_BEA, e='e')),
    ('stamp', (18.0, 28.5), ['kkkkk', 'kBBwB', 'kBCCB', ' BCCe', '  BB '], dict(_BEA, e='e'))])
_EMI = {'u': L['D7'], 'v': L['D6'], 'k': 'k', 'w': 'w'}
fix('Emilia (Re:Zero, chibi, adesivo)', ops=[
    ('stamp', (16.5, 15.0), ['kkkkk', 'kuuwu', 'kuvvu', ' uvvu', '  uu '], _EMI),
    ('stamp', (15.5, 23.0), ['kkkkk', 'kuuwu', 'kuvvu', ' uvvu', '  uu '], _EMI)])


# ====== RODADA 2 (conferência da lista inteira) ======
import numpy as _np, cv2 as _cv2


def hull_fill(letter=None, seeds=None, nearest=None):
    """func: preenche os vazios dentro do fecho convexo das contas `seeds` (None = todas): com `letter`, ou com a conta mais próxima entre as letras `nearest` (cenário pintado com falhas)"""
    def f(g, sx, sy):
        H, W = len(g), len(g[0])
        m = _np.array([[(c != '.' and (seeds is None or c in seeds)) for c in r] for r in g], _np.uint8)
        pts = _cv2.findNonZero(m)
        if pts is None: return
        mask = _np.zeros((H, W), _np.uint8); _cv2.fillConvexPoly(mask, _cv2.convexHull(pts), 1)
        src = [(y, x) for y in range(H) for x in range(W) if nearest and g[y][x] in nearest]
        ys = _np.array([q[0] for q in src]); xs = _np.array([q[1] for q in src])
        for y in range(H):
            for x in range(W):
                if mask[y, x] and g[y][x] == '.':
                    if letter: g[y][x] = letter
                    else:
                        k = int(_np.argmin((ys - y) ** 2 + (xs - x) ** 2)); g[y][x] = g[ys[k]][xs[k]]
    return f


# ------------------------------------------------------------------ Spy x Family
fix('Anya Forger (chibi)', ops=[
    ('recolor', 0, 99, 0, 99, ['s'], L['E11']),                        # pele da fonte (251,223,195): o G1 ficava escuro e acinzentado
    ('recolor', 26, 99, 0, 99, ['r'], '/')])                           # vestido azul-marinho (78,71,89); o quadriculado vermelho do peito fica
fix('Anya Forger (pixel, gráfico)', ops=[
    ('recolor', 0, 99, 0, 99, [L['H12']], L['E11']),                   # rosto
    ('recolor', 0, 22, 0, 99, [L['G3'], L['G5']], L['F14']),           # cabelo rosa (o bege G3 lia como cor de pele)
    ('recolor', 0, 12, 0, 99, ['l'], 'w'), ('recolor', 12, 20, 0, 99, ['l'], 'w')])
fix('Loid Forger (Spy x Family, chibi)', ops=[
    ('blocks', [(15, 5, ['kkkkk', 'wQwNw', 'wQQNw', ' NNN ']), (15, 14, ['kkkkk', 'wQwNw', 'wQQNw', ' NNN ']), (22, 11, ['tt'])])])
fix('Yor Forger (Spy x Family, chibi)', ops=[
    ('blocks', [(13, 4, ['kkkkk', 'wkwÉw', 'wkkÉw', ' ÉÉÉ ']), (13, 12, ['kkkkk', 'wkwÉw', 'wkkÉw', ' ÉÉÉ ']), (20, 9, ['nn'])])])
fix("Elias Ainsworth (The Ancient Magus' Bride, chibi, adesivo)", ops=[
    ('recolor', 19, 23, 12, 16, ['k'], 'w'),
    ('put', {(21, 3): 'k', (22, 4): 'k', (21, 5): 'k', (22, 6): 'k', (22, 7): 'k', (21, 8): 'k', (22, 9): 'k', (21, 10): 'k', (22, 11): 'k', (21, 12): 'k', (20, 13): 'k', (21, 13): 'k'})])

# ------------------------------------------------------------------ Yu Yu Hakusho
fix('Yusuke Urameshi (Yu Yu Hakusho, pose)', nobig=True, ops=[
    ('recolor', 13, 19, 8, 22, ['r', '#', L['G3'], L['M6'], 'l', L['F3']], L['E11']),
    ('recolor', 12, 17, 2, 8, ['r'], L['G3']),
    ('blocks', [(14, 11, ['kkkkk', 'wÕwkw', 'wÕkkw', ' ÕÕÕ ']), (14, 18, ['kkkkk', 'wÕwkw', 'wÕkkw', ' ÕÕÕ ']), (19, 16, ['k   k', ' kkk '])])])
fix('Kazuma Kuwabara (Yu Yu Hakusho, espada espiritual)', ops=[
    ('blocks', [(10, 16, ['}kkk}kkk}', '}wkw}wkw}']), (14, 19, ['ttt'])])])
fix('Koenma (Yu Yu Hakusho, chibi)', ops=[
    ('recolor', 14, 16, 8, 14, ['k'], L['E10']),
    ('blocks', [(1, 6, ['   kkkkk   ', ' kkkkkkkkk ', ' kkrrrrrkk ', 'kkrkkkkkrkk', 'kkrrrkrrrkk', 'kkrrkkkrrkk', 'kkrrrkrrrkk', 'kkrkkkkkrkk', ' kkrrrrrkk ', ' kkkkkkkkk ', '   kkkkk   ']),
                (14, 9, ['kkk  ', ' k kk', 'kk k ']),
                (19, 6, ['kkkkk', 'wnwkw', 'wnkkw', ' kkk ']), (19, 13, ['kkkkk', 'wnwkw', 'wnkkw', ' kkk ']),
                (24, 10, [' cc ', 'cecc', ' cc '])])])
fix('Yusuke Urameshi (Yu Yu Hakusho, chibi, folha)', ops=[
    ('blocks', [(16, 0, ['.kookkkkkokkkkkkk@@kkk',
                         '.k@okwwwkookwwwkk@@kkk',
                         '.k@okÉwÉkookÉwÉkk@@kkk',
                         '.kkokÉÉÉkookÉÉÉko@@kk.',
                         '..koowÉwoooowÉwoo@kk..',
                         '...kooooookoooooo@kk..',
                         '....kkkkkkkkkkkk@@k...',
                         '.....kowkwwkwwk@k.....',
                         '......kkkkkkkkkk......',
                         '......kkooooookk......'])])])
fix('Keiko Yukimura (Yu Yu Hakusho, chibi, folha)', ops=[
    ('boost', (15, 27, 6, 24), None, [{'rgb': (252, 187, 135), 'tol': 55, 'frac': 0.35, 'letter': L['A12']}]),
    ('blocks', [(18, 8, [' kkkk ', 'kÉÉÉÉk', 'kÉwÉÉk', 'kÉÉÉÉk', ' kkkk ']), (17, 17, ['kkkk', 'ÉÉÉk', 'ÉwÉk', 'ÉÉÉk', 'kkkk']),
                (22, 16, ['n']), (24, 16, ['ÉÉ'])])])
fix('Hiei (Yu Yu Hakusho, chibi, folha)', nobig=True, ops=[
    ('recolor', 20, 25, 4, 20, ['w'], 'k'),
    ('blocks', [(21, 7, ['kkkkk', 'wwrrk', 'wwrkk', 'wwrrk', ' kkk ']), (21, 14, ['kkkkk', 'krrww', 'kkrww', 'krrww', ' kkk ']),
                (23, 12, ['DD', 'DD', 'DD'])], {'D': 'A10'})])
fix('Yu Yu Hakusho (quarteto em círculo)', ops=[
    ('recolor', 7, 10, 12, 24, ['l', 'm', 'i'], L['E11']),
    ('blocks', [(8, 14, ['kkkk', 'wkkw']), (8, 20, ['kkkk', 'wkkw']),
                (25, 26, ['kkkk', 'wfkw', 'wffw']), (24, 31, ['kkk', 'fkw', 'ffw']),
                (25, 5, ['kkk', 'wkk']),
                (37, 13, ['kkkk', 'wnkw', 'wnnw']), (37, 18, ['kkkk', 'wnkw', 'wnnw'])])])

# ------------------------------------------------------------------ Sukuna: poderes relidos da fonte (preto fica, fogo vermelho e espírito com olhos laranja e dentes), rosto desenhado
_POW = [{'rgb': (225, 35, 30), 'tol': 75, 'frac': 0.14, 'letter': 'r'}, {'rgb': (130, 20, 25), 'tol': 55, 'frac': 0.28, 'letter': L['F8']}]
fix('Sukuna (Jujutsu Kaisen, chibi, adesivo)', ops=[
    ('boost', (17, 33, 0, 12), None, _POW),
    ('boost', (6, 23, 32, 44), None, [{'rgb': (250, 110, 30), 'tol': 70, 'frac': 0.14, 'letter': 'o'}, {'rgb': (255, 255, 255), 'tol': 40, 'frac': 0.45, 'letter': 'w'}] + _POW),
    ('clean', {}),
    ('blocks', [(18, 14, ['kkkkk', 'wrkrw', ' kkk ']), (15, 23, ['kkkkk', 'wrkrw', ' kkk ']), (12, 18, [' k ', 'kkk', ' k ']),
                (23, 18, ['kkkkkkk', 'wkrrrkw', ' krrrk ', '  kkk  '])])])

# ------------------------------------------------------------------ Alucard ×3
fix('Alucard (Hellsing, chibi, pistolas)', ops=[
    ('blocks', [(22, 15, ['@@@@@@@@@@@@@@@@']), (23, 16, ['@@@k@@@@@@@k@@@']), (24, 16, ['@@@kwwwwwwwk@@@']), (25, 17, ['@@@kwwwwwk@@@']), (26, 20, ['@kkkkk@']), (27, 22, ['@@@'])], {'@': 'E14'})])
fix('Alucard (Hellsing, chibi, sentado)', ops=[
    ('boost', (0, 17, 0, 35), None, [{'black': 38, 'frac': 0.3, 'letter': 'k'}]),
    ('put', {(21, 15): L['E14'], (22, 14): L['E14'], (22, 15): L['E14'], (23, 14): L['E14']}),
    ('blocks', [(20, 13, ['kkkk ', 'krrk ', 'krwk ', ' kk  ']), (18, 21, ['kkk', 'rrk', 'rwr', 'rrk']), (24, 13, ['k   k']), (25, 13, [' kkk '])])])
fix('Alucard (Hellsing, chibi, adesivo)', conv=reconv('Alucard (Hellsing, chibi, adesivo)', K=30, dark_frac=0.5, black_L=14, sat=1.2), ops=[
    ('blocks', [(14, 17, ['kkkkkkkk kkkkkk ']), (15, 17, ['}wrkrw}kk}rkrw}']), (16, 17, ['}}rrr}}}}}}rr}}']), (17, 17, ['}}}kkkkkkk}}}}k']), (18, 17, ['}}}wwwwwww}}}kk']), (19, 17, ['kk}}kkkkk}}kkkk'])])])

# ------------------------------------------------------------------ How I Met Your Mother
fix('Casal sob o guarda-chuva amarelo na chuva (How I Met Your Mother)', ops=[
    ('recolor', 0, 24, 0, 37, ['o'], 'a'),                             # avesso do guarda-chuva: ocre, não laranja
    ('recolor', 25, 49, 0, 37, ['o', 'C'], L['G9']),                   # sobretudo caramelo
    ('recolor', 0, 49, 0, 37, [L['G3']], L['A12']),                    # pele
    ('recolor', 43, 49, 14, 20, ['e'], 'b'),                           # assinatura
    ('recolor', 23, 23, 11, 11, ['w'], L['A12']),
    ('blocks', [(24, 8, ['wk wk']), (26, 10, ['t']), (26, 24, ['wk wk']), (28, 26, ['t'])])],
    bops=[('recolor', 44, 50, 16, 27, ['w'], L['A12']), ('recolor', 50, 55, 46, 57, ['w'], L['A12']),
          ('blocks', [(46, 17, [' kk ', 'wwkw', ' ww ']), (46, 22, [' kk ', 'wwkw', ' ww ']), (50, 21, ['t']), (52, 20, ['ttt']),
                      (51, 47, [' kk ', 'wwkw', ' ww ']), (51, 52, [' kk ', 'wwkw', ' ww ']), (57, 50, ['ttt'])])])
fix('Casal sob o guarda-chuva amarelo (How I Met Your Mother, ilustração)', ops=[
    ('recolor', 20, 43, 0, 35, ['}', 's'], L['H12'])])
fix('Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)', ops=[
    ('boost', (0, 47, 0, 48), None, [{'rgb': (250, 235, 110), 'tol': 75, 'frac': 0.08, 'letter': 'y', 'fill': True}, {'rgb': (20, 90, 190), 'tol': 75, 'frac': 0.1, 'letter': '&', 'fill': True}]),
    ('func', hull_fill(letter='k'))])
fix('Casal sob o guarda-chuva amarelo (How I Met Your Mother, pintura) (grande)', ops=[
    ('recolor', 0, 99, 0, 55, [L['F9']], L['G13'])])
fix('Barney Stinson (How I Met Your Mother, de terno) (grande)', ops=[
    ('recolor', 0, 96, 0, 55, [L['F8']], '!'), ('recolor', 0, 96, 0, 55, ['r'], L['F8']), ('recolor', 0, 96, 0, 55, ['!'], 'r'),
    ('blocks', [(8, 29, ['nnn nnn']), (10, 29, ['kkk kkk']), (11, 29, ['wbk kbw']), (13, 32, ['t']), (15, 29, ['n   n']), (16, 30, ['nnn'])])])
fix('Barney Stinson (How I Met Your Mother, sinal de paz) (grande)', ops=[
    ('recolor', 0, 40, 0, 87, ['o', L['A10']], L['A13']),
    ('blocks', [(36, 30, [' kkkkkkk ', 'kkw3kk3wk', ' ww3kk3wk', '   333   ']), (36, 48, [' kkkkkkk ', 'kw3kk3wkk', 'kw3kk3ww ', '   333   '])])])

# ------------------------------------------------------------------ La La Land


def _scenery(g, sx, sy):
    """completa as falhas do cenário pintado: vazio dentro do fecho das pinceladas vira a pincelada mais próxima (nada de mãos, cabelo ou contorno como semente)"""
    H, W = len(g), len(g[0])
    up = set('qp,?{') | {L['E9'], L['D13'], L['D21'], L['E2'], L['E4']}
    low = {L['A9'], L['A10'], 'o', L['E1'], L['E15']}
    seeds = [(y, x) for y in range(H) for x in range(W) if (g[y][x] in up and y < 0.62 * H) or (g[y][x] in low and y >= 0.5 * H)]
    pts = _np.array([[x, y] for y, x in seeds], _np.int32).reshape(-1, 1, 2)
    mask = _np.zeros((H, W), _np.uint8); _cv2.fillConvexPoly(mask, _cv2.convexHull(pts), 1)
    ys = _np.array([q[0] for q in seeds]); xs = _np.array([q[1] for q in seeds])
    for y in range(H):
        for x in range(W):
            if mask[y, x] and g[y][x] == '.':
                k = int(_np.argmin((ys - y) ** 2 + (xs - x) ** 2)); g[y][x] = g[ys[k]][xs[k]]


fix('Casal dançando (La La Land)', ops=[('func', _scenery)])
_NIGHT = dict(K=40, dark_frac=0.08, black_L=4.0, sat=1.3, contrast=1.2)
fix('Casal dançando à noite (La La Land)', conv=reconv('Casal dançando à noite (La La Land)', **_NIGHT), ops=[
    ('ramp', (29, 49, 0, 37), None, {'k'}, ['/', '&', '4'], 0),
    ('boost', (0, 8, 0, 31), None, [{'rgb': (225, 225, 255), 'tol': 80, 'frac': 0.05, 'letter': 'e'}]),
    ('boost', (22, 28, 0, 8), None, [{'rgb': (255, 235, 170), 'tol': 80, 'frac': 0.05, 'letter': 'y'}, {'rgb': (225, 235, 255), 'tol': 70, 'frac': 0.05, 'letter': 'e'}]),
    ('blocks', [(15, 16, ['k', 'k']), (16, 24, ['k', 'k']), (18, 15, ['q']), (18, 25, ['q'])])])

# ------------------------------------------------------------------ Paige (rostos)
fix('Paige (WWE, com cinturão)', ops=[
    ('blocks', [(7, 12, ['kkkkskkkk', 'kwnkskwnk', 'sssssssss', 'sssssssss', 'ssswwwsss', 'sssrrrsss'])])],
    bops=[('blocks', [(9, 16, ['kkkk kkkk', 'kwnk kwnk', 'kkkk kkkk']), (14, 19, ['wwww', 'rrrr'])])])
fix('Paige (WWE, top roxo)', ops=[
    ('blocks', [(6, 8, ['skkkkskk', 'swnkswnk', 'ssssssss', 'ssssssss', 'ssrrrrss', 'sssrrsss'])])], nobig=True)
fix('Paige (WWE, erguendo o cinturão)', ops=[
    ('blocks', [(10, 11, ['kkkkskk', 'kwnksnk', 'sssssss', 'srrrsss', 'ssrrsss'])])], nobig=True)

# ------------------------------------------------------------------ gráficos e o resto
fix('Seto Kaiba (pixel)', ops=[('blocks', [(9, 17, ['kkk']), (10, 17, ['wbk'])])], nobig=True)
fix('Menina de cabelo preto e mechas azuis (pixel)', ops=[
    ('recolor', 3, 9, 0, 22, [L['G9'], L['A12']], 's'),               # marca d'água
    ('recolor', 19, 25, 0, 22, ['w'], '.')])                          # vãos de fundo entre braços e corpo
_C2 = dict(K=36, dark_frac=0.14, black_L=14.0, sat=1.25)
fix('Guerreiro verde de túnica vermelha (corpo inteiro)', conv=reconv('Guerreiro verde de túnica vermelha (corpo inteiro)', skin=False, **_C2), ops=[
    ('boost', (0, 6, 4, 18), None, [{'rgb': (230, 230, 230), 'tol': 50, 'frac': 0.14, 'letter': 'i'}]),
    ('blocks', [(8, 9, ['k  k'])])])
fix('Chibi de roupa listrada verde e roxa sobre uma tábua', ops=[('smooth', (0, 40, 0, 48), None, 2)])
_EYE_PZ = ['       kkkkkk       ', '    kkkyyyyyykkk    ', '  kkyykkkkkkkkyykkk ', 'kkyykkkkyyyykkkkyyyk', 'kyyykkkyykkyykkkkyyk', 'kyyykkkyywkyykkkkyyk', 'kkkyykkkyyyykkkkyykk', '  kkyyykkkkkkkyyykk ', '    kkkyyyyyyykkk   ', '       kkkkkkk      ']
fix('Quebra-cabeça do Milênio (ilustração)', nobig=True,
    conv=reconv('Quebra-cabeça do Milênio (ilustração)', K=10, dark_frac=0.3, black_L=18.0, sat=1.15, hatch=3, skin=False), ops=[
    ('recolor', 0, 99, 0, 99, [L['H12'], L['M5'], L['M6'], 'j', 'l', 'i'], L['A13']),
    ('blocks', [(18, 14, _EYE_PZ)])])
fix('Boneca de cabelo listrado (chibi)', ops=[
    ('recolor', 0, 99, 0, 99, ['j'], L['E11']),
    ('recolor', 0, 99, 0, 99, ['R'], L['B14']),
    ('recolor', 17, 21, 3, 28, [L['F8']], L['E7']),
    ('recolor', 22, 24, 20, 27, ['r'], 'p'), ('recolor', 22, 25, 8, 14, ['r'], 'p')])
fix('Snoopy de Demolidor (chibi)', ops=[('recolor', 0, 99, 0, 99, ['r'], L['F13'])])


# ====== RODADA 3 (retoques por cima do que já foi gravado) ======
import rev_fix as _RF


def more(name, ops=None, bops=None):
    """acrescenta operações DEPOIS das que o molde já tem (`fix` substitui, `more` soma)"""
    sp = _RF.FIXR.get(name)
    if sp is None: fix(name, ops=ops, bops=bops); return
    sp['ops'] = sp['ops'] + _RF._inject(name, ops or [])
    sp['bops'] = sp['bops'] + _RF._inject(name, bops or [])


more('Toshiro Hitsugaya (Bleach, chibi, katana)', ops=[('recolor', 0, 99, 0, 99, ['s'], L['E11'])])
more('Jushiro Ukitake (Bleach, chibi)', ops=[('recolor', 0, 99, 0, 99, ['s'], L['E11'])])
more('Bartholomew Kuma (One Piece, chibi)', ops=[
    ('blocks', [(10, 20, ['kwwwwwwk']), (11, 20, ['kkkkkkkk kwwwwwk']), (14, 20, ['@@@@@@@@@@@@@']), (15, 33, ['@@@']), (16, 27, ['@ @'])], {'@': 'F7'})])
more('C.C. (Code Geass, desenho sobre a grade)', ops=[
    ('blocks', [(15, 9, ['kkkkk', 'wEkEw', 'wEkEw', ' EEE ']), (16, 20, ['kkkkkk', 'wEEkEw', 'wEkkEw', ' aEEa ']), (19, 11, ['}}']), (19, 19, ['}'])], {'}': 'E11', 'a': 'A6'})])
more('Kenpachi Zaraki (Bleach, chibi)', ops=[('recolor', 0, 99, 0, 99, ['}'], L['G2'])])          # pele da fonte (239,206,171): o E11 ficava rosado e pálido
more('Dracule Mihawk (One Piece, chibi)', ops=[
    ('recolor', 17, 19, 14, 18, [L['E6']], 'k'),
    ('blocks', [(20, 15, ['kkkkkkkk', 'kSwrrwSk', 'kSrkkrSk', ' kkkkkk '])], {'S': 'E14'})],
    bops=[('blocks', [(41, 32, ['  kkkkkkkk  ', ' SSwrrrrwSS ', 'SSwrrkkrrwSS', ' SSSrrrrSSS ', '   kkkkkk   ']), (46, 46, ['kkkkkk', ' wrrw '])], {'S': 'E14'})])
# Goku Black: a limpeza do rosto do 1 placa, escalada, apagava os olhos do grande: o grande parte da conversão original, só com a pele certa
_RF.FIXR['Goku Black Rosé (Dragon Ball, chibi)']['nobig'] = True
more('Goku Black Rosé (Dragon Ball, chibi)', ops=[
    ('recolor', 20, 99, 0, 99, ['s'], L['E11']),
    ('blocks', [(27, 7, ['wwmk']), (27, 11, ['}}}}']), (27, 15, ['kmww'])], {'}': 'E11'})])
fix('Goku Black Rosé (Dragon Ball, chibi) (grande)', ops=[('recolor', 40, 99, 0, 99, ['s'], L['E11'])])
# La La Land à noite: sem o bloco azul claro junto das pernas
more('Casal dançando à noite (La La Land)', ops=[('recolor', 28, 49, 6, 27, ['3', L['D1'], L['D2']], '&')])
# Kuwabara de 1 placa: só as pupilas nos olhos brancos (o grande já tem olhos)
fix('Kazuma Kuwabara (Yu Yu Hakusho, chibi, folha)', nobig=True, ops=[('put', {(17, 12): 'k', (16, 18): 'k', (17, 18): 'k'})])
# Kallen: o oval de 4x5 sem pálpebra lia como um "+": pálpebra preta em cima, brilho e fundo mais claro
_KAL = ['kkkk', 'IwII', 'IIII', 'IIII', 'JJJJ']
more('Kallen Stadtfeld (Code Geass, chibi)', ops=[
    ('stamp', (22.7, 13.16), _KAL, {'I': L['F7'], 'J': L['D14']}), ('stamp', (22.73, 23.12), _KAL, {'I': L['F7'], 'J': L['D14']})])
