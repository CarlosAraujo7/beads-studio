"""DESATIVADO em 2026-10-31: o usuário pediu para excluir a aba "Sem bordas pretas" ("não vou usar"). Não rode nem recrie as cópias. Fica só como histórico (CLAUDE.md §7.25)."""
raise SystemExit("DESATIVADO: a aba Sem bordas pretas foi excluida a pedido do usuario.")
"""Aba "Sem bordas pretas" (pedido do usuário, 2026-10-31; CLAUDE.md §7.25): cópia sem o contorno preto SÓ dos moldes de 1 placa em que o preto é claramente só contorno (como a Sandy do Bob Esponja).
A cópia é um molde normal do catálogo: id "sem-borda-<id>", nome "<nome> (sem bordas)"; o app a põe na aba pelo prefixo do id, então editar, excluir, mover e "Gravar no catálogo" funcionam.
  python tools/sem_bordas.py --report     separa claros e não claros: folhas tools/out/sbk_*.png e sbr_*.png (antes | depois, fundo cinza); não grava
  python tools/sem_bordas.py --apply      deixa no catálogo só as cópias dos claros: acrescenta as que faltam, apaga as outras (cópia que ele editou fica); nunca mexe no original nem recria o que ele excluiu
Quem é claro: `clear_border` mede (traço preto contínuo em volta da figura, pouco preto por dentro, cores limpas); INCLUDE/EXCLUDE (começo do nome) são as decisões tomadas olhando as folhas. Moldes novos: olhe a folha.
Como tira a borda, por molde:
  1. Só é contorno o preto FINO. Massa preta (cabelo, capa, armadura: >= 3 de largura) fica.
  2. Contorno externo (encosta no vazio, com cor logo atrás) sai: a figura perde 1 conta em volta.
  3. Linha interna fina e longa vira um tom mais escuro da cor vizinha. Sobre branco vira cinza claro.
  4. Olhos, bocas, botões e outros pretos pequenos e fechados ficam.
  5. Linha preta sem cor atrás (antena, fio) fica: ela é o desenho."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import cv2
from collections import Counter
import palette as P, illus, loose, tplfile
import outline as O
from tplfile import parse
from PIL import Image, ImageDraw

OUT = os.path.join(HERE, 'out')
PREFIX = 'sem-borda-'; SUF = ' (sem bordas)'
LAB = {c['letter']: illus._lab(np.array([int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)) for c in P.ALL}
HEX = {c['letter']: tuple(int(c['hex'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) for c in P.ALL}
DARK = {l for l, v in LAB.items() if v[0] < 24 and (v[1] ** 2 + v[2] ** 2) ** .5 < 16}       # preto de verdade: H7, G8, B15, F7...
SMALL = 16                                                                                 # preto fechado até este tamanho é detalhe (olho, boca, botão)
_shade = {}


def shade(l):
    """tom mais escuro da mesma cor no kit: 16-26 de L abaixo, mesmo matiz; nunca preto"""
    if l in _shade: return _shade[l]
    v = LAB[l]; best = None; bd = 1e9
    if v[0] < 36: _shade[l] = l; return l                                   # vizinha já escura (cinza-chumbo, marrom-escuro): a linha fica da cor dela
    neutral = float(np.hypot(v[1], v[2])) < 8
    for m, u in LAB.items():
        if m == l or m in DARK: continue
        if neutral and float(np.hypot(u[1], u[2])) >= 8: continue           # cinza escurece para cinza, nunca para marrom
        dL = v[0] - u[0]
        if not 10 <= dL <= 30: continue
        d = abs(dL - 18) * 0.6 + float(np.hypot(u[1] - v[1], u[2] - v[2]))
        if d < bd: bd, best = d, m
    _shade[l] = best or l
    return _shade[l]


def convert(rows):
    """devolve (linhas, dados da análise)"""
    H, W = len(rows), len(rows[0]); a = np.array([list(r) for r in rows])
    dark = np.isin(a, list(DARK)); empty = a == '.'; color = ~dark & ~empty
    info = dict(dark=int(dark.sum()), beads=int((~empty).sum()), border=0, removed=0, recolored=0)
    if not dark.any(): return list(rows), info
    k3 = np.ones((3, 3), np.uint8)
    mass = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, k3).astype(bool)                       # preto com 3+ de largura
    # olho/pupila de 2+ contas, mesmo ligado ao contorno: mancha pequena e compacta no miolo da figura também é massa
    op2 = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    nb, lb, stb, _ = cv2.connectedComponentsWithStats(op2, connectivity=4)
    pad0 = np.pad(empty, 1, constant_values=True)
    n40 = pad0[:-2, 1:-1] | pad0[2:, 1:-1] | pad0[1:-1, :-2] | pad0[1:-1, 2:]
    for i in range(1, nb):
        bw, bh, ar = int(stb[i][2]), int(stb[i][3]), int(stb[i][4])
        if ar <= SMALL and max(bw, bh) <= 5 and not ((lb == i) & n40).any(): mass |= lb == i
    thin = dark & ~mass
    costume = dark.sum() / float(max(1, (~empty).sum())) > 0.30                                           # roupa/corpo preto (Spawn, Venom): só o contorno de fora sai; o preto de dentro é o desenho
    pad = np.pad(empty, 1, constant_values=True)
    n4 = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]                                   # encosta no vazio/fora
    dil = lambda m, it=1: cv2.dilate(m.astype(np.uint8), k3, iterations=it).astype(bool)
    near_color = dil(color, 2)                                                                            # cor a até 2 contas
    # peças pretas finas
    n, lab, st, _ = cv2.connectedComponentsWithStats(thin.astype(np.uint8), connectivity=8)
    out = a.copy()
    for i in range(1, n):
        m = lab == i; sz = int(st[i][4])
        touches_out = (m & n4).any()
        if not touches_out and sz <= SMALL and not (dil(m) & mass).any(): continue                         # olho, boca, botão: detalhe solto no meio da cor
        if not touches_out and sz <= 5: continue                                                          # traço curto ligado a massa (cílio, sobrancelha)
        if not (m & near_color).any(): continue                                                           # fio preto sem cor por perto: é o desenho
        ys, xs = np.nonzero(m)
        for y, x in zip(ys, xs):
            if not near_color[y, x]: continue
            nb = a[max(0, y - 1):y + 2, max(0, x - 1):x + 2]
            if n4[y, x] and (color[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any() or sz > 2):
                out[y, x] = '.'; info['removed'] += 1; continue                                           # contorno externo
            if costume: continue
            cols = [c for c in nb.flat if c != '.' and c not in DARK]
            if not cols:
                nb2 = a[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
                cols = [c for c in nb2.flat if c != '.' and c not in DARK]
            if not cols: continue
            out[y, x] = shade(Counter(cols).most_common(1)[0][0]); info['recolored'] += 1                  # linha interna
    r = [''.join(l) for l in out]
    # a 1ª passada pode deixar um segundo anel preto (contorno de 2 contas): mais uma vez só sobre o que sobrou fino
    return r, info


def finish(rows, was):
    if not any(c != '.' for l in rows for c in l): return was
    rows = loose.fix_loose(rows)                                            # também liga peças grandes que se tocam só na diagonal
    return O.trim(rows)


def has_border(rows):
    a = np.array([list(r) for r in rows]); empty = a == '.'
    pad = np.pad(empty, 1, constant_values=True)
    n4 = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    edge = ~empty & n4
    return float(np.isin(a[edge], list(DARK)).mean()) if edge.any() else 0.0


# decisões olhando as folhas: começo do nome do original
INCLUDE = ['Armadura de diamante', 'Merida', 'Ban (', 'Hellboy', 'Sakura Haruno', 'Goku Instinto Superior (pixel', 'Esfera do Dragão de 4', 'Charmander (versão 2', 'Vash the Stampede (chibi', 'Kurama', 'Hulkbuster (Marvel, pixel', 'Capitão América (chibi, fot', 'Bepo', 'Ursinho Pooh com pote', 'Hello Kitty zumbi', 'Nami (One Piece, gr', 'Frieren (chibi', 'Sansão', 'Heatblast', 'Meliodas com espada', 'Radar do Dragão', 'Franky', 'Jinbe', 'Shenlong', 'Darkness', 'Coraline', 'Bisonho', 'Cetro', 'Chopper', 'Taco', 'Hange', 'Kento Nanami (Jujutsu Kaisen, chibi, sentado', 'Perry', 'Vegeta Super Saiyajin Blue', 'Hagrid', 'Saitama', 'All Might (forma magra', 'Psyduck', 'Brook', 'Kazuma Kuwabara (Yu Yu Hakusho, espada', 'Majin Boo', 'Bulbasaur', 'Shadow', 'Link (com escudo', 'Link (Zelda, chibi', 'Lula (chibi', 'Lula de chapéu', 'Vaporeon', 'TARDIS', 'Pipoca', 'Luffy (One Piece, gr', 'Hawks (My Hero Academia, pixel', 'Pikachu surpreso', 'Bidu', 'Zoro (pixel', 'Lua (Soul Eater', 'Titã Bestial', 'Titã Colossal (Attack', 'Cachorro marrom', 'Stella', 'Diamondhead', 'Jolteon', 'Squirtle', 'Bloom', 'Naruto (chibi', 'Red (Pokémon', 'Loid', 'Espeon', 'Bala de canhão', 'Sylveon', 'Bandeira dos Chapéus', 'Patinho de guarda-chuva', 'Lobisomem', 'Sonic (chibi', 'Denji', 'Endeavor (My Hero Academia, rosto', 'Wolverine (Marvel, gr', 'Trafalgar Law', 'Kakashi (chibi', 'Doutor Destino', 'Thousand Sunny (One Piece', 'Loki', 'Eevee na', 'Ash Ketchum', 'Shiryu de Dragão (pixel', 'Dumbledore', 'Seu Barriga', 'Cogumelo do Mario', 'Homem de Ferro (voando', 'Balde de abóbora', 'Usopp', 'Mônica (pulando', 'Leon S. Kennedy', 'Shoto Todoroki (chibi', 'Shinobu', 'Aqua (', 'Shun de Andrômeda (pixel', 'Esfinge', 'Scott Pilgrim', 'Tecna', 'Vi (Arcane', 'Aang (chibi, saltando', 'Ikki de Fênix (pixel', 'Soul (', 'Ivysaur', 'Beatrice (Re:Zero, chibi', 'Sanji (pixel', 'Panda (Kung Fu', 'Seiya de Pégaso (pixel', 'Megumin (pixel', 'Edward Elric', 'Papai Noel', 'Pennywise (chibi, corpo', 'Mirio', 'Astronauta', 'Coala', 'Aquático', 'Bob Esponja', 'Patrick', 'Lula Molusco', 'Gary', 'Sandy', 'Sr. Sirigueijo', 'Superman (chibi', 'Chaves', 'Mario (', 'Zumbi (Plants', 'Kuririn', 'Goku Super Saiyajin (pixel', 'Ash e Pikachu', 'Gato siamês', 'Glaceon', 'Leafeon', 'Hello Kitty', 'Sanji', 'Hulk (chibi', 'Kiko', 'Mônica com', 'Peashooter de gelo', 'Alice', 'Mulher-Maravilha', 'Wolverine', 'Mutano', 'Lindinha', 'Charizard', 'Charmander (', 'Relâmpago McQueen', 'Carro azul', 'Hisuian Zorua', 'Deku', 'Snoopy', 'Visão (Marvel', 'Ursinho Pooh', 'Tigrão', 'Coruja do Duolingo', 'Leitão', 'Gengar', 'Stitch', 'Angel', 'Finn', 'BMO', 'Luffy (chibi grande', 'Piu-Piu', 'Coragem', 'Chikorita', 'Wanda', 'Sapo mago', 'Tubarão fofo', 'Robô fofo', 'Jane', 'Nick Wilde', 'Kazuma (KonoSuba', 'Ayase', 'Doutor Estranho (chibi, pix', 'Rimuru (slime', 'Chapéu Seletor', 'Logo do Superman', 'Minion', 'Groot', 'Tartaruga verde', 'Dinossauro verde', 'Taz', 'Unicórnio', 'Tricerátops azul', 'Chiquinha', 'Emily', 'Raiva', 'Ansiedade', 'Flareon', 'Sininho', 'Snorlax (', 'Snorlax', 'Pikachu (rosto', 'Haku (versão pastel', 'Gato banana', 'Remy', 'Velha turbo', 'Dragão verde-água', 'Crânio de T-rex', 'Akuma no Mi', 'Goku (chibi pixel', 'Galinha (versão', 'Tristeza', 'Dragonite', 'Pikachu de Mewtwo', 'Nojinho', 'Vergonha', 'Tanjiro Kamado', 'Hulk (chibi, foto', 'Percy Jackson (pixel', 'Goku (em pé', 'Goku (pixel, corpo', 'Gon Freecss (pixel']
EXCLUDE = ['Criatura cinza espinhosa', 'Onix', 'Jiraiya', 'Going Merry', 'Olho de Hórus', 'Bakugo', 'Emblema do Sol', 'Chibi de cabelo cinza', 'Kratos (God of War, chibi', 'Kiko (Chaves, ilustr', 'Alphonse Elric com gato', 'Hornet', 'Pernalonga', 'Lucario', 'Umbreon', 'Dovahkiin', 'Casa assombrada', 'Banguela', 'Snorlax de Batman']


def metrics(r0, r):
    """edge: fração da borda da figura que é preta; ring: maior trecho contínuo de contorno preto / toda a borda; left: preto que sobra no resultado;
    noise: contas de cor sem nenhuma vizinha igual (arte com ruído não tem contorno "limpo"); gone: contas tiradas"""
    a = np.array([list(l) for l in r0]); empty = a == '.'; dark = np.isin(a, list(DARK))
    pad = np.pad(empty, 1, constant_values=True)
    n4 = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    edge = ~empty & n4; n_edge = max(1, int(edge.sum()))
    n, lab, st, _ = cv2.connectedComponentsWithStats((edge & dark).astype(np.uint8), connectivity=8)
    ring = (int(st[1:, 4].max()) if n > 1 else 0) / float(n_edge)
    n0 = int((~empty).sum()); n1 = sum(c != '.' for l in r for c in l)
    left = sum(c in DARK for l in r for c in l) / float(max(1, n1))
    H, W = a.shape; lone = tot = 0
    for y in range(H):
        for x in range(W):
            c = a[y, x]
            if c == '.' or c in DARK: continue
            tot += 1
            if not any(0 <= yy < H and 0 <= xx < W and a[yy, xx] == c for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))): lone += 1
    return dict(edge=float((edge & dark).sum()) / n_edge, ring=ring, left=left, dark0=float(dark.sum()) / max(1, n0), gone=1 - n1 / float(max(1, n0)), noise=lone / float(max(1, tot)))


def clear_border(t, r, info):
    """o preto é claramente só contorno: figura cercada por um traço preto contínuo, quase nada preto sobra por dentro, cores limpas e as linhas internas não são o desenho"""
    if t['name'].startswith(tuple(EXCLUDE)): return False
    if t['name'].startswith(tuple(INCLUDE)): return True
    m = metrics(t['rows'], r); b = max(1, info['beads'])
    if not (0.06 <= m['gone'] <= 0.55 and info['recolored'] / float(b) <= 0.22): return False
    if m['ring'] >= 0.85: return m['left'] <= 0.30 and m['noise'] <= 0.20                    # traço preto fechado em volta da figura inteira
    return m['ring'] >= 0.40 and m['edge'] >= 0.85 and m['left'] <= 0.25 and m['noise'] <= 0.10  # fechado, só interrompido por uma ou outra parte (braço colorido, chama)


def build(items, only=None):
    res = []
    for t in items:
        if t['id'].startswith(PREFIX) or max(len(t['rows']), len(t['rows'][0])) > 50: continue
        if only and not any(o.lower() in t['name'].lower() for o in only): continue
        r0 = t['rows']; share = has_border(r0)
        r, info = convert(r0); r = finish(r, r0); info['share'] = share
        res.append((t, r, info))
    return res


def sheet(res, path, sc=5, W=1900):
    tiles = []
    for t, r, info in res:
        a, b = t['rows'], r
        h = max(len(a), len(b)) * sc; w = (len(a[0]) + len(b[0])) * sc + 6
        im = Image.new('RGB', (w, h + 12), (165, 165, 170)); d = ImageDraw.Draw(im)
        for ox, g in ((0, a), (len(a[0]) * sc + 6, b)):
            for y, l in enumerate(g):
                for x, c in enumerate(l):
                    if c != '.': d.rectangle((ox + x * sc, 12 + y * sc, ox + x * sc + sc - 1, 12 + y * sc + sc - 1), fill=HEX[c])
        d.rectangle((0, 0, w, 11), fill=(40, 40, 44)); d.text((1, 0), t['name'][:int(w / 6)].encode('ascii', 'replace').decode(), fill=(255, 255, 0))
        tiles.append(im)
    x = y = 6; rh = 0; pos = []
    for t in tiles:
        if x + t.width + 6 > W: x = 6; y += rh + 6; rh = 0
        pos.append((x, y)); x += t.width + 6; rh = max(rh, t.height)
    S = Image.new('RGB', (W, y + rh + 6), (60, 60, 66))
    for t, p in zip(tiles, pos): S.paste(t, p)
    S.save(path)


def main():
    a = sys.argv[1:]; only = None
    if '--only' in a: only = [x for x in a[a.index('--only') + 1:] if not x.startswith('--')]
    tp = os.path.join(ROOT, 'templates.js'); d = parse(tp)
    res = build(d['items'], only)
    if '--report' in a:
        keep = [x for x in res if clear_border(*x)]; rej = [x for x in res if not clear_border(*x)]
        rej.sort(key=lambda x: -(metrics(x[0]['rows'], x[1])['edge'] - 2 * metrics(x[0]['rows'], x[1])['left'] - metrics(x[0]['rows'], x[1])['noise']))
        for f in os.listdir(OUT):
            if f.startswith('sbk_') or f.startswith('sbr_'): os.remove(os.path.join(OUT, f))
        for tag, lst in (('sbk', keep), ('sbr', rej)):
            for k in range(0, len(lst), 80): sheet(lst[k:k + 80], os.path.join(OUT, '%s_%d.png' % (tag, k // 80)), sc=4)
        print('claros:', len(keep), '| não claros:', len(rej))
        return
    same = [t['name'] for t, r, _ in res if r == t['rows']]
    print(len(res), 'moldes de 1 placa |', len(same), 'iguais (sem preto fino a tirar)')
    if '--apply' in a:
        items = list(d['items']); removed = set(d.get('removed') or [])
        keep = {t['id']: (t, r) for t, r, info in res if clear_border(t, r, info)}
        gen = {t['id']: r for t, r, _ in res}
        have = {t['id'] for t in items}; out = []; apagadas = 0; mantidas = []; allow = set(); orig = {t['id'] for t in items if not t['id'].startswith(PREFIX)}
        for t in items:
            if t['id'].startswith(PREFIX):
                oid = t['id'][len(PREFIX):]
                if oid not in orig or (oid not in keep and gen.get(oid) == t['rows']):      # original excluído: a cópia vai junto
                    apagadas += 1; allow.add(t['id']); continue
                if oid not in keep:
                    mantidas.append(t['name'])                                      # ele editou esta cópia: não apago
            out.append(t)
        novas = 0
        for oid, (t, r) in keep.items():
            i = PREFIX + oid; n = t['name'] + SUF
            if i in have or n in removed: continue
            out.append({'id': i, 'cat': t['cat'], 'group': t['group'], 'name': n, 'rows': r}); novas += 1
        tplfile.write(tp, d['legend'], d['cfg'], out, d.get('removed'), allow=allow)
        print('apagadas', apagadas, '| novas', novas, '| editadas mantidas', mantidas, '| total', len(out), '| cópias', sum(t['id'].startswith(PREFIX) for t in out))
        return
    for f in os.listdir(OUT):
        if f.startswith('sb_') and f.endswith('.png'): os.remove(os.path.join(OUT, f))
    show = [x for x in res if x[1] != x[0]['rows']]
    per = int(a[a.index('--per') + 1]) if '--per' in a else 90
    for k in range(0, len(show), per):
        sheet(show[k:k + per], os.path.join(OUT, 'sb_%d.png' % (k // per)), sc=int(a[a.index('--sc') + 1]) if '--sc' in a else 4)
    print('folhas', (len(show) + per - 1) // per, '| pretos restantes (média % das contas):', round(100 * np.mean([sum(c in DARK for l in r for c in l) / max(1, sum(c != '.' for l in r for c in l)) for _, r, _ in res]), 1))
    print('letras escuras:', sorted(DARK))


if __name__ == '__main__':
    main()
