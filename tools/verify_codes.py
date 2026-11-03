"""VERIFICA OS CÓDIGOS DAS 120 CONTAS (2026-11-02, pedido do dono: "revise também os códigos das contas: tem um bege com código H12, mas ele não existe nas paletas que mandei, dá certo trocar pelo A1, mas verifique isso melhor").
1) LÊ o código impresso em cada um dos 120 círculos das 5 cartelas (paleta 120/foto-cartela-N.jpeg) com OCR (RapidOCR, num venv temporário) e compara com o que a paleta do projeto diz (tools/data/palette.json, ordem das cartelas em measure_beads.CARDS);
2) compara, por código, a cor da TINTA da cartela com a cor da CONTA na bandeja sem tampa (as duas devem ser da mesma família; onde destoam muito, o rótulo ou a bandeja estão trocados);
3) lista pares de códigos cujas CONTAS são quase iguais (ΔE2000 pequeno nas fotos sem tampa): são as que o dono confunde (bege x creme) e as candidatas a um código só.
uso (com o Python do venv que tem o rapidocr):  ocrenv/Scripts/python.exe tools/verify_codes.py [--ocr]     (sem --ocr só faz as partes 2 e 3 com o Python normal)
saída: tools/out/verify_codes_ocr.json (código lido x esperado), tools/out/verify_codes.png (folha), texto no terminal."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import measure_cards as MC
import measure_beads2 as MB

PAL = json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']
PAL_CODES = [c['code'] for c in PAL]


def lab(rgb):
    return cv2.cvtColor(np.uint8([[np.clip(rgb, 0, 255)]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float) * np.array([100 / 255.0, 1, 1]) - np.array([0, 128, 128])


def de(a, b):
    import r5
    return float(np.ravel(r5._de2000(lab(a), np.array([lab(b)])))[0])


def ocr_cards():
    from rapidocr_onnxruntime import RapidOCR
    eng = RapidOCR(); out = {}
    for n in range(1, 6):
        im = np.array(Image.open(os.path.join(ROOT, 'paleta 120', 'foto-cartela-%d.jpeg' % n)).convert('RGB'))
        cs = MC.centers(n); exp = MC.CARDS[n].split(); res = []
        for i, c in enumerate(cs):
            x, y = int(c[0]), int(c[1]); r = 46
            crop = im[max(0, y - r):y + r, max(0, x - r):x + r]
            big = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            big = cv2.copyMakeBorder(big, 20, 20, 20, 20, cv2.BORDER_REPLICATE)
            r_ = eng(big)[0] or []
            txt = ''.join(t[1] for t in sorted(r_, key=lambda t: t[0][0][0])).replace(' ', '').upper()
            conf = float(np.mean([t[2] if isinstance(t[2], float) else float(t[2]) for t in r_])) if r_ else 0.0
            res.append(dict(pos=i, esperado=exp[i], lido=txt, conf=round(conf, 2)))
        out[n] = res
    return out


def main():
    want_ocr = '--ocr' in sys.argv
    if want_ocr:
        ocr = ocr_cards()
        json.dump(ocr, open(os.path.join(HERE, 'out', 'verify_codes_ocr.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        bad = [(n, r) for n, lst in ocr.items() for r in lst if r['lido'] != r['esperado']]
        print('OCR dos códigos impressos: %d de 120 iguais ao que a paleta diz' % (120 - len(bad)))
        for n, r in bad: print('   cartela %s posição %2d: esperado %-4s lido %-6s (confiança %.2f)' % (n, r['pos'] + 1, r['esperado'], r['lido'] or '-', r['conf']))
    # 1b) conjunto de códigos: paleta x cartelas
    card_codes = [c for n in range(1, 6) for c in MC.CARDS[n].split()]
    print('\ncódigos nas cartelas: %d (únicos %d) | na paleta: %d' % (len(card_codes), len(set(card_codes)), len(PAL_CODES)))
    print('na paleta e FORA das cartelas:', sorted(set(PAL_CODES) - set(card_codes)), '| nas cartelas e FORA da paleta:', sorted(set(card_codes) - set(PAL_CODES)))
    dup = sorted({c for c in card_codes if card_codes.count(c) > 1}); print('códigos repetidos nas cartelas:', dup)
    # 2) tinta da cartela x conta da bandeja sem tampa
    cards = json.load(open(os.path.join(HERE, 'data', 'cards_measured.json'), encoding='utf-8'))
    ink = {}
    for n, v in cards.items():
        lst = v['cores'] if isinstance(v, dict) and 'cores' in v else v
        for it in lst: ink[it['code']] = np.array(it['rgb'], float)
    beads = {}
    for n, lst in json.load(open(os.path.join(HERE, 'data', 'beads_measured2.json'), encoding='utf-8')).items():
        for it in lst: beads[it['code']] = np.array(it['rgb'], float)
    rows = []
    for code in PAL_CODES:
        if code in ink and code in beads: rows.append((code, de(ink[code], beads[code]), ink[code], beads[code]))
    rows.sort(key=lambda r: -r[1])
    print('\nTINTA da cartela x CONTA da bandeja (ΔE2000), os 14 maiores:')
    for code, d, a, b in rows[:14]: print('   %-4s ΔE %5.1f   tinta #%02X%02X%02X   conta #%02X%02X%02X' % (code, d, *[int(round(v)) for v in a], *[int(round(v)) for v in b]))
    # 3) pares de contas quase iguais
    codes = [c for c in PAL_CODES if c in beads]
    pairs = []
    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            d = de(beads[a], beads[b])
            if d < 6.0: pairs.append((d, a, b))
    pairs.sort()
    print('\nCONTAS quase iguais na bandeja sem tampa (ΔE2000 < 6): %d pares' % len(pairs))
    for d, a, b in pairs[:40]: print('   %-4s x %-4s ΔE %4.1f   #%02X%02X%02X  #%02X%02X%02X' % (a, b, d, *[int(round(v)) for v in beads[a]], *[int(round(v)) for v in beads[b]]))
    json.dump([(a, b, round(d, 2)) for d, a, b in pairs], open(os.path.join(HERE, 'out', 'verify_codes_pairs.json'), 'w', encoding='utf-8'))


if __name__ == '__main__':
    main()
