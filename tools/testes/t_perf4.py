"""Perfil de CPU: pincelada no maior molde e troca Criar <-> Montar."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
async def prof_start(b):
    await b.send('Profiler.enable'); await b.send('Profiler.setSamplingInterval', interval=200); await b.send('Profiler.start')
async def prof_stop(b, label, top=14):
    prof = (await b.send('Profiler.stop'))['profile']
    nodes = {n['id']: n for n in prof['nodes']}; self_us = {}
    for sid, dt in zip(prof['samples'], prof['timeDeltas']): self_us[sid] = self_us.get(sid, 0) + dt
    agg = {}
    for nid, us in self_us.items():
        cf = nodes[nid]['callFrame']; key = '%s %s:%d' % (cf['functionName'] or '(anônima)', (cf['url'].split('/')[-1].split('?')[0] or '-'), cf['lineNumber'] + 1); agg[key] = agg.get(key, 0) + us
    tot = sum(v for k, v in agg.items() if not k.startswith('(idle)')) or 1
    print('CPU %s (ativo %.0f ms)' % (label, tot / 1000))
    for k, us in sorted(agg.items(), key=lambda kv: -kv[1])[:top]:
        if k.startswith('(idle)'): continue
        print('   %5.1f%%  %7.1f ms  %s' % (100 * us / tot, us / 1000, k))
    await b.send('Profiler.disable')
async def main():
    b = B2(w=1280, h=800, port=9420); await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=p4%d' % (int(time.time()) % 100000), 3.5)
        await b.js("openById('mago-negro-chibi-circulo-dourado-grande')", 0.8)
        await b.js("S.zoom=18;syncZoomUI();requestDraw()", 0.5)
        box = json.loads(await b.js("""(()=>{const r=document.getElementById('cv').getBoundingClientRect();return JSON.stringify({x:r.x,y:r.y,z:S.zoom,R:RULER})})()"""))
        await b.js("selectColor(CODE_IDX.F5)", 0.2)
        x0 = box['x'] + box['R'] + 5 * box['z']; y0 = box['y'] + box['R'] + 5 * box['z']
        await prof_start(b)
        await b.send('Input.dispatchMouseEvent', type='mousePressed', x=x0, y=y0, button='left', clickCount=1)
        for i in range(120):
            await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=x0 + i * 3, y=y0 + (i % 20) * 2, button='left', buttons=1)
        await b.send('Input.dispatchMouseEvent', type='mouseReleased', x=x0 + 360, y=y0, button='left', clickCount=1)
        await asyncio.sleep(0.5)
        await prof_stop(b, 'pincelada (120 movimentos) no molde 100x100')
        # só passar o mouse (sem apertar): custo do destaque / informação
        await prof_start(b)
        for i in range(120):
            await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=x0 + i * 3, y=y0 + (i % 20) * 2)
        await asyncio.sleep(0.3)
        await prof_stop(b, 'só passar o mouse (120 movimentos, sem apertar)')
        await b.js("setMode('assemble')", 0.8)
        await prof_start(b)
        await b.js("setMode('create')", 1.2)
        await prof_stop(b, 'voltar de Montar para Criar')
        await prof_start(b)
        await b.js("setMode('assemble')", 1.2)
        await prof_stop(b, 'entrar em Montar')
    finally:
        await b.close()
asyncio.run(main())
