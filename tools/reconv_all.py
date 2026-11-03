"""REFAZ, COM A PALETA DE HOJE, TODAS AS CONVERSÕES QUE O PIPELINE SABE REPRODUZIR (2026-11-03). NÃO GRAVA NADA NO CATÁLOGO: cada molde vai para tools/out/rc_all/<script>/<n>.json
{name, series, rows} (a conta REAL mais parecida com a cor de cada ponto da imagem original, com a trava de pele da época). Serve para a auditoria (tools/rc_audit.py).
uso:  python tools/reconv_all.py [--jobs 6] [script ...]        (sem script: todos os rN_exfinal e o r_outros)
      python tools/reconv_all.py --one r20_exfinal            (um script só, neste processo; é o que cada trabalhador roda)
Cada script roda num processo à parte (o r6 lê REMNUM uma vez só). Log: tools/out/rc_all/log_<script>.txt. Pode ser interrompido e retomado: o que já tem arquivo é pulado."""
import os, sys, json, re, glob, subprocess, time, importlib, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
RAMP = os.environ.get('DARKRAMP') == '1'                         # 2026-11-03: reconverte com a rampa de cinzas (darkramp.py) para achar os moldes pretos que melhoram; saída em out/rc_ramp
OUT = os.path.join(HERE, 'out', 'rc_ramp' if RAMP else 'rc_all')


def slug(n): return re.sub(r'[^a-z0-9]+', '-', n.lower().encode('ascii', 'ignore').decode()).strip('-')[:70]


def run_one(script):
    os.environ['BEADPAL'] = '120'
    d = os.path.join(OUT, script); os.makedirs(d, exist_ok=True)
    mod = importlib.import_module(script)
    import r5
    if RAMP:
        import illus5, darkramp
        _orig = illus5.convert5

        def _patched(*a, **k):
            k['center_map'] = darkramp.ramp(lo=14.0, mid2=26.5, base=k.get('center_map')); k.setdefault('hl_gain', 1.0)
            return _orig(*a, **k)
        illus5.convert5 = _patched
        import illus as _illus
        _oc = _illus._cells

        def _pc(*a, **k):                      # convert4 / convert (remessas 13-18): a rampa vale para o escuro que não é contorno (mais alto, porque a conta é a MÉDIA dos pontos escuros)
            k.setdefault('dark_map', darkramp.ramp(lo=20.0, hi=44.0)); return _oc(*a, **k)
        _illus._cells = _pc
    cfg = getattr(mod, 'CFG', None)
    if cfg is None: print('sem CFG'); return
    ok = bad = skip = 0
    for k, it in enumerate(cfg):
        try:
            name = it[0]
            fn = next((x for x in it[1:] if callable(x)), None)
            if fn is None and isinstance(name, str) and len(it) >= 4 and isinstance(it[2], int) and isinstance(it[3], dict) and hasattr(mod, 'conv'):       # r15-r18: ilustração = conv(idx, **style_defaults(nome, kw))
                import illus; idx, kw = it[2], it[3]; fn = (lambda idx=idx, kw=kw, name=name: mod.conv(idx, **illus.style_defaults(name, kw)))
            if fn is None or not isinstance(name, str): skip += 1; continue
            path = os.path.join(d, '%03d_%s.json' % (k, slug(name)))
            if os.path.exists(path): ok += 1; continue
            series = it[1] if isinstance(it[1], str) else ''
            r5.SKIN_ON = r5.skin_for(name, series)
            t0 = time.time(); rows = fn()
            if not isinstance(rows, list) or not rows or not isinstance(rows[0], str): skip += 1; continue
            json.dump({'name': name, 'series': series, 'rows': rows}, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
            ok += 1; print('ok %3d %-50s %dx%d  %.1fs' % (k, name[:50], len(rows[0]), len(rows), time.time() - t0), flush=True)
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt): raise
            bad += 1; print('ERRO %3d %s: %r' % (k, it[0] if it else '?', e), flush=True)
    print('FIM %s: %d ok, %d com erro, %d pulados' % (script, ok, bad, skip), flush=True)


def main():
    a = sys.argv[1:]
    if '--one' in a: run_one(a[a.index('--one') + 1]); return
    jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else 6
    scripts = [x for x in a if not x.startswith('--') and not x.isdigit()]
    if not scripts:
        scripts = sorted([os.path.basename(f)[:-3] for f in glob.glob(os.path.join(HERE, 'r[0-9]*_exfinal.py'))], key=lambda s: int(re.match(r'r(\d+)_', s).group(1)))
        scripts += ['r_outros']
    os.makedirs(OUT, exist_ok=True)
    pending = list(scripts); running = []
    while pending or running:
        while pending and len(running) < jobs:
            s = pending.pop(0); lg = open(os.path.join(OUT, 'log_%s.txt' % s), 'w', encoding='utf-8')
            env = dict(os.environ, PYTHONIOENCODING='utf-8', BEADPAL='120', DARKRAMP='1' if RAMP else '0')
            p = subprocess.Popen([sys.executable, '-u', os.path.join(HERE, 'reconv_all.py'), '--one', s], stdout=lg, stderr=subprocess.STDOUT, env=env, cwd=HERE)
            running.append((s, p, lg)); print('começou', s, flush=True)
        for s, p, lg in list(running):
            if p.poll() is not None: lg.close(); running.remove((s, p, lg)); print('terminou', s, 'código', p.returncode, flush=True)
        time.sleep(3)
    print('TUDO PRONTO')


if __name__ == '__main__':
    main()
