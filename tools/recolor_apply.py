"""TROCA DE CORES (SÓ AS CORES) EM MOLDES QUE O DONO NOMEOU (2026-11-03). Cada troca diz "o código X vira o código Y" (códigos Pindou, não letras: `G7=F11,F10=G8`), vale para o molde inteiro,
não mexe em nenhuma conta de lugar (confere a forma) e só grava com --autorizado. Regra 4.9: só os moldes que ele pediu.
uso:  python tools/recolor_apply.py preview ID "G7=F11,F10=G8" [--src REM IDX [x0,y0,x1,y1]] [--out arq.png]     (só imagem, nada gravado)
      python tools/recolor_apply.py apply   ID "G7=F11,F10=G8" --autorizado [--expect SHA8]                  (grava; cópia do original em tools/backups/recolor-originais.json)
      python tools/recolor_apply.py revert  ID --autorizado                                                    (devolve o desenho que estava antes da PRIMEIRA troca)
      python tools/recolor_apply.py show    ID                                                                  (letras, códigos, hex e contas do molde, e o SHA8 atual)
`apply` também aceita um arquivo JSON {id: "G7=F11,..."} no lugar de ID e da troca: python tools/recolor_apply.py apply-json lote.json --autorizado
Registro: tools/data/recolor_applied.json (id -> sha depois, mapa, data). `--templates ARQ` aplica numa CÓPIA do catálogo (teste)."""
import os, sys, json, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tplfile
import remap_cores as RC, palette_tone as PT
from PIL import Image, ImageDraw, ImageFont

T = os.path.join(ROOT, 'templates.js')
APPLIED = os.path.join(HERE, 'data', 'recolor_applied.json')
ORIG = os.path.join(HERE, 'backups', 'recolor-originais.json')
LETTER_OF = {c['code']: c['letter'] for c in RC.NEW}
NEWP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.NEW}
NB = RC.NEW_BY_L


def sha(rows): return hashlib.sha1('\n'.join(rows).encode('utf-8')).hexdigest()


def parse_map(s):
    m = {}
    for part in s.split(','):
        part = part.strip()
        if not part: continue
        a, b = part.split('=')
        a, b = a.strip().upper(), b.strip().upper()
        if a not in LETTER_OF or b not in LETTER_OF: raise SystemExit('código desconhecido em "%s"' % part)
        if a != b: m[LETTER_OF[a]] = LETTER_OF[b]
    return m


def recolor(rows, m): return [''.join(m.get(c, c) if c != '.' else '.' for c in r) for r in rows]


def get(path, iid):
    d = tplfile.parse(path); it = next((t for t in d['items'] if t['id'] == iid), None)
    if it is None: raise SystemExit('molde não está no catálogo: ' + iid)
    return d, it


def show(iid, path=T):
    d, it = get(path, iid); import collections
    cnt = collections.Counter(ch for r in it['rows'] for ch in r if ch != '.')
    print('%s | %s | %d x %d | SHA8 %s' % (it['id'], it['name'], len(it['rows'][0]), len(it['rows']), sha(it['rows'])[:8]))
    for l, n in cnt.most_common():
        print('  %-4s %-8s %-20s %s  %d' % (NB[l]['code'], repr(l), NB[l]['name'][:20], NB[l]['hex'], n))


def preview(iid, mapstr, a):
    d, it = get(T, iid); m = parse_map(mapstr); new = recolor(it['rows'], m)
    sc = max(3, 440 // max(len(it['rows']), len(it['rows'][0])))
    tiles = [('AGORA (catálogo)', RC.draw(it['rows'], NEWP, sc, (236, 236, 236))), ('COM A TROCA', RC.draw(new, NEWP, sc, (236, 236, 236)))]
    if '--src' in a:
        import src_vs_mold as SV
        i = a.index('--src'); rem, idx = a[i + 1], int(a[i + 2]); box = tuple(int(v) for v in a[i + 3].split(',')) if len(a) > i + 3 and a[i + 3].count(',') == 3 else None
        s = SV.source(rem, idx, box); r = 440 / s.height; tiles.insert(0, ('IMAGEM ORIGINAL', s.resize((max(1, int(s.width * r)), 440), Image.LANCZOS)))
    F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)
    W = sum(t[1].width for t in tiles) + 20 * (len(tiles) + 1); H = max(t[1].height for t in tiles) + 40
    sh = Image.new('RGB', (W, H), (250, 248, 244)); dr = ImageDraw.Draw(sh); x = 20
    for nm, im in tiles:
        dr.text((x, 6), nm + ('   ' + mapstr[:60] if nm == 'COM A TROCA' else ''), fill=(20, 20, 20), font=F); sh.paste(im, (x, 26)); x += im.width + 20
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(HERE, 'out', 'rca_%s.png' % iid[:40]); sh.save(out); print(out, sh.size)


def do_apply(items, a):
    real = '--templates' not in a; path = T if real else a[a.index('--templates') + 1]
    if real and '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado e só nos moldes que o dono nomeou (CLAUDE.md 4.9).')
    d = tplfile.parse(path); by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
    applied_p = APPLIED if real else APPLIED + '.teste'; applied = json.load(open(applied_p, encoding='utf-8')) if os.path.exists(applied_p) else {}
    orig_p = ORIG if real else ORIG + '.teste'; orig = json.load(open(orig_p, encoding='utf-8')) if os.path.exists(orig_p) else {}
    allow = set(); log = []
    if len(items) > tplfile.MAX_POR_VEZ: raise SystemExit('mais de %d moldes de uma vez' % tplfile.MAX_POR_VEZ)
    for iid, (mapstr, expect) in items.items():
        if iid not in by: print('PULEI (não está no catálogo):', iid); continue
        it = its[by[iid]]; m = parse_map(mapstr)
        if expect and sha(it['rows'])[:8] != expect: print('PULEI (o molde mudou desde que eu olhei):', iid); continue
        new = recolor(it['rows'], m)
        if any((c1 == '.') != (c2 == '.') for r1, r2 in zip(it['rows'], new) for c1, c2 in zip(r1, r2)) or len(new) != len(it['rows']): raise SystemExit('forma mudou: ' + iid)
        bad = {c for r in new for c in r if c != '.' and c not in d['legend']}
        if bad: raise SystemExit('letras fora da legenda: %s %s' % (iid, bad))
        if iid not in orig: orig[iid] = it['rows']
        n = sum(c1 != c2 for r1, r2 in zip(it['rows'], new) for c1, c2 in zip(r1, r2))
        its[by[iid]] = dict(it, rows=new); allow.add(iid)
        applied[iid] = dict(sha=sha(new), mapa=dict(list(applied.get(iid, {}).get('mapa', {}).items()) + [(mapstr, 1)]) if False else mapstr, data=datetime.date.today().isoformat())
        log.append('%s: %d contas mudam de cor (%s)' % (it['name'], n, mapstr))
    if not allow: print('nada a gravar'); return
    if real:
        os.makedirs(os.path.dirname(orig_p), exist_ok=True); json.dump(orig, open(orig_p, 'w', encoding='utf-8'), ensure_ascii=False)
    tplfile.write(path, d['legend'], d['cfg'], its, d.get('removed'), allow=allow)
    json.dump(applied, open(applied_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('\n'.join(log)); print('ok')


def do_revert(iid, a):
    if '--autorizado' not in a: raise SystemExit('RECUSADO: só com --autorizado.')
    orig = json.load(open(ORIG, encoding='utf-8')) if os.path.exists(ORIG) else {}
    if iid not in orig: raise SystemExit('sem original guardado para ' + iid)
    d = tplfile.parse(T); by = {t['id']: k for k, t in enumerate(d['items'])}; its = list(d['items'])
    if sha(its[by[iid]]['rows']) != json.load(open(APPLIED, encoding='utf-8')).get(iid, {}).get('sha'): raise SystemExit('o molde foi mudado depois (por ele no app?): não mexo')
    its[by[iid]] = dict(its[by[iid]], rows=orig[iid]); tplfile.write(T, d['legend'], d['cfg'], its, d.get('removed'), allow={iid})
    ap = json.load(open(APPLIED, encoding='utf-8')); ap.pop(iid, None); json.dump(ap, open(APPLIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); orig.pop(iid, None)
    json.dump(orig, open(ORIG, 'w', encoding='utf-8'), ensure_ascii=False); print('devolvido:', iid)


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == 'show': show(a[1])
    elif cmd == 'preview': preview(a[1], a[2], a)
    elif cmd == 'apply':
        expect = a[a.index('--expect') + 1] if '--expect' in a else None
        do_apply({a[1]: (a[2], expect)}, a)
    elif cmd == 'apply-json':
        spec = json.load(open(a[1], encoding='utf-8'))
        do_apply({k: ((v[0], v[1]) if isinstance(v, list) else (v, None)) for k, v in spec.items()}, a)
    elif cmd == 'revert': do_revert(a[1], a)
    else: print(__doc__)


if __name__ == '__main__':
    main()
