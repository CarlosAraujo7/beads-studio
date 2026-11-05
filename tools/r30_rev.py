"""Revisão dos moldes da remessa 30 que o dono citou no chat (2026-11-05, depois da "grande revisão" dele gravada pelo app): "só precisa fazer revisões nesses que mandei
em anexo, em geral são revisões leves, ver melhorias como na seras e no alucard, ou ajustar um pouquinho da coloração do okarun, ajustar principalmente os olhos dos
personagens no geral e rostos". LEI DO CATÁLOGO: só os moldes que ele mandou (pelo nome, nas capturas) e POR CIMA das linhas que estão no catálogo (as edições dele ficam);
Seras e Alucard ("ver melhorias") são reconvertidos, porque ele não tinha mexido neles.
  python tools/r30_rev.py build ["trecho" ...]          monta data/r30_rev_new.json (nome -> linhas novas) a partir do catálogo atual
  python tools/r30_revsheet.py "trecho" ... --new        folha de leitura com o resultado
  BEADS_ALTERAR_EXISTENTES=1 python tools/r30_rev.py apply [--dry]   grava (só se o molde ainda está como o build leu; de 40 em 40; cópia inteira antes)
  BEADS_ALTERAR_EXISTENTES=1 python tools/r30_rev.py revert           volta (só nos que ainda estão como esta ferramenta deixou)
Operações (mesmo formato do TOUCH6 da remessa 29): ('block', linha, coluna, [linhas de símbolos]) com leg = símbolo -> código ('.' = vazio, ' ' = não mexe);
('map', l0, l1, c0, c1, {código: código}); ('sym', l0, l1, a2, 'L'|'R', c0, c1); ('paint', l0, l1, c0, c1) = tudo que não é a pele principal do retângulo vira essa pele (boca);
('set', {(linha, coluna): código}) = conta a conta (lista calculada pela cor da arte em tools/r30_eyesheet.art_cells)."""
import os, sys, json, shutil, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import tplfile, loose

PATH = os.path.join(os.path.dirname(HERE), 'templates.js')
D = os.path.join(HERE, 'data')
NEW = os.path.join(D, 'r30_rev_new.json')
BASE = os.path.join(D, 'r30_rev_base.json')
APPLIED = os.path.join(D, 'r30_rev_applied.json')


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


# ------------------------------------------------------------------ reconversões (Seras e Alucard: "ver melhorias"; ele não tinha mexido neles)
def green_fringe(im):
    """franja verde (efeito de aberração cromática da arte) em volta do traço preto: vira máscara para o cv2.inpaint, senão sobra conta verde no contorno"""
    import cv2
    f = im.astype(np.float32) / 255.0; r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx = f.max(axis=2); mn = f.min(axis=2); s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    m = ((g > r + 0.10) & (g > b + 0.04) & (s > 0.25)).astype(np.uint8)
    return cv2.dilate(m, np.ones((3, 3), np.uint8)) > 0


def reconv(idx, name, post=None, **kw):
    """reconverte pela mesma rota da remessa 30 (illus6.convert6 via ill6 da 29) com a imagem já repintada (franja verde) e os kw dados; sem boca (no_mouth30)"""
    def f():
        import cv2
        from PIL import Image
        import r30_exfinal as X
        P = X.P
        tmp = os.path.join(X.OUT, f'_r30rev_{idx}.png')
        im = np.array(Image.open(X.F[idx]).convert('RGB'))
        Image.fromarray(cv2.inpaint(im, green_fringe(im).astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)).save(tmp)
        old = X.F[idx]; X.F[idx] = tmp
        try:
            P.CUR[0] = name
            a = dict(X.CH6); a.update(kw)
            box = a.pop('box', None); clear = a.pop('clear', ()); skin = a.pop('skin', True)
            r = P.ill6(idx, a, box=box, clear=clear, skin=skin)
        finally:
            X.F[idx] = old
        if post: r = post(r)
        r = X.no_mouth30(r)
        return X.fin(X.lg(r))
    return f


def yellow_all(ref=(228, 187, 47), tol=60):
    """fundo amarelo EM QUALQUER LUGAR (também os pedaços fechados entre o braço, a arma e a capa): para figura que não tem amarelo (Alucard)"""
    def f(rgb):
        return np.linalg.norm(rgb.astype(np.float32) - np.array(ref, np.float32), axis=2) < tol
    return f


REV = {}          # nome no catálogo -> dict(reconv=função opcional, leg={...}, ops=[...])


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
        rows = t['reconv']() if t.get('reconv') else cur
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
    bk = os.path.join(HERE, 'backups', 'pre-r30-rev.js' if not revert else 'pre-r30-rev-revert.js')
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
    import r30_rev_defs          # noqa: F401  (preenche o REV do módulo r30_rev, que é outro objeto que o deste __main__)
    import r30_rev as _m
    REV.update(_m.REV)
    a = sys.argv[1:]
    if not a or a[0] == 'build': build([x for x in a[1:] if not x.startswith('--')])
    elif a[0] == 'apply': apply(dry='--dry' in a)
    elif a[0] == 'revert': apply(revert=True, dry='--dry' in a)
