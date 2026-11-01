"""4ª revisão pedida pelo usuário (2026-10-31, CLAUDE.md §7.24). SÓ os moldes da lista dele (FIX4); nenhum outro é tocado.
Base = backups/pre-rev4.js (o catálogo que ele acabou de gravar). `apply` só troca um molde igual à base ou ao que esta ferramenta gravou (data/rev4_applied.json).
  python tools/rev4.py build [trecho ...] [--H 480]     prévias fonte|antes|depois em tools/out/r4_*.png e data/rev4_new.json
  python tools/rev4.py apply [--dry]
  python tools/rev4.py read "nome" [r0 r1 c0 c1] [--new] [--cell 16]   folha de leitura (fonte com a grade | molde com a grade) em tools/out/r4read.png
  python tools/rev4.py dump "nome" [r0 r1 c0 c1] [--new]               molde em texto"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import palette as P
import loose, tplfile
import outline as O
from tplfile import parse
import facetools as FT
import rev_fix

BASE = os.path.join(HERE, 'backups', 'pre-rev4.js')
NEW = os.path.join(HERE, 'data', 'rev4_new.json')
APPLIED = os.path.join(HERE, 'data', 'rev4_applied.json')
OUT = os.path.join(HERE, 'out')
L = {c['code']: c['letter'] for c in P.ALL}
CODE = {c['letter']: c['code'] for c in P.ALL}
FIX4 = {}
SRC = {'Quatro Braços (Ben 10, pixel)': (24, 71, None), 'Chucky (chibi)': (24, 27, None), 'Dante (Devil May Cry, pixel)': (24, 70, None),
       'Criatura roxa (pixel, gráfico)': (22, 35, None), 'Trompa azul e guarda-chuva amarelo (How I Met Your Mother, logo)': (22, 30, None),
       'Omni-Man (Invencível, pixel)': (24, 44, None), 'Pennywise (chibi, corpo inteiro)': (24, 62, None), 'Pennywise de capa amarela (chibi)': (24, 13, None),
       'Sukuna (Jujutsu Kaisen, pixel, corpo inteiro)': (24, 0, None), 'Jack Sparrow (Piratas do Caribe, chibi, adesivo)': (24, 3, None),
       'Paige (WWE, com cinturão)': (21, 1, (250, 0, 1010, 1242)), 'Paige (WWE, top roxo)': (21, 2, (220, 10, 730, 1020)), 'Paige (WWE, erguendo o cinturão)': (21, 2, (860, 0, 1330, 1020))}
RENAME = {}


def fix4(name, fn, rename=None):
    FIX4[name] = fn
    if rename: RENAME[name] = rename


def base_items(): return {t['name']: t for t in parse(BASE)['items']}


def blocks(rows, items, legend=None):
    legend = legend or {}
    g = [list(r) for r in rows]
    for y0, x0, lines in items:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c == ' ': continue
                g[y0 + j][x0 + i] = '.' if c == '.' else (L[legend[c]] if c in legend else c)
    return [''.join(r) for r in g]


def recolor(rows, r0, r1, c0, c1, frm, to):
    g = [list(r) for r in rows]
    for y in range(max(0, r0), min(len(g), r1 + 1)):
        for x in range(max(0, c0), min(len(g[0]), c1 + 1)):
            if g[y][x] in frm: g[y][x] = to
    return [''.join(r) for r in g]


def mirror(rows, side='L', axis2=None):
    """espelha o molde inteiro: `side` = metade que fica; axis2 = 2×eixo (par = em cima de coluna; ímpar = entre colunas). Sem eixo: o centro da largura."""
    W = len(rows[0])
    a = W - 1 if axis2 is None else axis2
    out = []
    n = max(a + 1, 2 * W - 1 - a)
    pad = n - W
    for r in rows:
        g = list(r) + ['.'] * n
        new = ['.'] * n
        for x in range(n):
            mx = a - x
            src = x if (2 * x <= a) == (side == 'L') or 2 * x == a else mx
            new[x] = g[src] if 0 <= src < len(g) else '.'
        out.append(''.join(new))
    return O.trim(out)


def flat(raw, geo, W, H, pal, prio=None):
    ox, oy, cw, ch = geo; prio = prio or {}
    cols = np.array([p[0] for p in pal], np.float32); lets = [p[1] for p in pal]
    rows = []
    for y in range(H):
        r = []
        for x in range(W):
            win = raw[max(0, int(oy + y * ch)):max(0, int(oy + (y + 1) * ch)), max(0, int(ox + x * cw)):max(0, int(ox + (x + 1) * cw))].reshape(-1, 3).astype(np.float32)
            if not len(win): r.append('.'); continue
            d = ((win[:, None, :] - cols[None, :, :]) ** 2).sum(axis=2)
            k = np.bincount(d.argmin(axis=1), minlength=len(pal)) / float(len(win))
            tot = {}
            for i, q in enumerate(lets): tot[q] = tot.get(q, 0) + k[i]
            c_ = None
            for l, f in prio.items():
                if tot.get(l, 0) >= f: c_ = l; break
            r.append(c_ or max(tot, key=tot.get))
        rows.append(''.join(r))
    return rows


def source_of(name):
    from PIL import Image
    s = SRC.get(name)
    if not s: return None
    return Image.fromarray(FT.src_raw(*s))


def cmd_build(args):
    import rev4_defs                                                  # noqa: F401
    H = 480
    if '--H' in args: k = args.index('--H'); H = int(args[k + 1]); del args[k:k + 2]
    filt = [a for a in args if not a.startswith('--')]
    items = base_items(); new = json.load(open(NEW, encoding='utf-8')) if os.path.exists(NEW) else {}
    pairs = []
    for name, fn in FIX4.items():
        if filt and not any(f.lower() in name.lower() for f in filt): continue
        if name not in items: print('  NÃO ESTÁ NO CATÁLOGO:', name); continue
        b = items[name]['rows']; r = fn(b)
        if len({len(x) for x in r}) != 1: print('  ERRO larguras', name, {len(x) for x in r}); continue
        if loose.loose_count(r): r = loose.fix_loose(r)
        r = O.trim(r); new[name] = r
        pairs.append(('%s %dx%d' % (name[:58], len(r[0]), len(r)), b, r, source_of(name)))
    new = {k: v for k, v in new.items() if k in FIX4}
    json.dump(new, open(NEW, 'w', encoding='utf-8'), ensure_ascii=False)
    for f in os.listdir(OUT):
        if f.startswith('r4_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(pairs), 3):
        rev_fix.sheet(pairs[k:k + 3], os.path.join(OUT, 'r4_%d.png' % (k // 3)), H=H)
    print(len(pairs), 'painéis ->', (len(pairs) + 2) // 3, 'folhas tools/out/r4_*.png')


def cmd_apply(args):
    import rev4_defs                                                  # noqa: F401
    dry = '--dry' in args
    new = json.load(open(NEW, encoding='utf-8'))
    applied = json.load(open(APPLIED, encoding='utf-8')) if os.path.exists(APPLIED) else {}
    base = {k: v['rows'] for k, v in base_items().items()}
    d = parse(os.path.join(ROOT, 'templates.js')); items = {t['name']: t for t in d['items']}
    for old, nw in RENAME.items():
        if nw in items and old not in items: items[old] = items[nw]
    done = same = 0; skipped = []; gone = []
    for name, rows in new.items():
        if name not in items: gone.append(name); continue
        t = items[name]
        if t['rows'] == rows and t['name'] == RENAME.get(name, t['name']): same += 1; continue
        if t['rows'] not in (base.get(name), applied.get(name), rows): skipped.append(name); continue
        t['rows'] = rows; applied[name] = rows; done += 1
        if name in RENAME: t['name'] = RENAME[name]
    print('trocados: %d | já iguais: %d | pulados (editados): %d | fora do catálogo: %d' % (done, same, len(skipped), len(gone)))
    for n in skipped: print('  PULEI (editado):', n)
    for n in gone: print('  excluído:', n)
    if dry: print('(--dry)'); return
    if done:
        tplfile.write(os.path.join(ROOT, 'templates.js'), d['legend'], d['cfg'], list(d['items']), d.get('removed'), allow=[items[n]['id'] for n in new if n in items])
        json.dump(applied, open(APPLIED, 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravado templates.js')


def _rows(q, use_new):
    items = {k: v['rows'] for k, v in base_items().items()}
    if use_new and os.path.exists(NEW): items.update(json.load(open(NEW, encoding='utf-8')))
    big = '(grande)' in q
    hit = [n for n in items if q.lower() in n.lower() and n.endswith('(grande)') == big]
    if len(hit) != 1: raise SystemExit('AMBÍGUO: %s' % hit[:6])
    return hit[0], items[hit[0]]


def cmd_dump(args):
    use_new = '--new' in args; a = [x for x in args if not x.startswith('--')]
    name, rows = _rows(a[0], use_new); nums = [int(v) for v in a[1:5]]
    r0, r1, c0, c1 = nums if len(nums) == 4 else (0, len(rows), 0, len(rows[0]))
    r1 = min(r1, len(rows)); c1 = min(c1, len(rows[0]))
    print(name, len(rows[0]), 'x', len(rows))
    print('      ' + ''.join(str((c // 10) % 10) if c % 10 == 0 else ' ' for c in range(c0, c1)))
    print('      ' + ''.join(str(c % 10) for c in range(c0, c1)))
    for y in range(r0, r1): print('%4d  %s' % (y, rows[y][c0:c1]))
    used = {c for y in range(r0, r1) for c in rows[y][c0:c1] if c != '.'}
    print('legenda: ' + '  '.join('%s=%s' % (c, CODE.get(c, '?')) for c in sorted(used, key=lambda c: CODE.get(c, ''))))


def cmd_read(args):
    use_new = '--new' in args
    a = [x for x in args if not x.startswith('--') ]
    cell = 16
    if '--cell' in args: cell = int(args[args.index('--cell') + 1]); a = [x for x in a if x != str(cell)]
    name, rows = _rows(a[0], use_new); nums = [int(v) for v in a[1:5]]
    region = tuple(nums) if len(nums) == 4 else (0, len(rows), 0, len(rows[0]))
    raw = FT.src_raw(*SRC[name.replace(' (grande)', '')]); geo = FT.align(raw, rows, verbose=True)
    FT.sheet(raw, rows, geo, region, os.path.join(OUT, 'r4read.png'), cell=cell, title=name[:40], letters=cell >= 14)
    print('tools/out/r4read.png', geo)


if __name__ == '__main__':
    import rev4 as _m
    a = sys.argv[1:]
    {'build': _m.cmd_build, 'apply': _m.cmd_apply, 'dump': _m.cmd_dump, 'read': _m.cmd_read}[a[0] if a else 'build'](a[1:])
