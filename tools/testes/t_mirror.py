import asyncio, sys, json, base64
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=mir9'

# cor do pixel (em coordenadas da tela) no canvas principal
PIX = """window.__pix=(cx,cy)=>{const dpr=window.devicePixelRatio||1;const d=cv.getContext('2d').getImageData(Math.round(cx*dpr),Math.round(cy*dpr),1,1).data;return [d[0],d[1],d[2],d[3]]};"""


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)))")
        await b.js(PIX)
        print('molde:', await b.js("""(async()=>{const all=decodeTemplates();const t=all.find(t=>/^Pikachu/.test(t.name)&&t.w<=50&&t.h<=50);openTpl(t);await new Promise(r=>setTimeout(r,500));
          S.style='pixel';S.showGrid=false;S.showCodes=false;return t.name+' '+t.w+'x'+t.h})()"""))
        print('padrão do espelho:', await b.js("S.asm.mirror"), '| localStorage:', await b.js("localStorage.getItem('beadstudio.asmmirror')"))

        # 1) Criar: não espelha
        r = await b.js("""(async()=>{setMode('create');await new Promise(r=>setTimeout(r,300));return JSON.stringify({asmMir:asmMir(),mx5:mx(5)})})()""")
        print('criar:', r)

        # 2) Montar espelhada: cores na tela batem com o desenho invertido
        r = await b.js("""(async()=>{setMode('assemble');await new Promise(r=>setTimeout(r,500));
          S.asm.row=groupStart(26);renderAssemble();requestDraw();await new Promise(r=>setTimeout(r,400));
          const y=S.asm.row,w=S.w,cs=S.zoom,rc=cv.getBoundingClientRect(),res={y,mir:asmMir(),ok:0,bad:0,okNormal:0,ex:[]};
          const acc=getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();const ac=[1,3,5].map(i=>parseInt(acc.slice(i,i+2),16));
          const hexRgb=h=>[1,3,5].map((i,k)=>Math.round(parseInt(h.slice(i,i+2),16)*.88+ac[k]*.12));      // a linha atual tem um véu de 12% da cor de destaque
          for(let x=0;x<w;x++){const v=S.grid[y*w+x];if(!v)continue;
            const want=hexRgb(PALETTE[v-1].hex);
            const dx=w-1-x;                                     // coluna na tela (espelhada)
            const p=__pix(RULER+dx*cs+cs*.5,RULER+y*cs+cs*.1);
            const near=(a,b)=>Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1])+Math.abs(a[2]-b[2])<20;
            if(near(p,want))res.ok++;else{res.bad++;if(res.ex.length<4)res.ex.push([x,PALETTE[v-1].code,p])}
            const q=__pix(RULER+x*cs+cs*.5,RULER+y*cs+cs*.1);if(near(q,want))res.okNormal++;      // sem espelho (só para comparar)
          }
          return JSON.stringify(res)})()""")
        print('pixels da linha atual:', r)

        # 3) cellAt: um clique no centro da coluna da tela dx devolve a coluna lógica w-1-dx
        r = await b.js("""(()=>{const rc=cv.getBoundingClientRect(),cs=S.zoom,w=S.w,out=[];
          for(const dx of [0,3,w-1]){const e={clientX:rc.left+RULER+dx*cs+cs/2,clientY:rc.top+RULER+S.asm.row*cs+cs/2};out.push([dx,cellAt(e,false).x,w-1-dx,cellAt(e,true).x])}
          const rl=rulerAt({clientX:rc.left+RULER+2*cs+cs/2,clientY:rc.top+8});return JSON.stringify({cliques:out,regua_col_tela2:rl.x,esperado:w-1-2})})()""")
        print('cellAt/rulerAt:', r)

        # 4) clique de verdade (mouse) numa conta: marca a conta certa
        r = await b.js("""(()=>{const rc=cv.getBoundingClientRect(),cs=S.zoom,w=S.w,y=S.asm.row;let dx=-1;for(let k=0;k<w;k++){if(S.grid[y*w+(w-1-k)]){dx=k;break}}
          return JSON.stringify({dx,x:rc.left+RULER+dx*cs+cs/2,y:rc.top+RULER+y*cs+cs/2,lx:w-1-dx,antes:S.done[y*w+(w-1-dx)]})})()""")
        info = json.loads(r); print('alvo do clique:', info)
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=info['x'], y=info['y'])
        await b.send('Input.dispatchMouseEvent', type='mousePressed', x=info['x'], y=info['y'], button='left', clickCount=1)
        await b.send('Input.dispatchMouseEvent', type='mouseReleased', x=info['x'], y=info['y'], button='left', clickCount=1)
        await asyncio.sleep(0.4)
        r = await b.js("""JSON.stringify({marcou:S.done[S.asm.row*S.w+(S.w-1-%d)],hover:S.hover&&S.hover.x,info:document.getElementById('hoverInfo').innerText})""" % info['dx'])
        print('depois do clique:', r)
        await b.js("S.done.fill(0);asmChanged()")

        # 5) lista da linha: 1ª conta = a que está mais à esquerda da TELA
        r = await b.js("""(()=>{const y=S.asm.row,w=S.w;let first=-1,last=-1;for(let k=0;k<w;k++){if(S.grid[y*w+k]){if(first<0)first=k;last=k}}
          const runs=[...document.querySelectorAll('#runs .run')];const t0=runs[0]&&runs[0].innerText.replace(/\\s+/g,' '),t1=runs.length&&runs[runs.length-1].innerText.replace(/\\s+/g,' ');
          return JSON.stringify({linha:y+1,primeiraContaLogica:first+1,ultimaContaLogica:last+1,colunasTelaEsperadas:[w-last,w-first],primeiroItem:t0,ultimoItem:t1})})()""")
        print('lista:', r)
        await b.shot(OUT + 'mirror_montar_espelhada.png')

        # 6) seleção: texto com as colunas da tela
        r = await b.js("""(()=>{const y=S.asm.row,w=S.w,m=new Uint8Array(w*S.h);for(let x=0;x<3;x++)m[y*w+x]=1;setSel(m);const st=selStats();return JSON.stringify({onde:selWhere(st),chip:document.getElementById('selSize').textContent})})()""")
        print('seleção (lógicas 1-3):', r)
        await b.js("clearSel()")

        # 7) desligar: volta ao normal
        await b.js("document.getElementById('asmMirror').click()", 0.5)
        r = await b.js("""(()=>{const y=S.asm.row,w=S.w,cs=S.zoom,res={mir:asmMir(),ok:0,bad:0};const acc=getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();const ac=[1,3,5].map(i=>parseInt(acc.slice(i,i+2),16));const hexRgb=h=>[1,3,5].map((i,k)=>Math.round(parseInt(h.slice(i,i+2),16)*.88+ac[k]*.12));
          for(let x=0;x<w;x++){const v=S.grid[y*w+x];if(!v)continue;const want=hexRgb(PALETTE[v-1].hex),p=__pix(RULER+x*cs+cs*.5,RULER+y*cs+cs*.1);
            if(Math.abs(p[0]-want[0])+Math.abs(p[1]-want[1])+Math.abs(p[2]-want[2])<20)res.ok++;else res.bad++}
          res.nota=document.getElementById('mirNote').innerText.slice(0,60);res.menu=document.getElementById('mMirrorTxt').textContent;res.ls=localStorage.getItem('beadstudio.asmmirror');return JSON.stringify(res)})()""")
        print('desligado:', r)
        await b.shot(OUT + 'mirror_montar_normal.png')

        # 8) liga pelo menu
        r = await b.js("""(()=>{document.getElementById('mMirror').click();return JSON.stringify({mir:S.asm.mirror,menu:document.getElementById('mMirrorTxt').textContent,box:document.getElementById('asmMirror').checked,ls:localStorage.getItem('beadstudio.asmmirror')})})()""")
        print('ligado pelo menu:', r)

        # 9) guia em PNG: espelhado x normal
        for mir in (True, False):
            await b.js("S.asm.mirror=%s" % ('true' if mir else 'false'))
            d = await b.js("""(()=>{const c=renderOffscreen(28,{guide:true});return c.toDataURL('image/png')})()""")
            open(OUT + 'mirror_guia_%s.png' % ('espelhado' if mir else 'normal'), 'wb').write(base64.b64decode(d.split(',')[1]))
        await b.js("S.asm.mirror=true")
        print('guias salvos')

        # 10) strip do painel (2 linhas) espelhado: cores batem
        await b.js("S.asm.mirror=true;setAsmSpan(2)", 0.5)
        r = await b.js("""(()=>{const cvs=document.getElementById('rowStrip'),rows=groupRows(S.asm.row),dpr=window.devicePixelRatio||1,cell=cvs.clientWidth/S.w;let ok=0,bad=0;const c=cvs.getContext('2d');
          const hexRgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
          rows.forEach((y,k)=>{for(let x=0;x<S.w;x++){const v=S.grid[y*S.w+x];if(!v||S.done[y*S.w+x])continue;
            const cx=(mx(x)+.5)*cell,cy=13+k*22;const d=c.getImageData(Math.round(cx*dpr),Math.round(cy*dpr),1,1).data;const want=hexRgb(PALETTE[v-1].hex);
            if(Math.abs(d[0]-want[0])+Math.abs(d[1]-want[1])+Math.abs(d[2]-want[2])<30)ok++;else bad++}});
          return JSON.stringify({linhas:rows,ok,bad})})()""")
        print('tira do painel:', r)
        await b.shot(OUT + 'mirror_montar_2linhas.png')
        print('erros de página:', await b.js("JSON.stringify(window.__erros)"))
        await b.js("setAsmSpan(1)")
    finally:
        await b.close()

asyncio.run(main())
