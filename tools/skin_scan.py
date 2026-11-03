"""LEVANTAMENTO DA COR DE PELE/ROSTO DO CATÁLOGO (2026-11-03, pedido do dono: "a grande maioria tem cor de rosto e pele bege claro, verifique os personagens e alinhe isso").
SÓ LÊ o catálogo (nada é gravado). Para cada molde acha o ROSTO (uma região de contas de "pele" pela cor ANTIGA da letra, com pelo menos 2 buracos pequenos dentro: olhos, boca)
e diz qual letra/conta é a pele dominante, que cor ela mostra hoje e a que família isso pertence.
uso:  python tools/skin_scan.py [--json tools/out/skin_scan.json]      (resumo no terminal)
Também importado por tools/skin_align.py (`scan_mold`)."""
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np
import remap_cores as RC, palette_tone as PT, tplfile

T = os.path.join(ROOT, 'templates.js')
NEWB = RC.NEW_BY_L; OLDB = RC.OLD_BY_L
_SK = {l: RC.is_skin_old(l) for l in OLDB}
_DARK_OLD = {l: RC.lab(RC.OLD_RGB[l])[0] < 38 for l in OLDB}


def labn(letter): return RC.lab(PT.hex2rgb(NEWB[letter]['hex']))


def hue(l): return float(np.degrees(np.arctan2(l[2], l[1])) % 360)


def comps(mask, conn=4):
    h, w = mask.shape; seen = np.zeros_like(mask, bool); out = []
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if conn == 8 else [])
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                st = [(y, x)]; seen[y, x] = True; cells = []
                while st:
                    cy, cx = st.pop(); cells.append((cy, cx))
                    for dy, dx in nb:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((ny, nx))
                out.append(cells)
    return out


def scan_mold(rows):
    """devolve dict(face=bool, skin_letters={letra: contas no rosto}, face_area, holes) ou face=False"""
    h, w = len(rows), len(rows[0]); g = np.array([list(r) for r in rows])
    skin = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            c = g[y, x]
            if c != '.' and _SK.get(c): skin[y, x] = True
    best = None
    for cells in comps(skin, 4):
        if len(cells) < 12: continue
        m = np.zeros((h, w), bool)
        for y, x in cells: m[y, x] = True
        ys = [c[0] for c in cells]; xs = [c[1] for c in cells]; y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        # buracos: não-pele dentro da caixa que não alcançam a borda da caixa passando por não-pele
        sub = ~m[y0:y1 + 1, x0:x1 + 1]; sh, sw = sub.shape
        outside = np.zeros_like(sub, bool); st = []
        for y in range(sh):
            for x in (0, sw - 1):
                if sub[y, x] and not outside[y, x]: outside[y, x] = True; st.append((y, x))
        for x in range(sw):
            for y in (0, sh - 1):
                if sub[y, x] and not outside[y, x]: outside[y, x] = True; st.append((y, x))
        while st:
            cy, cx = st.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < sh and 0 <= nx < sw and sub[ny, nx] and not outside[ny, nx]: outside[ny, nx] = True; st.append((ny, nx))
        holes = sub & ~outside
        hc = [c for c in comps(holes, 4) if len(c) <= 14]
        if len(hc) >= 2 and (best is None or len(cells) > best[0]): best = (len(cells), cells, len(hc))
    if best is None: return dict(face=False)
    cnt = collections.Counter(g[y, x] for y, x in best[1])
    return dict(face=True, face_area=best[0], holes=best[2], skin_letters=dict(cnt), cells=best[1])


def family(letter):
    """família da cor que a letra mostra HOJE: o que o dono vê no rosto"""
    L, a, b = labn(letter); C = (a * a + b * b) ** .5; h = hue((L, a, b))
    if L >= 90 and C < 12: return 'branco-rosado'
    if C > 40: return 'laranja/ouro vivo'
    if 8 <= h < 40 and C >= 14: return 'rosa/salmão'
    if 40 <= h < 66: return 'bege-pêssego' if L >= 80 else 'caramelo/médio'
    if 66 <= h < 92: return 'bege-creme' if L >= 82 else 'oliva/médio'
    if 92 <= h < 125: return 'creme-oliva'
    return 'outra'


def main():
    d = tplfile.parse(T); res = {}
    for it in d['items']:
        s = scan_mold(it['rows'])
        if not s['face']: continue
        tot = sum(s['skin_letters'].values()); dom = max(s['skin_letters'], key=s['skin_letters'].get)
        res[it['id']] = dict(name=it['name'], cat=it['cat'], dom=dom, code=NEWB[dom]['code'], hex=NEWB[dom]['hex'], fam=family(dom), area=s['face_area'], holes=s['holes'],
                             letters={l: [NEWB[l]['code'], n] for l, n in sorted(s['skin_letters'].items(), key=lambda kv: -kv[1])}, dom_share=round(s['skin_letters'][dom] / tot, 2))
    print('moldes:', len(d['items']), '| com rosto detectado:', len(res))
    print('\nPor conta dominante da pele (cor de hoje):')
    c1 = collections.Counter((v['code'], v['hex']) for v in res.values())
    for (code, hx), n in c1.most_common(30): print('  %-4s %s  %3d moldes  %s' % (code, hx, n, [NEWB[l]['name'] for l in NEWB if NEWB[l]['code'] == code][0]))
    print('\nPor família:')
    for f, n in collections.Counter(v['fam'] for v in res.values()).most_common(): print('  %-22s %d' % (f, n))
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]; json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); print('gravado', out)


if __name__ == '__main__':
    main()
