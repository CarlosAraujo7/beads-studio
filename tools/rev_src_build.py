"""Gera data/rev_src.json: nome do molde -> [remessa, índice, caixa em px] para as ilustrações das remessas 21, 22 e 23 (as folhas de leitura `rev_sheet.py` usam isto).
uso: python tools/rev_src_build.py"""
import os, sys, json
os.environ['BEADPAL'] = '120'
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import r22_exfinal as R22
import r23_exfinal as R23
src = {}
for mod, rem in ((R22, 22), (R23, 23)):
    for it in mod.CFG:
        n, idx = it[0], it[2]
        if it[4] == 'ill': src[n] = [rem, idx, list(it[6]) if len(it) > 6 and it[6] else None]
# remessa 21 (WWE): nome, índice, caixa (r21_exfinal.ITEMS)
src['Paige (WWE, com cinturão)'] = [21, 1, [250, 0, 1010, 1242]]
src['Paige (WWE, top roxo)'] = [21, 2, [220, 10, 730, 1020]]
src['Paige (WWE, erguendo o cinturão)'] = [21, 2, [860, 0, 1330, 1020]]
# moldes de outras remessas que também entram na revisão (nome -> [remessa, índice, caixa])
src['Anya Forger (chibi)'] = [12, 22, None]
src['Anya Forger (pixel, gráfico)'] = [20, 61, None]
src['Seto Kaiba (pixel)'] = [20, 128, None]
src['Menina de cabelo preto e mechas azuis (pixel)'] = [20, 17, None]
src['Chaveiro de chapéu e faixa verde e amarela (foto de peça pronta)'] = [22, 99, [85, 200, 325, 465]]
src['Kratos (God of War, pixel, corpo inteiro)'] = [23, 20, None]
src['Kratos (God of War, pixel, em pé)'] = [23, 22, None]
json.dump(src, open(os.path.join(HERE, 'data', 'rev_src.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(src), 'fontes')
