"""Refaz as cores de moldes do catálogo com as CONTAS REAIS (CLAUDE.md §7.40, 2026-11-02). Os moldes foram convertidos com as cores ESTIMADAS de antes; com a paleta das contas a pele bege vira creme/laranja,
o marrom vira laranja e o ouro vira amarelo, e vários moldes ficam "homogêneos demais" (dois tons que o molde separava viram a mesma conta). Aqui cada cor do molde troca para a conta real mais parecida com o que ela
mostrava antes (`remap_cores.remap4`: atribuição de custo mínimo em ΔE2000 + proteção do matiz + desprezo por cor mais viva que a de antes + PRESERVAÇÃO DAS BORDAS, com a pele agrupada e o H12 fora dos destinos). Juntar tons quase iguais é OUTRA operação (tools/merge_apply.py), pedida pelo dono em 2026-11-02.
**É alteração em massa: só roda nos moldes que o dono autorizou (regra 4.9) e só com --autorizado.** Limites: no máximo 40 por gravação (trava do tplfile), só moldes que já estavam no catálogo
quando a paleta mudou (`data/remap_legacy_ids.json`: os de remessas novas já nascem na paleta nova) e nunca o mesmo molde duas vezes sobre o resultado anterior: `--redo` refaz A PARTIR DO ORIGINAL (instantâneo
`tools/backups/pre-remap-cores.js`) e só se o molde ainda é exatamente o que esta ferramenta gravou (`data/remap_applied.json`); `--revert` devolve o original.
uso:  python tools/remap_apply.py --snapshot                       (grava os ids de agora como "antigos"; rode ANTES de acrescentar remessas)
      python tools/remap_apply.py (--cat ID | --ids a,b | --nome trecho)... [--dry] [--redo | --revert] [--autorizado] [--templates ARQ]
--dry só mostra o que trocaria (nada gravado). --templates ARQ aplica numa CÓPIA (teste da trava e da gravação: nunca teste no arquivo real). Cópia do catálogo antes: tools/backups/pre-remap-cores.js."""
import os, sys, json, hashlib, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tplfile, loose
import outline as O
import remap_cores as RC

T = os.path.join(ROOT, 'templates.js')
LEGACY = os.path.join(HERE, 'data', 'remap_legacy_ids.json')
APPLIED = os.path.join(HERE, 'data', 'remap_applied.json')
SNAP = os.path.join(HERE, 'backups', 'pre-remap-cores.js')
LOTE = tplfile.MAX_POR_VEZ


def sha(rows): return hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest()


def main():
    a = sys.argv[1:]
    if '--snapshot' in a:
        ids = [t['id'] for t in tplfile.parse(T)['items']]
        if os.path.exists(LEGACY): print('já existe', LEGACY, '(não sobrescrevo)'); return
        json.dump(ids, open(LEGACY, 'w', encoding='utf-8')); print('ids antigos gravados:', len(ids)); return
    real = '--templates' not in a
    path = T if real else a[a.index('--templates') + 1]
    dry = '--dry' in a; redo = '--redo' in a; revert = '--revert' in a
    if real and not dry and '--autorizado' not in a:
        print('RECUSADO: troca de cores é alteração em massa; só com --autorizado, e só nos moldes que o dono pediu (CLAUDE.md 4.9 e 7.40).'); sys.exit(1)
    cats = [a[i + 1] for i, v in enumerate(a) if v == '--cat']; ids = [x for i, v in enumerate(a) if v == '--ids' for x in a[i + 1].split(',')]; nomes = [a[i + 1].lower() for i, v in enumerate(a) if v == '--nome']
    if not (cats or ids or nomes): print('diga quais moldes: --cat, --ids ou --nome'); sys.exit(1)
    legacy = set(json.load(open(LEGACY, encoding='utf-8')))
    applied_p = APPLIED if real else APPLIED + '.teste'
    applied = json.load(open(applied_p, encoding='utf-8')) if os.path.exists(applied_p) else {}
    d = tplfile.parse(path); items = list(d['items'])
    orig = {t['id']: t['rows'] for t in tplfile.parse(SNAP)['items']} if (redo or revert) else {}
    sel = [t for t in items if t['cat'] in cats or t['id'] in ids or any(n in t['name'].lower() for n in nomes)]
    todo = []; skip = []
    for t in sel:
        if t['id'] not in legacy: skip.append((t['id'], 'nasceu depois da troca de paleta')); continue
        done = applied.get(t['id'])
        if redo or revert:
            if not done: skip.append((t['id'], 'ainda não foi trocado')); continue
            if sha(t['rows']) != done['sha']: skip.append((t['id'], 'foi mudado depois (por ele no app?): não mexo')); continue
            if t['id'] not in orig: skip.append((t['id'], 'sem original no instantâneo')); continue
        elif done: skip.append((t['id'], 'já trocado (use --redo para refazer a partir do original)')); continue
        todo.append(t)
    print('selecionados %d | a %s %d | pulados %d' % (len(sel), 'devolver' if revert else 'trocar', len(todo), len(skip)))
    for i, why in skip[:25]: print('   pulado:', i, '-', why)
    if not todo: return
    if real and not dry and not os.path.exists(SNAP):
        shutil.copy(path, SNAP); print('cópia do catálogo antes:', SNAP)
    pos = {t['id']: k for k, t in enumerate(items)}
    for b0 in range(0, len(todo), LOTE):
        lote = todo[b0:b0 + LOTE]; allow = set(); reg = {}
        for t in lote:
            src = orig[t['id']] if (redo or revert) else t['rows']
            if revert: rows = list(src); m = {}
            else:
                m = RC.remap4(src)
                rows = O.trim([''.join(m.get(c, c) if c != '.' else '.' for c in r) for r in src])           # só apara; as letras trocadas não criam nem tiram contas
            if len(rows) != len(t['rows']) or any(len(x) != len(y) for x, y in zip(rows, t['rows'])): raise SystemExit('tamanho mudou: ' + t['id'])
            bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
            if bad: raise SystemExit('letras fora da legenda: %s %s' % (t['id'], bad))
            items[pos[t['id']]] = dict(t, rows=rows); allow.add(t['id']); reg[t['id']] = None if revert else dict(sha=sha(rows), mapa={k: v for k, v in m.items() if k != v}, algoritmo='v4')
        print('lote %d: %d moldes' % (b0 // LOTE + 1, len(lote)), '(--dry: nada gravado)' if dry else '')
        if dry: continue
        tplfile.write(path, d['legend'], d['cfg'], items, d.get('removed'), allow=allow, do_backup=False)       # a cópia de segurança é uma só (pre-remap-cores.js): 25 lotes girariam os 30 backups do usuário
        for k, v in reg.items():
            if v is None: applied.pop(k, None)
            else: applied[k] = v
        json.dump(applied, open(applied_p, 'w', encoding='utf-8'), ensure_ascii=False)
        d = tplfile.parse(path); items = list(d['items']); pos = {t['id']: k for k, t in enumerate(items)}
    print('ok')


if __name__ == '__main__':
    main()
