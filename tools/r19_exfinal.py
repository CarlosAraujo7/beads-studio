"""Remessa 19 (47 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r19_exfinal.py   -> data/final21_120.json
Quase tudo são gráficos de pixel (cópia exata, exact6). Folhas com vários personagens (Pooh e amigos, SpongeBob, Hora de Aventura, Eeveelutions,
Angel e Stitch, dois céus) são divididas por colunas/linhas vazias.
Puladas: 4, 6, 13, 24 (cópias exatas por MD5 de remessas 3, 13 e 6), 5 (foto de 2 chaveiros), 14 (gráfico chinês de mini-princesa em 3D) e 15 (foto de peça do Minecraft).
"""
import os, sys, json
os.environ['REMNUM'] = '19'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, r6, outline as O
from flat import render_flat
from palette import sfx
E = r6.exact6
BG = (232, 224, 216)        # fundo bege dos gráficos de bolinhas (download (n).png)


def cblocks(rows, min_gap=1):
    """separa em blocos por colunas vazias (personagens lado a lado)"""
    W = len(rows[0]); out = []; cur = []
    for x in range(W):
        if all(r[x] == '.' for r in rows):
            if cur: out.append(cur); cur = []
        else: cur.append(x)
    if cur: out.append(cur)
    return [O.trim([''.join(r[x] for x in xs) for r in rows]) for xs in out]


def rblocks(rows):
    """separa em blocos por linhas vazias"""
    out = []; cur = []
    for r in rows:
        if all(c == '.' for c in r):
            if cur: out.append(cur); cur = []
        else: cur.append(r)
    if cur: out.append(cur)
    return [O.trim(b) for b in out]


def grid_blocks(rows, nrow, ncol):
    """folha em grade nrow×ncol (figuras do mesmo 'quadro'): corta por linhas vazias e depois por colunas vazias"""
    out = []
    for band in rblocks(rows):
        out += cblocks(band)
    return out


_CACHE = {}
def cached(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]


def part(key, fn, i): return lambda: cached(key, fn)[i]


def lg(rows): return r5.largest(rows)


def fox38():
    """#38: print de editor (passo 15 px, régua de 17 px) com fundo xadrez branco/cinza IGUAL ao branco das contas: só as contas têm um pontinho escuro no centro.
    Converte tudo (sem tirar fundo) e esvazia as células claras sem pontinho."""
    import glob, numpy as np
    from PIL import Image
    f = sorted(glob.glob(os.path.join(os.path.dirname(SP), 'remessas', 'remessa 19', '*.*')))[38]
    im = np.array(Image.open(f).convert('L')).astype(float)
    W, H = 38, 40
    rows = E(38, crop_img=(17, 17, 17 + 15 * W, 17 + 15 * H), px=dict(px=15, py=15, ox=0, oy=0, W=W, H=H), mode=True, ref=(0, 255, 0), tol=1)
    # E recorta (trim) as linhas/colunas vazias: sem fundo removido não há nada a cortar, então rows tem H x W
    out = []
    for j, r in enumerate(rows):
        s = ''
        for i, ch in enumerate(r):
            cx, cy = 17 + 15 * i + 7, 17 + 15 * j + 7
            dot = im[cy - 2:cy + 3, cx - 2:cx + 3].min() < 130
            s += ch if (ch not in 'wiqlh' or dot) else '.'
        out.append(s)
    return lg(O.trim(out))


CFG = [
 # ---- gráficos de pixel (cópia exata)
 ('Gato siamês (pixel, versão 2)', 'Outros', lambda: E(0)),
 ('Darth Vader (capacete, pixel)', 'Star Wars', lambda: E(1)),
 ('Homem-Aranha (chibi, pixel)', 'Marvel', lambda: E(3)),
 ('Luffy (chibi grande, pixel)', 'One Piece', lambda: E(7)),
 ('Praia com tartaruga (pixel)', 'Outros', lambda: E(8, ref=(0, 255, 0), tol=1)),
 ('Sonic (pixel)', 'Sonic', lambda: E(9)),
 ('Luffy (chibi, pixel, versão 2)', 'One Piece', lambda: E(10)),
 ('Keroppi', 'Hello Kitty', lambda: E(11)),
 ('Creeper (chibi, pixel)', 'Minecraft', lambda: E(12, crop=(1, 31, 1, 30))),
 ('Dinossauro verde (pixel)', 'Outros', lambda: E(16)),
 ('Homem de Ferro (chibi, pixel)', 'Marvel', lambda: E(17)),
 ('Stormtrooper (capacete, pixel)', 'Star Wars', lambda: E(19)),
 ('Violão roxo (pixel)', 'Instrumentos', lambda: E(21, crop=(0, 27, 0, 16))),
 ('Crash Bandicoot (pixel)', 'Crash Bandicoot', lambda: E(23)),
 ('Groot (chibi, no vaso, pixel)', 'Marvel', lambda: E(25)),
 ('Peashooter (pixel)', 'Plants vs Zombies', lambda: E(27)),
 ('Bakugo Katsuki (chibi, pixel)', 'My Hero Academia', lambda: E(28)),
 ('Yoshi (pixel)', 'Mario', lambda: E(29)),
 ('Tubarão fofo (pixel)', 'Outros', lambda: E(31)),
 ('Crânio de T-rex (pixel)', 'Outros', lambda: E(42)),
 ('Tricerátops azul (pixel)', 'Outros', lambda: E(43)),
 ('Naruto sobre o sapo (pixel)', 'Naruto', lambda: E(44)),
 ('Deadpool (pixel, corpo inteiro)', 'Marvel', lambda: E(45)),
 ('Goku (chibi, pixel, fundo azul)', 'Dragon Ball', lambda: E(46)),
 ('Sapo mago de chapéu roxo (pixel)', 'Outros', lambda: E(26, px=18.5)),
 # ---- gráficos de bolinhas (fundo bege)
 ('Jesus (chibi com auréola, pixel)', 'Religião', lambda: E(32, post=lg)),
 ('Chibi de cabelo prateado e katana longa (pixel)', 'Outros', lambda: E(33, crop=(2, 48, 1, 41), ref=BG, tol=10, post=lg)),
 ('Unicórnio arco-íris (pixel, versão 2)', 'Outros', lambda: E(34, ref=BG, tol=10, post=lg)),
 ('Groudon primal (pixel)', 'Pokémon', lambda: E(35, ref=BG, tol=10, post=lg)),
 ('Bulbasaur (pixel)', 'Pokémon', lambda: E(36, ref=BG, tol=10, post=lg)),
 ('Máscara de raposa (kitsune, pixel)', 'Outros', lambda: E(37, ref=(234, 234, 234), tol=8, post=lg)),
 ('Raposa branca de caudas vermelhas (pixel)', 'Outros', fox38),
 ('Inosuke (chibi, pixel)', 'Demon Slayer', lambda: E(39)),
 ('Ivysaur (pixel)', 'Pokémon', lambda: E(40, ref=BG, tol=10, post=lg)),
]

# ---- folhas: Pooh e amigos (img 2), SpongeBob (30), Hora de Aventura (41), Eeveelutions (18), Angel e Stitch (22), dois céus (20)
POOH = ['Bisonho', 'Ursinho Pooh', 'Tigrão', 'Leitão']
for i, n in enumerate(POOH):
    CFG.append((f'{n} (pixel)', 'Ursinho Pooh', part('pooh', lambda: grid_blocks(E(2, px=10.32), 2, 2), i)))
SPONGE = ['Bob Esponja (pixel)', 'Patrick Estrela (pixel)', 'Lula Molusco (pixel)', 'Gary (pixel)', 'Sr. Sirigueijo (pixel)', 'Sandy Bochechas (pixel)']
for i, n in enumerate(SPONGE):
    CFG.append((n, 'Bob Esponja', part('sponge', lambda: grid_blocks(E(30), 2, 3), i)))
ADV = ['Finn', 'Jake', 'Princesa Jujuba', 'Rei Gelado', 'Princesa Caroço', 'BMO', 'Princesa Chama', 'Marceline', 'Guarda de banana', 'Lady Rainicorn']
for i, n in enumerate(ADV):
    CFG.append((f'{n} (pixel)', 'Hora de Aventura', part('adv', lambda: grid_blocks(E(41), 4, 3), i)))
EEV = ['Eevee', 'Jolteon', 'Flareon', 'Vaporeon', 'Umbreon', 'Espeon', 'Leafeon', 'Glaceon', 'Sylveon']
for i, n in enumerate(EEV):
    CFG.append((f'{n} (pixel, versão 2)', 'Pokémon', part('eev', lambda: grid_blocks(E(18), 3, 3), i)))
def angel_stitch():
    a = E(22, crop=(1, 31, 1, 58), clear=[(0, 6, 24, 30), (19, 25, 47, 53)])      # moldura branca de fora, coração entre os dois e a bola roxa do canto
    a = [r.replace('u', '.').replace('x', '.') for r in a]                       # bola roxa do canto e pontinhos de legenda
    return [lg(O.trim([r[:26] for r in a])), lg(O.trim([r[27:] for r in a]))]


CFG.append(('Angel (Lilo & Stitch, pixel)', 'Lilo & Stitch', part('as', angel_stitch, 0)))
CFG.append(('Stitch (pixel, versão 2)', 'Lilo & Stitch', part('as', angel_stitch, 1)))
CFG.append(('Céu dividido: noite e dia (pixel)', 'Outros', lambda: E(20, ref=(0, 255, 0), tol=1)))

# JÁ EXISTEM no catálogo (dupcheck + comparação lado a lado, 2026-10-30: mesma arte, só mudam as cores/recorte da conversão antiga). Pedido do usuário: "mantenha as novas
# e o que estiver duplicado tire os antigos" -> a conversão nova entra com o NOME ANTIGO e `add_templates.py --replace --readd` troca as linhas (o molde antigo some;
# id, categoria e posição ficam). Os que o usuário tinha excluído (Espeon, Glaceon, Sylveon) voltam com --readd.
OLD = {'Homem de Ferro (chibi, pixel)': 'Homem de Ferro (chibi)', 'Naruto sobre o sapo (pixel)': 'Naruto Modo Sapo', 'Yoshi (pixel)': 'Yoshi',
       'Goku (chibi, pixel, fundo azul)': 'Goku (chibi pixel)', 'Luffy (chibi, pixel, versão 2)': 'Luffy (chibi, pixel)', 'Crash Bandicoot (pixel)': 'Crash Bandicoot',
       'Groot (chibi, no vaso, pixel)': 'Groot (no vaso)', 'Peashooter (pixel)': 'Peashooter (Plants vs Zombies)', 'Homem-Aranha (chibi, pixel)': 'Homem-Aranha (chibi)',
       'Inosuke (chibi, pixel)': 'Inosuke (máscara de javali)'}
OLD.update({f'{n} (pixel, versão 2)': f'{n} (sentado)' for n in EEV})
CFG = [(('BMO (mini, pixel)' if n == 'BMO (pixel)' else n), g, f) for n, g, f in CFG]       # "BMO (pixel)" já existe (outra arte, 26x28)

# ---- REVISÃO (2026-10-30, pedido do usuário depois de gravar o catálogo definitivo: "as que mantive não ficaram completamente fiéis; as evoluções do Eevee perderam os olhos")
# Auditoria: fonte (cores brutas das células, alinhadas) × molde, e métrica de erro de cor. Achados:
#  (1) Eeveelutions (fonte em JPEG, 8,6 px por célula): o `snap` RGB(16) + `despeckle120`(ΔE<11) apagavam detalhes claros e miúdos (olhos azul-claro do Sylveon, íris marrom do Leafeon, azul-petróleo
#      do Glaceon) e deixavam as cores manchadas -> conversão `faithful.patched(T=0, smooth_T=8, desp_T=5)`: suaviza só o ruído (difere < 8 ΔE da mediana dos vizinhos) e usa despeckle conservador (5);
#  (2) a trava de PELE do near120 (`r5.SKIN_ON`) empurrava para bege-rosado o que é osso (crânio de T-rex), amarelo (barriga do sapo mago) e creme (máscara kitsune): trava só em rostos humanos;
#  (3) Tricerátops: ícone de lupa (marca d'água do site) no canto = 21 contas, tirado.
# Os demais (Bulbasaur, Ivysaur, praia, T-rex etc.) JÁ eram fiéis: a conversão "fiel" funde gradações de sombreado e piora gráficos limpos, então NÃO é usada neles.
# As diferenças de cor que sobram (Yoshi, Stitch, Peashooter, Tricerátops…) são limite da paleta: cor vivida da fonte (13,94,241) não existe em contas (a mais perto é usada).
REVISED_EEV = [f'{n} (sentado)' for n in EEV]
REVISED_SKIN = ['Crânio de T-rex (pixel)', 'Sapo mago de chapéu roxo (pixel)', 'Máscara de raposa (kitsune, pixel)', 'Praia com tartaruga (pixel)', 'Dinossauro verde (pixel)']


def revised():
    import faithful
    out = []
    for n, g, fn in CFG:
        name = OLD.get(n, n)
        if name in REVISED_EEV:
            r5.SKIN_ON = False; _CACHE.clear()
            with faithful.patched(T=0, smooth_T=8, desp_T=5): out.append((name, g, fn()))
        elif name in REVISED_SKIN:
            r5.SKIN_ON = False; _CACHE.clear(); out.append((name, g, fn()))
    return out


if __name__ == '__main__' and sys.argv[1:] == ['--revisao']:
    out = revised()
    json.dump(out, open(os.path.join(SP, 'data', 'final21_revisao' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(out), 'moldes revisados'); sys.exit(0)

if __name__ == '__main__':
    only = sys.argv[1:]
    out = []; items = []
    for n, g, fn in CFG:
        if only and not any(o in n for o in only): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = fn(); out.append((OLD.get(n, n), g, r)); items.append((f'{n[:26]} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
        except SystemExit as e:
            print('ERRO', n, e)
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(out), 'templates')
    if not only: json.dump(out, open(os.path.join(SP, 'data', 'final21' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'r19_x_{k // 12}' + sfx() + '.png'), scale=8, W=1900)
