"""Monta a paleta CANDIDATA a partir das fotos das CONTAS (paleta 120/foto-contas-N.jpg) e a compara com a antiga em moldes do catálogo. NÃO altera palette.json nem o app.
O dono reprovou a paleta feita da cartela (a tinta impressa não é a cor da conta: rosto bege virou cinza) e mandou fotos das bandejas: a cor de cada compartimento vale para o código impresso na cartela.
uso:  python tools/build_bead_palette.py [--apply]
Regras (CLAUDE.md §7.38):
  1. cor = mediana da faixa de luminância 40-85% da janela central do compartimento (tira furo, sombra entre contas e reflexo da tampa), com o matiz do papel da cartela tirado (canal x média/papel, brilho igual);
  2. ficam como estavam: cinzas e transparente (H1, H2, H3, H4, H5, H7), a família da PELE (SKIN), os terrosos e escuros (EARTH) e todo vermelho, rosa, laranja e roxo (o reflexo frio da tampa os puxa para o rosa/azul); só mudam as cores VIVAS de matiz 40-255 graus (amarelo, verde, ciano, azul);
  3. cor escura (L < 50) é compensada: a faixa clara a deixa mais clara que a conta (reflexo da tampa), então vai 35% para a mediana da faixa 20-55 da própria janela;
  4. diferença de até 5 ΔE2000 para a antiga NÃO muda (está dentro do erro da foto): a pele (E11, E14, E2, G3, A12...) quase toda fica como estava;
  5. nome novo (rótulo a partir do hex) só nas que mudam; est=True nas que mudam (aparecem com ~ em Ajustar cores).
Grava tools/data/palette_contas_candidata.json, tools/out/palette_contas_trocas.png (antiga x candidata) e tools/out/palette_contas_moldes.png (moldes com as duas). Com --apply grava em palette.json (cópia em tools/backups/palette-pre-contas.json)."""
import os, sys, json, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import measure_beads as MB
import r5, make_palette as MP, tplfile
OUT = os.path.join(HERE, 'out')
OLD = json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))
OLDC = {c['code']: c for c in OLD['colors']}
KEEP = {'H1', 'H2', 'H3', 'H4', 'H5', 'H7'}
# a PELE (o dono reprovou a cartela justamente por rosto cinza) e os TERROSOS/escuros: a bandeja tem véu azul da tampa e a medição sai rosada, roxa ou azulada; ficam como estavam
SKIN = {'G1', 'G2', 'G3', 'E1', 'E11', 'E14', 'E15', 'A12', 'G9', 'F1', 'F14', 'E8', 'E2'}
EARTH = {'G5', 'G7', 'G13', 'G14', 'G17', 'F6', 'F7', 'F10', 'F11', 'M5', 'M6', 'M9', 'M12', 'H6', 'H12', 'B12', 'A1'}
# erros claros da antiga (quase preto onde a conta é verde ou marrom escuro): valor pelo cartão (tinta, que não sofre o véu) e pelo recorte da bandeja
MANUAL = {'B11': '#50785F', 'B15': '#2D6A5F', 'G8': '#4A2E2C'}
h2 = lambda h: np.array([int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
hx = lambda t: '#%02X%02X%02X' % tuple(int(round(min(255, max(0, v)))) for v in t)


def lab(rgb):
    return cv2.cvtColor(np.uint8([[np.clip(rgb, 0, 255)]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float) * np.array([100 / 255.0, 1, 1]) - np.array([0, 128, 128])


def de(a, b):
    return float(np.ravel(r5._de2000(lab(a), np.array([lab(b)])))[0])


def window_color(rgb, c, lo, hi, rad=40):
    MB.LO, MB.HI = lo, hi
    return MB.bead_color(rgb, c, rad)


new = {}
for n in range(1, 6):
    rgb = np.array(Image.open(os.path.join(ROOT, 'paleta 120', 'foto-contas-%d.jpg' % n)).convert('RGB'))
    paper = MB.paper_rgb(rgb, MB.PAPER[n]); gain = paper.mean() / paper
    for code, c in zip(MB.CARDS[n].split(), MB.centers(n)):
        lit = np.clip(window_color(rgb, c, 40, 85) * gain, 0, 255)
        if lab(lit)[0] < 50:                                               # compensa o reflexo da tampa nas escuras
            dark = np.clip(window_color(rgb, c, 20, 55) * gain, 0, 255)
            lit = 0.65 * lit + 0.35 * dark
        new[code] = lit

cand = []; changed = []
for c in OLD['colors']:
    code = c['code']; o = h2(c['hex']); nw = new[code]
    dE = de(nw, o)
    Lc = lab(nw)
    import colorsys
    hue = colorsys.rgb_to_hsv(*(np.clip(nw, 0, 255) / 255.0))[0] * 360
    # só cor viva ou média E de matiz amarelo, verde, ciano ou azul (40-255 graus): vermelho, rosa, laranja e roxo saem PUXADOS PARA O ROSA pelo reflexo frio da tampa (o boné do Mario ficava rosa)
    vivid = (np.hypot(Lc[1], Lc[2]) >= 32 and 45 <= Lc[0] <= 90 and 40 <= hue <= 255)
    if code in MANUAL: nw = h2(MANUAL[code]); dE = de(nw, o)
    elif code in KEEP or code in SKIN or code in EARTH or dE <= 5.0 or not vivid:
        cand.append(dict(c)); continue
    d = dict(c); d['hex'] = hx(nw); d['est'] = True
    cand.append(d); changed.append((code, c['hex'], d['hex'], dE))
# nomes novos só nas que mudam (a antiga fica com o nome que tinha)
seen = {c['name'] for c in cand if c['code'] not in {x[0] for x in changed}}
for d in cand:
    if d['code'] in {x[0] for x in changed}:
        nm = MP.name_of(d['hex'])
        if nm in seen: nm = '%s (%s)' % (nm, d['code'])
        seen.add(nm); d['name'] = nm
json.dump({'fonte': 'candidata: cores medidas nas fotos das contas (paleta 120/foto-contas-N.jpg, 2026-11-02); só muda onde a conta destoa da antiga por mais de 5 ΔE; cinzas e H1/H2 ficam', 'colors': cand},
          open(os.path.join(HERE, 'data', 'palette_contas_candidata.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('mudam %d de 120 (ficam %d: cinzas/transparente e as que a conta confirma)' % (len(changed), 120 - len(changed)))
for code, a, b, dE in sorted(changed, key=lambda x: (x[0][0], int(x[0][1:]))): print('  %-4s %s -> %s   ΔE %.1f   %s -> %s' % (code, a, b, dE, OLDC[code]['name'], next(d['name'] for d in cand if d['code'] == code)))

# folha antiga x candidata (120 tiles)
cw = 54
sheet = Image.new('RGB', (24 * (cw + 4) + 8, 5 * (cw + 30) + 8), (250, 250, 250)); dr = ImageDraw.Draw(sheet)
for i, (o, d) in enumerate(zip(OLD['colors'], cand)):
    X = 8 + (i % 24) * (cw + 4); Y = 8 + (i // 24) * (cw + 30)
    dr.rectangle([X, Y, X + cw, Y + cw // 2 - 1], fill=tuple(int(v) for v in h2(o['hex']))); dr.rectangle([X, Y + cw // 2, X + cw, Y + cw], fill=tuple(int(v) for v in h2(d['hex'])))
    dr.text((X, Y + cw + 4), o['code'], fill=(0, 0, 0))
    if o['hex'] != d['hex']: dr.text((X, Y + cw + 15), 'novo', fill=(180, 0, 0))
sheet.save(os.path.join(OUT, 'palette_contas_trocas.png'))

# moldes do catálogo com as duas paletas (rosto, pele e cores vivas)
items = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
want = ['Pikachu sentado', 'Tanjiro Kamado', 'Naruto Uzumaki (chibi', 'Sakura', 'Izuku Midoriya', 'Monkey D. Luffy', 'Mario', 'Hello Kitty', 'Rem', 'Gojo', 'Goku (chibi', 'Harry Potter', 'Stitch', 'Bob Esponja', 'Homem-Aranha', 'Kirby']
pick = []
for w in want:
    m = [it for it in items if it['name'].lower().startswith(w.lower()) or w.lower() in it['name'].lower()]
    m = [it for it in m if len(it['rows'][0]) <= 50 and len(it['rows']) <= 50]
    if m: pick.append(m[0])
pick = pick[:12]
L_old = {c['letter']: h2(c['hex']) for c in OLD['colors']}; L_new = {d['letter']: h2(d['hex']) for d in cand}
S = 6
def draw(rows, pal):
    im = Image.new('RGB', (len(rows[0]) * S, len(rows) * S), (255, 255, 255)); d = ImageDraw.Draw(im)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.': d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=tuple(int(v) for v in pal[ch]))
    return im
ims = [(it['name'], draw(it['rows'], L_old), draw(it['rows'], L_new)) for it in pick]
cols = 3; cellw = max(max(a.size[0] for _, a, _ in ims) * 2 + 24, 200); cellh = max(a.size[1] for _, a, _ in ims) + 22
sh = Image.new('RGB', (cols * cellw, ((len(ims) + cols - 1) // cols) * cellh), (240, 240, 240)); dd = ImageDraw.Draw(sh)
for i, (nm, a, b) in enumerate(ims):
    X = (i % cols) * cellw; Y = (i // cols) * cellh
    sh.paste(a, (X + 4, Y + 18)); sh.paste(b, (X + 4 + a.size[0] + 12, Y + 18)); dd.text((X + 4, Y + 3), nm[:34] + '   (antiga | candidata)', fill=(0, 0, 0))
sh.save(os.path.join(OUT, 'palette_contas_moldes.png'))
print('folhas: tools/out/palette_contas_trocas.png e palette_contas_moldes.png (%d moldes)' % len(ims))
if '--apply' in sys.argv and '--force' not in sys.argv:
    print('OBSOLETO (2026-11-02): a paleta das contas SEM tampa (build_bead_palette2.py) substituiu esta, que só trocava 26 cores. --apply só roda com --force.')
elif '--apply' in sys.argv:
    bk = os.path.join(HERE, 'backups', 'palette-pre-contas.json')
    if not os.path.exists(bk): shutil.copy(os.path.join(HERE, 'data', 'palette.json'), bk)
    json.dump({'fonte': 'cores medidas nas fotos das contas (2026-11-02); ver CLAUDE.md §7.38', 'colors': cand}, open(os.path.join(HERE, 'data', 'palette.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('palette.json gravado (cópia antes em', bk, '); rode python tools/sync_palette_to_app.py')
