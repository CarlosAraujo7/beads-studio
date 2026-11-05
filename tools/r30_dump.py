"""Molde em TEXTO com régua e códigos (uma conta = código de 3 caracteres), para ler coordenadas exatas:
  python tools/r30_dump.py "nome exato ou trecho" [l0 l1 c0 c1] [--new]
sem janela = o rosto achado pelo _face_eyes da remessa 29 com folga."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import tplfile
from palette import ALL
CODE = {p['letter']: p['code'] for p in ALL}


def main():
    a = sys.argv[1:]; new = '--new' in a; a = [x for x in a if x != '--new']
    q = a[0]; lim = [int(v) for v in a[1:5]] if len(a) >= 5 else None
    cat = {t['name']: t['rows'] for t in tplfile.parse(os.path.join(os.path.dirname(HERE), 'templates.js'))['items']}
    if new:
        for n, r in json.load(open(os.path.join(HERE, 'data', 'r30_rev_new.json'), encoding='utf-8')).items(): cat[n] = r
    hits = [n for n in cat if n == q] or [n for n in cat if q.lower() in n.lower()]
    n = hits[0]; rows = cat[n]; H, W = len(rows), len(rows[0])
    if lim: r0, r1, c0, c1 = lim
    else:
        import numpy as np, r29_exfinal as P
        face, hull, eyes = P._face_eyes(rows)
        if face is None: r0, r1, c0, c1 = 0, H // 2, 0, W - 1
        else:
            ys, xs = np.nonzero(face); r0, r1, c0, c1 = max(0, ys.min() - 5), ys.max() + 3, max(0, xs.min() - 4), xs.max() + 4
    r1 = min(r1, H - 1); c1 = min(c1, W - 1)
    print(f'{n}  {W}x{H}  linhas {r0}-{r1}, colunas {c0}-{c1}')
    print('    ' + ''.join(f'{x:>4}' for x in range(c0, c1 + 1)))
    for y in range(r0, r1 + 1):
        print(f'{y:>3} ' + ''.join(f'{(CODE.get(rows[y][x], "  .") if rows[y][x] != "." else "  ."):>4}' for x in range(c0, c1 + 1)))


if __name__ == '__main__':
    main()
