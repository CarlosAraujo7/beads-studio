"""APLICA EM LOTE O PLANO DE CORES FEITO A PARTIR DA IMAGEM ORIGINAL (2026-11-03). Pedido do dono: "revise a cor de pele de TODOS os personagens ... analisa todos com cuidado".
O plano (tools/rc_plan.py → tools/out/rc_plan/<id>.json) só troca a COR de cada conta (a conta REAL mais parecida com a cor da imagem original); nenhuma conta muda de lugar (a forma é conferida) e
contas retocadas à mão depois da conversão ficam como estão. Os 40 moldes por gravação são o limite da trava do tplfile; antes do 1º lote há UMA cópia inteira do catálogo em
tools/backups/pre-recon-massa.js (o backup automático só guarda 30 e apagaria os do app), e cada molde guarda o desenho de antes em tools/backups/recolor-originais.json (o mesmo de recolor_apply.py),
então `python tools/recon_apply.py revert ID --autorizado` desfaz um molde e `python tools/rc_bulk.py revert --autorizado` desfaz o lote inteiro (só os moldes que ele não mexeu depois).
uso:  python tools/rc_bulk.py list   [--gmin 3] [--status pronto,quase] [--cat x] [--ids a,b]
      python tools/rc_bulk.py apply  --autorizado [--gmin 3] [--status pronto,quase] [--cat x] [--ids a,b] [--skip a,b] [--skin N] [--max 40] [--dry]
      python tools/rc_bulk.py revert --autorizado [--ids a,b]
Registro: tools/data/recolor_applied.json (mesmo de recolor_apply.py; marca 'feito' no plano)."""
import os, sys, json, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import tplfile
import recolor_apply as RA
import remap_cores as RC

T = RA.T
PLAN = os.path.join(HERE, 'out', 'rc_plan.json'); PD = os.path.join(HERE, 'out', 'rc_plan')
FULL = os.path.join(HERE, 'backups', 'pre-recon-massa.js')
LOTE = os.path.join(HERE, 'data', 'rcbulk_lote.json')            # ids que ESTE script gravou (para o revert em lote)


SKIN_L = {c['letter'] for c in RC.NEW if c['code'] in RC.SKIN_NEW}


def skin_delta(k, cat, de):
    """quantas contas de PELE (a letra de hoje ou a do plano é de pele) mudam de cor em mais de 4 ΔE"""
    new = json.load(open(os.path.join(PD, k + '.json'), encoding='utf-8'))['rows']; n = 0
    for r1, r2 in zip(cat, new):
        for c, r in zip(r1, r2):
            if c != '.' and c != r and (c in SKIN_L or r in SKIN_L) and de(c, r) > 4: n += 1
    return n


def sel(a):
    plan = json.load(open(PLAN, encoding='utf-8'))
    gmin = float(a[a.index('--gmin') + 1]) if '--gmin' in a else 3.0
    stat = a[a.index('--status') + 1].split(',') if '--status' in a else ['pronto', 'quase']
    cat = a[a.index('--cat') + 1].split(',') if '--cat' in a else None
    ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else None
    skip = set(a[a.index('--skip') + 1].split(',')) if '--skip' in a else set()
    skinn = int(a[a.index('--skin') + 1]) if '--skin' in a else None         # além do G: moldes com pelo menos N contas de PELE que mudam > 4 ΔE (o rosto é pouca coisa no G)
    if skinn is not None:
        import rc_plan as RPL
        cur = {t['id']: t['rows'] for t in tplfile.parse(T)['items']}
    out = []
    for k, v in plan.items():
        if v['status'] not in stat or k in skip or not os.path.exists(os.path.join(PD, k + '.json')): continue
        if ids is not None:
            if k not in ids: continue
        elif v.get('G', 0) < gmin and not (skinn is not None and k in cur and skin_delta(k, cur[k], RPL.de) >= skinn): continue
        if cat and v['cat'] not in cat: continue
        out.append(k)
    out.sort(key=lambda k: (plan[k]['cat'], plan[k]['name']))
    return plan, out


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == 'revert': return revert(a)
    plan, ids = sel(a)
    d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}
    if cmd == 'list':
        for k in ids: print('%-8s G%4.1f ret%4d %-40s %s' % (plan[k]['cat'][:8], plan[k].get('G', 0), plan[k].get('edited', 0), plan[k]['name'][:40], k))
        print(len(ids), 'moldes'); return
    if cmd != 'apply': print(__doc__); return
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado (CLAUDE.md 4.9: o dono pediu a revisão da cor de pele de todos os personagens).')
    mx = int(a[a.index('--max') + 1]) if '--max' in a else 40
    ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
    orig = json.load(open(RA.ORIG, encoding='utf-8')) if os.path.exists(RA.ORIG) else {}
    lote = json.load(open(LOTE, encoding='utf-8')) if os.path.exists(LOTE) else []
    todo = []; pulados = []
    for k in ids:
        if k in ap or k not in by: continue
        cur = d['items'][by[k]]['rows']; new = json.load(open(os.path.join(PD, k + '.json'), encoding='utf-8'))['rows']
        if len(cur) != len(new) or len(cur[0]) != len(new[0]) or any((c1 == '.') != (c2 == '.') for r1, r2 in zip(cur, new) for c1, c2 in zip(r1, r2)):
            pulados.append((k, 'forma')); continue
        if cur == new: pulados.append((k, 'igual')); continue
        bad = {c for r in new for c in r if c != '.' and c not in d['legend']}
        if bad: pulados.append((k, 'letras fora da legenda')); continue
        todo.append(k)
    print('no plano: %d | a gravar: %d | pulados: %s' % (len(ids), len(todo), pulados[:8]))
    if '--dry' in a: return
    if not todo: return
    if not os.path.exists(FULL): shutil.copy(T, FULL); print('cópia inteira do catálogo:', FULL)
    for i in range(0, len(todo), mx):
        lot = todo[i:i + mx]; d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
        for k in lot:
            if k not in orig: orig[k] = its[by[k]]['rows']
            its[by[k]] = dict(its[by[k]], rows=json.load(open(os.path.join(PD, k + '.json'), encoding='utf-8'))['rows'])
        json.dump(orig, open(RA.ORIG, 'w', encoding='utf-8'), ensure_ascii=False)
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), do_backup=False, allow=set(lot))
        for k in lot: ap[k] = dict(sha=RA.sha(its[by[k]]['rows']), mapa='reconversão (lote)', data=datetime.date.today().isoformat()); lote.append(k)
        json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(lote, open(LOTE, 'w', encoding='utf-8'))
        print('lote gravado: %d moldes (%d/%d)' % (len(lot), min(i + mx, len(todo)), len(todo)), flush=True)


def revert(a):
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado.')
    ap = json.load(open(RA.APPLIED, encoding='utf-8')); orig = json.load(open(RA.ORIG, encoding='utf-8'))
    lote = json.load(open(LOTE, encoding='utf-8')) if os.path.exists(LOTE) else []
    ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else list(lote)
    mx = 40; feitos = []; deixados = []
    d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}
    cand = [k for k in ids if k in by and k in orig and k in ap and RA.sha(d['items'][by[k]]['rows']) == ap[k]['sha']]
    deixados = [k for k in ids if k not in cand]
    for i in range(0, len(cand), mx):
        lot = cand[i:i + mx]; d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
        for k in lot: its[by[k]] = dict(its[by[k]], rows=orig[k])
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), do_backup=False, allow=set(lot))
        for k in lot: ap.pop(k, None); orig.pop(k, None); feitos.append(k)
    json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(orig, open(RA.ORIG, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump([k for k in lote if k not in feitos], open(LOTE, 'w', encoding='utf-8'))
    print('devolvidos: %d | deixados (ele mexeu depois ou não são deste lote): %d' % (len(feitos), len(deixados)))


if __name__ == '__main__':
    main()
