"""Captura a seção Novidades em repouso e com o mouse no 1º cartão (para olhar o resultado)."""
import asyncio, sys, time, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep


async def main():
    b = B2(w=1280, h=900, port=9452)
    await b.start()
    try:
        await b.goto('http://localhost:8765/index.html?x=look%d' % (int(time.time()) % 100000), 3.5)
        await b.js("document.getElementById('homeNew').scrollIntoView({block:'center'})", 0.6)
        r = json.loads(await b.js("(()=>{const r=document.getElementById('homeNew').getBoundingClientRect();return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height})})()"))
        clip = (max(0, r['x'] - 10), max(0, r['y'] - 10), min(1280, r['w'] + 20), r['h'] + 20)
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=5, y=5); await asyncio.sleep(0.5)
        await b.shot(OUT + 'novidades_repouso.png', clip=clip)
        t = json.loads(await b.js("(()=>{const t=document.getElementById('homeNewRow').children[0].getBoundingClientRect();return JSON.stringify({x:t.x+t.width/2,y:t.y+t.height/2})})()"))
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=t['x'], y=t['y']); await asyncio.sleep(0.7)
        await b.shot(OUT + 'novidades_hover_primeiro.png', clip=clip)
    finally:
        await b.close()
asyncio.run(main())
