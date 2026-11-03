"""AUDITORIA DE FIDELIDADE DAS CORES (2026-11-03). SÓ LÊ. Para cada molde do catálogo que tem reconversão (tools/out/rc_all, feita por reconv_all.py), alinha a reconversão ao molde e mede o quanto as cores do
catálogo se afastam da conta REAL mais parecida com a imagem original.
Saída: tools/out/rc_audit.json {id: {name, status, G, big, edited, ...}} e um resumo no terminal.
  status = 'igual'   (mesma forma: a reconversão serve como está)      | 'ajustada' (a mesma forma depois do trim/limpeza de contas soltas/buracos)
         | 'forma'   (a forma do molde difere da reconversão: foi retocado ou reduzido depois da conversão) | 'sem fonte' (não há reconversão para esse nome)
  G = ΔE2000 médio (por conta) entre a cor do catálogo e a da reconversão; big = fração das contas com ΔE > 10; edited = contas que diferem da conversão original gravada (retoque à mão ou troca de cores).
uso:  python tools/rc_audit.py [--list 60]"""
import os, sys, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import tplfile, remap_cores as RC, palette_tone as PT, r5
import outline as O, loose

NB = RC.NEW_BY_L
LAB = {l: RC.lab(PT.hex2rgb(NB[l]['hex'])) for l in NB}
_dc = {}


def de(l1, l2):
    if l1 == l2: return 0.0
    k = (l1, l2) if l1 < l2 else (l2, l1)
    if k not in _dc: _dc[k] = float(np.ravel(r5._de2000(LAB[l1], np.array([LAB[l2]])))[0])
    return _dc[k]


def mask(rows): return [[c != '.' for c in r] for r in rows]


def variants(rec):
    yield 'igual', rec
    try:
        t = O.trim(rec); yield 'ajustada', t
        f = O.trim(loose.fix_loose(rec)); yield 'ajustada', f
        g = O.trim(loose.fill_pinholes(loose.fix_loose(rec))); yield 'ajustada', g
        h = O.trim(loose.fill_pinholes(rec)); yield 'ajustada', h
    except Exception:
        return


def align(cur, rec):
    mc = mask(cur)
    for st, v in variants(rec):
        if len(v) == len(cur) and len(v[0]) == len(cur[0]) and mask(v) == mc: return st, v
    return 'forma', None


def load_rc():
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, 'out', 'rc_all', '*', '*.json'))):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        out.setdefault(d['name'], []).append(d)
    return out


def main():
    cat = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']; rc = load_rc()
    import recon_apply as RP
    orig = RP.conversions()
    res = {}; cnt = collections.Counter()
    for it in cat:
        name = it['name']; cur = it['rows']
        cands = rc.get(name)
        if not cands: res[it['id']] = dict(name=name, status='sem fonte', cat=it['cat']); cnt['sem fonte'] += 1; continue
        best = None
        for c in cands:
            st, v = align(cur, c['rows'])
            if v is not None: best = (st, v); break
        if best is None: res[it['id']] = dict(name=name, status='forma', cat=it['cat'], dims=[len(cur[0]), len(cur), len(cands[0]['rows'][0]), len(cands[0]['rows'])]); cnt['forma'] += 1; continue
        st, v = best
        tot = 0; s = 0.0; big = 0; edited = 0; o = orig.get(name)
        for y, (r1, r2) in enumerate(zip(cur, v)):
            for x, (c1, c2) in enumerate(zip(r1, r2)):
                if c1 == '.': continue
                d = de(c1, c2); tot += 1; s += d; big += d > 10
                if o is not None and len(o) == len(cur) and len(o[0]) == len(cur[0]) and o[y][x] != c1: edited += 1
        res[it['id']] = dict(name=name, status=st, cat=it['cat'], G=round(s / max(1, tot), 2), big=round(big / max(1, tot), 3), edited=edited, beads=tot, orig=o is not None)
        cnt[st] += 1
    json.dump(res, open(os.path.join(HERE, 'out', 'rc_audit.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('moldes:', len(cat), '|', dict(cnt))
    al = [(v['G'], k, v) for k, v in res.items() if 'G' in v]
    gs = np.array([g for g, _, _ in al])
    if len(gs):
        print('G (ΔE médio até a conta mais parecida da imagem) nos moldes alinhados: mediana %.1f, p75 %.1f, p90 %.1f' % (np.median(gs), np.percentile(gs, 75), np.percentile(gs, 90)))
        for th in (2, 3, 4, 5, 6, 8): print('  G >= %d: %d moldes' % (th, int((gs >= th).sum())))
    n = int(sys.argv[sys.argv.index('--list') + 1]) if '--list' in sys.argv else 0
    for g, k, v in sorted(al, reverse=True)[:n]: print('  %5.1f big %3.0f%% edit %4d  %-8s %s | %s' % (g, v['big'] * 100, v['edited'], v['cat'][:14], v['name'][:50], v['status']))


if __name__ == '__main__':
    main()
