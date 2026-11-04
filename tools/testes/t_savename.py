"""Diálogo "Salvar molde" com nome comprido (pedido do dono, 2026-11-04: o nome saía cortado e aparecia barra de rolagem lateral).
Confere, em 1280 e 390 de largura: sem rolagem lateral no diálogo, o botão "Salvar alterações em …" cabe na largura, o nome é cortado com reticências, o title tem o nome inteiro,
e o mesmo lugar/tamanho do botão com nome curto e comprido (regra 4.11). Também confere a galeria só com as abas Moldes e Projetos 3D.
Rodar: python -m http.server 8765 na raiz do projeto e  python -u tools/testes/t_savename.py"""
import asyncio, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=savename1'
LONG = 'Casal sob o guarda-chuva amarelo (How I Met Your Mother, ilustração)'

MEASURE = """(()=>{const d=document.querySelector('#dlgSaveTpl'),body=d.querySelector('.body'),b=document.querySelector('#stOverwrite'),n=b.querySelector('.stn');
const rb=b.getBoundingClientRect(),rd=d.querySelector('.dlg').getBoundingClientRect();
return JSON.stringify({rolagemLateral:body.scrollWidth>body.clientWidth+1,botaoCabe:rb.right<=rd.right+0.5&&rb.left>=rd.left-0.5,cortado:n?n.scrollWidth>n.clientWidth+1:null,
 title:b.title,x:Math.round(rb.left),y:Math.round(rb.top),w:Math.round(rb.width),h:Math.round(rb.height)})})()"""


async def run(w, h, tag):
    b = Browser(w=w, h=h)
    await b.start()
    res = {}
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));window.confirm=()=>true")
        await b.js("applyTheme('light')")
        for key, name in (('comprido', LONG), ('curto', None)):
            r = await b.js("""(async()=>{const all=decodeTemplates().filter(t=>!t.trashed);const t=%s;if(!t)return 'molde não achado';openTpl(t);await new Promise(r=>setTimeout(r,600));
              openSaveTpl();await new Promise(r=>setTimeout(r,300));return 'ok '+t.name})()""" % (
                "all.find(t=>t.name===%s)" % json.dumps(name) if name else "all.filter(t=>t.name.length<=12)[0]"))
            m = json.loads(await b.js(MEASURE))
            res[key] = m
            print(tag, key, r, m)
            await b.shot(OUT + f'savename_{tag}_{key}.png')
            await b.js("document.querySelector('#dlgSaveTpl').close()")
        same = res['comprido']['x'] == res['curto']['x'] and res['comprido']['y'] == res['curto']['y'] and res['comprido']['w'] == res['curto']['w'] and res['comprido']['h'] == res['curto']['h']
        ok = (not res['comprido']['rolagemLateral'] and res['comprido']['botaoCabe'] and res['comprido']['cortado'] and LONG in res['comprido']['title'] and same)
        print(tag, 'botão no mesmo lugar e tamanho (curto x comprido):', same)
        r = await b.js("""(async()=>{goHome&&goHome();await new Promise(r=>setTimeout(r,400));openGallery({});await new Promise(r=>setTimeout(r,900));
          return JSON.stringify([...document.querySelectorAll('#tplPlates .ptab')].map(x=>x.textContent.trim()))})()""")
        print(tag, 'abas da galeria:', r)
        await b.shot(OUT + f'savename_{tag}_galeria.png')
        tabs = json.loads(r)
        ok = ok and len(tabs) == 2 and tabs[0].startswith('Moldes') and tabs[1].startswith('Projetos 3D')
        print(tag, 'erros de página:', await b.js("JSON.stringify(window.__erros)"))
        print(tag, 'RESUMO:', 'OK' if ok else 'FALHA')
    finally:
        await b.close() if hasattr(b, 'close') else None


async def main():
    await run(1280, 900, 'desk')
    await run(390, 844, 'cel')
asyncio.run(main())
