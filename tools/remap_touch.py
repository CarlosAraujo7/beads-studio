"""Acerto MANUAL de cores num molde que `remap_apply.py` já refez (CLAUDE.md §7.40): troca uma letra por outra, SÓ nas cores (nenhuma conta aparece, some ou muda de lugar).
Serve quando a conta real mais parecida que o algoritmo achou ainda destoa (ex.: o Ryuk ficou com 14 contas de azul vivo onde o original tinha um azul-ardósia quase cinza).
Só mexe no molde que o dono nomeou (regra 4.9), só se ele ainda é exatamente o que `remap_apply` gravou (`data/remap_applied.json`: sha) e só com --autorizado.
uso:  python tools/remap_touch.py --id ID --map "!=d" [--map "x=y" ...] [--dry] [--autorizado] [--templates ARQ]
      (as letras são as do templates.js; `!=d` = toda conta `!` vira `d`). Atualiza o registro (sha e mapa) para `--redo`/`--revert` do remap_apply continuarem valendo."""
import os, sys, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tplfile

T = os.path.join(ROOT, 'templates.js')
APPLIED = os.path.join(HERE, 'data', 'remap_applied.json')


def sha(rows): return hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest()


def main():
    a = sys.argv[1:]
    ids = [a[i + 1] for i, v in enumerate(a) if v == '--id']; maps = [a[i + 1] for i, v in enumerate(a) if v == '--map']
    if len(ids) != 1 or not maps: print('uso: --id ID --map "x=y" [--map ...]'); sys.exit(1)
    real = '--templates' not in a; path = T if real else a[a.index('--templates') + 1]; dry = '--dry' in a
    if real and not dry and '--autorizado' not in a: print('RECUSADO: só com --autorizado e só no molde que o dono nomeou (CLAUDE.md 4.9).'); sys.exit(1)
    sub = {}
    for m in maps:
        src, dst = m.split('=', 1)
        if len(src) != 1 or len(dst) != 1: print('mapa inválido:', m); sys.exit(1)
        sub[src] = dst
    applied_p = APPLIED if real else APPLIED + '.teste'
    applied = json.load(open(applied_p, encoding='utf-8')) if os.path.exists(applied_p) else {}
    d = tplfile.parse(path); items = list(d['items']); pos = {t['id']: k for k, t in enumerate(items)}
    i = ids[0]
    if i not in pos: print('molde não está no catálogo:', i); sys.exit(1)
    t = items[pos[i]]; done = applied.get(i)
    if not done: print('esse molde não foi refeito pelo remap_apply: não mexo'); sys.exit(1)
    if sha(t['rows']) != done['sha']: print('o molde foi mudado depois (por ele no app?): não mexo'); sys.exit(1)
    rows = [''.join(sub.get(c, c) if c != '.' else '.' for c in r) for r in t['rows']]
    bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
    if bad: print('letras fora da legenda:', bad); sys.exit(1)
    n = sum(r1[k] != r2[k] for r1, r2 in zip(t['rows'], rows) for k in range(len(r1)))
    print('%s: %d contas mudam de cor (%s)' % (t['name'], n, ', '.join('%s→%s' % kv for kv in sub.items())))
    if dry: print('(--dry: nada gravado)'); return
    items[pos[i]] = dict(t, rows=rows)
    tplfile.write(path, d['legend'], d['cfg'], items, d.get('removed'), allow={i})
    m = dict(done.get('mapa', {}))
    for src, dst in sub.items():
        hit = False
        for k, v in list(m.items()):
            if v == src: m[k] = dst; hit = True
        if not hit and src not in m: m[src] = dst
    applied[i] = dict(sha=sha(rows), mapa=m, algoritmo=done.get('algoritmo', 'v4') + '+manual')
    json.dump(applied, open(applied_p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok')


if __name__ == '__main__':
    main()
