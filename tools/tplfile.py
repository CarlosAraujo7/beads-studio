"""Ler e gravar o templates.js do projeto (o mesmo formato que o app grava pelo botão "Gravar no catálogo").

    from tplfile import parse, write
    d = parse(path)          # {'legend': {...}, 'cfg': {...}|None, 'baked': str|None, 'items': [{'id','cat','group','name','rows'}]}
    write(path, d['legend'], d['cfg'], d['items'])   # faz cópia de segurança em tools/backups/ antes de gravar
"""
import os, re, json, unicodedata, datetime, shutil

_STR = r'"(?:[^"\\]|\\.)*"'
ITEM_RE = re.compile(r'\{id:(%s),cat:(%s),group:(%s),name:(%s),rows:\[(.*?)\n\]\}' % (_STR, _STR, _STR, _STR), re.S)
HEADER = [
    '// Templates de beads - cada letra e um codigo de cor Pindou (veja TPL_LEGEND).',
    '// Formato: {id:"x", cat:"categoria", group:"Serie", name:"Nome", rows:["....kk....", ...]}  ("." = vazio)',
    '// Este arquivo e gravado pelo proprio app (Templates > Gravar no catalogo) e acrescentado por tools/add_templates.py.',
]


def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'item'


def parse(path):
    text = open(path, encoding='utf-8').read()
    legend = json.loads(re.search(r'window\.TPL_LEGEND\s*=\s*(\{.*?\});', text, re.S).group(1))
    m = re.search(r'window\.TPL_CATS_CFG\s*=\s*(\{.*?\});\s*\n', text, re.S)
    cfg = json.loads(m.group(1)) if m else None
    m = re.search(r'window\.TPL_BAKED\s*=\s*("[^"]*");', text)
    baked = json.loads(m.group(1)) if m else None
    m = re.search(r'window\.TPL_REMOVED\s*=\s*(\[.*?\]);', text, re.S)
    removed = json.loads(m.group(1)) if m else []
    items = []
    for m in ITEM_RE.finditer(text):
        rows = json.loads('[' + m.group(5) + ']')
        items.append({'id': json.loads(m.group(1)), 'cat': json.loads(m.group(2)), 'group': json.loads(m.group(3)),
                      'name': json.loads(m.group(4)), 'rows': rows})
    return {'legend': legend, 'cfg': cfg, 'baked': baked, 'removed': removed, 'items': items}


def render(legend, cfg, items, removed=None):
    out = list(HEADER)
    out.append('window.TPL_LEGEND = ' + json.dumps(legend, ensure_ascii=False) + ';')
    if cfg is not None:
        out.append('window.TPL_CATS_CFG = ' + json.dumps(cfg, ensure_ascii=False) + ';')
    out.append('window.TPL_BAKED = ' + json.dumps(datetime.datetime.now().isoformat(timespec='seconds')) + ';')
    if removed: out.append('window.TPL_REMOVED = ' + json.dumps(removed, ensure_ascii=False) + ';')
    out.append('window.TEMPLATES = [')
    for t in items:
        out.append('{id:%s,cat:%s,group:%s,name:%s,rows:[' % tuple(json.dumps(t[k], ensure_ascii=False) for k in ('id', 'cat', 'group', 'name')))
        out.append(',\n'.join(json.dumps(r) for r in t['rows']))
        out.append(']},')
    out.append('];')
    return '\n'.join(out) + '\n'


def backup(path, keep=30):
    """copia o arquivo atual para tools/backups/templates-AAAAMMDD-HHMMSS.js (guarda as últimas `keep`)"""
    if not os.path.exists(path): return None
    bdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups'); os.makedirs(bdir, exist_ok=True)
    dst = os.path.join(bdir, 'templates-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.js')
    shutil.copy(path, dst)
    olds = sorted(f for f in os.listdir(bdir) if f.startswith('templates-') and f.endswith('.js'))
    for f in olds[:-keep]: os.remove(os.path.join(bdir, f))
    return dst


class CatalogoProtegido(Exception):
    pass


MAX_POR_VEZ = 40


def guard(path, items, removed=None, allow=(), readd=()):
    """TRAVA pedida pelo usuário (2026-10-31; CLAUDE.md §4.9): gravar só pode ACRESCENTAR moldes. Mudar ou apagar um molde existente exige o id dele em `allow`, recolocar um nome que ele excluiu exige o nome em `readd`
    e nunca mais de MAX_POR_VEZ moldes de uma vez. Assim nenhuma ferramenta antiga ou algoritmo em massa consegue mexer no catálogo, mesmo por engano."""
    if not os.path.exists(path): return
    old = parse(path); new = {t['id']: t for t in items}; allow = set(allow); readd = set(readd)
    changed = [t for t in old['items'] if t['id'] not in new or any(t[k] != new[t['id']][k] for k in ('rows', 'name', 'cat'))]
    if changed and os.environ.get('BEADS_ALTERAR_EXISTENTES') != '1':
        raise CatalogoProtegido('GRAVAÇÃO RECUSADA: CATÁLOGO CONGELADO (pedido do dono, 2026-11-03: "a partir de agora não é pra mexer em nenhum molde que já está no catálogo, só em novas imagens para virar novos moldes"). '
                                'Mudaria/apagaria %d molde(s), ex.: %s. Só se acrescenta. A trava só se solta com BEADS_ALTERAR_EXISTENTES=1, e isso só se ELE pedir NO CHAT aquele molde pelo nome.' % (len(changed), [t['name'] for t in changed[:5]]))
    bad = [t['name'] for t in changed if t['id'] not in allow]
    if bad: raise CatalogoProtegido('GRAVAÇÃO RECUSADA: mudaria %d molde(s) sem autorização, ex.: %s' % (len(bad), bad[:8]))
    if len(changed) > MAX_POR_VEZ: raise CatalogoProtegido('GRAVAÇÃO RECUSADA: %d moldes de uma vez (máximo %d)' % (len(changed), MAX_POR_VEZ))
    oldids = {t['id'] for t in old['items']}; oldrem = set(old.get('removed') or [])
    back = [t['name'] for t in items if t['id'] not in oldids and t['name'] in oldrem and t['name'] not in readd]
    if back: raise CatalogoProtegido('GRAVAÇÃO RECUSADA: traria de volta molde(s) que ele excluiu: %s' % back[:8])
    lost = oldrem - set(removed or []) - readd
    if lost: raise CatalogoProtegido('GRAVAÇÃO RECUSADA: apagaria %d nome(s) da lista de excluídos, ex.: %s' % (len(lost), sorted(lost)[:5]))


def write(path, legend, cfg, items, removed=None, do_backup=True, allow=(), readd=()):
    guard(path, items, removed, allow, readd)
    if do_backup: backup(path)
    open(path, 'w', encoding='utf-8').write(render(legend, cfg, items, removed))
