"""PLANO DE REFAZER AS CORES A PARTIR DA IMAGEM ORIGINAL, MOLDE POR MOLDE (2026-11-03). SÓ LÊ o catálogo; grava só em tools/out/rc_plan*.
Para cada molde: acha a reconversão de hoje (tools/out/rc_all, do reconv_all.py) pelo NOME ou, se o nome mudou, pela FORMA (mesmas dimensões e silhueta ≥ 97% igual), alinha à silhueta do molde
(a reconversão crua, aparada, com contas soltas/buracos limpos como o add_templates faz) e monta o molde NOVO: onde o molde e a conversão original gravada (tools/data/final*_120.json) coincidem, entra a cor
da reconversão; onde ele foi retocado à mão (difere da conversão original), a conta fica como está. Sem conversão original gravada ou com dimensões diferentes, o molde vai para a lista manual.
Saída: tools/out/rc_plan.json {id: {name, cat, status, G, big, edited, beads, how, ...}} e tools/out/rc_plan/<id>.json {rows} (o molde novo) para os que têm plano.
  status:  'pronto'  (silhueta igual; plano completo)   | 'quase' (silhueta ≥ 92% igual: contas que só existem num dos lados ficam como no catálogo)
           'manual'  (sem conversão original gravada, ou forma/dimensões diferentes)   | 'sem fonte'
uso:  python tools/rc_plan.py"""
import os, sys, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import tplfile, remap_cores as RC, palette_tone as PT, r5
import outline as O, loose
import recon_apply as RP

NB = RC.NEW_BY_L
LAB = {l: RC.lab(PT.hex2rgb(NB[l]['hex'])) for l in NB}
_dc = {}
OUTD = os.path.join(HERE, 'out', 'rc_plan'); os.makedirs(OUTD, exist_ok=True)
OB = RC.OLD_BY_L; LETTER_OF = {c['code']: c['letter'] for c in RC.NEW}
DEC_P = os.path.join(HERE, 'data', 'recon_decisions.json')       # {"skip": [nomes], "over": {nome: "F11=F8"}}: decisões tomadas OLHANDO as folhas de conferência
DEC = json.load(open(DEC_P, encoding='utf-8')) if os.path.exists(DEC_P) else {'skip': [], 'over': {}}


def _lh(l):
    L, a, b = RC.lab(PT.hex2rgb(OB[l]['hex'])); return L, (a * a + b * b) ** .5, float(np.degrees(np.arctan2(b, a)) % 360)


def guard(c, r):
    """A reconversão escolhe a conta mais parecida em ΔE, e erra de dois jeitos que a conferência a olho achou: (1) vermelho de verdade vira o marrom F11; (2) azul/roxo ESCURO vira preto.
    c = letra atual do molde (cor antiga), r = letra da reconversão. Devolve a letra que fica."""
    if c == r or r == '.': return r
    L, C, h = _lh(c); code = NB[r]['code']
    if code == 'F11' and C >= 38 and L >= 38 and (h >= 340 or h <= 30): return LETTER_OF['F8']
    if code in ('H7', 'H6') and C >= 18 and L < 45 and LAB[c][0] < 40: return c
    return r


def de(l1, l2):
    if l1 == l2: return 0.0
    k = (l1, l2) if l1 < l2 else (l2, l1)
    if k not in _dc: _dc[k] = float(np.ravel(r5._de2000(LAB[l1], np.array([LAB[l2]])))[0])
    return _dc[k]


def mask(rows): return np.array([[c != '.' for c in r] for r in rows])


def variants(rec):
    yield rec
    for f in (lambda r: O.trim(r), lambda r: O.trim(loose.fix_loose(r)), lambda r: O.trim(loose.fill_pinholes(loose.fix_loose(r))), lambda r: O.trim(loose.fill_pinholes(r))):
        try: yield f(rec)
        except Exception: pass


def best(C, rec):
    """a variante da reconversão com as MESMAS dimensões do molde e a silhueta mais parecida: (iou, linhas) ou (0, None)"""
    mc = mask(C); b = (0.0, None)
    for v in variants(rec):
        if len(v) != len(C) or len(v[0]) != len(C[0]): continue
        mv = mask(v); u = (mc | mv).sum(); iou = (mc & mv).sum() / u if u else 0
        if iou > b[0]: b = (iou, v)
        if iou == 1.0: break
    return b


def pool():
    byname = collections.defaultdict(list); bydims = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(HERE, 'out', 'rc_all', '*', '*.json'))):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        byname[d['name']].append(d); rows = d['rows']
        bydims[(len(rows[0]), len(rows))].append(d)
        for v in variants(rows)[1:] if False else []: pass
    return byname, bydims


def main():
    cat = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']; byname, bydims = pool(); orig = RP.conversions()
    applied = set(json.load(open(os.path.join(HERE, 'data', 'recolor_applied.json'), encoding='utf-8')))
    remapped = set(json.load(open(os.path.join(HERE, 'data', 'remap_applied.json'), encoding='utf-8')))
    summary = {}; cnt = collections.Counter()
    for it in cat:
        iid, name, C = it['id'], it['name'], it['rows']; rec_info = dict(name=name, cat=it['cat'])
        cands = list(byname.get(name, [])); how = 'nome'
        if not cands:
            how = 'forma'
            for d in bydims.get((len(C[0]), len(C)), []): cands.append(d)
        bestc = (0.0, None, None)
        for d in cands:
            iou, v = best(C, d['rows'])
            if v is not None and iou > bestc[0]: bestc = (iou, v, d)
            if iou == 1.0: break
        iou, R, d = bestc
        if how == 'forma' and iou < 0.97: R = None
        if R is None or iou < 0.92:
            summary[iid] = dict(rec_info, status='sem fonte' if not cands or R is None and how == 'forma' else 'manual', motivo='silhueta diferente' if cands else 'sem reconversão', iou=round(iou, 3)); cnt[summary[iid]['status']] += 1; continue
        if name in DEC['skip']: summary[iid] = dict(rec_info, status='pulado', iou=round(iou, 3)); cnt['pulado'] += 1; continue
        o = orig.get(d['name'] if how == 'forma' else name)
        if iid in applied: summary[iid] = dict(rec_info, status='feito', iou=round(iou, 3)); cnt['feito'] += 1; continue
        known = iid in remapped
        if o is None or len(o) != len(C) or len(o[0]) != len(C[0]):
            if not (iou == 1.0 and not known) or o is not None:
                summary[iid] = dict(rec_info, status='manual', motivo='sem conversão original gravada de mesma dimensão', iou=round(iou, 3), how=how); cnt['manual'] += 1; continue
            o = None
        rows = []; edited = 0; tot = 0; s = 0.0; big = 0
        dom = {}                               # troca de cores NO MOLDE INTEIRO (remap, recolor, r_old120) não é retoque à mão: cada letra da conversão original vira, quase sempre, a mesma letra do catálogo
        if o is not None:
            M = collections.defaultdict(collections.Counter)
            for ro, rc_ in zip(o, C):
                for co, cc in zip(ro, rc_):
                    if co != '.' and cc != '.': M[co][cc] += 1
            dom = {k: v.most_common(1)[0][0] for k, v in M.items()}
        for y, (rc, rr) in enumerate(zip(C, R)):
            line = []
            for x, (c, r) in enumerate(zip(rc, rr)):
                if c == '.': line.append('.'); continue
                tot += 1
                ed = (o is not None and o[y][x] != '.' and dom.get(o[y][x], o[y][x]) != c) or (known and o is None)
                if r == '.' or ed:
                    edited += (1 if ed else 0); line.append(c)
                else:
                    r = guard(c, r); line.append(r); dd = de(c, r); s += dd; big += dd > 10
            rows.append(''.join(line))
        ov = DEC['over'].get(name)
        if ov:
            import recolor_apply as RA2
            rows = RA2.recolor(rows, RA2.parse_map(ov))
        st = 'pronto' if iou == 1.0 else 'quase'
        summary[iid] = dict(rec_info, status=st, iou=round(iou, 3), how=how, G=round(s / max(1, tot), 2), big=round(big / max(1, tot), 3), edited=edited, beads=tot, src=(d['name'] if how == 'forma' else name))
        json.dump({'rows': rows}, open(os.path.join(OUTD, iid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False); cnt[st] += 1
    json.dump(summary, open(os.path.join(HERE, 'out', 'rc_plan.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('moldes:', len(cat), '|', dict(cnt))
    gs = np.array([v['G'] for v in summary.values() if 'G' in v])
    for th in (2, 3, 4, 5, 6, 8): print('  G >= %d: %d moldes' % (th, int((gs >= th).sum())))
    ed = [(v['edited'] / max(1, v['beads']), k) for k, v in summary.items() if 'G' in v]
    print('com retoque à mão em mais de 5%% das contas: %d' % sum(1 for e, k in ed if e > 0.05))


if __name__ == '__main__':
    main()
