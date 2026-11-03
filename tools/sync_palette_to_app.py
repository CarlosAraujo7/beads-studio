"""Copia a paleta de tools/data/palette.json para dentro do index.html (bloco entre /*PAL-BEGIN*/ e /*PAL-END*/) e garante que o
TPL_LEGEND do templates.js tenha as 120 letras (o app precisa delas para gravar moldes com as cores novas).

uso:  python tools/sync_palette_to_app.py        (depois de mexer em data/palette.json; aumente o `var b` do index.html se o templates.js mudou)

O ÍNDICE de cada cor no app (1..120) é a posição nesta lista e é o que os desenhos salvos guardam: as 24 primeiras NUNCA mudam de lugar.
"""
import os, re, sys, json
SP = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SP)
sys.path.insert(0, SP)
import palette as P
import tplfile

BEGIN, END = '/*PAL-BEGIN*/', '/*PAL-END*/'
html_path = os.path.join(ROOT, 'index.html')
html = open(html_path, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in html else '\n'

rows = ',\n'.join('  [%s,%s,%s,%s]' % (json.dumps(c['code']), json.dumps(c['name'], ensure_ascii=False), json.dumps(c['hex']), json.dumps(c.get('hex_foto', c['hex']))) for c in P.ALL)
VIVID = json.load(open(os.path.join(SP, 'data', 'palette.json'), encoding='utf-8')).get('vivacidade', 1.0)
est = ', '.join(json.dumps(c['code']) for c in P.ALL if c['est'])
block = (f"{BEGIN}\n"
         "/* Paleta Pindou de 120 cores — gerada por tools/sync_palette_to_app.py a partir de tools/data/palette.json.\n"
         "   As 24 primeiras são as do kit antigo (ordem da tabela impressa); o ÍNDICE (1..120) é o que o desenho guarda: não reordene. */\n"
         f"const DEFAULT_PALETTE = [\n{rows}\n];\n"
         f"/* cores novas cujo hex foi ESTIMADO da foto do anúncio (marcadas com ~ em Ajustar cores) */\n"
         f"const VIVID_DEFAULT = {int(round(VIVID * 100))};   /* vivacidade padrão (%): o 3º valor de cada cor já vem com ela; o 4º é a medida crua da foto (100%) */\n"
         f"/* contas que na prática são OUTRA (o H12 é o mesmo creme da A1): não aparecem para escolher e nunca são destino de troca de cores; os moldes antigos que tinham H12 já foram trocados */\n"
         f"const ALIAS_OF = {json.dumps({c['code']: c['alias'] for c in P.ALL if c.get('alias')})};\n"
         f"const EST_CODES = new Set([{est}]);\n"
         f"{END}")
block = block.replace('\n', nl)
if BEGIN in html:
    html = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda m: block, html, flags=re.S)
else:
    m = re.search(r'const DEFAULT_PALETTE = \[.*?\n\];', html, re.S)
    if not m: sys.exit('bloco DEFAULT_PALETTE não encontrado')
    html = html[:m.start()] + block + html[m.end():]
open(html_path, 'w', encoding='utf-8', newline='').write(html)
print('index.html: %d cores' % len(P.ALL))

# templates.js: legenda com as 120 letras (acrescenta as que faltam; só troca a linha do TPL_LEGEND — moldes, TPL_BAKED e o resto ficam como estão)
tpath = os.path.join(ROOT, 'templates.js')
text = open(tpath, encoding='utf-8', newline='').read()
m = re.search(r'window\.TPL_LEGEND\s*=\s*(\{.*?\});', text, re.S)
legend = json.loads(m.group(1))
missing = {l: c for l, c in P.LEGEND.items() if l not in legend}
if missing:
    legend.update(missing)
    tplfile.backup(tpath)
    text = text[:m.start()] + 'window.TPL_LEGEND = ' + json.dumps(legend, ensure_ascii=False) + ';' + text[m.end():]
    open(tpath, 'w', encoding='utf-8', newline='').write(text)
    print('templates.js: legenda ganhou %d letras' % len(missing))
else:
    print('templates.js: legenda já tem as 120 letras')
