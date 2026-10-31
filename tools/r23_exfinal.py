"""Remessa 23 (39 imagens). Rode com a paleta de 120 cores:  BEADPAL=120 python tools/r23_exfinal.py [filtro...] [--grupo graf|spr|senapapa|ill] [--nobig] [--merge] [--rule] [--H 520]
   -> data/final25_120.json (1 placa) + data/final25_multi_120.json ("(grande)").
Reaproveita os auxiliares do r22_exfinal.py (gráficos com legenda conferida, renders Senapapa, ilustrações convert5 + irmão grande, folhas de conferência com fundo roxo).
Pedido do usuário (2026-10-30): repetidas entram (nome "(versão 2)" se colidir) e categoria nova leva ícone-miniatura (CAT_MINI_PICK do index.html)."""
import os, sys, json
os.environ['REMNUM'] = '23'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import numpy as np
import r5, r6, outline as O, illus
import r22_exfinal as R
import weak_cm as WC
import weak_fix as WF
from palette import sfx
from PIL import Image
E = r6.exact6
lg = R.lg
F = r6.FILES
CH, WH, ST, NONE = R.CH, R.WH, R.ST, R.NONE


def CM_BLOND2(rgb, L, letter, is_black):
    """cabelo LOIRO claro (Beatrice, Loid): o amarelo pálido (matiz 40-66, sat >= 0,12; ou 32-40 com sat >= 0,26) caía na trava de pele do near120 e no pale_skin e virava rosa/pele: vai para o amarelo mais próximo SEM a trava"""
    import colorsys
    h, sat, v = colorsys.rgb_to_hsv(*(np.array(rgb, float) / 255.0)); h *= 360
    if v >= 0.55 and ((40 <= h <= 66 and sat >= 0.12) or (32 <= h < 40 and sat >= 0.26)): return r5.near120(tuple(rgb), skin=False)
    return None


def CM23(rgb, L, letter, is_black): return CM_BLOND2(rgb, L, letter, is_black) or R.CM_PURPLE(rgb, L, letter, is_black)


CH = dict(CH, center_map=CM23)


def mask_paper(rgb):
    """desenho sobre papel quadriculado (C.C. do XVHDL): cinza/branco NEUTRO e não escuro (papel, linhas finas e grossas da grade) vira fundo, mesmo sem ligação com a borda; pele clara (sat >= 0,05) e traço preto ficam"""
    f = rgb.astype(np.float32); mx = f.max(axis=2); mn = f.min(axis=2)
    return ((mx - mn) / np.maximum(mx, 1) < 0.05) & (mx > 105)


def size_of(i): return Image.open(F[i]).size


CFG = []
# ---------------------------------------------------------------- gráficos e sprites (cópia exata)
_w30, _h30 = size_of(30)
CFG += [
 ('Alphonse Elric com gato (pixel, gráfico)', 'Fullmetal Alchemist', 17, lambda: E(17, post=lg), 'graf'),
 ('Kratos (God of War, chibi, gráfico)', 'God of War', 24, lambda: E(24, post=lg), 'graf'),
 ('Darkness (KonoSuba, gráfico)', 'KonoSuba', 25, lambda: E(25, crop=(1, 38, 1, 30), colmap=[((249, 229, 163), 14, 'j'), ((252, 242, 186), 14, 'j')], post=lg), 'graf'),
 ('Aqua (KonoSuba, gráfico)', 'KonoSuba', 30, lambda: E(30, crop_img=(14, 14, _w30 - 14, _h30 - 14), post=lg), 'graf'),
 ('Patinho de guarda-chuva (pixel, versão 2)', 'Animais', 18, lambda: R.pix_graph(18, dict(px=35.97, py=36.04, ox=56.98, oy=56.67, W=27, H=36),
        'H7:196 A4:183 C5:89 D3:55 C8:32 F5:26 A7:24 D2:10 C6:5 C7:5 D15:3 H4:2 A8:2 A15:1 B17:1 C15:1 C16:1 F7:1 M12:1', kit=True, ring=True, name='Patinho (versão 2)'), 'graf'),
 ('Kratos (God of War, pixel, corpo inteiro)', 'God of War', 20, lambda: E(20, achro=70, post=lg), 'spr'),
 ('Kratos (God of War, pixel, em pé)', 'God of War', 22, lambda: E(22, post=lg), 'spr'),
]
for _k, _n in enumerate(['Edward Elric (pixel, sprite)', 'Alphonse Elric (pixel, sprite)']):
    CFG.append((_n, 'Fullmetal Alchemist', 37, (lambda k=_k: R.cached('c37', lambda: R.comps(E(37, achro=150), 2, by_x=True))[k]), 'spr'))

# ---------------------------------------------------------------- renders de contas redondas (Senapapa)
SEN = [
 (6, 'Roy Mustang (Fullmetal Alchemist, contas redondas)', 'Fullmetal Alchemist', [(150, 0, 250, 36), (213, 210, 250, 250), (0, 226, 140, 250)]),
 (7, 'Fern (Frieren, contas redondas)', 'Frieren', [(158, 0, 250, 36), (203, 210, 250, 250), (0, 222, 172, 250)]),
 (13, 'Igris (Solo Leveling, contas redondas)', 'Solo Leveling', [(164, 0, 250, 36), (203, 210, 250, 250), (0, 226, 108, 250)]),
 (29, 'Beatrice (Re:Zero, contas redondas)', 'Re:Zero', [(158, 0, 250, 28), (213, 214, 250, 250), (0, 230, 98, 250)]),
]
for _i, _n, _g, _clr in SEN:
    CFG.append((_n, _g, _i, (lambda i=_i, n=_n, c=_clr: lg(R.bead_render(i, name=n, clear=c))), 'senapapa'))

# ---------------------------------------------------------------- ilustrações (convert5) + irmão grande
ILL = [
 ('C.C. (Code Geass, retrato)', 'Code Geass', 0, dict(CH), 4, None),
 ('Alucard (Hellsing, chibi, pistolas)', 'Hellsing', 1, dict(CH, fix=WF.fx('alucard_pistolas'), fixg=WF.fx('alucard_pistolas', True)), 4, None),
 ('Snoopy de Demolidor (chibi)', 'Outros', 2, dict(CH), 4, None),
 ('Beatrice (Re:Zero, chibi)', 'Re:Zero', 3, dict(CH), 4, None),
 ('Alucard (Hellsing, chibi, sentado)', 'Hellsing', 4, dict(CH, center_map=WC.combo(WC.CM_BROWN, CM23), fix=WF.fx('alucard_sentado'), fixg=WF.fx('alucard_sentado', True)), 4, None),
 ("Elias Ainsworth (The Ancient Magus' Bride, chibi, adesivo)", "The Ancient Magus' Bride", 5, dict(CH, **WH, thr=205, peel=1.5), 4, None),
 ('Gokudera Hayato (Katekyo Hitman Reborn, chibi)', 'Katekyo Hitman Reborn', 8, dict(CH, bg='flat', tol=60), 4, None),
 ('Luva de Roy Mustang (Fullmetal Alchemist, adesivo)', 'Fullmetal Alchemist', 9, dict(CH, thr=205, peel=2.0, fix=WF.fx('luva'), fixg=WF.fx('luva', True)), 4, None),
 ('Frieren (chibi, cajado)', 'Frieren', 10, dict(CH), 4, None),
 ('Lucy Heartfilia (Fairy Tail, chibi)', 'Fairy Tail', 11, dict(CH), 4, None),
 ('Emilia (Re:Zero, chibi, adesivo)', 'Re:Zero', 12, dict(CH, **ST, fix=WF.fx('emilia'), fixg=WF.fx('emilia', True)), 4, None),
 ('C.C. (Code Geass, chibi, versão 2)', 'Code Geass', 14, dict(CH, fix=WF.fx('cc_chibi'), fixg=WF.fx('cc_chibi', True)), 4, None),
 ('Snorlax de Batman (Pokémon)', 'Pokémon', 15, dict(CH, thr=205, peel=1.0), 4, None),
 ('Loid Forger (Spy x Family, chibi)', 'Spy x Family', 16, dict(CH), 4, None),
 ('C.C. (Code Geass, desenho sobre a grade)', 'Code Geass', 19, dict(CH, mask=mask_paper, clear=[(395, 728, 672, 772)]), 4, (58, 0, 736, 905)),
 ('Po (Kung Fu Panda, corpo inteiro)', 'Kung Fu Panda', 21, dict(CH, **WH), 4, None),
 ('Panda (Kung Fu Panda, chibi, adesivo)', 'Kung Fu Panda', 23, dict(CH, **WH), 4, None),
 ('Yor Forger (Spy x Family, chibi)', 'Spy x Family', 26, dict(CH), 4, None),
 ('Ceifador de lanterna (adesivo)', 'Outros', 27, dict(CH, **ST), 4, None),
 ('Po (Kung Fu Panda, chutando)', 'Kung Fu Panda', 28, dict(CH, **WH, noshadow=True), 4, None),
 ('Boneca de cabelo listrado (chibi)', 'Outros', 31, dict(CH), 4, None),
 ('Kallen Stadtfeld (Code Geass, chibi)', 'Code Geass', 32, dict(CH), 4, None),
 ('Hibari Kyoya (Katekyo Hitman Reborn, chibi)', 'Katekyo Hitman Reborn', 33, dict(CH, fix=WF.fx('hibari'), fixg=WF.fx('hibari', True)), 4, None),
 ('Stark (Frieren, chibi)', 'Frieren', 34, dict(CH), 4, None),
 ('Fern (Frieren, chibi, adesivo)', 'Frieren', 35, dict(CH, **ST), 4, None),
 ('Alucard (Hellsing, chibi, adesivo)', 'Hellsing', 36, dict(CH, thr=232, fix=WF.fx('alucard_adesivo'), fixg=WF.fx('alucard_adesivo', True)), 4, None),
 ('Happy (Fairy Tail)', 'Fairy Tail', 38, dict(CH, **WH), 4, None),
]
NOSKIN23 = ('Snoopy', 'Snorlax', 'Panda', 'Po (', 'Happy', 'Ceifador', 'Kratos', 'Luva', 'Alphonse', 'Elias')


def _skin(n): return not any(k in n for k in NOSKIN23)


for _n, _g, _i, _kw, _pl, _box in ILL:
    CFG.append((_n, _g, _i, (lambda i=_i, kw=_kw, b=_box, sk=_skin(_n): R.ill(i, kw, box=b, skin=sk)), 'ill', _pl, _box, _kw))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--H' in sys.argv: args.remove(sys.argv[sys.argv.index('--H') + 1])
    grupo = None
    if '--grupo' in sys.argv:
        grupo = sys.argv[sys.argv.index('--grupo') + 1]; args = [a for a in args if a != grupo]
    one = []; multi = []; sheet_items = []; big_items = []
    for it in CFG:
        n, g, idx, fn, grp = it[:5]
        if grupo and grp != grupo: continue
        if args and not any(a in n for a in args): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g)
            r = fn(); one.append((n, g, r)); sheet_items.append((f'{idx}: {n} {len(r[0])}x{len(r)}', R.source_img(idx, it[6] if len(it) > 6 else None), r))
            if grp == 'ill' and it[5] and '--nobig' not in sys.argv:
                b = R.ill(idx, it[7], plates=it[5], box=it[6], skin=_skin(n))
                multi.append((n + ' (grande)', g, b, {'plates': R.plates_of(b)})); big_items.append((f'{idx}: {n} (grande) {len(b[0])}x{len(b)}', R.source_img(idx, it[6]), b))
            elif R.plates_of(r) > 1: multi.append((n + ' (grande)', g, r, {'plates': R.plates_of(r)}))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(one), 'moldes de 1 placa,', len(multi), 'grandes')
    tag = (grupo or 'all') + ('_f' if args else '')
    rl = 5 if '--rule' in sys.argv else 0
    HH = int(sys.argv[sys.argv.index('--H') + 1]) if '--H' in sys.argv else 300
    per = 8 if HH <= 340 else 4 if HH <= 620 else 2
    for k in range(0, len(sheet_items), per):
        R.pairsheet(sheet_items[k:k + per], os.path.join(OUT, f'r23_{tag}_{k // per}.png'), ruler=rl, H=HH)
    for k in range(0, len(big_items), 4):
        R.pairsheet(big_items[k:k + 4], os.path.join(OUT, f'r23_{tag}_big{k // 4}.png'), H=560)
    print('folhas', (len(sheet_items) + per - 1) // per, '| grandes', (len(big_items) + 3) // 4)
    if '--merge' in sys.argv:
        for fn, new_ in (('final25', one), ('final25_multi', multi)):
            if not new_: continue
            pth = os.path.join(SP, 'data', fn + sfx() + '.json')
            old_ = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) else []
            by = {x[0]: list(x) for x in new_}
            old_ = [by.pop(x[0]) if x[0] in by else x for x in old_] + list(by.values())
            json.dump(old_, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
        print('mesclado em final25 / final25_multi')
    if not args and not grupo:
        json.dump(one, open(os.path.join(SP, 'data', 'final25' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(multi, open(os.path.join(SP, 'data', 'final25_multi' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print('gravados final25 / final25_multi')
