"""Novidades no catálogo: passar o mouse num cartão (principalmente o PRIMEIRO) não pode mexer nos outros (posição, rolagem da fileira)."""
import asyncio, sys, json, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep

SNAP = """JSON.stringify((()=>{const row=document.getElementById('homeNewRow');const rr=row.getBoundingClientRect();
  return {scrollLeft:row.scrollLeft,scrollTop:row.scrollTop,rowX:+rr.x.toFixed(2),
  tiles:[...row.children].slice(0,5).map(t=>{const r=t.getBoundingClientRect();return [+r.x.toFixed(2),+r.y.toFixed(2),+r.width.toFixed(2),+r.height.toFixed(2)]}),
  // posição de LAYOUT (sem transform): offsetLeft/offsetTop
  lay:[...row.children].slice(0,5).map(t=>[t.offsetLeft,t.offsetTop])}})())"""


async def hover_tile(b, i):
    r = json.loads(await b.js("(()=>{const t=document.getElementById('homeNewRow').children[%d];const r=t.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()" % i))
    await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=r['x'], y=r['y'])
    await asyncio.sleep(0.6)


async def main(dpr=1.0, w=1280):
    b = B2(w=w, h=900, port=9451)
    await b.start()
    try:
        await b.send('Log.enable'); await b.viewport(w, 900, dpr, False)
        await b.goto('http://localhost:8765/index.html?x=nov%d' % (int(time.time()) % 100000), 3.5)
        await b.js("document.getElementById('homeNewRow').scrollIntoView({block:'center'})", 0.6)
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=5, y=5); await asyncio.sleep(0.5)
        base = json.loads(await b.js(SNAP))
        print('repouso :', base)
        bad = 0
        for i in range(0, 5):
            await hover_tile(b, i)
            s = json.loads(await b.js(SNAP))
            # o cartão sob o mouse sobe/cresce de propósito; os OUTROS não podem sair do lugar, e a fileira não pode rolar
            mexeu = []
            for j in range(5):
                if j == i: continue
                if s['tiles'][j] != base['tiles'][j]: mexeu.append((j, base['tiles'][j], s['tiles'][j]))
            rol = s['scrollLeft'] != base['scrollLeft'] or s['scrollTop'] != base['scrollTop']
            lay = s['lay'] != base['lay']
            ok = not mexeu and not rol and not lay
            bad += (not ok)
            print('%s mouse no cartão %d: scrollLeft %s scrollTop %s | layout igual: %s | outros que mexeram: %s' % ('OK   ' if ok else 'FALHA', i + 1, s['scrollLeft'], s['scrollTop'], not lay, mexeu[:3]))
            if i == 0: print('        cartão 1 em hover:', s['tiles'][0], 'repouso:', base['tiles'][0])
            await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=5, y=5); await asyncio.sleep(0.5)
        # alinhamento: o 1º cartão fica na mesma coluna do título da seção
        al = json.loads(await b.js("JSON.stringify({h2:document.querySelector('#homeNew h2').getBoundingClientRect().x,t0:document.getElementById('homeNewRow').children[0].getBoundingClientRect().x})"))
        okal = abs(al['h2'] - al['t0']) < 0.6
        bad += (not okal)
        print('%s 1º cartão alinhado ao título: título x=%.1f, cartão x=%.1f' % ('OK   ' if okal else 'FALHA', al['h2'], al['t0']))
        # fileira ROLADA: o mesmo teste depois de rolar um cartão e meio para a direita
        await b.js("document.getElementById('homeNewRow').scrollLeft=262", 0.5)
        base2 = json.loads(await b.js(SNAP)); print('rolada  :', base2['scrollLeft'], base2['tiles'][:2])
        for i in range(0, 5):
            r = json.loads(await b.js("(()=>{const t=document.getElementById('homeNewRow').children[%d];const r=t.getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()" % i))
            if r['x'] < 0 or r['x'] > w: continue
            await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=r['x'], y=r['y']); await asyncio.sleep(0.6)
            s = json.loads(await b.js(SNAP))
            mexeu = [(j, base2['tiles'][j], s['tiles'][j]) for j in range(5) if j != i and s['tiles'][j] != base2['tiles'][j]]
            rol = s['scrollLeft'] != base2['scrollLeft']
            ok = not mexeu and not rol
            bad += (not ok)
            print('%s rolada, mouse no cartão %d: scrollLeft %s (era %s) | outros que mexeram: %s' % ('OK   ' if ok else 'FALHA', i + 1, s['scrollLeft'], base2['scrollLeft'], mexeu[:3]))
            await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=5, y=5); await asyncio.sleep(0.4)
        await b.js("document.getElementById('homeNewRow').scrollLeft=0", 0.4)
        await b.send('Input.dispatchMouseEvent', type='mouseMoved', x=5, y=5); await asyncio.sleep(0.4)
        # volta ao repouso
        end = json.loads(await b.js(SNAP))
        print('%s de volta ao repouso igual ao início' % ('OK   ' if end == base else 'FALHA'), '' if end == base else (end, base))
        bad += (end != base)
        await b.shot(OUT + 'novidades_hover_%s.png' % ('1' if dpr == 1 else str(dpr)), clip=None)
        pr = [p for p in b.problems() if 'favicon' not in p]
        print('erros de página:', pr)
        return bad
    finally:
        await b.close()

if __name__ == '__main__':
    d = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 1280
    print('RESUMO: %d com problema' % asyncio.run(main(d, w)))
