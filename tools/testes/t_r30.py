"""Remessa 30 no site (rode depois do add_templates): catálogo, tela Novos moldes na remessa 30, um molde novo aberto no editor com a categoria certa,
as 11 categorias novas com ícone e sem erros de página.
Rodar: python -m http.server 8765 na raiz do projeto e  python -u tools/testes/t_r30.py"""
import asyncio, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=r30a'
NOVAS = ['kuroko-no-basket', 'eyeshield-21', 'beelzebub', 'wistoria', 'shokugeki-no-soma', 'ao-no-exorcist', 'zero-no-tsukaima',
         'miss-kobayashis-dragon-maid', 'shangri-la-frontier', 'record-of-ragnarok', 'fate-grand-order']


async def main():
    b = Browser(w=1280, h=900)
    await b.start()
    ok = True
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)));addEventListener('unhandledrejection',e=>window.__erros.push('rej:'+String(e.reason)));window.confirm=()=>true")
        print('catálogo:', await b.js("TEMPLATES.length"), '| remessas:', await b.js("JSON.stringify((window.REMESSAS||[]).slice(0,2).map(r=>({n:r.n,ids:r.ids.length})))"))
        await b.js("applyTheme('light')")
        r = json.loads(await b.js("""(async()=>{openNews&&openNews();await new Promise(r=>setTimeout(r,900));return JSON.stringify({batch:tplBatch,cartoes:document.querySelectorAll('#dlgTemplates .tcard').length})})()"""))
        print('novos moldes:', r); ok = ok and r['batch'] == 30 and r['cartoes'] > 0
        await b.shot(OUT + 'r30_news.png')
        r = json.loads(await b.js("""(async()=>{const t=decodeTemplates().find(t=>t.name==='Tetsuya Kuroko (Kuroko no Basket, chibi, bola)');if(!t)return JSON.stringify({erro:'molde não achado'});openTpl(t);await new Promise(r=>setTimeout(r,700));return JSON.stringify({nome:t.name,cat:t.cat,grupo:t.group,view:document.body.dataset.view,S:[S.w,S.h]})})()"""))
        print('abrir molde novo:', r); ok = ok and r.get('cat') == 'kuroko-no-basket' and r.get('view') == 'edit'
        await b.shot(OUT + 'r30_open.png')
        r = json.loads(await b.js("""(()=>{const cats=catList(loadCatCfg());const by=new Map(cats.map(c=>[c.id,c]));return JSON.stringify(%s.map(id=>{const c=by.get(id);const n=decodeTemplates().filter(t=>!t.trashed&&t.cat===id).length;return {id,existe:!!c,nome:c&&c.name,n,icone:typeof CAT_MINI_PICK!=='undefined'&&!!CAT_MINI_PICK[id]&&decodeTemplates().some(t=>t.cat===id&&(t.origName||t.name)===CAT_MINI_PICK[id][0])}}))})()""" % json.dumps(NOVAS)))
        for c in r: print('  categoria', c)
        ok = ok and all(c['existe'] and c['n'] > 0 and c['icone'] for c in r)
        await b.js("(async()=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());setView('home',false);openGallery({cat:'eyeshield-21'})})()", 1.2)
        n = await b.js("document.querySelectorAll('#dlgTemplates .tcard, #dlgTemplates .cblock .mini, #dlgTemplates .cblock canvas').length")
        print('galeria Eyeshield 21: elementos', n); ok = ok and n > 0
        await b.shot(OUT + 'r30_eyeshield.png')
        er = await b.js("JSON.stringify(window.__erros)")
        print('erros de página:', er); ok = ok and er == '[]'
        print('RESUMO:', 'OK' if ok else 'FALHA')
    finally:
        await b.close() if hasattr(b, 'close') else None
asyncio.run(main())
