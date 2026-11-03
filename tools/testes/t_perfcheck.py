"""Depois das otimizações: o visual e o comportamento continuam certos? (ícones em canvas, desenho preguiçoso, content-visibility, Voltar, seleção, arrastar)"""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
ok_all = []


def check(name, cond, extra=''):
    ok_all.append(bool(cond))
    print(('OK   ' if cond else 'FALHA'), name, extra)


# um canvas "foi desenhado" se tem algum pixel com alfa
JS_DRAWN = "(c=>{try{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;for(let i=3;i<d.length;i+=4)if(d[i])return true}catch(e){}return false})"


async def visible_stats(b, sel, root='#tplMain'):
    """quantos elementos `sel` estão na área visível (±) e quantos deles têm o canvas desenhado"""
    return json.loads(await b.js("""(()=>{const drawn=%s;const m=document.querySelector('%s').getBoundingClientRect();
      const els=[...document.querySelectorAll('%s')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.bottom>m.top&&r.top<m.bottom});
      const blank=els.filter(e=>{const c=e.querySelector('canvas');return !c||!drawn(c)});
      return JSON.stringify({visiveis:els.length,emBranco:blank.length,exemplo:blank.slice(0,3).map(e=>e.dataset.id||e.className)})})()""" % (JS_DRAWN, root, sel)))


async def main():
    b = B2(w=1280, h=800, port=9400)
    await b.start()
    try:
        await b.send('Log.enable')
        await b.goto('http://localhost:8765/index.html?x=pc%d' % (int(time.time()) % 100000), 3.5)
        # ---- tela inicial: ícones em canvas e vitrine
        r = json.loads(await b.js("""JSON.stringify({imgs:document.querySelectorAll('img.cmini').length,cvs:document.querySelectorAll('canvas.cmini').length,
           pintados:[...document.querySelectorAll('canvas.cmini')].filter(c=>c._p&&(%s)(c)).length,
           vitrine:document.querySelectorAll('#homeTrack .hm canvas').length,vitrineDesenhada:[...document.querySelectorAll('#homeTrack .hm canvas')].filter(c=>(%s)(c)).length})""" % (JS_DRAWN, JS_DRAWN)))
        print('   início:', r)
        check('início: ícones de categoria em canvas e todos pintados', r['imgs'] == 0 and r['cvs'] > 15 and r['pintados'] == r['cvs'])
        check('início: vitrine inteira desenhada (as duas voltas)', r['vitrine'] == 44 and r['vitrineDesenhada'] == 44)
        await b.shot(OUT + 'perf_inicio.png')
        # ---- galeria em blocos: desenho preguiçoso
        await b.js("tplView='blocks';openGallery()", 1.5)
        tot = json.loads(await b.js("JSON.stringify({minis:document.querySelectorAll('.mini').length,desenhadas:[...document.querySelectorAll('.mini canvas')].filter(c=>(%s)(c)).length,iconesBloco:[...document.querySelectorAll('.cblock canvas.cmini')].filter(c=>c._p).length,blocos:document.querySelectorAll('.cblock').length})" % JS_DRAWN))
        print('   blocos ao abrir:', tot)
        check('blocos: só uma parte das miniaturas é desenhada ao abrir (preguiçoso)', 0 < tot['desenhadas'] < tot['minis'] * 0.5, str(tot))
        check('blocos: todos os ícones de categoria pintados', tot['iconesBloco'] >= tot['blocos'] * 0.9, str(tot))
        v = await visible_stats(b, '.cblock .mini')
        check('blocos: tudo que está visível está desenhado', v['visiveis'] > 20 and v['emBranco'] == 0, str(v))
        await b.shot(OUT + 'perf_blocos.png')
        # rolar por toda a galeria: nenhuma miniatura visível pode ficar em branco
        h = await b.js("document.getElementById('tplMain').scrollHeight")
        piores = 0; passos = 0
        for y in range(0, int(h), 500):
            await b.js("document.getElementById('tplMain').scrollTop=%d" % y, 0.18)
            v = await visible_stats(b, '.cblock .mini'); passos += 1; piores = max(piores, v['emBranco'])
        check('blocos: rolando até o fim nada visível fica em branco', piores == 0, 'passos %d, pior %d' % (passos, piores))
        tot = json.loads(await b.js("JSON.stringify({minis:document.querySelectorAll('.mini').length,desenhadas:[...document.querySelectorAll('.mini canvas')].filter(c=>(%s)(c)).length})" % JS_DRAWN))
        check('blocos: depois de rolar tudo, todas desenhadas', tot['desenhadas'] >= tot['minis'] - 5, str(tot))
        # ---- voltar restaura a rolagem (blocos)
        await b.js("document.getElementById('tplMain').scrollTop=2200", 0.4)
        sy = await b.js("document.getElementById('tplMain').scrollTop")
        mid = await b.js("""(()=>{const m=document.getElementById('tplMain').getBoundingClientRect();const e=[...document.querySelectorAll('.cblock .mini')].find(x=>{const r=x.getBoundingClientRect();return r.top>m.top+120&&r.bottom<m.bottom-60});e.click();return e.dataset.id})()""")
        await asyncio.sleep(0.8)
        check('blocos: clicar numa miniatura abre o molde (delegação)', await b.js("document.body.dataset.view") == 'edit' and await b.js("S.tpl&&S.tpl.id") == mid)
        await b.js("document.getElementById('btnBack').click()", 1.2)
        sy2 = await b.js("document.getElementById('tplMain').scrollTop")
        fl = await b.js("!!document.querySelector('.mini.flash')")
        check('blocos: o Voltar devolve a mesma rolagem e destaca o molde', abs(sy2 - sy) <= 2 and fl, 'antes %s depois %s flash %s' % (sy, sy2, fl))
        # ---- seleção de vários e arrastar (delegação)
        await b.js("document.getElementById('tplSelect').click()", 0.4)
        await b.js("document.getElementById('tplMain').scrollTop=0", 0.3)
        await b.js("document.querySelectorAll('.cblock .mini')[0].click();document.querySelectorAll('.cblock .mini')[1].click()", 0.3)
        r = json.loads(await b.js("JSON.stringify({sel:document.querySelectorAll('.mini.sel').length,txt:document.getElementById('tbCount').textContent})"))
        check('blocos: selecionar vários marca as miniaturas', r['sel'] == 2 and '2' in r['txt'], str(r))
        await b.js("document.getElementById('tplSelect').click()", 0.3)
        r = json.loads(await b.js("""(()=>{const mini=document.querySelector('.cblock .mini');const id=mini.dataset.id;const from=mini.closest('.cblock').dataset.cat;
          const blocks=[...document.querySelectorAll('.cblock')];const dest=blocks.find(x=>x.dataset.cat!==from&&x.dataset.cat!=='other');
          const dt=new DataTransfer();mini.dispatchEvent(new DragEvent('dragstart',{bubbles:true,cancelable:true,dataTransfer:dt}));
          dest.dispatchEvent(new DragEvent('dragover',{bubbles:true,cancelable:true,dataTransfer:dt}));
          dest.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));
          const t=decodeTemplates().find(x=>x.id===id);return JSON.stringify({id,from,to:dest.dataset.cat,agora:t&&t.cat})})()"""))
        check('blocos: arrastar uma miniatura para outro bloco muda a categoria', r['agora'] == r['to'] and r['from'] != r['to'], str(r))
        # ---- lista: todas as categorias, com content-visibility
        await b.js("tplView='list';openGallery({cat:'dragon-ball'})", 1.0)
        await b.js("document.querySelector('#tplSide .cat-btn[data-cat=all]').click()", 1.0)
        r = json.loads(await b.js("JSON.stringify({cv:document.getElementById('dlgTemplates').classList.contains('cv'),cartoes:document.querySelectorAll('.tcard').length,secoes:document.querySelectorAll('.tsec').length,icones:[...document.querySelectorAll('#tplSide canvas.cmini')].filter(c=>c._p).length,iconesSecao:[...document.querySelectorAll('.tsec h3 canvas.cmini')].filter(c=>c._p).length})"))
        print('   lista Todos:', r)
        check('lista Todos: usa content-visibility e tem ~1000 cartões', r['cv'] and r['cartoes'] > 900 and r['secoes'] > 100)
        check('lista Todos: ícones da lateral e das seções pintados', r['icones'] > 100 and r['iconesSecao'] > 100)
        v = await visible_stats(b, '.tcard')
        check('lista Todos: cartões visíveis desenhados', v['visiveis'] > 5 and v['emBranco'] == 0, str(v))
        await b.shot(OUT + 'perf_lista_todos.png')
        h = await b.js("document.getElementById('tplMain').scrollHeight")
        piores = 0; passos = 0
        for y in range(0, int(h), 700):
            await b.js("document.getElementById('tplMain').scrollTop=%d" % y, 0.2)
            v = await visible_stats(b, '.tcard'); passos += 1; piores = max(piores, v['emBranco'])
        check('lista Todos: rolando até o fim nada visível fica em branco', piores == 0, 'passos %d, pior %d' % (passos, piores))
        # ---- voltar na lista Todos (montada inteira): mesma rolagem
        await b.js("document.getElementById('tplMain').scrollTop=6000", 0.5)
        sy = await b.js("document.getElementById('tplMain').scrollTop")
        mid = await b.js("""(()=>{const m=document.getElementById('tplMain').getBoundingClientRect();const e=[...document.querySelectorAll('.tcard')].find(x=>{const r=x.getBoundingClientRect();return r.top>m.top+160&&r.bottom<m.bottom-40});e.querySelector('.tmain').click();return e.dataset.id})()""")
        await asyncio.sleep(0.8)
        await b.js("document.getElementById('btnBack').click()", 1.5)
        sy2 = await b.js("document.getElementById('tplMain').scrollTop")
        fl = await b.js("!!document.querySelector('.tcard.flash')")
        cv = await b.js("document.getElementById('dlgTemplates').classList.contains('cv')")
        check('lista Todos: o Voltar devolve a mesma rolagem e destaca o cartão', abs(sy2 - sy) <= 2 and fl and not cv, 'antes %s depois %s flash %s cv %s' % (sy, sy2, fl, cv))
        # ---- busca com atraso
        await b.js("(()=>{const i=document.getElementById('tplSearch');i.value='pikachu';i.dispatchEvent(new Event('input',{bubbles:true}))})()", 0.05)
        antes = await b.js("document.querySelectorAll('.tcard').length")
        await asyncio.sleep(0.5)
        depois = await b.js("document.querySelectorAll('.tcard').length")
        check('busca: a lista só muda depois do atraso e filtra', antes > 900 and 0 < depois < 40, '%s -> %s' % (antes, depois))
        await b.js("(()=>{const i=document.getElementById('tplSearch');i.value='';i.dispatchEvent(new Event('input',{bubbles:true}))})()", 0.6)
        # ---- Organizar categorias: ícones
        await b.js("openCats()", 0.8)
        r = json.loads(await b.js("JSON.stringify({linhas:document.querySelectorAll('#catRows .cr').length,icones:[...document.querySelectorAll('#catRows canvas.cmini')].filter(c=>c._p&&(%s)(c)).length})" % JS_DRAWN))
        check('Organizar categorias: ícones pintados', r['linhas'] > 100 and r['icones'] > 100, str(r))
        await b.shot(OUT + 'perf_organizar.png')
        await b.js("document.getElementById('dlgCats').close();document.getElementById('dlgTemplates').close()", 0.4)
        # ---- novos moldes
        await b.js("openNews()", 1.0)
        v = await visible_stats(b, '.tcard')
        check('Novos moldes: cartões visíveis desenhados', v['visiveis'] > 5 and v['emBranco'] == 0, str(v))
        pr = [p for p in b.problems() if 'favicon' not in p]
        check('sem erros de console', not pr, json.dumps(pr, ensure_ascii=False))
    finally:
        await b.close()
    print('RESUMO:', sum(ok_all), '/', len(ok_all), 'ok')
asyncio.run(main())
