"""APLICA A RAMPA DE CINZAS NOS MOLDES QUE O DONO ESCOLHER (2026-11-03). Nada é gravado sem `--autorizado` e sem a lista de moldes (regra 4.9): o plano está em tools/out/ramp_plan/<id>.json (feito por `python tools/ramp_plan.py`).
Cada molde só é gravado se o desenho do catálogo ainda é EXATAMENTE o que o plano viu (sha8 do plano): se o dono o editou no app depois, o molde é pulado com aviso. A forma não muda (só a letra de algumas contas).
O desenho de antes da rampa fica em tools/backups/rampa-originais.json, os originais de antes de TODAS as trocas continuam em recolor-originais.json, uma cópia inteira do catálogo em tools/backups/pre-rampa.js (feita uma vez), o registro em tools/data/recolor_applied.json
e a lista do lote em tools/data/rampa_lote.json; `revert` devolve os moldes (só os que ele não mexeu depois).
uso:  python tools/ramp_apply.py list                                  (candidatos: >= 50% de preto e a rampa muda >= 4% das contas)
      python tools/ramp_apply.py apply --autorizado --ids a,b,c       (ou --all-cand para todos os candidatos)
      python tools/ramp_apply.py revert --autorizado [--ids a,b]"""
import os, sys, json, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import tplfile, recolor_apply as RA

T = RA.T
PLAN = os.path.join(HERE, 'out', 'ramp_plan.json'); PD = os.path.join(HERE, 'out', 'ramp_plan')
FULL = os.path.join(HERE, 'backups', 'pre-rampa.js')
RORIG = os.path.join(HERE, 'backups', 'rampa-originais.json')            # o desenho de ANTES DA RAMPA (já recolorido), para o revert voltar só a rampa
LOTE = os.path.join(HERE, 'data', 'rampa_lote.json')


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    plan = {r['id']: r for r in json.load(open(PLAN, encoding='utf-8'))}
    cand = [i for i, r in plan.items() if r['k7'] >= 0.5 and r['share'] >= 0.04 and r['delta'] >= 25]
    ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else (cand if '--all-cand' in a else [])
    if cmd == 'list':
        for i in cand: print('H7 %.2f  muda %3d (%4.1f%%)  %-9s %-60s %s' % (plan[i]['k7'], plan[i]['delta'], 100 * plan[i]['share'], plan[i]['cat'][:9], plan[i]['name'][:60], i))
        print(len(cand), 'candidatos'); return
    if cmd == 'revert': return revert(a, ids or None)
    if cmd != 'apply': print(__doc__); return
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado e só nos moldes que o dono escolheu (CLAUDE.md 4.9).')
    if not ids: raise SystemExit('diga quais moldes: --ids a,b,c (ou --all-cand)')
    d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}
    ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
    rorig = json.load(open(RORIG, encoding='utf-8')) if os.path.exists(RORIG) else {}
    lote = json.load(open(LOTE, encoding='utf-8')) if os.path.exists(LOTE) else []
    todo = []
    for i in ids:
        if i not in by or i not in plan or not os.path.exists(os.path.join(PD, i + '.json')): print('PULEI (sem plano ou fora do catálogo):', i); continue
        cur = d['items'][by[i]]['rows']; new = json.load(open(os.path.join(PD, i + '.json'), encoding='utf-8'))['rows']
        if RA.sha(cur)[:8] != plan[i]['sha']: print('PULEI (o molde mudou desde o plano):', plan[i]['name']); continue
        if len(cur) != len(new) or len(cur[0]) != len(new[0]) or any((c1 == '.') != (c2 == '.') for r1, r2 in zip(cur, new) for c1, c2 in zip(r1, r2)): print('PULEI (forma diferente):', plan[i]['name']); continue
        if cur == new: continue
        bad = {c for r in new for c in r if c != '.' and c not in d['legend']}
        if bad: print('PULEI (letras fora da legenda):', plan[i]['name']); continue
        todo.append(i)
    print('a gravar:', len(todo))
    if not todo: return
    if not os.path.exists(FULL): shutil.copy(T, FULL); print('cópia inteira do catálogo:', FULL)
    for k in range(0, len(todo), 40):
        lot = todo[k:k + 40]; d = tplfile.parse(T); by = {t['id']: j for j, t in enumerate(d['items'])}; its = list(d['items'])
        for i in lot:
            if i not in rorig: rorig[i] = its[by[i]]['rows']
            its[by[i]] = dict(its[by[i]], rows=json.load(open(os.path.join(PD, i + '.json'), encoding='utf-8'))['rows'])
        json.dump(rorig, open(RORIG, 'w', encoding='utf-8'), ensure_ascii=False)
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), do_backup=False, allow=set(lot))
        for i in lot: ap[i] = dict(sha=RA.sha(its[by[i]]['rows']), mapa='rampa de cinzas (ramp_apply)', data=datetime.date.today().isoformat()); lote.append(i)
        json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(lote, open(LOTE, 'w', encoding='utf-8'))
        print('lote gravado:', len(lot), 'moldes', flush=True)


def revert(a, ids):
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado.')
    ap = json.load(open(RA.APPLIED, encoding='utf-8')); orig = json.load(open(RORIG, encoding='utf-8'))
    lote = json.load(open(LOTE, encoding='utf-8')) if os.path.exists(LOTE) else []
    ids = ids or list(lote); d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}
    cand = [i for i in ids if i in by and i in orig and i in ap and RA.sha(d['items'][by[i]]['rows']) == ap[i]['sha']]
    done = []
    for k in range(0, len(cand), 40):
        lot = cand[k:k + 40]; d = tplfile.parse(T); by = {t['id']: j for j, t in enumerate(d['items'])}; its = list(d['items'])
        for i in lot: its[by[i]] = dict(its[by[i]], rows=orig[i])
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), do_backup=False, allow=set(lot))
        for i in lot: ap.pop(i, None); orig.pop(i, None); done.append(i)
    json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(orig, open(RORIG, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump([i for i in lote if i not in done], open(LOTE, 'w', encoding='utf-8')); print('devolvidos:', len(done), '| deixados (ele mexeu depois):', len(ids) - len(done))


if __name__ == '__main__':
    main()
