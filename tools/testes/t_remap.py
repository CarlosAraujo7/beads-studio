"""Confere o botão 'Refazer as cores deste molde' do app: (1) a troca do JS = a do Python (tools/out/remap_py_maps.json) em 60 moldes; (2) abrir o diálogo, aplicar, desfazer; (3) capturas.
ATENÇÃO: o item (1) está DESATUALIZADO (as linhas "DIFERE"): o mapa de referência é de antes de 2026-11-03, quando os moldes foram recoloridos pela imagem (CLAUDE.md §7.44), então o plano
do JS sobre as letras de hoje não tem por que bater com ele. Só (2) e (3) continuam valendo (diálogo abre, aplica, Ctrl+Z desfaz, celular cabe)."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')) + os.sep
OUT = ROOT + 'tools/out/'
URL = 'http://localhost:8765/index.html?v=' + str(time.time_ns())
PY = json.load(open(OUT + 'remap_py_maps.json', encoding='utf-8'))

JS_MAP = """(async(id)=>{
  const all=decodeTemplates();const t=all.find(t=>t.id===id);if(!t)return JSON.stringify({erro:'molde não achado'});
  openTpl(t);await new Promise(r=>setTimeout(r,60));
  const plan=recolorPlan();const out={};
  for(const k of Object.keys(plan))out[PALETTE[k-1].code]=PALETTE[plan[k]-1].code;
  return JSON.stringify(out)})"""


async def main():
    b = Browser(w=1280, h=800)
    await b.start()
    await b.goto(URL, 2.5)
    await b.js('window.confirm=()=>true')      # um confirm() aberto trava o CDP: o app pergunta antes de trocar um desenho mexido
    print('vivid:', await b.js('vivid'), '| LEGACY B3:', await b.js('LEGACY_HEX.B3'), '| botão:', await b.js("!!document.getElementById('btnRecolor')"))
    diffs = []; ok = 0
    for i, (mid, py) in enumerate(PY.items()):
        r = await b.js('%s(%s)' % (JS_MAP, json.dumps(mid)))
        js = json.loads(r)
        if 'erro' in js: diffs.append((mid, 'ERRO ' + js['erro'])); continue
        bad = {k: (py.get(k), js.get(k)) for k in set(py) | set(js) if py.get(k) != js.get(k)}
        if bad: diffs.append((mid, bad))
        else: ok += 1
    print('moldes iguais JS = Python: %d de %d' % (ok, len(PY)))
    for mid, bad in diffs[:12]: print('  DIFERE', mid, bad if isinstance(bad, str) else dict(list(bad.items())[:6]))

    # fluxo do diálogo num molde que o dono listou como bom na lista original (Umaru já foi trocado; usa Perry pose 2 para ter troca visível)
    r = await b.js("""(async()=>{const all=decodeTemplates();const t=all.find(t=>t.name==='Mona Lisa');openTpl(t);await new Promise(r=>setTimeout(r,400));
      applyTheme('light');document.getElementById('btnRecolor').click();await new Promise(r=>setTimeout(r,400));
      const d=document.getElementById('dlgRecolor');
      return JSON.stringify({aberto:d.open,info:document.getElementById('recInfo').textContent.slice(0,120),cv:[document.getElementById('recA').width,document.getElementById('recA').height],aplicarHab:!document.getElementById('recApply').disabled})})()""")
    print('diálogo:', r)
    await b.shot(OUT + 'rec_1_dialogo.png')
    r = await b.js("""(async()=>{const antes=counts.slice();const g0=S.grid.slice();
      document.getElementById('recApply').click();await new Promise(r=>setTimeout(r,300));
      const mudou=S.grid.some((v,i)=>v!==g0[i]);const geo=S.grid.every((v,i)=>(v===0)===(g0[i]===0));
      const toast=document.getElementById('toast').textContent;
      undo();await new Promise(r=>setTimeout(r,200));const volta=S.grid.every((v,i)=>v===g0[i]);
      return JSON.stringify({mudou,geometriaIgual:geo,toast,desfazVolta:volta,aberto:document.getElementById('dlgRecolor').open})})()""")
    print('aplicar/desfazer:', r)
    # celular
    await b.viewport(390, 844, 2, True)
    r = await b.js("""(async()=>{document.getElementById('btnRecolor').scrollIntoView();document.getElementById('btnRecolor').click();await new Promise(r=>setTimeout(r,400));
      const d=document.getElementById('dlgRecolor').getBoundingClientRect();return JSON.stringify({w:d.width|0,h:d.height|0,vp:[innerWidth,innerHeight]})})()""")
    print('celular:', r)
    await b.shot(OUT + 'rec_2_celular.png')
    print('erros de página:', await b.js("window.__erros||'nenhum registrado'"))
    await b.close()

asyncio.run(main())
