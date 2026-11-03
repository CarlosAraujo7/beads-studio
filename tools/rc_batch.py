"""FOLHA DE CONFERÊNCIA EM LOTE (2026-11-03): para cada molde, IMAGEM ORIGINAL | AGORA (catálogo) | RECONVERSÃO de hoje. SÓ LÊ.
uso:  python tools/rc_batch.py saida.png id:REM:IDX[:x0,y0,x1,y1] [...]      (o json da reconversão é tools/out/rc/<tag>.json; a tag vem do dicionário TAGS abaixo ou do próprio id)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont
import remap_cores as RC, palette_tone as PT, tplfile
import src_vs_mold as SV

NEWP = {c['letter']: PT.hex2rgb(c['hex']) for c in RC.NEW}
F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 12)
TAGS = {'jiraiya-chibi-grafico': 'jiraiya', 'jon-snow-game-of-thrones-retrato': 'jon', 'dabi-my-hero-academia-chibi': 'dabi', 'bepo-one-piece-pixel': 'bepo', 'annabeth-chase-pixel': 'annabeth', 'mona-lisa': 'mona',
        'eijiro-kirishima-my-hero-academia-pixel': 'kiri', 'hawks-my-hero-academia-pixel': 'hawks', 'pennywise-de-capa-amarela-chibi': 'pennywise', 'hagrid-chibi-pixel': 'hagrid',
        'megumin-pixel-de-chapeu': 'megumin', 'darkness-konosuba-grafico': 'darkness', 'inuyasha-chibi': 'inuyasha', 'hulkbuster-marvel-pixel-acao': 'hulk'}


def main():
    a = sys.argv[1:]; out = a[0]; specs = a[1:]
    d = tplfile.parse(os.path.join(ROOT, 'templates.js')); by = {t['id']: t for t in d['items']}
    blocks = []
    for sp in specs:
        p = sp.split(':'); iid, rem, idx = p[0], p[1], int(p[2]); box = tuple(int(v) for v in p[3].split(',')) if len(p) > 3 else None
        it = by[iid]; cur = it['rows']; rec = json.load(open(os.path.join(HERE, 'out', 'rc', '%s.json' % TAGS.get(iid, iid)), encoding='utf-8'))
        H = 250; sc = max(2, H // max(len(cur), len(cur[0])))
        src = SV.source(rem, idx, box); r = H / src.height; src = src.resize((max(1, int(src.width * r)), H), Image.LANCZOS)
        a1 = RC.draw(cur, NEWP, sc, (236, 236, 236)); a2 = RC.draw(rec, NEWP, sc, (236, 236, 236))
        blocks.append((it['name'] + '  %dx%d%s' % (len(cur[0]), len(cur), '' if (len(cur) == len(rec) and len(cur[0]) == len(rec[0])) else '  [FORMA DIFERENTE: %dx%d]' % (len(rec[0]), len(rec))), src, a1, a2))
    cols = 2; cw = max(b[1].width + b[2].width + b[3].width + 50 for b in blocks); ch = max(b[1].height for b in blocks) + 26
    rows_n = (len(blocks) + cols - 1) // cols
    sh = Image.new('RGB', (cols * cw, rows_n * ch + 6), (250, 248, 244)); dr = ImageDraw.Draw(sh)
    for k, (nm, s, a1, a2) in enumerate(blocks):
        X = (k % cols) * cw + 8; Y = (k // cols) * ch + 4
        dr.text((X, Y), nm[:70], fill=(20, 20, 20), font=F)
        sh.paste(s, (X, Y + 18)); sh.paste(a1, (X + s.width + 14, Y + 18)); sh.paste(a2, (X + s.width + a1.width + 28, Y + 18))
    sh.save(out); print(out, sh.size)


if __name__ == '__main__':
    main()
