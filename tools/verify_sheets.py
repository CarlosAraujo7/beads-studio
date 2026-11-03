"""Folhas de conferência dos códigos (2026-11-02): para cada uma das 5 cartelas, cada código aparece com o CÍRCULO impresso da cartela (esquerda), a CONTA da bandeja sem tampa (direita) e o código que a paleta do projeto usa.
Serve para ver, a olho, se o rótulo e a bandeja são mesmo o mesmo código (mesma família de cor) e achar contas que se parecem demais.   uso: python tools/verify_sheets.py  -> tools/out/verify_sheet_N.png"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import measure_cards as MC
import measure_beads2 as MB

F = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 13); Fs = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 11)
PAL = {c['code']: c for c in json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']}
tw = 92
for n in range(1, 6):
    card = Image.open(os.path.join(ROOT, 'paleta 120', 'foto-cartela-%d.jpeg' % n)).convert('RGB')
    bead = Image.open(MB.path(n)).convert('RGB')
    cc = MC.centers(n); codes_card = MC.CARDS[n].split()
    bc = MB.centers(n); codes_bead = MB.codes_physical(n)
    where = {c: i for i, c in enumerate(codes_bead)}
    sheet = Image.new('RGB', (6 * (2 * tw + 14) + 8, 4 * (tw + 36) + 28), (250, 248, 244)); d = ImageDraw.Draw(sheet)
    d.text((8, 4), 'cartela %d (arquivo %d): círculo impresso | conta da bandeja | cor na paleta' % (n, n), fill=(20, 20, 20), font=F)
    for i, code in enumerate(codes_card):
        x, y = int(cc[i][0]), int(cc[i][1]); r = 42
        a = card.crop((x - r, y - r, x + r, y + r)).resize((tw, tw), Image.LANCZOS)
        j = where[code]; bx, by = int(bc[j][0]), int(bc[j][1]); rb = 56
        b = bead.crop((bx - rb, by - rb, bx + rb, by + rb)).resize((tw, tw), Image.LANCZOS)
        X = 8 + (i % 6) * (2 * tw + 14); Y = 28 + (i // 6) * (tw + 36)
        sheet.paste(a, (X, Y)); sheet.paste(b, (X + tw, Y))
        hx = PAL[code]['hex']; d.rectangle([X, Y + tw + 2, X + 2 * tw - 1, Y + tw + 12], fill=tuple(int(hx[k:k + 2], 16) for k in (1, 3, 5)))
        d.text((X, Y + tw + 14), code, fill=(150, 0, 0), font=F); d.text((X + 40, Y + tw + 16), PAL[code]['name'][:20], fill=(80, 80, 80), font=Fs)
    out = os.path.join(HERE, 'out', 'verify_sheet_%d.png' % n); sheet.save(out); print(out, sheet.size)
