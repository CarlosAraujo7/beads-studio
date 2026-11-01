"""11ª revisão (2026-11-01, CLAUDE.md §7.33): olhos de Grimmjow, Hyoga, Shiryu e Ikki; preto em volta do capacete do Ikki. Só por retoque.gravar.
  BEADPAL=120 python tools/rev11.py sheet "nome" r0 r1 c0 c1 [célula] [--new]   leitura: arte | molde; tools/out/r11s.png
  BEADPAL=120 python tools/rev11.py [--H n]                                     prévia tools/out/r11_N.png
  BEADPAL=120 python tools/rev11.py --apply"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rev10 as V
from rev10 import put, O, parse, R, T, OUT, loose, retoque
from PIL import Image
V.SRC.update({'Grimmjow (Bleach, gráfico)': (20, None), 'Shiryu de Dragão (pixel, corpo inteiro, armadura verde)': (13, (290, 0, 439, 200))})
FIX = {}


def fix(n):
    def d(fn): FIX[n] = fn; return fn
    return d


@fix('Grimmjow (Bleach, gráfico)')
def grimmjow(r):
    """lido na grade nativa da arte: o olho azul com branco fica em x18-19; rosto liso (o ruído da conversão virava mancha), de 3/4: olho de longe menor; sem boca"""
    return put(r, [(8, 14, ['ÖÔÔÔsssss']), (9, 14, ['ÔkkÔkkkss']), (10, 14, ['sbsswbkss']), (11, 15, ['ÔÔÔsssss']), (12, 17, ['Ôssss'])])


@fix('Hyoga de Cisne (pixel, corpo inteiro, versão 2)')
def hyoga(r):
    """de 3/4 como na arte: franja loira à esquerda, olho de longe de 1 conta e o de perto com branco, pálpebra preta sobre o azul; sem boca"""
    return put(r, [(9, 13, ['kk3kk']), (10, 12, ['yskswks']), (11, 12, ['yybswbs']), (12, 12, ['aaysssk'])])


@fix('Shiryu de Dragão (pixel, corpo inteiro, armadura verde)')
def shiryu(r):
    """dois olhos separados por 1 conta de pele, com a franja preta em cima; queixo que afina; sem boca"""
    return put(r, [(10, 16, ['ksssssk']), (11, 16, ['kskskSk'.replace('S', 's')]), (12, 17, ['kÑssÑk'[:5]]), (12, 22, ['k'])])


@fix('Ikki de Fênix (pixel, corrente vermelha)')
def ikki(r):
    """menos preto em volta do capacete: o cabelo azul encosta direto no capacete, como na arte (o azul apagado virou o azul do cabelo) e a sombra sobre e sob a viseira vira vermelho-escuro; dois olhos, sem boca"""
    return put(r, [(1, 29, ['.k']), (1, 33, ['&&&b']), (2, 26, ['&']), (2, 32, ['&&&&&']), (3, 26, ['&b&']), (3, 32, ['&&&&b']), (3, 41, ['.']),
                   (4, 26, ['&&&']), (4, 31, ['ÈÈÈÈÈÈÈÈ']), (4, 39, ['É']), (5, 25, ['&b&&']), (6, 25, ['&&&&&']), (7, 26, ['&b&&È']),
                   (8, 26, ['&&&&']), (8, 32, ['ÈÈkÌÈÈ&&&']), (9, 26, ['b&&&']), (9, 34, ['Ñsssk&&']), (10, 27, ['&&&ww']), (10, 34, ['kskskb'[:5]]), (10, 39, ['&b']),
                   (11, 27, ['&&k']), (11, 30, ['mli']), (11, 33, ['ksssk..'])])


def main():
    cat = {t['name']: t for t in parse(T)['items']}; a = sys.argv[1:]
    if a and a[0] == 'sheet':
        n = next(k for k in V.SRC if a[1].lower() in k.lower())
        rows = FIX[n](cat[n]['rows']) if '--new' in a and n in FIX else cat[n]['rows']
        V.sheet(n, rows, int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]) if len(a) > 6 and a[6].isdigit() else 24, os.path.join(OUT, 'r11s.png'))
        return
    H = int(a[a.index('--H') + 1]) if '--H' in a else 600
    new = {n: O.trim(fn(cat[n]['rows'])) for n, fn in FIX.items()}
    if '--apply' in a:
        retoque.gravar({cat[n]['id']: new[n] for n in new}, {cat[n]['id']: cat[n]['rows'] for n in new}); return
    items = []
    for n in new:
        items.append((f'{n[:40]} ANTES', Image.fromarray(V.raw_of(n)), cat[n]['rows']))
        items.append((f'DEPOIS {len(new[n][0])}x{len(new[n])} soltas {loose.loose_count(new[n])}', None, new[n]))
    for k in range(0, len(items), 4):
        R.pairsheet(items[k:k + 4], os.path.join(OUT, f'r11_{k // 4}.png'), H=H)


if __name__ == '__main__':
    main()
