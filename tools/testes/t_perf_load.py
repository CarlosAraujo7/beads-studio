"""Perfil de CPU do carregamento da página (do navigate até a tela inicial pronta)."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
PAGE = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
async def main():
    b = B2(w=1280, h=800, port=9380); await b.start()
    try:
        await b.send('Profiler.enable'); await b.send('Profiler.setSamplingInterval', interval=200); await b.send('Profiler.start')
        t0 = time.time()
        await b.send('Page.navigate', url='http://localhost:8765/%s?x=ld%d' % (PAGE, int(time.time()) % 100000))
        for _ in range(100):
            await asyncio.sleep(0.1)
            try:
                if await b.js("document.readyState==='complete'&&!!window.TEMPLATES&&document.body.dataset.view==='home'&&!!document.querySelector('#homeNewRow .tile')"): break
            except Exception: pass
        wall = (time.time() - t0) * 1000
        prof = (await b.send('Profiler.stop'))['profile']
        nodes = {n['id']: n for n in prof['nodes']}; self_us = {}
        for sid, dt in zip(prof['samples'], prof['timeDeltas']): self_us[sid] = self_us.get(sid, 0) + dt
        agg = {}
        for nid, us in self_us.items():
            cf = nodes[nid]['callFrame']; key = '%s %s:%d' % (cf['functionName'] or '(anônima)', (cf['url'].split('/')[-1].split('?')[0] or '-'), cf['lineNumber'] + 1); agg[key] = agg.get(key, 0) + us
        tot = sum(agg.values()) or 1
        print('carregamento até a tela inicial pronta: %.0f ms (parede) | CPU amostrada %.0f ms' % (wall, tot / 1000))
        for k, us in sorted(agg.items(), key=lambda kv: -kv[1])[:16]: print('   %5.1f%%  %7.1f ms  %s' % (100 * us / tot, us / 1000, k))
    finally:
        await b.close()
asyncio.run(main())
