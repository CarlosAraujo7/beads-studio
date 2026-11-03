"""Tela inicial nova: capturas (claro/escuro, desktop/celular) + erros de console + conferências por JS."""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
TAG = sys.argv[1] if len(sys.argv) > 1 else 'depois'


class B2(Browser):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.events = []

    async def send(self, method, **params):
        import json as J
        self.n += 1; i = self.n
        await self.ws.send(J.dumps({'id': i, 'method': method, 'params': params}))
        while True:
            m = J.loads(await self.ws.recv())
            if 'id' not in m:
                self.events.append(m); continue
            if m.get('id') == i:
                if 'error' in m: raise RuntimeError(f'{method}: {m["error"]}')
                return m.get('result', {})

    def problems(self):
        out = []
        for m in self.events:
            md = m.get('method')
            if md == 'Runtime.exceptionThrown':
                d = m['params']['exceptionDetails']; out.append('EXC ' + (d.get('exception', {}).get('description') or d.get('text', '')))
            elif md == 'Runtime.consoleAPICalled' and m['params']['type'] in ('error', 'assert'):
                out.append('CONSOLE ' + ' '.join(str(a.get('value', a.get('description', ''))) for a in m['params']['args']))
            elif md == 'Log.entryAdded' and m['params']['entry']['level'] == 'error':
                out.append('LOG ' + m['params']['entry']['text'] + ' ' + m['params']['entry'].get('url', ''))
        return out


async def main():
    b = B2(w=1280, h=900)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=' + TAG, 4.2)
        info = await b.js("""JSON.stringify({
          n: window.TEMPLATES.length, view: document.body.dataset.view,
          chips: document.querySelectorAll('#homeChips .hchip').length,
          track: document.querySelectorAll('#homeTrack .hm').length, marqHidden: document.getElementById('homeMarq').hidden,
          fl: document.querySelectorAll('#homeFl .hfl').length,
          dayHidden: document.getElementById('homeDay').hidden, dayName: document.getElementById('dayName').textContent,
          stats: [...document.querySelectorAll('#homeStats b')].map(b => b.textContent),
          news: document.querySelectorAll('#homeNewRow .tile').length, cats: document.querySelectorAll('#homeCatGrid .cattile').length,
          ph: document.getElementById('homeSearch').placeholder,
          hactBg: getComputedStyle(document.querySelector('.hact.g-violet')).backgroundImage.slice(0, 120),
          acc2: getComputedStyle(document.documentElement).getPropertyValue('--acc2'),
          anim: document.getElementById('home').classList.contains('anim')
        })""")
        print('INFO', info)
        await b.viewport(1280, 900)
        await b.js("applyTheme('light');window.scrollTo(0,0);document.getElementById('home').scrollTop=0", 0.8)
        await b.shot(OUT + 'home_%s_first_light.png' % TAG)
        await b.viewport(1280, 2300)
        await asyncio.sleep(0.6)
        await b.shot(OUT + 'home_%s_desktop_light.png' % TAG)
        await b.js("applyTheme('dark')", 0.9)
        await b.shot(OUT + 'home_%s_desktop_dark.png' % TAG)
        await b.viewport(390, 3000, 1.5, True)
        await b.js("applyTheme('light');document.getElementById('home').scrollTop=0", 1.0)
        await b.shot(OUT + 'home_%s_mobile_light.png' % TAG)
        await b.js("applyTheme('dark')", 0.8)
        await b.shot(OUT + 'home_%s_mobile_dark.png' % TAG)
        await asyncio.sleep(0.3)
        pr = b.problems()
        print('PROBLEMAS:', json.dumps(pr, ensure_ascii=False) if pr else 'nenhum')
    finally:
        await b.close()
if __name__ == '__main__':
    asyncio.run(main())
