"""Das cores medidas nas fotos das cartelas (tools/data/cards_measured.json, de measure_cards.py) às cores do kit de 120: balanço de branco pelo PAPEL de cada foto e comparação com a paleta atual.
uso:  python tools/calibrate_cards.py            -> tabela, estatísticas e tools/out/palette_compare.png (antes em cima, medido embaixo); NÃO altera nada
      python tools/calibrate_cards.py --json     -> grava tools/data/palette_cartelas.json (candidata, com o hex medido de cada código)
Balanço de branco: cada canal é multiplicado por 255/papel (o papel branco vira branco); o brilho do papel em cada foto (214-221) é só exposição da câmera. É estimativa de foto (sem cartão de referência
de cor): erro esperado de poucos ΔE, e vale a mesma ressalva dos hex antigos."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r5
OUT = os.path.join(HERE, 'out')
M = json.load(open(os.path.join(HERE, 'data', 'cards_measured.json'), encoding='utf-8'))
PAL = json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))
old = {c['code']: c for c in PAL['colors']}


def lab(rgb):
    import cv2
    return cv2.cvtColor(np.uint8([[np.clip(rgb, 0, 255)]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float) * np.array([100 / 255.0, 1, 1]) - np.array([0, 128, 128])


def de(a, b):
    return float(np.ravel(r5._de2000(lab(a), np.array([lab(b)])))[0])


rows = []
for n in sorted(M, key=int):
    info = M[n]['info']; paper = np.array(info['papel_rgb'], float); gain = 255.0 / paper
    for c in M[n]['cores']:
        loc = np.array(c.get('papel_local') or info['papel_rgb'], float)          # papel NO LUGAR da forma (a luz cai de um lado da cartela)
        rgb = np.clip(np.array(c['rgb'], float) * (255.0 / loc), 0, 255)
        rows.append(dict(code=c['code'], foto=int(n), raw=c['rgb'], wb=[int(round(v)) for v in rgb], frac=c['frac'], old=old[c['code']]['hex'], est=old[c['code']]['est']))
hx = lambda t: '#%02X%02X%02X' % tuple(t)
for r in rows:
    o = old[r['code']]['hex'].lstrip('#'); orgb = np.array([int(o[i:i + 2], 16) for i in (0, 2, 4)], float)
    r['de'] = de(np.array(r['wb'], float), orgb); r['hex'] = hx(r['wb']); r['old_rgb'] = [int(v) for v in orgb]
print('%-4s %-5s %-12s %-12s %6s  %s' % ('cód', 'foto', 'medido WB', 'paleta atual', 'ΔE00', 'obs'))
for r in sorted(rows, key=lambda r: -r['de'])[:30]:
    print('%-4s %-5d %-12s %-12s %6.1f  %s' % (r['code'], r['foto'], r['hex'], r['old'], r['de'], 'antiga (24)' if not r['est'] else 'estimada do anúncio'))
d_old = [r['de'] for r in rows if not r['est']]; d_est = [r['de'] for r in rows if r['est']]
print('\nΔE2000 medido x paleta atual: 24 antigas média %.1f (máx %.1f) | 96 estimadas média %.1f (máx %.1f)' % (np.mean(d_old), max(d_old), np.mean(d_est), max(d_est)))
print('papéis (RGB) por foto:', {n: M[n]['info']['papel_rgb'] for n in M})
# folha de comparação: em cima a paleta atual, embaixo o medido
cw = 56; per = 24
sheet = Image.new('RGB', (per * (cw + 4) + 10, 5 * (2 * (cw // 2 + 14) + 12) + 10), (255, 255, 255)); dr = ImageDraw.Draw(sheet)
for i, r in enumerate(sorted(rows, key=lambda r: (r['foto'], rows.index(r)))):
    X = 5 + (i % per) * (cw + 4); Y = 5 + (i // per) * (2 * (cw // 2 + 14) + 12)
    dr.rectangle([X, Y, X + cw, Y + cw // 2], fill=tuple(r['old_rgb'])); dr.rectangle([X, Y + cw // 2 + 1, X + cw, Y + cw + 1], fill=tuple(r['wb']))
    dr.text((X + 2, Y + cw + 3), r['code'], fill=(0, 0, 0)); dr.text((X + 2, Y + cw + 13), '%.0f' % r['de'], fill=(160, 0, 0))
sheet.save(os.path.join(OUT, 'palette_compare.png')); print('folha: tools/out/palette_compare.png (em cima: paleta atual; embaixo: medido; número vermelho = ΔE)')
if '--json' in sys.argv:
    json.dump({r['code']: dict(hex=r['hex'], foto=r['foto'], raw=r['raw'], de_vs_atual=round(r['de'], 1)) for r in rows}, open(os.path.join(HERE, 'data', 'palette_cartelas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('gravado tools/data/palette_cartelas.json')
