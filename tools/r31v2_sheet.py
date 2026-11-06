"""Folhas fonte | atual | nova (2ª versão da remessa 31). python tools/r31v2_sheet.py [trecho ...] [--H 300] [--tag t] [--new arquivo.json]
'atual' = data/final33_raw_120.json; 'nova' = data/r31v2_raw_120.json (se existir) ou a limpeza r31v2.clean da atual."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import r31_exfinal as X
import r31v2

if __name__ == '__main__':
    argv = sys.argv[1:]; H = 300; tag = 'v'; newf = os.path.join(HERE, 'data', 'r31v2_raw_120.json'); onlynew = False
    if '--H' in argv: k = argv.index('--H'); H = int(argv[k + 1]); del argv[k:k + 2]
    if '--tag' in argv: k = argv.index('--tag'); tag = argv[k + 1]; del argv[k:k + 2]
    if '--new' in argv: k = argv.index('--new'); newf = argv[k + 1]; del argv[k:k + 2]
    if '--onlynew' in argv: argv.remove('--onlynew'); onlynew = True
    cur = {x[0]: x[2] for x in json.load(open(os.path.join(HERE, 'data', 'final33_raw_120.json'), encoding='utf-8'))}
    new = {x[0]: x[2] for x in json.load(open(newf, encoding='utf-8'))} if os.path.exists(newf) else {}
    items = []
    for n, g, idx, fn, grp in X.CFG:
        if argv and not any(a.lower() in n.lower() for a in argv): continue
        if n not in cur: continue
        if onlynew and n not in new: continue
        nr = new.get(n) or (r31v2.clean(cur[n]) if grp != 'graf' else cur[n])
        src = X.R.source_img(idx, getattr(fn, 'box', None))
        items.append((f'{idx}: {n[:40]} atual', src, cur[n]))
        items.append((f'nova {len(nr[0])}x{len(nr)}', None, nr))
    for f in os.listdir(X.OUT):
        if f.startswith(f'r31v_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    per = 12
    for k in range(0, len(items), per):
        X.R.pairsheet(items[k:k + per], os.path.join(X.OUT, f'r31v_{tag}_{k // per}.png'), H=H)
    print(len(items) // 2, 'moldes,', (len(items) + per - 1) // per, 'folhas')
