import asyncio, sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
URL = 'http://localhost:8765/index.html?v=' + str(__import__('time').time_ns())


def OPEN(prefix):
    return """(async()=>{const all=decodeTemplates();const t=all.find(t=>t.name.startsWith(%s)&&t.w<=50&&t.h<=50);openTpl(t);await new Promise(r=>setTimeout(r,500));return t.name+' '+t.w+'x'+t.h})()""" % json.dumps(prefix)


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    await b.goto(URL, 2.0)
    print('B3 no app:', await b.js("PALETTE.find(p=>p.code==='B3').hex"), '| H1:', await b.js("PALETTE.find(p=>p.code==='H1').name"), '| legado B3:', await b.js("LEGACY_HEX.B3"))
    print('molde:', await b.js(OPEN('Mario (pe'), 0.6))
    await b.js("applyTheme('light')", 0.3)
    await b.shot(OUT + 'pal_1_mario_novo.png')
    # botão Voltar às cores antigas
    await b.js("document.querySelector('#mColors').click()", 0.4)
    r = await b.js("""(async()=>{const d=document.getElementById('dlgColors');const open=d.open;
      window.confirm=()=>true;
      document.getElementById('colLegacy').click();await new Promise(r=>setTimeout(r,300));
      const antiga=PALETTE.find(p=>p.code==='B3').hex, nOv=Object.keys(overrides).length;
      document.getElementById('colReset').click();await new Promise(r=>setTimeout(r,300));
      return JSON.stringify({dialogoAberto:open,aposLegado_B3:antiga,overrides:nOv,aposRestaurar_B3:PALETTE.find(p=>p.code==='B3').hex,overridesDepois:Object.keys(overrides).length})})()""")
    print('legado:', r)
    await b.shot(OUT + 'pal_2_ajustar_cores.png')
    await b.js("document.getElementById('dlgColors').close()", 0.2)
    # legado aplicado e foto do Mario antigo
    await b.js("(async()=>{document.getElementById('colLegacy')&&0;overrides={};PALETTE.forEach((p,i)=>{const o=LEGACY_HEX[p.code];if(o&&o.toUpperCase()!==DEFAULT_PALETTE[i][2].toUpperCase())overrides[p.code]=o});derivePalette();refreshAll()})()", 0.5)
    await b.shot(OUT + 'pal_3_mario_antigo.png')
    await b.js("overrides={};derivePalette();refreshAll()", 0.3)
    # menu Todas as cores no escuro
    await b.js("applyTheme('dark');document.getElementById('palMore').click()", 0.6)
    await b.shot(OUT + 'pal_4_todas_as_cores.png')
    print('erros de página:', await b.js("window.__erros||'nenhum registrado'"))
    await b.close()

asyncio.run(main())
