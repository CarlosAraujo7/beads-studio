import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=alias9'


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)))")
        print('ALIAS_OF:', await b.js("JSON.stringify(ALIAS_OF)"), '| H12 idx', await b.js("CODE_IDX.H12"), '| A1 idx', await b.js("CODE_IDX.A1"))
        print('contador "Todas as cores":', await b.js("document.querySelector('#palMore .palcount').textContent"))
        print('molde:', await b.js("""(async()=>{const all=decodeTemplates();const t=all.find(t=>/^Kirby/.test(t.name)&&t.w<=50&&t.h<=50);openTpl(t);await new Promise(r=>setTimeout(r,500));return t.name+' '+t.w+'x'+t.h})()"""))
        # 1) menu Todas as cores: sem H12
        r = await b.js("""(async()=>{document.getElementById('palMore').click();await new Promise(r=>setTimeout(r,300));
          const bt=[...document.querySelectorAll('#palBody .hexbtn')];const cods=bt.map(x=>PALETTE[x.dataset.i-1].code);
          const q=document.getElementById('palSearch');q.value='H12';q.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,150));
          const vis=[...document.querySelectorAll('#palBody .hexbtn')].filter(x=>!x.hidden).map(x=>PALETTE[x.dataset.i-1].code);
          q.value='';q.dispatchEvent(new Event('input',{bubbles:true}));
          return JSON.stringify({n:bt.length,temH12:cods.includes('H12'),temA1:cods.includes('A1'),buscaH12:vis,vazio:!document.getElementById('palEmpty').hidden})})()""")
        print('menu:', r)
        # 2) parecidas com A1 e com H12
        r = await b.js("""JSON.stringify({deA1:similarTo(CODE_IDX.A1,10).map(x=>PALETTE[x.v-1].code),deH12:similarTo(CODE_IDX.H12,6).map(x=>PALETTE[x.v-1].code)})""")
        print('similarTo:', r)
        await b.js("closePalPop()")
        # 3) Ajustes: trocar/por
        r = await b.js("""(async()=>{document.querySelector('#tabsCreate button[data-tab=project]').click();await new Promise(r=>setTimeout(r,200));
          const f=[...document.getElementById('repFrom').options].map(o=>o.textContent),t=[...document.getElementById('repTo').options].map(o=>o.textContent);
          return JSON.stringify({de:f.length,para:t.length,deH12:f.find(x=>x.startsWith('H12')),paraH12:t.find(x=>x.startsWith('H12'))||null})})()""")
        print('trocar/por:', r)
        # 4) desenho com contas H12 (como num desenho salvo antigo): linha da lista avisa
        r = await b.js("""(async()=>{document.querySelector('#tabsCreate button[data-tab=counts]').click();
          const h=CODE_IDX.H12;let k=0;for(let i=0;i<S.grid.length&&k<5;i++)if(S.grid[i]){S.grid[i]=h;k++}
          recount();renderCounts();await new Promise(r=>setTimeout(r,200));
          const row=document.querySelector('#countList .crow[data-v="'+h+'"]');
          return JSON.stringify({linha:row?row.innerText.replace(/\\s+/g,' '):null})})()""")
        print('lista:', r)
        await b.shot(OUT + 'alias_ui_lista.png')
        # 5) Ajustar cores
        r = await b.js("""(async()=>{openColors();await new Promise(r=>setTimeout(r,300));const box=document.getElementById('colList');
          const row=[...box.children].find(x=>/H12/.test(x.innerText));return JSON.stringify({h12:row?row.innerText.replace(/\\s+/g,' '):null,n:box.children.length})})()""")
        print('ajustar cores:', r)
        await b.shot(OUT + 'alias_ui_ajustar.png')
        print('erros de página:', await b.js("JSON.stringify(window.__erros)"))
    finally:
        await b.close()

asyncio.run(main())
