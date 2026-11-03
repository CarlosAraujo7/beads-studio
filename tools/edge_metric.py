"""MÉTRICA DE DETALHE (2026-11-02): o dono viu as miniaturas dos moldes "perderem qualidade" e as cores ficarem "homogêneas demais, ruim de identificar as coisas" com a paleta medida nas contas.
Mede isso: em cada molde, para cada par de contas vizinhas (cima/baixo/esquerda/direita) de LETRAS diferentes (uma borda do desenho), o ΔE2000 entre as duas cores mostradas.
  - contraste médio das bordas (ponderado pelo nº de bordas);
  - "bordas apagadas": bordas que ERAM visíveis na paleta antiga (ΔE >= 12) e agora ficam fracas (ΔE < 8);
  - "tons fundidos": pares de letras do molde que ficaram com ΔE < 5 entre si (antes >= 8).
Compara: ANTIGA (palette-pre-contas.json) | NOVA 100% (hex_foto) | NOVA atual (palette.json, vivacidade 70%) | NOVA atual + troca de cores (remap3 e remap4).
uso: python tools/edge_metric.py            -> tabela geral e os 15 moldes mais afetados;   python tools/edge_metric.py --json  -> tools/out/edge_metric.json"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np
import remap_cores as RC, tplfile
import palette_tone as PT

PAL_NEW = json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']
LET = [c['letter'] for c in RC.NEW]                     # a ordem das 120 letras (a mesma nas 3 paletas)


def de_matrix(hexes):
    labs = np.array([PT.rgb2lab(PT.hex2rgb(h)) for h in hexes])
    M = np.zeros((len(hexes), len(hexes)))
    for i in range(len(hexes)): M[i] = np.ravel(RC.r5._de2000(labs[i], labs))
    return M


PALS = {
    'antiga': [c['hex'] for c in RC.OLD],
    'nova100': [c.get('hex_foto') or c['hex'] for c in PAL_NEW],
    'nova70': [c['hex'] for c in PAL_NEW],
}
MATS = {k: de_matrix(v) for k, v in PALS.items()}
IDX = {l: i for i, l in enumerate(LET)}


def edges(rows):
    """{(i, j): n} pares (i<j) de índices de letra vizinhas de letras diferentes; n = nº de bordas entre elas"""
    H, W = len(rows), len(rows[0]); out = {}
    for y in range(H):
        for x in range(W):
            a = rows[y][x]
            if a == '.': continue
            for dy, dx in ((0, 1), (1, 0)):
                yy, xx = y + dy, x + dx
                if yy < H and xx < W:
                    b = rows[yy][xx]
                    if b != '.' and b != a:
                        i, j = IDX[a], IDX[b]
                        if i > j: i, j = j, i
                        out[(i, j)] = out.get((i, j), 0) + 1
    return out


def metrics(rows, mat_new, mat_old=None, ed=None, mapping=None):
    """contraste médio das bordas, % de bordas apagadas, nº de pares de tons fundidos. `mapping` = {letra antiga: letra nova} (a troca de cores); as bordas vêm do molde ANTIGO."""
    mat_old = MATS['antiga'] if mat_old is None else mat_old
    ed = edges(rows) if ed is None else ed
    if not ed: return dict(mean=0, lost=0, merged=0, n=0)
    tot = sum(ed.values()); s = 0.0; lost = 0; merged = 0
    for (i, j), n in ed.items():
        a, b = (i, j) if mapping is None else (IDX[mapping.get(LET[i], LET[i])], IDX[mapping.get(LET[j], LET[j])])
        dn = mat_new[a, b]; do = mat_old[i, j]
        s += n * dn
        if do >= 12 and dn < 8: lost += n
        if do >= 8 and dn < 5: merged += 1
    return dict(mean=s / tot, lost=100.0 * lost / tot, merged=merged, n=tot)


if __name__ == '__main__':
    items = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
    res = {}
    for k in ('antiga', 'nova100', 'nova70'): res[k] = []
    res['remap3'] = []
    rows_all = []
    for t in items:
        rows = t['rows']; ed = edges(rows)
        if not ed: continue
        m3 = RC.remap3(rows)
        rec = dict(id=t['id'], name=t['name'], cat=t.get('cat'))
        for k in ('antiga', 'nova100', 'nova70'): rec[k] = metrics(rows, MATS[k], ed=ed)
        rec['remap3'] = metrics(rows, MATS['nova70'], ed=ed, mapping=m3)
        rows_all.append(rec)
    print('moldes com bordas:', len(rows_all))
    for k in ('antiga', 'nova100', 'nova70', 'remap3'):
        mean = np.mean([r[k]['mean'] for r in rows_all]); lost = np.mean([r[k]['lost'] for r in rows_all]); mg = np.mean([r[k]['merged'] for r in rows_all])
        print('%-8s contraste médio das bordas %5.1f | bordas apagadas %5.1f%% | pares de tons fundidos por molde %4.1f' % (k, mean, lost, mg))
    worst = sorted(rows_all, key=lambda r: -r['nova70']['lost'])[:15]
    print('\nmais afetados (nova70): % de bordas apagadas  [depois da troca remap3]')
    for r in worst: print('  %5.1f%% [%5.1f%%]  %s' % (r['nova70']['lost'], r['remap3']['lost'], r['name'][:60]))
    if '--json' in sys.argv: json.dump(rows_all, open(os.path.join(HERE, 'out', 'edge_metric.json'), 'w', encoding='utf-8'), ensure_ascii=False)
