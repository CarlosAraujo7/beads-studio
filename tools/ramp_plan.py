"""PLANO DA RAMPA DE CINZAS PARA OS MOLDES QUASE TODOS PRETOS (2026-11-03). SÓ LÊ o catálogo; grava só em tools/out/ramp_plan* (nada vai para o templates.js sem o dono escolher os moldes).
Pedido do dono: "o Xenomorfo é todo preto, fica ruim quando feito; seria bacana ter gradientes com cinza e detalhes nesses moldes majoritariamente pretos".
Método (só mexe nas contas que a rampa muda, então o que ele retocou à mão e o que já foi recolorido continua): `DARKRAMP=1 python tools/reconv_all.py` reconverte tudo com `darkramp.ramp` + `hl_gain` (saída tools/out/rc_ramp);
aqui, para cada molde, a reconversão SEM rampa (tools/out/rc_all) e a COM rampa são alinhadas à silhueta do catálogo (`rc_plan.best`) e só entram as contas em que (a) a rampa mudou a letra e (b) o catálogo ainda tem a letra da reconversão sem rampa
(se não tem, a conta foi retocada à mão ou ajustada por mim: fica).
Candidato = molde com >= 50% de contas pretas (H7) e a rampa muda >= 4% das contas (e >= 25).
uso:  python tools/ramp_plan.py [--sheet]   (--sheet gera as folhas AGORA | PROPOSTA em tools/out/ramp_cand_NN.png)
Só serve para ILUSTRAÇÃO/adesivo (convert5). Gráfico em malha e pixel art são cópia fiel e não têm rampa; as ilustrações antigas (convert4, remessas 14-18) não passam pelo convert5 e ficam sem proposta."""
import os, sys, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import numpy as np
import tplfile, remap_cores as RC, rc_plan as RP, recolor_apply as RA

NB = RC.NEW_BY_L
OUTD = os.path.join(HERE, 'out', 'ramp_plan'); os.makedirs(OUTD, exist_ok=True)


def load(sub):
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, 'out', sub, '*', '*.json'))):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        out[os.path.relpath(f, os.path.join(HERE, 'out', sub))] = d
    return out


def main():
    cat = tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']; byname = {}
    for it in cat: byname.setdefault(it['name'], []).append(it)
    base = load('rc_all'); ramp = load('rc_ramp'); res = []
    for rel, rd in ramp.items():
        bd = base.get(rel)
        if bd is None or bd['name'] != rd['name']: continue
        for it in byname.get(rd['name'], []):
            C = it['rows']
            ib, Rb = RP.best(C, bd['rows']); ir, Rr = RP.best(C, rd['rows'])
            if Rb is None or Rr is None or ib < 0.96 or ir < 0.96: continue
            n = sum(1 for r in C for ch in r if ch != '.')
            k7 = sum(1 for r in C for ch in r if ch == 'k') / max(1, n)
            rows = []; nd = 0
            for y, rc in enumerate(C):
                line = ''
                for x, c in enumerate(rc):
                    b = Rb[y][x]; r = Rr[y][x]
                    if c != '.' and b != '.' and r != '.' and r != b and c == b:
                        line += RP.guard(c, r); nd += (RP.guard(c, r) != c)
                    else: line += c
                rows.append(line)
            res.append(dict(id=it['id'], name=it['name'], cat=it['cat'], sha=RA.sha(C)[:8], beads=n, k7=round(k7, 3), delta=nd, share=round(nd / max(1, n), 3), iou=(round(ib, 3), round(ir, 3))))
            json.dump({'rows': rows}, open(os.path.join(OUTD, it['id'] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    res.sort(key=lambda r: (-r['k7'], -r['delta']))
    json.dump(res, open(os.path.join(HERE, 'out', 'ramp_plan.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    cand = [r for r in res if r['k7'] >= 0.5 and r['share'] >= 0.04 and r['delta'] >= 25]
    print('moldes comparados:', len(res), '| candidatos (>= 50%% de preto e rampa muda >= 4%%): %d' % len(cand))
    for r in cand: print('  H7 %.2f  muda %3d (%4.1f%%)  %-9s %s' % (r['k7'], r['delta'], 100 * r['share'], r['cat'][:9], r['name'][:60]))
    json.dump([r['id'] for r in cand], open(os.path.join(HERE, 'out', 'ramp_cand_ids.json'), 'w'))
    if '--sheet' in sys.argv: sheets(cand)


def sheets(cand, per=18, cols=3, sc=4):
    from PIL import Image, ImageDraw
    import src_vs_mold as SV
    F = SV.F; cat = {t['id']: t for t in tplfile.parse(os.path.join(ROOT, 'templates.js'))['items']}
    pages = [cand[i:i + per] for i in range(0, len(cand), per)]
    for pi, page in enumerate(pages):
        tiles = []
        for r in page:
            C = cat[r['id']]['rows']; P = json.load(open(os.path.join(OUTD, r['id'] + '.json'), encoding='utf-8'))['rows']
            s = max(2, min(sc, 190 // max(len(C), len(C[0])) + 1)); tiles.append((r, RC.draw(C, SV.NEWP, s, (236, 236, 236)), RC.draw(P, SV.NEWP, s, (236, 236, 236))))
        cw = max(a.width + b.width for _, a, b in tiles) + 30; ch = max(a.height for _, a, b in tiles) + 20
        rn = (len(tiles) + cols - 1) // cols
        im = Image.new('RGB', (cols * cw, rn * ch + 18), (250, 248, 244)); dr = ImageDraw.Draw(im)
        dr.text((4, 2), 'rampa de cinzas  pág %d/%d   AGORA | PROPOSTA' % (pi + 1, len(pages)), fill=(20, 20, 20), font=F)
        for n, (r, a, b) in enumerate(tiles):
            X = (n % cols) * cw + 4; Y = 18 + (n // cols) * ch
            dr.text((X, Y), '%s  (%d contas mudam)' % (r['name'][:34], r['delta']), fill=(20, 20, 20), font=F); im.paste(a, (X, Y + 14)); im.paste(b, (X + a.width + 10, Y + 14))
        im.save(os.path.join(HERE, 'out', 'ramp_cand_%02d.png' % pi))
    print(len(pages), 'folhas: tools/out/ramp_cand_NN.png')


if __name__ == '__main__':
    main()
