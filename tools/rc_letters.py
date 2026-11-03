"""CORES DOS MOLDES SEM IMAGEM DE ORIGEM (2026-11-03). Pedido do dono: "revise as cores de pele de TODOS os personagens". Os ~580 moldes com imagem de origem foram refeitos a partir dela (rc_plan.py / rc_bulk.py). Os
que sobram (remessas 1-4, folhas antigas, os "(grande)" de 4 placas...) não têm como reler a imagem; neles só se troca a COR DE CADA LETRA ANTIGA pela conta real que as fontes das imagens refeitas escolheram
na maioria das vezes (tabela aprendida em 568 moldes: tools/out/_learned_map.json), escolhendo entre as candidatas (>= 15%) a mais perto da cor que a letra mostrava ANTES da paleta nova.
Nenhuma conta muda de lugar; só as letras listadas em GLOBAL (marrons que viraram laranja, verde-oliva que virou limão, pele laranja ou amarelada, vinho, cinza escuro que virou preto...). O vermelho F8 NÃO é tocado
(o carmim virava marrom: ver CLAUDE.md §7.43). Os "(grande)" cujo irmão pequeno já foi refeito usam a troca que o irmão teve (mapa de letra por molde, quando ela vale em >= 50% das contas da letra).
uso:  python tools/rc_letters.py list
      python tools/rc_letters.py sheet PREFIXO [--ids a,b] [--per 24]      (folhas ANTES | AGORA | NOVO, nada é gravado)
      python tools/rc_letters.py apply --autorizado [--ids a,b] [--max 40]
      python tools/rc_letters.py revert --autorizado [--ids a,b]
Registro: tools/data/recolor_applied.json (mapa 'letras'), lote em tools/data/rcletters_lote.json, original de cada molde em tools/backups/recolor-originais.json, cópia inteira em tools/backups/pre-recon-letras.js."""
import os, sys, json, shutil, datetime, collections, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import tplfile, recolor_apply as RA, remap_cores as RC

T = RA.T
PLAN = os.path.join(HERE, 'out', 'rc_plan.json')
LOTE = os.path.join(HERE, 'data', 'rcletters_lote.json')
FULL = os.path.join(HERE, 'backups', 'pre-recon-letras.js')
LETTER_OF = {c['code']: c['letter'] for c in RC.NEW}
NB = RC.NEW_BY_L

# código antigo -> código novo (decidido olhando a tabela aprendida: a conta que as imagens escolheram, a mais parecida com o que a letra mostrava antes)
GLOBAL = {
    # marrons: na paleta antiga eram escuros; os códigos F10/G13/G7/G6 viraram LARANJA
    'F10': 'G8', 'F7': 'G8', 'F11': 'G8', 'G13': 'F11', 'G7': 'F11', 'G6': 'G7',
    # verdes escuros/oliva
    'B17': 'B11', 'B12': 'B15', 'B8': 'B12', 'B5': 'B8', 'B4': 'B8', 'B2': 'B5', 'B14': 'B5', 'B16': 'B13', 'B7': 'B12',
    # azuis acinzentados
    'C16': 'C9', 'C7': 'C8', 'C8': 'C16', 'C15': 'C11',
    # roxo e rosa
    'D14': 'D21', 'E4': 'E3',
    # amarelo-âmbar
    'A6': 'A10',
    # cinza escuro (o H6 novo é quase igual ao preto: o sombreado sumia)
    'H6': 'H5',
    # PELE: G5 virou laranja vivo, G9 amarelo-ouro, G1 creme-amarelado; G3 ficou pálido demais
    'G5': 'A12', 'G3': 'A12', 'G2': 'A9', 'G1': 'E14', 'E14': 'E11', 'G9': 'G2',
    # (2ª passada, depois de olhar o Pennywise de capa amarela: o rosto BRANCO virou rosa-pele) quase brancos e cinzas claros que viraram rosa/lilás
    'E8': 'H2', 'D19': 'H1', 'C13': 'C14', 'C6': 'D1',
    # rosas, vinhos e roxos: a conta nova mais perto do que a letra mostrava antes
    'E5': 'E7', 'E13': 'F7', 'E7': 'F7', 'E10': 'E6', 'E3': 'F14', 'E9': 'E3', 'D12': 'D19', 'D20': 'D18',
    # verde-azulado, oliva e amarelo-mostarda; cinzas/marrons escuros; pretos esverdeados
    'B19': 'B12', 'B18': 'B17', 'A15': 'A11', 'A14': 'F2', 'M6': 'M9', 'M5': 'M6', 'G17': 'H5', 'B15': 'H7', 'B11': 'H7',
}
GMAP = {LETTER_OF[a]: LETTER_OF[b] for a, b in GLOBAL.items()}


def sibling_map(small_id, d, orig):
    """troca de letra que o irmão pequeno teve (original -> atual): letra antiga -> letra nova mais comum, só se vale em >= 50% das contas da letra"""
    o = orig.get(small_id); cur = next((t['rows'] for t in d['items'] if t['id'] == small_id), None)
    if o is None or cur is None or len(o) != len(cur) or len(o[0]) != len(cur[0]): return None
    M = collections.defaultdict(collections.Counter)
    for r1, r2 in zip(o, cur):
        for a, b in zip(r1, r2):
            if a != '.' and b != '.': M[a][b] += 1
    out = {}
    for a, c in M.items():
        b, n = c.most_common(1)[0]
        if a != b and n / sum(c.values()) >= 0.5: out[a] = b
    return out


def targets():
    plan = json.load(open(PLAN, encoding='utf-8')); d = tplfile.parse(T); ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
    orig = json.load(open(RA.ORIG, encoding='utf-8')) if os.path.exists(RA.ORIG) else {}
    byname = {t['name']: t for t in d['items']}; out = []
    rm = set(json.load(open(os.path.join(HERE, 'data', 'remap_applied.json'), encoding='utf-8')))        # já passaram pela troca de letras antiga (remap v4): não repito
    for t in d['items']:
        if t['id'] in ap or t['id'] in rm: continue
        st = plan.get(t['id'], {}).get('status')
        if st not in ('manual', 'sem fonte'): continue                 # 'pulado' = decidido olhando (Ned Stark, Caldeirão...): não mexo
        m = dict(GMAP); how = 'global'
        mm = re.match(r'(.*?)\s*\(grande\)$', t['name'])
        if mm and mm.group(1) in byname and byname[mm.group(1)]['id'] in ap:
            sm = sibling_map(byname[mm.group(1)]['id'], d, orig)
            if sm: m = dict(GMAP); m.update(sm); how = 'irmão'
        out.append((t, m, how))
    return d, out


def apply_map(rows, m): return [''.join(m.get(c, c) if c != '.' else '.' for c in r) for r in rows]


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]; ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else None
    if cmd == 'revert': return revert(a, ids)
    d, tg = targets()
    tg = [(t, m, h) for t, m, h in tg if (ids is None or t['id'] in ids)]
    new = {t['id']: apply_map(t['rows'], m) for t, m, h in tg}
    chg = [(t, h) for t, m, h in tg if new[t['id']] != t['rows']]
    if cmd == 'list':
        for t, h in chg: print('%-8s %-14s %s' % (h, t['cat'][:14], t['name'][:60]))
        print(len(chg), 'moldes mudam (de', len(tg), 'sem imagem de origem)'); return
    if cmd == 'sheet':
        sys.path.insert(0, os.path.join(HERE, 'out')); import _np_sheet as S
        per = int(a[a.index('--per') + 1]) if '--per' in a else 24
        S.sheet([t for t, h in chg], os.path.join(HERE, 'out', a[1]), per=per, cols=3, scale=3, newrows=new); return
    if cmd != 'apply': print(__doc__); return
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado (CLAUDE.md 4.9: o dono pediu a revisão das cores de pele de todos os personagens).')
    mx = int(a[a.index('--max') + 1]) if '--max' in a else 40
    if not chg: print('nada a gravar'); return
    if not os.path.exists(FULL): shutil.copy(T, FULL); print('cópia inteira do catálogo:', FULL)
    ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
    orig = json.load(open(RA.ORIG, encoding='utf-8')) if os.path.exists(RA.ORIG) else {}
    lote = json.load(open(LOTE, encoding='utf-8')) if os.path.exists(LOTE) else []
    idl = [t['id'] for t, h in chg]
    for i in range(0, len(idl), mx):
        lot = idl[i:i + mx]; d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
        for k in lot:
            if k not in orig: orig[k] = its[by[k]]['rows']
            its[by[k]] = dict(its[by[k]], rows=new[k])
        json.dump(orig, open(RA.ORIG, 'w', encoding='utf-8'), ensure_ascii=False)
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), do_backup=False, allow=set(lot))
        for k in lot: ap[k] = dict(sha=RA.sha(new[k]), mapa='letras (rc_letters)', data=datetime.date.today().isoformat()); lote.append(k)
        json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(lote, open(LOTE, 'w', encoding='utf-8'))
        print('lote gravado: %d moldes (%d/%d)' % (len(lot), min(i + mx, len(idl)), len(idl)), flush=True)


def revert(a, ids):
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado.')
    ap = json.load(open(RA.APPLIED, encoding='utf-8')); orig = json.load(open(RA.ORIG, encoding='utf-8'))
    lote = json.load(open(LOTE, encoding='utf-8')) if os.path.exists(LOTE) else []
    ids = ids or list(lote); d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}
    cand = [k for k in ids if k in by and k in orig and k in ap and RA.sha(d['items'][by[k]]['rows']) == ap[k]['sha']]
    feitos = []
    for i in range(0, len(cand), 40):
        lot = cand[i:i + 40]; d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
        for k in lot: its[by[k]] = dict(its[by[k]], rows=orig[k])
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), do_backup=False, allow=set(lot))
        for k in lot: ap.pop(k, None); orig.pop(k, None); feitos.append(k)
    json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(orig, open(RA.ORIG, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump([k for k in lote if k not in feitos], open(LOTE, 'w', encoding='utf-8'))
    print('devolvidos: %d | deixados (ele mexeu depois): %d' % (len(feitos), len(ids) - len(feitos)))


if __name__ == '__main__':
    main()
