"""Capturas de estado de várias telas: python t_shots.py TAG [tela ...]   telas: home gal lista novos td edit montar  (claro/escuro; desktop 1280x800 e celular 390x844)"""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
TAG = sys.argv[1] if len(sys.argv) > 1 else 'x'
WANT = sys.argv[2:] or ['home', 'gal', 'lista', 'novos', 'td', 'edit', 'montar']


async def state(b, name):
    """leva a página ao estado `name` (parte sempre da tela inicial)"""
    await b.js("document.querySelectorAll('dialog[open]').forEach(d=>d.close());if(typeof goHome==='function'&&document.body.dataset.view!=='home')setView('home',false)", 0.6)
    if name == 'home':
        await b.js("document.getElementById('home').scrollTop=0", 0.4)
    elif name == 'gal':
        await b.js("tplView='blocks';openGallery()", 1.2)
    elif name == 'lista':
        await b.js("tplView='list';openGallery({cat:'dragon-ball'})", 1.2)
    elif name == 'novos':
        await b.js("openNews()", 1.2)
    elif name == 'td':
        await b.js("openGallery();setPlates('d')", 1.4)
    elif name in ('edit', 'montar'):
        await b.js("openById(window.TEMPLATES.find(t=>/Pikachu sentado/.test(t.name)).id)", 1.0)
        if name == 'montar':
            await b.js("setMode('assemble')", 1.2)


async def main():
    for dev, (w, h, sc, mob) in {'desktop': (1280, 800, 1, False), 'mobile': (390, 844, 1.5, True)}.items():
        b = B2(w=w, h=h, port=9340)
        await b.start()
        try:
            await b.send('Log.enable')
            await b.viewport(w, h, sc, mob)
            await b.goto('http://localhost:8765/index.html?x=' + TAG, 3.8)
            for theme in ('light', 'dark'):
                await b.js("applyTheme('%s')" % theme, 0.5)
                for st in WANT:
                    await state(b, st)
                    await b.shot(OUT + 'sh_%s_%s_%s_%s.png' % (TAG, st, dev, theme))
            pr = [p for p in b.problems() if 'favicon' not in p]
            print(dev, 'problemas:', pr if pr else 'nenhum')
        finally:
            await b.close()
asyncio.run(main())
