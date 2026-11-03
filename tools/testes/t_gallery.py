"""Galeria e editor depois do visual novo: fluxos de clique, seleção, abas, 3D, cor do molde, confete e animação de entrada."""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
ok_all = []


def check(name, cond, extra=''):
    ok_all.append(bool(cond))
    print(('OK   ' if cond else 'FALHA'), name, extra)


async def main():
    b = B2(w=1280, h=800, port=9350)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=gal', 3.8)
        # --- abrir a galeria: animação de entrada liga e desliga sozinha
        await b.js("openGallery()", 0.4)
        check('galeria abre com a animação de entrada', await b.js("document.getElementById('dlgTemplates').classList.contains('gal-anim')"))
        await asyncio.sleep(1.8)
        check('animação de entrada se desliga sozinha', not await b.js("document.getElementById('dlgTemplates').classList.contains('gal-anim')"))
        # digitar na busca NÃO repete a animação
        await b.js("(()=>{const i=document.getElementById('tplSearch');i.value='naruto';i.dispatchEvent(new Event('input',{bubbles:true}))})()", 0.5)
        check('digitar na busca não repete a animação', not await b.js("document.getElementById('dlgTemplates').classList.contains('gal-anim')"))
        await b.js("(()=>{const i=document.getElementById('tplSearch');i.value='';i.dispatchEvent(new Event('input',{bubbles:true}))})()", 0.5)
        # --- blocos: cor por bloco e por miniatura
        r = json.loads(await b.js("""JSON.stringify({blocos:document.querySelectorAll('.cblock').length,
           comCor:[...document.querySelectorAll('.cblock')].filter(e=>e.style.getPropertyValue('--tint')).length,
           minis:document.querySelectorAll('.mini').length, minisCor:[...document.querySelectorAll('.mini')].filter(e=>e.style.getPropertyValue('--tint')).length,
           fundoBloco:getComputedStyle(document.querySelector('.cblock')).backgroundImage.slice(0,60)})"""))
        print('   blocos:', r)
        check('blocos e miniaturas ganham a cor do desenho', r['blocos'] > 20 and r['comCor'] >= r['blocos'] * 0.8 and r['minisCor'] >= r['minis'] * 0.7)
        # --- clicar numa miniatura abre o molde e o Voltar volta para a galeria
        mid = await b.js("document.querySelector('.mini').dataset.id")
        await b.js("document.querySelector('.mini').click()", 0.8)
        r = json.loads(await b.js("JSON.stringify({view:document.body.dataset.view,tpl:S.tpl&&S.tpl.id,back:!document.getElementById('btnBack').hidden,lbl:document.querySelector('#btnBack .lbl').textContent,mold:getComputedStyle(document.getElementById('app')).getPropertyValue('--mold')})"))
        check('miniatura abre o molde, com Voltar', r['view'] == 'edit' and r['tpl'] == mid and r['back'] and r['lbl'] == 'Voltar', str(r))
        check('o editor ganha a cor do molde (--mold)', 'hsl' in r['mold'], r['mold'])
        await b.js("document.getElementById('btnBack').click()", 0.9)
        check('Voltar reabre a galeria', await b.js("document.getElementById('dlgTemplates').open"))
        # --- lista: cartões coloridos e clique
        await b.js("tplView='list';openGallery({cat:'dragon-ball'})", 1.0)
        r = json.loads(await b.js("JSON.stringify({cards:document.querySelectorAll('.tcard').length,cor:[...document.querySelectorAll('.tcard')].filter(e=>e.style.getPropertyValue('--tint')).length,cv:document.querySelector('.tcard canvas').style.width+'x'+document.querySelector('.tcard canvas').style.height})"))
        print('   lista:', r)
        check('cartões da lista com cor e desenho nítido', r['cards'] > 5 and r['cor'] >= r['cards'] * 0.8 and 'px' in r['cv'])
        # --- seleção de vários: marcar dois cartões
        await b.js("document.getElementById('tplSelect').click()", 0.4)
        await b.js("document.querySelectorAll('.tcard .tmain')[0].click();document.querySelectorAll('.tcard .tmain')[1].click()", 0.3)
        r = json.loads(await b.js("JSON.stringify({sel:document.querySelectorAll('.tcard.sel').length,txt:document.getElementById('tbCount').textContent})"))
        check('selecionar vários marca os cartões', r['sel'] == 2 and '2' in r['txt'], str(r))
        await b.js("document.getElementById('tplSelect').click()", 0.3)
        # --- abas: 2 placas, 4 placas e Projetos 3D
        for k in ('2', '4', 'd', '1'):
            await b.js("tplView='blocks';setPlates('%s')" % k, 0.8)
            n = await b.js("document.querySelectorAll('.cblock').length+document.querySelectorAll('#tplProjects .pcard, #tplProjects .tcard, #tplProjects button').length")
            check('aba %s abre sem erro' % k, n > 0 or k == '3', str(n))
        # --- novos moldes: abas das remessas cabem na tela (nada cortado à direita)
        await b.js("document.getElementById('dlgTemplates').close();openNews()", 1.0)
        r = json.loads(await b.js("""(()=>{const t=document.getElementById('tplPlates'),s=document.getElementById('tplSort');const rt=t.getBoundingClientRect(),rs=s.getBoundingClientRect();
           return JSON.stringify({tabs:t.querySelectorAll('.ptab').length,sortDireita:Math.round(rs.right),larguraTela:innerWidth,rolagem:t.scrollWidth>t.clientWidth+1})})()"""))
        print('   novos moldes:', r)
        check('Novos moldes: a ordenação cabe na tela', r['sortDireita'] <= r['larguraTela'] and not r['rolagem'])
        r = json.loads(await b.js("JSON.stringify({side:getComputedStyle(document.getElementById('tplSide')).display,batchClass:document.getElementById('tplDlgBody').classList.contains('view-batch'),seg:getComputedStyle(document.getElementById('tplViewSeg')).visibility,secoes:document.querySelectorAll('#tplSections .tsec').length})"))
        check('Novos moldes: sem barra lateral, com seções por categoria', r['side'] == 'none' and r['batchClass'] and r['seg'] == 'hidden' and r['secoes'] > 0, str(r))
        await b.shot(OUT + 'gal_novos_depois.png')
        await b.js("document.getElementById('dlgTemplates').close();setView('home',false)", 0.5)
        # --- editor: cor do molde acompanha o desenho e some num desenho vazio
        await b.js("setGrid(12,12,new Uint8Array(144),'Teste');setView('edit')", 0.5)
        v0 = await b.js("getComputedStyle(document.getElementById('app')).getPropertyValue('--mold').trim()")
        await b.js("(()=>{const i=CODE_IDX.F5;for(let k=0;k<40;k++)S.grid[k]=i;gridChanged()})()", 0.4)
        v1 = await b.js("document.getElementById('app').style.getPropertyValue('--mold')")
        check('desenho vermelho -> --mold vermelho', 'hsl(' in v1 and (int(v1.split('(')[1].split(' ')[0]) < 20 or int(v1.split('(')[1].split(' ')[0]) > 340), '%s | vazio: %s' % (v1, v0))
        # --- confete: só quando uma ação COMPLETA a montagem
        await b.js("setMode('assemble');S.done.fill(0);recount();renderAssemble()", 0.4)
        await b.js("(()=>{for(let k=0;k<S.grid.length;k++)if(S.grid[k]&&k!==S.grid.findIndex(v=>v>0))S.done[k]=1;asmChanged()})()", 0.3)
        check('quase completo: sem confete', not await b.js("!!document.querySelector('.confetti')"))
        await b.js("(()=>{const k=S.grid.findIndex(v=>v>0);S.done[k]=1;asmChanged()})()", 0.5)
        r = json.loads(await b.js("JSON.stringify({confete:document.querySelectorAll('.confetti i').length,toast:document.getElementById('toast').textContent})"))
        check('completar a montagem faz confete e aviso', r['confete'] > 20 and 'completo' in r['toast'], str(r))
        await b.shot(OUT + 'montar_confete.png')
        await asyncio.sleep(3.0)
        check('confete some sozinho', not await b.js("!!document.querySelector('.confetti')"))
        await b.js("asmChanged()", 0.3)
        check('refazer a conta sem mudar não repete o confete', not await b.js("!!document.querySelector('.confetti')"))
        pr = [p for p in b.problems() if 'favicon' not in p]
        check('sem erros de console', not pr, json.dumps(pr, ensure_ascii=False))
    finally:
        await b.close()
    print('RESUMO:', sum(ok_all), '/', len(ok_all), 'ok')
asyncio.run(main())
