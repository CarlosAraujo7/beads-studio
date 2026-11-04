"""Remessa 29, 2ª revisão (retorno do dono no chat, 2026-11-04): monta data/final31_raw_120.json a partir da versão que está no CATÁLOGO
(data/final31_raw_v6_120.json) e só muda o que ele pediu, pelo nome:
  - Cavaleiros com a pele da cor da armadura (SKIN6 do r29_exfinal): o rosto é inundado NA ARTE a partir das sementes e pintado de bege POR CIMA do molde do catálogo
    (a conversão nova serve só para a geometria e a arte: reconverter mudaria algumas contas fora do rosto, porque o k-means varia conforme os moldes convertidos antes);
  - retoques à mão (TOUCH6: olhos, tiara dos dois Seiya, rosto do Mayuri, a gata Turbo Granny) também por cima do molde do catálogo;
  - REDO = refeitos por inteiro (conversão nova + TOUCH6): o Grimmjow (a roupa branca virava pele).
Tudo o mais fica IGUAL ao catálogo. Depois:  BEADS_ALTERAR_EXISTENTES=1 python tools/r29_replace.py --de data/final31_raw_v6_120.json --copia pre-r29-rev2.js
  BEADPAL=120 python tools/r29_rev2.py            monta o JSON e diz o que mudou (nada é gravado no catálogo)"""
import os, sys, json
os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r29_exfinal as Z
import illus6, loose
from r29_eyesheet import offset

D = os.path.join(HERE, 'data')
REDO = {'Grimmjow (Bleach, chibi)'}


def skin_patch(name, rows6):
    n, g, idx, fn, grp = next(c for c in Z.CFG if c[0] == name)
    Z.CUR[0] = name
    fn()                                                       # só para a geometria (LAST_GEOM) e a arte preparada
    G6 = dict(illus6.LAST_GEOM)
    dy, dx = offset(G6['rows'], rows6)
    nh, nw, top, left = G6['nh'], G6['nw'], G6['top'], G6['left']
    H2, W2 = nh + 2, nw + 2
    G = [['.'] * W2 for _ in range(H2)]
    for y, r in enumerate(rows6):
        for x, ch in enumerate(r):
            gy, gx = y + dy + top, x + dx + left
            if 0 <= gy < H2 and 0 <= gx < W2: G[gy][gx] = ch
    s = Z.SKIN6[name]
    sh = s.get('face_shadow', 'E14')
    G2 = illus6._face_skin6(G, s['face_seeds'], s.get('face_box'), s.get('face_tol', 36), Z.L[s.get('face_main', 'E11')], Z.L[sh] if sh else None,
                            s.get('face_dark', 6.0), G6['raw'], G6['fg'], nh, nw, absorb={Z.L[c] for c in s.get('face_absorb', ())})
    out = [''.join(G2[y + dy + top][x + dx + left] for x in range(len(rows6[0]))) for y in range(len(rows6))]
    return Z.no_mouth(out)                                     # como no fluxo normal: com o rosto de pele, a boca (se houver) sai


def main():
    v6 = json.load(open(os.path.join(D, 'final31_raw_v6_120.json'), encoding='utf-8'))
    by6 = {x[0]: x for x in v6}
    out = []; changed = []
    for n, g, idx, fn, grp in Z.CFG:
        if n not in by6: continue
        rows6 = by6[n][2]
        if n in REDO:
            Z.CUR[0] = n; r5_skin = Z.r5.SKIN_ON; Z.r5.SKIN_ON = False
            rows = Z.touch6(n, fn()); Z.r5.SKIN_ON = r5_skin
        elif n in Z.SKIN6: rows = Z.touch6(n, skin_patch(n, rows6))
        elif n in Z.TOUCH6: rows = Z.touch6(n, rows6)
        else: rows = rows6
        if rows != rows6:
            same = len(rows) == len(rows6) and len(rows[0]) == len(rows6[0])
            d = sum(1 for a, b in zip(''.join(rows), ''.join(rows6)) if a != b) if same else -1
            changed.append((n, d, len(rows[0]), len(rows), loose.loose_count(rows)))
        out.append([n, by6[n][1], rows])
    json.dump(out, open(os.path.join(D, 'final31_raw_120.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(out), 'moldes no JSON;', len(changed), 'mudam em relação ao catálogo:')
    for n, d, w, h, lc in changed: print(f'  {d:4d} contas  {w}x{h}  soltas={lc}  {n}')


if __name__ == '__main__':
    main()
