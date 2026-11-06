"""Revisão da remessa 31 pedida pelo dono no chat (2026-11-06): "Tentei passar a remessa 31 usando o sonnet e a maioria dos moldes saiu ruim, agora quero que revise
usando o opus, veja como está a remessa em relação a imagem original e ajuste". Pedido sobre a remessa inteira (só os moldes da remessa 31), POR CIMA das linhas que estão
no catálogo; as 3 folhas de figuras encostadas (Assassination Classroom ×2 e o trio da WWE) vêm da reconversão com a máscara nova (data/r31v2_raw_120.json, `v2=True`).
  python tools/r31_rev.py build ["trecho" ...]          monta data/r31_rev_new.json
  BEADS_ALTERAR_EXISTENTES=1 python tools/r31_rev.py apply [--dry]  /  revert
Operações: as mesmas do tools/r30_rev.py (block, map, sym, set, paint, fn)."""
import os, sys, json, shutil, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import tplfile, loose

PATH = os.path.join(os.path.dirname(HERE), 'templates.js')
D = os.path.join(HERE, 'data')
NEW = os.path.join(D, 'r31_rev_new.json')
BASE = os.path.join(D, 'r31_rev_base.json')
APPLIED = os.path.join(D, 'r31_rev_applied.json')


def sha(rows): return hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest()[:12]


# ------------------------------------------------------------------ olhos (modelo da "Rei Ayanami (chibi, fundo amarelo)", que ele achou impecável)
def E4L(): return ['KKKK', 'KDHD', 'WMMM', ' LLL']
def E4R(): return ['KKKK', 'DHDK', 'MMMW', 'LLL ']
E3L = ['KKK', 'DHD', 'WMM', ' LL']          # 3 de largura
E3R = ['KKK', 'DHD', 'MMW', 'LL ']
E2 = ['KK', 'DH', 'ML']                     # rosto pequeno
E2B = ['KK', 'HD', 'LM']                    # o mesmo com o brilho do outro lado


def eyes(yl, xl, yr, xr, D_, M, Lt, skin='E11', tl=None, tr=None, extra=(), leg=None, pre=()):
    """pre = operações ANTES dos olhos (limpeza do rosto: um 'map' depois dos olhos apagaria o brilho branco); extra = depois"""
    lg_ = {'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': D_, 'M': M, 'L': Lt, 'E': skin}
    lg_.update(leg or {})
    return dict(leg=lg_, ops=list(pre) + [('block', yl, xl, tl or E4L()), ('block', yr, xr, tr or E4R())] + list(extra))



REV = {}          # nome no catálogo -> dict(v2=True opcional, leg={...}, ops=[...])
_V2 = {}


def V2ROWS():
    if not _V2:
        _V2.update({x[0]: x[2] for x in json.load(open(os.path.join(D, 'r31v2_raw_120.json'), encoding='utf-8'))})
    return _V2


# ------------------------------------------------------------------ montagem
def apply_ops(rows, t):
    from palette import ALL
    L = {p['code']: p['letter'] for p in ALL}
    g = [list(r) for r in rows]; H, W = len(g), len(g[0]); leg = t.get('leg', {})
    def put(y, x, ch):
        if ch == ' ' or not (0 <= y < H and 0 <= x < W): return
        g[y][x] = '.' if ch == '.' else L[leg[ch]]
    for op in t.get('ops', []):
        if op[0] == 'block':
            _, r0, c0, lines = op
            for dy, s in enumerate(lines):
                for dx, ch in enumerate(s): put(r0 + dy, c0 + dx, ch)
        elif op[0] == 'map':
            _, r0, r1, c0, c1, mp = op
            ml = {L[a]: L[b] for a, b in mp.items()}
            for y in range(max(0, r0), min(H, r1 + 1)):
                for x in range(max(0, c0), min(W, c1 + 1)):
                    if g[y][x] in ml: g[y][x] = ml[g[y][x]]
        elif op[0] == 'sym':
            _, r0, r1, a2, side, c0, c1 = op
            for y in range(r0, r1 + 1):
                for x in range(c0, c1 + 1):
                    if (side == 'L' and 2 * x < a2) or (side == 'R' and 2 * x > a2):
                        xm = a2 - x
                        if 0 <= xm < W and 0 <= y < H: g[y][xm] = g[y][x]
        elif op[0] == 'set':                     # ('set', {(linha, coluna): código}) conta a conta, com o código direto
            for (y, x), code in op[1].items():
                if 0 <= y < H and 0 <= x < W: g[y][x] = '.' if code == '.' else L[code]
        elif op[0] == 'paint':
            import r29_exfinal as P
            rr = P.paint_mouth([''.join(r) for r in g], op[1:5], verbose=False)
            g = [list(r) for r in rr]
        elif op[0] == 'fn':
            rr = op[1]([''.join(r) for r in g]); g = [list(r) for r in rr]; H, W = len(g), len(g[0])
    return [''.join(r) for r in g]


def build(qs):
    d = tplfile.parse(PATH); by = {t['name']: t for t in d['items']}
    new = json.load(open(NEW, encoding='utf-8')) if os.path.exists(NEW) and qs else {}
    base = json.load(open(BASE, encoding='utf-8')) if os.path.exists(BASE) and qs else {}
    for n, t in REV.items():
        if qs and not any(q.lower() in n.lower() for q in qs): continue
        if n not in by: print('NÃO ESTÁ NO CATÁLOGO:', n); continue
        cur = by[n]['rows']
        rows = t['reconv']() if t.get('reconv') else (V2ROWS()[n] if t.get('v2') else cur)
        rows = apply_ops(rows, t)
        if loose.loose_count(rows): rows = loose.fix_loose(rows)
        H, W = len(rows), len(rows[0])
        if H > 50 or W > 50: raise SystemExit(f'{n}: {W}x{H} passa de 50')
        new[n] = rows; base[n] = sha(cur)
        ch = sum(1 for a, b in zip(''.join(cur), ''.join(rows)) if a != b) if (len(cur), len(cur[0])) == (H, W) else None
        print(f'- {n}: {len(cur[0])}x{len(cur)} -> {W}x{H}' + (f', {ch} contas mudaram' if ch is not None else ' (reconvertido)'))
    for n in list(new):
        if n not in REV: del new[n]; base.pop(n, None)
    json.dump(new, open(NEW, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(new), 'moldes em', NEW)


def apply(revert=False, dry=False):
    new = json.load(open(NEW, encoding='utf-8')); base = json.load(open(BASE, encoding='utf-8'))
    applied = json.load(open(APPLIED, encoding='utf-8')) if os.path.exists(APPLIED) else {}
    d = tplfile.parse(PATH); by = {t['name']: t for t in d['items']}
    todo = []
    if revert:
        for n, v in applied.items():
            if n in by and sha(by[n]['rows']) == sha(v['new']): todo.append((n, v['new'], v['old']))
            else: print('fica (mudou depois ou saiu):', n)
    else:
        for n, rows in new.items():
            if n not in by: print('NÃO ESTÁ NO CATÁLOGO:', n); continue
            cur = by[n]['rows']
            if sha(cur) != base.get(n): print('PULEI (o molde mudou depois do build):', n); continue
            if rows != cur: todo.append((n, cur, rows))
    print(('reverter' if revert else 'gravar'), len(todo), 'moldes')
    if dry or not todo: return
    bk = os.path.join(HERE, 'backups', 'pre-r31-rev.js' if not revert else 'pre-r31-rev-revert.js')
    if os.path.exists(bk):
        root, ext = os.path.splitext(bk); bk = root + datetime.datetime.now().strftime('-%Y%m%d-%H%M%S') + ext
    shutil.copy(PATH, bk); print('cópia inteira em', bk)
    for k in range(0, len(todo), tplfile.MAX_POR_VEZ):
        lote = {n: (o, nr) for n, o, nr in todo[k:k + tplfile.MAX_POR_VEZ]}
        d = tplfile.parse(PATH); allow = set()
        for t in d['items']:
            if t['name'] in lote and t['rows'] == lote[t['name']][0]:
                t['rows'] = lote[t['name']][1]; allow.add(t['id'])
        tplfile.write(PATH, d['legend'], d['cfg'], d['items'], d.get('removed'), allow=allow)
        print('lote gravado:', len(allow))
    for n, o, nr in todo:
        if revert: applied.pop(n, None)
        else: applied[n] = {'old': applied.get(n, {}).get('old', o), 'new': nr}
    json.dump(applied, open(APPLIED, 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    import r31_rev_defs          # noqa: F401  (preenche o REV do módulo r30_rev, que é outro objeto que o deste __main__)
    import r31_rev as _m
    REV.update(_m.REV)
    a = sys.argv[1:]
    if not a or a[0] == 'build': build([x for x in a[1:] if not x.startswith('--')])
    elif a[0] == 'apply': apply(dry='--dry' in a)
    elif a[0] == 'revert': apply(revert=True, dry='--dry' in a)
