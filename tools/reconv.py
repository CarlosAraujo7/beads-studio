"""REFAZ UMA CONVERSÃO COM A PALETA DE HOJE, SEM GRAVAR NADA (2026-11-03): roda o item do CFG de tools/rN_exfinal.py (a mesma imagem e os mesmos parâmetros da época) com BEADPAL=120 e devolve as linhas.
Serve para ver o que o conversor escolheria HOJE para cada cor da imagem original (a conta real mais parecida) e comparar com o molde que está no catálogo (que veio da paleta antiga).
uso:  python tools/reconv.py REM "Nome exato do molde" [--json saida.json]
Cada script rN_exfinal tem forma própria de CFG: os de tupla (nome, série, função) e os de (nome, série, idx, função, grupo, ...) são reconhecidos; o resto falha com mensagem."""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ['BEADPAL'] = '120'


def main():
    a = sys.argv[1:]
    rem, name = a[0], a[1]
    mod = importlib.import_module('r%s_exfinal' % rem if rem.isdigit() else 'r_%s' % rem)       # número = rN_exfinal; texto = r_<texto> (ex.: outros -> r_outros)
    import r5
    cfg = [it for it in mod.CFG if it[0] == name]
    if not cfg: sys.exit('nome não está no CFG de r%s_exfinal: %s' % (rem, name))
    it = cfg[0]; fn = next((x for x in it[1:] if callable(x)), None)
    if fn is None: sys.exit('item sem função: %r' % (it[:3],))
    r5.SKIN_ON = r5.skin_for(it[0], it[1] if isinstance(it[1], str) else '')
    rows = fn()
    print(name, len(rows[0]), 'x', len(rows), '| skin guard:', r5.SKIN_ON)
    if '--json' in a: json.dump(rows, open(a[a.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
