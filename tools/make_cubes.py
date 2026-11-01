"""Cubos 3D DE ENCAIXE gerados por tools/cube3d.py (a junta é a de dentes alternados dos cubos lidos das fotos: Abelha, Presente).
Hoje só o DADO (cubo de 6 lados, 7×7×7 desde 2026-10-31: o de 5×5×5 ficou ruim de encaixar na mão, a pedido do usuário. 7 é o menor tamanho com todas as pintas separadas;
5 era o menor possível: a borda de cada face é dividida com as vizinhas, então as pintas só cabem no miolo, e com 4 o miolo é 2×2 e não cabem 5 nem 6 pintas). Os 12 cubos de personagens feitos em 2026-10-29 (Pikachu, Kirby, Creeper, Minion, Batman, Homem de Ferro, Darth Vader, Toad,
Groot, Hello Kitty, Naruto e o Dado 13×13×13) foram APAGADOS a pedido do usuário; o que se aprendeu com eles está em CLAUDE.md (§3, "Cubos GERADOS").
make_3d.py usa cubes() daqui. Para um cubo novo: monte um `spec` (veja cube3d.cube_project) com a textura de cada face.
"""
import os, sys
SP = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SP)
import cube3d


def steps():
    return ['Monte as peças (as iguais são feitas mais de uma vez) e passe o ferro em cada uma, dos dois lados, com papel de forno; deixe esfriar sob um peso.',
            'Os dentes alternam de propósito: onde uma peça tem conta na borda, a vizinha tem vão. Comece pela base e erga a frente, a traseira e as duas laterais.',
            'Feche com a tampa de cima. Se ficar frouxo, uma gota de cola nos cantos. Projeto desenhado (não é de uma foto): teste o encaixe antes de fazer em várias cores.']


def die_face(n, N=5):
    """face de dado N×N com `n` pintas de 1 conta (só no miolo: a borda é das outras faces)"""
    g = [['w'] * N for _ in range(N)]
    a = 1 if N <= 7 else 2
    b, c = N // 2, N - 1 - a                         # posições das pintas (N=5: 1, 2, 3; N=7: 1, 3, 5; N=9: 2, 4, 6)
    pos = {'tl': (a, a), 'tr': (c, a), 'ml': (a, b), 'mr': (c, b), 'bl': (a, c), 'br': (c, c), 'c': (b, b)}
    lay = {1: ['c'], 2: ['tl', 'br'], 3: ['tl', 'c', 'br'], 4: ['tl', 'tr', 'bl', 'br'], 5: ['tl', 'tr', 'c', 'bl', 'br'], 6: ['tl', 'tr', 'ml', 'mr', 'bl', 'br']}
    for p in lay[n]:
        x, y = pos[p]; g[y][x] = 'k'
    return [''.join(r) for r in g]


# cubo mágico da remessa 3D 3 (foto PandaHall): os 6 painéis numerados da foto, 3×3 quadrados de 3×3 contas separados por linhas pretas; a contagem fecha: 9 quadrados de cada uma das 6 cores
R_PAINEIS = {'top': ['RBG', 'RYG', 'GRY'], 'front': ['ROW', 'YOY', 'YWB'], 'right': ['OWO', 'ORR', 'WYB'], 'left': ['RRO', 'BGB', 'GWW'], 'back': ['ROO', 'GWB', 'YOY'], 'bottom': ['BGG', 'YBW', 'BGW']}
R_COR = {'R': 'r', 'B': 'b', 'G': 'L', 'Y': 'y', 'O': 'o', 'W': 'w'}


def rubik_face(p):
    g = [['k'] * 13 for _ in range(13)]
    for j in range(3):
        for i in range(3):
            for y in range(3):
                for x in range(3): g[1 + j * 4 + y][1 + i * 4 + x] = R_COR[p[j][i]]
    return [''.join(r) for r in g]


def rubik():
    n = 13
    return {'id': 'cubo-magico', 'name': f'Cubo mágico ({n}×{n}×{n})', 'size': (n, n, n), 'level': 'Médio',
            'tex': {f: rubik_face(p) for f, p in R_PAINEIS.items()}, 'fill': {'*': 'k'}, 'ears': None,
            'names': {'top': 'Painel 1 (cima)', 'front': 'Painel 2 (frente)', 'right': 'Painel 3 (direita)', 'left': 'Painel 4 (esquerda)', 'back': 'Painel 5 (costas)', 'bottom': 'Painel 6 (base)'},
            'steps': ['Monte os 6 painéis e passe o ferro em cada um, dos dois lados, com papel de forno; deixe esfriar sob um peso.',
                      'Os dentes pretos alternam de propósito: onde um painel tem conta na borda, o vizinho tem vão. Comece pela base e erga os 4 painéis dos lados.',
                      'Feche com o painel de cima. Se ficar frouxo, uma gota de cola nos cantos.'],
            'desc': f'Cubo mágico de {n}×{n}×{n} contas (cerca de {n * 0.26:.1f} cm): 6 painéis planos com 9 quadrados de 3×3 contas separados por linhas pretas. As cores de cada painel são as da foto (6 cores, 9 quadrados de cada, como num cubo embaralhado). Os dentes das bordas seguem a junta dos nossos cubos, que fecha sem sobrar nem faltar conta; na foto eles podem ficar em outra posição.'}


def build():
    N = 7
    return [rubik(), {'id': 'cubo-dado', 'name': f'Cubo Dado ({N}×{N}×{N})', 'size': (N, N, N), 'level': 'Fácil', 'solid': True,
             'tex': {'front': die_face(1, N), 'back': die_face(6, N), 'right': die_face(2, N), 'left': die_face(5, N), 'top': die_face(3, N), 'bottom': die_face(4, N)},
             'fill': {'*': 'w'}, 'ears': None, 'steps': steps(),
             'desc': f'Dado de 6 lados de {N}×{N}×{N} contas (cerca de {N * 0.26:.1f} cm), branco com pintas pretas, em 6 peças planas com dentes alternados que se encaixam sem sobrar nem faltar conta. '
                     'As 6 faces têm de 1 a 6 pintas e as opostas somam 7 (1×6, 2×5, 3×4). Passe pouco o ferro, para os dentes não encolherem. '
                     'É um projeto desenhado (não é de uma foto de peça pronta): teste o encaixe antes.'}]


def cubes():
    return [cube3d.cube_project(s) for s in build()]


if __name__ == '__main__':
    for p in cubes():
        n = sum(sum(1 for r in pc['rows'] for ch in r if ch != '.') * pc['qty'] for pc in p['pieces'])
        print(f"{p['name']:28} peças {sum(pc['qty'] for pc in p['pieces'])} contas {n} casca {p['_shell']}")
        for pc in p['pieces']:
            print('  ', pc['name'], pc['qty'])
            for r in pc['rows']: print('     ', r)
