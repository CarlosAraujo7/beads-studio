"""PRÉVIA (só leitura) de refazer as cores de um molde com a paleta das CONTAS (2026-11-02): o molde foi convertido com as cores ESTIMADAS de antes (paleta do anúncio) e,
com as cores reais, a pele bege vira creme/laranja e os marrons viram caramelo. Aqui cada letra do molde ganha a CONTA REAL mais parecida com a cor que ele mostrava antes
(ΔE2000, uma conta diferente para cada letra: não junta tons que o molde separa). NÃO grava nada no catálogo (regra 4.9): só imagens em tools/out/.
uso:  python tools/remap_cores.py "trecho do nome" ["outro trecho" ...] [--out arquivo.png] [--scale 8]
Cada linha da folha: ANTES (paleta antiga) | AGORA (mesmas letras, paleta nova: o que ele vê hoje) | PROPOSTA (letras trocadas, paleta nova)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import r5, tplfile

OLD = json.load(open(os.path.join(HERE, 'backups', 'palette-pre-contas.json'), encoding='utf-8'))['colors']
NEW = json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']
OLD_BY_L = {c['letter']: c for c in OLD}; NEW_BY_L = {c['letter']: c for c in NEW}; NEW_BY_C = {c['code']: c for c in NEW}
h2 = lambda h: np.array([int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)


import palette_tone as _PT


def lab(rgb):
    """Lab EXATO (float, sem a quantização de 8 bits do OpenCV): o mesmo cálculo do JS do index.html, para a troca de cores do app e a do Python darem o mesmo resultado"""
    return _PT.rgb2lab(rgb)


NEW_LAB = np.array([lab(h2(c['hex'])) for c in NEW])


def de_to_new(rgb):
    """ΔE2000 de uma cor para as 120 da paleta nova"""
    return np.ravel(r5._de2000(lab(rgb), NEW_LAB))


def remap(rows):
    """{letra antiga: letra nova}. Atribuição de custo mínimo (húngaro) entre as letras do molde e as 120 contas, custo = peso x ΔE2000(cor ANTIGA da letra, cor NOVA da conta);
    cada letra ganha uma conta diferente, exceto as de cor antiga quase igual (ΔE < 3), que ficam juntas."""
    from scipy.optimize import linear_sum_assignment
    cnt = {}
    for r in rows:
        for ch in r:
            if ch != '.': cnt[ch] = cnt.get(ch, 0) + 1
    letters = sorted(cnt, key=lambda c: -cnt[c])
    cost = np.zeros((len(letters), len(NEW)))
    for i, ch in enumerate(letters):
        d = de_to_new(h2(OLD_BY_L[ch]['hex']))
        cost[i] = (cnt[ch] + 6) * d
    ri, ci = linear_sum_assignment(cost)
    m = {letters[i]: NEW[j]['letter'] for i, j in zip(ri, ci)}
    # letras de cor antiga quase igual ficam com a mesma conta (a da mais frequente)
    for i, a in enumerate(letters):
        for b in letters[:i]:
            if np.ravel(r5._de2000(lab(h2(OLD_BY_L[a]['hex'])), np.array([lab(h2(OLD_BY_L[b]['hex']))])))[0] < 3.0:
                m[a] = m[b]; break
    return m


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# VERSÃO 2 (2026-11-02, depois de o dono achar "estranho o degradê de bege" no rosto dos Cavaleiros: a versão 1 espalhava os tons de pele em contas de matiz diferente, rosa, damasco e até
# verde-oliva). Na versão 2 as letras de PELE (cor antiga clara e quente) de ΔE < 10 entre si viram UM grupo, só podem ir para contas de pele (SKIN_NEW) e o matiz conta mais no custo.
import colorsys
OLD_RGB = {L: h2(c['hex']) for L, c in OLD_BY_L.items()}
NEW_IDX = {c['code']: i for i, c in enumerate(NEW)}
SKIN_NEW = ['E11', 'E1', 'E14', 'E15', 'G1', 'A9', 'A12', 'F1', 'F14', 'G2', 'G3', 'G9', 'E8', 'H12', 'A1', 'G14', 'M9']


def is_skin_old(letter):
    """cor antiga de PELE: clara, pouco saturada e de matiz bege/pêssego no Lab (o creme amarelado A1/A3 e o dourado NÃO são pele: na 1ª tentativa entravam no grupo e clareavam o rosto do Shiryu)"""
    L, a, b = lab(OLD_RGB[letter]); C = (a * a + b * b) ** .5; h = float(np.degrees(np.arctan2(b, a)) % 360)
    return (L >= 76 and 7 <= C <= 31 and 35 <= h <= 80) or (L >= 80 and 7 <= C <= 26 and 80 < h <= 105)       # o 2º ramo é o creme claro (H12/A1): o rosto creme do Seiya de prata virava cáqui; o tan de cabelo (G9, G3, A12: L < 76 ou croma > 31) NÃO é pele


def _huab(l): return float(np.degrees(np.arctan2(l[2], l[1])) % 360)


def _dh(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def remap2(rows, skin_T=10.0, hue_w=0.5, hue_free=18.0, chroma_w=0.6, chroma_free=10.0, dup_pen=5.0):
    """{letra antiga: letra nova}. Igual à versão 1, mas: (1) letras de pele de ΔE < skin_T entre si formam um grupo só; (2) o grupo de pele só vai para contas de pele (SKIN_NEW);
    (3) no custo da pele o desvio de matiz acima de hue_free graus custa hue_w por grau (bege não pode virar rosa nem oliva)."""
    from scipy.optimize import linear_sum_assignment
    cnt = {}
    for r in rows:
        for ch in r:
            if ch != '.': cnt[ch] = cnt.get(ch, 0) + 1
    letters = sorted(cnt, key=lambda c: -cnt[c])
    labs = {ch: lab(OLD_RGB[ch]) for ch in letters}
    groups = []                                   # cada grupo: dict(letters, lab, count, skin)
    for ch in letters:
        if is_skin_old(ch):
            for g in groups:
                if g['skin'] and float(np.ravel(r5._de2000(labs[ch], np.array([g['rep']])))[0]) < skin_T:
                    g['letters'].append(ch); g['count'] += cnt[ch]; break
            else:
                groups.append(dict(letters=[ch], lab=labs[ch], rep=labs[ch], count=cnt[ch], skin=True))
        else:
            groups.append(dict(letters=[ch], lab=labs[ch], rep=labs[ch], count=cnt[ch], skin=False))
    for g in groups:                              # cor do grupo = média das cores antigas das letras, pesada pelas contas
        if len(g['letters']) > 1:
            w = np.array([cnt[c] for c in g['letters']], float); g['lab'] = (np.array([labs[c] for c in g['letters']]) * w[:, None]).sum(axis=0) / w.sum()
    nb = len(NEW)
    cost = np.zeros((len(groups), nb * 2))                       # 2 cópias de cada conta: usar a MESMA conta em duas letras custa dup_pen a mais (junta em vez de empurrar para uma cor viva)
    skin_idx = [NEW_IDX[c] for c in SKIN_NEW]
    chroma_new = np.hypot(NEW_LAB[:, 1], NEW_LAB[:, 2])
    for i, g in enumerate(groups):
        d = np.ravel(r5._de2000(g['lab'], NEW_LAB))
        c_old = float(np.hypot(g['lab'][1], g['lab'][2]))
        d = d + chroma_w * np.maximum(0.0, chroma_new - c_old - chroma_free)        # cor antiga apagada não pode virar conta muito mais viva
        if g['skin']:
            pen = np.array([hue_w * max(0.0, _dh(_huab(g['lab']), _huab(NEW_LAB[j])) - hue_free) + 0.5 * max(0.0, g['lab'][0] - NEW_LAB[j][0]) + 0.15 * max(0.0, NEW_LAB[j][0] - g['lab'][0]) for j in range(len(NEW))])
            d = d + pen
            mask = np.full(nb, 1e4); mask[skin_idx] = 0.0
            d = d + mask
        cost[i] = (g['count'] + 6) * np.concatenate([d, d + dup_pen])
    ri, ci = linear_sum_assignment(cost)
    m = {}
    for i, j in zip(ri, ci):
        for ch in groups[i]['letters']: m[ch] = NEW[j % nb]['letter']
    for i, a in enumerate(letters):               # letras não-pele de cor antiga quase igual ficam com a mesma conta
        if is_skin_old(a): continue
        for b in letters[:i]:
            if not is_skin_old(b) and float(np.ravel(r5._de2000(labs[a], np.array([labs[b]])))[0]) < 3.0:
                m[a] = m[b]; break
    return m


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# VERSÃO 3 (2026-11-02, depois de o dono dizer que "a maior diferença foi que todas as cores ficaram muito mais vivas, e não é isso" e listar moldes com azul que virou roxo, laranja neon etc.).
# O custo deixa de ser só ΔE2000 e passa a PROTEGER o matiz, desprezar a "mais viva que antes" e preferir conta mais clara a mais escura. O mesmo cálculo existe em JS no index.html
# (botão "Cores de antes" em Contas por cor); `tools/remap_js_check.py` confere que os dois dão a MESMA troca.
# contas que NÃO contam como contas separadas (o dono, 2026-11-02: o H12 não existe nas cartelas dele como bege e "dá certo trocar pelo A1"; nas bandejas o H12 e o A1 são o mesmo creme, ΔE 4,6):
# nunca são escolhidas como destino de uma troca de cores (a letra do H12 num molde vai para a conta mais parecida que NÃO seja alias).
ALIAS_CODES = ('H12',)
ALIAS_IDX = [NEW_IDX[c] for c in ALIAS_CODES]


V3 = dict(skin_T=10.0, hue_w=0.35, hue_free=12.0, skin_hue_free=18.0, chroma_w=0.45, chroma_free=10.0, dull_w=0.15, dull_free=20.0, dark_w=0.35, light_w=0.12, dup_pen=5.0, same_T=3.0, count_k=6.0)


def _lch(l):
    return float(l[0]), float(np.hypot(l[1], l[2])), float(np.degrees(np.arctan2(l[2], l[1])) % 360)


def cost_v3(old_lab, new_labs, skin, P=V3):
    """custo de cada uma das contas novas para uma cor antiga (vetor de len(new_labs))"""
    L1, C1, h1 = _lch(old_lab)
    base = np.ravel(r5._de2000(old_lab, new_labs)).astype(float)
    out = np.empty(len(new_labs))
    for j in range(len(new_labs)):
        L2, C2, h2 = _lch(new_labs[j])
        dh = _dh(h1, h2)
        w = min(1.0, C1 / 25.0) * min(1.0, C2 / 25.0)                      # o matiz só conta quando as duas cores são cromáticas
        pen = P['hue_w'] * w * max(0.0, dh - (P['skin_hue_free'] if skin else P['hue_free']))
        pen += P['chroma_w'] * max(0.0, C2 - C1 - P['chroma_free']) + P['dull_w'] * max(0.0, C1 - C2 - P['dull_free'])
        pen += P['dark_w'] * max(0.0, L1 - L2) + P['light_w'] * max(0.0, L2 - L1)
        out[j] = base[j] + pen
    return out


def remap3(rows, P=V3, new_labs=None, skin_codes=None):
    """{letra antiga: letra nova}: atribuição de custo mínimo (húngaro) entre os GRUPOS de letras do molde e as 120 contas (2 cópias de cada: repetir a mesma conta custa dup_pen a mais).
    Letras de pele de ΔE < skin_T entre si formam UM grupo e só vão para contas de pele; letras quase iguais (ΔE < same_T) fora da pele também ficam com a mesma conta."""
    from scipy.optimize import linear_sum_assignment
    new_labs = NEW_LAB if new_labs is None else new_labs
    skin_idx = [NEW_IDX[c] for c in (skin_codes or SKIN_NEW)]
    cnt = {}
    for r in rows:
        for ch in r:
            if ch != '.': cnt[ch] = cnt.get(ch, 0) + 1
    letters = sorted(cnt, key=lambda c: -cnt[c])
    labs = {ch: lab(OLD_RGB[ch]) for ch in letters}
    groups = []
    for ch in letters:
        if is_skin_old(ch):
            for g in groups:
                if g['skin'] and float(np.ravel(r5._de2000(labs[ch], np.array([g['rep']])))[0]) < P['skin_T']:
                    g['letters'].append(ch); g['count'] += cnt[ch]; break
            else:
                groups.append(dict(letters=[ch], lab=labs[ch], rep=labs[ch], count=cnt[ch], skin=True))
        else:
            groups.append(dict(letters=[ch], lab=labs[ch], rep=labs[ch], count=cnt[ch], skin=False))
    for g in groups:
        if len(g['letters']) > 1:
            w = np.array([cnt[c] for c in g['letters']], float); g['lab'] = (np.array([labs[c] for c in g['letters']]) * w[:, None]).sum(axis=0) / w.sum()
    nb = len(new_labs); cost = np.zeros((len(groups), nb * 2))
    for i, g in enumerate(groups):
        d = cost_v3(g['lab'], new_labs, g['skin'], P)
        d[ALIAS_IDX] += 1e4
        if g['skin']:
            mask = np.full(nb, 1e4); mask[skin_idx] = 0.0; d = d + mask
        cost[i] = (g['count'] + P['count_k']) * np.concatenate([d, d + P['dup_pen']])
    ri, ci = linear_sum_assignment(cost)
    m = {}
    for i, j in zip(ri, ci):
        for ch in groups[i]['letters']: m[ch] = NEW[j % nb]['letter']
    for i, a in enumerate(letters):
        if is_skin_old(a): continue
        for b in letters[:i]:
            if not is_skin_old(b) and float(np.ravel(r5._de2000(labs[a], np.array([labs[b]])))[0]) < P['same_T']:
                m[a] = m[b]; break
    return m


def draw(rows, pal, scale, bg=(255, 255, 255)):
    im = Image.new('RGB', (len(rows[0]) * scale, len(rows) * scale), bg); d = ImageDraw.Draw(im)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.': d.rectangle([x * scale, y * scale, x * scale + scale - 1, y * scale + scale - 1], fill=tuple(int(v) for v in pal[ch]))
    return im


def sheet(items, out, scale=8):
    P_old = {c['letter']: h2(c['hex']) for c in OLD}; P_new = {c['letter']: h2(c['hex']) for c in NEW}
    F = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13); Fb = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 14)
    cells = []
    for it in items:
        rows = it['rows']; m = remap(rows)
        rows2 = [''.join(m.get(ch, ch) if ch != '.' else '.' for ch in r) for r in rows]
        cells.append((it['name'], draw(rows, P_old, scale, (236, 236, 236)), draw(rows, P_new, scale, (236, 236, 236)), draw(rows2, P_new, scale, (236, 236, 236)), m, rows))
    # uma linha por molde
    W = max(c[1].width * 3 + 60 for c in cells); y = 8; parts = []
    for c in cells: parts.append((y, c)); y += c[1].height + 56
    sh = Image.new('RGB', (W, y + 8), (250, 248, 244)); dr = ImageDraw.Draw(sh)
    for y0, (name, a, b, c3, m, rows) in parts:
        dr.text((8, y0), name, fill=(20, 20, 20), font=Fb)
        dr.text((8, y0 + 18), 'ANTES (paleta antiga)', fill=(90, 90, 90), font=F); dr.text((8 + a.width + 20, y0 + 18), 'AGORA (mesmas letras, paleta nova)', fill=(160, 40, 40), font=F); dr.text((8 + 2 * (a.width + 20), y0 + 18), 'PROPOSTA (contas trocadas)', fill=(30, 120, 60), font=F)
        for k, im in enumerate((a, b, c3)): sh.paste(im, (8 + k * (a.width + 20), y0 + 38))
    sh.save(out); return sh.size


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(HERE, 'out', 'remap_preview.png')
    if '--out' in sys.argv: args.remove(out)
    scale = int(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 8
    if '--scale' in sys.argv: args.remove(str(scale))
    items = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
    sel = []
    for a in args:
        hit = [it for it in items if it['id'] == a or a.lower() in it['name'].lower()]
        sel += hit[:1]
    print(len(sel), 'moldes ->', out, sheet(sel, out, scale))


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# VERSÃO 4 (2026-11-02, "as cores ficaram homogêneas demais, ruim de identificar as coisas"): a v3 acerta a COR de cada letra, mas pode juntar dois tons que o molde separava
# (o kit mede quase igual H6 e H7, vários laranjas...). A v4 acrescenta ao custo a PRESERVAÇÃO DAS BORDAS: para cada par de letras vizinhas no desenho, o contraste novo (ΔE2000 entre as duas contas)
# deve ficar perto do antigo (até um teto): custo = LAM x bordas x max(0, min(ΔE_antigo, CAP) x RHO - ΔE_novo). Resolvido por busca local (um grupo de cores por vez) a partir da solução da v3.
V4 = dict(V3, lam=1.5, cap=30.0, rho=0.8, top=10, passes=8, lw=1.5, slack=8.0)       # slack: a busca local só considera contas a no máximo `slack` de ΔE-de-custo do melhor destino do grupo (o preto do contorno não vira cinza para abrir contraste)


def edge_contrast(l1, l2, lw=1.5):
    """contraste entre duas cores para as BORDAS: Lab com a luminosidade ampliada (lw x): é a diferença de claro/escuro que deixa uma miniatura legível"""
    return float(np.sqrt((lw * (l1[0] - l2[0])) ** 2 + (l1[1] - l2[1]) ** 2 + (l1[2] - l2[2]) ** 2))


def letter_edges(rows):
    """{(a, b): n} bordas (cima/baixo/esquerda/direita) entre letras diferentes, a < b"""
    H = len(rows); out = {}
    for y in range(H):
        r = rows[y]
        for x in range(len(r)):
            a = r[x]
            if a == '.': continue
            for yy, xx in ((y, x + 1), (y + 1, x)):
                if yy < H and xx < len(rows[yy]):
                    b = rows[yy][xx]
                    if b != '.' and b != a:
                        k = (a, b) if a < b else (b, a); out[k] = out.get(k, 0) + 1
    return out


def remap4(rows, P=V4, new_labs=None, skin_codes=None):
    from scipy.optimize import linear_sum_assignment
    new_labs = NEW_LAB if new_labs is None else new_labs
    skin_idx = [NEW_IDX[c] for c in (skin_codes or SKIN_NEW)]
    cnt = {}
    for r in rows:
        for ch in r:
            if ch != '.': cnt[ch] = cnt.get(ch, 0) + 1
    letters = sorted(cnt, key=lambda c: -cnt[c])
    labs = {ch: lab(OLD_RGB[ch]) for ch in letters}
    groups = []
    for ch in letters:
        if is_skin_old(ch):
            for g in groups:
                if g['skin'] and float(np.ravel(r5._de2000(labs[ch], np.array([g['rep']])))[0]) < P['skin_T']:
                    g['letters'].append(ch); g['count'] += cnt[ch]; break
            else:
                groups.append(dict(letters=[ch], lab=labs[ch], rep=labs[ch], count=cnt[ch], skin=True))
        else:
            groups.append(dict(letters=[ch], lab=labs[ch], rep=labs[ch], count=cnt[ch], skin=False))
    for g in groups:
        if len(g['letters']) > 1:
            w = np.array([cnt[c] for c in g['letters']], float); g['lab'] = (np.array([labs[c] for c in g['letters']]) * w[:, None]).sum(axis=0) / w.sum()
    nb = len(new_labs); G = len(groups)
    base = np.zeros((G, nb)); dmat = np.zeros((G, nb))
    for i, g in enumerate(groups):
        d = cost_v3(g['lab'], new_labs, g['skin'], P)
        d[ALIAS_IDX] += 1e4
        if g['skin']:
            mask = np.full(nb, 1e4); mask[skin_idx] = 0.0; d = d + mask
        dmat[i] = d; base[i] = (g['count'] + P['count_k']) * d
    kk = np.array([(g['count'] + P['count_k']) * P['dup_pen'] for g in groups])
    cost2 = np.concatenate([base, base + kk[:, None]], axis=1)
    ri, ci = linear_sum_assignment(cost2)
    assign = [0] * G
    for i, j in zip(ri, ci): assign[i] = j % nb
    gid = {ch: i for i, g in enumerate(groups) for ch in g['letters']}
    EG = {}
    for (a, b), n in letter_edges(rows).items():
        ga, gb = gid[a], gid[b]
        if ga == gb: continue
        k = (ga, gb) if ga < gb else (gb, ga)
        dold = min(edge_contrast(labs[a], labs[b], P['lw']), P['cap']) * P['rho']
        EG.setdefault(k, []).append((n, dold))
    DEN = np.zeros((nb, nb))
    for i in range(nb):
        for j in range(nb): DEN[i, j] = edge_contrast(new_labs[i], new_labs[j], P['lw'])
    nbr = {i: [] for i in range(G)}
    for (ga, gb), lst in EG.items():
        nbr[ga].append((gb, lst)); nbr[gb].append((ga, lst))

    def edge_cost(g, b, asg):
        s = 0.0
        for h, lst in nbr[g]:
            dn = DEN[b, asg[h]]
            for n, dold in lst: s += n * max(0.0, dold - dn)
        return P['lam'] * s

    def dup_cost(g, b, asg):
        return sum(kk[g] for h in range(G) if h != g and asg[h] == b)

    own = {}
    for i, g in enumerate(groups):
        if len(g['letters']) == 1 and NEW_BY_L[g['letters'][0]]['code'] not in ALIAS_CODES: own[i] = NEW_IDX[NEW_BY_L[g['letters'][0]]['code']]
    for _ in range(P['passes']):
        changed = False
        for g in sorted(range(G), key=lambda i: -groups[i]['count']):
            dmin = dmat[g].min()
            cand = {int(b) for b in np.argsort(base[g])[:P['top']] if dmat[g][b] <= dmin + P['slack']} | {assign[g]}
            if g in own: cand.add(own[g])
            cur = assign[g]; best = base[g][cur] + edge_cost(g, cur, assign) + dup_cost(g, cur, assign); bj = cur
            for b in sorted(cand):
                v = base[g][b] + edge_cost(g, b, assign) + dup_cost(g, b, assign)
                if v < best - 1e-9: best, bj = v, b
            if bj != cur: assign[g] = bj; changed = True
        if not changed: break
    m = {}
    for i, g in enumerate(groups):
        for ch in g['letters']: m[ch] = NEW[assign[i]]['letter']
    for i, a in enumerate(letters):
        if is_skin_old(a): continue
        for b in letters[:i]:
            if not is_skin_old(b) and float(np.ravel(r5._de2000(labs[a], np.array([labs[b]])))[0]) < P['same_T']:
                m[a] = m[b]; break
    return m


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# JUNTAR TONS QUASE IGUAIS (2026-11-02, pedido do dono: "no molde do Kurama chibi há 3 tons de vermelho que são praticamente a mesma coisa; é mais simples e até divertido usar um só; mantém só uma das cores
# (usar mais se necessário) e deixa a opção: se o vermelho padrão acabar, uso um parecido"). Depois da troca de cores, contas de destino com ΔE2000 < MERGE_T (na tela) viram UMA só: a mais usada fica; as outras
# continuam disponíveis como substitutas (botão ⇄). A busca é por frequência (não encadeia: A~B e B~C não juntam C com A se C não é parecida com A).
MERGE_T = 6.0


def merge_near(m, rows, T=MERGE_T, new_labs=None):
    new_labs = NEW_LAB if new_labs is None else new_labs
    cnt = {}
    for r in rows:
        for ch in r:
            if ch != '.': cnt[ch] = cnt.get(ch, 0) + 1
    use = {}
    for a, n in cnt.items(): use[m[a]] = use.get(m[a], 0) + n
    order = sorted(use, key=lambda b: -use[b])
    keep = []; to = {}
    for b in order:
        lb = new_labs[NEW_IDX[NEW_BY_L[b]['code']]]
        for k in keep:
            if float(np.ravel(r5._de2000(lb, np.array([new_labs[NEW_IDX[NEW_BY_L[k]['code']]]])))[0]) < T: to[b] = k; break
        else:
            keep.append(b); to[b] = b
    return {a: to[b] for a, b in m.items()}


def remap5(rows, merge=True, T=MERGE_T):
    """a troca de cores completa: v4 + (opcional) juntar tons quase iguais"""
    m = remap4(rows)
    return merge_near(m, rows, T) if merge else m


def merge_similar(rows, T=MERGE_T, new_labs=None):
    """JUNTAR TONS QUASE IGUAIS pelas contas que o molde JÁ usa (é o que o dono descreveu: o Kurama usa F5, F13 e F8, que são "praticamente a mesma coisa": fica só uma). Não troca para outras contas;
    só leva as parecidas (ΔE2000 < T entre as cores na tela) para a mais usada do grupo. Devolve {letra: letra}."""
    new_labs = NEW_LAB if new_labs is None else new_labs
    cnt = {}
    for r in rows:
        for ch in r:
            if ch != '.': cnt[ch] = cnt.get(ch, 0) + 1
    order = sorted(cnt, key=lambda c: -cnt[c])
    keep = []; m = {}
    for a in order:
        la = new_labs[NEW_IDX[NEW_BY_L[a]['code']]]
        for k in keep:
            if float(np.ravel(r5._de2000(la, np.array([new_labs[NEW_IDX[NEW_BY_L[k]['code']]]])))[0]) < T: m[a] = k; break
        else:
            keep.append(a); m[a] = a
    return m
