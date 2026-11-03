"""Gera tools/data/palette.json (as 120 cores do kit) a partir da foto da cartela do anúncio (paleta 120/cartela-120-anuncio.png).

As 24 cores do kit antigo (bandeja do meio à direita da foto) mantêm exatamente os hex, nomes e letras que o app já usava.
As outras 96 são ESTIMADAS: cada cor é amostrada na foto (faixas acima e abaixo do número, onde só há conta) e passa por uma
calibração afim RGB ajustada nas 24 cores conhecidas (erro médio ~7 ΔE em validação cruzada). Quando chegar a cartela de verdade,
corrija os hex direto em data/palette.json (ou pelo "Ajustar cores…" do app) — nada mais precisa mudar.

Cada cor: {code, name, hex, letter, est}. `letter` é o caractere usado nas linhas do templates.js ('.' = vazio):
as 24 letras antigas ficam como estavam; as 96 novas usam j z, A-Z, 0-9, pontuação e letras acentuadas do Latin-1
(sem aspas e sem barra invertida, para caber em strings do JavaScript).

uso:  python tools/make_palette.py          (reescreve data/palette.json e tools/out/palette_120.png com a folha de conferência)
"""
import os, sys, json, colorsys
import numpy as np
from PIL import Image, ImageDraw

SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
PHOTO = os.path.join(ROOT, 'paleta 120', 'cartela-120-anuncio.png')

# --- as 24 cores atuais (ordem da tabela impressa = índices 1..24 do app; NÃO mudar a ordem: projetos salvos usam o índice)
BASE = [('B3', 'Verde claro', '#7FC79C', 'g'), ('C3', 'Azul bebê', '#C3E5F3', 'e'), ('D9', 'Lavanda', '#C8C4E4', 'x'), ('E2', 'Rosa claro', '#F1C4D1', 'q'),
        ('G1', 'Bege', '#E4C7B5', 's'), ('A4', 'Amarelo', '#EBC22F', 'y'),
        ('B5', 'Verde', '#5FA66E', 'f'), ('C5', 'Turquesa', '#55BEDB', 'c'), ('D6', 'Lilás', '#A89BC6', 'v'), ('E4', 'Rosa', '#EA9BB8', 'p'),
        ('G5', 'Salmão', '#D99479', 't'), ('A6', 'Âmbar', '#E9A23B', 'a'),
        ('B8', 'Verde escuro', '#3F8761', 'h'), ('C8', 'Azul', '#6B98D3', 'b'), ('D7', 'Roxo', '#75609A', 'u'), ('F5', 'Vermelho', '#BD3A4B', 'r'),
        ('G7', 'Marrom', '#8F5E50', 'n'), ('A7', 'Laranja', '#EC8546', 'o'),
        ('H1', 'Cinza gelo', '#E4E7EA', 'i'), ('H2', 'Branco', '#FFFFFF', 'w'), ('H3', 'Cinza claro', '#B5B8BE', 'l'), ('H4', 'Cinza', '#8A8D93', 'm'),
        ('H5', 'Cinza escuro', '#5F6065', 'd'), ('H7', 'Preto', '#2E2E32', 'k')]

# --- bandejas da foto (6 colunas x 4 linhas cada; (x, y) = canto da bandeja na imagem de 491x485)
TRAYS = {
    't1': ((262, 48), ['A15 A5 A8 A12 A9 G6', 'A1 B13 B1 B2 B4 B11', 'H12 C1 B16 B6 C15 B15', 'C14 D17 D1 C4 C17 C9']),
    't2': ((56, 190), ['C2 C13 D19 E8 A13 A11', 'C10 C6 D18 E3 A10 G9', 'C11 C7 D21 D13 F13 G13', 'B12 D3 D15 E7 F8 G8']),
    't3': ((264, 190), ['B3 C3 D9 E2 G1 A4', 'B5 C5 D6 E4 G5 A6', 'B8 C8 D7 F5 G7 A7', 'H1 H2 H3 H4 H5 H7']),
    't4': ((56, 334), ['A3 B20 D16 D8 E1 G2', 'B18 B10 D11 D12 E12 G3', 'B14 B19 D2 D20 E5 F10', 'B17 B7 C16 D14 E13 F7']),
    't5': ((264, 334), ['E11 E14 F1 A14 M6 M5', 'E15 F14 F9 F2 G14 M9', 'E9 E6 F12 F3 F11 M12', 'D5 E10 F4 F6 G17 H6']),
}

# --- símbolos das 96 cores novas (todos de 1 caractere, sem " nem \ nem '.')
SYMBOLS = list('jz') + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + list('0123456789') + list('!#$%&()*+,-/:;<=>?@[]^_`{|}~') \
    + [chr(c) for c in range(0xC0, 0xD7)] + [chr(c) for c in range(0xD8, 0xDF)]


def h2rgb(h): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def rgb2lab(rgb):
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    x, y, z = (M @ c) / np.array([0.95047, 1.0, 1.08883])
    f = lambda t: np.cbrt(t) if t > 0.008856 else 7.787 * t + 16 / 116
    return np.array([116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))])


def lab2rgb(L, clip=True):
    fy = (L[0] + 16) / 116; fx = fy + L[1] / 500; fz = fy - L[2] / 200
    f = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    xyz = np.array([f(fx) * 0.95047, f(fy), f(fz) * 1.08883])
    M = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]))
    c = M @ xyz
    c = np.where(c > 0.0031308, 1.055 * np.abs(c) ** (1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255, 0, 255) if clip else c * 255


def rgb2lab_raw(rgb):
    """como rgb2lab, mas aceita RGB fora de 0..255 (resultado da calibração antes de caber no gamut)"""
    c = np.asarray(rgb, float) / 255
    c = np.where(c > 0.04045, ((np.abs(c) + 0.055) / 1.055) ** 2.4 * np.sign(c), c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    x, y, z = np.maximum((M @ c) / np.array([0.95047, 1.0, 1.08883]), 1e-6)
    f = lambda t: np.cbrt(t) if t > 0.008856 else 7.787 * t + 16 / 116
    return np.array([116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))])


def sample(im):
    out = {}
    for t, ((x0, y0), rows) in TRAYS.items():
        for j, row in enumerate(rows):
            for i, code in enumerate(row.split()):
                cx0 = x0 + 4 + i * 33.0; cy0 = y0 + 4 + j * 33.0
                bands = [(cx0 + 4, cy0 + 3, cx0 + 29, cy0 + 9), (cx0 + 4, cy0 + 25, cx0 + 29, cy0 + 31)]   # acima e abaixo do número
                px = np.vstack([im[int(b):int(d), int(a):int(c)].reshape(-1, 3) for a, b, c, d in bands])
                out[code] = np.median(px, axis=0)
    return out


def name_of(hexc):
    """nome aproximado em português a partir do hex (só um rótulo; o código é o que vale). Evita nomes repetidos demais:
    pastel (claro e pouco saturado) e 'preto ...' com a tinta para os quase pretos que não são H7."""
    r, g, b = [v / 255 for v in h2rgb(hexc)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b); h *= 360
    L, a_, b_ = rgb2lab(h2rgb(hexc)); C = (a_ ** 2 + b_ ** 2) ** .5
    if C < 7:
        return 'Branco' if L > 93 else 'Cinza gelo' if L > 85 else 'Cinza claro' if L > 68 else 'Cinza' if L > 50 else 'Cinza escuro' if L > 28 else 'Preto'
    if h < 18 or h >= 340:
        if s >= 0.45: base = 'Coral' if L >= 68 else 'Vermelho' if L >= 45 else 'Vermelho escuro' if L >= 30 else 'Vinho'
        else: base = 'Rosa claro' if L >= 82 else 'Rosa' if L >= 62 else 'Rosa antigo' if L >= 42 else 'Vinho'
        tint = 'avermelhado'
    elif h < 40:
        if s >= 0.55 and L >= 58: base = 'Laranja'
        elif s >= 0.3 and L >= 68: base = 'Salmão'
        elif L < 30: base = 'Marrom escuro'
        elif L < 48: base = 'Marrom'
        else: base = 'Caramelo' if s >= 0.3 else ('Bege' if L >= 75 else 'Bege escuro')
        tint = 'amarronzado'
    elif h < 65:
        if s >= 0.5: base = 'Amarelo claro' if L >= 82 else 'Amarelo' if L >= 62 else 'Mostarda'
        else: base = 'Creme' if L >= 82 else 'Bege' if L >= 62 else 'Oliva'
        tint = 'amarelado'
    elif h < 100: base = 'Verde-limão' if L >= 62 else 'Verde-oliva'; tint = 'esverdeado'
    elif h < 160: base = 'Verde claro' if L >= 82 else 'Verde' if L >= 42 else 'Verde escuro'; tint = 'esverdeado'
    elif h < 195: base = 'Verde-água claro' if L >= 82 else 'Verde-água' if L >= 55 else 'Verde-petróleo'; tint = 'esverdeado'
    elif h < 250: base = 'Azul gelo' if L >= 88 else 'Azul claro' if L >= 68 else 'Azul' if L >= 45 else 'Azul escuro' if L >= 30 else 'Azul-marinho'; tint = 'azulado'
    elif h < 292: base = 'Lilás claro' if L >= 78 else 'Lilás' if L >= 55 else 'Roxo' if L >= 32 else 'Roxo escuro'; tint = 'arroxeado'
    else: base = 'Rosa claro' if L >= 82 else 'Rosa' if L >= 62 else 'Magenta' if L >= 40 else 'Vinho'; tint = 'arroxeado'
    if L < 24: return 'Preto ' + tint                                   # quase preto (G8, B15, B11…), diferente do H7
    if L >= 76 and C < 30 and 'claro' not in base and 'gelo' not in base and base not in ('Creme', 'Bege'): return base + ' pastel'
    return base


def main():
    if '--force' not in sys.argv:
        print('OBSOLETO (2026-11-02): make_palette.py reescreve data/palette.json com as ESTIMATIVAS da foto do anúncio (a paleta SUPERADA). A das contas sem tampa vale: tools/build_bead_palette2.py, CLAUDE.md 7.38. Só roda com --force.')
        return
    im = np.asarray(Image.open(PHOTO).convert('RGB')).astype(float)
    samp = sample(im)
    known = {c: h for c, _, h, _ in BASE}
    ks = list(known)
    X = np.array([samp[k] for k in ks]); Y = np.array([h2rgb(known[k]) for k in ks], float)
    A = np.hstack([X, np.ones((len(X), 1))])
    P = np.linalg.solve(A.T @ A + 1e3 * np.eye(4), A.T @ Y)    # RGB -> RGB afim (ridge leve), ajustado nas 24 cores conhecidas
    est = {}
    for code, v in samp.items():
        if code in known: continue
        p = np.hstack([v, 1.0]) @ P
        # a calibração afim pode sair do gamut e girar o matiz das cores muito claras: trabalha em Lab, limita a luminosidade,
        # puxa metade do caminho de volta ao matiz da foto e reduz o croma (mantendo L e matiz) até a cor caber
        ls, le = rgb2lab(v), rgb2lab_raw(p)
        he = np.arctan2(le[2], le[1]); ce = np.hypot(le[1], le[2]); L2 = min(le[0], 97.0)
        if np.hypot(ls[1], ls[2]) > 6:
            hs = np.arctan2(ls[2], ls[1]); dh = (hs - he + np.pi) % (2 * np.pi) - np.pi; he = he + 0.5 * dh
        for _ in range(60):
            q = lab2rgb([L2, ce * np.cos(he), ce * np.sin(he)], clip=False)
            if q.min() >= -0.5 and q.max() <= 255.5: break
            ce *= 0.95
        p = np.clip(q, 0, 255)
        est[code] = '#%02X%02X%02X' % tuple(int(round(min(255, max(0, c)))) for c in p)
    colors = [dict(code=c, name=n, hex=h, letter=l, est=False) for c, n, h, l in BASE]
    key = lambda c: ('ABCDEFGHM'.index(c[0]), int(c[1:]))
    new = sorted(est, key=key)
    assert len(new) == 96 and len(SYMBOLS) == 96 and len(set(SYMBOLS)) == 96
    seen = {c['name'] for c in colors}
    for code, sym in zip(new, SYMBOLS):
        nm = name_of(est[code])
        if nm in seen: nm = f'{nm} ({code})'          # nome já usado: o código desambigua nas listas
        seen.add(nm)
        colors.append(dict(code=code, name=nm, hex=est[code], letter=sym, est=True))
    assert len({c['code'] for c in colors}) == 120 and len({c['letter'] for c in colors}) == 120
    json.dump({'fonte': 'estimado da foto do anúncio (cartela-120-anuncio.png); as 24 primeiras são as do kit antigo',
               'colors': colors}, open(os.path.join(SP, 'data', 'palette.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # folha de conferência: 10 colunas, nome e código
    W, H = 150, 56
    sheet = Image.new('RGB', (10 * W, 12 * H), (30, 30, 34)); d = ImageDraw.Draw(sheet)
    for i, c in enumerate(colors):
        x, y = (i % 10) * W, (i // 10) * H
        d.rectangle([x + 2, y + 2, x + W - 3, y + H - 3], fill=c['hex'])
        lum = sum(h2rgb(c['hex'])) / 3
        ink = (20, 20, 20) if lum > 140 else (245, 245, 245)
        d.text((x + 8, y + 8), f"{c['code']}  [{c['letter']}]" + ('' if not c['est'] else ' ~'), fill=ink); d.text((x + 8, y + 26), c['name'], fill=ink)
    os.makedirs(os.path.join(SP, 'out'), exist_ok=True)
    sheet.save(os.path.join(SP, 'out', 'palette_120.png'))
    print(len(colors), 'cores gravadas em data/palette.json')


if __name__ == '__main__':
    main()
