"""Tela inicial nova: fluxos (busca, "/", atalhos, vitrine, molde do dia, Voltar), movimento reduzido e hover."""
import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
ok_all = []


def check(name, cond, extra=''):
    ok_all.append(bool(cond))
    print(('OK   ' if cond else 'FALHA'), name, extra)


async def main():
    b = B2(w=1280, h=900, port=9334)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=fluxos', 3.5)
        # 1) tecla "/" leva o cursor para a busca
        await b.js("window.dispatchEvent(new KeyboardEvent('keydown',{key:'/',bubbles:true,cancelable:true}))", 0.3)
        check('"/" foca a busca', await b.js("document.activeElement.id==='homeSearch'"))
        # 2) digitar na busca mostra os resultados e esconde atalhos e vitrine
        await b.js("(()=>{const i=document.getElementById('homeSearch');i.value='naruto';i.dispatchEvent(new Event('input',{bubbles:true}))})()", 0.5)
        r = json.loads(await b.js("""JSON.stringify({
          searching: document.querySelector('.home-main').classList.contains('searching'),
          foundVisible: !document.getElementById('homeFound').hidden, mainHidden: document.getElementById('homeMain').hidden,
          chipsDisp: getComputedStyle(document.getElementById('homeChips')).display, marqDisp: getComputedStyle(document.getElementById('homeMarq')).display,
          tiles: document.querySelectorAll('#homeFoundGrid .tile').length, title: document.getElementById('homeFoundTitle').textContent,
          stageH: Math.round(document.getElementById('homeStage').getBoundingClientRect().height)})"""))
        print('   busca:', r)
        check('busca ativa o estado searching', r['searching'] and r['foundVisible'] and r['mainHidden'])
        check('atalhos e vitrine somem na busca', r['chipsDisp'] == 'none' and r['marqDisp'] == 'none')
        check('há resultados', r['tiles'] > 0)
        await b.shot(OUT + 'home_busca.png')
        # limpar a busca volta ao normal
        await b.js("(()=>{const i=document.getElementById('homeSearch');i.value='';i.dispatchEvent(new Event('input',{bubbles:true}))})()", 0.5)
        r = json.loads(await b.js("""JSON.stringify({searching: document.querySelector('.home-main').classList.contains('searching'), mainHidden: document.getElementById('homeMain').hidden, marqDisp: getComputedStyle(document.getElementById('homeMarq')).display})"""))
        check('limpar a busca volta ao normal', (not r['searching']) and (not r['mainHidden']) and r['marqDisp'] != 'none', str(r))
        # 3) atalho de categoria abre a galeria naquela categoria
        cat = await b.js("document.querySelector('#homeChips .hchip[data-c]').dataset.c")
        await b.js("document.querySelector('#homeChips .hchip[data-c]').click()", 0.8)
        check('chip de categoria abre a galeria', await b.js("document.getElementById('dlgTemplates').open") and await b.js("tplCat") == cat, cat)
        await b.js("document.getElementById('dlgTemplates').close()", 0.6)
        check('fechar a galeria mantém a tela inicial', await b.js("document.body.dataset.view") == 'home')
        # 4) "Novos moldes" (chip) abre a tela de remessas
        await b.js("document.querySelector('#homeChips .hchip[data-act=news]').click()", 0.8)
        check('chip Novos moldes abre as remessas', await b.js("document.getElementById('dlgTemplates').open && tplBatch!=null"))
        await b.js("document.getElementById('dlgTemplates').close()", 0.6)
        # 5) Surpreenda-me abre um molde no editor, com o botão Voltar
        await b.js("document.querySelector('#homeChips .hchip[data-act=rand]').click()", 0.8)
        r = json.loads(await b.js("JSON.stringify({view:document.body.dataset.view, tpl:S.tpl&&S.tpl.id, back:!document.getElementById('btnBack').hidden, lbl:document.querySelector('#btnBack .lbl').textContent})"))
        check('Surpreenda-me abre um molde', r['view'] == 'edit' and r['tpl'] and r['back'], str(r))
        await b.js("document.getElementById('btnBack').click()", 0.8)
        check('Voltar devolve a tela inicial', await b.js("document.body.dataset.view") == 'home')
        # 6) bolha da vitrine abre o molde
        await b.js("document.querySelector('#homeTrack .hm').click()", 0.8)
        check('bolha da vitrine abre um molde', await b.js("document.body.dataset.view") == 'edit' and await b.js("!!S.tpl"))
        await b.js("goHome()", 0.8)
        # 7) molde do dia: abrir e trocar
        name0 = await b.js("document.getElementById('dayName').textContent")
        await b.js("document.getElementById('dayOpen').click()", 0.8)
        check('Abrir este molde abre o molde do dia', await b.js("document.body.dataset.view") == 'edit' and await b.js("S.name") == name0, name0)
        await b.js("goHome()", 0.8)
        await b.js("document.getElementById('dayNext').click()", 0.8)
        name1 = await b.js("document.getElementById('dayName').textContent")
        tag1 = await b.js("document.getElementById('dayTag').textContent")
        check('Outro molde troca a sugestão', name1 != name0 and 'sugest' in tag1.lower(), '%s | %s' % (name1, tag1))
        # 8) hover levanta o atalho
        box = json.loads(await b.js("(()=>{const r=document.getElementById('hNew').getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()"))
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=box['x'], y=box['y'])
        await asyncio.sleep(0.5)
        tr = await b.js("getComputedStyle(document.getElementById('hNew')).transform")
        check('hover levanta o atalho', tr != 'none' and 'matrix' in tr, tr)
        # 9) tela de edição -> início: a vitrine NÃO é reconstruída (sem piscar) e os números continuam
        n1 = await b.js("document.querySelectorAll('#homeTrack .hm').length")
        await b.js("document.getElementById('hTpls').click()", 0.6)
        await b.js("document.getElementById('dlgTemplates').close()", 0.6)
        n2 = await b.js("document.querySelectorAll('#homeTrack .hm').length")
        check('vitrine continua a mesma depois de abrir/fechar a galeria', n1 == n2 == 44, '%s %s' % (n1, n2))
        # 10) contagens
        st = await b.js("JSON.stringify([...document.querySelectorAll('#homeStats b')].map(x=>x.textContent))")
        print('   números:', st)
        # 11) tema/acento: troca de cor de destaque atualiza os degradês
        for acc in ('coral', 'verde', 'rosa'):
            await b.js("applyAccent('%s')" % acc, 0.4)
            a = await b.js("getComputedStyle(document.querySelector('.hact.g-violet')).backgroundImage.slice(0,90)")
            print('   acento', acc, '->', a)
        await b.js("applyAccent('coral')", 0.5)
        await b.shot(OUT + 'home_acento_coral.png', clip=(0, 0, 1280, 900))
        await b.js("applyAccent('violeta')", 0.3)
        pr = [p for p in b.problems() if 'favicon' not in p]
        check('sem erros de console', not pr, json.dumps(pr, ensure_ascii=False))
    finally:
        await b.close()

    # movimento reduzido
    b = B2(w=1280, h=900, port=9335)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.send('Emulation.setEmulatedMedia', features=[{'name': 'prefers-reduced-motion', 'value': 'reduce'}])
        await b.goto('http://localhost:8765/index.html?x=calmo', 3.0)
        r = json.loads(await b.js("""JSON.stringify({
          track: getComputedStyle(document.getElementById('homeTrack')).animationName,
          stage: getComputedStyle(document.getElementById('homeStage')).animationName,
          marqOverflow: getComputedStyle(document.getElementById('homeMarq')).overflowX,
          ph: document.getElementById('homeSearch').placeholder,
          stats: [...document.querySelectorAll('#homeStats b')].map(x=>x.textContent)})"""))
        print('   movimento reduzido:', r)
        check('movimento reduzido: sem animações', r['track'] == 'none' and r['stage'] == 'none' and r['marqOverflow'] == 'auto')
        check('movimento reduzido: números direto no valor', r['stats'][0] == '1.123' or r['stats'][0].replace('.', '').isdigit() and int(r['stats'][0].replace('.', '')) > 100)
        await b.shot(OUT + 'home_movimento_reduzido.png', clip=(0, 0, 1280, 900))
        pr = [p for p in b.problems() if 'favicon' not in p]
        check('sem erros de console (movimento reduzido)', not pr, json.dumps(pr, ensure_ascii=False))
    finally:
        await b.close()
    print('RESUMO:', sum(ok_all), '/', len(ok_all), 'ok')
asyncio.run(main())
