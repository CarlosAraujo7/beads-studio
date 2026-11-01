"""Remessa 21 (3 imagens, 2026-10-31): RENDERS de peças de contas montadas sobre placa (imagens geradas: as contas não seguem uma grade exata nem a grade dos pinos,
então não dá para ler conta a conta com segurança). Pedido do usuário: "fazer como está e também fazer moldes de tamanho menor pra ver como fica".
  * "como está" = no TAMANHO NATIVO de contas do desenho (passo das contas medido por autocorrelação: cinturão 18,6 px, Paige da 2ª imagem 20 px, as duas da 3ª 10,5-11 px),
    convertido por illus5.convert5 (hatch apaga o furo/brilho de cada conta) e com o rosto conferido conta a conta contra a fonte (olhos com brilho branco e íris, boca) -> "Nome (grande)";
  * menores: 1 placa (lado maior 50) e "(mini)" (lado maior 36), REDUZIDOS do nativo já corrigido (shrink 'bias', que preserva melhor olhos e contorno do que reconverter).
  BEADPAL=120 python tools/r21_exfinal.py [filtro...]   -> data/final23_120.json (1 placa e mini) + data/final23_multi_120.json (nativo, "(grande)")"""
import os, sys, json, glob
os.environ['REMNUM'] = '21'
SP = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SP)
sys.path.insert(0, SP)
import r5, illus, illus5, beadclean, loose, shrink
from flat import render_flat
from palette import sfx
F = sorted(glob.glob(os.path.join(ROOT, 'remessas', 'remessa 21', '*.*')))
BASE = dict(K=20, thr=200, bg='white', hatch=3, dark_frac=0.45, black_L=16.0, seal=0.0, smooth_de=16.0, sat=1.1, contrast=1.05, sharp=0.0)


def conv(idx, size, box=None, skin=True, **kw):
    r5.SKIN_ON = skin
    a = dict(BASE); a.update(kw); a['size'] = size
    rows = illus5.convert5(rgb=illus._load(F[idx], box), **a)
    rows = r5.largest(beadclean.clean(rows))
    rows = loose.fill_pinholes(rows)[0]
    return loose.fix_loose(rows) if loose.loose_count(rows) else rows


def put(rows, cells):
    g = [list(r) for r in rows]
    for (y, x), c in cells.items(): g[y][x] = c
    return [''.join(r) for r in g]


# rostos: coordenadas (linha, coluna) do molde NATIVO, lidas na fonte com a mesma grade (facetools.align: IoU 0,97-0,99). w H2 · i H1 · d H5 · k H7 · s G1 · & D3 (íris) · r F5 · ^ E6 · ] E5
def FIX_WWE(rows):
    """olho esquerdo: 2 brilhos brancos com a pupila entre eles; olho direito: 1 brilho; boca: dentes brancos entre cantos pretos e lábio rosado embaixo"""
    c = {(11, 17): 'w', (11, 19): 'w', (11, 23): 'w',
         (14, 20): 's', (14, 21): 's', (14, 23): 's',
         (15, 19): 'k', (15, 20): 'w', (15, 21): 'w', (15, 22): 'k', (15, 23): 's',
         (16, 20): ']', (16, 21): ']', (16, 23): 's'}
    return put(rows, c)


def FIX_P1(rows):
    """top roxo: olho esquerdo branco · íris azul · branco; olho direito íris azul-escura + brilho; lábio de cima vermelho, de baixo rosa"""
    c = {(13, 18): 'k', (13, 19): 'w', (13, 20): '&', (13, 21): 'w', (13, 22): 'k', (14, 26): '&', (14, 27): 'w',
         (17, 21): 'r', (17, 22): 'r', (17, 23): 'r', (18, 21): '^', (18, 22): '^', (18, 23): '^', (18, 24): 's', (19, 21): 's', (19, 22): 's', (19, 23): 's'}
    return put(rows, c)


def FIX_P2(rows):
    """erguendo o cinturão: olho esquerdo branco · pupila cinza · branco; olho direito pupila + brilho; lábio vermelho em cima e rosa embaixo"""
    c = {(20, 22): 'i', (20, 23): 'd', (20, 24): 'w', (21, 29): 'd', (21, 30): 'w',
         (25, 24): 'r', (25, 25): 'r', (25, 26): 'r', (25, 27): 'r', (25, 28): 's', (26, 24): 's', (26, 25): '^', (26, 26): '^', (26, 27): 's', (26, 28): 's'}
    return put(rows, c)


# (nome, série, índice, caixa em px, lado maior nativo, skin, parâmetros, retoque)
ITEMS = [
    ('Cinturão das Divas (WWE)', 'WWE', 0, (180, 290, 1355, 735), 62, False, dict(hatch=5, K=18, sat=1.3, smooth_de=0.0), None),
    ('Paige (WWE, com cinturão)', 'WWE', 1, (250, 0, 1010, 1242), 63, True, dict(K=20), FIX_WWE),
    ('Paige (WWE, top roxo)', 'WWE', 2, (220, 10, 730, 1020), 91, True, dict(K=20), FIX_P1),
    ('Paige (WWE, erguendo o cinturão)', 'WWE', 2, (860, 0, 1330, 1020), 96, True, dict(K=20), FIX_P2),
]


# rosto nos moldes MENORES: a redução apaga olhos de 1-2 contas; aqui eles voltam no lugar proporcional. (centro do olho e brilho, no molde nativo) e centro da boca
FACE = {'Paige (WWE, com cinturão)': dict(eyes=[((10.5, 18.0), (11, 17)), ((10.5, 23.5), (11, 23))], mouth=(15.5, 20.5)),
        'Paige (WWE, top roxo)': dict(eyes=[((12.8, 20.0), (13, 19)), ((13.8, 26.5), (14, 27))], mouth=(17.5, 22.0)),
        'Paige (WWE, erguendo o cinturão)': dict(eyes=[((20.0, 23.0), (20, 24)), ((21.0, 29.5), (21, 30))], mouth=(25.5, 25.5))}


def smaller(rows, size, face=None):
    s = size / float(max(len(rows), len(rows[0])))
    r = shrink.shrink(rows, size, 'bias', empty_at=0.6)
    if face:
        g = [list(x) for x in r]; H, W = len(g), len(g[0])
        def setc(y, x, c):
            if 0 <= y < H and 0 <= x < W and g[y][x] != '.': g[y][x] = c
        for (ey, ex), (hy, hx) in face['eyes']:
            cy, cx = int(round(ey * s)), int(round(ex * s))
            if size >= 45:                                   # 1 placa: olho preto de 2 contas com 1 brilho branco
                hy2, hx2 = int(round(hy * s)), int(round(hx * s))
                setc(cy, cx, 'k'); setc(cy, cx + (1 if hx2 <= cx else -1), 'k'); setc(hy2 if hy2 != cy else cy, hx2 if hx2 != cx else cx - 1, 'w')
            else:                                            # mini: olho de 1 conta preta
                setc(cy, cx, 'k')
        my, mx = face['mouth']; y, x = int(round(my * s)), int(round(mx * s))
        setc(y, x, 'r')
        if size >= 45: setc(y, x + 1, 'r')
        r = [''.join(x) for x in g]
    return loose.fix_loose(r) if loose.loose_count(r) else r


if __name__ == '__main__':
    only = sys.argv[1:]
    one, multi, items = [], [], []
    pl = lambda r: -(-len(r[0]) // 50) * -(-len(r) // 50)
    for n, g, idx, box, native, sk, kw, fix in ITEMS:
        if only and not any(o in n for o in only): continue
        big = conv(idx, native, box, sk, **kw)
        if fix: big = fix(big)
        small = smaller(big, 50, FACE.get(n)); mini = smaller(big, 36, FACE.get(n))
        multi.append((n + ' (grande)', g, big, {'plates': pl(big)}))
        one.append((n, g, small)); one.append((n + ' (mini)', g, mini))
        for lab, r in (('nativo', big), ('1 placa', small), ('mini', mini)):
            items.append((f'{n[:22]} {lab} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
        print(n, 'nativo %dx%d' % (len(big[0]), len(big)), '1 placa %dx%d' % (len(small[0]), len(small)), 'mini %dx%d' % (len(mini[0]), len(mini)), flush=True)
    if not only:
        json.dump(one, open(os.path.join(SP, 'data', 'final23' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(multi, open(os.path.join(SP, 'data', 'final23_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    render_flat(items, os.path.join(SP, 'out', 'r21_x.png'), scale=7, W=1900)
