"""Acrescenta templates novos (uma remessa convertida) ao templates.js SEM apagar nada do que já está lá
(inclusive o que o usuário renomeou, moveu, ajustou ou excluiu e gravou pelo app).

uso (na raiz do projeto):
    python tools/add_templates.py tools/data/final12.json            # um ou mais arquivos finalN.json
    python tools/add_templates.py tools/data/final13.json --dry      # só mostra o que faria
    python tools/add_templates.py x.json --templates outro/templates.js   # (para testes)

Cada item do json é [nome, série, linhas] (o "série" do rN_exfinal.py é só a franquia de origem). No app o molde tem só
nome e categoria; no templates.js o campo "group" é apenas o nome da categoria. Regras:
  * nome que já existe no catálogo -> pulado com AVISO (renomeie no rN_exfinal.py);
  * categoria = a que tem o nome da série (inclusive categorias que o usuário criou ou renomeou), senão a franquia
    conhecida (tools/franchises.py), senão a mais usada por moldes da mesma série; série nova vira categoria nova;
    séries genéricas ("Outros"...) vão para "Outros";
  * moldes com mais de 50 em algum lado são REDUZIDOS para 1 placa (shrink.py), a menos que o item traga um 4º elemento {"plates": N} (molde de 2, 3 ou 4 placas de propósito; a prioridade é 1 placa, mais só quando fica feio ou impossível) (--keep-big desliga);
  * faz cópia de segurança do templates.js em tools/backups/ antes de gravar.
"""
import os, sys, json, argparse, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from collections import Counter
import tplfile
import franchises as F
import shrink
import loose

ap = argparse.ArgumentParser()
ap.add_argument('files', nargs='+')
ap.add_argument('--dry', action='store_true')
ap.add_argument('--readd', action='store_true', help='recoloca também os que o usuário excluiu antes')
ap.add_argument('--replace', action='store_true', help='nome que já existe: TROCA as linhas do molde (mantém id, categoria e posição). Use para refazer as versões de 120 cores quando os hex da paleta forem corrigidos; apaga ajustes que o usuário gravou nesses moldes')
ap.add_argument('--fill-holes', action='store_true', help='preenche buraquinhos (vazios de até 3 contas cercados por contas): use nas remessas de ILUSTRAÇÃO (convert4); em pixel art copiado de gráfico o vazio pode ser de propósito')
ap.add_argument('--keep-big', action='store_true', help='NÃO reduz para 1 placa (por padrão todo molde novo com mais de 50 em algum lado é reduzido: política do catálogo desde 2026-10-27)')
ap.add_argument('--templates', default=os.path.join(os.path.dirname(HERE), 'templates.js'))
ap.add_argument('--autorizado', action='store_true', help='obrigatório com --replace ou --readd: só use quando o usuário pediu exatamente esses moldes (CLAUDE.md §4.9)')
a = ap.parse_args()
if (a.replace or a.readd) and not a.autorizado:
    raise SystemExit('RECUSADO: --replace e --readd mexem no que o usuário decidiu. Só com --autorizado, e só se ele pediu esses moldes pelo nome.')

d = tplfile.parse(a.templates)
items = d['items']
names = {t['name'] for t in items}
removed = set(d.get('removed') or [])
ids = {t['id'] for t in items}
letters = set(d['legend'])
by_group = {}
for t in items: by_group.setdefault(t['group'], Counter())[t['cat']] += 1

ICONS = {i: ic for i, _, ic in F.CATEGORIES}
def _n(x): return ''.join(ch for ch in unicodedata.normalize('NFD', x.lower()) if ch.isalnum() and not unicodedata.combining(ch))
def by_name(g):
    """id da categoria cujo nome (o que aparece na galeria) é a série g; None se não houver"""
    cfg = d['cfg'] or {}; names = dict(cfg.get('names') or {})
    cands = {c['id']: names.get(c['id']) or c['name'] for c in cfg.get('custom', [])}
    for i, n, _ in F.CATEGORIES: cands.setdefault(i, names.get(i) or n)
    cands.update({'earrings': names.get('earrings') or 'Brincos', 'other': names.get('other') or 'Outros'})
    hit = [i for i, n in cands.items() if _n(n) == _n(g)]
    return hit[0] if hit else None
def cat_name(cat, fallback):
    if cat == 'other': return ((d['cfg'] or {}).get('names') or {}).get('other') or 'Outros'
    cfg = d['cfg'] or {}
    for c in cfg.get('custom', []):
        if c['id'] == cat: return (cfg.get('names') or {}).get(cat) or c['name']
    return (cfg.get('names') or {}).get(cat) or F.NAME_BY_ID.get(cat) or fallback

def ensure_cat(cat, label):
    if cat in ('other', 'earrings'): return
    cfg = d['cfg'] = d['cfg'] or {'order': [], 'names': {}, 'icons': {}, 'custom': [], 'hidden': []}
    if any(c['id'] == cat for c in cfg['custom']): return
    cfg['custom'].append({'id': cat, 'name': F.NAME_BY_ID.get(cat, label), 'icon': ICONS.get(cat, 'cStar')})
    order = [x for x in cfg.get('order', []) if x not in (cat, 'other')]
    at = order.index('earrings') if 'earrings' in order else len(order)
    cfg['order'] = order[:at] + [cat] + order[at:] + ['other']
    print('categoria nova criada na galeria:', F.NAME_BY_ID.get(cat, label))

added = 0; skipped = 0; replaced = 0; nloose = 0; allow = set(); readd = set()
for f in a.files:
    path = f if os.path.exists(f) else os.path.join(HERE, 'data', f)
    for item in json.load(open(path, encoding='utf-8')):
        n, g, rows = item[:3]; opts = item[3] if len(item) > 3 else {}      # 4º item opcional: {"plates": N} = molde de N placas de propósito (não reduz para 1 placa)
        if a.fill_holes: rows = loose.fill_pinholes(rows)[0]
        _lc = loose.loose_count(rows)
        if _lc: rows = loose.fix_loose(rows); nloose += _lc                 # regra do usuário: NUNCA contas soltas (loose.py)
        if n in names:
            if a.replace:
                t = next(x for x in items if x['name'] == n)
                if t['rows'] != rows: t['rows'] = rows; replaced += 1; allow.add(t['id'])
                continue
            print('AVISO: nome repetido, pulado:', n); skipped += 1; continue
        if n in removed and not a.readd:
            print('pulado (o usuário excluiu este template antes; use --readd para recolocar):', n); skipped += 1; continue
        if n in removed: readd.add(n)
        w = {len(r) for r in rows}
        bad = {c for r in rows for c in r if c != '.' and c not in letters}
        if len(w) != 1 or bad:
            print('ERRO: linhas inválidas em', n, w, bad); skipped += 1; continue
        if g in F.GENERIC_GROUPS and not by_name(g):       # nome genérico só vai para "Outros" se o usuário não tiver criado uma categoria com esse nome (ele criou "Animais")
            cat = 'other'
        else:
            # série = franquia: vai para a categoria dela; se ainda não existe na galeria, a categoria é criada
            cat = by_name(g) or F.GROUP_MAP.get(g) or (by_group[g].most_common(1)[0][0] if g in by_group else tplfile.slug(g))
            ensure_cat(cat, g)
        want = int(opts.get('plates', 1)); pl = lambda r: -(-max(len(x) for x in r) // 50) * -(-len(r) // 50)
        if not a.keep_big and pl(rows) > want:
            # prioridade é 1 placa; só fica com mais de uma quem pediu (opts.plates) e, mesmo assim, no máximo `want` placas
            old_dim = (len(rows[0]), len(rows)); size = 50 if want == 1 else 100
            rows = shrink.shrink(rows, size, 'bias', empty_at=0.6)
            while pl(rows) > want and size > 50: size -= 1; rows = shrink.shrink(rows, size, 'bias', empty_at=0.6)
            print('reduzido para %d placa(s):' % want, n, '%dx%d -> %dx%d' % (old_dim[0], old_dim[1], len(rows[0]), len(rows)))
            rows = loose.fix_loose(rows)
        grp = cat_name(cat, g)
        base = tplfile.slug(n); i = base; k = 2
        while i in ids: i = '%s-%d' % (base, k); k += 1
        ids.add(i); names.add(n)
        items.append({'id': i, 'cat': cat, 'group': grp, 'name': n, 'rows': rows}); by_group.setdefault(grp, Counter())[cat] += 1
        added += 1
if nloose: print('contas soltas removidas/ligadas nos itens recebidos:', nloose)
print('acrescentados:', added, '| pulados:', skipped, '| trocados:', replaced, '| total:', len(items))
if a.dry: print('(--dry: nada foi gravado)')
elif added or replaced:
    tplfile.write(a.templates, d['legend'], d['cfg'], items, d.get('removed'), allow=allow, readd=readd)
    print('gravado:', a.templates, '(cópia de segurança em tools/backups/)')
