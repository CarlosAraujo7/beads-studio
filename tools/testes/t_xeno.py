import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    try:
        await b.goto('http://localhost:8765/index.html?x=xeno2', 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)))")
        print('catálogo:', await b.js("TEMPLATES.length"))
        r = await b.js("""(async()=>{const t=decodeTemplates().find(t=>t.name==='Xenomorfo (Alien, chibi)');openTpl(t);await new Promise(r=>setTimeout(r,800));
          const cnt={};document.querySelectorAll('#counts .crow, .crow').forEach(e=>{});return JSON.stringify({nome:t.name,S:[S.w,S.h,total],view:view})})()""")
        print('abrir Xenomorfo:', r)
        print('erros:', await b.js("JSON.stringify(window.__erros)"))
    finally:
        pass
asyncio.run(main())
