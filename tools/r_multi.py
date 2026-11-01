"""Moldes de MAIS DE UMA PLACA (2, 3 ou 4). A prioridade do catálogo é 1 placa; estes existem onde 1 placa fica feia ou é impossível
(pedido do usuário, 2026-10-27, junto com as abas "1 placa / 2 placas / 3 / 4" da galeria).

  (a) remessa 14: ilustrações que não ficaram reconhecíveis em 50 contas (retratos, artes detalhadas) refeitas com mais contas (illus.convert4(plates=N));
  (b) irmãos "(grande)" de moldes que o catálogo reduziu muito para caber numa placa (a versão de 1 placa continua lá): voltam ao tamanho original
      (ou o menor que caiba em 2 placas sem perder mais de 15%).

uso:  BEADPAL=120 python tools/r_multi.py [filtro...]   -> data/final_multi_120.json (itens [nome, série, linhas, {"plates": N}]) + prévias out/multi_x_*.png
depois: python tools/add_templates.py tools/data/final_multi_120.json
"""
import os, sys, json, glob
os.environ['REMNUM'] = '14'
SP = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SP)
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, outline as O, illus, shrink, tplfile
from flat import render_flat
from palette import sfx
FILES = sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa 14', '*.*')))
DK = dict(dark_frac=0.26, dark_L=28.0, ncolors=20)


def plates_of(rows): return -(-max(len(r) for r in rows) // 50) * -(-len(rows) // 50)


def M(idx, plates, **kw):
    a = dict(DK); a.update(kw)
    return illus.convert4(FILES[idx], plates=plates, **a)


# (nome, série, imagem da remessa 14, placas, kwargs)
A = [
 ('All Might (retrato)', 'My Hero Academia', 1, 4, dict(bg='flat', tol=60)),
 ('Seiya de Pégaso (retrato)', 'Cavaleiros do Zodíaco', 26, 4, {}),
 ('Seiya de Sagitário (chibi, asas)', 'Cavaleiros do Zodíaco', 2, 4, {}),
 ('Seiya de Sagitário (chibi, busto)', 'Cavaleiros do Zodíaco', 7, 4, {}),
 ('Shun de Andrômeda (chibi, capacete rosa)', 'Cavaleiros do Zodíaco', 8, 4, {}),
 ('Colar do Ace (chamas)', 'One Piece', 22, 4, {}),
]
# deixados de fora mesmo com 2-4 placas (continuam ruins/ruidosos): Shiryu retrato de mangá (32), Shiryu com pétalas (31), Ikki tatuagem (42), Goku criança com Shenlong (23), chibi de cabelo claro (14)
# (b) irmãos "(grande)" — nomes dos moldes do catálogo que foram muito reduzidos
B = ['Saitama (One Punch Man)', 'Haku (Viagem de Chihiro)', 'Naruto (chibi pixel, brilho verde)', 'Okarun transformado', 'Echo Echo (Ben 10)']


def fit_multi(rows):
    """volta ao tamanho original; se ele for muito grande, o menor tamanho que cabe em 2 placas (perdendo <= 15%) ou, senão, no máximo 100 (4 placas)"""
    w = max(len(r) for r in rows); h = len(rows); lo, hi = min(w, h), max(w, h)
    s2 = int(min(100, 50 * hi / lo))
    if hi <= 100 and plates_of(rows) <= 4 and not (s2 >= 0.85 * hi and plates_of(rows) > 2): return rows
    size = s2 if s2 >= 0.85 * hi else min(100, hi)
    return shrink.shrink(rows, size, 'bias', empty_at=0.6) if size < hi else rows


def build(only=()):
    out = []
    for n, g, idx, pl, kw in A:
        if only and not any(o in n for o in only): continue
        r5.SKIN_ON = r5.skin_for(n, g)
        r = M(idx, pl, **kw); out.append((n, g, r, {'plates': plates_of(r)}))
    big = json.load(open(os.path.join(SP, 'out', 'big_orig.json'), encoding='utf-8')) if os.path.exists(os.path.join(SP, 'out', 'big_orig.json')) else {}
    cat = {t['name']: t for t in tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']}
    byname = {v['name']: v for v in big.values()}
    for n in B:
        nn = f'{n} (grande)'
        if only and not any(o in nn for o in only): continue
        if n not in byname: print('AVISO: sem original grande de', n); continue
        r = fit_multi(byname[n]['rows']); out.append((nn, cat[n]['group'] if n in cat else 'Outros', r, {'plates': plates_of(r)}))
    return out


if __name__ == '__main__':
    only = sys.argv[1:]
    out = build(only)
    print(len(out), 'moldes de várias placas:', [(n[:28], len(r[0]), len(r), o['plates']) for n, g, r, o in out])
    if not only: json.dump(out, open(os.path.join(SP, 'data', 'final_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    items = [(f'{n[:24]} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r) for n, g, r, o in out]
    for k in range(0, len(items), 6):
        render_flat(items[k:k + 6], os.path.join(OUT, f'multi_x_{k // 6}' + sfx() + '.png'), scale=7, W=1900)
