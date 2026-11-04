"""Ordenação "Minha ordem" da galeria com arrasto DE VERDADE (pedidos do dono, 2026-11-04: criar a ordem própria e depois "melhorar a função de poder arrastar
os moldes dentro da categoria e colocar na ordem que quiser").
Usa o MOUSE de verdade (Input.dispatchMouseEvent: pressionar, mover em passos, soltar) e confere: durante o arrasto aparece o molde levantado e o lugar vazio já
anda (os outros abrem espaço); soltar põe o molde ali e guarda (beadstudio.cats -> myorder, e no "Gravar no catálogo"); Esc cancela; Ctrl+Z desfaz; clique simples
ainda abre o molde; nos Blocos a caixa de miniaturas rola sozinha perto da borda; soltar em outra categoria muda de categoria e põe no lugar; recarregar mantém;
nas outras ordens, soltar (arrasto nativo) um molde sobre outro da mesma categoria passa para "Minha ordem".
Rodar: python -m http.server 8765 na raiz do projeto e  python -u tools/testes/t_myorder.py"""
import asyncio, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=myorder2'
CAT = 'evangelion'          # 6 moldes

HELP = r"""
window.__ids=sel=>[...document.querySelectorAll(sel)].map(x=>x.dataset.id);
window.__c=(el,fx,fy)=>{const r=el.getBoundingClientRect();return [r.left+r.width*(fx??.5),r.top+r.height*(fy??.5)]};
window.__setSort=v=>{const s=document.querySelector('#tplSort');s.value=v;s.dispatchEvent(new Event('change',{bubbles:true}))};
window.__html5=(src,dst,right)=>{const dt=new DataTransfer(),r=dst.getBoundingClientRect(),x=right?r.right-4:r.left+4,y=r.top+r.height/2;
  const ev=(t,el)=>el.dispatchEvent(new DragEvent(t,{bubbles:true,cancelable:true,dataTransfer:dt,clientX:x,clientY:y}));ev('dragstart',src);ev('dragover',dst);ev('drop',dst);ev('dragend',src)};
"""


async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    ok = True
    def check(cond, msg):
        nonlocal ok
        ok = ok and bool(cond); print('OK   ' if cond else 'FALHA', msg)
    async def mouse(t, x, y, buttons=0):
        await b.send('Input.dispatchMouseEvent', type=t, x=float(x), y=float(y), button='left' if t != 'mouseMoved' or buttons else 'none', buttons=buttons, clickCount=1 if t != 'mouseMoved' else 0)
    async def press(x, y):
        await mouse('mouseMoved', x, y); await mouse('mousePressed', x, y, 1)
    async def glide(x0, y0, x1, y1, n=12):
        for k in range(1, n + 1):
            await mouse('mouseMoved', x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n, 1); await asyncio.sleep(0.02)
    async def release(x, y):
        await mouse('mouseReleased', x, y); await asyncio.sleep(0.35)
    async def ids(sel): return json.loads(await b.js(f"JSON.stringify(__ids(\"{sel}\"))"))
    async def pt(sel, i, fx=.5, fy=.5): return json.loads(await b.js(f"JSON.stringify(__c(document.querySelectorAll(\"{sel}\")[{i}],{fx},{fy}))"))
    async def open_cat(cat, view):
        await b.js(f"(async()=>{{openGallery({{}});await new Promise(r=>setTimeout(r,700));tplCat='{cat}';setTplView('{view}');await new Promise(r=>setTimeout(r,600))}})()")
    try:
        await b.goto(URL, 2.5)
        await b.js("localStorage.removeItem('beadstudio.cats');localStorage.removeItem('beadstudio.tplsort')")
        await b.goto(URL, 2.5)
        await b.js(HELP + "window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));window.confirm=()=>true")
        await open_cat(CAT, 'list')
        sec = f".tsec[data-cat='{CAT}'] .tcard"
        cat0 = await ids(sec)
        await b.js("__setSort('my')"); await asyncio.sleep(0.4)
        check(await ids(sec) == cat0 and len(cat0) >= 4, f'Minha ordem sem nada salvo = ordem do catálogo ({len(cat0)} moldes)')
        check(await b.js("document.querySelector('#tplSections').classList.contains('sorting')&&document.querySelector('.tcard').draggable===false"), 'em Minha ordem o arrasto é o novo (sem o nativo do navegador)')
        # ---- 1. Lista: arrastar o último para o começo, com o mouse
        x0, y0 = await pt(sec, len(cat0) - 1); x1, y1 = await pt(sec, 0, .2)
        await press(x0, y0); await glide(x0, y0, x1, y1)
        mid = json.loads(await b.js(f"JSON.stringify({{ghost:!!document.querySelector('.srt-ghost'),ph:(document.querySelector(\"{sec}\")||{{}}).classList?.contains('srt-ph')}})"))
        check(mid['ghost'] and mid['ph'], f'durante o arrasto: molde levantado e o lugar vazio já no começo (os outros abriram espaço) {mid}')
        await release(x1, y1)
        exp = [cat0[-1]] + cat0[:-1]
        check(await ids(sec) == exp, 'soltou: o último foi para o começo')
        check(await b.js("document.querySelector('#dlgTemplates').open&&view!=='edit'"), 'soltar não abriu o molde')
        check(not await b.js("!!document.querySelector('.srt-ghost')"), 'o molde levantado some no fim')
        saved = json.loads(await b.js(f"JSON.stringify((JSON.parse(localStorage.getItem('beadstudio.cats')||'{{}}').myorder||{{}})['{CAT}'])"))
        check(saved == exp, 'ordem guardada (beadstudio.cats, myorder)')
        check(json.loads(await b.js(f"JSON.stringify(buildBaked().cfg.myorder['{CAT}'])")) == exp, 'vai no "Gravar no catálogo"')
        # ---- 2. Ctrl+Z desfaz
        await b.send('Input.dispatchKeyEvent', type='keyDown', key='z', code='KeyZ', windowsVirtualKeyCode=90, modifiers=2)
        await b.send('Input.dispatchKeyEvent', type='keyUp', key='z', code='KeyZ', windowsVirtualKeyCode=90, modifiers=2)
        await asyncio.sleep(0.4)
        check(await ids(sec) == cat0, 'Ctrl+Z desfez a mudança')
        # ---- 3. Esc cancela no meio
        x0, y0 = await pt(sec, 0); x1, y1 = await pt(sec, 2, .8)
        await press(x0, y0); await glide(x0, y0, x1, y1)
        await b.send('Input.dispatchKeyEvent', type='keyDown', key='Escape', code='Escape', windowsVirtualKeyCode=27)
        await b.send('Input.dispatchKeyEvent', type='keyUp', key='Escape', code='Escape', windowsVirtualKeyCode=27)
        await release(x1, y1)
        check(await ids(sec) == cat0 and await b.js("document.querySelector('#dlgTemplates').open"), 'Esc cancelou e a galeria continuou aberta')
        # ---- 4. de novo: o primeiro para depois do terceiro (metade direita)
        x0, y0 = await pt(sec, 0); x1, y1 = await pt(sec, 2, .85)
        await press(x0, y0); await glide(x0, y0, x1, y1); await release(x1, y1)
        exp2 = [cat0[1], cat0[2], cat0[0]] + cat0[3:]
        check(await ids(sec) == exp2, f'primeiro para depois do terceiro: {await ids(sec)}')
        await b.shot(OUT + 'myorder_lista.png')
        # ---- 5. clique simples ainda abre o molde
        x0, y0 = await pt(sec, 1)
        await press(x0, y0); await release(x0, y0)
        check(await b.js("view==='edit'"), 'clique simples (sem arrastar) abre o molde')
        await b.js("goBack&&goBack()"); await asyncio.sleep(0.8)
        # ---- 6. recarregar mantém
        await b.goto(URL, 2.5)
        await b.js(HELP + "window.confirm=()=>true;window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)))")
        await open_cat(CAT, 'list')
        check(await b.js("document.querySelector('#tplSort').value") == 'my' and await ids(sec) == exp2, 'depois de recarregar: Minha ordem e a mesma ordem')
        # ---- 7. Blocos: a caixa de miniaturas rola sozinha perto da borda de baixo
        await open_cat('all', 'blocks')
        big = await b.js("(()=>{const t=[...document.querySelectorAll('.cblock')].find(x=>x.dataset.cat!=='mine'&&x.querySelector('.cthumbs')&&x.querySelector('.cthumbs').scrollHeight>x.querySelector('.cthumbs').clientHeight+40);return t?t.dataset.cat:''})()")
        blk = f".cblock[data-cat='{big}']"
        await b.js(f"document.querySelector(\"{blk}\").scrollIntoView({{block:'center'}})"); await asyncio.sleep(0.4)
        mini = f"{blk} .mini"
        big0 = await ids(mini)
        x0, y0 = await pt(mini, 0)
        box = json.loads(await b.js(f"JSON.stringify((()=>{{const t=document.querySelector(\"{blk} .cthumbs\"),r=t.getBoundingClientRect();return [r.left+r.width/2,r.bottom-8,t.scrollHeight>t.clientHeight]}})())"))
        await press(x0, y0); await glide(x0, y0, box[0], box[1], 10)
        await asyncio.sleep(1.2)                                          # segurando perto da borda: a caixa rola
        st = await b.js(f"document.querySelector(\"{blk} .cthumbs\").scrollTop")
        await release(box[0], box[1])
        big1 = await ids(mini)
        pos = big1.index(big0[0])
        check(box[2] and st > 40 and pos > 15, f'Blocos: a caixa rolou sozinha (scrollTop {st}) e o molde foi para a posição {pos + 1} de {len(big1)}')
        # ---- 8. outra categoria: muda e entra no lugar
        await b.js(f"document.querySelector(\".cblock[data-cat='{CAT}']\").scrollIntoView({{block:'center'}})"); await asyncio.sleep(0.4)
        src_id = await b.js(f"(()=>{{const m=[...document.querySelectorAll('.cblock .mini')].find(x=>{{const c=x.closest('.cblock').dataset.cat;const r=x.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2,u=document.elementFromPoint(cx,cy);return c!=='{CAT}'&&c!=='mine'&&u&&u.closest&&u.closest('.mini')===x}});return m?m.dataset.id:''}})()")
        x0, y0 = await pt(f".mini[data-id='{src_id}']", 0); xh, yh = await pt(f".cblock[data-cat='{CAT}'] header", 0, .5, .5)
        await press(x0, y0); await glide(x0, y0, xh, yh, 16)              # 1º entra no bloco (os blocos podem se mexer quando ele sai do de origem)
        await asyncio.sleep(0.3)
        x1, y1 = await pt(f".cblock[data-cat='{CAT}'] .mini:not(.srt-ph)", 0, .85)   # e então mira o que está na tela agora, como quem olha
        await glide(xh, yh, x1, y1, 8); await asyncio.sleep(0.3)
        shown = json.loads(await b.js(f"JSON.stringify([...document.querySelectorAll(\".cblock[data-cat='{CAT}'] .mini\")].map(x=>x.classList.contains('srt-ph')?'@':x.dataset.id))"))
        await release(x1, y1)
        await asyncio.sleep(0.4)
        e3 = await ids(f".cblock[data-cat='{CAT}'] .mini")
        want = [src_id if x == '@' else x for x in shown]
        check('@' in shown and e3 == want and len(e3) == len(exp2) + 1, f'molde de outra categoria entrou em {CAT} exatamente onde o lugar vazio estava (posição {shown.index("@") + 1 if "@" in shown else "?"})')
        await b.shot(OUT + 'myorder_blocos.png')
        # ---- 9. nas outras ordens: soltar sobre outro da mesma categoria passa para Minha ordem (a partir da ordem à vista)
        await open_cat(CAT, 'list')
        await b.js("__setSort('az')"); await asyncio.sleep(0.4)
        az = await ids(sec)
        await b.js(f"(()=>{{const c=document.querySelectorAll(\"{sec}\");__html5(c[0],c[2],true)}})()"); await asyncio.sleep(0.5)
        exp4 = [az[1], az[2], az[0]] + az[3:]
        check(await b.js("document.querySelector('#tplSort').value") == 'my' and await ids(sec) == exp4, 'em A–Z, soltar sobre outro da mesma categoria passou para Minha ordem com a ordem à vista')
        # ---- 10. toque: segurar um instante e arrastar (celular/tablet); passar o dedo rápido continua rolando a galeria
        await b.send('Emulation.setTouchEmulationEnabled', enabled=True, maxTouchPoints=1)
        await b.js("__setSort('my')"); await asyncio.sleep(0.4)
        t0 = await ids(sec)
        x0, y0 = await pt(sec, 0); x1, y1 = await pt(sec, 2, .85)
        tp = lambda x, y: [{'x': float(x), 'y': float(y), 'id': 1}]
        await b.send('Input.dispatchTouchEvent', type='touchStart', touchPoints=tp(x0, y0))
        await asyncio.sleep(0.5)                                          # segurou
        for k in range(1, 11):
            await b.send('Input.dispatchTouchEvent', type='touchMove', touchPoints=tp(x0 + (x1 - x0) * k / 10, y0 + (y1 - y0) * k / 10)); await asyncio.sleep(0.03)
        await b.send('Input.dispatchTouchEvent', type='touchEnd', touchPoints=[]); await asyncio.sleep(0.5)
        t1 = await ids(sec)
        check(t1 == [t0[1], t0[2], t0[0]] + t0[3:], f'toque: segurar e arrastar levou o primeiro para depois do terceiro ({t1[:3]})')
        await b.send('Input.dispatchTouchEvent', type='touchStart', touchPoints=tp(x0, y0))
        for k in range(1, 6):
            await b.send('Input.dispatchTouchEvent', type='touchMove', touchPoints=tp(x0 + 60 * k / 5, y0)); await asyncio.sleep(0.02)
        await b.send('Input.dispatchTouchEvent', type='touchEnd', touchPoints=[]); await asyncio.sleep(0.5)
        check(await ids(sec) == t1 and not await b.js("!!document.querySelector('.srt-ghost')"), 'toque: passar o dedo sem segurar não arrasta molde')
        await b.send('Emulation.setTouchEmulationEnabled', enabled=False)
        errs = await b.js("JSON.stringify(window.__erros)")
        check(errs == '[]', f'erros de página: {errs}')
        print('RESUMO:', 'OK' if ok else 'FALHA')
    finally:
        await b.close() if hasattr(b, 'close') else None

asyncio.run(main())
