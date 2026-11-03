import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=r28e'

async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));addEventListener('unhandledrejection',e=>window.__erros.push('rej:'+String(e.reason)))")
        print('catálogo:', await b.js("TEMPLATES.length"), '| remessas:', await b.js("JSON.stringify((window.REMESSAS||[]).slice(0,2).map(r=>({n:r.n,ids:r.ids.length})))"))
        await b.js("applyTheme('light')")
        r = await b.js("""(async()=>{openNews&&openNews();await new Promise(r=>setTimeout(r,800));const n=document.querySelectorAll('#dlgTemplates .tcard').length;return JSON.stringify({view:document.body.dataset.view,cartoes:n,batch:typeof tplBatch!=='undefined'?tplBatch:null})})()""")
        print('novos moldes:', r)
        await b.shot(OUT + 'r28_news.png')
        r = await b.js("""(async()=>{const t=decodeTemplates().find(t=>t.name==='Gato branco dentro de um baú (gráfico, Mard 1023)');if(!t)return 'molde não achado';openTpl(t);await new Promise(r=>setTimeout(r,700));return JSON.stringify({nome:t.name,cat:t.group,view:view,S:[S.w,S.h,total]})})()""")
        print('abrir molde novo:', r)
        await b.shot(OUT + 'r28_open.png')
        r = await b.js("""(async()=>{goHome&&goHome();await new Promise(r=>setTimeout(r,500));openGallery({cat:'os-smurfs'});await new Promise(r=>setTimeout(r,700));const n=document.querySelectorAll('#dlgTemplates .tcard').length;return JSON.stringify({smurfs:n})})()""")
        print('categoria Os Smurfs:', r)
        print('erros de página:', await b.js("JSON.stringify(window.__erros)"))
    finally:
        await b.close() if hasattr(b, 'close') else None
asyncio.run(main())
