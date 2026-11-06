"""Compara dois catálogos (templates.js e/ou cópias de tools/backups/): só LEITURA.
    python tools/cat_compare.py ANTES.js DEPOIS.js [--nomes]
Mostra: quantos moldes cada um tem; os que sumiram (excluídos), os acrescentados, os que mudaram de DESENHO, de NOME e de CATEGORIA; se a ordem dos moldes em comum é a mesma;
as diferenças na lista de excluídos (TPL_REMOVED) e na organização (TPL_CATS_CFG: ordem, nomes, ícones, categorias criadas, escondidas, 'Minha ordem' etc.).
Serve para o registro da LEI DO CATÁLOGO (CLAUDE.md: cada gravação dele pelo app vira uma linha) e para conferir, depois de acrescentar uma remessa,
que os moldes antigos ficaram idênticos (id, nome, categoria, grupo e linhas) e na mesma ordem.
Com --nomes lista os nomes de cada grupo (senão só os primeiros 8)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tplfile


def compare(a_path, b_path, nomes=False, out=print):
    A = tplfile.parse(a_path); B = tplfile.parse(b_path)
    ia = {t['id']: t for t in A['items']}; ib = {t['id']: t for t in B['items']}
    lim = None if nomes else 8
    res = {}

    def show(titulo, lst):
        out(f'{titulo}: {len(lst)}' + (('  ' + ' | '.join(lst[:lim]) + (' …' if lim and len(lst) > lim else '')) if lst else ''))

    out(f'ANTES : {a_path}  ({len(A["items"])} moldes, carimbo {A.get("baked")})')
    out(f'DEPOIS: {b_path}  ({len(B["items"])} moldes, carimbo {B.get("baked")})')
    gone = [t['name'] for t in A['items'] if t['id'] not in ib]
    new = [t['name'] for t in B['items'] if t['id'] not in ia]
    rows = [t['name'] for t in A['items'] if t['id'] in ib and t['rows'] != ib[t['id']]['rows']]
    names = [f"{t['name']} -> {ib[t['id']]['name']}" for t in A['items'] if t['id'] in ib and t['name'] != ib[t['id']]['name']]
    cats = [f"{t['name']}: {t['cat']} -> {ib[t['id']]['cat']}" for t in A['items'] if t['id'] in ib and t['cat'] != ib[t['id']]['cat']]
    groups = [t['name'] for t in A['items'] if t['id'] in ib and t['group'] != ib[t['id']]['group'] and t['cat'] == ib[t['id']]['cat']]
    show('excluídos (somem)', gone); show('acrescentados', new); show('desenho mudou', rows); show('nome mudou', names); show('categoria mudou', cats)
    if groups: show('só o "group" mudou (mesma categoria)', groups)
    common_a = [t['id'] for t in A['items'] if t['id'] in ib]; common_b = [t['id'] for t in B['items'] if t['id'] in ia]
    same_order = common_a == common_b
    out('ordem dos moldes em comum: ' + ('IGUAL' if same_order else 'DIFERENTE'))
    ra, rb = set(A.get('removed') or []), set(B.get('removed') or [])
    show('nomes que entraram na lista de excluídos', sorted(rb - ra)); show('nomes que SAÍRAM da lista de excluídos', sorted(ra - rb))
    ca, cb = A.get('cfg') or {}, B.get('cfg') or {}
    difs = []
    for k in sorted(set(ca) | set(cb)):
        if ca.get(k) != cb.get(k):
            va, vb = ca.get(k), cb.get(k)
            if isinstance(va, dict) and isinstance(vb, dict):
                ks = [x for x in sorted(set(va) | set(vb)) if va.get(x) != vb.get(x)]
                difs.append(f'{k} ({len(ks)} chaves: {", ".join(map(str, ks[:6]))}{" …" if len(ks) > 6 else ""})')
            elif isinstance(va, list) and isinstance(vb, list):
                difs.append(f'{k} (lista {len(va)} -> {len(vb)})')
            else:
                difs.append(f'{k} ({va!r} -> {vb!r})')
    out('organização (TPL_CATS_CFG) diferente em: ' + (', '.join(difs) if difs else 'nada'))
    res.update(gone=gone, new=new, rows=rows, names=names, cats=cats, same_order=same_order, cfg=difs, rem_in=sorted(rb - ra), rem_out=sorted(ra - rb))
    return res


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2: print(__doc__); sys.exit(1)
    compare(args[0], args[1], nomes='--nomes' in sys.argv)
