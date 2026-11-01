"""ÚNICA forma de alterar moldes que já estão no catálogo (CLAUDE.md §4.9): uma lista curta, por id, de moldes que o usuário pediu.
    from retoque import gravar
    gravar({'id-do-molde': linhas_novas}, esperado={'id-do-molde': linhas_que_eu_olhei})
Só troca se o molde ainda é exatamente o que eu olhei (`esperado`); se ele editou no app nesse meio-tempo, pula e avisa."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault('BEADPAL', '120')
import tplfile, loose
import outline as O
T = os.path.join(ROOT, 'templates.js')


def atual(i): return next(t for t in tplfile.parse(T)['items'] if t['id'] == i)['rows']


def gravar(trocas, esperado):
    d = tplfile.parse(T); it = {t['id']: t for t in d['items']}; allow = set(); feitos = []; pulados = []
    for i, rows in trocas.items():
        t = it.get(i)
        if t is None or t['rows'] != esperado[i]: pulados.append(i); continue
        if len({len(r) for r in rows}) != 1: raise ValueError('larguras: ' + i)
        rows = O.trim(loose.fix_loose(rows))
        bad = {c for r in rows for c in r if c != '.' and c not in d['legend']}
        if bad: raise ValueError('letras: %s %s' % (i, bad))
        t['rows'] = rows; allow.add(i); feitos.append(t['name'])
    if feitos: tplfile.write(T, d['legend'], d['cfg'], list(d['items']), d.get('removed'), allow=allow)
    print('trocados:', feitos); print('pulados (editados ou excluídos por ele):', pulados)
