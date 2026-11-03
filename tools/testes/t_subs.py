import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html'

OPEN = """(async()=>{const all=decodeTemplates();const t=all.find(t=>/^Stitch/.test(t.name)&&t.w<=50&&t.h<=50);openTpl(t);await new Promise(r=>setTimeout(r,500));return t.name+' '+t.w+'x'+t.h})()"""


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    errs = []
    await b.goto(URL, 2.0)
    print('molde:', await b.js(OPEN, 0.6))
    print('tema inicial:', await b.js("document.documentElement.dataset.theme"))
    await b.js("applyTheme('light')")
    await b.js("window.scrollTo(0,0)", 0.3)
    await b.shot(OUT + 'subs_0_editor.png')

    # 1) submenu do ⇄ da 2ª cor da lista
    r = await b.js("""(async()=>{const btn=[...document.querySelectorAll('#countList .swapbtn')][1];btn.click();await new Promise(r=>setTimeout(r,300));
      const pop=document.getElementById('subPop'),r=pop.getBoundingClientRect();
      return JSON.stringify({aberto:!pop.hidden,titulo:document.getElementById('subTitle').textContent,n:pop.querySelectorAll('.subrow').length,pos:[r.left|0,r.top|0,r.width|0,r.height|0],foco:document.activeElement.className})})()""")
    print('submenu:', r)
    await b.shot(OUT + 'subs_1_submenu_claro.png')

    # 2) trocar: clica na 1ª substituta, confere contagens e desfaz
    r = await b.js("""(async()=>{const before=counts.slice();const row=document.querySelector('#subBody .subrow');const to=+row.dataset.v;const from=subV;
      row.click();await new Promise(r=>setTimeout(r,300));
      const res={de:PALETTE[from-1].code,para:PALETTE[to-1].code,antes_de:before[from],antes_para:before[to],depois_de:counts[from],depois_para:counts[to],aberto:!document.getElementById('subPop').hidden,toast:document.getElementById('toast').textContent,undo:hist.undo.length};
      undo();await new Promise(r=>setTimeout(r,200));
      res.restaurado=(counts[from]===before[from]&&counts[to]===before[to]);return JSON.stringify(res)})()""")
    print('troca:', r)

    # 3) Esc fecha
    r = await b.js("""(async()=>{[...document.querySelectorAll('#countList .swapbtn')][0].click();await new Promise(r=>setTimeout(r,200));const a=!document.getElementById('subPop').hidden;
      document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await new Promise(r=>setTimeout(r,100));
      return JSON.stringify({abriu:a,fechouComEsc:document.getElementById('subPop').hidden})})()""")
    print('esc:', r)

    # 4) menu Todas as cores com a faixa
    r = await b.js("""(async()=>{document.getElementById('palMore').click();await new Promise(r=>setTimeout(r,300));
      const s=document.getElementById('palSugg');const hx=[...document.querySelectorAll('#psRow .hexbtn')];
      return JSON.stringify({faixa:!s.hidden,titulo:document.getElementById('psTitle').textContent,n:hx.length,codigos:hx.map(h=>h.dataset.i&&PALETTE[h.dataset.i-1].code).join(' ')})})()""")
    print('faixa:', r)
    await b.shot(OUT + 'subs_2_todas_as_cores.png')
    r = await b.js("""(async()=>{const antes=S.color;const h=document.querySelector('#psRow .hexbtn');h.click();await new Promise(r=>setTimeout(r,200));
      return JSON.stringify({antes:PALETTE[antes-1].code,depois:PALETTE[S.color-1].code,menuAberto:!document.getElementById('palPop').hidden,novoTitulo:document.getElementById('psTitle').textContent})})()""")
    print('clique na faixa:', r)
    r = await b.js("""(async()=>{const q=document.getElementById('palSearch');q.value='verde';q.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));
      const vis=[...document.querySelectorAll('#palBody .hexbtn')].filter(b=>!b.hidden).length;
      const r1={faixaOculta:document.getElementById('palSugg').hidden,visiveis:vis};
      q.value='';q.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,100));r1.faixaVolta=!document.getElementById('palSugg').hidden;
      q.value='B13';q.dispatchEvent(new Event('input',{bubbles:true}));q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));await new Promise(r=>setTimeout(r,150));
      r1.enter=PALETTE[S.color-1].code;r1.fechou=document.getElementById('palPop').hidden;
      return JSON.stringify(r1)})()""")
    print('busca:', r)

    # 5) Ajustes -> trocar uma cor por outra
    r = await b.js("""(async()=>{document.querySelector('#tabsCreate button[data-tab=project]').click();await new Promise(r=>setTimeout(r,200));
      const d=document.getElementById('repFrom').closest('details');d.open=true;await new Promise(r=>setTimeout(r,200));
      return JSON.stringify({sug:document.querySelectorAll('#repSugg .hexbtn').length,txt:document.querySelector('#repSugg .rst').textContent})})()""")
    print('ajustes:', r)
    await b.shot(OUT + 'subs_3_ajustes.png')
    r = await b.js("""(async()=>{const h=document.querySelectorAll('#repSugg .hexbtn')[1];const code=PALETTE[h.dataset.i-1].code;h.click();await new Promise(r=>setTimeout(r,100));
      return JSON.stringify({clicou:code,repTo:PALETTE[document.getElementById('repTo').value-1].code,marcado:document.querySelector('#repSugg .hexbtn.on')&&PALETTE[document.querySelector('#repSugg .hexbtn.on').dataset.i-1].code})})()""")
    print('atalho:', r)

    # 6) "Outra cor…" do submenu leva ao Ajustes com a cor escolhida
    r = await b.js("""(async()=>{document.querySelector('#tabsCreate button[data-tab=counts]').click();await new Promise(r=>setTimeout(r,200));
      [...document.querySelectorAll('#countList .swapbtn')][2].click();await new Promise(r=>setTimeout(r,200));const alvo=subV;
      document.getElementById('subOther').click();await new Promise(r=>setTimeout(r,300));
      return JSON.stringify({alvo:PALETTE[alvo-1].code,repFrom:PALETTE[document.getElementById('repFrom').value-1].code,aba:S.tab,aberto:document.getElementById('repFrom').closest('details').open,subFechado:document.getElementById('subPop').hidden})})()""")
    print('outra cor:', r)

    # 7) escuro
    await b.js("document.querySelector('#tabsCreate button[data-tab=counts]').click();applyTheme('dark')", 0.4)
    await b.js("(async()=>{[...document.querySelectorAll('#countList .swapbtn')][1].click();await new Promise(r=>setTimeout(r,300))})()")
    await b.shot(OUT + 'subs_4_submenu_escuro.png')
    await b.js("closeSub();document.getElementById('palMore').click()", 0.4)
    await b.shot(OUT + 'subs_5_todas_escuro.png')
    await b.js("closePalPop()")

    # 8) celular
    await b.viewport(390, 844, 2, True)
    await b.js("applyTheme('light');window.scrollTo(0,0)", 0.5)
    r = await b.js("""(async()=>{document.getElementById('countList').scrollIntoView();await new Promise(r=>setTimeout(r,300));
      const btn=[...document.querySelectorAll('#countList .swapbtn')][1];btn.click();await new Promise(r=>setTimeout(r,300));
      const pop=document.getElementById('subPop'),r=pop.getBoundingClientRect();
      return JSON.stringify({aberto:!pop.hidden,pos:[r.left|0,r.top|0,r.width|0,r.height|0],vp:[innerWidth,innerHeight],cabe:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight})})()""")
    print('celular:', r)
    await b.shot(OUT + 'subs_6_celular.png')
    print('erros de página:', await b.js("window.__erros||'nenhum registrado'"))
    await b.close()

asyncio.run(main())
