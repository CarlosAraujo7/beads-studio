"""TROCA UM CÓDIGO POR OUTRO nos moldes do catálogo (CLAUDE.md §7.43, 2026-11-02, pedido do dono: "o H12 não existe como bege nas paletas que mandei, dá certo trocar pela A1; verifique melhor").
Verificado: nas bandejas sem tampa o H12 e a A1 são o mesmo creme (ΔE2000 4,6) e nas cartelas o H12 é um cinza-bege, não um bege separado. A troca é de LETRA (o desenho não muda: onde havia conta continua havendo).
**É mudança em muitos moldes (77 usam o H12): só com --autorizado** e só do par que o dono pediu. Máximo 40 por gravação (trava do tplfile); cópia do catálogo antes em tools/backups/pre-alias-<DE>.js;
`--revert` devolve (só se o molde ainda é exatamente o que esta ferramenta gravou: data/alias_applied.json).
uso:  python tools/alias_apply.py --de H12 --para A1 [--dry] [--revert] [--autorizado] [--templates ARQ]"""
import os, sys, json, hashlib, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tplfile

T = os.path.join(ROOT, 'templates.js')
APPLIED = os.path.join(HERE, 'data', 'alias_applied.json')
LOTE = tplfile.MAX_POR_VEZ


def sha(rows): return hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest()


def main():
    a = sys.argv[1:]
    real = '--templates' not in a
    path = T if real else a[a.index('--templates') + 1]
    dry = '--dry' in a; revert = '--revert' in a
    de = a[a.index('--de') + 1]; para = a[a.index('--para') + 1]
    if real and not dry and '--autorizado' not in a:
        print('RECUSADO: mexe em vários moldes do catálogo; só com --autorizado e só no par que o dono pediu (CLAUDE.md 4.9).'); sys.exit(1)
    pal = {c['code']: c['letter'] for c in json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']}
    L_de, L_para = pal[de], pal[para]
    snap = os.path.join(HERE, 'backups', 'pre-alias-%s.js' % de)
    applied_p = APPLIED if real else APPLIED + '.teste'
    applied = json.load(open(applied_p, encoding='utf-8')) if os.path.exists(applied_p) else {}
    d = tplfile.parse(path); items = list(d['items']); pos = {t['id']: k for k, t in enumerate(items)}
    orig = {t['id']: t['rows'] for t in tplfile.parse(snap)['items']} if (revert and os.path.exists(snap)) else {}
    todo = []
    for t in items:
        key = '%s>%s:%s' % (de, para, t['id'])
        if revert:
            done = applied.get(key)
            if done and sha(t['rows']) == done['sha'] and t['id'] in orig: todo.append((t, list(orig[t['id']]), key))
        elif any(L_de in r for r in t['rows']):
            todo.append((t, [r.replace(L_de, L_para) for r in t['rows']], key))
    print('moldes a %s: %d' % ('devolver' if revert else 'trocar %s por %s' % (de, para), len(todo)))
    if dry or not todo: print('(--dry: nada gravado)' if dry else 'nada a fazer'); return
    if real and not revert and not os.path.exists(snap): shutil.copy(path, snap); print('cópia do catálogo antes:', snap)
    for b0 in range(0, len(todo), LOTE):
        lote = todo[b0:b0 + LOTE]; allow = set(); reg = {}
        for t, rows, key in lote:
            items[pos[t['id']]] = dict(t, rows=rows); allow.add(t['id']); reg[key] = None if revert else dict(sha=sha(rows))
        tplfile.write(path, d['legend'], d['cfg'], items, d.get('removed'), allow=allow, do_backup=False)
        for k, v in reg.items():
            if v is None: applied.pop(k, None)
            else: applied[k] = v
        json.dump(applied, open(applied_p, 'w', encoding='utf-8'), ensure_ascii=False)
        d = tplfile.parse(path); items = list(d['items']); pos = {t['id']: k for k, t in enumerate(items)}
        print('lote %d: %d moldes' % (b0 // LOTE + 1, len(lote)))
    print('ok')


if __name__ == '__main__':
    main()
