"""Remessas 1-4: versão de 120 cores dos moldes que o pipeline antigo tirou de uma IMAGEM (gráfico com grade) e que ainda têm o mesmo desenho.

Para cada molde (id) escolhido em out/match_old.json (nota >= 0.78 e conferido a olho), converte a imagem de origem com a paleta de 120 cores (exact6) e
RECOLORE o molde atual: a geometria (quais contas existem) é a do molde que você já tem; só a cor de cada conta vem da conversão de 120 cores.
Se o molde é um recorte da conversão, acha o deslocamento em que as contas coincidem (>= 95%). Se não coincidir, o molde fica de fora.

uso:  BEADPAL=120 python tools/r_old120.py        -> data/old120.json   {id do molde: rows}  (make_120.py usa)
"""
import os, sys, json, glob
SP = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SP)
os.environ['REMNUM'] = '1'
sys.path.insert(0, SP)
if os.environ.get('BEADPAL') != '120': sys.exit('rode com BEADPAL=120')
import r6, tplfile

cat = {t['id']: t for t in tplfile.parse(os.path.join(SP, 'backups', 'pre-finalize-120.js'))['items']}      # instantâneo com todos os moldes de 24 cores (o catálogo atual pode ter perdido alguns por exclusão do usuário)
match = json.load(open(os.path.join(SP, 'out', 'match_old.json'), encoding='utf-8'))
# fora de propósito: o molde foi feito para reproduzir a SUA peça (Geass: disco lilás e pássaro rosa) e uma foto (Stitch como Link)
SKIP = {'sigilo-do-geass-code-geass', 'stitch-como-link-zelda'}
# imagens com mais de um molde (Avatar): a imagem 30 da remessa 2 é uma folha 2x2 de emblemas; cada molde é um quadrante da conversão
# quadrante (dy, dx) de cada emblema na conversão 64x64 (tiles cheios: a busca por coincidência não distingue)
OFFSETS = {'avatar-tribo-da-agua': (0, 0), 'avatar-reino-da-terra': (0, 32), 'avatar-nomades-do-ar': (32, 0), 'avatar-nacao-do-fogo': (32, 32)}


def occ(a, b, dy, dx):
    """fração das contas do molde `a` que coincidem (existem nos dois) com `b` deslocado; None se não cabe"""
    if dy < 0 or dx < 0 or dy + len(a) > len(b) or dx + len(a[0]) > len(b[0]): return None
    tot = sum(len(r) for r in a); ok = 0
    for y, r in enumerate(a):
        rb = b[y + dy]
        for x, c in enumerate(r):
            if (c != '.') == (rb[x + dx] != '.'): ok += 1
    return ok / tot


from palette import ALL
from make_palette import rgb2lab, h2rgb
_L = {c['letter']: rgb2lab(h2rgb(c['hex']))[0] for c in ALL}


def lum_agree(a, b, dy, dx):
    """fração das contas do molde cuja cor tem luminosidade parecida (±28) com a da conversão no mesmo lugar: separa o alinhamento certo do
    deslocado por 1 conta (molde SEM contorno sobre a conversão COM contorno encaixa na silhueta mas pega as cores do contorno)"""
    n = ok = 0
    for y, r in enumerate(a):
        rb = b[y + dy]
        for x, c in enumerate(r):
            if c == '.': continue
            d = rb[x + dx]
            n += 1
            if d != '.' and abs(_L[c] - _L[d]) <= 28: ok += 1
    return ok / max(1, n)


def recolor(mold, conv, fixed=None):
    best = None
    cands = [fixed] if fixed else [(dy, dx) for dy in range(0, len(conv) - len(mold) + 1) for dx in range(0, len(conv[0]) - len(mold[0]) + 1)]
    for dy, dx in cands:
        o = occ(mold, conv, dy, dx)
        if o is None or o < 0.90: continue
        sc = o + 0.6 * lum_agree(mold, conv, dy, dx)
        if best is None or sc > best[0]: best = (sc, o, dy, dx)
    if not best: return None, (0, 0, 0, 0)
    sc, o, dy, dx = best
    if o < 0.93 or lum_agree(mold, conv, dy, dx) < 0.60: return None, (o, o, dy, dx)
    out = []
    for y, r in enumerate(mold):
        row = ''
        for x, c in enumerate(r):
            d = conv[y + dy][x + dx]
            # onde a conversão não tem conta, ou a luminosidade difere muito (contorno que o molde não tem), fica a cor antiga (é letra válida das 120)
            row += c if (c == '.' or d == '.' or abs(_L[c] - _L[d]) > 34) else d
        out.append(row)
    return out, (o, o, dy, dx)


res = {}; fail = []
convs = {}
for k, v in sorted(match.items()):
    name, id_ = k.split('|')
    rem, idx, score = v[0]
    if score < 0.78 or id_ in SKIP: continue
    key = (rem, idx)
    if key not in convs:
        r6.FILES = sorted(glob.glob(os.path.join(ROOT, 'remessas', f'remessa {rem}', '*.*')))
        import r5 as _r5; _r5.SKIN_ON = _r5.skin_for(name, cat[id_]['group'])
        try: convs[key] = r6.exact6(idx)
        except Exception: convs[key] = None
    conv = convs[key]
    if not conv: fail.append((name, 'sem conversão')); continue
    if id_ not in cat: continue
    mold = cat[id_]['rows']
    rows, best = recolor(mold, conv, OFFSETS.get(id_))
    if rows is None: fail.append((name, f'melhor coincidência {best[0]:.2f}')); continue
    res[id_] = rows
print(len(res), 'recoloridos;', len(fail), 'falharam:', fail)
json.dump(res, open(os.path.join(SP, 'data', 'old120.json'), 'w', encoding='utf-8'), ensure_ascii=False)
