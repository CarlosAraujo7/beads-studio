"""Imprime um molde das remessas 22/23 (ilustrações do CFG) como TEXTO com régua de linha/coluna, para achar restos de texto/ruído e escrever os consertos de tools/weak_fix.py.
uso: python tools/weak_dump.py REM "trecho do nome" [--big] [--r0 N --r1 N --c0 N --c1 N]"""
import os, sys
REM = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weak_sheet as WS


def dump(rows, r0=0, r1=None, c0=0, c1=None):
    """letras fora do ASCII (as 96 novas do kit) viram símbolos do conjunto SYM, com a legenda (símbolo = letra = código Pindou) no fim"""
    import palette as P
    code = {c['letter']: c['code'] for c in P.ALL}
    r1 = r1 or len(rows); c1 = c1 or len(rows[0])
    SYM = '@#%&$=+~^;:,_`<>?|0123456789'; sym = {}
    def ch(c):
        if c == '.' or ord(c) < 128: return c
        if c not in sym: sym[c] = SYM[len(sym) % len(SYM)]
        return sym[c]
    print('      ' + ''.join(str((c // 10) % 10) if c % 10 == 0 else ' ' for c in range(c0, c1)))
    print('      ' + ''.join(str(c % 10) for c in range(c0, c1)))
    for y in range(r0, r1): print('%4d  %s' % (y, ''.join(ch(c) for c in rows[y][c0:c1])))
    used = {c for y in range(r0, r1) for c in rows[y][c0:c1] if c != '.'}
    print('legenda: ' + '  '.join('%s=%s' % (ch(c), code.get(c, '?')) for c in sorted(used, key=lambda c: code.get(c, '')) ))


if __name__ == '__main__':
    a = sys.argv[2:]
    def opt(k, d):
        return int(a[a.index(k) + 1]) if k in a else d
    q = [x for x in a if not x.startswith('--')][0]
    it = WS.find(q); rows = WS.get(it, '--big' in a)
    print(it[0], len(rows[0]), 'x', len(rows))
    dump(rows, opt('--r0', 0), opt('--r1', None), opt('--c0', 0), opt('--c1', None))
