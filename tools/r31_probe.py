"""Cor da ARTE conta a conta (mediana do miolo de cada conta do molde) numa janela, para medir olhos e bocas SEM chutar (remessa 31; lê a geometria salva em tools/out/r31_geom).
    python tools/r31_probe.py "trecho do nome" r0 r1 c0 c1 [--cur]
r1 e c1 são exclusivos. Imprime, por conta, o código do kit mais próximo da cor da arte e uma letra de classe (. = vazio fora da figura, # = escuro, o = branco, s = pele) e, com --cur, o código
que o molde TEM hoje na mesma conta (para ver o que o convert6 fez de errado). Régua de linha/coluna do molde nas bordas."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import r31_exfinal as X
import r31_eyes as EY
import r5
from palette import ALL

CODE = {c['letter']: c['code'] for c in ALL}


def cells(name, rows):
    G = X.load_geom(name)
    ctx = EY.Ctx(rows, G, X.P, X.L, X.LAB)
    return ctx


def art_color(ctx, r, c):
    xa, xb = int(ctx.pxx(c + 0.25)), int(ctx.pxx(c + 0.75)); ya, yb = int(ctx.pyy(r + 0.25)), int(ctx.pyy(r + 0.75))
    xa, ya = max(0, xa), max(0, ya); xb, yb = min(ctx.w, max(xb, xa + 1)), min(ctx.h, max(yb, ya + 1))
    q = ctx.raw[ya:yb, xa:xb].reshape(-1, 3)
    ok = ctx.fg[ya:yb, xa:xb].reshape(-1)
    if not len(q): return None
    if ok.sum() < 0.3 * len(q): return None
    return tuple(int(v) for v in np.median(q[ok], axis=0))


def main():
    a = sys.argv[1:]
    cur = '--cur' in a; onlycur = '--onlycur' in a; a = [x for x in a if x not in ('--cur', '--onlycur')]
    nm, r0, r1, c0, c1 = a[0], int(a[1]), int(a[2]), int(a[3]), int(a[4])
    data = {x[0]: x[2] for x in json.load(open(os.path.join(HERE, 'data', ('r31v2_raw_120.json' if os.environ.get('R31V2') == '1' else 'final33_raw_120.json')), encoding='utf-8'))}
    full = next(n for n in data if nm.lower() in n.lower())
    rows = data[full]; ctx = cells(full, rows)
    print(full, f'{len(rows[0])}x{len(rows)}  alinhamento {ctx.sc:.0%}')
    print('      ' + ''.join(f'{c:>5}' for c in range(c0, c1)))
    if onlycur:
        for r in range(r0, min(r1, len(rows))):
            print(f'{r:>4}  ' + ''.join(f'{(CODE[rows[r][c]] if rows[r][c] != "." else "."):>5}' for c in range(c0, min(c1, len(rows[0])))))
        return
    for r in range(r0, min(r1, len(rows))):
        line = []
        for c in range(c0, min(c1, len(rows[0]))):
            col = art_color(ctx, r, c)
            if col is None: line.append('    .'); continue
            code = CODE[r5.near120(col)]
            line.append(f'{code:>5}')
        print(f'{r:>4}  ' + ''.join(line))
        if cur:
            print('  cur ' + ''.join(f'{(CODE[rows[r][c]] if rows[r][c] != "." else "."):>5}' for c in range(c0, min(c1, len(rows[0])))))


if __name__ == '__main__':
    main()
