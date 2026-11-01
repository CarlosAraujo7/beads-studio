"""Remessa 17 (72 imagens, TODAS ilustrações/artes SEM grade: chibis, retratos, adesivos, emblemas). Rode: BEADPAL=120 python tools/r17_exfinal.py [filtro...]
  -> data/final19_120.json        versões de 1 PLACA (<= 50x50) de TUDO que foi convertido (pedido do usuário: "sempre faça uma versão de uma única placa")
  -> data/final19_multi_120.json  irmãos "(grande)" de 2-4 placas ({"plates": N}) das artes detalhadas (a alocação em mais placas vale a partir desta remessa)

Conversão por illus.convert4 (aproximada; ver §7.6 do CLAUDE.md).
"""
import os, sys, json, glob
os.environ['REMNUM'] = '17'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, outline as O, illus
from flat import render_flat
from palette import sfx
FILES = sorted(glob.glob(os.path.join(os.path.dirname(SP), 'remessas', 'remessa 17', '*.*')))
DK = dict(dark_frac=0.28, dark_L=28.0)
DKM = dict(dark_frac=0.26, dark_L=28.0, ncolors=20)


def plates_of(rows): return -(-max(len(r) for r in rows) // 50) * -(-len(rows) // 50)


def drop_small(maxsz, frac=0.85):
    """apaga pedacinhos soltos (<= maxsz contas) nos últimos (1-frac) das linhas: assinaturas/marcas d'água do artista"""
    import numpy as np, cv2
    def f(rows):
        h = len(rows); m = np.array([[ch != '.' for ch in r] for r in rows], np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        out = [list(r) for r in rows]
        for i in range(1, n):
            x, y, w, hh, a = st[i]
            if a <= maxsz and y >= frac * h:
                for yy in range(y, y + hh):
                    for xx in range(x, x + w):
                        if lab[yy, xx] == i: out[yy][xx] = '.'
        return O.trim([''.join(r) for r in out])
    return f


def clear_box(x0, x1, y0, y1):
    """apaga um retângulo (x0..x1, y0..y1 inclusivos, coordenadas do molde já cortado): assinatura do artista"""
    def f(rows):
        return O.trim([''.join('.' if x0 <= x <= x1 and y0 <= y <= y1 else ch for x, ch in enumerate(r)) if y0 <= y <= y1 else r for y, r in enumerate(rows)])
    return f


def grayfy(rows):
    """cores de croma baixo (o cinza do metal com tom lilás da foto) viram só os cinzas H1-H7"""
    from palette import ALL
    import colorsys
    gray = {c['letter']: c for c in ALL if c['code'] in ('H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7')}
    def lum(c): r, g, b = [int(c['hex'][i:i + 2], 16) for i in (1, 3, 5)]; return 0.299 * r + 0.587 * g + 0.114 * b
    mp = {}
    for c in ALL:
        r, g, b = [int(c['hex'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
        h_, s_, v_ = colorsys.rgb_to_hsv(r, g, b)
        if c['letter'] not in gray and s_ < 0.16 and v_ > 0.25:
            mp[c['letter']] = min(gray.values(), key=lambda gc: abs(lum(gc) - lum(c)))['letter']
    return [''.join(mp.get(ch, ch) for ch in r) for r in rows]


def conv(idx, plates=None, largest=False, post=None, **kw):
    a = dict(DKM if plates else DK); a.update(kw)
    r = illus.convert4(FILES[idx], plates=plates, **a)
    if largest: r = r5.largest(r)
    return post(r) if post else r


# DEIXADA DE FORA: idx 2 (Senku chibi: MD5 igual ao da remessa 13)
# (nome, série, imagem, kwargs da conversão, placas do irmão "(grande)" ou None[, kwargs só do irmão grande])
CFG = [
 # --- Meninas Superpoderosas
 ('Florzinha (Meninas Superpoderosas)', 'Meninas Superpoderosas', 6, {}, None),
 ('Docinho (Meninas Superpoderosas, ilustração)', 'Meninas Superpoderosas', 52, {}, None),
 ('Lindinha (Meninas Superpoderosas, ilustração)', 'Meninas Superpoderosas', 58, {}, None),
 ('Macaco Louco (Mojo Jojo)', 'Meninas Superpoderosas', 60, {}, None),
 ('Meninas Superpoderosas (trio)', 'Meninas Superpoderosas', 20, {}, None),
 # --- Jovens Titãs
 ('Robin (Jovens Titãs, apontando)', 'Jovens Titãs', 11, {}, None),
 ('Robin (Jovens Titãs, em pé)', 'Jovens Titãs', 57, dict(thr=190, dark_frac=0.5), None),
 ('Ravena (capuz roxo, ilustração)', 'Jovens Titãs', 38, dict(box=(150, 0, 400, 400), sat=1.0), None),
 ('Mutano (Jovens Titãs)', 'Jovens Titãs', 65, dict(bg='flat', tol=140), None),
 # --- Hunter x Hunter
 ('Kurapika (retrato, Hunter x Hunter)', 'Hunter x Hunter', 1, {}, 4),
 ('Kurapika (chibi, espadas de madeira)', 'Hunter x Hunter', 50, {}, None),
 ('Killua Zoldyck (chibi)', 'Hunter x Hunter', 10, dict(pale_skin=True), None),
 ('Neferpitou (Hunter x Hunter, adesivo)', 'Hunter x Hunter', 19, dict(bg='flat', tol=45, pale_skin=True, peel=1.0), 4),
 ('Gon Freecss (silhueta preta e branca)', 'Hunter x Hunter', 61, dict(seal=1.0), None),
 ('Gon Freecss (adesivo)', 'Hunter x Hunter', 66, {}, 4),
 # --- Dr. Stone
 ('Senku Ishigami (chibi, bravo)', 'Dr. Stone', 18, {}, None),
 ('Senku Ishigami (adesivo, soco)', 'Dr. Stone', 16, {}, 4),
 ('Senku Ishigami (adesivo, com frasco)', 'Dr. Stone', 46, {}, 4),
 # --- Fullmetal Alchemist
 ('Alphonse Elric (Fullmetal Alchemist)', 'Fullmetal Alchemist', 4, {}, 2),
 ('Roy Mustang (chibi)', 'Fullmetal Alchemist', 21, {}, 4),
 # --- Resident Evil / The Last of Us / Red Dead Redemption
 ('Leon S. Kennedy (arte em preto e branco)', 'Resident Evil', 5, dict(seal=1.0), 4),
 ('Joel (The Last of Us, retrato em tinta)', 'The Last of Us', 23, dict(seal=1.0), 4),
 ('Ellie (The Last of Us, retrato em tinta)', 'The Last of Us', 35, dict(seal=1.0), 4),
 ('Símbolo dos Vagalumes (The Last of Us)', 'The Last of Us', 45, {}, None),
 ('Arthur Morgan (Red Dead Redemption, ilustração)', 'Red Dead Redemption', 49, {}, 4),
 ('Arthur Morgan (chibi, fogueira)', 'Red Dead Redemption', 71, {}, None),
 # --- Skyrim
 ('Capacete de Skyrim com flecha (adesivo)', 'Skyrim', 24, dict(bg='flat', tol=40), None),
 ('Símbolo de Skyrim (preto e branco)', 'Skyrim', 25, dict(seal=1.0), None),
 ('Pôster de Skyrim (Dovahkiin e dragão)', 'Skyrim', 41, dict(bg='flat', tol=40, dark_frac=0.6, dark_L=15.0), 4),
 ('Símbolo de Skyrim (metal, fundo preto)', 'Skyrim', 43, dict(bg='flat', tol=12, dark_L=10.0, dark_frac=0.9, contrast=1.8, seal=1.0), None),
 # --- Doctor Who
 ('Doctor Who (chibi e TARDIS)', 'Doctor Who', 13, {}, 4),
 ('Dalek (Doctor Who)', 'Doctor Who', 30, {}, None),
 # --- Star Wars
 ('Darth Vader (chibi, ilustração)', 'Star Wars', 28, {}, None),
 ('Chewbacca (chibi)', 'Star Wars', 17, {}, None),
 ('Stormtrooper (ilustração)', 'Star Wars', 47, {}, 4),
 # --- O Senhor dos Anéis
 ('Legolas (chibi)', 'O Senhor dos Anéis', 48, {}, 4),
 ('Gollum (O Senhor dos Anéis)', 'O Senhor dos Anéis', 32, dict(bg='flat', tol=40), None),
 ('Gandalf (adesivo)', 'O Senhor dos Anéis', 69, dict(bg='flat', tol=45, peel=1.0), 4),
 ('Hobbit (chibi, com trouxa)', 'O Senhor dos Anéis', 7, {}, None),
 # --- Percy Jackson
 ('Percy Jackson (pintura, coroa de louros)', 'Percy Jackson', 14, dict(bg='none'), 4),
 ('Percy Jackson (pintura, jaqueta)', 'Percy Jackson', 68, dict(bg='none'), 4),
 ('Percy Jackson (foto, com espada)', 'Percy Jackson', 63, {}, None),
 ('Acampamento Meio-Sangue (Percy Jackson)', 'Percy Jackson', 56, {}, None),
 # --- Phineas e Ferb
 ('Perry, o Ornitorrinco (ilustração)', 'Phineas e Ferb', 15, {}, None),
 ('Perry, o Ornitorrinco (ilustração, pose 2)', 'Phineas e Ferb', 39, {}, None),
 # --- Power Rangers
 ('Alpha 5 (Power Rangers)', 'Power Rangers', 33, dict(post=drop_small(20, 0.85), seal=1.0), None),
 ('Power Ranger branco (retrato)', 'Power Rangers', 37, dict(bg='none'), 4),
 ('Power Ranger branco (chibi, espada)', 'Power Rangers', 53, {}, 4),
 ('Power Ranger verde (chibi)', 'Power Rangers', 67, {}, 4),
 # --- Soul Eater
 ('Lorde Shinigami (Soul Eater)', 'Soul Eater', 42, {}, None),
 ('Sol (Soul Eater)', 'Soul Eater', 64, dict(box=(0, 0, 1152, 1040)), None),
 ('Lua (Soul Eater)', 'Soul Eater', 64, dict(box=(0, 1040, 1152, 2048)), None),
 # --- Hora de Aventura / Tartarugas Ninja / Egito / Frieren / Re:Zero
 ('Gunter (Hora de Aventura)', 'Hora de Aventura', 36, {}, None),
 ('Lady Rainicorn (Hora de Aventura)', 'Hora de Aventura', 62, {}, 2),
 ('Leonardo (Tartarugas Ninja)', 'Tartarugas Ninja', 70, {}, 4),
 ('Esfinge (Egito Antigo)', 'Egito Antigo', 9, {}, None),
 ('Pirâmide (Egito Antigo, tijolos)', 'Egito Antigo', 54, dict(thr=190), None),
 ('Pirâmide (Egito Antigo, vetor)', 'Egito Antigo', 55, {}, None),
 ('Frieren (chibi, chorando)', 'Frieren', 22, dict(pale_skin=True), None),
 ('Himmel (Frieren, chibi)', 'Frieren', 51, dict(pale_skin=True), 4),
 ('Rem (chibi, mãos na cabeça)', 'Re:Zero', 34, dict(pale_skin=True), 4),
 # --- sem franquia identificada
 ('Herói de armadura vermelha e dourada (chibi)', 'Outros', 0, dict(post=drop_small(40, 0.9)), 4),
 ('Herói de armadura vermelha e branca (chibi)', 'Outros', 3, dict(post=drop_small(20, 0.85)), 4),
 ('Herói de armadura azul e dourada (chibi)', 'Outros', 8, dict(largest=True), 4),
 ('Herói de armadura azul e dourada com espada (chibi)', 'Outros', 27, {}, 4),
 ('Herói de armadura azul e dourada com bola', 'Outros', 31, {}, 4),
 ('Adaga com bandagem e dentes (arte de tatuagem)', 'Outros', 12, {}, 2),
 ('Olhos e dentes (arte de tatuagem)', 'Outros', 29, {}, 2),
 ('Emblema de máscara vermelha em chama roxa', 'Outros', 40, {}, None),
 ('Gato cinza com bolsa roxa', 'Outros', 26, {}, None),
 ('Chibi de cabelo loiro e olhos pretos grandes', 'Outros', 44, {}, None),
 ('Chibi de óculos escuros com guitarra', 'Outros', 59, {}, None),
]

if __name__ == '__main__':
    only = sys.argv[1:]
    one = []; big = []; items = []; items_big = []
    for n, g, idx, kw, pl, *kwb in CFG:
        if only and not any(o in n for o in only): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = conv(idx, **illus.style_defaults(n, kw)); one.append((n, g, r))
            items.append((f'{n[:24]} {idx} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
            if pl:
                rb = conv(idx, plates=pl, **illus.style_defaults(n, (kwb[0] if kwb else kw), big=True)); big.append((f'{n} (grande)', g, rb, {'plates': plates_of(rb)}))
                items_big.append((f'{n[:24]} {idx} {len(rb[0])}x{len(rb)}'.encode('ascii', 'replace').decode(), rb))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa;', len(big), 'irmãos grandes:', [(n[:20], len(r[0]), len(r), o['plates']) for n, g, r, o in big])
    if not only:
        json.dump(one, open(os.path.join(SP, 'data', 'final19' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(big, open(os.path.join(SP, 'data', 'final19_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'r17_x_{k // 12}' + sfx() + '.png'), scale=8, W=1900)
    for k in range(0, len(items_big), 8):
        render_flat(items_big[k:k + 8], os.path.join(OUT, f'r17_big_{k // 8}' + sfx() + '.png'), scale=6, W=1900)
