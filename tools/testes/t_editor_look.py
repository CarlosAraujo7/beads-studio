"""Capturas do editor depois da camada estática: Criar (cursor, régua) e Montar (linha atual, progresso, espelhado)."""
import asyncio, sys, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep


async def main():
    b = B2(w=1280, h=900, port=9441)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=look%d' % (int(time.time()) % 100000), 3.5)
        await b.js("openTpl(decodeTemplates().find(t=>/Pikachu sentado/.test(t.name)))", 0.9)
        await b.js("setMode('create');S.zoom=14;layout();draw()", 0.5)
        # passa o mouse de verdade sobre o desenho (cursor + régua)
        box = await b.js("(()=>{const r=cv.getBoundingClientRect();return JSON.stringify({x:r.x,y:r.y})})()")
        import json
        bx = json.loads(box)
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=bx['x'] + 30 + 14 * 22, y=bx['y'] + 30 + 14 * 18)
        await asyncio.sleep(0.4)
        await b.shot(OUT + 'editor_criar_depois.png')
        await b.js("setMode('assemble')", 0.8)
        await b.shot(OUT + 'editor_montar_depois.png')
        pr = [p for p in b.problems() if 'favicon' not in p]
        print('erros de página:', pr)
    finally:
        await b.close()
asyncio.run(main())
