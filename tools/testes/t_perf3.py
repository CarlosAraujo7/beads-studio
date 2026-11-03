"""Editor com o MAIOR molde do catálogo: abrir, desenhar a tela, pintar com o mouse de verdade, Montar."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
from t_perf import metrics, delta
async def main():
    b = B2(w=1280, h=800, port=9410); await b.start()
    try:
        await b.send('Log.enable'); await b.send('Performance.enable')
        await b.goto('http://localhost:8765/index.html?x=p3%d' % (int(time.time()) % 100000), 3.5)
        info = json.loads(await b.js("""JSON.stringify((()=>{const t=decodeTemplates().filter(t=>!t.trashed).sort((a,b)=>b.w*b.h-a.w*a.h)[0];return {id:t.id,name:t.name,w:t.w,h:t.h,beads:t.beads}})())"""))
        print('maior molde:', info)
        async def timed(label, js):
            m0 = await metrics(b)
            r = json.loads(await b.js("""(async()=>{const t0=performance.now();%s;const t1=performance.now();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return JSON.stringify({s:t1-t0,q:performance.now()-t0})})()""" % js))
            m1 = await metrics(b); d = delta(m0, m1)
            print('  %-46s script %6.1f ms | até o quadro %6.1f ms | estilo %d layout %d' % (label, r['s'], r['q'], d['estilo'], d['layout']))
        await timed('abrir o maior molde', "openById('%s')" % info['id'])
        await b.js("fitZoom()", 0.3)
        print('  zoom:', await b.js("S.zoom"))
        await timed('draw() (grade inteira, estilo contas)', "draw()")
        await b.js("S.zoom=18;syncZoomUI();requestDraw()", 0.4)
        await timed('draw() com zoom 18', "draw()")
        await b.js("S.style='pixel';requestDraw()", 0.2)
        await timed('draw() estilo pixels', "draw()")
        await b.js("S.style='bead';requestDraw()", 0.2)
        # pintar de verdade com o mouse
        box = json.loads(await b.js("""(()=>{const r=document.getElementById('cv').getBoundingClientRect();return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height,z:S.zoom,R:RULER})})()"""))
        print('  canvas:', box)
        await b.js("selectColor(CODE_IDX.F5)", 0.2)
        m0 = await metrics(b); t0 = time.time()
        x0 = box['x'] + box['R'] + 5 * box['z']; y0 = box['y'] + box['R'] + 5 * box['z']
        await b.send('Input.dispatchMouseEvent', type='mousePressed', x=x0, y=y0, button='left', clickCount=1)
        n = 0
        for i in range(120):
            await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=x0 + i * 3, y=y0 + (i % 20) * 2, button='left', buttons=1); n += 1
        await b.send('Input.dispatchMouseEvent', type='mouseReleased', x=x0 + 360, y=y0, button='left', clickCount=1)
        wall = (time.time() - t0) * 1000
        m1 = await metrics(b); d = delta(m0, m1)
        print('  pincelada de %d movimentos de mouse: %.0f ms de parede | tarefas %d ms (script %d, estilo %d, layout %d) => %.1f ms de CPU por movimento' % (n, wall, d['tarefa'], d['script'], d['estilo'], d['layout'], d['tarefa'] / n))
        print('  contas pintadas de vermelho:', await b.js("S.grid.filter(v=>v===CODE_IDX.F5).length"))
        await timed('entrar no modo Montar', "setMode('assemble')")
        await timed('próximas 10 linhas', "for(let i=0;i<10;i++){const n=document.getElementById('rNext2');if(n&&!n.disabled)n.click()}")
        await timed('marcar linha', "document.getElementById('rAll').click()")
        await timed('voltar ao Criar', "setMode('create')")
        # parado no editor: CPU em repouso
        m0 = await metrics(b); await asyncio.sleep(3.0); m1 = await metrics(b); d = delta(m0, m1)
        print('  editor PARADO por 3 s: tarefas %d ms (estilo %d, layout %d, estilos recalculados %d)' % (d['tarefa'], d['estilo'], d['layout'], d['n_estilo']))
        pr = [p for p in b.problems() if 'favicon' not in p]
        if pr: print('ERROS:', pr)
    finally:
        await b.close()
asyncio.run(main())
