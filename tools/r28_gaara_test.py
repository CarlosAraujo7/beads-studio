"""Teste da redução do Gaara (remessa 28, idx 62): fit50 (tira linhas e colunas) x vote (voto por grupo) a partir do tamanho nativo. Só gera uma folha em tools/out/."""
import os, sys
os.environ['BEADPAL'] = '120'
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r28_exfinal as X
from r28_exfinal import E, R, lg, O, vote, OUT
from r26_exfinal import fit50

GRID = dict(px=7.998, py=7.997, ox=7.77, oy=7.77, W=55, H=65)
nat = E(62, px=GRID, mode=True, post=lg)
nat = O.trim(nat)
print('nativo', len(nat[0]), 'x', len(nat))
a = fit50(nat); b = vote(nat, 50, de=13.0); c = vote(nat, 50, de=8.0)
print('fit50', len(a[0]), 'x', len(a), '| vote13', len(b[0]), 'x', len(b), '| vote8', len(c[0]), 'x', len(c))
src = R.source_img(62)
sheet = [('nativo %dx%d' % (len(nat[0]), len(nat)), src, nat), ('fit50 %dx%d' % (len(a[0]), len(a)), src, a), ('vote13 %dx%d' % (len(b[0]), len(b)), src, b), ('vote8 %dx%d' % (len(c[0]), len(c)), src, c)]
R.pairsheet(sheet, os.path.join(OUT, 'r28_gaara_test.png'), H=620)
for i, r in enumerate(nat): print('%2d %s' % (i, r))
