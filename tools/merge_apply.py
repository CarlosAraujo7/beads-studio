"""JUNTA TONS QUASE IGUAIS em moldes do catálogo (CLAUDE.md §7.40, pedido do dono em 2026-11-02: "no molde do Kurama chibi há 3 tons de vermelho que são praticamente a mesma coisa; é mais simples usar só um;
mantém uma das cores (usar mais se necessário) e deixa a opção de uma parecida se a padrão acabar"). Pelas contas que o molde JÁ usa (`remap_cores.merge_similar`): as que têm ΔE2000 < T entre si na tela viram a mais
usada do grupo. Não troca por outras contas; as parecidas continuam à mão no botão ⇄ do app.
**É mudança de molde: só nos que o dono nomeou (regra 4.9) e só com --autorizado.** Máximo 40 por gravação (trava do tplfile); uma cópia do catálogo antes em tools/backups/pre-juntar.js; `--revert` devolve o original
(só se o molde ainda é exatamente o que esta ferramenta gravou: data/merge_applied.json).
uso:  python tools/merge_apply.py --ids a,b [--T 6.0] [--dry] [--revert] [--autorizado] [--templates ARQ]"""
import os, sys, json, hashlib, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tplfile
import outline as O
import remap_cores as RC

T = os.path.join(ROOT, 'templates.js')
APPLIED = os.path.join(HERE, 'data', 'merge_applied.json')
SNAP = os.path.join(HERE, 'backups', 'pre-juntar.js')


def sha(rows): return hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest()


def main():
    a = sys.argv[1:]
    real = '--templates' not in a
    path = T if real else a[a.index('--templates') + 1]
    dry = '--dry' in a; revert = '--revert' in a
    thr = float(a[a.index('--T') + 1]) if '--T' in a else RC.MERGE_T
    if real and not dry and '--autorizado' not in a:
        print('RECUSADO: mexe em moldes do catálogo; só com --autorizado e só nos que o dono nomeou (CLAUDE.md 4.9).'); sys.exit(1)
    ids = [x for i, v in enumerate(a) if v == '--ids' for x in a[i + 1].split(',')]
    if not ids: print('diga quais moldes: --ids a,b'); sys.exit(1)
    applied_p = APPLIED if real else APPLIED + '.teste'
    applied = json.load(open(applied_p, encoding='utf-8')) if os.path.exists(applied_p) else {}
    d = tplfile.parse(path); items = list(d['items']); pos = {t['id']: k for k, t in enumerate(items)}
    orig = {t['id']: t['rows'] for t in tplfile.parse(SNAP)['items']} if (revert and os.path.exists(SNAP)) else {}
    allow = set(); reg = {}
    for i in ids:
        if i not in pos: print('   pulado:', i, '- não está no catálogo'); continue
        t = items[pos[i]]; done = applied.get(i)
        if revert:
            if not done or sha(t['rows']) != done['sha'] or i not in orig: print('   pulado:', i, '- nada a devolver (ou foi mudado depois)'); continue
            rows = list(orig[i]); m = {}
        else:
            m = RC.merge_similar(t['rows'], thr)
            rows = O.trim([''.join(m.get(c, c) if c != '.' else '.' for c in r) for r in t['rows']])
            if rows == t['rows']: print('   pulado:', i, '- nenhuma cor parecida a esse ponto (T=%.1f)' % thr); continue
        if len(rows) != len(t['rows']) or any(len(x) != len(y) for x, y in zip(rows, t['rows'])): raise SystemExit('tamanho mudou: ' + i)
        used0 = len({c for r in t['rows'] for c in r if c != '.'}); used1 = len({c for r in rows for c in r if c != '.'})
        print('  %-52s %2d -> %2d cores  %s' % (t['name'][:52], used0, used1, {RC.NEW_BY_L[x]['code']: RC.NEW_BY_L[y]['code'] for x, y in m.items() if x != y}))
        items[pos[i]] = dict(t, rows=rows); allow.add(i); reg[i] = None if revert else dict(sha=sha(rows), T=thr, mapa={RC.NEW_BY_L[x]['code']: RC.NEW_BY_L[y]['code'] for x, y in m.items() if x != y})
    if not allow: print('nada a gravar'); return
    if dry: print('(--dry: nada gravado)'); return
    if real and not os.path.exists(SNAP): shutil.copy(path, SNAP); print('cópia do catálogo antes:', SNAP)
    tplfile.write(path, d['legend'], d['cfg'], items, d.get('removed'), allow=allow, do_backup=False)
    for k, v in reg.items():
        if v is None: applied.pop(k, None)
        else: applied[k] = v
    json.dump(applied, open(applied_p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok:', len(allow), 'molde(s)')


if __name__ == '__main__':
    main()
