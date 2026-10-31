"""3ª revisão pedida pelo usuário (2026-10-31, CLAUDE.md §7.21): SÓ os moldes da lista dele (FIX3); nenhum outro é tocado.
Base = backups/pre-rev3.js (o catálogo que ele acabou de gravar). `apply` só troca um molde se ele ainda é igual à base ou ao que esta ferramenta gravou (data/rev3_applied.json);
molde editado/excluído por ele é pulado e avisado. Nunca acrescenta molde.
  python tools/rev3.py build [trecho ...] [--H 420]   prévias fonte|antes|depois com fundo roxo em tools/out/r3_*.png e data/rev3_new.json (sempre refeito por inteiro para os moldes filtrados)
  python tools/rev3.py apply [--dry] [trecho ...]
  python tools/rev3.py dump "nome" r0 r1 c0 c1 [--new]  molde em texto com régua (letras não ASCII viram símbolos, com legenda)
Leitura de arte chapada: `flat(raw, geo, W, H, pal, prio)`: cada pixel vai para a cor mais próxima de `pal` [(rgb, letra)] ('.' = vazio) e a conta fica com a mais frequente;
`prio` = {letra: fração}: basta essa fração da janela para a letra ganhar (traço fino de contorno ou de arco). Não faz média, então não sai cor intermediária."""
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

BASE = os.path.join(HERE, 'backups', 'pre-rev3.js')
NEW = os.path.join(HERE, 'data', 'rev3_new.json')
APPLIED = os.path.join(HERE, 'data', 'rev3_applied.json')
OUT = os.path.join(HERE, 'out')
L = {c['code']: c['letter'] for c in P.ALL}
FIX3 = {}


def fix3(name, fn, src=None): FIX3[name] = (fn, src)


def base_items(): return {t['name']: t for t in parse(BASE)['items']}


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
            ch_ = None
            for l, f in prio.items():
                if sum(k[i] for i, q in enumerate(lets) if q == l) >= f: ch_ = l; break
            if ch_ is None:
                tot = {}
                for i, q in enumerate(lets): tot[q] = tot.get(q, 0) + k[i]
                ch_ = max(tot, key=tot.get)
            r.append(ch_)
        rows.append(''.join(r))
    return rows


def blocks(rows, items, legend=None):
    """items = [(linha, coluna, ['texto', ...])]; ' ' não mexe, '.' esvazia; caractere da legenda vira o código Pindou"""
    legend = legend or {}
    g = [list(r) for r in rows]
    for y0, x0, lines in items:
        for j, ln in enumerate(lines):
            for i, c in enumerate(ln):
                if c == ' ': continue
                g[y0 + j][x0 + i] = '.' if c == '.' else (L[legend[c]] if c in legend else c)
    return [''.join(r) for r in g]


def source_of(spec):
    if spec is None: return None
    from PIL import Image
    rem, idx, box = spec
    return Image.fromarray(FT.src_raw(rem, idx, box))


def cmd_build(args):
    import rev3_defs                                                  # noqa: F401
    H = 420
    if '--H' in args: k = args.index('--H'); H = int(args[k + 1]); del args[k:k + 2]
    filt = [a for a in args if not a.startswith('--')]
    items = base_items(); new = json.load(open(NEW, encoding='utf-8')) if os.path.exists(NEW) else {}
    pairs = []
    for name, (fn, src) in FIX3.items():
        if filt and not any(f.lower() in name.lower() for f in filt): continue
        if name not in items: print('  NÃO ESTÁ NO CATÁLOGO:', name); continue
        b = items[name]['rows']; r = fn(b)
        if len({len(x) for x in r}) != 1: print('  ERRO larguras', name, {len(x) for x in r}); continue
        if loose.loose_count(r): r = loose.fix_loose(r)
        r = O.trim(r)                                                 # sem linha/coluna vazia na borda
        new[name] = r
        pairs.append(('%s %dx%d' % (name[:58], len(r[0]), len(r)), b, r, source_of(src)))
    # moldes que saíram de FIX3 não ficam no arquivo (rev_new.json cumulativo quase gravou versão velha)
    new = {k: v for k, v in new.items() if k in FIX3}
    json.dump(new, open(NEW, 'w', encoding='utf-8'), ensure_ascii=False)
    per = 3
    for f in os.listdir(OUT):
        if f.startswith('r3_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    for k in range(0, len(pairs), per):
        rev_fix.sheet(pairs[k:k + per], os.path.join(OUT, 'r3_%d.png' % (k // per)), H=H)
    print(len(pairs), 'painéis ->', (len(pairs) + per - 1) // per, 'folhas tools/out/r3_*.png')


def cmd_apply(args):
    import rev3_defs                                                  # noqa: F401
    dry = '--dry' in args; filt = [a for a in args if not a.startswith('--')]
    new = json.load(open(NEW, encoding='utf-8'))
    applied = json.load(open(APPLIED, encoding='utf-8')) if os.path.exists(APPLIED) else {}
    base = {k: v['rows'] for k, v in base_items().items()}
    d = parse(os.path.join(ROOT, 'templates.js')); items = {t['name']: t for t in d['items']}
    done = same = 0; skipped = []; gone = []
    for name, rows in new.items():
        if name not in FIX3: continue
        if filt and not any(f.lower() in name.lower() for f in filt): continue
        if name not in items: gone.append(name); continue
        t = items[name]
        if t['rows'] == rows: same += 1; continue
        if t['rows'] != base.get(name) and t['rows'] != applied.get(name): skipped.append(name); continue
        bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
        if bad: print('ERRO letras', name, bad); continue
        t['rows'] = rows; applied[name] = rows; done += 1
    print('trocados: %d | já iguais: %d | pulados (editados): %d | fora do catálogo: %d' % (done, same, len(skipped), len(gone)))
    for n in skipped: print('  PULEI (editado):', n)
    for n in gone: print('  excluído:', n)
    if dry: print('(--dry)'); return
    if done:
        tplfile.write(os.path.join(ROOT, 'templates.js'), d['legend'], d['cfg'], list(d['items']), d.get('removed'))
        json.dump(applied, open(APPLIED, 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravado templates.js')


def cmd_dump(args):
    use_new = '--new' in args
    a = [x for x in args if not x.startswith('--')]
    q = a[0]; nums = [int(v) for v in a[1:5]]
    items = {k: v['rows'] for k, v in base_items().items()}
    if use_new and os.path.exists(NEW): items.update(json.load(open(NEW, encoding='utf-8')))
    hit = [n for n in items if q.lower() in n.lower() and not n.endswith('(grande)')]
    if len(hit) != 1: print('AMBÍGUO:', hit[:6]); return
    rows = items[hit[0]]
    r0, r1, c0, c1 = nums if len(nums) == 4 else (0, len(rows), 0, len(rows[0]))
    r1 = min(r1, len(rows)); c1 = min(c1, len(rows[0]))
    code = {c['letter']: c['code'] for c in P.ALL}
    print(hit[0], len(rows[0]), 'x', len(rows))
    print('      ' + ''.join(str((c // 10) % 10) if c % 10 == 0 else ' ' for c in range(c0, c1)))
    print('      ' + ''.join(str(c % 10) for c in range(c0, c1)))
    for y in range(r0, r1): print('%4d  %s' % (y, rows[y][c0:c1]))
    used = {c for y in range(r0, r1) for c in rows[y][c0:c1] if c != '.'}
    print('legenda: ' + '  '.join('%s=%s' % (c, code.get(c, '?')) for c in sorted(used, key=lambda c: code.get(c, ''))))


if __name__ == '__main__':
    import rev3 as _m
    a = sys.argv[1:]
    {'build': _m.cmd_build, 'apply': _m.cmd_apply, 'dump': _m.cmd_dump}[a[0] if a else 'build'](a[1:])
