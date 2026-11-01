"""Acha, para cada molde do catálogo SEM fonte conhecida (remessas 1-4, feitos pelo pipeline antigo e depois retocados), a imagem de origem
mais provável nas pastas remessa 1..4 (comparação tolerante de forma/cor, layoutsim) e grava out/match_old.json:
    {nome do molde: [[remessa, idx, nota], ...]}      (as 3 melhores)
A conversão automática de cada imagem (exact6, 24 cores) é guardada em out/conv24_old.json para não repetir.

uso:  python tools/match_old.py            (demora alguns minutos)
"""
import os, sys, json, glob
SP = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SP)
sys.path.insert(0, SP)
os.environ['REMNUM'] = '1'
import r6, tplfile, layoutsim as L

cat = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
final = {}
for k in [7, 8, 9, 10, 11, 12, 13, 14]:
    for n, g, r in json.load(open(os.path.join(SP, 'data', f'final{k}.json'), encoding='utf-8')): final[n] = 1
for n, g, r in json.load(open(os.path.join(SP, 'data', 'final_outros.json'), encoding='utf-8')): final[n] = 1
for n, g, r in json.load(open(os.path.join(SP, 'data', 'final15_120.json'), encoding='utf-8')): final[n] = 1
targets = [t for t in cat if t['name'] not in final and not t['name'].endswith('(1 placa)')]
print(len(targets), 'moldes sem fonte conhecida', flush=True)

cache_path = os.path.join(SP, 'out', 'conv24_old.json')
conv = json.load(open(cache_path, encoding='utf-8')) if os.path.exists(cache_path) else {}
for rem in (1, 2, 3, 4):
    r6.FILES = sorted(glob.glob(os.path.join(ROOT, 'remessas', f'remessa {rem}', '*.*')))
    for i in range(len(r6.FILES)):
        key = f'{rem}:{i}'
        if key in conv: continue
        try:
            rows = r6.exact6(i)
            if not rows or len(rows) * len(rows[0]) < 6 or len(rows) > 400: rows = None
        except Exception:
            rows = None
        conv[key] = rows
    print('remessa', rem, 'convertida', flush=True)
json.dump(conv, open(cache_path, 'w', encoding='utf-8'))
import numpy as np
def prep(rows):
    sh, col = L.thumb(rows); return sh > 0, col
tc = {k: prep(r) for k, r in conv.items() if r}
def fast(a, b):
    sa, ca = a; sb, cb = b
    both = sa & sb; union = sa | sb
    if union.sum() == 0 or both.sum() == 0: return 0.0
    shape = both.sum() / union.sum()
    cd = np.linalg.norm(ca[both] - cb[both], axis=1) / 441.7
    return float(0.65 * shape + 0.35 * (1 - np.clip(cd.mean() * 2.2, 0, 1)))
out = {}
for t in targets:
    a = prep(t['rows'])
    sc = sorted(((fast(a, b), k) for k, b in tc.items()), reverse=True)
    out[t['name'] + '|' + t['id']] = [[*map(int, k.split(':')), round(s, 3)] for s, k in sc[:3]]
json.dump(out, open(os.path.join(SP, 'out', 'match_old.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('FIM', flush=True)
