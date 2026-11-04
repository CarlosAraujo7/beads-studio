"""Estabilidade de layout: mede onde ficam os controles em vários estados e acusa o que muda de lugar.
uso: python t_stable.py [dia] [montar] [barra] [galeria]   (padrão: todos)   [--w 1280] [--h 800]"""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OPT = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
W = int(OPT.get('--w', 1280)); H = int(OPT.get('--h', 800)); MOBILE = W < 600
WANT = ARGS or ['dia', 'montar', 'barra', 'galeria', 'ferr']
PROB = []

JS_RECT = """(sels=>{const o={};for(const s of sels){const e=document.querySelector(s);if(!e){o[s]=null;continue}
  const cs=getComputedStyle(e);const r=e.getBoundingClientRect();
  o[s]=(r.width===0&&r.height===0)||cs.visibility==='hidden'||cs.display==='none'?null:[Math.round(r.x*10)/10,Math.round(r.y*10)/10,Math.round(r.width*10)/10,Math.round(r.height*10)/10]}
  return JSON.stringify(o)})"""


class Track:
    def __init__(self, name, sels, tol=0.6):
        self.name, self.sels, self.tol, self.rows = name, sels, tol, []

    async def snap(self, b, label):
        r = json.loads(await b.js(JS_RECT + '(%s)' % json.dumps(self.sels)))
        self.rows.append((label, r))

    POSONLY = ('#dayName', '#dayMeta', '#dayDots', '#tplBadge', '#projName', '#pText')      # texto de largura variável: só a posição (x, y) importa
    IGNORE = ('#dayCanvas',)                                                      # desenho centralizado: o x muda por definição

    def report(self, keys=None):
        bad = []
        for s in self.sels:
            if keys and s not in keys: continue
            if s in self.IGNORE: continue
            seen = [(l, r[s]) for l, r in self.rows if r.get(s)]
            if len(seen) < 2: continue
            base = seen[0][1]
            idx = range(2) if s in self.POSONLY else range(4)
            diffs = [(l, v) for l, v in seen if any(abs(v[i] - base[i]) > self.tol for i in idx)]
            if diffs:
                bad.append((s, base, diffs[:3], len(diffs), len(seen)))
        ok = not bad
        print(('OK    ' if ok else 'PULA  ') + self.name + ('' if ok else '  <-- algo muda de lugar'))
        for s, base, diffs, n, tot in bad:
            print('      %s: base %s | muda em %d de %d estados, p.ex. %s' % (s, base, n, tot, [(l, v) for l, v in diffs]))
        PROB.extend(bad)


async def scen_dia(b):
    await b.js("document.querySelectorAll('dialog[open]').forEach(d=>d.close());setView('home',false);document.getElementById('home').scrollTop=0", 0.6)
    # moldes de teste: nomes e categorias de tamanhos bem diferentes
    n = await b.js("""(()=>{const all=decodeTemplates().filter(t=>!t.trashed),pool=homePool(all),cfg=loadCatCfg();
       const nm=t=>(catInfo(t.cat,cfg)||{name:''}).name;
       const by=(f,k)=>pool.slice().sort((a,b)=>f(b)-f(a)).slice(0,k);
       window.__dia=[...by(t=>t.name.length,5),...by(t=>-t.name.length,3),...by(t=>nm(t).length,4),...by(t=>-nm(t).length,2),...by(t=>colorsOf(t).length,2),...by(t=>-colorsOf(t).length,2)];
       return window.__dia.length})()""")
    tr = Track('Home: cartão da sugestão (21 moldes de teste)', ['#homeDay', '#dayOpen', '#dayNext', '#dayTag', '#dayName', '#dayMeta', '#dayDots', '#dayCanvas', '#homeStats', '#homeNew', '#homeCats'])
    for i in range(n):
        await b.js("renderDay([window.__dia[%d]])" % i, 0.12)
        nm = await b.js("document.getElementById('dayName').textContent")
        await tr.snap(b, '%d:%s' % (i, nm[:28]))
    tr.report()
    # clicando em "Outro molde" de verdade (botão fica sob o mouse)
    tr2 = Track('Home: clicar 25× em "Outro molde"', ['#homeDay', '#dayOpen', '#dayNext', '#homeStats', '#homeNew'])
    await b.js("homeDaySkip=0;renderHome()", 0.3)
    for i in range(25):
        await b.js("document.getElementById('dayNext').click()", 0.1)
        await tr2.snap(b, 'clique %d' % i)
    tr2.report()


async def open_mold(b, pat='Pikachu sentado'):
    await b.js("document.querySelectorAll('dialog[open]').forEach(d=>d.close());openById(window.TEMPLATES.find(t=>/%s/.test(t.name)).id)" % pat, 0.7)


async def scen_montar(b):
    sels = ['#asmSeg', '#asmMirror', '#spanSeg', '#rPrev', '#rNext', '#rNum', '#rAll', '#rNext2', '.rownav', '.spanrow', '#btnResetProg', '#pText']
    for span in (1, 2):
        await open_mold(b)
        await b.js("setMode('assemble');setAsmSpan(%d);S.asm.row=groupStart(0);S.asm.row=nextGroup(1,-1);renderAssemble()" % span, 0.5)
        tr = Track('Montar (linha por linha, %d linha%s por vez): passar por todas as linhas' % (span, 's' if span == 2 else ''), sels)
        for i in range(70):
            await tr.snap(b, 'passo %d' % i)
            more = await b.js("(()=>{const n=document.getElementById('rNext2');if(!n||n.disabled)return false;n.click();return true})()")
            await asyncio.sleep(0.04)
            if not more: break
        # marcar/desmarcar não pode mexer em nada
        await b.js("document.getElementById('rAll').click()", 0.15); await tr.snap(b, 'depois de marcar')
        await b.js("document.getElementById('rAll').click()", 0.15); await tr.snap(b, 'depois de desmarcar')
        tr.report()
    # espelho ligado e desligado
    await open_mold(b)
    await b.js("setMode('assemble');renderAssemble()", 0.4)
    tr = Track('Montar: espelhado sim/não', sels)
    for on in (True, False, True):
        await b.js("setAsmMirror(%s)" % ('true' if on else 'false'), 0.25); await tr.snap(b, 'espelho %s' % on)
    tr.report(['#asmSeg', '#asmMirror', '#spanSeg', '#rPrev', '#rNext', '#rNum', '#rAll', '#rNext2'])
    # cor por cor
    sels2 = ['#asmSeg', '#cAll', '#cNone', '#asmMirror']
    tr = Track('Montar (cor por cor): escolher cores e marcar', sels2)
    await b.js("document.querySelector('#asmSeg button[data-view=color]').click()", 0.3)
    nc = await b.js("document.querySelectorAll('#asmBody .cfocus').length")
    for i in range(nc):
        await b.js("document.querySelectorAll('#asmBody .cfocus')[%d].click()" % i, 0.1); await tr.snap(b, 'cor %d' % i)
    await b.js("document.getElementById('cAll').click()", 0.15); await tr.snap(b, 'marcar toda a cor')
    await b.js("document.getElementById('cNone').click()", 0.15); await tr.snap(b, 'desmarcar')
    tr.report()


async def scen_barra(b):
    sels = ['.topbar', '#btnBack', '#btnHome', '#projName', '#tplBadge', '#modeSwitch', '#btnUndo', '#btnRedo', '#btnSaveTpl', '#btnFile', '.themebox .themebtn']
    tr = Track('Barra do editor: voltar de vários lugares, molde aberto, alterado, desenho novo', sels)
    mid = "window.TEMPLATES.find(t=>/Pikachu sentado/.test(t.name)).id"
    close = "document.querySelectorAll('dialog[open]').forEach(d=>d.close());"
    # 1) da tela inicial
    await b.js(close + "setView('home',false);openById(%s)" % mid, 0.6); await tr.snap(b, 'aberto da tela inicial')
    # 2) da galeria
    await b.js(close + "setView('home',false);openGallery()", 0.9)
    await b.js("openTpl(decodeTemplates().find(t=>t.id===%s))" % mid, 0.6); await tr.snap(b, 'aberto da galeria')
    # 3) de "Novos moldes"
    await b.js(close + "setView('home',false);openNews()", 0.9)
    await b.js("openTpl(decodeTemplates().find(t=>t.id===%s))" % mid, 0.6); await tr.snap(b, 'aberto de Novos moldes')
    # 4) alterado
    await b.js("S.grid[S.grid.findIndex(v=>v>0)]=0;gridChanged()", 0.3); await tr.snap(b, 'depois de pintar (alterado)')
    # 5) desenho novo (sem molde e sem Voltar)
    await b.js(close + "setView('home',false);setGrid(20,20,new Uint8Array(400),'Meu projeto');navBack=null;syncBack();setView('edit')", 0.6); await tr.snap(b, 'desenho novo')
    # 6) modo montar e volta
    await b.js("setMode('assemble')", 0.4); await tr.snap(b, 'desenho novo, Montar')
    await b.js("setMode('create')", 0.3)
    tr.report()


async def scen_galeria(b):
    sels = ['.gal-head', '.gal-head .btn[data-close]', '#tplSearch', '#tplViewSeg', '#manageBtn', '#tplHelp', '#tplPlates', '#tplPlates .ptab:nth-child(1)', '#tplPlates .ptab:nth-child(2)', '#tplSort']
    close = "document.querySelectorAll('dialog[open]').forEach(d=>d.close());setView('home',false);"
    tr = Track('Galeria: cabeçalho e abas em vários estados', sels)
    await b.js(close + "tplView='blocks';openGallery()", 1.0); await tr.snap(b, 'blocos')
    await b.js("tplView='list';renderTemplates()", 0.5); await tr.snap(b, 'lista')
    await b.js("tplView='blocks';renderTemplates()", 0.4)
    await b.js("setPlates('d')", 0.6); await tr.snap(b, 'projetos 3D')
    await b.js("setPlates('1')", 0.5)
    for q in ('naruto', 'pikachu', 'zzzz', ''):
        await b.js("(()=>{const i=document.getElementById('tplSearch');i.value=%s;i.dispatchEvent(new Event('input',{bubbles:true}))})()" % json.dumps(q), 0.6)
        await tr.snap(b, 'busca "%s"' % q)
    await b.js("document.getElementById('dlgTemplates').close();openNews()", 1.0); await tr.snap(b, 'novos moldes')
    tr.report(['.gal-head', '.gal-head .btn[data-close]', '#tplSearch', '#manageBtn', '#tplHelp', '#tplViewSeg'])
    tr.report(['#tplPlates .ptab:nth-child(1)', '#tplSort'])


async def scen_ferr(b):
    sels = ['#btnSel', '#zOut', '#zIn', '#zFit', '#btnView', '#btnPanel', '#tools', '.tool[data-tool=pencil]', '.tool[data-tool=move]', '.curcolor', '#palMore', '#tabsCreate button:nth-child(1)', '#tabsCreate button:nth-child(2)', '.kpis', '#modeSwitch', '#btnSaveTpl']
    await open_mold(b)
    await b.js("setMode('create')", 0.4)
    tr = Track('Editor (Criar): trocar de ferramenta, de cor, de aba e ligar a seleção', sels)
    for tool in ('pencil', 'eraser', 'fill', 'picker', 'line', 'rect', 'ellipse', 'select', 'move', 'pencil'):
        await b.js("setTool('%s')" % tool, 0.15); await tr.snap(b, 'ferramenta ' + tool)
    for i in (1, 5, 20, 60, 100):
        await b.js("selectColor(%d)" % i, 0.15); await tr.snap(b, 'cor %d' % i)
    await b.js("document.getElementById('btnSel').click()", 0.2); await tr.snap(b, 'seleção ligada')
    await b.js("document.getElementById('btnSel').click()", 0.2)
    for t in ('project', 'counts'):
        await b.js("(()=>{const bt=[...document.querySelectorAll('#tabsCreate button')].find(x=>x.dataset.tab==='%s');if(bt)bt.click()})()" % t, 0.2); await tr.snap(b, 'aba ' + t)
    tr.report(['#btnSel', '#zOut', '#zIn', '#zFit', '#btnView', '#btnPanel', '#tools', '.tool[data-tool=pencil]', '.tool[data-tool=move]', '.curcolor', '#palMore', '#modeSwitch', '#btnSaveTpl', '#tabsCreate button:nth-child(1)', '#tabsCreate button:nth-child(2)'])


async def main():
    b = B2(w=W, h=H, port=9345)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.viewport(W, H, 1, MOBILE)
        await b.goto('http://localhost:8765/index.html?x=stable', 3.8)
        for name in WANT:
            await {'dia': scen_dia, 'montar': scen_montar, 'barra': scen_barra, 'galeria': scen_galeria, 'ferr': scen_ferr}[name](b)
        pr = [p for p in b.problems() if 'favicon' not in p]
        print('erros de página:', pr if pr else 'nenhum')
        print('RESUMO: %d elemento(s) mudam de lugar' % len(PROB))
    finally:
        await b.close()
asyncio.run(main())
