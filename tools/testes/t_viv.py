import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?v=' + str(time.time_ns())


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    await b.goto(URL, 2.0)
    print('vivid padrão:', await b.js('vivid'), '| B4:', await b.js("PALETTE.find(p=>p.code==='B4').hex"), '| B4 foto:', await b.js("DEFAULT_PALETTE.find(d=>d[0]==='B4')[3]"))
    print('pele E1:', await b.js("PALETTE.find(p=>p.code==='E1').hex"), 'E1 foto:', await b.js("DEFAULT_PALETTE.find(d=>d[0]==='E1')[3]"))
    # abre Ajustar cores e mexe no controle
    await b.js("document.querySelector('#mColors').click()", 0.5)
    print('slider:', await b.js("JSON.stringify({v:document.getElementById('vivSlider').value,out:document.getElementById('vivVal').textContent})"))
    await b.js("applyTheme('light')", 0.2)
    await b.shot(OUT + 'viv_1_dialogo75.png')
    r = await b.js("""(async()=>{const s=document.getElementById('vivSlider');
      const get=c=>PALETTE.find(p=>p.code===c).hex;
      const res={};
      s.value=100;s.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));res.v100={vivid,B4:get('B4'),E1:get('E1'),amostra:document.querySelector('#colList .sw').style.background};
      s.value=50;s.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));res.v50={vivid,B4:get('B4'),E1:get('E1'),nota:document.getElementById('vivNote').textContent.slice(0,60),ls:localStorage.getItem('beadstudio.vivid')};
      return JSON.stringify(res)})()""")
    print('mexendo:', r)
    await b.shot(OUT + 'viv_2_dialogo50.png')
    # recarrega: tem que lembrar 50
    await b.goto(URL + 'x', 2.0)
    print('após recarregar:', await b.js("JSON.stringify({vivid,B4:PALETTE.find(p=>p.code==='B4').hex})"))
    # restaurar padrão
    r = await b.js("""(async()=>{document.querySelector('#mColors').click();await new Promise(r=>setTimeout(r,300));document.getElementById('colReset').click();await new Promise(r=>setTimeout(r,300));
      return JSON.stringify({vivid,B4:PALETTE.find(p=>p.code==='B4').hex,ls:localStorage.getItem('beadstudio.vivid'),slider:document.getElementById('vivSlider').value})})()""")
    print('restaurar:', r)
    # um molde com 100% e 75% (Umaru)
    await b.js("document.getElementById('dlgColors').close()", 0.2)
    r = await b.js("""(async()=>{const all=decodeTemplates();const t=all.find(t=>t.name.startsWith('Umaru-chan'));openTpl(t);await new Promise(r=>setTimeout(r,500));return t.name})()""")
    print('molde:', r)
    await b.js("applyTheme('light')", 0.4)
    await b.shot(OUT + 'viv_3_umaru75.png')
    await b.js("(async()=>{const s=document.getElementById('vivSlider');vivid=100;derivePalette();refreshAll()})()", 0.5)
    await b.shot(OUT + 'viv_4_umaru100.png')
    print('erros:', await b.js("window.__erros||'nenhum registrado'"))
    await b.close()

asyncio.run(main())
