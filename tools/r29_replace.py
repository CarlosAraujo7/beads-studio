"""Troca no catálogo os moldes da REMESSA 29 pela versão refeita com o convert6 (pedido do dono no chat, 2026-11-04: "reveja essa remessa inteira… ficou bem ruim").
Só a remessa 29 e só os moldes que ainda estão EXATAMENTE como eu acrescentei (se ele ajustou ou excluiu algum no app, fica como ele deixou: LEI DO CATÁLOGO). Mesmo id, nome,
categoria e posição; só as linhas mudam. Grava de 40 em 40 (limite da trava) com UMA cópia inteira antes (tools/backups/pre-r29-v6.js).
  BEADS_ALTERAR_EXISTENTES=1 python tools/r29_replace.py [--dry]        aplica (sem a variável a trava recusa)
  BEADS_ALTERAR_EXISTENTES=1 python tools/r29_replace.py --revert       volta à 1ª versão (só nos que ainda estão como esta ferramenta deixou)
Entradas: data/final31_raw_v5_120.json + data/final31_v5_120.json (1ª versão: nomes do CFG e nomes do catálogo, mesma ordem) e data/final31_raw_120.json (versão nova, nomes do CFG).
2ª revisão (2026-11-04, os moldes que ele citou): --de data/final31_raw_v6_120.json = o que está no catálogo agora (nomes do CFG); --copia NOME = cópia inteira antes (nunca sobrescreve uma que existe).
  BEADS_ALTERAR_EXISTENTES=1 python tools/r29_replace.py --de data/final31_raw_v6_120.json --copia pre-r29-rev2.js [--dry | --revert]"""
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tplfile, loose

PATH = os.path.join(os.path.dirname(HERE), 'templates.js')
D = os.path.join(HERE, 'data')


def pairs(de=None):
    raw5 = json.load(open(os.path.join(D, 'final31_raw_v5_120.json'), encoding='utf-8'))
    cat5 = json.load(open(os.path.join(D, 'final31_v5_120.json'), encoding='utf-8'))
    new = {x[0]: x[2] for x in json.load(open(os.path.join(D, 'final31_raw_120.json'), encoding='utf-8'))}
    out = []
    for (ncfg, _, r_a), (ncat, _, r_b) in zip(raw5, cat5):
        assert r_a == r_b, ncfg
        nr = new.get(ncfg)
        if nr is None: continue
        if loose.loose_count(nr): nr = loose.fix_loose(nr)
        old = r_b
        if de is not None:                                    # o "de" é outra versão (nomes do CFG): o que esta ferramenta gravou da última vez
            old = de.get(ncfg)
            if old is None: continue
            if loose.loose_count(old): old = loose.fix_loose(old)
        out.append((ncat, old, nr))
    return out


def main():
    revert = '--revert' in sys.argv; dry = '--dry' in sys.argv
    de = None; copia = None
    if '--de' in sys.argv:
        f = sys.argv[sys.argv.index('--de') + 1]; f = f if os.path.isabs(f) else (os.path.join(HERE, f) if os.path.exists(os.path.join(HERE, f)) else os.path.abspath(f))
        de = {x[0]: x[2] for x in json.load(open(f, encoding='utf-8'))}
    if '--copia' in sys.argv: copia = sys.argv[sys.argv.index('--copia') + 1]
    pp = pairs(de)
    if revert: pp = [(n, nr, o) for n, o, nr in pp]           # de -> para invertido
    d = tplfile.parse(PATH); by = {t['name']: t for t in d['items']}
    todo = [(n, o, nr) for n, o, nr in pp if n in by and by[n]['rows'] == o and nr != o]
    same = [n for n, o, nr in pp if n in by and nr == o]
    edited = [n for n, o, nr in pp if n in by and by[n]['rows'] != o and by[n]['rows'] != nr]
    done = [n for n, o, nr in pp if n in by and by[n]['rows'] == nr and nr != o]
    gone = [n for n, o, nr in pp if n not in by]
    big = [(n, len(nr[0]), len(nr)) for n, o, nr in todo if len(nr[0]) > 50 or len(nr) > 50]
    print(f'remessa 29: {len(pp)} | a trocar: {len(todo)} | iguais (gráficos fiéis): {len(same)} | já trocados: {len(done)} | ajustados por ele (ficam): {len(edited)} {edited[:6]} | excluídos por ele: {len(gone)}')
    if big: raise SystemExit('maior que 50: %s' % big)
    if dry or not todo: print('(nada gravado)' if dry else 'nada a trocar'); return
    bk = os.path.join(HERE, 'backups', copia or ('pre-r29-v6.js' if not revert else 'pre-r29-v6-revert.js'))
    if os.path.exists(bk):                                    # nunca sobrescreve uma cópia antiga (ela é o caminho de volta de outra revisão)
        import datetime; root, ext = os.path.splitext(bk); bk = root + datetime.datetime.now().strftime('-%Y%m%d-%H%M%S') + ext
    shutil.copy(PATH, bk); print('cópia inteira em', bk)
    for k in range(0, len(todo), tplfile.MAX_POR_VEZ):
        lote = {n: (o, nr) for n, o, nr in todo[k:k + tplfile.MAX_POR_VEZ]}
        d = tplfile.parse(PATH); allow = set()
        for t in d['items']:
            if t['name'] in lote and t['rows'] == lote[t['name']][0]:
                t['rows'] = lote[t['name']][1]; allow.add(t['id'])
        tplfile.write(PATH, d['legend'], d['cfg'], d['items'], d.get('removed'), allow=allow)
        print('lote gravado:', len(allow))


if __name__ == '__main__':
    main()
