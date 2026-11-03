"""Confere um gráfico de contas COM LEGENDA contra o que está IMPRESSO nele (pedido do usuário, 2026-11-02: o número escrito em cada quadradinho serve para não errar a
posição/identidade das contas, mesmo quando as cores são parecidas). Ver CLAUDE.md §7.37. SÓ LEITURA: nada vai para o catálogo.

uso:  python tools/legend_check.py REMNUM IDX px py ox oy W H "COD:n COD:n …" [--n 24] [--zoom 5] [--thr 225] [--fix "lin,col=COD;lin,col=."]
  px py ox oy W H = a grade do pix_graph (ox/oy = BORDA esquerda/de cima da 1ª célula; a 1ª célula tem que ser a 1ª CONTA do desenho, SEM a régua numerada);
  "COD:n" = a legenda impressa, na ordem em que as amostras aparecem; --fix usa linha,coluna a partir de 1 (as da folha) = código lido a olho ('.' = vazio).
  --ocr = LÊ o código impresso em cada célula com o RapidOCR (precisa do python com `pip install rapidocr-onnxruntime`; ~0,5 s por célula) e lista onde o número e a cor discordam;
  --ocr-auto adota o número só onde a troca conserta a contagem (código que sobra -> código que falta); --ocr-scale N = ampliação da célula antes de ler (padrão automático: ~150/passo).
Faz três coisas:
 1. classifica cada célula pela cor mais próxima das amostras da legenda e compara com as CONTAGENS impressas (tem que fechar em todos os códigos);
 2. salva em tools/out/legend_check_REM_IDX.png as N células mais DUVIDOSAS (menor margem entre a 1ª e a 2ª cor), ampliadas e com a posição: leia o código escrito nelas
    e corrija com --fix (no pix_graph a correção é fix={(lin-1, col-1): 'COD'});
 3. separa as células BRANCAS: com texto (H2 impresso) é conta branca; sem texto é vazio. O fundo branco ligado à borda não sabe distinguir (conta branca na borda some).
Régua e grade: confira também o tamanho (colunas x linhas = os números da régua) e olhe a última coluna/linha com a grade sobreposta (gridfit.py --out); o molde da planta verde
(remessa 25) perdeu a última coluna e a 1ª linha por causa disso, não por causa da cor."""
import os, sys, argparse
SP = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
for k in ('rem', 'idx'): ap.add_argument(k)
for k in ('px', 'py', 'ox', 'oy'): ap.add_argument(k, type=float)
for k in ('W', 'H'): ap.add_argument(k, type=int)
ap.add_argument('legend')
ap.add_argument('--n', type=int, default=24); ap.add_argument('--zoom', type=int, default=5); ap.add_argument('--thr', type=int, default=225, help='(sem uso; o branco agora é uma cor da legenda)'); ap.add_argument('--fix', default='')
ap.add_argument('--ocr', action='store_true'); ap.add_argument('--ocr-auto', action='store_true'); ap.add_argument('--ocr-scale', type=int, default=0)
a = ap.parse_args()
os.environ['REMNUM'] = a.rem; os.environ.setdefault('BEADPAL', '120')
sys.path.insert(0, SP)
import numpy as np, cv2
from PIL import Image, ImageDraw
import r22_exfinal as R
r6, illus = R.r6, R.illus
idx, px, py, ox, oy, W, H = int(a.idx), a.px, a.py, a.ox, a.oy, a.W, a.H
grid = dict(px=px, py=py, ox=ox, oy=oy, W=W, H=H)
codes = [t.split(':') for t in a.legend.split()]
cnt = {c: int(n) for c, n in codes}
nonwhite = [(c, n) for c, n in cnt.items() if c != 'H2']
fix = {}
for part in [p for p in a.fix.split(';') if p.strip()]:
    pos, code = part.split('=')
    lin, col = [int(v) for v in pos.split(',')]
    fix[(lin - 1, col - 1)] = code.strip()

rgb = np.array(R.source_img(idx)).astype(np.uint8)
sw = R.legend_swatches(idx, int(oy + H * py + 35), len(nonwhite))
if len(sw) != len(nonwhite): print('AVISO: %d amostras na legenda, esperadas %d' % (len(sw), len(nonwhite)))
cls = [(c, np.array(col, float)) for (c, _), col in zip(nonwhite, sw)] + [('H2', np.array([255., 255., 255.]))]      # o branco entra como mais uma cor da legenda
arr = r6.load_cells(idx, px=grid, mode=True)
lab = illus._lab(arr); cl = np.stack([illus._lab(c[1]) for c in cls])
d = np.linalg.norm(lab[:, :, None, :] - cl[None, None, :, :], axis=3)
order = np.argsort(d, axis=2)
WI = len(cls) - 1                                                  # índice do branco
white = (order[:, :, 0] == WI) | (arr.min(axis=2) > 250)           # a cor mais próxima é o branco (a lavanda H10 não é)


def has_text(y, x, m=0.12):
    sub = rgb[int(round(oy + (y + m) * py)):int(round(oy + (y + 1 - m) * py)), int(round(ox + (x + m) * px)):int(round(ox + (x + 1 - m) * px))]
    if sub.size == 0: return False
    g = cv2.cvtColor(sub, cv2.COLOR_RGB2GRAY).astype(np.float32); h, w = g.shape
    b = max(2, min(h, w) // 7)
    bg = np.median(np.concatenate([g[:b].ravel(), g[-b:].ravel(), g[:, :b].ravel(), g[:, -b:].ravel()]))
    return float(np.abs(g - bg).max()) >= 45


# 1) contagens: célula não branca = cor mais próxima da legenda; branca COM texto = H2; branca sem texto = vazio; --fix manda
code_of, rows_ = {}, []
for y in range(H):
    for x in range(W):
        if (y, x) in fix: code_of[(y, x)] = fix[(y, x)]; continue
        if white[y, x]:
            if has_text(y, x): code_of[(y, x)] = 'H2'
            continue
        code_of[(y, x)] = cls[order[y, x, 0]][0]
        rows_.append((float(d[y, x, order[y, x, 1]] - d[y, x, order[y, x, 0]]), y, x, cls[order[y, x, 0]][0], cls[order[y, x, 1]][0]))
names_ = [c[0] for c in cls]
ocr_conf = []                                  # (y, x, código pela cor, código pelo número, texto cru, confiança)
if a.ocr or a.ocr_auto:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        sys.exit('OCR indisponível neste Python: rode com o python que tem o RapidOCR (pip install rapidocr-onnxruntime).')
    import re
    eng = RapidOCR()
    SC = a.ocr_scale or max(4, int(round(150 / px)))
    vocab = list(cnt.keys())

    def lev(s1, s2):
        p_ = list(range(len(s2) + 1))
        for i_, c1 in enumerate(s1, 1):
            q_ = [i_]
            for j_, c2 in enumerate(s2, 1): q_.append(min(p_[j_] + 1, q_[j_ - 1] + 1, p_[j_ - 1] + (c1 != c2)))
            p_ = q_
        return p_[-1]

    def canon(t):                              # confusões comuns de leitura (8 no lugar de B etc.)
        if not t: return t
        return {'8': 'B', '6': 'G', '0': 'D'}.get(t[0], t[0]) + t[1:].replace('O', '0').replace('I', '1').replace('L', '1').replace('S', '5').replace('Z', '2').replace('B', '8')

    def cands(t, conf):                        # códigos da legenda compatíveis com o texto lido; [] = leitura sem valor (curta, ruim ou duvidosa)
        if not t or len(t) < 2: return []
        sc = sorted((lev(canon(t), canon(v)), v) for v in vocab)
        d0 = sc[0][0]
        if d0 > 1 or (d0 == 1 and conf < 0.85): return []
        return [v for dd, v in sc if dd == d0]

    def ocr_cell(y, x, m=0.05):
        c = rgb[int(round(oy + (y + m) * py)):int(round(oy + (y + 1 - m) * py)), int(round(ox + (x + m) * px)):int(round(ox + (x + 1 - m) * px))]
        g = cv2.cvtColor(c, cv2.COLOR_RGB2GRAY).astype(np.float32); h_, w_ = g.shape; b0 = max(2, min(h_, w_) // 7)
        bgv = np.median(np.concatenate([g[:b0].ravel(), g[-b0:].ravel(), g[:, :b0].ravel(), g[:, -b0:].ravel()]))
        dif = np.abs(g - bgv); top = max(float(np.percentile(dif, 99)), 25.0)
        pol = cv2.cvtColor((255 * (1 - np.clip(dif / top, 0, 1))).astype(np.uint8), cv2.COLOR_GRAY2BGR)           # texto preto sobre branco, qualquer que seja a cor da célula
        for im_, pad_ in ((pol, (255, 255, 255)), (cv2.cvtColor(c, cv2.COLOR_RGB2BGR), None)):                    # 1º o normalizado; se não ler nada, a célula como está
            big = cv2.resize(im_, None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC)
            big = cv2.copyMakeBorder(big, 5 * SC, 5 * SC, 5 * SC, 5 * SC, cv2.BORDER_CONSTANT if pad_ else cv2.BORDER_REPLICATE, value=pad_)
            r_, _ = eng(big, use_det=True, use_cls=False, use_rec=True)
            if r_:
                b_ = max(r_, key=lambda z: float(z[2])); return re.sub(r'[^A-Z0-9]', '', str(b_[1]).upper()), float(b_[2])
        return None, 0.0

    n_none = n_read = n_ok = 0
    for (y, x), c0 in sorted(code_of.items()):
        if (y, x) in fix or c0 == '.': continue
        t, sc_ = ocr_cell(y, x)
        cs = cands(t, sc_)
        if not cs: n_none += 1; continue
        n_read += 1
        if c0 in cs: n_ok += 1; continue                       # o número é compatível com a cor (se havia empate, a cor desempatou)
        ocr_conf.append((y, x, c0, cs[0] if len(cs) == 1 else '/'.join(cs), t, sc_))
    adopted = []
    if a.ocr_auto:                              # só adota a troca que move uma conta de um código que SOBRA para um que FALTA na legenda (descarta os alarmes falsos)
        g0 = {}
        for k_, c_ in code_of.items():
            if c_ != '.': g0[c_] = g0.get(c_, 0) + 1
        for y, x, c0, cs_, t, sc_ in ocr_conf:
            if '/' not in cs_ and g0.get(c0, 0) > cnt.get(c0, 0) and g0.get(cs_, 0) < cnt.get(cs_, 0):
                code_of[(y, x)] = cs_; g0[c0] -= 1; g0[cs_] = g0.get(cs_, 0) + 1; adopted.append((y, x))
    print('OCR: %d células lidas pelo número (%d confirmam a cor), %d sem leitura útil (ficam com a cor), %d em que o número e a cor DISCORDAM%s' % (n_read, n_ok, n_none, len(ocr_conf), (' | %d adotadas (movem 1 conta de código que sobra para um que falta); as outras ficam com a cor' % len(adopted)) if a.ocr_auto else ''))
    for y, x, c0, sn, t, sc_ in ocr_conf: print('  linha %2d coluna %2d: cor=%s número=%s (leu "%s", confiança %.2f)' % (y + 1, x + 1, c0, sn, t, sc_))
    if ocr_conf: print('  --fix "%s"   |   fix={%s}' % (';'.join('%d,%d=%s' % (y + 1, x + 1, sn) for y, x, _, sn, _, _ in ocr_conf), ', '.join("(%d, %d): '%s'" % (y, x, sn) for y, x, _, sn, _, _ in ocr_conf)))
got = {}
for (y, x), c in code_of.items():
    if c != '.': got[c] = got.get(c, 0) + 1
print('grade', grid, '| legenda impressa:', sum(cnt.values()), 'contas')
ok = True
for c in cnt:
    g = got.get(c, 0); ok &= (g == cnt[c])
    print('  %-4s legenda %3d | lido %3d %s' % (c, cnt[c], g, '' if g == cnt[c] else '  <-- difere %+d' % (g - cnt[c])))
print('RESULTADO:', 'contagens IGUAIS à legenda em todos os códigos' if ok else 'contagens DIFERENTES: não entregue como cópia exata (ache a causa: grade, célula duvidosa ou fundo)', '| lidas', sum(got.values()))

over = [c for c in cnt if got.get(c, 0) > cnt[c]]; under = [c for c in cnt if got.get(c, 0) < cnt[c] and c in names_]
for u in under:
    for o in over:
        if o not in names_: continue
        cand = sorted((float(d[y, x, names_.index(u)] - d[y, x, names_.index(o)]), y, x) for (y, x), c in code_of.items() if c == o and not white[y, x] and (y, x) not in fix)[:6]
        print('suspeitas: a legenda tem %s a mais e %s a menos; células lidas como %s mais perto de %s (lin,col distância-extra): %s' % (u, o, o, u, ' '.join('(%d,%d)%.1f' % (y + 1, x + 1, m) for m, y, x in cand)))

# 3) brancas
wt = [(y + 1, x + 1) for y in range(H) for x in range(W) if white[y, x] and (y, x) not in fix and has_text(y, x)]
wn = [(y + 1, x + 1) for y in range(H) for x in range(W) if white[y, x] and (y, x) not in fix and not has_text(y, x)]
print('brancas COM texto (conta branca H2): %d %s' % (len(wt), wt[:12]))
bg = r6.flood_fn(arr, lambda p, q: bool(white[q]))
holes = [(y, x) for (y, x) in [(y - 1, x - 1) for y, x in wn] if not bg[y, x]]
print('brancas SEM texto dentro do desenho (vão no meio, NÃO é conta): %d %s' % (len(holes), [(y + 1, x + 1) for y, x in holes][:12]))
edge_dropped = [(y + 1, x + 1) for y, x in [(y - 1, x - 1) for y, x in wt] if bg[y, x]]
if edge_dropped: print('ATENÇÃO: conta branca (com texto) ligada ao fundo branco: o fundo a engoliria; conte-a:', edge_dropped[:12])

# 2) células duvidosas
rows_.sort()
sel = [(-1.0, y, x, 'cor ' + c0, 'núm ' + sn) for y, x, c0, sn, _, _ in ocr_conf] + rows_[:a.n]
Z = a.zoom; per = 6; cw = int(px * Z) + 2; chh = int(py * Z) + 2
sheet = Image.new('RGB', (per * (cw + 8), max(1, (len(sel) - 1) // per + 1) * (chh + 28)), (255, 255, 255)); dr = ImageDraw.Draw(sheet)
for i, (m, y, x, c1, c2) in enumerate(sel):
    tile = rgb[int(round(oy + y * py)):int(round(oy + (y + 1) * py)), int(round(ox + x * px)):int(round(ox + (x + 1) * px))]
    X0 = (i % per) * (cw + 8); Y0 = (i // per) * (chh + 28)
    sheet.paste(Image.fromarray(tile).resize((cw, chh), Image.LANCZOS), (X0, Y0))
    dr.text((X0, Y0 + chh + 2), '#%d  lin %d col %d' % (i + 1, y + 1, x + 1), fill=(0, 0, 0)); dr.text((X0, Y0 + chh + 13), '%s/%s  m=%.1f' % (c1, c2, m), fill=(160, 0, 0))
os.makedirs(os.path.join(SP, 'out'), exist_ok=True)
outp = os.path.join(SP, 'out', 'legend_check_%s_%d.png' % (a.rem, idx)); sheet.save(outp)
print('as %d células mais duvidosas (cor diz / 2ª cor; margem): %s' % (len(sel), ' '.join('(%d,%d)%s/%s=%.1f' % (y + 1, x + 1, c1, c2, m) for m, y, x, c1, c2 in sel[:10])))
print('folha para ler os números:', outp)
