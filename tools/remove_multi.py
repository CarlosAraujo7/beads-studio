"""Apaga do catálogo os moldes que ocupam MAIS DE UMA PLACA de 50x50 (pedido do dono no chat, 2026-11-04: "era pra tirar as abas de moldes com mais de uma placa e também para remover
os moldes com mais de uma placa, o sistema só deve ter moldes de 1 placa e 3d"). É a exceção à LEI DO CATÁLOGO que ele mesmo pediu, com o conjunto definido por ele.
Os nomes vão para a lista de excluídos (TPL_REMOVED), como faz o app, para nada os trazer de volta. Grava de 40 em 40 (limite da trava) com UMA cópia inteira antes.
uso:  BEADS_ALTERAR_EXISTENTES=1 python tools/remove_multi.py --autorizado          (sem --autorizado só mostra o que faria)"""
import os, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tplfile

PATH = os.path.join(os.path.dirname(HERE), 'templates.js')


def plates(rows): return -(-max(len(x) for x in rows) // 50) * -(-len(rows) // 50)


def main():
    d = tplfile.parse(PATH)
    multi = [t for t in d['items'] if plates(t['rows']) > 1]
    print('moldes:', len(d['items']), '| de mais de 1 placa:', len(multi))
    for t in multi: print('  ', plates(t['rows']), 'placas |', len(t['rows'][0]), 'x', len(t['rows']), '|', t['name'])
    if '--autorizado' not in sys.argv:
        print('(só mostrando: rode com --autorizado e BEADS_ALTERAR_EXISTENTES=1 para apagar)'); return
    if os.environ.get('BEADS_ALTERAR_EXISTENTES') != '1': raise SystemExit('falta BEADS_ALTERAR_EXISTENTES=1')
    bk = os.path.join(HERE, 'backups', 'pre-remove-multi.js')
    if not os.path.exists(bk): shutil.copy(PATH, bk); print('cópia inteira em', bk)
    ids = [t['id'] for t in multi]
    for k in range(0, len(ids), tplfile.MAX_POR_VEZ):
        lote = set(ids[k:k + tplfile.MAX_POR_VEZ])
        d = tplfile.parse(PATH)
        gone = [t for t in d['items'] if t['id'] in lote]
        items = [t for t in d['items'] if t['id'] not in lote]
        removed = list(d.get('removed') or [])
        for t in gone:
            if t['name'] not in removed: removed.append(t['name'])
        tplfile.write(PATH, d['legend'], d['cfg'], items, removed, allow=lote)
        print('lote gravado:', len(gone), 'apagados | restam', len(items))
    import make_remessas; make_remessas.write(); print('remessas.js atualizado')


if __name__ == '__main__':
    main()
