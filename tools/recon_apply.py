"""REFAZ AS CORES DE UM MOLDE A PARTIR DA IMAGEM ORIGINAL (2026-11-03), só nos moldes que o dono nomeou (regra 4.9). A conversão de hoje (tools/reconv.py → json) escolhe, para cada conta, a conta REAL mais parecida
com a cor da imagem; aqui ela entra no molde do catálogo SEM mudar nenhuma conta de lugar: só as cores. Contas que eu ou ele retocamos depois da conversão (o molde difere da conversão original gravada em
tools/data/final*_120.json) ficam como estão, trocadas pelo mapa --keep-map se der. `--over "A1=A3,E14=E1"` troca códigos no RESULTADO (decisões de olho: cabelo que ficou igual à pele, rosto que ficou rosa...) e `--cur "F10=G8"` decide pela cor ATUAL do molde (quando a reconversão juntou duas cores que o molde separa).
uso:  python tools/recon_apply.py preview ID reconv.json [--over "A1=A3"] [--src REM IDX [x0,y0,x1,y1]] [--out arq.png]
      python tools/recon_apply.py apply   ID reconv.json [--over "A1=A3"] --autorizado [--expect SHA8]
      python tools/recon_apply.py revert  ID --autorizado          (volta ao desenho de antes da PRIMEIRA troca; o original fica em tools/backups/recolor-originais.json)
Registro: tools/data/recolor_applied.json (o mesmo de recolor_apply.py). Antes de gravar, o molde tem que ser exatamente o que o preview mostrou (--expect SHA8) e a FORMA não pode mudar."""
import os, sys, json, glob, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tplfile
import remap_cores as RC, palette_tone as PT
import recolor_apply as RA
from PIL import Image, ImageDraw, ImageFont

T = RA.T
NEWP = RA.NEWP; NB = RA.NB; LETTER_OF = RA.LETTER_OF


def conversions():
    """nome -> linhas da conversão ORIGINAL gravada (paleta antiga): as de tools/data/final*_120.json (as mais novas por último)"""
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, 'data', 'final*_120.json')) + glob.glob(os.path.join(HERE, 'data', 'final_*_120.json')), key=os.path.getmtime):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        for it in d:
            if isinstance(it, list) and len(it) >= 3 and isinstance(it[2], list): out[it[0]] = it[2]
    return out


def merged(it, rec, over, curmap=None, allrec=False):
    cur = it['rows']; name = it['name']; cm = RA.parse_map(curmap) if curmap else {}
    if len(cur) != len(rec) or len(cur[0]) != len(rec[0]): raise SystemExit('tamanho do molde (%dx%d) e da reconversão (%dx%d) não batem' % (len(cur[0]), len(cur), len(rec[0]), len(rec)))
    if any((c1 == '.') != (c2 == '.') for r1, r2 in zip(cur, rec) for c1, c2 in zip(r1, r2)): raise SystemExit('a forma do molde e a da reconversão não batem: não troco')
    orig = None if allrec else conversions().get(name)       # allrec (--all): o molde não teve retoque à mão (só troca de cores de remap): tudo vem da reconversão
    edited = 0; rows = []
    for y, (rc, rr) in enumerate(zip(cur, rec)):
        line = []
        for x, (c, r) in enumerate(zip(rc, rr)):
            if c == '.': line.append('.'); continue
            if c in cm: line.append(cm[c]); continue                 # decisão de olho por letra ATUAL do molde (--cur "F10=G8"): vale no lugar da reconversão
            was = orig[y][x] if orig and len(orig) == len(cur) and len(orig[0]) == len(cur[0]) else None
            if was is not None and was != c: edited += 1; line.append(c)           # conta retocada depois da conversão: fica
            else: line.append(r)
        rows.append(''.join(line))
    if over: rows = RA.recolor(rows, RA.parse_map(over))
    return rows, edited, (orig is not None)


def draw_sheet(it, rows, a, over):
    sc = max(3, 440 // max(len(rows), len(rows[0]))); F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)
    tiles = [('AGORA (catálogo)', RC.draw(it['rows'], NEWP, sc, (236, 236, 236))), ('COM A IMAGEM ORIGINAL' + ('  +' + over if over else ''), RC.draw(rows, NEWP, sc, (236, 236, 236)))]
    if '--src' in a:
        import src_vs_mold as SV
        i = a.index('--src'); rem, idx = a[i + 1], int(a[i + 2]); box = tuple(int(v) for v in a[i + 3].split(',')) if len(a) > i + 3 and a[i + 3].count(',') == 3 else None
        s = SV.source(rem, idx, box); r = 440 / s.height; tiles.insert(0, ('IMAGEM ORIGINAL', s.resize((max(1, int(s.width * r)), 440), Image.LANCZOS)))
    W = sum(t[1].width for t in tiles) + 20 * (len(tiles) + 1); H = max(t[1].height for t in tiles) + 40
    sh = Image.new('RGB', (W, H), (250, 248, 244)); dr = ImageDraw.Draw(sh); x = 20
    for nm, im in tiles:
        dr.text((x, 6), nm[:70], fill=(20, 20, 20), font=F); sh.paste(im, (x, 26)); x += im.width + 20
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(HERE, 'out', 'rap_%s.png' % it['id'][:40]); sh.save(out); return out, sh.size


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == 'revert': RA.do_revert(a[1], a); return
    iid, rj = a[1], a[2]
    over = a[a.index('--over') + 1] if '--over' in a else ''; curmap = a[a.index('--cur') + 1] if '--cur' in a else ''
    d = tplfile.parse(T); it = next((t for t in d['items'] if t['id'] == iid), None)
    if it is None: raise SystemExit('molde não está no catálogo: ' + iid)
    rec = json.load(open(rj, encoding='utf-8'))
    rows, edited, had = merged(it, rec, over, curmap, '--all' in a)
    n = sum(c1 != c2 for r1, r2 in zip(it['rows'], rows) for c1, c2 in zip(r1, r2))
    print('%s | %dx%d | SHA8 atual %s | %d contas mudam de cor | contas retocadas depois da conversão (ficam): %d | conversão original gravada: %s' % (it['name'], len(rows[0]), len(rows), RA.sha(it['rows'])[:8], n, edited, 'sim' if had else 'não usada (tudo vem da reconversão)'))
    if cmd == 'preview':
        print(*draw_sheet(it, rows, a, (over + (' ' if over and curmap else '') + (('cur ' + curmap) if curmap else ''))))
    elif cmd == 'apply':
        expect = a[a.index('--expect') + 1] if '--expect' in a else None
        if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado e só nos moldes que o dono nomeou (CLAUDE.md 4.9).')
        if expect and RA.sha(it['rows'])[:8] != expect: raise SystemExit('o molde mudou desde que eu olhei: não mexo')
        orig_p = RA.ORIG; orig = json.load(open(orig_p, encoding='utf-8')) if os.path.exists(orig_p) else {}
        if iid not in orig: orig[iid] = it['rows']
        by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
        bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
        if bad: raise SystemExit('letras fora da legenda: %s' % bad)
        its[by[iid]] = dict(it, rows=rows)
        json.dump(orig, open(orig_p, 'w', encoding='utf-8'), ensure_ascii=False)
        tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), allow={iid})
        ap = json.load(open(RA.APPLIED, encoding='utf-8')) if os.path.exists(RA.APPLIED) else {}
        ap[iid] = dict(sha=RA.sha(rows), mapa='reconversão' + ((' +over ' + over) if over else '') + ((' +cur ' + curmap) if curmap else ''), data=datetime.date.today().isoformat())
        json.dump(ap, open(RA.APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); print('gravado:', it['name'])


if __name__ == '__main__':
    main()
