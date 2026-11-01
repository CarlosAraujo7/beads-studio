"""Projeto 3D da `remessa 3D 3`: Minion lido célula a célula do gráfico VitrumUP (a foto da peça montada está na mesma imagem). As medidas fecham exatamente: caixa de 11×15×8 contas,
dente de uma peça = vão da vizinha em todas as arestas (conferido pelo make_3d.check_disjoint). O outro arquivo da pasta (cubo mágico) é gerado em make_cubes.py.
Coordenadas: y=0 é a 1ª fileira abaixo das tampas; tampa em y=-2, chapa com furo em y=-1, anel azul em y=14, frente em z=7, costas em z=0, laterais em x=0 e x=10."""

M_FRENTE = ["...yy.yy...", "...yyyyy...", "yymmmymmmyy", "kmwwwmwwwmk", ".mw.wmw.wm.", ".mwwwmwwwm.", "yymmmymmmyy", "yyyyyyyyyyy", "yyyyyyykyyy", ".yyykkkyyy.", ".byyyyyyyb.", "ybbbbbbbbby", "ybbbbbbbbby", ".bbb$b$bbb.", ".bbb$b$bbb.", "bbbb$$$bbbb", "bb..bbb..bb"]
M_COSTAS = ["...yy.yy...", "...yyyyy...", "yyyyyyyyyyy", "kkkkkkkkkkk", ".kkkkkkkkk.", ".yyyyyyyyy.", "yyyyyyyyyyy", "yyyyyyyyyyy", "yyyyyyyyyyy", ".yyyyyyyyy.", ".byyyyyyyb.", "ybbbbbbbbby", "ybbbbbbbbby", ".bbbbbbbbb.", ".bbbbbbbbb.", "bbbbbbbbbbb", "bb..bbb..bb"]
M_LADO = [".yyyyyy.", ".kkkkkk.", "kkkkkkkk", "yyyyyyyy", ".yyyyyy.", ".yyyyyy.", ".yyyyyy.", "yyyyyyyy", "bbbbbbbb", ".yy.yyy.", ".yy.yyy.", "bbbbbbbb", "bbbbbbbb", ".bbbbbb.", ".bb..bb."]
M_TAMPA = ["y..y..y", "yyyyyyy", "yyyyyyy", "yyyyyyy", "yyyyyyy", "yyyyyyy", "yyyyyyy", "y..y..y"]
M_CHAPA = ["yy.....yy", "yyyyyyyyy", "yyyyyyyyy", "yyy...yyy", "yyy...yyy", "yyyyyyyyy", "yyyyyyyyy", "yy.....yy"]
M_ANEL = ["..bb...bb..", ".bbbbbbbbb.", ".bbbbbbbbb.", "bb..bbb..bb", "bb..bbb..bb", ".bbbbbbbbb.", ".bbbbbbbbb.", "..bb...bb.."]
M_PE_E = ["..bb.", "..bb.", ".kkkk", "kkkkk"]
M_PE_D = [".bb..", ".bb..", "kkkk.", "kkkkk"]
M_OMBRO = ["yyy", "yyy"]
M_BRACO = [".......kk", "......kkk", ".......yy", "......yy.", ".....yy..", ".yyyyy...", "y...y....", ".yyy....."]
M_OCULOS = [".mmm.mmm.", "mwwwmwwwm", "mw.wmw.wm", "mwwwmwwwm", ".mmm.mmm."]
M_PINO = ["k", "k"]

minion = {
    'id': 'minion-vitrumup', 'name': 'Minion (caixa de encaixe)', 'level': 'Difícil', 'view': [-24, -32], 'disjoint': True,
    'desc': 'Minion de encaixe: caixa de 11×15×8 contas com tampa em degrau, anel azul na base, óculos, pés e braços. Peças lidas do gráfico VitrumUP; os dentes de cada peça batem com os vãos das vizinhas em todas as arestas. A posição dos braços e das peças amarelas pequenas foi deduzida do encaixe e da foto, porque o gráfico não diz: confira antes de colar.',
    'pieces': [{'name': 'Frente', 'qty': 1, 'rows': M_FRENTE}, {'name': 'Costas', 'qty': 1, 'rows': M_COSTAS}, {'name': 'Lateral', 'qty': 2, 'rows': M_LADO, 'note': '2 iguais; o vão de 1 conta é por onde passa o ombro'},
               {'name': 'Tampa', 'qty': 1, 'rows': M_TAMPA}, {'name': 'Chapa com furo', 'qty': 1, 'rows': M_CHAPA, 'note': 'fica logo abaixo da tampa'}, {'name': 'Anel da base', 'qty': 1, 'rows': M_ANEL, 'note': 'os 2 furos recebem os pés'},
               {'name': 'Pé esquerdo', 'qty': 2, 'rows': M_PE_E, 'note': '2 iguais, um colado no outro'}, {'name': 'Pé direito', 'qty': 2, 'rows': M_PE_D, 'note': '2 iguais, um colado no outro'},
               {'name': 'Ombro', 'qty': 2, 'rows': M_OMBRO, 'note': 'atravessa o vão da lateral e o laço do braço'}, {'name': 'Braço', 'qty': 2, 'rows': M_BRACO, 'note': 'mão preta para baixo, virada para a frente'},
               {'name': 'Óculos', 'qty': 1, 'rows': M_OCULOS}, {'name': 'Pupila', 'qty': 2, 'rows': M_PINO, 'note': 'pino que atravessa os óculos e a frente'}],
    'parts': [{'piece': 0, 'face': 'front', 'at': [0, -2, 7]}, {'piece': 1, 'face': 'back', 'at': [10, -2, 0]}, {'piece': 2, 'face': 'left', 'at': [0, 0, 0]}, {'piece': 2, 'face': 'left', 'at': [10, 0, 0]},
              {'piece': 3, 'face': 'top', 'at': [2, -2, 0]}, {'piece': 4, 'face': 'top', 'at': [1, -1, 0]}, {'piece': 5, 'face': 'top', 'at': [0, 14, 0]},
              {'piece': 6, 'face': 'front', 'at': [0, 14, 3]}, {'piece': 6, 'face': 'front', 'at': [0, 14, 4]}, {'piece': 7, 'face': 'front', 'at': [6, 14, 3]}, {'piece': 7, 'face': 'front', 'at': [6, 14, 4]},
              {'piece': 8, 'face': 'front', 'at': [-2, 9, 3]}, {'piece': 8, 'face': 'front', 'at': [10, 9, 3]}, {'piece': 9, 'face': 'left', 'at': [-2, 8, 2], 'rot': 1}, {'piece': 9, 'face': 'left', 'at': [12, 8, 2], 'rot': 1},
              {'piece': 10, 'face': 'front', 'at': [1, 0, 8]}, {'piece': 11, 'face': 'top', 'at': [3, 2, 7]}, {'piece': 11, 'face': 'top', 'at': [7, 2, 7]}],
    'steps': ['Monte as 18 peças e passe o ferro em cada uma, dos dois lados, com papel de forno; deixe esfriar sob um peso.',
              'Erga a caixa: encaixe a frente, as costas e as duas laterais no anel azul da base. Os dentes de uma peça entram nos vãos da vizinha.',
              'Encaixe por cima a chapa com furo e, sobre ela, a tampa: as duas se prendem nos dentes do alto da frente e das costas.',
              'Cole os dois pés esquerdos entre si e os dois direitos entre si, e encaixe cada par num furo do anel.',
              'Passe cada ombro pelo vão da lateral e encaixe o laço do braço nele, com a mão preta para baixo.',
              'Prenda os óculos na frente com as pupilas, que atravessam os furos dos óculos e da frente. Use uma gota de cola onde ficar frouxo.'],
}

R3D3 = [minion]
