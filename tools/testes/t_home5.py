"""Conferência final: seção Categorias em 1280, 768 e 390 (nomes longos em até 2 linhas) e a tela inteira em 1280 claro."""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep


async def main():
    b = B2(w=1280, h=1500, port=9338)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=final', 4.2)
        await b.js("applyTheme('light');document.getElementById('home').scrollTop=0", 0.8)
        await b.shot(OUT + 'home_final_1280.png')
        for w in (768, 390):
            await b.viewport(w, 1500, 1.5 if w < 500 else 1, w < 500)
            await asyncio.sleep(0.8)
            await b.js("document.getElementById('homeCats').scrollIntoView({block:'start'})", 0.6)
            await b.shot(OUT + 'home_final_cats_%d.png' % w)
        clip = await b.js("JSON.stringify([...document.querySelectorAll('.cattile b')].map(e=>[e.textContent, e.scrollHeight>e.clientHeight+1]))")
        print('nomes cortados (true = passou de 2 linhas):', [x for x in json.loads(clip) if x[1]])
        pr = [p for p in b.problems() if 'favicon' not in p]
        print('problemas:', pr if pr else 'nenhum')
    finally:
        await b.close()
asyncio.run(main())
