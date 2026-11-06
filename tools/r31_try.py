"""Testa VARIANTES de parâmetros de uma imagem da remessa 31 lado a lado (fonte | variante 1 | variante 2 ...), sem gravar nada:
    BEADPAL=120 python tools/r31_try.py IDX "rótulo=dict(mask=grab())" "outro=dict(bg='flat', tol=60)" ... [--box x0,y0,x1,y1] [--noeyes] [--H 420] [--tag nome]
Cada variante é um dict Python com as opções do I() do r31_exfinal (mask, bg, refs, tol, thr, peel, paint, clear, skin, K, ...); os nomes de r31_exfinal (grab, flat, white, KM, OM, P) valem.
Saída: tools/out/r31try_<tag>.png"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import r31_exfinal as X
from r31_exfinal import *


def main():
    a = sys.argv[1:]
    idx = int(a[0]); specs = []; box = None; H = 420; tag = f'{idx}'; noeyes = False
    k = 1
    while k < len(a):
        if a[k] == '--box': box = tuple(int(v) for v in a[k + 1].split(',')); k += 2
        elif a[k] == '--H': H = int(a[k + 1]); k += 2
        elif a[k] == '--tag': tag = a[k + 1]; k += 2
        elif a[k] == '--noeyes': noeyes = True; k += 1
        else: specs.append(a[k]); k += 1
    items = []
    P.TOUCH6 = {}; P.SKIN6 = {}
    src = R.source_img(idx, box)
    items.append((f'{idx}: fonte', src, None))
    for sp in specs:
        lab, _, kw = sp.partition('=')
        kws = eval(kw, dict(vars(X)))
        if box and 'box' not in kws: kws['box'] = box
        if noeyes: kws.setdefault('eyes', False)
        P.CUR[0] = f'try chibi {lab}'
        try:
            r5.SKIN_ON = False
            rows = X.I(idx, **kws)()
            items.append((f'{lab} {len(rows[0])}x{len(rows)}', None, rows)); print(lab, len(rows[0]), 'x', len(rows))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', lab, repr(e))
    mold = [(t, s, r) for t, s, r in items if r is not None]
    pairs = []
    for t, s, r in mold: pairs.append((t, src if not pairs else None, r))
    # a fonte só aparece uma vez (na 1ª variante); as outras vêm só com o molde
    R.pairsheet(pairs, os.path.join(OUT, f'r31try_{tag}.png'), H=H)
    print('->', os.path.join(OUT, f'r31try_{tag}.png'))


if __name__ == '__main__':
    main()
