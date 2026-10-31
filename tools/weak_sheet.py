"""Folha de LEITURA do rosto de um molde das remessas 22/23 (refazer os fracos, 2026-10-31): recorte da fonte com a grade do molde | o molde com a mesma grade e números de linha/coluna.
uso (a paleta e a remessa vêm dos argumentos):  python tools/weak_sheet.py REM "trecho do nome" r0 r1 c0 c1 [cell] [--big] [--letters]
   REM = 22 ou 23; o nome é buscado no CFG de r22_exfinal.py / r23_exfinal.py (ilustrações); com --big usa o irmão grande. Grava tools/out/ws_<nome>.png e imprime o IoU do alinhamento."""
import os, sys
REM = sys.argv[1]
os.environ['REMNUM'] = REM; os.environ['BEADPAL'] = '120'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r5
import r22_exfinal as R
import facetools as FT
mod = R
if REM == '23':
    import r23_exfinal as R3
    mod = R3


def find(q):
    hit = [it for it in mod.CFG if it[4] == 'ill' and q in it[0]]
    if not hit: raise SystemExit('nome nao achado: ' + q)
    return hit[0]


def get(it, big=False):
    r5.SKIN_ON = mod._skin(it[0])
    if big: return R.ill(it[2], it[7], plates=it[5], box=it[6], skin=r5.SKIN_ON)
    return it[3]()


if __name__ == '__main__':
    a = [x for x in sys.argv[2:] if not x.startswith('--')]
    q = a[0]; r0, r1, c0, c1 = [int(v) for v in a[1:5]]; cell = int(a[5]) if len(a) > 5 else 30
    it = find(q); rows = get(it, '--big' in sys.argv)
    raw = FT.src_raw(REM, it[2], it[6])
    geom = FT.align(raw, rows)
    out = os.path.join(R.OUT, 'ws_' + ''.join(ch for ch in q if ch.isalnum())[:24] + ('_big' if '--big' in sys.argv else '') + '.png')
    r1 = min(r1, len(rows)); c1 = min(c1, len(rows[0]))
    FT.sheet(raw, rows, geom, (r0, r1, c0, c1), out, cell=cell, title='%s %dx%d' % (it[0][:40], len(rows[0]), len(rows)), letters='--letters' in sys.argv)
    print(out, len(rows[0]), 'x', len(rows))
