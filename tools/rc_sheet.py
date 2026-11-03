"""FOLHAS DE CONFERÊNCIA DO PLANO DE CORES (2026-11-03): ANTES (paleta antiga) | AGORA (catálogo) | PLANO (cores refeitas a partir da imagem original), vários moldes por folha. SÓ LÊ.
uso:  python tools/rc_sheet.py prefixo [--gmin 3] [--cat pokemon] [--ids a,b,c] [--per 15] [--scale 3] [--status pronto,quase]
Cada molde mostra: nome, G (diferença média de cor), contas retocadas (ficam), nº de cores (agora→plano); [H] = o plano tem 2+ cores a menos (pode ficar homogêneo)."""
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import remap_cores as RC, palette_tone as PT, tplfile

OLDP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.OLD}; NEWP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.NEW}
F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 11)


def ncolors(rows, mn=3):
    c = collections.Counter(ch for r in rows for ch in r if ch != '.'); return sum(1 for v in c.values() if v >= mn)


def main():
    a = sys.argv[1:]; pre = a[0]
    gmin = float(a[a.index('--gmin') + 1]) if '--gmin' in a else 3.0
    per = int(a[a.index('--per') + 1]) if '--per' in a else 15
    scale = int(a[a.index('--scale') + 1]) if '--scale' in a else 3
    cat = a[a.index('--cat') + 1].split(',') if '--cat' in a else None
    ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else None
    stat = a[a.index('--status') + 1].split(',') if '--status' in a else ['pronto', 'quase']
    plan = json.load(open(os.path.join(HERE, 'out', 'rc_plan.json'), encoding='utf-8'))
    d = tplfile.parse(os.path.join(ROOT, 'templates.js')); by = {t['id']: t for t in d['items']}
    sel = [k for k, v in plan.items() if v['status'] in stat and (ids is None or k in ids) and (ids is not None or v.get('G', 0) >= gmin) and (cat is None or v['cat'] in cat) and os.path.exists(os.path.join(HERE, 'out', 'rc_plan', k + '.json'))]
    sel.sort(key=lambda k: (plan[k]['cat'], plan[k]['name']))
    pages = [sel[i:i + per] for i in range(0, len(sel), per)]
    cols = 3
    for pi, page in enumerate(pages):
        tiles = []
        for k in page:
            C = by[k]['rows']; P = json.load(open(os.path.join(HERE, 'out', 'rc_plan', k + '.json'), encoding='utf-8'))['rows']
            sc = max(2, min(scale, 150 // max(1, max(len(C), len(C[0])) // 1 * 1) + 0)) if False else scale
            tiles.append((k, plan[k], RC.draw(C, OLDP, sc, (236, 236, 236)), RC.draw(C, NEWP, sc, (236, 236, 236)), RC.draw(P, NEWP, sc, (236, 236, 236)), ncolors(C), ncolors(P)))
        cw = max(t[2].width * 3 + 36 for t in tiles) + 6; ch = max(t[2].height for t in tiles) + 17
        rows_n = (len(tiles) + cols - 1) // cols
        im = Image.new('RGB', (cols * cw, rows_n * ch + 16), (250, 248, 244)); dr = ImageDraw.Draw(im)
        dr.text((4, 2), '%s  pág %d/%d   ANTES | AGORA | PLANO' % (pre, pi + 1, len(pages)), fill=(20, 20, 20), font=F)
        for n, (k, v, a1, a2, a3, c2, c3) in enumerate(tiles):
            X = (n % cols) * cw + 3; Y = 16 + (n // cols) * ch
            flag = ' [H]' if c3 <= c2 - 2 else ''
            dr.text((X, Y), ('%s  G%.0f ret%d c%d→%d%s' % (v['name'][:30], v.get('G', 0), v.get('edited', 0), c2, c3, flag)), fill=(150, 20, 20) if flag else (20, 20, 20), font=F)
            im.paste(a1, (X, Y + 14)); im.paste(a2, (X + a1.width + 8, Y + 14)); im.paste(a3, (X + a1.width * 2 + 16, Y + 14))
        im.save('%s_%02d.png' % (pre, pi))
    print(len(sel), 'moldes em', len(pages), 'folhas:', '%s_NN.png' % pre)
    json.dump(sel, open('%s_ids.json' % pre, 'w'))


if __name__ == '__main__':
    main()
