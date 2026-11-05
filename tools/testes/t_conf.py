import asyncio, sys, json, base64
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?x=conf9'


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    try:
        await b.goto(URL, 2.5)
        await b.js("window.__erros=[];addEventListener('error',e=>window.__erros.push(String(e.message)))")
        # molde com duplas parecidas onde alguma linha tem as duas cores (para ver o aviso da Montar)
        r = await b.js("""(()=>{const all=decodeTemplates().filter(t=>t.w<=50&&t.h<=50&&!/grande/.test(t.name));let best=null;
          for(const t of all){const g=rowsToGrid(t.rows).g;const w=t.w,h=t.h;const cnt={};g.forEach(v=>{if(v)cnt[v]=(cnt[v]||0)+1});
            const used=Object.keys(cnt).map(Number);const pr=confPairsRaw(used);if(!pr.length)continue;
            let rowsBoth=0;for(let y=0;y<h;y++){const s=new Set();for(let x=0;x<w;x++){const v=g[y*w+x];if(v)s.add(v)}if(pr.some(p=>s.has(p.a)&&s.has(p.b)))rowsBoth++}
            const score=rowsBoth*10+pr.length;if(!best||score>best.score)best={score,name:t.name,id:t.id,pairs:pr.length,rowsBoth}}
          return JSON.stringify(best)})()""".replace('confPairsRaw', 'confPairs'))
        print('molde escolhido:', r)
        info = json.loads(r)
        print(await b.js("""(async()=>{const t=decodeTemplates().find(t=>t.id===%s);openTpl(t);await new Promise(r=>setTimeout(r,500));return t.name+' '+t.w+'x'+t.h+' cores:'+usedColors})()""" % json.dumps(info['id'])))
        await b.js("applyTheme('light')")
        # Criar: selos ≈ na lista
        r = await b.js("""(()=>{const rows=[...document.querySelectorAll('#countList .crow')];const com=rows.filter(r=>r.querySelector('.conf'));
          return JSON.stringify({linhas:rows.length,comSelo:com.length,exemplo:com.slice(0,3).map(r=>r.innerText.replace(/\\s+/g,' ')+' | '+r.querySelector('.conf').title)})})()""")
        print('criar (lista):', r)
        await b.shot(OUT + 'conf_criar_lista.png')
        # Montar: acha uma linha com as duas cores
        r = await b.js("""(async()=>{setMode('assemble');await new Promise(r=>setTimeout(r,400));
          const used=[];for(let v=1;v<=NCOL;v++)if(counts[v])used.push(v);const pr=confPairs(used);let alvo=-1;
          for(let y=0;y<S.h&&alvo<0;y++){const s=new Set();for(let x=0;x<S.w;x++){const v=S.grid[y*S.w+x];if(v)s.add(v)}if(pr.some(p=>s.has(p.a)&&s.has(p.b)))alvo=y}
          S.asm.row=groupStart(alvo);renderAssemble();requestDraw();await new Promise(r=>setTimeout(r,500));
          const box=document.querySelector('.confbox');
          return JSON.stringify({linhaAlvo:alvo+1,aviso:box?box.innerText.replace(/\\s+/g,' '):null,selosNaLista:document.querySelectorAll('#runs .conf').length,chips:document.querySelectorAll('.take .conf').length})})()""")
        print('montar (aviso):', r)
        await b.shot(OUT + 'conf_montar_aviso.png')
        # códigos nas contas da linha atual
        r = await b.js("""(()=>{const y=S.asm.row,cs=S.zoom,x0=RULER;
          return JSON.stringify({zoom:cs,codigosNaLinha:cs>=14})})()""")
        print('zoom:', r)
        # Cor por cor: escolhe uma cor que tem parecida
        r = await b.js("""(async()=>{S.asm.view='color';renderAssemble();
          const used=[];for(let v=1;v<=NCOL;v++)if(counts[v])used.push(v);const alvo=used.find(v=>confOf(v).length);S.asm.color=alvo;renderAssemble();requestDraw();await new Promise(r=>setTimeout(r,400));
          return JSON.stringify({cor:PALETTE[alvo-1].code,parecidas:confOf(alvo).map(q=>PALETTE[q.v-1].code),selosNaLista:document.querySelectorAll('.cfocus .conf').length,seloNoQuadro:document.querySelectorAll('.cguide .conf').length})})()""")
        print('cor por cor:', r)
        await b.shot(OUT + 'conf_cor_por_cor.png')
        # guia PNG
        d = await b.js("""(()=>{return renderOffscreen(26,{guide:true}).toDataURL('image/png')})()""")
        open(OUT + 'conf_guia.png', 'wb').write(base64.b64decode(d.split(',')[1]))
        # tema escuro
        await b.js("S.asm.view='row';renderAssemble();applyTheme('dark')", 0.5)
        await b.shot(OUT + 'conf_montar_aviso_escuro.png')
        # diferenças em palavras: alguns pares conhecidos
        r = await b.js("""(()=>{const o={};for(const [a,c] of [['A1','G1'],['G1','E14'],['A6','A8'],['B2','B4'],['E6','F9'],['A4','A5']]){const i=CODE_IDX[a],j=CODE_IDX[c];o[a+' x '+c]=[+de00(PALETTE[i-1].lab,PALETTE[j-1].lab).toFixed(1),a+' é '+diffWords(i,j)+' que '+c]}return JSON.stringify(o)})()""")
        print('diferenças:', r)
        print('erros de página:', await b.js("JSON.stringify(window.__erros)"))
    finally:
        await b.close()

asyncio.run(main())
