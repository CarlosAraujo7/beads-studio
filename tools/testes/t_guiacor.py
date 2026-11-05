"""Montar "Cor por cor": linha de base primeiro e guia da próxima conta (pedidos do dono, 2026-11-04: "andar 16 contas pra cima e colocar na conta 17, ou andar
4 pra cima, 3 pra esquerda"; "minha grade não tem número: todos os desenhos vão ser feitos com a linha de base e, a partir das contas da base, vai guiar para as
outras cores"; "explicar os números, quanto é pra andar de fato").
Confere com o MOUSE e o TECLADO de verdade: sem a base pronta, o quadro mostra o 1º passo (linha de base, com a faixa dela) e não há alvo; "Base pronta" marca a
linha de baixo; depois o alvo é a conta da cor mais baixa e a PARTIDA É SEMPRE UMA CONTA DA PLACA (nunca a borda: nenhum texto de linha/coluna contada da borda),
de preferência da base, e o quadro diz qual ("Nª conta da base, contando da esquerda"); o caminho do quadro bate com as linhas e colunas da TELA (espelhada e normal);
"sem contar a de partida" aparece; a tela aproxima para os números caberem; Coloquei (clique) e espaço marcam e passam para a seguinte, a nova partida pode ser a que
acabou de ser posta; → pula e ← volta; clicar a conta na placa marca; cor acabada mostra "Próxima cor"; botões e quadro parados em todos os estados; sem erros.
Rodar: python -m http.server 8765 na raiz do projeto e  python -u tools/testes/t_guiacor.py"""
import asyncio, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=guiacor2'

STATE = r"""(()=>{const t=cgTarget(),r=t>=0?cgRef(t):-1,b=cgBase(),g=sel=>{const e=document.querySelector(sel);if(!e)return null;const q=e.getBoundingClientRect();return [Math.round(q.left),Math.round(q.top),Math.round(q.width),Math.round(q.height)]};
  return JSON.stringify({color:S.asm.color,t,r,tx:t>=0?mx(t%S.w):-1,ty:t>=0?(t/S.w)|0:-1,rx:r>=0?mx(r%S.w):-1,ry:r>=0?(r/S.w)|0:-1,h:S.h,w:S.w,zoom:S.zoom,
    baseY:b.y,baseDone:b.done,refInBase:r>=0&&b.cells.includes(r),refDone:r>=0?S.done[r]:null,last:S.asm.last,
    left:S.asm.color?counts[S.asm.color]-doneCounts[S.asm.color]:0,
    chips:[...document.querySelectorAll('#asmNav .cg-chip')].map(c=>c.textContent.trim()),card:(document.querySelector('#asmNav .cguide')||{}).innerText||'',
    strip:!!document.querySelector('#asmNav #cgStrip'),
    go:g('#cGo'),skip:g('#cSkip'),all:g('#cAll'),none:g('#cNone'),box:g('#asmNav .cguide'),goTxt:document.querySelector('#cGo').textContent.trim(),goDis:document.querySelector('#cGo').disabled,skipTxt:document.querySelector('#cSkip').textContent.trim()})})()"""


async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    ok = True
    def check(cond, msg):
        nonlocal ok
        ok = ok and bool(cond); print('OK   ' if cond else 'FALHA', msg)
    async def st(): return json.loads(await b.js(STATE))
    async def click_at(x, y):
        for t in ('mouseMoved', 'mousePressed', 'mouseReleased'):
            await b.send('Input.dispatchMouseEvent', type=t, x=x, y=y, button='left' if t != 'mouseMoved' else 'none', buttons=1 if t == 'mousePressed' else 0, clickCount=1 if t != 'mouseMoved' else 0)
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.4)
    async def click(sel):
        p = json.loads(await b.js(f"JSON.stringify((()=>{{const r=document.querySelector(\"{sel}\").getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}})())"))
        await click_at(*p)
    async def key(k, code, vk):
        await b.send('Input.dispatchKeyEvent', type='keyDown', key=k, code=code, windowsVirtualKeyCode=vk)
        await b.send('Input.dispatchKeyEvent', type='keyUp', key=k, code=code, windowsVirtualKeyCode=vk)
        await asyncio.sleep(0.4)
    edge_words = ('coluna da esquerda', 'linha de baixo para cima', 'da borda')
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));window.confirm=()=>true")
        r = await b.js("""(async()=>{const t=decodeTemplates().filter(t=>!t.trashed&&t.w<=50&&t.h<=50&&t.grid.filter(Boolean).length>=300).map(t=>[new Set(t.grid.filter(Boolean)).size,t]).sort((a,b)=>b[0]-a[0])[0][1];openTpl(t);await new Promise(r=>setTimeout(r,500));
            setMode('assemble');await new Promise(r=>setTimeout(r,400));S.done.fill(0);asmChanged();zoomAt(14);return t.name+' '+t.w+'x'+t.h})()""")
        print('molde (o de 1 placa com mais cores):', r)
        await asyncio.sleep(0.8)
        await click("#asmSeg button[data-view='color']")
        check(await b.js("S.asm.view") == 'color', 'clique (mouse) em "Cor por cor" troca a vista')
        lugares = []
        s0 = await st(); lugares.append(('1º passo sem cor', s0))
        check(not s0['baseDone'] and 'Linha de base' in s0['card'] and s0['strip'] and s0['goTxt'] == 'Base pronta' and not s0['goDis'] and s0['t'] == -1,
              f'sem a base: o quadro mostra o 1º passo (linha de base com a faixa), o botão é "Base pronta" e não há alvo')
        await click('#asmBody .cfocus')
        s1 = await st(); lugares.append(('1º passo com cor', s1))
        check(s1['color'] > 0 and s1['t'] == -1 and 'Linha de base' in s1['card'], 'escolher uma cor antes da base: continua o 1º passo (a base vem primeiro)')
        await b.shot(OUT + 'guia_cor_base.png')
        await click('#cGo')
        s2 = await st(); lugares.append(('guia', s2))
        base_done = await b.js(f"(()=>{{const y={s1['baseY']};for(let x=0;x<S.w;x++){{const i=y*S.w+x;if(S.grid[i]&&!S.done[i])return false}}return true}})()")
        check(base_done and s2['baseDone'], '"Base pronta" marcou a linha de baixo inteira')
        dv, dh = s2['ty'] - s2['ry'], s2['tx'] - s2['rx']
        expect = ([f'↑ {-dv}'] if dv < 0 else [f'↓ {dv}'] if dv > 0 else []) + ([f'← {-dh}'] if dh < 0 else [f'→ {dh}'] if dh > 0 else [])
        check(s2['t'] >= 0 and s2['r'] >= 0 and s2['refDone'] == 1 and s2['chips'] == expect, f'guia: partida numa conta da placa, caminho {s2["chips"]} (linhas {dv}, colunas da tela {dh})')
        who = await b.js(f"(()=>{{const c=cgBase().cells,k=c.indexOf({s2['r']}),n=c.length;return k+1<=n-k?(k+1)+'ª conta da base, contando da esquerda':(n-k)+'ª conta da base, contando da direita'}})()")
        check(s2['refInBase'] and who in s2['card'], f'a primeira partida é uma conta da base e o quadro diz qual, pela ponta mais perto ("{who}")')
        check('sem contar a de partida' in s2['card'], 'o quadro explica que a contagem não inclui a conta de partida')
        check(s2['zoom'] >= 20, f'a tela aproximou para os números caberem (zoom {s2["zoom"]})')
        low = json.loads(await b.js("JSON.stringify((()=>{const o=cgOrder(S.asm.color);return {first:o[0],maxY:Math.max(...o.map(i=>(i/S.w)|0))}})())"))
        check(s2['t'] == low['first'] and s2['ty'] == low['maxY'], 'o alvo é a conta da cor mais baixa (a montagem sobe da base)')
        await asyncio.sleep(0.6)
        await b.shot(OUT + 'guia_cor_1.png')
        # Coloquei (clique de verdade): a seguinte; a partida preferida passa a ser a que acabou de ser posta, se for perto
        await click('#cGo')
        s3 = await st(); lugares.append(('depois de Coloquei', s3))
        check((await b.js(f"S.done[{s2['t']}]")) == 1 and s3['t'] != s2['t'] and s3['left'] == s2['left'] - 1 and s3['last'] == s2['t'],
              f'"Coloquei" marcou a conta e passou para a seguinte (faltam {s2["left"]} -> {s3["left"]})')
        await key(' ', 'Space', 32)
        s4 = await st()
        check((await b.js(f"S.done[{s3['t']}]")) == 1 and s4['left'] == s3['left'] - 1, 'barra de espaço marcou o alvo')
        await key('ArrowRight', 'ArrowRight', 39)
        s5 = await st()
        await key('ArrowLeft', 'ArrowLeft', 37)
        s6 = await st()
        check(s5['t'] != s4['t'] and s5['left'] == s4['left'] and s6['t'] == s4['t'], '→ pula para a seguinte e ← volta, sem marcar nada')
        lugares.append(('depois de pular', s5))
        # clicar a conta-alvo na placa (mouse de verdade) também marca
        await b.js("cgFocus()"); await asyncio.sleep(0.8)
        p = json.loads(await b.js("JSON.stringify((()=>{const t=cgTarget(),rc=cv.getBoundingClientRect(),cs=S.zoom;return [rc.left+RULER+mx(t%S.w)*cs+cs/2,rc.top+RULER+((t/S.w)|0)*cs+cs/2,t]})())"))
        if await b.js(f"(document.elementFromPoint({p[0]},{p[1]})||{{}}).id") == 'cv':
            await click_at(p[0], p[1])
            s7 = await st()
            check((await b.js(f"S.done[{p[2]}]")) == 1 and s7['t'] != p[2] and s7['last'] == p[2], 'clicar a conta na placa marca, e ela vira a "que você acabou de pôr"')
        else:
            print('PULA  clique na placa (a conta-alvo não está à vista nesta janela)')
        # caminho em L: espelhada x normal
        found = await b.js("(()=>{for(let k=0;k<400;k++){const t=cgTarget();if(t<0)return false;const r=cgRef(t);if(r>=0&&mx(t%S.w)!==mx(r%S.w)&&((t/S.w)|0)!==((r/S.w)|0))return true;S.asm.tgt=cgNext(t,1)}return false})()")
        await b.js("renderAssemble();requestDraw();cgFocus()"); await asyncio.sleep(0.9)
        sl = await st(); lugares.append(('caminho em L', sl))
        await b.shot(OUT + 'guia_cor_L.png')
        await b.js("setAsmMirror(true)"); await asyncio.sleep(0.3)
        a = await st()
        await b.js("setAsmMirror(false)"); await asyncio.sleep(0.3)
        bb = await st()
        await b.js("setAsmMirror(true)"); await asyncio.sleep(0.3)
        dha, dhb = a['tx'] - a['rx'], bb['tx'] - bb['rx']
        sides = ('←' in ''.join(a['chips']) and '→' in ''.join(bb['chips'])) or ('→' in ''.join(a['chips']) and '←' in ''.join(bb['chips']))
        check(found and dha != 0 and a['t'] == bb['t'] and a['r'] == bb['r'] and dha == -dhb and sides, f'espelhada x normal (caminho em L): colunas da tela {dha} x {dhb}, quadro {a["chips"]} x {bb["chips"]}')
        # cor acabada e "Próxima cor"
        await click('#cAll')
        s8 = await st(); lugares.append(('cor acabada', s8))
        check(s8['t'] == -1 and 'colocadas' in s8['card'] and s8['skipTxt'].startswith('Próxima cor'), f'cor acabada: o quadro avisa e o 2º botão vira "{s8["skipTxt"]}"')
        c0 = s8['color']
        await click('#cSkip')
        s9 = await st()
        check(s9['color'] not in (0, c0) and s9['t'] >= 0 and s9['refDone'] == 1, f'"Próxima cor" trocou a cor ({c0} -> {s9["color"]}) e o guia segue com partida na placa')
        await asyncio.sleep(0.6)
        await b.shot(OUT + 'guia_cor_2.png')
        # nunca contagem pela borda, em nenhum estado
        check(not any(w in s['card'] for _, s in lugares for w in edge_words), 'nenhum estado conta pela borda da placa (linha ou coluna da borda)')
        # lugares fixos
        base = lugares[0][1]
        moved = [(n, k, s[k], base[k]) for n, s in lugares for k in ('go', 'skip', 'all', 'none', 'box') if s[k] != base[k]]
        check(not moved, f'botões e quadro parados em {len(lugares)} estados' + (f': {moved[:3]}' if moved else ''))
        errs = await b.js("JSON.stringify(window.__erros)")
        check(errs == '[]', f'erros de página: {errs}')
        print('RESUMO:', 'OK' if ok else 'FALHA')
    finally:
        await b.close() if hasattr(b, 'close') else None

asyncio.run(main())
