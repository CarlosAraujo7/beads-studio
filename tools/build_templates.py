import sys, json, re, unicodedata, os
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import img2tpl as T

# trava: se o templates.js foi gravado pelo app (ou acrescentado por add_templates.py) ele é a fonte da verdade; regenerar tudo apagaria o que o usuário fez
_tpl_js = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates.js')
if os.path.exists(_tpl_js) and 'window.TPL_BAKED' in open(_tpl_js, encoding='utf-8').read() and '--force' not in sys.argv:
    sys.exit('PARADO: o templates.js foi gravado pelo app / por add_templates.py e conteria trabalho do usuário que este build apagaria.\n'
             'Para acrescentar uma remessa use:  python tools/add_templates.py tools/data/finalN.json\n'
             'Só use --force para recomeçar do zero (uma cópia fica em tools/backups/).')

def load(f): return json.load(open(os.path.join(SP, 'data', f), encoding='utf-8'))

# ordem de montagem: cada arquivo pode sobrescrever (por nome) um template anterior
J = []
index = {}
def add(name, grp, rows):
    if name in index: J[index[name]] = (name, grp, rows)
    else: index[name] = len(J); J.append((name, grp, rows))
for f in ('final1.json', 'final2.json', 'final3.json', 'final4.json', 'final5.json', 'final6.json'):
    for name, grp, rows in load(f): add(name, grp, rows)

# correções feitas a pedido (troca de desenho, nome ou série) e remoções
REMOVE_ALL = []
for fxf in ('fixes.json', 'fixes2.json'):
    fx = load(fxf)
    for f in fx['fixes']:
        old = f['match']
        if old not in index: print('AVISO: nao achei', old); continue
        name, grp, rows = J[index[old]]
        J[index[old]] = (f['name'], f['group'] or grp, f['rows'] or rows)
        index[f['name']] = index.pop(old)
    REMOVE_ALL += fx['remove']
for n in REMOVE_ALL:
    if n not in index: print('AVISO: nao achei para remover', n); continue
    i = index.pop(n); J[i] = None
J = [x for x in J if x]

# sem contorno preto (menos onde o preto faz parte do desenho) e sem pecas soltas
import polish as PL
json.dump(J, open(os.path.join(OUT, 'prepolish.json'), "w", encoding="utf-8"), ensure_ascii=False)
RAWJ = {n: r for n, g, r in J}
J = [(n, g, PL.polish(n, r)) for n, g, r in J]
index = {n: i for i, (n, g, r) in enumerate(J)}
# desenhos refeitos a mao/foto (ja sem contorno): entram depois do polimento
if os.path.exists(os.path.join(SP, 'data', 'fixes3.json')):
    fx3 = load('fixes3.json')
    for f in fx3['fixes']:
        old = f['match']
        if old not in index: print('AVISO fixes3: nao achei', old); continue
        i = index[old]; name, grp, rows = J[i]
        J[i] = (f['name'], f['group'] or grp, PL.O.connect_components(f['rows']))
        index[f['name']] = index.pop(old)
    for f in fx3.get('adds', []):
        J.append((f['name'], f['group'], PL.O.connect_components(f['rows'])))
    drop = set(fx3.get('remove', []))
    J = [x for x in J if x[0] not in drop]
    index = {n: i for i, (n, g, r) in enumerate(J)}

# simetria: emblemas e desenhos de frente espelham a metade mais cheia
J = [(n, g, PL.O.bridge(PL.O.connect_components(PL.symmetrize(r)), 6) if PL.symmetric_name(n) else r) for n, g, r in J]

# a pedido: voltam EXATAMENTE como estavam antes de mexer nos contornos (sem polimento, sem espelhar, sem ligar pecas)
EXACT = {'Reborn e Leon (Hitman Reborn)': None, 'Rukia (Bleach)': None, 'Chibi de cabelo branco': 'Frieren (chibi)', 'Allen Walker (D.Gray-man)': None,
         'Emblema de Fairy Tail': None, 'Psyduck': None, 'Pikachu surpreso': None, 'Dovahkiin (Skyrim)': None, 'Cowboy (Red Dead Redemption)': None,
         'Logo de Red Dead Redemption II': None, 'Coruja do Duolingo': None, 'Aku Aku (Crash Bandicoot)': None, 'Chapéu Seletor': None,
         'Professora McGonagall': None, 'Michael Jackson': None, 'Groot (chibi)': None, 'Chaves': None, 'Galinha': None,
         'Peashooter (Plants vs Zombies)': None, 'Banguela (Toothless)': None, 'Chikorita': None}
def dobby_sem_cauda():
    r = [list(x) for x in RAWJ['Dobby']]
    for y in range(len(r)):
        for x in range(len(r[0])):
            if y >= 15 and x >= 16 and r[y][x] == 'k': r[y][x] = '.'          # so a cauda preta
    return PL.O.trim([''.join(x) for x in r])
_new = []
for n, g, r in J:
    if n == 'Dobby': _new.append((n, g, dobby_sem_cauda()))
    elif n in EXACT: _new.append((EXACT[n] or n, g, RAWJ[n]))
    else: _new.append((n, g, r))
J = _new

# remessa 5: ja chega pronta (fundo, contorno e cores tratados em r5.py / r5_final.py) - entra sem polimento
if os.path.exists(os.path.join(SP, 'data', 'final7.json')):
    _have = {n for n, g, r in J}
    for n, g, r in load('final7.json'):
        if n in _have: print('AVISO: nome repetido na remessa 5', n); continue
        J.append((n, g, r))

# remessa 6: idem (r6.py / r6_exfinal.py)
if os.path.exists(os.path.join(SP, 'data', 'final8.json')):
    _have = {n for n, g, r in J}
    for n, g, r in load('final8.json'):
        if n in _have: print('AVISO: nome repetido na remessa 6', n); continue
        J.append((n, g, r))

# remessa 7: idem (r7_exfinal.py)
if os.path.exists(os.path.join(SP, 'data', 'final9.json')):
    _have = {n for n, g, r in J}
    for n, g, r in load('final9.json'):
        if n in _have: print('AVISO: nome repetido na remessa 7', n); continue
        J.append((n, g, r))

# remessa 8: idem (r8_exfinal.py)
if os.path.exists(os.path.join(SP, 'data', 'final10.json')):
    _have = {n for n, g, r in J}
    for n, g, r in load('final10.json'):
        if n in _have: print('AVISO: nome repetido na remessa 8', n); continue
        J.append((n, g, r))

# remessa 9: idem (r9_exfinal.py)
if os.path.exists(os.path.join(SP, 'data', 'final11.json')):
    _have = {n for n, g, r in J}
    for n, g, r in load('final11.json'):
        if n in _have: print('AVISO: nome repetido na remessa 9', n); continue
        J.append((n, g, r))

# remessa 10: idem (r10_exfinal.py)
if os.path.exists(os.path.join(SP, 'data', 'final12.json')):
    _have = {n for n, g, r in J}
    for n, g, r in load('final12.json'):
        if n in _have: print('AVISO: nome repetido na remessa 10', n); continue
        J.append((n, g, r))

# séries reorganizadas por nome
REGROUP = {
    'Coruja do Duolingo': 'Outros jogos', 'BMO (Hora de Aventura)': 'Hora de Aventura', 'Peashooter (Plants vs Zombies)': 'Outros jogos',
    'Pou': 'Outros jogos', 'Piu-Piu': 'Looney Tunes', 'Piu-Piu com gorro': 'Looney Tunes', 'Galinha': 'Animais', 'Unicórnio arco-íris': 'Outros desenhos',
    'Aku Aku (Crash Bandicoot)': 'Outros jogos', 'Coragem, o Cão Covarde': 'Outros desenhos',
    'Sagrado Coração de Jesus': 'Símbolos e objetos', 'Nossa Senhora Aparecida': 'Símbolos e objetos', 'A Noite Estrelada': 'Símbolos e objetos',
    'Carta UNO': 'Símbolos e objetos', 'Pintinho': 'Animais', 'Banguela (Toothless)': 'Como Treinar o seu Dragão',
    'Garoto pescador (chapéu de palha)': 'Outros', 'Lanterna Verde': 'Super-heróis',
    'Gojo': 'Jujutsu Kaisen', 'Gojo (peça)': 'Jujutsu Kaisen', 'Máscara Hollow (Bleach)': 'Bleach', 'Rukia (Bleach)': 'Bleach', 'Vegeta Super Saiyajin Blue': 'Dragon Ball',
}
RENAME_GROUP = {'Animes': 'Outros animes', 'Desenhos e jogos': 'Outros desenhos', 'Filmes e séries': 'Outros filmes e séries'}
J = [(n, RENAME_GROUP.get(REGROUP.get(n, g), REGROUP.get(n, g)), r) for n, g, r in J]

# categorias (ordem da galeria) e a série de cada uma
from cats import CATS
cat_of = {}; order_of = {}
for cid, cname, series in CATS:
    for k, s in enumerate(series): cat_of[s] = cid; order_of[s] = (len(order_of), k)
unknown = sorted({g for n, g, r in J if g not in cat_of})
if unknown: print('SERIES SEM CATEGORIA:', unknown)
catpos = {c[0]: i for i, c in enumerate(CATS)}
J.sort(key=lambda t: (catpos.get(cat_of.get(t[1], 'other'), 99), CATS[catpos.get(cat_of.get(t[1], 'other'), 9)][2].index(t[1]) if t[1] in cat_of else 99))

def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')
LEG = {T.PAL[i][0]: T.LETTER[T.PAL[i][0]] for i in range(24)}
out = ['// Templates de beads - cada letra e um codigo de cor Pindou (veja TPL_LEGEND).',
       '// Formato: {id:"x", cat:"categoria", group:"Serie", name:"Nome", rows:["....kk....", ...]}  ("." = vazio)',
       'window.TPL_LEGEND = ' + json.dumps({v: k for k, v in LEG.items()}) + ';',
       'window.TEMPLATES = [']
ids = set()
for name, grp, rows in J:
    i = slug(name) or 'item'; base = i; k = 2
    while i in ids: i = f'{base}-{k}'; k += 1
    ids.add(i)
    bad = [c for r in rows for c in r if c != '.' and c not in {v for v in LEG.values()}]
    assert not bad and len({len(r) for r in rows}) == 1, name
    out.append('{id:%s,cat:%s,group:%s,name:%s,rows:[' % (json.dumps(i), json.dumps(cat_of.get(grp, 'other')), json.dumps(grp, ensure_ascii=False), json.dumps(name, ensure_ascii=False)))
    out.append(',\n'.join(json.dumps(r) for r in rows))
    out.append(']},')
out.append('];')
raise SystemExit('DESATIVADO (2026-10-31): reconstruir o catálogo apagaria o trabalho do usuário. Veja CLAUDE.md §4.9.')
import tplfile; tplfile.backup(os.path.join(os.path.dirname(SP), 'templates.js'))
open(os.path.join(os.path.dirname(SP), 'templates.js'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
from collections import Counter
cnt = Counter(cat_of.get(g, 'other') for n, g, r in J)
print(len(J), 'templates gravados')
for cid, cname, series in CATS:
    print(' ', cname.encode('ascii', 'replace').decode(), cnt[cid], '|', ', '.join(f"{s}:{sum(1 for n, g, r in J if g == s)}" for s in series).encode('ascii', 'replace').decode())
