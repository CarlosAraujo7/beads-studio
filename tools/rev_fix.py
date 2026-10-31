"""Revisão de ~60 moldes das remessas 21-23 pedida pelo usuário (2026-10-31, CLAUDE.md §7.20): olhos, cores, poderes (efeitos), bordas, molduras.
Base de TODO conserto = o catálogo como estava antes desta revisão (`backups/pre-rev.js`, já com as edições que o usuário fez no app); cada molde tem uma lista de operações
(`weak_fix.apply`: wipe / recolor / soften / boost / blocks / put / func / lg, mais as daqui: ramp, bedge, frame) e, opcionalmente, uma reconversão da fonte (`conv`).
  python tools/rev_fix.py build [trecho ...] [--big] [--pv NOME]   gera data/rev_new.json e as folhas antes|depois em out/rev_pv_*.png (fundo roxo)
  python tools/rev_fix.py apply [--dry]                            grava no templates.js SÓ o molde que ainda é igual à base (ou ao que esta ferramenta gravou antes); o editado/excluído é pulado
Os consertos ficam em tools/rev_defs.py (um `fix(nome, ops=[...], bops=[...], conv=...)` por molde)."""
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from PIL import Image, ImageDraw
import weak_fix as WF
import palette as P
from tplfile import parse
import tplfile, loose

PRE = os.path.join(HERE, 'backups', 'pre-rev.js')
NEW = os.path.join(HERE, 'data', 'rev_new.json')
APPLIED = os.path.join(HERE, 'data', 'rev_applied.json')
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
L = {c['code']: c['letter'] for c in P.ALL}
HEXL = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}
FIXR = {}


def _src_of(name):
    p = os.path.join(HERE, 'data', 'rev_src.json')
    if not os.path.exists(p): return None
    s = json.load(open(p, encoding='utf-8')).get(name.replace(' (grande)', ''))
    return (s[0], s[1], tuple(s[2]) if s[2] else None) if s else None


def _inject(name, ops):
    src = _src_of(name); out = []
    for op in ops:
        if op[0] in ('boost', 'eye', 'ramp') and op[2] is None:
            if src is None: raise SystemExit('sem fonte para ' + name + ' (rev_src.json)')
            op = (op[0], op[1], src) + tuple(op[3:])
        out.append(op)
    return out


def fix(name, ops=None, bops=None, conv=None, nobig=False):
    """ops valem nos dois tamanhos (as de região são escaladas); bops só no irmão grande, em coordenadas dele; conv(big) -> linhas reconvertidas da fonte (None = parte da base).
    Um ('boost', região, None, regras) recebe a fonte do molde sozinho (data/rev_src.json)."""
    FIXR[name] = dict(ops=_inject(name, ops or []), bops=_inject(name, bops or []), conv=conv, nobig=nobig)


def pre():
    return parse(PRE)


def _dims(rows): return (len(rows[0]), len(rows))


def build_one(name, spec, items):
    base = items.get(name); out = {}
    if base is None: print('  NÃO ACHEI', name); return out
    b1 = base['rows']
    r1 = spec['conv'](False) if spec['conv'] else b1
    r1 = WF.apply(r1, spec['ops'], _dims(b1), False)
    if loose.loose_count(r1): r1 = loose.fix_loose(r1)
    out[name] = r1
    if not spec['nobig'] and (name + ' (grande)') in items:
        bb = items[name + ' (grande)']['rows']
        rb = spec['conv'](True) if spec['conv'] else bb
        rb = WF.apply(rb, spec['ops'], _dims(b1), True)
        if spec['bops']: rb = WF.apply(rb, spec['bops'], _dims(rb), False)
        if loose.loose_count(rb): rb = loose.fix_loose(rb)
        out[name + ' (grande)'] = rb
    return out


def sheet(pairs, path, H=330, W=1900, src=None):
    """pairs = [(título, linhas antes, linhas depois)]; cada painel: [fonte | antes | depois] com fundo roxo"""
    L2 = HEXL
    def render(rows, sc):
        h = len(rows) * sc; w = len(rows[0]) * sc
        im = Image.new('RGB', (w, h), (98, 70, 140)); d = ImageDraw.Draw(im)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.': d.rectangle((x * sc, y * sc, x * sc + sc - 1, y * sc + sc - 1), fill=L2[ch])
        return im
    tiles = []
    for t, a, b, s in pairs:
        sc = max(2, min(12, H // max(len(a), len(b))))
        ia, ib = render(a, sc), render(b, sc)
        sm = None
        if s is not None:
            hh = max(ia.height, ib.height); sm = s.resize((max(1, round(s.width * hh / s.height)), hh), Image.LANCZOS)
        w = (sm.width + 6 if sm else 0) + ia.width + 6 + ib.width
        tiles.append((t, sm, ia, ib, w, max(ia.height, ib.height)))
    pad = 10; x = pad; y = pad; rowh = 0; pos = []
    for t, sm, ia, ib, w, h in tiles:
        if x + w + pad > W: x = pad; y += rowh + pad; rowh = 0
        pos.append((x, y)); x += w + pad; rowh = max(rowh, h + 16)
    sh = Image.new('RGB', (W, y + rowh + pad), (60, 60, 66)); dr = ImageDraw.Draw(sh)
    for (t, sm, ia, ib, w, h), (x, y) in zip(tiles, pos):
        dr.text((x, y), t[:70].encode('ascii', 'replace').decode(), fill=(255, 255, 0)); xx = x
        if sm: sh.paste(sm, (xx, y + 14)); xx += sm.width + 6
        sh.paste(ia, (xx, y + 14)); xx += ia.width + 6; sh.paste(ib, (xx, y + 14))
    sh.save(path)


def source_of(name):
    p = os.path.join(HERE, 'data', 'rev_src.json')
    if not os.path.exists(p): return None
    src = json.load(open(p, encoding='utf-8')).get(name.replace(' (grande)', ''))
    if not src: return None
    import facetools as FT
    rem, idx, box = src
    return Image.fromarray(FT.src_raw(rem, idx, tuple(box) if box else None))


def cmd_build(args):
    import rev_defs                                               # noqa: F401  (preenche FIXR)
    big = '--big' in args
    H = 330
    if '--H' in args: H = int(args[args.index('--H') + 1]); args = [a for a in args if a not in ('--H', str(H))]
    filt = [a for a in args if not a.startswith('--')]
    d = pre(); items = {i['name']: i for i in d['items']}
    new = json.load(open(NEW, encoding='utf-8')) if os.path.exists(NEW) else {}
    pairs = []
    for name, spec in FIXR.items():
        if filt and not any(f.lower() in name.lower() for f in filt): continue
        try:
            res = build_one(name, spec, items)
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', name, repr(e)); continue
        for n, rows in res.items():
            new[n] = rows
            if n.endswith('(grande)') and not big: continue
            pairs.append(('%s %dx%d' % (n, len(rows[0]), len(rows)), items[n]['rows'], rows, source_of(n)))
    json.dump(new, open(NEW, 'w', encoding='utf-8'), ensure_ascii=False)
    tag = 'f' if filt else 'all'
    per = 6 if H <= 340 else 3
    for k in range(0, len(pairs), per):
        sheet(pairs[k:k + per], os.path.join(OUT, 'rev_pv_%s_%d.png' % (tag, k // per)), H=H)
    print(len(pairs), 'painéis;', 'folhas', (len(pairs) + per - 1) // per, '-> tools/out/rev_pv_%s_*.png' % tag)


def cmd_apply(args):
    dry = '--dry' in args
    skip = []
    if '--except' in args:
        k = args.index('--except'); skip = [a for a in args[k + 1:] if not a.startswith('--')]; args = args[:k]
    filt = [a for a in args if not a.startswith('--')]
    new = json.load(open(NEW, encoding='utf-8'))
    applied = json.load(open(APPLIED, encoding='utf-8')) if os.path.exists(APPLIED) else {}
    base = {i['name']: i['rows'] for i in pre()['items']}
    d = parse(os.path.join(ROOT, 'templates.js')); items = {i['name']: i for i in d['items']}
    done = same = 0; skipped = []; gone = []
    for name, rows in new.items():
        if filt and not any(f.lower() in name.lower() for f in filt): continue
        if skip and any(f.lower() in name.lower() for f in skip): continue
        if name not in items: gone.append(name); continue
        t = items[name]
        if t['rows'] == rows: same += 1; continue
        if t['rows'] != base.get(name) and t['rows'] != applied.get(name): skipped.append(name); continue
        if len({len(r) for r in rows}) != 1: print('ERRO larguras diferentes', name); continue
        bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
        if bad: print('ERRO letras fora da legenda', name, bad); continue
        t['rows'] = rows; applied[name] = rows; done += 1
    print('trocados: %d | já iguais: %d | pulados (o usuário editou depois): %d | não estão mais no catálogo: %d' % (done, same, len(skipped), len(gone)))
    for n in skipped: print('  PULEI (editado):', n)
    for n in gone: print('  excluído pelo usuário:', n)
    if dry: print('(--dry)'); return
    if done:
        tplfile.write(os.path.join(ROOT, 'templates.js'), d['legend'], d['cfg'], list(d['items']), d.get('removed'))
        json.dump(applied, open(APPLIED, 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravado templates.js (cópia com carimbo em tools/backups/)')


def cmd_dump(args):
    """imprime um molde (da base, ou do rev_new.json com --new) como TEXTO com régua: dump "trecho do nome" [r0 r1 c0 c1] [--big] [--new]"""
    use_new = '--new' in args; big = '--big' in args
    a = [x for x in args if not x.startswith('--')]
    q = a[0]; nums = [int(v) for v in a[1:5]]
    d = pre(); items = {i['name']: i['rows'] for i in d['items']}
    if use_new and os.path.exists(NEW): items.update(json.load(open(NEW, encoding='utf-8')))
    hit = [n for n in items if q.lower() in n.lower() and n.endswith('(grande)') == big]
    if len(hit) != 1:
        ex = [n for n in hit if n.lower() == q.lower()]
        if len(ex) == 1: hit = ex
        else: print('AMBÍGUO/NÃO ACHEI:', hit[:6]); return
    rows = items[hit[0]]
    r0, r1, c0, c1 = nums if len(nums) == 4 else (0, len(rows), 0, len(rows[0]))
    r1 = min(r1, len(rows)); c1 = min(c1, len(rows[0]))
    code = {c['letter']: c['code'] for c in P.ALL}
    SYM = '@#%&$=+~^;:,_`<>?|0123456789'; sym = {}
    def ch(c):
        if c == '.' or ord(c) < 128: return c
        if c not in sym: sym[c] = SYM[len(sym) % len(SYM)]
        return sym[c]
    print(hit[0], len(rows[0]), 'x', len(rows))
    print('      ' + ''.join(str((c // 10) % 10) if c % 10 == 0 else ' ' for c in range(c0, c1)))
    print('      ' + ''.join(str(c % 10) for c in range(c0, c1)))
    for y in range(r0, r1): print('%4d  %s' % (y, ''.join(ch(c) for c in rows[y][c0:c1])))
    used = {c for y in range(r0, r1) for c in rows[y][c0:c1] if c != '.'}
    print('legenda: ' + '  '.join('%s=%s' % (ch(c), code.get(c, '?')) for c in sorted(used, key=lambda c: code.get(c, ''))))


def cmd_probe(args):
    """cor média (RGB) da janela da fonte de cada conta pedida: probe "trecho do nome" r,c r,c ... [--big]   (ajuda a escolher alvos de `boost`)"""
    import facetools as FT
    a = [x for x in args if not x.startswith('--')]; big = '--big' in args
    q = a[0]; pts = [tuple(int(v) for v in t.split(',')) for t in a[1:]]
    d = pre(); items = {i['name']: i['rows'] for i in d['items']}
    hit = [n for n in items if q.lower() in n.lower() and n.endswith('(grande)') == big]
    ex = [n for n in hit if n.lower() == q.lower()]
    if len(ex) == 1: hit = ex
    if len(hit) != 1: print('AMBÍGUO/NÃO ACHEI:', hit[:6]); return
    name = hit[0]; rows = items[name]; rem, idx, box = _src_of(name)
    raw = FT.src_raw(rem, idx, box); geo = FT.align(raw, rows, verbose=False); ox, oy, cw, ch = geo
    for (r, c) in pts:
        win = raw[int(oy + r * ch):int(oy + (r + 1) * ch), int(ox + c * cw):int(ox + (c + 1) * cw)].reshape(-1, 3).astype(float)
        if not len(win): print((r, c), 'fora'); continue
        dark = win.max(axis=1) < 80; white = win.min(axis=1) > 235
        rest = win[~dark & ~white]
        f = lambda m: tuple(int(v) for v in m) if len(m) else None
        print((r, c), 'média', f(win.mean(axis=0)), '| preto %.2f branco %.2f' % (dark.mean(), white.mean()), '| resto (mediana)', f(np.median(rest, axis=0)) if len(rest) else None, '| letra atual', rows[r][c])


def cmd_blobs(args):
    """manchas de uma cor na fonte, em coordenadas de conta (linha, coluna decimais): blobs "trecho do nome" r0,r1,c0,c1 R,G,B tol [minpx]   (para escolher centros de olhos/detalhes)"""
    import facetools as FT, cv2
    a = [x for x in args if not x.startswith('--')]
    q = a[0]; r0, r1, c0, c1 = [int(v) for v in a[1].split(',')]; rgb = tuple(int(v) for v in a[2].split(',')); tol = float(a[3]); minpx = int(a[4]) if len(a) > 4 else 8
    d = pre(); items = {i['name']: i['rows'] for i in d['items']}
    hit = [n for n in items if q.lower() in n.lower() and not n.endswith('(grande)')]
    ex = [n for n in hit if n.lower() == q.lower()]
    if len(ex) == 1: hit = ex
    if len(hit) != 1: print('AMBÍGUO/NÃO ACHEI:', hit[:6]); return
    name = hit[0]; rows = items[name]; rem, idx, box = _src_of(name)
    raw = FT.src_raw(rem, idx, box); ox, oy, cw, ch = FT.align(raw, rows, verbose=False)
    ya0, yb0, xa0, xb0 = max(0, int(oy + r0 * ch)), int(oy + (r1 + 1) * ch), max(0, int(ox + c0 * cw)), int(ox + (c1 + 1) * cw)
    sub = raw[ya0:yb0, xa0:xb0].astype(np.int32)
    m = (np.linalg.norm(sub - np.array(rgb), axis=2) < tol).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    bl = sorted([(int(st[i][4]), round((cen[i][1] + ya0 - oy) / ch, 2), round((cen[i][0] + xa0 - ox) / cw, 2), round(st[i][2] / cw, 1), round(st[i][3] / ch, 1)) for i in range(1, n) if st[i][4] >= minpx], reverse=True)
    print(name, 'bead px = %.1f x %.1f' % (cw, ch))
    for b in bl[:8]: print('  área %5d | centro linha %.2f coluna %.2f | largura %.1f altura %.1f contas' % b)


def run(argv):
    cmd = argv[0] if argv else 'build'
    {'build': cmd_build, 'apply': cmd_apply, 'dump': cmd_dump, 'probe': cmd_probe, 'blobs': cmd_blobs}[cmd](argv[1:])


if __name__ == '__main__':
    import rev_fix as _m          # o módulo importado pelo nome (e não este __main__) é o que o rev_defs preenche
    _m.run(sys.argv[1:])
