"""Remessa 16 (37 imagens, TODAS ilustrações/artes SEM grade: chibis, retratos, adesivos, emblemas). Rode: BEADPAL=120 python tools/r16_exfinal.py [filtro...]
  -> data/final18_120.json        versões de 1 PLACA (<= 50x50) de TUDO que foi convertido (pedido do usuário: "sempre faça uma versão de uma única placa")
  -> data/final18_multi_120.json  irmãos "(grande)" de 2-4 placas ({"plates": N}) das artes detalhadas (a alocação em mais placas vale a partir desta remessa)

Conversão por illus.convert4 (aproximada; ver §7.6 do CLAUDE.md).
"""
import os, sys, json, glob
os.environ['REMNUM'] = '16'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, outline as O, illus
from flat import render_flat
from palette import sfx
FILES = sorted(glob.glob(os.path.join(os.path.dirname(SP), 'remessas', 'remessa 16', '*.*')))
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


# DEIXADA DE FORA: idx 9 (Kaiju nº 8 em armadura branca/cinza sobre fundo branco: as linhas finas somem e o rosto vira mancha, nem com 100 contas fica reconhecível)
# (nome, série, imagem, kwargs da conversão, placas do irmão "(grande)" ou None[, kwargs só do irmão grande])
CFG = [
 # --- Chainsaw Man
 ('Denji e Pochita (Chainsaw Man)', 'Chainsaw Man', 0, {}, 4),
 ('Denji (Chainsaw Man, chibi)', 'Chainsaw Man', 18, {}, None),
 ('Power (Chainsaw Man, chibi)', 'Chainsaw Man', 23, {}, None),
 ('Homem-Motosserra (Chainsaw Man, adesivo)', 'Chainsaw Man', 12, {}, 4),
 # --- Carros
 ('Mate (Carros)', 'Carros', 1, dict(dark_frac=0.45, dark_L=18.0), 2),
 ('Relâmpago McQueen (ilustração)', 'Carros', 8, dict(thr=190), 2),
 # --- Chaves
 ('Chaves no barril (adesivo)', 'Chaves e Chapolin', 7, dict(peel=1.0), 2),
 ('Kiko (Chaves, ilustração)', 'Chaves e Chapolin', 16, dict(largest=True), 2),
 ('Seu Barriga (Chaves)', 'Chaves e Chapolin', 28, {}, 2),
 # --- Coragem
 ('Coragem (ilustração, assustado)', 'Coragem, o Cão Covarde', 33, dict(dark_frac=0.4), None),
 # --- D.Gray-man
 ('Allen Walker (retrato, D.Gray-man)', 'D.Gray-man', 2, dict(bg='none'), 4),
 ('Allen Walker (sorrindo, D.Gray-man)', 'D.Gray-man', 14, dict(box=(0, 0, 400, 368), thr=240), 4),
 ('Allen Walker (chibi, com Timcanpy)', 'D.Gray-man', 35, dict(thr=240), 4),
 # --- Code Geass
 ('Olho do Geass (Code Geass)', 'Code Geass', 3, dict(bg='none'), 2),
 ('Olho do Geass (brilhando, fundo preto)', 'Code Geass', 30, dict(bg='flat', tol=25), None),
 ('Sigilo do Geass (vermelho)', 'Code Geass', 20, {}, None),
 ('Sigilo do Geass (vinho)', 'Code Geass', 21, {}, None),
 ('Sigilo do Geass (branco, fundo preto)', 'Code Geass', 34, dict(bg='flat', tol=30), None),
 ('Lelouch (retrato, olho do Geass)', 'Code Geass', 24, dict(bg='none'), 4),
 ('Lelouch (chibi, traje de Zero)', 'Code Geass', 29, {}, None),
 ('Lelouch (chibi, traje imperial branco)', 'Code Geass', 36, {}, 4),
 ('Zero (Code Geass, chibi)', 'Code Geass', 5, {}, None),
 ('C.C. (Code Geass, chibi)', 'Code Geass', 19, {}, None),
 ('Guren (Code Geass, mecha de asas rosas)', 'Code Geass', 10, {}, 2),
 # --- Kaiju nº 8
 ('Kaiju nº 8 (chibi, sentado)', 'Kaiju nº 8', 4, {}, 4),
 ('Kaiju nº 8 (forma kaiju, busto)', 'Kaiju nº 8', 31, {}, 4),
 ('Kaiju nº 8 (chibi, adesivo)', 'Kaiju nº 8', 25, {}, 2),
 ('Kaiju nº 8 (caveira, círculo)', 'Kaiju nº 8', 13, {}, None),
 ('Kaiju de juba branca (chibi)', 'Kaiju nº 8', 17, {}, None),
 ('Kikoru Shinomiya (Kaiju nº 8, chibi)', 'Kaiju nº 8', 11, dict(post=drop_small(30, 0.9)), None),
 ('Mina Ashiro (Kaiju nº 8, chibi)', 'Kaiju nº 8', 15, dict(thr=245, post=drop_small(30, 0.9)), None),
 ('Kafka Hibino (Kaiju nº 8, chibi)', 'Kaiju nº 8', 22, dict(post=drop_small(30, 0.9)), None),
 ('Reno Ichikawa (Kaiju nº 8, chibi)', 'Kaiju nº 8', 26, dict(post=drop_small(30, 0.9)), None),
 # --- sem franquia identificada
 ('Chibi robô azul e dourado', 'Outros', 6, dict(thr=240, largest=True), None),
 ('Bolinhas aladas, preta e dourada', 'Outros', 27, dict(thr=240), None),
 ('Figura de máscara branca em chamas vermelhas', 'Outros', 32, dict(thr=190), None),
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
        json.dump(one, open(os.path.join(SP, 'data', 'final18' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(big, open(os.path.join(SP, 'data', 'final18_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'r16_x_{k // 12}' + sfx() + '.png'), scale=8, W=1900)
    for k in range(0, len(items_big), 6):
        render_flat(items_big[k:k + 6], os.path.join(OUT, f'r16_big_{k // 6}' + sfx() + '.png'), scale=7, W=1900)
