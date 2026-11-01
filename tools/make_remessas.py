"""Gera remessas.js: de qual remessa veio cada molde do catálogo (tela "Novos moldes" do app, CLAUDE.md §3).
  python tools/make_remessas.py
Fica FORA do templates.js de propósito: o app regrava o templates.js inteiro em "Gravar no catálogo", e este arquivo só LÊ o catálogo; nunca o altera.
O add_templates.py chama isto sozinho depois de gravar. A remessa N (N >= 5) é data/final{N+2}[_multi][_120].json; as cópias _replace e _revisao não contam (são revisões).
O id do molde nasce do nome de origem, então um molde renomeado no app continua achado pelo id. Molde que ele excluiu não entra."""
import os, re, sys, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import tplfile
OUT = os.path.join(ROOT, 'remessas.js')
RX = re.compile(r'^final(\d+)(_multi)?(_120)?\.json$')


def build(templates=None):
    items = tplfile.parse(templates or os.path.join(ROOT, 'templates.js'))['items']
    by_name = {t['name']: t['id'] for t in items}; ids = {t['id'] for t in items}
    files = {}
    for f in glob.glob(os.path.join(HERE, 'data', 'final*.json')):
        m = RX.match(os.path.basename(f))
        if m and int(m.group(1)) >= 7: files.setdefault(int(m.group(1)) - 2, []).append(f)
    seen = set(); out = []
    for n in sorted(files):                         # da mais antiga para a mais nova: molde repetido fica na primeira em que entrou
        got = []
        for f in sorted(files[n]):
            for it in json.load(open(f, encoding='utf-8')):
                i = by_name.get(it[0]) or tplfile.slug(it[0])
                if i in ids and i not in seen: seen.add(i); got.append(i)
        if got: out.append({'n': n, 'ids': got})
    out.reverse()
    return out


def write(templates=None):
    data = build(templates)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Gerado por tools/make_remessas.py: de qual remessa veio cada molde. Não edite à mão.\nwindow.REMESSAS=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    return data


if __name__ == '__main__':
    d = write()
    print('\n'.join('remessa %d: %d moldes' % (b['n'], len(b['ids'])) for b in d))
