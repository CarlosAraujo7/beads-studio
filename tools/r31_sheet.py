"""Folhas fonte | molde da remessa 31 SEM reconverter (lê data/final33_raw_120.json):  python tools/r31_sheet.py [trecho do nome ...] [--H 500] [--tag nome]
-> tools/out/r31s_<tag>_N.png. Serve para olhar de novo só alguns moldes (a conversão não é reproduzível conta a conta entre execuções, então não se reconverte para olhar)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import r31_exfinal as X

if __name__ == '__main__':
    argv = sys.argv[1:]
    H = 500; tag = 'f'
    if '--H' in argv: k = argv.index('--H'); H = int(argv[k + 1]); del argv[k:k + 2]
    if '--tag' in argv: k = argv.index('--tag'); tag = argv[k + 1]; del argv[k:k + 2]
    data = {x[0]: x for x in json.load(open(os.path.join(HERE, 'data', 'final33_raw_120.json'), encoding='utf-8'))}
    items = []
    for n, g, idx, fn, grp in X.CFG:
        if argv and not any(a.lower() in n.lower() for a in argv): continue
        if n not in data: continue
        r = data[n][2]
        items.append((f'{idx}: {n} {len(r[0])}x{len(r)}', X.R.source_img(idx, getattr(fn, 'box', None)), r))
    per = 8 if H <= 340 else 4 if H <= 620 else 2
    for f in os.listdir(X.OUT):
        if f.startswith(f'r31s_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    for k in range(0, len(items), per):
        X.R.pairsheet(items[k:k + per], os.path.join(X.OUT, f'r31s_{tag}_{k // per}.png'), H=H)
    print(len(items), 'moldes,', (len(items) + per - 1) // per, 'folhas')
