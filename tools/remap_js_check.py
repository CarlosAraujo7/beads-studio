"""Confere que a troca de cores do APP (JS, botão "Refazer cores deste molde" em Contas por cor) e a do PYTHON (remap_cores.remap3) dão a MESMA troca.
uso:  python tools/remap_js_check.py dump N        -> grava tools/out/remap_py_maps.json com a troca do Python para N moldes do catálogo (os 5 "bons", Cavaleiros e N-? ao acaso)
O lado JS roda no Chrome headless (scratchpad/t_remap.py) e compara com esse arquivo."""
import os, sys, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import remap_cores as RC, tplfile

N = int(sys.argv[2]) if len(sys.argv) > 2 else 60
items = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
random.seed(7)
pick = [t for t in items if t.get('cat') == 'cavaleiros-do-zodiaco' and len(t['rows']) <= 50 and len(t['rows'][0]) <= 50][:6]
pick += [t for t in items if t['name'] in ('Mona Lisa', 'Bepo (One Piece, pixel)', 'Annabeth Chase (pixel)', 'Perry, o Ornitorrinco (ilustração)', 'Perry, o Ornitorrinco (ilustração, pose 2)')]
rest = [t for t in items if t not in pick and len(t['rows']) <= 50 and len(t['rows'][0]) <= 50]
pick += random.sample(rest, max(0, N - len(pick)))
out = {}
for t in pick:
    m = RC.remap3(t['rows'])
    out[t['id']] = {RC.OLD_BY_L[a]['code']: RC.NEW_BY_L[b]['code'] for a, b in m.items()}
json.dump(out, open(os.path.join(HERE, 'out', 'remap_py_maps.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(out), 'moldes gravados em tools/out/remap_py_maps.json')
