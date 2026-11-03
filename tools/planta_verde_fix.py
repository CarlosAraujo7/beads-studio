"""PLANTA VERDE DE OLHO VERMELHO (gráfico): a conversão do catálogo foi feita com a grade errada (passo vertical 29,25 em vez de 28,8, coluna 23 e linha 1 fora da grade: 411 contas em vez de 422,
18 células erradas; CLAUDE.md §7.37). Aqui a grade certa (dict abaixo, conferida pela legenda: 8+41+92+68+93+63+4+49+4 = 422 contas), a legenda com F13 e as 3 células lidas pelo número (fix).
O dono nomeou este molde em 2026-11-03 ("Planta verde de olho vermelho (gráfico) com cores erradas"), então é um dos moldes que posso trocar (regra 4.9).
uso:  python tools/planta_verde_fix.py            (só gera a prévia em tools/out/planta_verde_nova.png e o JSON em tools/out/planta_verde_nova.json)
      python tools/planta_verde_fix.py --apply    (grava no templates.js SÓ se o molde ainda é o que eu li; cópia do original em tools/backups/recolor-originais.json)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import r25_exfinal as X
import tplfile, remap_cores as RC, recolor_apply as RA
from PIL import Image

R = X.R; L = X.L; fin = X.fin
ID = 'planta-verde-de-olho-vermelho-grafico'
GRID = dict(px=28.83, py=28.80, ox=36.5, oy=26.0, W=23, H=30)
LEGEND = 'A22:8 B11:41 B23:92 B29:68 B32:93 F11:63 F13:4 G6:49 H2:4'
FIX = {(4, 6): 'B29', (9, 21): 'B29', (19, 4): '.'}


def convert():
    old = R.kit_letter

    def kl(c, col):
        if c == 'B29': return (L['B14'],)
        if c == 'H2': return ('w',)
        if c == 'B23': return (L['B11'],)
        return R.nearest_letter(col)
    R.kit_letter = kl
    try: return fin(R.pix_graph(35, GRID, LEGEND, name='Planta verde (grade certa)', fix=FIX))
    finally: R.kit_letter = old


def main():
    rows = convert(); print(len(rows[0]), 'x', len(rows), '| contas', sum(c != '.' for r in rows for c in r))
    json.dump({'rows': rows}, open(os.path.join(HERE, 'out', 'planta_verde_nova.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    d = tplfile.parse(RA.T); by = {t['id']: t for t in d['items']}; cur = by[ID]['rows']
    NEWP = RA.NEWP; sc = 14
    a = RC.draw(cur, NEWP, sc, (236, 236, 236)); b = RC.draw(rows, NEWP, sc, (236, 236, 236))
    import src_vs_mold as SV
    s = SV.source(25, 35); r = a.height / s.height; s = s.resize((max(1, int(s.width * r)), a.height), Image.LANCZOS)
    im = Image.new('RGB', (s.width + a.width + b.width + 60, a.height + 20), (250, 248, 244)); x = 15
    for t in (s, a, b): im.paste(t, (x, 10)); x += t.width + 15
    out = os.path.join(HERE, 'out', 'planta_verde_nova.png'); im.save(out); print(out, im.size)
    if '--apply' in sys.argv:
        if '--autorizado' not in sys.argv: raise SystemExit('RECUSADO: só com --autorizado.')
        orig = json.load(open(RA.ORIG, encoding='utf-8')) if os.path.exists(RA.ORIG) else {}
        if ID not in orig: orig[ID] = cur
        bad = {c for r_ in rows for c in r_ if c != '.' and c not in d['legend']}
        if bad: raise SystemExit('letras fora da legenda: %s' % bad)
        its = list(d['items']); i = [t['id'] for t in its].index(ID); its[i] = dict(its[i], rows=rows)
        json.dump(orig, open(RA.ORIG, 'w', encoding='utf-8'), ensure_ascii=False)
        tplfile.write(RA.T, d['legend'], d['cfg'], its, d.get('removed'), allow={ID})
        ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
        import datetime
        ap[ID] = dict(sha=RA.sha(rows), mapa='grade certa + legenda (planta_verde_fix.py)', data=datetime.date.today().isoformat())
        json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); print('gravado:', by[ID]['name'])


if __name__ == '__main__':
    main()
