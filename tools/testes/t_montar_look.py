"""Capturas da Montar para OLHAR (pedido do dono, 2026-11-04: "no modo pixel os preenchimentos ficarem o círculo azul, sem vazar as cores pra fora do
círculo", "o fundo fica opaco demais para se posicionar", "as cores parecidas ficam marcadas e atrapalham", "com as bolinhas o centro fica confuso com o código").
Grava em tools/out/: montar_look_<modo>_<cena>.png (tela inteira) e montar_look_<modo>_<cena>_zoom.png (recorte ampliado em volta do alvo ou da linha).
Cenas: base (1º passo da Cor por cor), alvo (cor com parecida escolhida, caminho até a conta), linha (Linha por linha, 2 linhas, com os códigos), escuro (alvo no tema escuro).
Modos: pixel e contas. Imprime o que a cena mostra (cor, parecidas, selo no quadro) e os erros de página.
Rodar: python -m http.server 8765 na raiz do projeto e  python -u tools/testes/t_montar_look.py"""
import asyncio, sys, json, os, base64, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=montarlook'


async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));window.confirm=()=>true;applyTheme('light')")
        # o molde de 1 placa com mais cores (tem cores parecidas)
        r = await b.js("""(async()=>{const t=decodeTemplates().filter(t=>!t.trashed&&t.w<=50&&t.h<=50&&t.grid.filter(Boolean).length>=300).map(t=>[new Set(t.grid.filter(Boolean)).size,t]).sort((a,b)=>b[0]-a[0])[0][1];openTpl(t);await new Promise(r=>setTimeout(r,500));
            setMode('assemble');await new Promise(r=>setTimeout(r,400));S.done.fill(0);asmChanged();return t.name+' '+t.w+'x'+t.h})()""")
        print('molde:', r)
        await asyncio.sleep(0.6)

        async def crop(path, box, k=2):
            img = Image.open(path)
            x0, y0, x1, y1 = [int(round(v)) for v in box]
            x0, y0 = max(0, x0), max(0, y0)
            x1, y1 = min(img.width, x1), min(img.height, y1)
            c = img.crop((x0, y0, x1, y1))
            c = c.resize((c.width * k, c.height * k), Image.NEAREST)
            c.save(path.replace('.png', '_zoom.png'))

        for style in ('pixel', 'bead'):
            tag = 'pixel' if style == 'pixel' else 'contas'
            await b.js(f"S.style='{style}';$$('#styleSeg button').forEach(x=>x.classList.toggle('on',x.dataset.style===S.style));S.done.fill(0);asmChanged();S.asm.view='color';S.asm.color=0;S.asm.tgt=-1;renderAssemble();zoomAt(22);requestDraw()", 0.6)
            # 1º passo: a linha de base
            await b.js("cgFocus()", 0.9)
            p = OUT + f'montar_look_{tag}_base.png'
            await b.shot(p)
            box = json.loads(await b.js("JSON.stringify((()=>{const rc=cv.getBoundingClientRect(),y=cgBase().y,cs=S.zoom;return [rc.left,rc.top+RULER+(y-3)*cs,rc.left+Math.min(rc.width,620),rc.top+RULER+(y+1)*cs+8]})())"))
            await crop(p, box)
            # Base pronta, cor com parecida e o caminho mais comprido possível
            info = json.loads(await b.js("""JSON.stringify((()=>{cgPlace();const used=[];for(let v=1;v<=NCOL;v++)if(counts[v])used.push(v);
              const cand=used.filter(v=>confOf(v).length).map(v=>{S.asm.color=v;S.asm.tgt=-1;const t=cgTarget(),r=t>=0?cgRef(t):-1;if(t<0||r<0)return [v,-99];
                const dv=Math.abs(((t/S.w)|0)-((r/S.w)|0)),dh=Math.abs(t%S.w-r%S.w),n=dv+dh;return [v,(dv&&dh?10:0)+(n>=4&&n<=14?10:0)-Math.abs(n-8)*.1]}).sort((a,b)=>b[1]-a[1]);      // cena típica: caminho em L de 4 a 14 casas
              const v=cand.length?cand[0][0]:used[0];S.asm.color=v;S.asm.tgt=-1;renderAssemble();requestDraw();cgFocus();
              return {cor:PALETTE[v-1].code,parecidas:confOf(v).map(q=>PALETTE[q.v-1].code),seloNoQuadro:!!document.querySelector('.cguide .conf'),quadro:document.querySelector('.cguide').innerText.replace(/\\s+/g,' ')}})())"""))
            print(tag, 'alvo:', info)
            await asyncio.sleep(1.0)
            p = OUT + f'montar_look_{tag}_alvo.png'
            await b.shot(p)
            box = json.loads(await b.js("""JSON.stringify((()=>{const rc=cv.getBoundingClientRect(),cs=S.zoom,t=cgTarget(),r=cgRef(t),X=i=>rc.left+RULER+mx(i%S.w)*cs,Y=i=>rc.top+RULER+((i/S.w)|0)*cs;
              const xs=[X(t),X(r)],ys=[Y(t),Y(r)];return [Math.min(...xs)-4*cs,Math.min(...ys)-3*cs,Math.max(...xs)+5*cs,Math.max(...ys)+3*cs]})())"""))
            await crop(p, box)
            # tema escuro, mesma cena
            await b.js("applyTheme('dark')", 0.8)
            p = OUT + f'montar_look_{tag}_escuro.png'
            await b.shot(p)
            await crop(p, box)
            await b.js("applyTheme('light')", 0.8)
            # Linha por linha, 2 linhas, com os códigos nas contas
            await b.js("S.asm.view='row';setAsmSpan(2);S.asm.row=groupStart(Math.floor(S.h/2));renderAssemble();zoomAt(26);requestDraw();scrollToRow()", 1.0)
            p = OUT + f'montar_look_{tag}_linha.png'
            await b.shot(p)
            box = json.loads(await b.js("JSON.stringify((()=>{const rc=cv.getBoundingClientRect(),cs=S.zoom,y=S.asm.row;return [rc.left,rc.top+RULER+(y-1)*cs,rc.left+Math.min(rc.width,700),rc.top+RULER+(y+rowSpanLen(y)+1)*cs]})())"))
            await crop(p, box)
            await b.js("setAsmSpan(1)", 0.3)
        print('erros de página:', await b.js("JSON.stringify(window.__erros)"))
    finally:
        await b.close()

asyncio.run(main())
