"""Quais moldes dá para montar com as contas que sobraram? Só LÊ o catálogo. Saída: tools/out/moldes-com-as-contas-que-tenho.png (miniaturas já com as trocas) e o resumo na tela.
  BEADPAL=120 python tools/estoque.py
ESTOQUE = estimativa por cor, olhando a foto da bandeja (kit antigo de 24 cores, 2026-11-01); troque quando contar de verdade.
Faixas:  1 exato = só cores do kit e estoque suficiente;
         2 troca = as cores que ele não tem viram a mais parecida que há em quantidade, com pouca diferença (nenhuma cor com ΔE > LIM);
         3 sem preto = como 2, mas TODO o preto vira UMA cor escura que o molde ainda não usa (muda o visual: contorno colorido); fora se o preto passa de metade do molde."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
from collections import Counter
from tplfile import parse
import palette as P, shrink
from PIL import Image, ImageDraw, ImageFont
L = {c['code']: c['letter'] for c in P.ALL}; CODE = {c['letter']: c['code'] for c in P.ALL}; LAB = shrink.LAB
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}
ESTOQUE = {'H1': 250, 'H2': 300, 'H3': 180, 'H4': 150, 'H5': 12, 'H7': 7, 'B8': 200, 'B5': 0, 'B3': 200, 'C8': 300, 'C5': 40, 'C3': 250, 'D7': 250, 'D6': 250, 'D9': 250, 'F5': 12, 'E4': 250, 'E2': 250, 'G7': 150, 'G5': 25, 'G1': 25, 'A7': 250, 'A6': 250, 'A4': 12}
LIM = 14.0
DARK = ['D7', 'G7', 'B8', 'H4']           # o que faz o papel do preto quando ele acaba, do mais escuro para o mais claro


def is_black(c):
    return LAB[c][0] < 30 and (LAB[c][1] ** 2 + LAB[c][2] ** 2) ** .5 < 14


def plan(rows, troca_preto=None):
    """devolve (dá para montar?, trocas {código pedido: código usado}, maior ΔE). troca_preto = letra que faz TODO o preto (uma cor só: misturar duas no contorno fica feio)"""
    cnt = Counter(c for r in rows for c in r if c != '.')
    st = {L[k]: v for k, v in ESTOQUE.items()}
    swaps = {}; worst = 0.0
    if troca_preto:
        n = sum(v for c, v in cnt.items() if is_black(c))
        if st[troca_preto] < n: return False, swaps, worst
        st[troca_preto] -= n
        for c in [c for c in cnt if is_black(c)]: swaps[CODE[c]] = CODE[troca_preto]; del cnt[c]
    for c, n in sorted(cnt.items(), key=lambda kv: (kv[0] not in st, -kv[1])):
        left = n
        if c in st:
            use = min(left, st[c]); st[c] -= use; left -= use
        while left:
            cand = [k for k, v in st.items() if v > 0]
            if not cand: return False, swaps, worst
            k = min(cand, key=lambda q: float(np.linalg.norm(LAB[q] - LAB[c])))
            de = float(np.linalg.norm(LAB[k] - LAB[c]))
            if de > LIM: return False, swaps, worst
            worst = max(worst, de)
            use = min(left, st[k]); st[k] -= use; left -= use
            swaps[CODE[c]] = CODE[k]
    return True, swaps, worst


def faixa(rows):
    ok, sw, w = plan(rows)
    if ok: return (1 if not sw else 2), sw, w
    cnt = Counter(c for r in rows for c in r if c != '.'); tot = sum(cnt.values()); nb = sum(v for c, v in cnt.items() if is_black(c))
    if nb > 0.5 * tot: return 0, {}, 0                                # o preto é a figura (Vader, Slender Man): trocado, deixa de ser ela
    for d in DARK:
        if cnt.get(L[d], 0) > 0: continue                             # a figura já usa essa cor: o contorno se perderia nela
        ok, sw, w = plan(rows, L[d])
        if ok: return 3, sw, w
    return 0, {}, 0


def applied(rows, sw):
    m = {L[k]: L[v] for k, v in sw.items()}
    return [''.join(m.get(c, c) for c in r) for r in rows]


def main():
    items = parse(os.path.join(ROOT, 'templates.js'))['items']
    F = {1: [], 2: [], 3: []}
    for t in items:
        k, sw, w = faixa(t['rows'])
        if k: F[k].append((t['group'], t['name'], t['rows'], sum(c != '.' for r in t['rows'] for c in r), sw, w))
    print('moldes', len(items), {k: len(v) for k, v in F.items()})
    font = ImageFont.load_default()
    all_ = []
    for k, its in F.items():
        its.sort(key=lambda x: (x[0], x[3]))
        print('=== faixa', k, len(its))
        for g, n, r, b, sw, w in its: print(f'{g} | {n} | {b} contas | {sw} | {w:.0f}'); all_.append((k, g, n, applied(r, sw), b, sw))
    cols, cw, ch = 7, 200, 244; rows_ = (len(all_) + cols - 1) // cols
    S = Image.new('RGB', (cols * cw, rows_ * ch), (58, 58, 62)); d = ImageDraw.Draw(S)
    for i, (k, g, n, r, b, sw) in enumerate(all_):
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        sc = max(1, min(186 // len(r[0]), 186 // len(r)))
        for y, l in enumerate(r):
            for x, c in enumerate(l):
                if c != '.': d.rectangle((x0 + 6 + x * sc, y0 + 4 + y * sc, x0 + 6 + (x + 1) * sc - 1, y0 + 4 + (y + 1) * sc - 1), fill=HEX[c])
        d.text((x0 + 4, y0 + 192), n[:32], fill=(255, 255, 0), font=font)
        d.text((x0 + 4, y0 + 206), f'{b} contas', fill=(255, 255, 255), font=font)
        d.text((x0 + 4, y0 + 220), ('preto -> ' + next((v for q, v in sw.items() if is_black(L[q])), '')) if k == 3 else 'cores exatas', fill=(255, 255, 255), font=font)
    S.save(os.path.join(HERE, 'out', 'moldes-com-as-contas-que-tenho.png'))


if __name__ == '__main__':
    main()
