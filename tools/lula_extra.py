"""Bonecos do Lula e estrela da categoria Política (2026-10-31; ver CLAUDE.md §7.22). Gera data/final_lula_120.json (entra com add_templates.py).
O usuário escolheu como referência de largura e tamanho a peça de chaveiro da remessa 22 idx 99 (23x25, pernas de 5 contas): CHAVEIRO foi lido conta a conta dessa foto, com a pele em bege claro (pedido dele).
Só o desenho desse chaveiro entra no de chapéu; o sem chapéu é o mesmo corpo e o mesmo rosto, com o chapéu trocado por cabelo (desenhado à mão, seguindo o gráfico do iPad que ele mandou).
A estrela vem do gráfico do iPad: lida conta a conta; a barra lateral cobre a ponta esquerda (linha 6, coluna 0), restaurada pela simetria."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import palette as P
import outline as O
L = {c['code']: c['letter'] for c in P.ALL}
SKIN = 'G1'
MAP = {'W': L['H1'], 'S': L[SKIN], 'k': L['H7'], 'g': L['B4'], 'b': L['D3'], 'y': L['A4'], 'r': L['F5'], 'w': L['H2'], 'a': L['A6'], 'T': L['G9'], 'N': L['G13'], '.': '.'}

CHAVEIRO = [
    '........NNNNNNN........',
    '.......NTTTTTTTN.......',
    '......NTTTTTTTTTN......',
    '.....NTTTTTTTTTTTN.....',
    '.....NTTTTTTTTTTTN.....',
    '.....kkkkkkkkkkkkk.....',
    '...NNkkkkkkkkkkkkkNN...',
    '.NNTTTTTTTTTTTTTTTTTNN.',
    'NTTTWWWWSSSSSSSWWWWTTTN',
    'NTWWWWWSSSSSSSSSWWWWWTN',
    '.NNWWSWSSkSSSkSSWSWWNN.',
    '...NWSSSSkSSSkSSSSWN...',
    '....NNWWSSWWWSSWWNN....',
    '.....kNgWWWWWWWNNk.....',
    '....kbbggbrwrkkbbbk....',
    '...kbbSgybrrrkbbbbbk...',
    '...kbSSbygbrkbbbbbSk...',
    '...kbSSSgygbbbbbbSSk...',
    '....kkbbbgygbbbbgkk....',
    '.....kkkkkgyagkgkk.....',
    '.....kbbbbbbgggbbk.....',
    '.....kbbbbbkbabbbk.....',
    '.....kbbbbbkbbbbbk.....',
    '.....kbbbbbkbbbbbk.....',
    '......kkkkk.kkkkk......']

# sem chapéu: mesmas linhas do chaveiro da 10 para baixo (olhos, barba, corpo), sem o marrom da aba; o topo vira cabelo
SEM = [
    '.........WWWWW.........',
    '.......WWWWWWWWW.......',
    '......WWWWWWWWWWW......',
    '.....WWWWWWWWWWWWW.....',
    '....WWWWWWWWWWWWWWW....',
    '....WWWWSSSSSSSWWWW....',
    '...WWWSSSSSSSSSSSWWW...',
    '...WWWSSSSSSSSSSSWWW...',
    '...WWSSSSSSSSSSSSSWW...',
    '...WWSSSSSSSSSSSSSWW...',
    '...WWSSSSkSSSkSSSSWW...',
    '....WSSSSkSSSkSSSSW....',
    '......WWSSWWWSSWW......',
    '.....kbgWWWWWWWbbk.....'] + CHAVEIRO[14:]

_S = {1: (10, 10), 2: (9, 11), 3: (8, 12), 4: (8, 12), 5: (7, 13), 6: (6, 14), 7: (0, 20), 8: (1, 19), 9: (2, 18), 10: (3, 17), 11: (4, 16), 12: (4, 16), 13: (4, 16), 14: (4, 16), 15: (3, 17)}
ESTRELA = [''.join('r' if a <= x <= b else '.' for x in range(21)) for _, (a, b) in sorted(_S.items())]
for spans in (((2, 8), (12, 18)), ((2, 6), (14, 18)), ((1, 5), (15, 19))):
    ESTRELA.append(''.join('r' if any(a <= x <= b for a, b in spans) else '.' for x in range(21)))


def conv(rows, m=None): return [''.join((m or MAP)[c] for c in r) for r in rows]


ITEMS = [('Estrela vermelha (gráfico)', 'Política', conv(ESTRELA)),
         ('Lula (chibi, gráfico)', 'Política', O.trim(conv(SEM))),
         ('Lula de chapéu (chibi, gráfico)', 'Política', conv(CHAVEIRO))]

if __name__ == '__main__':
    for n, s, r in ITEMS: assert len({len(x) for x in r}) == 1, n
    json.dump(ITEMS, open(os.path.join(HERE, 'data', 'final_lula_120.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for n, s, r in ITEMS: print(n, '%dx%d' % (len(r[0]), len(r)), sum(c != '.' for x in r for c in x), 'contas')
