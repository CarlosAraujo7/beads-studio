"""Aplica a VIVACIDADE padrão na paleta (2026-11-02, pedido do dono: "a maior diferença foi que você deixou todas as cores muito mais vivas, e não é isso").
O celular exagera a saturação (o croma médio da paleta medida é 1,55x o da antiga; 20 cores passam de croma 80). Cada cor guarda a medida crua da foto em `hex_foto` e o `hex` passa a ser a cor com o croma comprimido
com JOELHO (palette_tone.tone_knee: até croma 28 nada muda, então pele, creme e pastéis ficam como estão; acima, croma' = 28 + (croma - 28) x s).
uso:  python tools/apply_vividness.py [S]      (S = 0,75 por padrão; 1,0 devolve a medida crua)   depois:  python tools/sync_palette_to_app.py
É idempotente: parte sempre de `hex_foto` (se existir). Depois de rodar `build_bead_palette2.py --apply` (que grava só a medida) rode este de novo.
Cópia antes: tools/backups/palette-pre-vivacidade.json. O app tem o controle "Vivacidade" em Menu > Ajustar cores (100% = medida crua)."""
import os, sys, json, shutil
SP = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SP)
import palette_tone as PT

S = float(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 0.75
p = os.path.join(SP, 'data', 'palette.json')
d = json.load(open(p, encoding='utf-8'))
bk = os.path.join(SP, 'backups', 'palette-pre-vivacidade.json')
if not os.path.exists(bk): shutil.copy(p, bk)
n = 0
for c in d['colors']:
    raw = c.get('hex_foto') or c['hex']
    c['hex_foto'] = raw
    new = PT.rgb2hex(PT.tone_knee(PT.hex2rgb(raw), S))
    if new != c['hex']: n += 1
    c['hex'] = new
d['vivacidade'] = S
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('vivacidade %.2f: %d de %d cores mudaram em relação à gravada' % (S, n, len(d['colors'])))
import numpy as np
ch = [float(np.hypot(*PT.rgb2lab(PT.hex2rgb(c['hex']))[1:])) for c in d['colors']]; cr = [float(np.hypot(*PT.rgb2lab(PT.hex2rgb(c['hex_foto']))[1:])) for c in d['colors']]
print('croma médio: foto %.1f -> agora %.1f | cores com croma > 80: %d -> %d' % (np.mean(cr), np.mean(ch), sum(v > 80 for v in cr), sum(v > 80 for v in ch)))
