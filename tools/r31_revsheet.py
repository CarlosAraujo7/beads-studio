"""Folha fonte | catálogo | revisão (data/r31_rev_new.json) da remessa 31.  python tools/r31_revsheet.py [trecho ...] [--H 300] [--tag t] [--per 12]
-> tools/out/r31rv_<tag>_N.png"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import r31_exfinal as X
import tplfile

if __name__ == '__main__':
    a = sys.argv[1:]; H = 300; tag = 'r'; per = 12; rr = None
    nf = 'r31_rev2_new.json' if '--rev2' in a else 'r31_rev_new.json'; a = [x for x in a if x != '--rev2']
    if '--rows' in a:
        k = a.index('--rows'); rr = tuple(int(v) for v in a[k + 1].split(',')); del a[k:k + 2]
    for opt in ('--H', '--tag', '--per'):
        if opt in a:
            k = a.index(opt); v = a[k + 1]; del a[k:k + 2]
            if opt == '--H': H = int(v)
            elif opt == '--tag': tag = v
            else: per = int(v)
    raw = json.load(open(os.path.join(HERE, 'data', 'final33_raw_120.json'), encoding='utf-8'))
    fin = json.load(open(os.path.join(HERE, 'data', 'final33_120.json'), encoding='utf-8'))
    cat = {x[0]: y[0] for x, y in zip(raw, fin)}
    new = json.load(open(os.path.join(HERE, 'data', nf), encoding='utf-8'))
    by = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    items = []
    for n, g, idx, fn, grp in X.CFG:
        cn = cat.get(n, n)
        if cn not in new or cn not in by: continue
        if a and not any(q.lower() in n.lower() for q in a): continue
        src = X.R.source_img(idx, getattr(fn, 'box', None))
        if getattr(fn, 'rot', 0): src = src.rotate(-90 * fn.rot, expand=True)
        o, nw = by[cn], new[cn]
        if rr:
            o, nw = o[rr[0]:rr[1]], nw[rr[0]:rr[1]]
            src = src.crop((0, int(src.height * rr[0] / len(by[cn])), src.width, int(src.height * min(rr[1], len(by[cn])) / len(by[cn]))))
        items.append((f'{idx}: {n[:42]}', src, o)); items.append(('revisão', None, nw))
    for f in os.listdir(X.OUT):
        if f.startswith(f'r31rv_{tag}_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    for k in range(0, len(items), per):
        X.R.pairsheet(items[k:k + per], os.path.join(X.OUT, f'r31rv_{tag}_{k // per}.png'), H=H)
    print(len(items) // 2, 'moldes,', (len(items) + per - 1) // per, 'folhas')
