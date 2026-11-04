"""Folha de LEITURA de rosto da remessa 29: fonte com a grade das contas | molde com a mesma grade e régua (para escolher mouth_zone=(linha 0, linha 1, coluna 0, coluna 1) no CFG).
  BEADPAL=120 python tools/r29_sheet.py "trecho do nome" r0 r1 c0 c1 [célula] [--boca]     -> tools/out/r29_face.png
  O molde é o da conversão SEM a limpeza de boca (para ver onde ela está); --boca mostra com a limpeza."""
import os, sys
os.environ.setdefault('BEADPAL', '120')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r29_exfinal as Z
import facetools as FT

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if '--boca' not in sys.argv: Z.NO_MOUTH[0] = False
    key = a[0]; r0, r1, c0, c1 = [int(v) for v in a[1:5]]; cell = int(a[5]) if len(a) > 5 else 30
    n, g, idx, fn, grp = next(c for c in Z.CFG if key.lower() in c[0].lower())
    rows = fn()
    raw = FT.src_raw(29, idx, getattr(fn, 'box', None))
    geom = FT.align(raw, rows)
    out = os.path.join(HERE, 'out', 'r29_face.png')
    FT.sheet(raw, rows, geom, (r0, min(r1, len(rows)), c0, min(c1, len(rows[0]))), out, cell=cell, title=n, letters=True)
    print(n, len(rows[0]), len(rows), out)
