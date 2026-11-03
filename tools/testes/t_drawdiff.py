"""O desenho do editor (camada estática + dinâmica) sai IDÊNTICO ao antigo, pixel a pixel, em vários estados?
Compara a página atual com uma cópia ANTIGA do index.html rodando os mesmos cenários (22 cenários: Criar, Montar, 4 placas, tema escuro, seleção, prévias...).
uso:  python tools/testes/t_drawdiff.py [DPR=1] [ARQUIVO_ANTIGO=_old_index.html]
      (o arquivo antigo tem que estar na RAIZ do projeto para o servidor local entregá-lo: copie para lá uma versão de tools/backups/index-pre-*.html e apague depois.
       Antes de refatorar o desenho, guarde o index.html atual em tools/backups/ para ter com o que comparar.)
Rode em DPR 1, 1.25, 1.5 e 2: o antialiasing muda com a escala. Se falhar, grava dd_novo_/dd_antigo_/dd_dif_ em tools/out/."""
import asyncio, sys, json, time, base64, io
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_home2 import B2
from PIL import Image, ImageChops
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out') + os.sep
DPR = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
OLD = sys.argv[2] if len(sys.argv) > 2 else '_old_index.html'

SMALL = "(window.TEMPLATES.find(t=>/Pikachu sentado/.test(t.name)).id)"
BIG = "'mago-negro-chibi-circulo-dourado-grande'"
# cada cenário: JS que põe o estado e depois chama draw() (síncrono)
SCEN = [
    ('1 placa, contas, zoom 16', "openTpl(decodeTemplates().find(t=>t.id===%s));setMode('create');S.zoom=16;S.style='bead';S.showGrid=true;S.showCodes=false;S.hover=null;layout();draw()" % SMALL),
    ('1 placa, passando o mouse (cursor e régua)', "S.hover={x:12,y:20};S.tool='pencil';S.brush=2;draw()"),
    ('1 placa, pincel 3 e espelho H', "S.brush=3;S.mirrorH=true;S.hover={x:8,y:9};draw()"),
    ('1 placa, estilo pixels', "S.mirrorH=false;S.hover=null;S.style='pixel';draw()"),
    ('1 placa, códigos nas contas (zoom 24)', "S.style='bead';S.zoom=24;S.showCodes=true;layout();draw()"),
    ('1 placa, sem grade, zoom 10', "S.showCodes=false;S.showGrid=false;S.zoom=10;layout();draw()"),
    ('1 placa, tema escuro', "S.showGrid=true;S.zoom=16;layout();applyTheme('dark');draw()"),
    ('1 placa, destaque de cor (hover na lista)', "S.hl=CODE_IDX.A4;draw();"),
    ('1 placa, seleção', "S.hl=0;S.sel=new Uint8Array(S.w*S.h);S.selW=S.w;S.selH=S.h;for(let y=10;y<22;y++)for(let x=8;x<30;x++)S.sel[y*S.w+x]=1;draw()"),
    ('1 placa, prévia de forma', "S.sel=null;preview={cells:[[5,5],[6,6],[7,7],[8,8],[9,9],[10,10]],val:CODE_IDX.F5};draw()"),
    ('1 placa, prévia de borracha', "preview={cells:[[5,5],[6,6],[7,7]],val:0};S.tool='eraser';draw()"),
    ('1 placa, depois de pintar (grade mudou)', "preview=null;S.tool='pencil';for(let k=0;k<30;k++)S.grid[100+k]=CODE_IDX.F5;recount();draw()"),
    ('1 placa, desfazer', "undo();draw()"),
    ('Montar, linha por linha', "applyTheme('light');setMode('assemble');S.asm.view='row';S.asm.mirror=false;S.asm.row=groupStart(20);S.hover=null;draw()"),
    ('Montar, linha com a conta sob o mouse (hoverRun)', "S.asm.hoverRun={x0:10,x1:18,y:20};draw()"),
    ('Montar, espelhada', "S.asm.hoverRun=null;S.asm.mirror=true;draw()"),
    ('Montar, 2 linhas e progresso', "setAsmSpan(2);for(let x=0;x<S.w;x++)for(let y=0;y<20;y++)if(S.grid[y*S.w+x])S.done[y*S.w+x]=1;recount();draw()"),
    ('Montar, cor por cor (parecidas)', "S.asm.view='color';S.asm.color=CODE_IDX.A4;draw()"),
    ('Montar, cor por cor sem espelho', "S.asm.mirror=false;draw()"),
    ('4 placas, contas zoom 6 (limites de placa)', "setMode('create');S.done.fill(0);openTpl(decodeTemplates().find(t=>t.id===%s));S.zoom=6;S.style='bead';S.hover=null;layout();draw()" % BIG),
    ('4 placas, zoom 18', "S.zoom=18;layout();draw()"),
    ('4 placas, mouse no meio', "S.hover={x:50,y:50};S.brush=1;draw()"),
]


async def run(page, label):
    b = B2(w=1280, h=900, port=9430 + (0 if page == 'new' else 1))
    await b.start()
    res = {}
    try:
        await b.send('Log.enable'); await b.viewport(1280, 900, DPR, False)
        await b.goto('http://localhost:8765/%s?x=dd%d' % ('index.html' if page == 'new' else OLD, int(time.time()) % 100000), 3.5)
        if page == 'old':
            # a página antiga deixava o lineJoin 'round' do drawCode vazar de um quadro para o outro (e o layout() o zerava): para comparar com o novo, que o
            # define pelo que está na tela, a antiga também começa cada quadro pela mesma regra (round só com códigos nas contas)
            await b.js("(()=>{const o=draw;window.draw=function(){ctx.lineJoin=((S.showCodes&&S.zoom>=22)||(S.mode==='assemble'&&S.zoom>=14))?'round':'miter';return o()}})()")
        for name, js in SCEN:
            try:
                await b.js(js, 0.35)
                du = await b.js("cv.toDataURL('image/png')")
                res[name] = du
            except Exception as e:
                res[name] = 'ERRO ' + str(e)[:120]
        pr = [p for p in b.problems() if 'favicon' not in p]
        if pr: print(label, 'ERROS DE PÁGINA:', pr[:2])
    finally:
        await b.close()
    return res


async def main():
    new = await run('new', 'novo'); old = await run('old', 'antigo')
    bad = 0
    for name, _ in SCEN:
        a, o = new.get(name, ''), old.get(name, '')
        if a.startswith('ERRO') or o.startswith('ERRO'):
            print('FALHA', name, '| novo:', a[:100] if a.startswith('ERRO') else 'ok', '| antigo:', o[:100] if o.startswith('ERRO') else 'ok'); bad += 1; continue
        ia = Image.open(io.BytesIO(base64.b64decode(a.split(',')[1]))).convert('RGBA'); io_ = Image.open(io.BytesIO(base64.b64decode(o.split(',')[1]))).convert('RGBA')
        if ia.size != io_.size:
            print('FALHA', name, 'tamanhos diferentes', ia.size, io_.size); bad += 1; continue
        diff = ImageChops.difference(ia, io_); bbox = diff.getbbox()
        if bbox is None:
            print('OK    idêntico:', name)
        else:
            n = sum(1 for p in diff.getdata() if p != (0, 0, 0, 0)); mx = max(max(p) for p in diff.getdata())
            print('FALHA %s: %d pixels diferentes (máx %d) em %s' % (name, n, mx, bbox)); bad += 1
            tag = ''.join(ch for ch in name if ch.isalnum())[:30]
            ia.save(OUT + 'dd_novo_%s.png' % tag); io_.save(OUT + 'dd_antigo_%s.png' % tag); diff.point(lambda v: min(255, v * 8)).save(OUT + 'dd_dif_%s.png' % tag)
    print('RESUMO: %d cenários, %d com diferença' % (len(SCEN), bad))
asyncio.run(main())
