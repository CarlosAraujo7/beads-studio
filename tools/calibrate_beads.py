"""Das cores medidas nas CONTAS (tools/data/beads_measured.json, de measure_beads.py) às cores do kit de 120: balanço de branco pelo papel de cada foto e comparação com a paleta ANTIGA (tools/data/palette.json)
e com a da CARTELA (tools/data/palette_cartelas.json, que o dono reprovou em 2026-11-02: a tinta impressa não é a cor da conta). NÃO altera nada.
uso:  python tools/calibrate_beads.py [--gain] [--json]    -> tabela, estatísticas, tools/out/contas_compare_N.png (uma folha por bandeja) e, com --json, tools/data/palette_contas.json (candidata)
  --gain G   multiplica o brilho depois do balanço (padrão 1.0; o papel branco vira 255*G)
  --fit      ajuste robusto por foto (ganho+deslocamento por canal) das cores medidas contra a paleta antiga: absorve exposição, matiz e véu da tampa; destaca onde a antiga destoa da conta
  --chroma   só tira o matiz azulado do papel (o brilho fica como na foto); --raw = cores como fotografadas, sem correção
Cada tile da folha: recorte da foto (a conta de verdade) | medido (balanço de branco) | paleta antiga | cartela, com o código e o ΔE2000 medido x antiga."""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import r5
OUT = os.path.join(HERE, 'out')
M = json.load(open(os.path.join(HERE, 'data', 'beads_measured.json'), encoding='utf-8'))
OLD = {c['code']: c for c in json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']}
CARD = json.load(open(os.path.join(HERE, 'data', 'palette_cartelas.json'), encoding='utf-8'))
G = float(sys.argv[sys.argv.index('--gain') + 1]) if '--gain' in sys.argv else 1.0


def lab(rgb):
    return cv2.cvtColor(np.uint8([[np.clip(rgb, 0, 255)]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float) * np.array([100 / 255.0, 1, 1]) - np.array([0, 128, 128])


def de(a, b):
    return float(np.ravel(r5._de2000(lab(a), np.array([lab(b)])))[0])


h2 = lambda h: np.array([int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
hx = lambda t: '#%02X%02X%02X' % tuple(int(round(v)) for v in t)
def robust_affine(X, Y, iters=25):
    """por canal: y = a*x + b ajustado por mínimos quadrados reponderados (Huber): as cores em que a paleta antiga está errada pesam pouco e não puxam o ajuste"""
    a = np.zeros(3); b = np.zeros(3)
    for c in range(3):
        w = np.ones(len(X))
        for _ in range(iters):
            A = np.stack([X[:, c], np.ones(len(X))], axis=1) * w[:, None]
            sol = np.linalg.lstsq(A, Y[:, c] * w, rcond=None)[0]
            r = Y[:, c] - (sol[0] * X[:, c] + sol[1]); sc = max(1.4826 * np.median(np.abs(r)), 3.0)
            w = 1.0 / np.maximum(1.0, np.abs(r) / (1.5 * sc))
        a[c], b[c] = sol
    return a, b


FIT = {}
if '--fit' in sys.argv:
    for n in sorted(M, key=int):
        X = np.array([c['rgb'] for c in M[n]['cores']], float); Y = np.array([h2(OLD[c['code']]['hex']) for c in M[n]['cores']], float)
        FIT[n] = robust_affine(X, Y)
        print('foto', n, 'ajuste (ganho, deslocamento) por canal R,G,B:', [(round(float(FIT[n][0][i]), 2), round(float(FIT[n][1][i]), 1)) for i in range(3)])

rows = []
for n in sorted(M, key=int):
    paper = np.array(M[n]['info']['papel_rgb'], float)
    gain = (paper.mean() / paper) * G if '--chroma' in sys.argv else (np.ones(3) * G if '--raw' in sys.argv else 255.0 * G / paper)      # --chroma: só tira o matiz do papel (brilho igual); --raw: sem correção; padrão: papel vira 255
    for c in M[n]['cores']:
        wb = np.clip(FIT[n][0] * np.array(c['rgb'], float) + FIT[n][1], 0, 255) if FIT else np.clip(np.array(c['rgb'], float) * gain, 0, 255)
        o = h2(OLD[c['code']]['hex']); k = h2(CARD[c['code']]['hex'])
        rows.append(dict(code=c['code'], foto=int(n), raw=c['rgb'], wb=wb, old=o, card=k, de_old=de(wb, o), de_card=de(wb, k), cx=c['cx'], cy=c['cy']))
print('papel por foto (RGB):', {n: M[n]['info']['papel_rgb'] for n in M})
d_old = [r['de_old'] for r in rows]; d_card = [r['de_card'] for r in rows]
print('ΔE2000 conta x paleta antiga: média %.1f, mediana %.1f, máx %.1f | conta x cartela: média %.1f' % (np.mean(d_old), np.median(d_old), max(d_old), np.mean(d_card)))
print('\nPELE e parentes (código: antiga | cartela | CONTA):')
for code in ('G1', 'G2', 'G3', 'E1', 'E11', 'E14', 'E15', 'A12', 'G9', 'F1', 'F14', 'G5', 'A11', 'M9', 'E2', 'E8', 'H1', 'H2', 'H3', 'H4', 'H5', 'H7'):
    r = next(x for x in rows if x['code'] == code)
    print('  %-4s %s | %s | %s   ΔE conta x antiga %.1f' % (code, hx(r['old']), hx(r['card']), hx(r['wb']), r['de_old']))
print('\nmaiores diferenças conta x antiga:')
for r in sorted(rows, key=lambda r: -r['de_old'])[:14]: print('  %-4s antiga %s  conta %s  ΔE %.1f' % (r['code'], hx(r['old']), hx(r['wb']), r['de_old']))

if '--report' in sys.argv:
    T = float(sys.argv[sys.argv.index('--report') + 1])
    big = [r for r in rows if r['de_old'] > T]
    print()
    print('códigos em que a conta destoa da antiga por mais de %.1f: %d de %d' % (T, len(big), len(rows)))
    for r in sorted(big, key=lambda r: (r['code'][0], int(r['code'][1:]))): print('  %-4s foto %d  antiga %s  conta %s  ΔE %.1f' % (r['code'], r['foto'], hx(r['old']), hx(r['wb']), r['de_old']))

# folhas de conferência (uma por bandeja)
crops = {}
for n in sorted(M, key=int):
    im = Image.open(os.path.join(ROOT, 'paleta 120', 'foto-contas-%s.jpg' % n)).convert('RGB')
    tw, th = 150, 150
    sheet = Image.new('RGB', (6 * (tw + 6) + 6, 4 * (th + 40) + 6), (250, 250, 250)); dr = ImageDraw.Draw(sheet)
    for i, r in enumerate([x for x in rows if x['foto'] == int(n)]):
        X = 6 + (i % 6) * (tw + 6); Y = 6 + (i // 6) * (th + 40)
        crop = im.crop((r['cx'] - 45, r['cy'] - 45, r['cx'] + 45, r['cy'] + 45)).resize((tw // 2 + 20, th // 2 + 20), Image.LANCZOS)
        sheet.paste(crop, (X, Y))
        sx = X + tw // 2 + 22; sw = (tw - tw // 2 - 22) // 1
        dr.rectangle([sx, Y, X + tw, Y + (th // 2 + 20) // 3 - 1], fill=tuple(int(v) for v in r['wb']))
        dr.rectangle([sx, Y + (th // 2 + 20) // 3, X + tw, Y + 2 * (th // 2 + 20) // 3 - 1], fill=tuple(int(v) for v in r['old']))
        dr.rectangle([sx, Y + 2 * (th // 2 + 20) // 3, X + tw, Y + th // 2 + 19], fill=tuple(int(v) for v in r['card']))
        dr.text((X, Y + th // 2 + 24), r['code'] + '  ΔE antiga %.0f' % r['de_old'], fill=(0, 0, 0))
        dr.text((X, Y + th // 2 + 34), hx(r['wb']) + ' / ' + hx(r['old']), fill=(90, 90, 90))
    sheet.save(os.path.join(OUT, 'contas_compare_%s.png' % n))
print('\nfolhas: tools/out/contas_compare_1..5.png (cada tile: foto da conta | cima = medido, meio = antiga, baixo = cartela)')
if '--json' in sys.argv:
    json.dump({r['code']: dict(hex=hx(r['wb']), foto=r['foto'], raw=r['raw'], de_vs_antiga=round(r['de_old'], 1)) for r in rows}, open(os.path.join(HERE, 'data', 'palette_contas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('gravado tools/data/palette_contas.json')
