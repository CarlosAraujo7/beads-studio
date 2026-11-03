"""Medidor de desempenho (CDP): carregamento, tela inicial parada, galeria (blocos, lista, busca), editor e uso repetido.
uso: python t_perf.py [fase ...] [--dpr=1.5] [--page=index.html]   fases: load micro gal busca idle editor montar leak cpu"""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OPT = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
DPR = float(OPT.get('--dpr', 1)); PAGE = OPT.get('--page', 'index.html'); W = int(OPT.get('--w', 1280)); H = int(OPT.get('--h', 800))
WANT = ARGS or ['load', 'micro', 'gal', 'busca', 'idle', 'editor', 'montar', 'leak']
URL = 'http://localhost:8765/%s?x=perf%d' % (PAGE, int(time.time()) % 100000)


async def metrics(b):
    r = await b.send('Performance.getMetrics')
    return {m['name']: m['value'] for m in r['metrics']}


def delta(m0, m1):
    k = lambda n: (m1.get(n, 0) - m0.get(n, 0))
    return dict(tarefa=round(k('TaskDuration') * 1000), script=round(k('ScriptDuration') * 1000), estilo=round(k('RecalcStyleDuration') * 1000), layout=round(k('LayoutDuration') * 1000),
                n_estilo=int(k('RecalcStyleCount')), n_layout=int(k('LayoutCount')), nos=int(m1.get('Nodes', 0)), ouvintes=int(m1.get('JSEventListeners', 0)), heap_mb=round(m1.get('JSHeapUsedSize', 0) / 1e6, 1))


async def timed(b, label, js, wait=0.05):
    """tempo do script e até o 2º quadro (inclui estilo, layout e pintura); devolve (ms_script, ms_ate_quadro, métricas)"""
    m0 = await metrics(b)
    r = json.loads(await b.js("""(async()=>{const t0=performance.now();%s;const t1=performance.now();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const t2=performance.now();return JSON.stringify({script:t1-t0,quadro:t2-t0})})()""" % js))
    await asyncio.sleep(wait)
    m1 = await metrics(b)
    d = delta(m0, m1)
    print('  %-52s script %6.0f ms | até o quadro %6.0f ms | estilo %4d (%d) layout %4d (%d) | nós %d heap %s MB' % (label, r['script'], r['quadro'], d['estilo'], d['n_estilo'], d['layout'], d['n_layout'], d['nos'], d['heap_mb']))
    return r, d


async def cpu_profile(b, js_async, top=14, label=''):
    await b.send('Profiler.enable'); await b.send('Profiler.setSamplingInterval', interval=250)
    await b.send('Profiler.start')
    await b.js("(async()=>{%s})()" % js_async)
    prof = (await b.send('Profiler.stop'))['profile']
    nodes = {n['id']: n for n in prof['nodes']}
    self_us = {}
    for sid, dt in zip(prof['samples'], prof['timeDeltas']):
        self_us[sid] = self_us.get(sid, 0) + dt
    agg = {}
    for nid, us in self_us.items():
        cf = nodes[nid]['callFrame']
        key = '%s %s:%d' % (cf['functionName'] or '(anônima)', (cf['url'].split('/')[-1].split('?')[0] or '-'), cf['lineNumber'] + 1)
        agg[key] = agg.get(key, 0) + us
    tot = sum(agg.values()) or 1
    print('  CPU %s (total %.0f ms amostrados)' % (label, tot / 1000))
    for k, us in sorted(agg.items(), key=lambda kv: -kv[1])[:top]:
        print('     %5.1f%%  %7.1f ms  %s' % (100 * us / tot, us / 1000, k))
    await b.send('Profiler.disable')


async def new_browser(port):
    b = B2(w=W, h=H, port=port)
    await b.start()
    await b.send('Log.enable'); await b.send('Performance.enable')
    await b.viewport(W, H, DPR, False)
    return b


async def main():
    port = 9360
    # ---------- carregamento ----------
    if 'load' in WANT:
        b = await new_browser(port); port += 1
        try:
            t0 = time.time()
            await b.goto(URL, 0.1)
            for _ in range(80):
                if await b.js("document.readyState==='complete'&&!!window.TEMPLATES&&document.body.dataset.view==='home'"): break
                await asyncio.sleep(0.1)
            wall = (time.time() - t0) * 1000
            r = json.loads(await b.js("""JSON.stringify((()=>{const n=performance.getEntriesByType('navigation')[0],rs=performance.getEntriesByType('resource').filter(x=>/templates|projetos3d|remessas/.test(x.name));
               return {dcl:Math.round(n.domContentLoadedEventEnd),load:Math.round(n.loadEventEnd),res:rs.map(x=>[x.name.split('/').pop().split('?')[0],Math.round(x.duration),Math.round(x.transferSize/1024)+'KB'])}})())"""))
            m = await metrics(b)
            print('CARREGAMENTO (dpr %s): parede %.0f ms | DOMContentLoaded %s ms | load %s ms | recursos %s' % (DPR, wall, r['dcl'], r['load'], r['res']))
            print('  script acumulado %.0f ms | estilo %.0f ms | layout %.0f ms | tarefas %.0f ms | nós %d | heap %.1f MB' % (m['ScriptDuration'] * 1000, m['RecalcStyleDuration'] * 1000, m['LayoutDuration'] * 1000, m['TaskDuration'] * 1000, m['Nodes'], m['JSHeapUsedSize'] / 1e6))
        finally:
            await b.close()

    b = await new_browser(port); port += 1
    try:
        await b.goto(URL, 3.5)
        # ---------- microbenchmarks ----------
        if 'micro' in WANT:
            print('MICRO (média de 15 chamadas, ms)')
            r = json.loads(await b.js("""JSON.stringify((()=>{const T=(f,n=15)=>{f();const t=performance.now();for(let i=0;i<n;i++)f();return Math.round((performance.now()-t)/n*100)/100};
               const all=decodeTemplates().filter(t=>!t.trashed);
               return {decodeTemplates:T(()=>decodeTemplates()),liveBatches:T(()=>liveBatches()),loadCatCfg:T(()=>loadCatCfg()),catList:T(()=>catList()),buildCatMinis:T(()=>buildCatMinis(all)),
                 renderHome:T(()=>renderHome(),8),homePool:T(()=>homePool(all)),versions:T(()=>buildVerIndex(all),5),loadMeta:T(()=>loadMeta()),loadEdits:T(()=>loadEdits()),loadDeleted:T(()=>loadDeleted()),
                 lsTamanhoKB:Object.fromEntries(Object.keys(localStorage).map(k=>[k,Math.round((localStorage.getItem(k)||'').length/1024)]))}})())"""))
            for k, v in r.items(): print('   %-16s %s' % (k, v))
        # ---------- galeria ----------
        if 'gal' in WANT:
            print('GALERIA (dpr %s)' % DPR)
            await timed(b, 'abrir (blocos, 1 placa: ~1000 miniaturas)', "tplView='blocks';openGallery()", 0.3)
            await timed(b, 'trocar para a aba 2 placas', "setPlates('2')", 0.2)
            await timed(b, 'trocar para a aba 1 placa', "setPlates('1')", 0.2)
            await timed(b, 'Lista, categoria Dragon Ball (34 cartões)', "tplView='list';tplCat='dragon-ball';setTplView('list')", 0.2)
            await timed(b, 'Lista, TODAS as categorias (~1000 cartões)', "document.querySelector('#tplSide .cat-btn[data-cat=all]').click()", 0.5)
            await timed(b, 'voltar a Blocos', "setTplView('blocks')", 0.3)
            await timed(b, 'fechar a galeria', "document.getElementById('dlgTemplates').close()", 0.2)
            await timed(b, 'abrir Novos moldes (remessa 28: 123 cartões)', "openNews()", 0.3)
            await timed(b, 'mudar para a remessa 27', "setBatch(27)", 0.2)
            await b.js("document.getElementById('dlgTemplates').close()", 0.3)
        if 'busca' in WANT:
            print('BUSCA NA GALERIA (digitando "naruto" letra a letra)')
            await b.js("tplView='blocks';openGallery()", 1.2)
            for q in ('n', 'na', 'nar', 'naru', 'narut', 'naruto', 'narut', 'naru', 'nar', 'na', 'n', ''):
                await timed(b, 'busca "%s"' % q, "(()=>{const i=document.getElementById('tplSearch');i.value=%s;i.dispatchEvent(new Event('input',{bubbles:true}))})()" % json.dumps(q), 0.05)
            await b.js("document.getElementById('dlgTemplates').close()", 0.3)
            print('BUSCA NA TELA INICIAL')
            for q in ('p', 'pi', 'pik', 'pika', ''):
                await timed(b, 'busca inicial "%s"' % q, "(()=>{const i=document.getElementById('homeSearch');i.value=%s;i.dispatchEvent(new Event('input',{bubbles:true}))})()" % json.dumps(q), 0.2)
        # ---------- tela inicial parada ----------
        if 'idle' in WANT:
            print('TELA INICIAL PARADA (4 s sem mexer)')
            await b.js("document.querySelectorAll('dialog[open]').forEach(d=>d.close());setView('home',false);document.getElementById('home').scrollTop=0", 0.5)
            for label, css in (('como está (animações ligadas)', ''), ('sem a animação do degradê do palco', '.hstage{animation:none!important}'), ('sem backdrop-filter na busca', '.hsearch{-webkit-backdrop-filter:none!important;backdrop-filter:none!important}'), ('sem vitrine animada', '.hmarq .track{animation:none!important}'), ('sem nenhuma animação do início', '.hstage,.hmarq .track,.hday .art canvas{animation:none!important}.hsearch{-webkit-backdrop-filter:none!important;backdrop-filter:none!important}')):
                await b.js("(()=>{let s=document.getElementById('__p');if(!s){s=document.createElement('style');s.id='__p';document.head.appendChild(s)}s.textContent=%s})()" % json.dumps(css), 0.4)
                m0 = await metrics(b); await asyncio.sleep(4.0); m1 = await metrics(b)
                d = delta(m0, m1)
                print('  %-46s tarefas %4d ms em 4 s (script %d, estilo %d, layout %d) | estilos recalculados %d' % (label, d['tarefa'], d['script'], d['estilo'], d['layout'], d['n_estilo']))
            await b.js("document.getElementById('__p').remove()", 0.1)
        # ---------- editor ----------
        if 'editor' in WANT:
            print('EDITOR (dpr %s)' % DPR)
            await timed(b, 'abrir um molde de 1331 contas', "openById(window.TEMPLATES.find(t=>/Pikachu sentado/.test(t.name)).id)", 0.4)
            await timed(b, 'Ajustar zoom', "fitZoom()", 0.2)
            r, d = await timed(b, 'pintar 1 conta (gridChanged)', "(()=>{S.grid[5]=CODE_IDX.F5;gridChanged()})()", 0.1)
            await timed(b, 'refreshAll()', "refreshAll()", 0.1)
            await timed(b, 'renderCounts()', "renderCounts()", 0.1)
            await timed(b, 'requestDraw() (desenha o quadriculado)', "draw()", 0.1)
            await timed(b, '30 pinceladas seguidas (gridChanged cada)', "for(let i=0;i<30;i++){S.grid[100+i]=CODE_IDX.A4;gridChanged()}", 0.2)
            await timed(b, 'undo', "undo()", 0.1)
            await timed(b, 'trocar de cor (selectColor)', "selectColor(CODE_IDX.A4)", 0.1)
            await timed(b, 'mudar para a aba Ajustes e voltar', "(()=>{const t=[...document.querySelectorAll('#tabsCreate button')];t[1].click();t[0].click()})()", 0.1)
        if 'montar' in WANT:
            print('MONTAR (dpr %s)' % DPR)
            await timed(b, 'entrar no modo Montar', "setMode('assemble')", 0.4)
            await timed(b, 'próxima linha (renderAssemble)', "document.getElementById('rNext2').click()", 0.1)
            await timed(b, '20 próximas linhas', "for(let i=0;i<20;i++){const n=document.getElementById('rNext2');if(n&&!n.disabled)n.click()}", 0.2)
            await timed(b, 'marcar a linha', "document.getElementById('rAll').click()", 0.1)
            await timed(b, 'voltar ao Criar', "setMode('create')", 0.2)
        pr = [p for p in b.problems() if 'favicon' not in p]
        if pr: print('ERROS:', pr)
    finally:
        await b.close()

    # ---------- uso repetido: vaza memória ou degrada? ----------
    if 'leak' in WANT:
        b = await new_browser(port); port += 1
        try:
            await b.goto(URL, 3.5)
            print('USO REPETIDO (12 voltas: abrir galeria, buscar, abrir molde, voltar, início)')
            base = None
            for it in range(12):
                m0 = await metrics(b)
                t = json.loads(await b.js("""(async()=>{const t0=performance.now();const w=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                  tplView='blocks';openGallery();await w();
                  const i=document.getElementById('tplSearch');i.value='pik';i.dispatchEvent(new Event('input',{bubbles:true}));await w();i.value='';i.dispatchEvent(new Event('input',{bubbles:true}));await w();
                  document.querySelector('.mini').click();await w();
                  document.getElementById('btnBack').click();await w();
                  document.getElementById('dlgTemplates').close();await w();
                  return JSON.stringify({ms:Math.round(performance.now()-t0)})})()"""))
                await asyncio.sleep(0.2)
                m1 = await metrics(b)
                if base is None: base = m1
                print('  volta %2d: %5d ms | nós %6d (%+d) | ouvintes %6d (%+d) | heap %6.1f MB (%+.1f)' % (it + 1, t['ms'], m1['Nodes'], m1['Nodes'] - base['Nodes'], m1['JSEventListeners'], m1['JSEventListeners'] - base['JSEventListeners'], m1['JSHeapUsedSize'] / 1e6, (m1['JSHeapUsedSize'] - base['JSHeapUsedSize']) / 1e6))
        finally:
            await b.close()

    # ---------- onde o CPU vai (perfil) ----------
    if 'cpu' in WANT:
        b = await new_browser(port); port += 1
        try:
            await b.goto(URL, 3.5)
            await cpu_profile(b, "tplView='blocks';openGallery();await new Promise(r=>setTimeout(r,800));document.getElementById('dlgTemplates').close();", label='abrir a galeria em blocos')
            await cpu_profile(b, "const w=()=>new Promise(r=>setTimeout(r,60));openGallery();for(const q of ['n','na','nar','naru','narut','naruto']){const i=document.getElementById('tplSearch');i.value=q;i.dispatchEvent(new Event('input',{bubbles:true}));await w()}", label='digitar "naruto" na galeria')
            await cpu_profile(b, "document.getElementById('dlgTemplates').close();tplView='list';tplCat='all';openGallery();await new Promise(r=>setTimeout(r,1000))", label='Lista com todas as categorias')
        finally:
            await b.close()
if __name__ == '__main__':
    asyncio.run(main())
