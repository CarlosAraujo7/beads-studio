"""Capturas REAIS da galeria (miniaturas) com a paleta antiga, a nova a 100% e a nova a 70% (a de agora), para ver o que o dono viu."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?v=' + str(time.time_ns())

SET = {
 'antiga': "overrides={};PALETTE.forEach(p=>{const o=LEGACY_HEX[p.code];if(o)overrides[p.code]=o});derivePalette();",
 'nova100': "overrides={};vivid=100;derivePalette();",
 'nova70': "overrides={};vivid=70;derivePalette();",
}


async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    await b.goto(URL, 2.5)
    for name, js in SET.items():
        await b.js(js + "miniSrc.clear();applyTheme('light');", 0.3)
        # galeria em Lista, categoria Harry Potter (muita pele, creme e marrom) — miniaturas grandes (cartões)
        await b.js("""(async()=>{openGallery({cat:'harry-potter'});await new Promise(r=>setTimeout(r,500));
            try{setTplView('list')}catch(e){} await new Promise(r=>setTimeout(r,500));
            const m=document.getElementById('tplMain');if(m)m.scrollTop=0})()""", 0.8)
        await b.shot(OUT + 'thumbs_%s_lista.png' % name)
        # blocos: várias categorias com miniaturas pequenas
        await b.js("""(async()=>{try{setTplView('blocks')}catch(e){} await new Promise(r=>setTimeout(r,600));const m=document.getElementById('tplMain');if(m)m.scrollTop=0})()""", 0.8)
        await b.shot(OUT + 'thumbs_%s_blocos.png' % name)
        await b.js("try{document.getElementById('dlgTemplates').close()}catch(e){}", 0.2)
        print(name, 'ok')
    await b.close()

asyncio.run(main())
