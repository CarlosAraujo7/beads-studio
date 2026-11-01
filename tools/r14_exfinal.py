"""Remessa 14 (49 imagens, TODAS ilustrações/artes SEM grade: chibis, retratos, adesivos). Rode: BEADPAL=120 python tools/r14_exfinal.py  -> data/final16_120.json

Conversão por illus.convert4 (até 50 contas, APROXIMADA): média só dos pontos claros da janela + contorno escuro quando a janela é >= dark_frac escura,
realce de saturação/contraste/nitidez antes e redução de paleta (14 cores) depois. Retratos/artes muito detalhados (All Might, Seiya e Shiryu em
ilustração de revista, Ikki tatuagem…) NÃO ficam reconhecíveis em 50 contas e foram deixados de fora (ver lista SKIP no fim).
"""
import os, sys, json, glob
os.environ['REMNUM'] = '14'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'out'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, SP)
import r5, outline as O, illus
from flat import render_flat
from palette import sfx
FILES = sorted(glob.glob(os.path.join(os.path.dirname(SP), 'remessas', 'remessa 14', '*.*')))
DK = dict(dark_frac=0.28, dark_L=28.0)


def drop_reds(rows):
    """apaga contas de tom vermelho/vinho/rosa (o contorno salmão-escuro do adesivo do Panda, que não é do desenho)"""
    import colorsys
    from palette import ALL
    bad = set()
    for c in ALL:
        r, g, b = [int(c['hex'][i:i + 2], 16) / 255 for i in (1, 3, 5)]
        h, s_, v = colorsys.rgb_to_hsv(r, g, b); h *= 360
        if (h <= 25 or h >= 325) and s_ >= 0.22: bad.add(c['letter'])
    return O.trim([''.join('.' if ch in bad else ch for ch in r) for r in rows])


CUR = ['']          # nome do molde em conversão (o main põe aqui antes de chamar fn()) — para illus.style_defaults


def S(idx, largest=False, **kw):
    a = dict(DK); a.update(illus.style_defaults(CUR[0], kw))
    r = illus.convert4(FILES[idx], **a)
    return r5.largest(r) if largest else r      # largest: tira pedaços soltos (restos do texto japonês, respingos do fundo)


CFG = [
 # --- Hitman Reborn
 ('Tsuna (chibi, capa preta)', 'Katekyo Hitman Reborn', lambda: S(0)),
 ('Tsuna (chibi, com luvas)', 'Katekyo Hitman Reborn', lambda: S(19)),
 ('Tsuna (chibi, chama na testa)', 'Katekyo Hitman Reborn', lambda: S(37)),
 ('Tsuna (X-Burner)', 'Katekyo Hitman Reborn', lambda: S(40)),
 ('Lambo (Hitman Reborn, chibi)', 'Katekyo Hitman Reborn', lambda: S(46)),
 # --- Cavaleiros do Zodíaco
 ('Seiya de Pégaso (chibi, capacete)', 'Cavaleiros do Zodíaco', lambda: S(18)),
 ('Seiya de Pégaso (chibi, armadura de prata)', 'Cavaleiros do Zodíaco', lambda: S(20)),
 ('Seiya de Sagitário (chibi)', 'Cavaleiros do Zodíaco', lambda: S(47)),
 ('Shun de Andrômeda (chibi, corpo inteiro)', 'Cavaleiros do Zodíaco', lambda: S(5)),
 ('Shun de Andrômeda (chibi)', 'Cavaleiros do Zodíaco', lambda: S(45)),
 ('Hyoga de Cisne (chibi)', 'Cavaleiros do Zodíaco', lambda: S(25)),
 ('Ikki de Fênix (chibi)', 'Cavaleiros do Zodíaco', lambda: S(29)),
 ('Shiryu de Dragão (chibi)', 'Cavaleiros do Zodíaco', lambda: S(38)),
 ('Shiryu de Dragão (chibi, capacete)', 'Cavaleiros do Zodíaco', lambda: S(33)),
 ('Shaka de Virgem (chibi)', 'Cavaleiros do Zodíaco', lambda: S(35)),
 # --- animes
 ('Zenitsu Agatsuma (retrato)', 'Demon Slayer', lambda: S(3)),
 ('Naruto comendo ramen', 'Naruto', lambda: S(4)),
 ('Naruto com Kurama (chibi)', 'Naruto', lambda: S(11, box=(0, 0, 330, 322))),
 ('Goku (retrato)', 'Dragon Ball', lambda: S(6, bg='flat', tol=95)),
 ('Kuririn (chibi)', 'Dragon Ball', lambda: S(43)),
 ('Panda (Jujutsu Kaisen)', 'Jujutsu Kaisen', lambda: r5.largest(drop_reds(S(9, bg='flat', tol=105)))),
 ('Luffy Gear 5 (rosto)', 'One Piece', lambda: S(10)),
 ('Chopper (One Piece)', 'One Piece', lambda: S(12)),
 ('Shoto Todoroki (retrato)', 'My Hero Academia', lambda: S(16)),
 ('Shoto Todoroki (gelo e fogo)', 'My Hero Academia', lambda: S(41)),
 ('Rukia Kuchiki (chibi)', 'Bleach', lambda: S(17)),
 ('Kirito (chibi)', 'Sword Art Online', lambda: S(27)),
 ('Asta (Black Clover, retrato)', 'Black Clover', lambda: S(34)),
 ('Tatsumaki (One Punch Man, chibi)', 'One Punch Man', lambda: S(44)),
 ('Garoto de óculos redondos (retrato)', 'Outros', lambda: S(28)),
 ('Homem de cabelo branco com chamas vermelhas (retrato)', 'Outros', lambda: S(30)),
 # --- Pokémon (textos em japonês recortados) e animais
 ('Togepi (ilustração)', 'Pokémon', lambda: S(21)),
 ('Togepi (ilustração, versão 2)', 'Pokémon', lambda: S(36, box=(175, 0, 736, 736), largest=True)),
 ('Squirtle (ilustração)', 'Pokémon', lambda: S(39, box=(175, 0, 736, 736), largest=True)),
 ('Jigglypuff (ilustração)', 'Pokémon', lambda: S(48, box=(165, 0, 736, 736), largest=True)),
 ('Gato siamês (ilustração)', 'Outros', lambda: S(24)),
]
# lidas e DEIXADAS DE FORA (não ficam reconhecíveis em 50 contas): 1 All Might (retrato de revista), 2 e 7 Seiya/Cavaleiro de Sagitário de asas/busto,
# 8 Shun de capacete rosa, 14 chibi de cabelo claro e luvas (confuso), 13 Lucario (já existe no catálogo), 22 colar do Ace em chamas, 23 Goku criança com dragão, 26 Seiya (retrato a lápis),
# 31 Shiryu com pétalas, 32 Shiryu (retrato manga), 42 Ikki tatuagem
SKIP = {11: 'Sasuke com cobra (fonte pequena demais, a cobra some; a metade de cima — Naruto com Kurama — ficou)', 1: 'All Might (retrato de revista)', 2: 'Seiya de Sagitário de asas', 7: 'Cavaleiro de Sagitário (busto)', 8: 'Shun de capacete rosa', 14: 'chibi de cabelo claro e luvas', 15: 'chapéus do Sabo e do Ace (pendente)', 13: 'Lucario (já existe)',
        22: 'colar do Ace', 23: 'Goku criança com dragão', 26: 'Seiya (retrato a lápis)', 31: 'Shiryu com pétalas', 32: 'Shiryu (retrato manga)', 42: 'Ikki tatuagem'}

if __name__ == '__main__':
    only = sys.argv[1:]
    out = []; items = []
    for n, g, fn in CFG:
        if only and not any(o in n for o in only): continue
        try:
            r5.SKIN_ON = r5.skin_for(n, g); CUR[0] = n
            r = fn(); out.append((n, g, r)); items.append((f'{n[:26]} {len(r[0])}x{len(r)}'.encode('ascii', 'replace').decode(), r))
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERRO', n, repr(e))
    print(len(out), 'templates')
    if not only: json.dump(out, open(os.path.join(SP, 'data', 'final16' + sfx() + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for k in range(0, len(items), 12):
        render_flat(items[k:k + 12], os.path.join(OUT, f'r14_x_{k // 12}' + sfx() + '.png'), scale=8, W=1900)
