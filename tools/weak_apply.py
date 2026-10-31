"""Troca no templates.js os moldes das remessas 22/23 que foram REFEITOS (pedido do usuário, 2026-10-31: "refazer fracos antes"; veja CLAUDE.md §7.19).
Só troca um molde se o desenho que está no catálogo ainda é IGUAL ao que eu tinha acrescentado (linhas de data/pre_weak_*.json, com a mesma limpeza de contas soltas do add_templates) ou
ao que esta mesma ferramenta gravou antes (data/weak_applied.json); se o usuário editou (desenho diferente) ou excluiu o molde, NÃO mexe e avisa. Nome, id, categoria e posição ficam.
uso: python tools/weak_apply.py [--dry] [--only trecho do nome ...]"""
import os, sys, json, shutil, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import tplfile, loose

ap = argparse.ArgumentParser()
ap.add_argument('--dry', action='store_true')
ap.add_argument('--only', nargs='*', default=[])
a = ap.parse_args()

FILES = [('final24_120', 'pre_weak_final24_120'), ('final24_multi_120', 'pre_weak_final24_multi_120'), ('final25_120', 'pre_weak_final25_120'), ('final25_multi_120', 'pre_weak_final25_multi_120')]
TPL = os.path.join(ROOT, 'templates.js')
APPLIED = os.path.join(HERE, 'data', 'weak_applied.json')
applied = json.load(open(APPLIED, encoding='utf-8')) if os.path.exists(APPLIED) else {}


def clean(rows):
    return loose.fix_loose(rows) if loose.loose_count(rows) else rows


d = tplfile.parse(TPL)
items = d['items']; by = {t['name']: t for t in items}
done = 0; same = 0; skipped = []; missing = []
for new_f, pre_f in FILES:
    new = {x[0]: x[2] for x in json.load(open(os.path.join(HERE, 'data', new_f + '.json'), encoding='utf-8'))}
    pre = {x[0]: x[2] for x in json.load(open(os.path.join(HERE, 'data', pre_f + '.json'), encoding='utf-8'))}
    for name, rows in new.items():
        if a.only and not any(o in name for o in a.only): continue
        if name not in pre or pre[name] == rows: continue                    # não mudou
        if name not in by: missing.append(name); continue                    # o usuário excluiu
        t = by[name]; target = clean(rows)
        if t['rows'] == target: same += 1; continue
        mine = {json.dumps(clean(pre[name])), json.dumps(applied.get(name))}
        if json.dumps(t['rows']) not in mine: skipped.append(name); continue  # o usuário editou o desenho
        if len({len(r) for r in target}) != 1: print('ERRO linhas de larguras diferentes:', name); continue
        bad = {c for r in target for c in r if c != '.' and c not in d['legend']}
        if bad: print('ERRO letras fora da legenda em', name, bad); continue
        t['rows'] = target; applied[name] = target; done += 1
print('trocados: %d | já iguais: %d | pulados (o usuário editou): %d | excluídos pelo usuário: %d' % (done, same, len(skipped), len(missing)))
for n in skipped: print('  PULEI (editado):', n)
for n in missing: print('  não está mais no catálogo:', n)
if a.dry: print('(--dry: nada foi gravado)')
elif done:
    bk = os.path.join(HERE, 'backups', 'pre-weak.js')
    if not os.path.exists(bk): shutil.copyfile(TPL, bk); print('cópia do catálogo antes da 1ª troca:', bk)
    tplfile.write(TPL, d['legend'], d['cfg'], items, d.get('removed'))
    json.dump(applied, open(APPLIED, 'w', encoding='utf-8'), ensure_ascii=False)
    print('gravado', TPL, '(cópia de segurança com carimbo em tools/backups/)')
