"""Correção de 3 moldes dos Cavaleiros do Zodíaco depois do feedback do usuário (2026-10-30), que achou que a simetria COMPLETA não ficou boa neles:
  - shiryu-de-dragao-chibi        olhos "estranhos": a conversão tinha comido os olhos (preto), então aqui eles são DESENHADOS à mão (esclera, íris cinza, pupila preta, brilho branco, pálpebra preta)
                                   e as gemas vermelhas do diadema também; o resto é o espelho de antes (metade esquerda do molde original).
  - shun-de-andromeda-chibi       parecia "espelhado": a barra de cabelo (mechas) do espelho completo ficava igual dos dois lados. Aqui só o capacete/olhos/corpo ficam simétricos e o cabelo mantém a assimetria natural.
  - shun-de-andromeda-chibi-corpo-inteiro   o usuário aprovou a versão ORIGINAL; só revisão leve (sem espelhar, ele disse que não precisa de frente).
Originais: tools/backups/pre-cav-simetria.js. uso:  python tools/cav_chibis_fix.py [--dry] [--only shiryu|shun|shunfull]   (prévias em tools/out/cavfix_*.png)
"""
import os, sys, glob, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import tplfile, mirror, loose
from flat import render_flat

ORIG = os.path.join(HERE, 'backups', 'pre-cav-simetria.js')


def orig_rows(i):
    return next(x for x in tplfile.parse(ORIG)['items'] if x['id'] == i)['rows']


def patch(rows, cells):
    """cells = {(y, x): letra}; devolve novas linhas"""
    g = [list(r) for r in rows]
    for (y, x), ch in cells.items(): g[y][x] = ch
    return [''.join(r) for r in g]


def block(rows, y0, x0, lines):
    """cola um bloco de texto (lista de strings; ' ' = não mexe) em (y0, x0)"""
    g = [list(r) for r in rows]
    for j, ln in enumerate(lines):
        for i, ch in enumerate(ln):
            if ch != ' ': g[y0 + j][x0 + i] = ch
    return [''.join(r) for r in g]


def render_grid(rows, path, scale=18, title=''):
    """renderiza o molde com régua (números a cada 5 linhas/colunas) e linhas de grade leves, para desenhar/conferir à mão"""
    from PIL import Image, ImageDraw
    from flat import L2HEX
    h, w = len(rows), len(rows[0]); m = 26
    im = Image.new('RGB', (w * scale + m + 6, h * scale + m + 6 + (14 if title else 0)), (60, 60, 66)); d = ImageDraw.Draw(im)
    oy = m + (14 if title else 0)
    if title: d.text((m, 2), title, fill=(255, 255, 255))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            x0, y0 = m + i * scale, oy + j * scale
            c = ((200, 200, 205) if (i + j) % 2 == 0 else (225, 225, 228)) if ch == '.' else L2HEX[ch]
            d.rectangle((x0, y0, x0 + scale - 1, y0 + scale - 1), fill=c)
    for i in range(0, w + 1):
        d.line((m + i * scale, oy, m + i * scale, oy + h * scale), fill=(255, 0, 255) if i % 5 == 0 else (120, 120, 130), width=1)
        if i % 5 == 0 and i < w: d.text((m + i * scale + 2, oy - 12), str(i), fill=(255, 255, 0))
    for j in range(0, h + 1):
        d.line((m, oy + j * scale, m + w * scale, oy + j * scale), fill=(255, 0, 255) if j % 5 == 0 else (120, 120, 130), width=1)
        if j % 5 == 0 and j < h: d.text((2, oy + j * scale + 2), str(j), fill=(255, 255, 0))
    im.save(path)


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SHIRYU (chibi, diadema de dragão). Metade esquerda do original + olhos desenhados + gemas vermelhas, depois espelho em torno do eixo entre as colunas 19 e 20 (a2=39).
# Olho esquerdo = colunas 10..19, linhas 22..25 (coordenadas do molde ORIGINAL): w esclera, d íris cinza, k pupila/pálpebra, brilho branco na pupila (voltado para o centro nos dois olhos).
SHIRYU_EYE = ['kwwdddkkkk',
              'kwdkwddkkk',
              'swwdkkdwkk',
              '.swwddwsjk']
SHIRYU_GEM = [(15, 17), (16, 17), (17, 17)]            # gema vermelha do diadema (col. 17, linhas 15-17); a do outro lado vem do espelho (col. 22)


def fix_shiryu():
    rows = orig_rows('shiryu-de-dragao-chibi')
    rows = block(rows, 22, 10, SHIRYU_EYE)
    rows = patch(rows, {c: 'r' for c in SHIRYU_GEM})
    new = mirror.mirror(rows, 39, 'L')
    return new


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SHUN (chibi, capacete). O espelho completo (a2=37) deixou o cabelo e a mecha da franja iguais dos dois lados e os olhos viraram uma "máscara" preta: ficou "espelhado".
# Aqui a simetria é só do CAPACETE (chifres e cristal: letras $ x w i nas linhas 0-23, eixo a2=36 = coluna 18, o centro do rosto na fonte) e dos OLHOS (desenhados, esquerdo copiado espelhado);
# o cabelo, a mecha da franja e a armadura ficam como no original (assimétricos como na ilustração).
HELM = set('$xwi')
SHUN_EYE = ['kkkkkk',                  # linha 24 (pálpebra)        colunas 10..15
            'wNkkwN',                  # 25
            'wNkkkN',                  # 26
            'wNNNNN',                  # 27
            'sswwws']                  # 28


def fix_shun():
    O = orig_rows('shun-de-andromeda-chibi'); A2 = 36
    g = [list(r) for r in O]; W = len(O[0])
    # 1) capacete: a peça do capacete que existe num dos lados vale para os dois (preferindo a metade esquerda)
    for y in range(0, 24):
        for x in range(0, A2 // 2):
            xm = A2 - x
            if xm >= W: continue
            L, R = O[y][x], O[y][xm]
            if L in HELM: g[y][xm] = L
            elif R in HELM: g[y][x] = R
    rows = [''.join(r) for r in g]
    # 2) olhos: bloco esquerdo (cols 10..15, linhas 24..28) e o espelho dele (cols 21..26); a mecha da franja (verdes claros S/K a partir da col. 15) é do original e fica
    strand = {(y, x): O[y][x] for y in range(22, 32) for x in range(15, 22) if O[y][x] in 'SK'}
    rows = block(rows, 24, 10, SHUN_EYE)
    g = [list(r) for r in rows]
    for j, ln in enumerate(SHUN_EYE):
        for i, ch in enumerate(ln):
            if ch != ' ': g[24 + j][A2 - (10 + i)] = ch
    for (y, x), ch in strand.items(): g[y][x] = ch
    for x in (8, 28): g[19][x] = 'r'                       # ornamento vermelho do capacete, um de cada lado (a fonte tem os dois; o original só tinha o direito)
    return [''.join(r) for r in g]


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SHUN (chibi, corpo inteiro). O usuário gostou da versão original; ela só tinha problemas de COR (armadura quase preta em vez de magenta, rosto sem olhos). A forma (silhueta) é a mesma:
# mesma máscara e mesmo tamanho (26x49), reconvertida com contorno mais exigente (dark_frac 0,40 / dark_L 16) e mais saturação (1,4) para a armadura e as calças saírem rosa/lilás, e o ROSTO é
# redesenhado à mão (olhos azul-petróleo com esclera branca, pálpebras pretas, mecha da franja entre os olhos). Fonte: remessa 14 idx 5 (400x600).
SHUNFULL_FACE = {          # a-linhas 16..19, colunas 7..18; ' ' = fica como a conversão
    16: 'ggaabassggga',
    17: 'gwtaabsswtwg',
    18: 'gwTbaasswTwS',
    19: 'SsTssaasssSS',
}
ROLE = {'g': 'H7', 'w': 'H2', 't': 'C15', 'T': 'B7', 'a': 'B17', 'b': 'B4', 's': 'G2', 'S': 'G3'}


def _hsv(letter):
    import colorsys
    from palette import HEX_BY_LETTER
    h = HEX_BY_LETTER[letter].lstrip('#'); r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    hh, s_, v = colorsys.rgb_to_hsv(r, g, b); return hh * 360, s_, v


def fix_shunfull():
    """original + armadura recolorida + rosto redesenhado (ver o cabeçalho): onde o original tem o vinho quase preto (F7/F8) da armadura e a reconversão mais saturada tem vermelho/rosa, vale o vermelho/rosa;
    os contornos pretos, o cabelo e a silhueta ficam exatamente como o usuário aprovou."""
    import r5, illus
    from palette import ALL
    code = {p['code']: p['letter'] for p in ALL}
    r5.SKIN_ON = True
    src = sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa 14', '*.*')))[5]
    base = illus.convert4(src, dark_frac=0.40, dark_L=16.0, sat=1.4, ncolors=22)       # mesma máscara (777 contas) e mesmo tamanho do original
    orig = orig_rows('shun-de-andromeda-chibi-corpo-inteiro')
    assert len(base) == len(orig) and len(base[0]) == len(orig[0])
    dark_red = {code['F7'], code['F8']}
    def reddish(l):
        h, s_, v = _hsv(l); return (h >= 320 or h <= 20) and s_ >= 0.25 and v >= 0.45
    g = [list(r) for r in orig]
    for y in range(20, len(orig)):
        for x in range(len(orig[0])):
            if orig[y][x] in dark_red and base[y][x] != '.' and reddish(base[y][x]): g[y][x] = base[y][x]
    for y, ln in SHUNFULL_FACE.items():
        for i, ch in enumerate(ln):
            if ch != ' ': g[y][7 + i] = code[ROLE[ch]]
    return [''.join(r) for r in g]


if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    out = {}
    if only in (None, 'shiryu'): out['shiryu-de-dragao-chibi'] = fix_shiryu()
    if only in (None, 'shun'): out['shun-de-andromeda-chibi'] = fix_shun()
    if only in (None, 'shunfull'): out['shun-de-andromeda-chibi-corpo-inteiro'] = fix_shunfull()
    for i, new in out.items():
        old = orig_rows(i)
        render_grid(new, os.path.join(HERE, 'out', 'cavfix_new_%s.png' % i), scale=18, title=i)
        render_flat([('ORIGINAL', old), ('NOVO', new)], os.path.join(HERE, 'out', 'cavfix_cmp_%s.png' % i), scale=14, W=1300)
        print(i, len(new[0]), len(new), 'soltas', loose.loose_count(new))
        assert not loose.loose_count(new) and max(len(new[0]), len(new)) <= 100
    if '--apply' in sys.argv:
        # só troca se o molde do catálogo ainda é o que EU deixei (o original, ou o espelho completo da rodada anterior); se o usuário mexeu no app, pula e avisa
        import apply_cav_symmetry as AS
        TPL = os.path.join(ROOT, 'templates.js'); d = tplfile.parse(TPL); by = {it['id']: it for it in d['items']}
        shutil.copy(TPL, os.path.join(HERE, 'backups', 'pre-cav-fix.js'))
        for i, new in out.items():
            cur = by[i]['rows']; old = orig_rows(i)
            known = [old]
            if i in AS.OLD_PICK: known.append(mirror.mirror(old, *AS.OLD_PICK[i]))
            if cur == new: print('  =', i, '(já aplicado)'); continue
            if cur not in known: print('  PULEI', i, '(o desenho do catálogo não é o que eu tinha gravado: você ajustou no app?)'); continue
            by[i]['rows'] = new; print('  trocado', i)
        tplfile.write(TPL, d['legend'], d['cfg'], d['items'], d.get('removed')); print('gravado')
