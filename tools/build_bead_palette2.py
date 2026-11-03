"""Monta a paleta CANDIDATA a partir das fotos das contas SEM TAMPA (tools/measure_beads2.py -> tools/data/beads_measured2.json) e a compara com a antiga em moldes do catálogo. NÃO altera palette.json nem o app sem --apply.
Contexto (CLAUDE.md §7.38): a paleta da CARTELA foi reprovada (tinta impressa não é a cor da conta: rosto bege virou cinza); a 1ª leva de fotos das bandejas (tampa fechada) saiu com véu azul e só serviu para 26 cores;
as fotos SEM TAMPA mostram as contas como são, então a cor de cada compartimento vale para o código impresso na cartela.
uso:  python tools/build_bead_palette2.py [--apply]
Regras:
  1. cor = a medida na foto (mediana da faixa de luminância 50-85% da janela central do compartimento), SEM balanço de branco (a foto de celular já vem equilibrada; os cinzas saem com ~8 de desvio no verde/azul, dentro do erro);
  2. ficam como estavam: H1 (transparente), H2 (branco, #FFFFFF), H3, H4, H5 e H7 (cinzas e preto do kit antigo: neutros que a foto desvia um pouco para o ciano) e os NOMES dessas;
  3. nome novo (rótulo a partir do hex) para as demais; est=True (aparecem com ~ em Ajustar cores);
  4. cor medida com canal estourado (0 ou 255) é a cor real da conta saturada pelo celular: fica como medida.
Grava tools/data/palette_contas2_candidata.json, tools/out/palette_contas2_trocas.png (antiga x candidata) e tools/out/palette_contas2_moldes.png (moldes com as duas). Com --apply grava em palette.json (cópia em tools/backups/palette-pre-contas2.json)."""
import os, sys, json, shutil, colorsys
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import r5, make_palette as MP, tplfile
OUT = os.path.join(HERE, 'out')
AD = json.load(open(os.path.join(HERE, 'backups', 'palette-pre-contas.json'), encoding='utf-8'))      # a paleta estimada da foto do anúncio (antes de qualquer ajuste de 2026-11-02)
ADC = {c['code']: c for c in AD['colors']}
CUR = {c['code']: c for c in json.load(open(os.path.join(HERE, 'data', 'palette.json'), encoding='utf-8'))['colors']}
MEAS = json.load(open(os.path.join(HERE, 'data', 'beads_measured2.json'), encoding='utf-8'))
KEEP = {'H1', 'H2', 'H3', 'H4', 'H5', 'H7'}
ALIAS = {'H12': 'A1'}       # conta que na prática é outra (o H12 é o mesmo creme da A1; CLAUDE.md 7.43): o campo `alias` do palette.json tem que sobreviver à regravação
h2 = lambda h: np.array([int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
hx = lambda t: '#%02X%02X%02X' % tuple(int(round(min(255, max(0, v)))) for v in t)


def lab(rgb):
    return cv2.cvtColor(np.uint8([[np.clip(rgb, 0, 255)]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float) * np.array([100 / 255.0, 1, 1]) - np.array([0, 128, 128])


def de(a, b):
    return float(np.ravel(r5._de2000(lab(a), np.array([lab(b)])))[0])


def name2(hexc):
    """rótulo em português a partir do hex (make_palette.name_of com o ciano separado do verde-água); o código é o que vale"""
    r, g, b = [v / 255 for v in h2(hexc)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b); h *= 360
    L, a_, b_ = lab(h2(hexc)); C = (a_ ** 2 + b_ ** 2) ** .5
    if 182 <= h < 206 and s >= 0.25 and L >= 50 and not (h >= 203 and L >= 78): return 'Ciano claro' if L >= 78 else 'Ciano'
    if 325 <= h < 352 and s >= 0.45 and 45 <= L < 75: return 'Rosa choque'                      # E6, F9: o name_of os chamava de Vermelho
    if (h >= 350 or h < 20) and s >= 0.45 and 55 <= L < 72: return 'Coral'                      # F2, F3, F12
    if 158 <= h < 182 and s >= 0.45 and L >= 50 and L < 85: return 'Turquesa'
    if 44 <= h < 70 and s >= 0.7 and L >= 70: return 'Amarelo'                  # o name_of chamava de "Amarelo claro" o amarelo vivo
    if L < 28 and C > 40 and 235 <= h < 300: return 'Azul-marinho'               # D15: azul profundo, não é preto
    return MP.name_of(hexc)


meas = {}
for n, lst in MEAS.items():
    for it in lst: meas[it['code']] = np.array(it['rgb'], float)
cand = []; changed = []
for c in AD['colors']:
    code = c['code']; o = h2(c['hex'])
    if code in KEEP or code not in meas:
        d = dict(c)
        if code == 'H1': d['name'] = CUR['H1']['name']                    # "Transparente (H1)"
        cand.append(d); continue
    nw = meas[code]; d = dict(c); d['hex'] = hx(nw); d['est'] = True
    cand.append(d); changed.append((code, c['hex'], d['hex'], de(nw, o)))
seen = {d['name'] for d in cand if d['code'] in KEEP}
for d in cand:
    if d['code'] in KEEP: continue
    nm = name2(d['hex'])
    if nm in seen: nm = '%s (%s)' % (nm, d['code'])
    seen.add(nm); d['name'] = nm
for d in cand:
    if d['code'] in ALIAS: d['alias'] = ALIAS[d['code']]
json.dump({'fonte': 'candidata: cores medidas nas fotos das contas SEM TAMPA (paleta 120/foto-contas-sem-tampa-N.jpg, 2026-11-02); H1, H2, H3, H4, H5 e H7 do kit antigo ficam', 'colors': cand},
          open(os.path.join(HERE, 'data', 'palette_contas2_candidata.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('mudam %d de 120 (ficam %d: H1 H2 H3 H4 H5 H7)' % (len(changed), 120 - len(changed)))
des = [x[3] for x in changed]
print('ΔE medida x antiga(ad): média %.1f, mediana %.1f, máx %.1f' % (np.mean(des), np.median(des), max(des)))
if '--list' in sys.argv:
    for code, a, b, dE in sorted(changed, key=lambda x: (x[0][0], int(x[0][1:]))): print('  %-4s %s -> %s   ΔE %.1f   %s -> %s' % (code, a, b, dE, ADC[code]['name'], next(d['name'] for d in cand if d['code'] == code)))

# folha antiga x candidata (120 tiles)
cw = 54
sheet = Image.new('RGB', (24 * (cw + 4) + 8, 5 * (cw + 30) + 8), (250, 250, 250)); dr = ImageDraw.Draw(sheet)
for i, (o, d) in enumerate(zip(AD['colors'], cand)):
    X = 8 + (i % 24) * (cw + 4); Y = 8 + (i // 24) * (cw + 30)
    dr.rectangle([X, Y, X + cw, Y + cw // 2 - 1], fill=tuple(int(v) for v in h2(o['hex']))); dr.rectangle([X, Y + cw // 2, X + cw, Y + cw], fill=tuple(int(v) for v in h2(d['hex'])))
    dr.text((X, Y + cw + 4), o['code'], fill=(0, 0, 0))
    if o['hex'] != d['hex']: dr.text((X, Y + cw + 15), 'novo', fill=(180, 0, 0))
sheet.save(os.path.join(OUT, 'palette_contas2_trocas.png'))

# moldes do catálogo com as duas paletas (rosto, pele e cores vivas)
items = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']
want = ['Pikachu sentado', 'Tanjiro Kamado', 'Naruto Uzumaki (chibi', 'Sakura', 'Izuku Midoriya', 'Monkey D. Luffy', 'Mario', 'Hello Kitty', 'Rem', 'Gojo', 'Goku (chibi', 'Harry Potter', 'Stitch', 'Bob Esponja', 'Homem-Aranha', 'Kirby']
pick = []
for w in want:
    m = [it for it in items if it['name'].lower().startswith(w.lower()) or w.lower() in it['name'].lower()]
    m = [it for it in m if len(it['rows'][0]) <= 50 and len(it['rows']) <= 50]
    if m: pick.append(m[0])
pick = pick[:12]
L_old = {c['letter']: h2(c['hex']) for c in AD['colors']}; L_new = {d['letter']: h2(d['hex']) for d in cand}
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
sh.save(os.path.join(OUT, 'palette_contas2_moldes.png'))
print('folhas: tools/out/palette_contas2_trocas.png e palette_contas2_moldes.png (%d moldes)' % len(ims))
if '--apply' in sys.argv:
    bk = os.path.join(HERE, 'backups', 'palette-pre-contas2.json')
    if not os.path.exists(bk): shutil.copy(os.path.join(HERE, 'data', 'palette.json'), bk)
    json.dump({'fonte': 'cores medidas nas fotos das contas SEM TAMPA (2026-11-02); ver CLAUDE.md §7.38', 'colors': cand}, open(os.path.join(HERE, 'data', 'palette.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('palette.json gravado (cópia antes em', bk, '); rode python tools/sync_palette_to_app.py')
