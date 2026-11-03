"""Tela inicial nova em tablet (768) e celular (390), claro, e sem molde nenhum (catálogo vazio simulado)."""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep


async def main():
    b = B2(w=768, h=2200, port=9336)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=tab', 4.0)
        await b.js("applyTheme('light');document.getElementById('home').scrollTop=0", 0.8)
        await b.shot(OUT + 'home_tablet_light.png')
        ov = await b.js("document.documentElement.scrollWidth>innerWidth")
        print('rolagem lateral no tablet:', ov)
        await b.viewport(390, 2600, 1.5, True)
        await b.js("document.getElementById('home').scrollTop=0", 0.8)
        await b.shot(OUT + 'home_celular_light.png')
        ov = await b.js("document.documentElement.scrollWidth>innerWidth")
        print('rolagem lateral no celular:', ov, '| largura da página:', await b.js("document.documentElement.scrollWidth"))
        # elementos que passam da tela no celular
        wide = await b.js("""JSON.stringify([...document.querySelectorAll('.home *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.right>innerWidth+1&&!e.closest('.hchips')&&!e.closest('.hmarq')&&!e.closest('.hrow')&&!e.closest('.hfls')}).slice(0,8).map(e=>e.className+'|'+e.tagName+'|'+Math.round(e.getBoundingClientRect().right)))""")
        print('estouram a largura:', wide)
        pr = [p for p in b.problems() if 'favicon' not in p]
        print('problemas:', pr if pr else 'nenhum')
    finally:
        await b.close()
    # catálogo vazio: remove os moldes antes de a página rodar
    b = B2(w=1280, h=1200, port=9337)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.send('Page.addScriptToEvaluateOnNewDocument', source="localStorage.setItem('beadstudio.deleted','[]')")
        await b.goto('http://localhost:8765/index.html?x=vazio', 0.5)
        # simula catálogo vazio: esvazia TEMPLATES e recarrega a tela inicial
        await b.js("window.TEMPLATES.length=0;tplDecoded=null;renderHome();document.getElementById('home').scrollTop=0", 1.0)
        info = await b.js("""JSON.stringify({day:document.getElementById('homeDay').hidden, marq:document.getElementById('homeMarq').hidden, chips:document.querySelectorAll('#homeChips .hchip').length,
           stats:[...document.querySelectorAll('#homeStats b')].map(x=>x.textContent), news:document.getElementById('homeNew').hidden, cats:document.getElementById('homeCats').hidden, d:document.getElementById('hTplsD').textContent})""")
        print('catálogo vazio:', info)
        await b.shot(OUT + 'home_vazio.png')
        pr = [p for p in b.problems() if 'favicon' not in p]
        print('problemas (vazio):', pr if pr else 'nenhum')
    finally:
        await b.close()
asyncio.run(main())
