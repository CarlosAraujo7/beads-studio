"""Confere 'Juntar cores quase iguais' do app: (1) JS = Python (merge_similar, T=6) em 60 moldes; (2) o diálogo no Kurama (Raposa de Nove Caudas): abrir, mexer no valor, aplicar, desfazer; (3) capturas."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?v=' + str(time.time_ns())
PYM = json.load(open(OUT + 'remap_py_merge.json', encoding='utf-8'))

JS_MAP = """(async(id)=>{
  const all=decodeTemplates();const t=all.find(t=>t.id===id);if(!t)return JSON.stringify({erro:'molde não achado'});
  openTpl(t);await new Promise(r=>setTimeout(r,40));
  const plan=mergePlan(6);const out={};
  for(const k of Object.keys(plan))out[PALETTE[k-1].code]=PALETTE[plan[k]-1].code;
  return JSON.stringify(out)})"""


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    await b.goto(URL, 2.5)
    ok = 0; diffs = []
    for mid, py in PYM.items():
        js = json.loads(await b.js('%s(%s)' % (JS_MAP, json.dumps(mid))))
        if 'erro' in js: diffs.append((mid, js['erro'])); continue
        bad = {k: (py.get(k), js.get(k)) for k in set(py) | set(js) if py.get(k) != js.get(k)}
        if bad: diffs.append((mid, bad))
        else: ok += 1
    print('juntar: moldes iguais JS = Python: %d de %d' % (ok, len(PYM)))
    for mid, bad in diffs[:8]: print('  DIFERE', mid, bad)
    # diálogo no Kurama
    r = await b.js("""(async()=>{const all=decodeTemplates();const t=all.find(t=>t.id==='kurama-raposa-de-nove-caudas');openTpl(t);await new Promise(r=>setTimeout(r,400));applyTheme('light');
      document.getElementById('btnMerge').click();await new Promise(r=>setTimeout(r,400));
      const d=document.getElementById('dlgRecolor');
      return JSON.stringify({aberto:d.open,titulo:document.getElementById('recTitle').textContent,info:document.getElementById('recInfo').textContent.slice(0,170),colunas:document.getElementById('recGrid').className,antesVisivel:!document.getElementById('recBfig').hidden,botao:document.getElementById('recApply').textContent})})()""")
    print('diálogo (juntar):', r)
    await b.shot(OUT + 'merge_1_dialogo.png')
    r = await b.js("""(async()=>{const s=document.getElementById('mergeT');
      s.value=3;s.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));const info3=document.getElementById('recInfo').textContent.slice(0,90);
      s.value=12;s.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));const info12=document.getElementById('recInfo').textContent.slice(0,120);
      s.value=6;s.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));
      return JSON.stringify({valor3:info3,valor12:info12,ls:localStorage.getItem('beadstudio.mergeT')})})()""")
    print('valores:', r)
    r = await b.js("""(async()=>{const g0=S.grid.slice(),c0=usedColors;
      document.getElementById('recApply').click();await new Promise(r=>setTimeout(r,300));
      const mudou=S.grid.some((v,i)=>v!==g0[i]),geo=S.grid.every((v,i)=>(v===0)===(g0[i]===0)),cores=usedColors,toast=document.getElementById('toast').textContent;
      undo();await new Promise(r=>setTimeout(r,200));const volta=S.grid.every((v,i)=>v===g0[i]);
      return JSON.stringify({coresAntes:c0,coresDepois:cores,mudou,geometriaIgual:geo,toast,desfazVolta:volta})})()""")
    print('aplicar/desfazer:', r)
    # modo refazer ainda funciona (mostra 3 colunas)
    r = await b.js("""(async()=>{document.getElementById('btnRecolor').click();await new Promise(r=>setTimeout(r,400));
      return JSON.stringify({titulo:document.getElementById('recTitle').textContent,antesVisivel:!document.getElementById('recBfig').hidden,colunas:document.getElementById('recGrid').className,sliderVisivel:!document.getElementById('mergeRow').hidden,info:document.getElementById('recInfo').textContent.slice(0,150)})})()""")
    print('refazer depois do juntar:', r)
    await b.shot(OUT + 'merge_2_refazer.png')
    print('erros de página:', await b.js("window.__erros||'nenhum registrado'"))
    await b.close()

asyncio.run(main())
