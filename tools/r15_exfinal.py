"""Remessa 15 (35 imagens, TODAS ilustrações/artes SEM grade: chibis, retratos, adesivos, emblemas). Rode: BEADPAL=120 python tools/r15_exfinal.py [filtro...]
  -> data/final17_120.json        versões de 1 PLACA (<= 50x50) de TUDO que foi convertido (pedido do usuário: "sempre faça uma versão de uma única placa")
  -> data/final17_multi_120.json  irmãos "(grande)" de 2-4 placas ({"plates": N}) das artes detalhadas (a alocação em mais placas vale a partir desta remessa)

Conversão por illus.convert4 (aproximada; ver §7.6 do CLAUDE.md).
"""
import os, sys, json, glob
os.environ['REMNUM'] = '15'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, outline as O, illus
from flat import render_flat
from palette import sfx
FILES = sorted(glob.glob(os.path.join(os.path.dirname(SP), 'remessas', 'remessa 15', '*.*')))
DK = dict(dark_frac=0.28, dark_L=28.0)
DKM = dict(dark_frac=0.26, dark_L=28.0, ncolors=20)


def plates_of(rows): return -(-max(len(r) for r in rows) // 50) * -(-len(rows) // 50)


def drop_small(maxsz, frac=0.85):
    """apaga pedacinhos soltos (<= maxsz contas) nos últimos (1-frac) das linhas: assinaturas/marcas d'água do artista"""
    import numpy as np, cv2
    def f(rows):
        h = len(rows); m = np.array([[ch != '.' for ch in r] for r in rows], np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        out = [list(r) for r in rows]
        for i in range(1, n):
            x, y, w, hh, a = st[i]
            if a <= maxsz and y >= frac * h:
                for yy in range(y, y + hh):
                    for xx in range(x, x + w):
                        if lab[yy, xx] == i: out[yy][xx] = '.'
        return O.trim([''.join(r) for r in out])
    return f


def clear_box(x0, x1, y0, y1):
    """apaga um retângulo (x0..x1, y0..y1 inclusivos, coordenadas do molde já cortado): assinatura do artista"""
    def f(rows):
        return O.trim([''.join('.' if x0 <= x <= x1 and y0 <= y <= y1 else ch for x, ch in enumerate(r)) if y0 <= y <= y1 else r for y, r in enumerate(rows)])
    return f


def grayfy(rows):
    """cores de croma baixo (o cinza do metal com tom lilás da foto) viram só os cinzas H1-H7"""
    from palette import ALL
    import colorsys
    gray = {c['letter']: c for c in ALL if c['code'] in ('H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7')}
    def lum(c): r, g, b = [int(c['hex'][i:i + 2], 16) for i in (1, 3, 5)]; return 0.299 * r + 0.587 * g + 0.114 * b
    mp = {}
    for c in ALL:
        r, g, b = [int(c['hex'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
        h_, s_, v_ = colorsys.rgb_to_hsv(r, g, b)
        if c['letter'] not in gray and s_ < 0.16 and v_ > 0.25:
            mp[c['letter']] = min(gray.values(), key=lambda gc: abs(lum(gc) - lum(c)))['letter']
    return [''.join(mp.get(ch, ch) for ch in r) for r in rows]


def conv(idx, plates=None, largest=False, post=None, **kw):
    a = dict(DKM if plates else DK); a.update(kw)
    r = illus.convert4(FILES[idx], plates=plates, **a)
    if largest: r = r5.largest(r)
    return post(r) if post else r


# (nome, série, imagem, kwargs da conversão, placas do irmão "(grande)" ou None[, kwargs só do irmão grande])
CFG = [
 # --- Assassination Classroom
 ('Koro-sensei (emblema)', 'Assassination Classroom', 0, {}, None),
 ('Koro-sensei (corpo inteiro)', 'Assassination Classroom', 15, {}, 2),
 ('Nagisa Shiota (Assassination Classroom)', 'Assassination Classroom', 33, {}, 2),
 # --- Attack on Titan
 ('Reiner (chibi, Titã Blindado)', 'Attack on Titan', 3, {}, None),
 ('Titã Blindado e Reiner (chibis)', 'Attack on Titan', 4, dict(bg='flat', tol=60, post=drop_small(14)), 4, dict(post=drop_small(60))),
 ('Reiner Braun (pôster)', 'Attack on Titan', 8, dict(bg='none', dark_frac=0.18, box=(0, 0, 280, 335)), 2, dict(bg='none', dark_frac=0.18)),
 ('Reiner Braun (chibi, braços cruzados)', 'Attack on Titan', 11, {}, None),
 ('Reiner Braun (chibi, versão 2)', 'Attack on Titan', 13, {}, None),
 ('Titã Blindado e Reiner (arte)', 'Attack on Titan', 17, {}, 2),
 ('Eren Jaeger (chibis)', 'Attack on Titan', 22, dict(bg='flat', tol=60, post=drop_small(14)), 4, dict(post=clear_box(36, 51, 80, 86))),
 # --- Mob Psycho 100
 ('Dimple (Mob Psycho 100)', 'Mob Psycho 100', 5, {}, None),
 ('Mob e Dimple (painel de mangá)', 'Mob Psycho 100', 9, dict(box=(20, 20, 580, 700), bg='none'), None),
 ('Mob (Mob Psycho 100, rosto)', 'Mob Psycho 100', 29, {}, None),
 # --- Bleach
 ('Ichigo (máscara de Hollow e espada)', 'Bleach', 6, dict(dark_frac=0.2, thr=235), None),
 ('Ichigo (máscara de Hollow, fundo preto)', 'Bleach', 23, dict(bg='none'), 2),
 # --- Avatar
 ('Aang (chibi, dobrando pedras)', 'Avatar: A Lenda de Aang', 7, {}, 4),
 ('Aang (chibi, saltando)', 'Avatar: A Lenda de Aang', 14, {}, 4),
 ('Aang (corpo inteiro)', 'Avatar: A Lenda de Aang', 18, dict(thr=235), 2),
 ('Aang (quatro elementos, adesivo)', 'Avatar: A Lenda de Aang', 21, {}, 2),
 ('Aang (Estado Avatar, elementos)', 'Avatar: A Lenda de Aang', 24, {}, 4),
 # --- Black Clover
 ('Asta (Black Clover, fundo escuro)', 'Black Clover', 2, dict(bg='none'), 4),
 ('Asta (Black Clover, adesivo preto e branco)', 'Black Clover', 27, {}, 4),
 ('Asta (Black Clover, forma demônio, adesivo)', 'Black Clover', 30, {}, 4),
 ('Chibi demônio de cabelo branco', 'Black Clover', 16, {}, None),
 # --- Dragon Ball / Naruto / Ben 10 / Bob Esponja / One Punch Man
 ('Radar do Dragão (Dragon Ball)', 'Dragon Ball', 10, {}, None),
 ('Esfera do Dragão de 4 estrelas', 'Dragon Ball', 28, {}, None),
 ('Cabaça de areia do Gaara', 'Naruto', 19, {}, None),
 ('Sharingan (Naruto)', 'Naruto', 20, {}, None),
 ('Shuriken (Naruto)', 'Naruto', 26, {}, None),
 ('Bandana da Folha (Naruto)', 'Naruto', 34, dict(post=grayfy, ncolors=6), None),
 ('Omnitrix (Ben 10, ilustração)', 'Ben 10', 12, {}, None),
 ('Omnitrix (Ben 10, vetor)', 'Ben 10', 25, {}, None),
 ('Ben Tennyson (Ben 10)', 'Ben 10', 32, {}, 4),
 ('Bob Esponja (corpo inteiro)', 'Bob Esponja', 31, {}, 2),
 ('Saitama (retrato, One Punch Man)', 'One Punch Man', 1, {}, None),
]

if __name__ == '__main__':
    only = sys.argv[1:]
    one = []; big = []; items = []; items_big = []
    for n, g, idx, kw, pl, *kwb in CFG:
        if only and not any(o in n for o in only): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = conv(idx, **illus.style_defaults(n, kw)); one.append((n, g, r))
            items.append((f'{n[:24]} {idx} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
            if pl:
                rb = conv(idx, plates=pl, **illus.style_defaults(n, (kwb[0] if kwb else kw), big=True)); big.append((f'{n} (grande)', g, rb, {'plates': plates_of(rb)}))
                items_big.append((f'{n[:24]} {idx} {len(rb[0])}x{len(rb)}'.encode('ascii', 'replace').decode(), rb))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa;', len(big), 'irmãos grandes:', [(n[:20], len(r[0]), len(r), o['plates']) for n, g, r, o in big])
    if not only:
        json.dump(one, open(os.path.join(SP, 'data', 'final17' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(big, open(os.path.join(SP, 'data', 'final17_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'r15_x_{k // 12}' + sfx() + '.png'), scale=8, W=1900)
    for k in range(0, len(items_big), 6):
        render_flat(items_big[k:k + 6], os.path.join(OUT, f'r15_big_{k // 6}' + sfx() + '.png'), scale=7, W=1900)
