"""Linhas de um molde da revisão (data/r31_rev_new.json) em códigos, com régua.  python tools/r31_dumpnew.py "trecho" r0 r1 [c0 c1]"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
from palette import ALL
C = {p['letter']: p['code'] for p in ALL}
a = sys.argv[1:]
new = json.load(open(os.path.join(HERE, 'data', '' + ('r31_rev2_new.json' if '--rev2' in sys.argv else 'r31_rev_new.json')), encoding='utf-8'))
n = next(k for k in new if a[0].lower() in k.lower()); r = new[n]
r0, r1 = int(a[1]), int(a[2]); c0, c1 = (int(a[3]), int(a[4])) if len(a) > 4 else (0, len(r[0]))
print(n, len(r[0]), 'x', len(r))
print('    ' + ''.join(f'{c:>4}' for c in range(c0, c1)))
for y in range(r0, min(r1, len(r))):
    print(f'{y:>3} ' + ''.join(f'{(C[r[y][x]] if r[y][x] != "." else "."):>4}' for x in range(c0, min(c1, len(r[0])))))
