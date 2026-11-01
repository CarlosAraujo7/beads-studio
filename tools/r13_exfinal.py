"""Remessa 13 (40 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r13_exfinal.py   -> data/final15_120.json
(sem BEADPAL grava data/final15.json com as 24 cores antigas — só para comparar).

Três tipos de imagem:
  * gráficos de pixel (exact6): cópia exata, como nas outras remessas;
  * ilustrações/adesivos SEM grade (illus.py): reduzidas a até 50 contas, APROXIMADAS (confira olhando);
  * folhas com várias figuras (22 monstrinhos de terror, 10 chibis de One Piece): cada figura vira um molde.
"""
import os, sys, json
os.environ['REMNUM'] = '13'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, r6, outline as O, illus
from flat import render_flat
import glob
from palette import sfx
E = r6.exact6
FILES = sorted(glob.glob(os.path.join(os.path.dirname(SP), 'remessas', 'remessa 13', '*.*')))


def S(idx, size=50, **kw): return illus.convert(FILES[idx], size=size, **kw)


def SPLIT(idx, n, size, join=3, min_area=0.003): return illus.split(FILES[idx], n, size=size, join=join, min_area=min_area)


def strip_frame(rows):
    """tira linhas/colunas de borda quase todas brancas (moldura de 1 célula do print)"""
    rows = list(rows)
    while rows and sum(c == 'w' for c in rows[0]) > 0.8 * len(rows[0]): rows.pop(0)
    while rows and sum(c == 'w' for c in rows[-1]) > 0.8 * len(rows[-1]): rows.pop()
    while rows and sum(r[0] == 'w' for r in rows) > 0.8 * len(rows): rows = [r[1:] for r in rows]
    while rows and sum(r[-1] == 'w' for r in rows) > 0.8 * len(rows): rows = [r[:-1] for r in rows]
    return O.trim(rows)


def cut(w): return lambda rows: O.trim([r[:w] for r in rows])


_SHEETS = {}
def sheet(idx, n, size, join=3):
    if (idx, n) not in _SHEETS: _SHEETS[(idx, n)] = SPLIT(idx, n, size, join)
    return _SHEETS[(idx, n)]


CFG = [
 # --- gráficos de pixel (cópia exata)
 ('Subaru Natsuki (Re:Zero, corpo inteiro)', 'Re:Zero', lambda: E(1)),
 ('Shoto Todoroki (pixel, corpo inteiro)', 'My Hero Academia', lambda: E(2)),
 ('Chibi de cabelo castanho e capa azul (pixel)', 'Outros', lambda: E(4)),
 ('Homem de jaqueta e cabelo longo (pixel)', 'Outros', lambda: E(5, post=lambda r: O.trim(r[:47]))),
 ('Sasuke Uchiha (corpo inteiro, pixel)', 'Naruto', lambda: E(6)),
 ('Frieren sobre livros (pixel)', 'Frieren', lambda: E(7, post=lambda r: r5.largest(O.trim([x[:58] for x in r])))),
 ('Cavaleiro Oco (Hollow Knight)', 'Hollow Knight', lambda: E(9)),
 ('Darkness (KonoSuba, pixel)', 'KonoSuba', lambda: E(13)),
 ('Darkness (KonoSuba, pixel, versão 2)', 'KonoSuba', lambda: E(14)),
 ('Pochita (Chainsaw Man)', 'Chainsaw Man', lambda: E(15)),
 ('Link (Zelda, chibi pixel)', 'Zelda', lambda: E(16)),
 ('Homem de Ferro (voando, pixel)', 'Marvel', lambda: E(17)),
 ('Velho de manto dourado e tapa-olho (pixel)', 'Outros', lambda: E(18)),
 ('Link (com escudo Hylian, pixel)', 'Zelda', lambda: E(19)),
 ('Esqueleto de manto azul (pixel)', 'Outros', lambda: E(20)),
 ('Naruto (chibi pixel, brilho verde)', 'Naruto', lambda: E(24)),
 ('All Might (forma magra, pixel)', 'My Hero Academia', lambda: E(25)),
 ('Mirio Togata (pixel)', 'My Hero Academia', lambda: E(27)),
 ('Reator Arc (Homem de Ferro)', 'Marvel', lambda: E(28)),
 ('Megumin (pixel, de chapéu)', 'KonoSuba', lambda: E(31)),
 ('Ichigo Kurosaki (pixel, corpo inteiro)', 'Bleach', lambda: E(32, crop=(0, 64, 0, 37))),      # a última coluna é uma linha branca de moldura: sem ela o fundo verde-claro é achado pelos cantos
 ('Goku (pixel, cabelo espetado)', 'Dragon Ball', lambda: E(35)),
 ('Kurama (pixel, laranja)', 'Naruto', lambda: E(37)),
 ('Shinra Kusakabe (Fire Force)', 'Fire Force', lambda: E(38, clear=[(0, 3, 0, 3)])),
 ('Criatura robótica com coração (pixel)', 'Outros', lambda: E(39, crop_img=(0, 0, 675, 597), ref=(64, 86, 74), tol=30, post=strip_frame)),
 # --- gráfico de editor (3 rostos): moldura e legenda recortadas
 ('Três rostos empilhados (cabelo branco, roxo e vermelho)', 'Outros', lambda: E(36, crop_img=(36, 96, 1149, 1209), px=21.4, mode=True, ref=(205, 204, 210), tol=14)),
 # --- adesivos / ilustrações (aproximado, até 50 contas)
 ('Senku Ishigami (Dr. Stone, adesivo)', 'Dr. Stone', lambda: S(0)),
 ('Toji Fushiguro (adesivo)', 'Jujutsu Kaisen', lambda: S(3)),
 ('Echidna (Re:Zero, adesivo)', 'Re:Zero', lambda: S(8)),
 ('Ichigo Kurosaki (chibi, adesivo)', 'Bleach', lambda: S(10)),
 ('Encapuzado de olho vermelho (adesivo)', 'Outros', lambda: S(11)),
 ('Pássaro de máscara vermelha (adesivo)', 'Outros', lambda: S(12)),
 ('Rimuru Tempest (adesivo)', 'Tensura (Slime)', lambda: S(26)),
 ('Subaru Natsuki (adesivo)', 'Re:Zero', lambda: S(29)),
 ('Beatrice (Re:Zero, adesivo)', 'Re:Zero', lambda: S(30)),
 ('Subaru Natsuki (aura sombria, adesivo)', 'Re:Zero', lambda: S(34, thr=175, white_outside=(0.3, 0.34))),
]
# --- folha de 10 chibis de One Piece (img 33) e de monstrinhos de terror (img 22)
OP = ['Luffy', 'Zoro', 'Nami', 'Chopper', 'Usopp', 'Sanji', 'Nico Robin', 'Franky', 'Brook', 'Jinbe']
for i, n in enumerate(OP):
    CFG.append((f'{n} (chibi, One Piece)', 'One Piece', (lambda i=i: sheet(33, 10, 40)[i])))
HORROR = ['Freddy Krueger', 'Jason Voorhees', 'Pennywise', 'Ghostface', 'Pinhead', 'Espantalho de abóbora', 'Encapuzado azul', 'Michael Myers (máscara branca)',
          'Frankenstein', 'Cabelo preto de camisa preta', 'Monstro azul de olhos laranja', 'Máscara de hóquei', 'Homem de pele escura e boné', 'Monstro verde', 'Homem de branco',
          'Menino de macacão azul', 'Fantasma cinza', 'Demônio vermelho', 'Homem de chapéu marrom', 'Monstro azul de capuz vermelho', 'Lobisomem', 'Ceifador', 'Esqueleto',
          'Gosma verde', 'Diabo vermelho', 'Homem de terno', 'Mulher pálida de cabelo preto', 'Homem de chapéu laranja e roupa roxa', 'Monstro azul de chapéu', 'Ruivo de camisa bege']
for i, n in enumerate(HORROR):
    CFG.append((f'{n} (monstrinho de terror)', 'Halloween', (lambda i=i: sheet(22, 30, 30, 0)[i])))

if __name__ == '__main__':
    only = sys.argv[1:]
    out = []; items = []
    for n, g, fn in CFG:
        if only and not any(o in n for o in only): continue
        try:
            __import__('r5').SKIN_ON = __import__('r5').skin_for(n, g)
            r = fn(); out.append((n, g, r)); items.append((f'{n[:26]} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
        except SystemExit as e:
            print('ERRO', n, e)
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(out), 'templates')
    if not only: json.dump(out, open(os.path.join(SP, 'data', 'final15' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'r13_x_{k // 12}' + sfx() + '.png'), scale=8, W=1900)
