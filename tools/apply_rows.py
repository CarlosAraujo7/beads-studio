"""GRAVA O DESENHO PRONTO (linhas) DE UM MOLDE QUE O DONO NOMEOU (2026-11-03). Só a forma e as cores que eu preparei em tools/out/*.json ({"rows": [...]}), só com --autorizado, só se o molde ainda é exatamente o que eu li
(--expect SHA8) e guardando o original em tools/backups/recolor-originais.json (o mesmo de recolor_apply.py, então `python tools/recon_apply.py revert ID --autorizado` desfaz).
Se o tamanho mudar (--forma), o dono tem que ter pedido o molde pelo nome.
uso:  python tools/apply_rows.py ID linhas.json [--expect SHA8] [--forma] [--nota "o que mudou"] --autorizado"""
import os, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import tplfile, recolor_apply as RA


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); return
    iid, rj = a[0], a[1]
    rows = json.load(open(rj, encoding='utf-8')); rows = rows['rows'] if isinstance(rows, dict) else rows
    d = tplfile.parse(RA.T); by = {t['id']: k for k, t in enumerate(d['items'])}
    if iid not in by: raise SystemExit('molde não está no catálogo: ' + iid)
    it = d['items'][by[iid]]; cur = it['rows']
    n = sum(c1 != c2 for r1, r2 in zip(cur, rows) for c1, c2 in zip(r1, r2)) if len(cur) == len(rows) and len(cur[0]) == len(rows[0]) else -1
    print('%s | atual %dx%d, novo %dx%d | SHA8 atual %s | contas que mudam: %s' % (it['name'], len(cur[0]), len(cur), len(rows[0]), len(rows), RA.sha(cur)[:8], n if n >= 0 else 'forma nova'))
    if '--autorizado' not in a: print('(prévia: nada gravado; use --autorizado)'); return
    if n < 0 and '--forma' not in a: raise SystemExit('o tamanho mudou: só com --forma (e o molde tem que ter sido pedido pelo nome)')
    if any(len(r) != len(rows[0]) for r in rows): raise SystemExit('linhas de tamanhos diferentes')
    bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
    if bad: raise SystemExit('letras fora da legenda: %s' % bad)
    if '--expect' in a and RA.sha(cur)[:8] != a[a.index('--expect') + 1]: raise SystemExit('o molde mudou desde que eu olhei: não mexo')
    orig = json.load(open(RA.ORIG, encoding='utf-8')) if os.path.exists(RA.ORIG) else {}
    if iid not in orig: orig[iid] = cur
    its = list(d['items']); its[by[iid]] = dict(it, rows=rows)
    json.dump(orig, open(RA.ORIG, 'w', encoding='utf-8'), ensure_ascii=False)
    tplfile.write(RA.T, d['legend'], d['cfg'], its, d.get('removed'), allow={iid})
    ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
    ap[iid] = dict(sha=RA.sha(rows), mapa=(a[a.index('--nota') + 1] if '--nota' in a else 'linhas prontas (apply_rows.py)'), data=datetime.date.today().isoformat())
    json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); print('gravado:', it['name'])


if __name__ == '__main__':
    main()
