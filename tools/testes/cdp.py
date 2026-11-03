"""Chrome headless por CDP: abre uma página, roda JS e salva capturas (o painel do navegador do app não captura direito com o painel oculto)."""
import asyncio, json, os, subprocess, tempfile, time, base64, urllib.request, shutil
import websockets

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


class Browser:
    def __init__(self, port=9333, w=1280, h=800, scale=1.0):
        self.port, self.w, self.h, self.scale = port, w, h, scale
        self.prof = tempfile.mkdtemp(prefix='cdp_')
        self.proc = None; self.ws = None; self.n = 0

    async def start(self):
        self.proc = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={self.port}', f'--user-data-dir={self.prof}',
                                      f'--window-size={self.w},{self.h}', '--hide-scrollbars', '--no-first-run', '--disable-extensions', 'about:blank'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{self.port}/json'))
                pg = [t for t in tabs if t.get('type') == 'page'][0]
                break
            except Exception:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError('Chrome não respondeu')
        self.ws = await websockets.connect(pg['webSocketDebuggerUrl'], max_size=64 * 1024 * 1024)
        await self.send('Page.enable'); await self.send('Runtime.enable')
        await self.viewport(self.w, self.h, self.scale)

    async def send(self, method, **params):
        self.n += 1; i = self.n
        await self.ws.send(json.dumps({'id': i, 'method': method, 'params': params}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get('id') == i:
                if 'error' in m: raise RuntimeError(f'{method}: {m["error"]}')
                return m.get('result', {})

    async def viewport(self, w, h, scale=1.0, mobile=False):
        self.w, self.h = w, h
        await self.send('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=scale, mobile=mobile)

    async def goto(self, url, wait=1.2):
        await self.send('Page.navigate', url=url)
        await asyncio.sleep(wait)

    async def js(self, expr, wait=0.0):
        r = await self.send('Runtime.evaluate', expression=expr, awaitPromise=True, returnByValue=True)
        if wait: await asyncio.sleep(wait)
        if 'exceptionDetails' in r:
            d = r['exceptionDetails']; raise RuntimeError('JS: ' + (d.get('exception', {}).get('description') or d.get('text')))
        return r['result'].get('value')

    async def shot(self, path, clip=None):
        p = {'format': 'png'}
        if clip: p['clip'] = dict(x=clip[0], y=clip[1], width=clip[2], height=clip[3], scale=1)
        r = await self.send('Page.captureScreenshot', **p)
        open(path, 'wb').write(base64.b64decode(r['data']))
        return path

    async def close(self):
        try:
            if self.ws: await self.ws.close()
        finally:
            if self.proc: self.proc.terminate()
            time.sleep(0.5); shutil.rmtree(self.prof, ignore_errors=True)
