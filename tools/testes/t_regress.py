import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=reg9'


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));addEventListener('unhandledrejection',e=>window.__erros.push('rej:'+String(e.reason)))")
        print('catálogo:', await b.js("TEMPLATES.length"), '| paleta:', await b.js("PALETTE.length"), '| ALIAS_OF', await b.js("JSON.stringify(ALIAS_OF)"))
        # início
        await b.js("applyTheme('light')")
        await b.shot(OUT + 'reg_home.png')
        print('início:', await b.js("document.body.dataset.view+' | novidades:'+document.querySelectorAll('#homeNewRow .tile').length"))
        # galeria: abre, busca, abre um molde
        r = await b.js("""(async()=>{openGallery({query:'pikachu'});await new Promise(r=>setTimeout(r,600));const n=document.querySelectorAll('#dlgTemplates .tcard,#dlgTemplates .cblock .mini').length;
          const t=decodeTemplates().find(t=>/^Pikachu/.test(t.name)&&t.w<=50);openTpl(t);await new Promise(r=>setTimeout(r,600));return JSON.stringify({resultados:n,aberto:t.name,view:view,S:[S.w,S.h,total]})})()""")
        print('galeria:', r)
        # Criar: pinta, desfaz
        r = await b.js("""(async()=>{setMode('create');const before=total,sn=snap();setCell(10,0,CODE_IDX.H7);commit(sn);await new Promise(r=>setTimeout(r,200));
          const mid=total;undo();await new Promise(r=>setTimeout(r,200));return JSON.stringify({antes:before,depois:mid,desfeito:total})})()""")
        print('criar/desfazer:', r)
        # Montar: 1 linha e 2 linhas, marcar linha, cor por cor, selecionar
        r = await b.js("""(async()=>{setMode('assemble');await new Promise(r=>setTimeout(r,500));const z=S.zoom;
          document.getElementById('rAll').click();await new Promise(r=>setTimeout(r,200));const d1=doneTotal;
          setAsmSpan(2);await new Promise(r=>setTimeout(r,300));const rows2=groupRows(S.asm.row).length;
          document.querySelector('#asmSeg button[data-view=color]').click();await new Promise(r=>setTimeout(r,300));
          const first=document.querySelector('.cfocus');first.click();await new Promise(r=>setTimeout(r,300));const cor=S.asm.color;
          document.querySelector('#asmSeg button[data-view=row]').click();await new Promise(r=>setTimeout(r,300));
          document.getElementById('btnSel').click();await new Promise(r=>setTimeout(r,100));const selOn=S.selOn;document.getElementById('btnSel').click();
          setAsmSpan(1);S.done.fill(0);asmChanged();
          return JSON.stringify({zoomMontar:z,marcadasNaLinha:d1,linhasDoGrupo:rows2,corEscolhida:cor,selLigou:selOn})})()""")
        print('montar:', r)
        # volta para Criar: zoom e espelho voltam ao normal
        r = await b.js("""(async()=>{setMode('create');await new Promise(r=>setTimeout(r,300));return JSON.stringify({mir:asmMir(),badge:document.getElementById('mirBadge').hidden,hint:document.getElementById('hint').textContent.slice(0,40)})})()""")
        print('de volta ao Criar:', r)
        # ajuda: tópico Montar menciona o espelho
        r = await b.js("""(async()=>{openHelp&&openHelp('montar');await new Promise(r=>setTimeout(r,400));return JSON.stringify({tem:/Espelhado/.test(document.querySelector('#dlgHelp').innerText),parecidas:/parecidas/.test(document.querySelector('#dlgHelp').innerText)})})()""")
        print('ajuda:', r)
        await b.js("document.querySelector('#dlgHelp').close&&document.querySelector('#dlgHelp').close()")
        # celular
        await b.viewport(390, 844, 2, True)
        await b.js("window.scrollTo(0,0);setMode('assemble')", 0.8)
        await b.shot(OUT + 'reg_celular_montar.png')
        r = await b.js("""JSON.stringify({scrollW:document.documentElement.scrollWidth,vw:innerWidth,badge:!document.getElementById('mirBadge').hidden,zoom:S.zoom})""")
        print('celular:', r)
        print('erros de página:', await b.js("JSON.stringify(window.__erros)"))
    finally:
        await b.close()

asyncio.run(main())
