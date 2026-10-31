"""Compara variantes de reconversão (illus5.convert5) de uma ilustração: python tools/rev_var.py "nome do molde" [--big] [--H 380] "rótulo:k=v,k=v" ...
A 1ª coluna é a fonte; depois o molde ATUAL (backups/pre-rev.js) e cada variante. Valores: números, True/False/None ou texto sem espaço. Grava tools/out/var_<n>.png."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import rev_fix, rev_defs
from rev_defs import reconv
from tplfile import parse


def parse_kv(s):
    lab, _, kv = s.partition(':'); kw = {}
    for item in [x for x in kv.split(',') if x]:
        k, _, v = item.partition('=')
        try: v = eval(v, {'__builtins__': {}}, {'True': True, 'False': False, 'None': None})
        except Exception: pass
        kw[k] = v
    return lab, kw


if __name__ == '__main__':
    a = sys.argv[1:]
    big = '--big' in a
    if big: a.remove('--big')
    H = 380
    if '--H' in a: k = a.index('--H'); H = int(a[k + 1]); del a[k:k + 2]
    name = a[0]; vs = [parse_kv(x) for x in a[1:]]
    d = parse(os.path.join(HERE, 'backups', 'pre-rev.js')); items = {i['name']: i['rows'] for i in d['items']}
    cur = items[name + (' (grande)' if big else '')]
    pairs = [('ATUAL %dx%d' % (len(cur[0]), len(cur)), cur, cur, rev_fix.source_of(name))]
    for lab, kw in vs:
        r = reconv(name, **kw)(big)
        pairs.append(('%s %dx%d' % (lab, len(r[0]), len(r)), cur, r, None))
    out = os.path.join(HERE, 'out', 'var_%s.png' % ''.join(ch for ch in name if ch.isalnum())[:16])
    rev_fix.sheet(pairs, out, H=H, W=1900); print(out)
