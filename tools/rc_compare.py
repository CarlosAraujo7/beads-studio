"""COMPARA O MOLDE DO CATÁLOGO COM A RECONVERSÃO DE HOJE (2026-11-03). SÓ LÊ.
uso:  python tools/rc_compare.py REM IDX id-do-molde reconv.json [--box x0,y0,x1,y1] [--out arq.png] [--H 460]
Folha:  IMAGEM ORIGINAL | ANTES (paleta antiga) | AGORA (catálogo) | RECONVERSÃO (a conta real mais parecida da imagem, hoje)
Tabela (se as dimensões e a forma batem): para cada letra do molde, em quais letras a reconversão a transformou (contas) e os hex de cada uma."""
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import remap_cores as RC, palette_tone as PT, tplfile
import src_vs_mold as SV

OLDP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.OLD}
NEWP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.NEW}
NB = RC.NEW_BY_L; OB = RC.OLD_BY_L
F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)


def letter_table(cur, rec):
    t = collections.defaultdict(collections.Counter)
    for y, (r1, r2) in enumerate(zip(cur, rec)):
        for x, (c1, c2) in enumerate(zip(r1, r2)):
            if c1 != '.' or c2 != '.': t[c1][c2] += 1
    return t


def main():
    a = sys.argv[1:]
    rem, idx, iid, rj = a[0], int(a[1]), a[2], a[3]
    box = tuple(int(v) for v in a[a.index('--box') + 1].split(',')) if '--box' in a else None
    H = int(a[a.index('--H') + 1]) if '--H' in a else 460
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(HERE, 'out', 'rcc_%s.png' % iid[:36])
    d = tplfile.parse(os.path.join(ROOT, 'templates.js')); it = next(t for t in d['items'] if t['id'] == iid); cur = it['rows']
    rec = json.load(open(rj, encoding='utf-8'))
    same = len(cur) == len(rec) and len(cur[0]) == len(rec[0])
    sc = max(2, H // max(len(cur), len(cur[0])))
    src = SV.source(rem, idx, box); r = H / src.height; src = src.resize((max(1, int(src.width * r)), H), Image.LANCZOS)
    tiles = [('IMAGEM ORIGINAL', src), ('ANTES (paleta antiga)', RC.draw(cur, OLDP, sc, (236, 236, 236))), ('AGORA (catálogo)', RC.draw(cur, NEWP, sc, (236, 236, 236))),
             ('RECONVERSÃO de hoje', RC.draw(rec, NEWP, sc, (236, 236, 236)))]
    W = sum(t[1].width for t in tiles) + 20 * (len(tiles) + 1); HH = max(t[1].height for t in tiles) + 40
    sh = Image.new('RGB', (W, HH), (250, 248, 244)); dr = ImageDraw.Draw(sh); x = 20
    for nm, im in tiles:
        dr.text((x, 6), nm, fill=(20, 20, 20), font=F); sh.paste(im, (x, 26)); x += im.width + 20
    sh.save(out); print(out, sh.size, '| catálogo', len(cur[0]), 'x', len(cur), '| reconv', len(rec[0]), 'x', len(rec), '| mesma forma:', same and all(((c1 == '.') == (c2 == '.')) for r1, r2 in zip(cur, rec) for c1, c2 in zip(r1, r2)))
    if same:
        t = letter_table(cur, rec)
        print('letra atual (cód antigo / hoje) -> reconversão (letra: cód hex, contas)')
        for l, cnt in sorted(t.items(), key=lambda kv: -sum(kv[1].values())):
            if l == '.': continue
            tot = sum(cnt.values())
            print('  %-3s %-4s old %s now %s (%d) -> %s' % (repr(l), OB[l]['code'], OB[l]['hex'], NB[l]['hex'], tot,
                  ' | '.join('%s %s %s %d' % (repr(k), NB[k]['code'], NB[k]['hex'], n) if k != '.' else 'vazio %d' % n for k, n in cnt.most_common(3))))


if __name__ == '__main__':
    main()
