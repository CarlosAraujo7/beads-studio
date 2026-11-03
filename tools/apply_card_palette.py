"""Aplica em tools/data/palette.json as cores MEDIDAS nas fotos das 5 cartelas reais do kit de 120 (tools/data/palette_cartelas.json, gerado por calibrate_cards.py --json; fotos em paleta 120/).
Mantém código, LETRA e ORDEM de cada cor (o índice 1..120 é o que os desenhos salvos guardam) e troca o hex, o nome (rótulo a partir do hex, make_palette.name_of) e est=False.
Exceções: H2 = branco puro (#FFFFFF) e H1 = TRANSPARENTE na vida real (ele mostrou a caixa de contas transparentes em 2026-11-01): mantém o hex antigo (#E4E7EA, o tom de uma conta clara sobre o branco).
É estimativa de FOTO (papel como branco, sem cartão de referência de cor): se uma cor não parecer com a conta de verdade, corrija no "Ajustar cores…" do app ou direto em palette.json.
Cópia antes: tools/backups/palette-pre-cartelas.json.   uso:  python tools/apply_card_palette.py [--dry]   (depois: python tools/sync_palette_to_app.py)"""
import os, sys, json, shutil
SP = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SP)
import make_palette as MP

if '--force' not in sys.argv:
    print('OBSOLETO (2026-11-02): apply_card_palette.py sobrescreve data/palette.json com uma paleta SUPERADA (a das contas sem tampa vale: tools/build_bead_palette2.py, CLAUDE.md 7.38). Só roda com --force.')
    sys.exit(1)

dry = '--dry' in sys.argv
pal = json.load(open(os.path.join(SP, 'data', 'palette.json'), encoding='utf-8'))
cart = json.load(open(os.path.join(SP, 'data', 'palette_cartelas.json'), encoding='utf-8'))
cols = pal['colors']
assert len(cols) == 120 and set(cart) == {c['code'] for c in cols}, 'a lista de códigos das cartelas não é a da paleta'
SPECIAL = {'H2': ('#FFFFFF', 'Branco'), 'H1': (None, 'Transparente')}
seen = set(); changes = []
new = []
for c in cols:
    hexn = SPECIAL[c['code']][0] if c['code'] in SPECIAL and SPECIAL[c['code']][0] else cart[c['code']]['hex'] if c['code'] not in SPECIAL else c['hex']
    nm = SPECIAL[c['code']][1] if c['code'] in SPECIAL else MP.name_of(hexn)
    if nm in seen: nm = f"{nm} ({c['code']})"
    seen.add(nm)
    n = dict(code=c['code'], name=nm, hex=hexn, letter=c['letter'], est=False)
    new.append(n); changes.append((c['code'], c['hex'], hexn, c['name'], nm))
print('%-4s %-9s -> %-9s  %s -> %s' % ('cód', 'antes', 'depois', 'nome antes', 'nome depois'))
for code, a, b, na, nb in changes[:24]: print('%-4s %-9s -> %-9s  %s -> %s' % (code, a, b, na, nb))
print('... (%d cores no total; %d com nome novo)' % (len(changes), sum(1 for x in changes if x[3] != x[4])))
if dry: print('(simulação: nada gravado)'); sys.exit(0)
bk = os.path.join(SP, 'backups', 'palette-pre-cartelas.json')
if not os.path.exists(bk): shutil.copy(os.path.join(SP, 'data', 'palette.json'), bk)
json.dump({'fonte': 'medido nas fotos das 5 cartelas reais do kit (paleta 120/foto-cartela-N.jpeg, 2026-11-02; balanço de branco pelo papel; CLAUDE.md §7.38). Antes: estimado da foto do anúncio.',
           'colors': new}, open(os.path.join(SP, 'data', 'palette.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('palette.json gravado; cópia antes em', bk)
