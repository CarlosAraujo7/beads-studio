"""Remessa 31 pela REGRA FIEL (2026-11-06, topo do CLAUDE.md: "passe a tentar seguir fielmente qualquer desenho"): reconverte só os moldes que o dono mostrou nas capturas
(menos o Piccolo) e todos os de Eyeshield 21, SEM tirar a boca, SEM carimbar olhos e SEM retoque de rosto. Ficam só os consertos de conversão (máscara de fundo, hachura)
e a limpeza de ruído (r31v2.strong) e a regra do branco (H1 -> H2 no branco do desenho).
    BEADPAL=120 R31FIEL=1 python tools/r31_fiel.py build ["trecho" ...]    -> tools/data/r31fiel_new.json (guarda cada reconversão: não é reproduzível conta a conta)
    BEADPAL=120 R31FIEL=1 python tools/r31_fiel.py sheet ["trecho" ...]    -> tools/out/r31fiel_N.png (imagem | catálogo | fiel)
NÃO grava no catálogo: a gravação, se ele aprovar, é pelo tools/r31_rev.py (mesmo esquema de build/apply/revert)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120'); os.environ['R31FIEL'] = '1'
import r31_exfinal as X
import r31v2, tplfile

D = os.path.join(HERE, 'data')
NEW = os.path.join(D, 'r31fiel_new.json')
CAT = os.path.join(os.path.dirname(HERE), 'templates.js')
_raw = json.load(open(os.path.join(D, 'final33_raw_120.json'), encoding='utf-8'))
_fin = json.load(open(os.path.join(D, 'final33_120.json'), encoding='utf-8'))
CATNAME = {a[0]: b[0] for a, b in zip(_raw, _fin)}          # nome do CFG -> nome no catálogo

# os moldes das capturas (menos o Piccolo, que ele mesmo ajustou) e todos os de Eyeshield 21, por categoria no catálogo
SERIES = ('Akame ga Kill', 'Attack on Titan', 'Code Geass', 'Dororo', 'Dragon Ball', 'Genéricos', 'Hellsing', 'Hunter x Hunter', 'Marvel', 'My Hero Academia', 'Naruto',
          'WWE', 'Eyeshield 21')
FORA = ('Piccolo',)

# consertos de CONVERSÃO (não de rosto), os mesmos que funcionaram na revisão: fundo da cor da pele vazava o rosto; mangá com hachura virava sujeira; figuras encostadas na folha
_E21 = dict(hatch=5, pre_blur=3, line_L=30, t_line=0.14)
_E21M = dict(hatch=7, pre_blur=4, line_L=28, t_line=0.18)
X.KW_FIEL.update({
    'Chi-Chi (Dragon Ball, chibi, cartão rosa)': dict(mask=X.OM(dark=100)),
    'Sarada Uchiha (Naruto, chibi, fundo rosa)': dict(mask=X.OM(dark=100)),
    'Lutadora loira (WWE, estilo Meninas Superpoderosas, trio)': dict(mask=X.OMF(47, (0, 125, 345, 470), cut=[(290, 125, 345, 212)])),
    'Becky Lynch (WWE, estilo Meninas Superpoderosas, trio)': dict(mask=X.OMF(47, (285, 25, 605, 420), cut=[(285, 232, 332, 420), (572, 130, 605, 420)])),
    'Paige (WWE, estilo Meninas Superpoderosas, trio)': dict(mask=X.OMF(47, (555, 105, 862, 485), cut=[(555, 105, 585, 215)])),
})
for _n, _s, _i, _f, _g in X.CFG:
    if _s == 'Eyeshield 21' or _i == 40:
        X.KW_FIEL[_n] = dict(_E21M if 'desenho' in _n else _E21)


def targets(qs=()):
    cat = {t['name']: t for t in tplfile.parse(CAT)['items']}
    out = []
    for n, s, idx, fn, grp in X.CFG:
        cn = CATNAME.get(n)
        if cn not in cat or grp not in ('ill', 'folha'): continue          # excluído por ele, ou gráfico/pixel art/foto (já são cópia fiel)
        if cat[cn]['group'] not in SERIES or any(f in cn for f in FORA): continue
        if qs and not any(q.lower() in cn.lower() for q in qs): continue
        out.append((n, cn, idx, fn))
    return out


def build(qs):
    new = json.load(open(NEW, encoding='utf-8')) if os.path.exists(NEW) else {}
    for n, cn, idx, fn in targets(qs):
        if cn in new and not qs: continue          # já convertido: guarda (a conversão não é reproduzível conta a conta)
        X.P.CUR[0] = n; X.r5.SKIN_ON = False
        print('-', cn, flush=True)
        r = fn()
        r = X.h1_small(n, X.h1_face(n, r))          # branco do desenho = conta branca H2 (a H1 é transparente)
        r = r31v2.strong(r)
        new[cn] = r
        json.dump(new, open(NEW, 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(new), 'moldes em', NEW)


def sheet(qs):
    new = json.load(open(NEW, encoding='utf-8'))
    cat = {t['name']: t['rows'] for t in tplfile.parse(CAT)['items']}
    items = []
    for n, cn, idx, fn in targets(qs):
        if cn not in new: continue
        src = X.R.source_img(idx, getattr(fn, 'box', None))
        if getattr(fn, 'rot', 0): src = src.rotate(-90 * fn.rot, expand=True)
        items += [(f'{idx}: {cn[:44]}', src, cat[cn]), ('fiel', None, new[cn])]
    for f in os.listdir(X.OUT):
        if f.startswith('r31fiel_') and f.endswith('.png'): os.remove(os.path.join(X.OUT, f))
    per = 18
    for k in range(0, len(items), per):
        X.R.pairsheet(items[k:k + per], os.path.join(X.OUT, f'r31fiel_{k // per + 1}.png'), H=280)
    print(len(items) // 2, 'moldes,', (len(items) + per - 1) // per, 'folhas')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'sheet': sheet(a[1:])
    else: build(a[1:] if a and a[0] == 'build' else a)
