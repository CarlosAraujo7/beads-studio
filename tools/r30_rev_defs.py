"""Definições da revisão da remessa 30 (tools/r30_rev.py): um item por molde que o dono mandou nas capturas (2026-11-05). Coordenadas = linhas do molde ATUAL do
catálogo (ou do reconvertido, quando há reconv), lidas em tools/r30_revsheet.py."""
from r30_rev import REV, eyes, reconv, yellow_all, E4L, E4R, E3L, E3R, E2, E2B

SER = 'Seras Victoria (Hellsing, chibi, braço de sombra)'
ALU = 'Alucard (Hellsing, chibi, pistolas e capa)'
REV[SER] = dict(reconv=reconv(2, SER, bg='flat', tol=50, K=40), ops=[])
REV[ALU] = dict(reconv=reconv(77, ALU, mask=yellow_all(), K=40), ops=[])

# ---- Hellsing: rosto redesenhado sobre a reconversão (olhos vermelhos com pálpebra preta e brilho; sem boca)
REV[SER]['ops'] = [('map', 13, 18, 12, 21, {'G1': 'E11', 'F9': 'E11', 'F11': 'E11'}),
                   ('block', 16, 13, ['EEEEEEEE']), ('block', 17, 13, ['EEEEEEEE']),
                   ('block', 13, 13, E3L), ('block', 13, 17, E4R())]
REV[SER]['leg'] = {'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F5', 'L': 'F3', 'E': 'E11'}
REV[ALU]['ops'] = [('map', 10, 14, 18, 26, {'A1': 'E11', 'A12': 'E14', 'M9': 'E14', 'G14': 'E14'}),
                   ('block', 9, 23, ['MM']),                                   # o brilho vermelho acima do olho (a arte tem um rastro de luz)
                   ('block', 10, 22, E4R()), ('block', 14, 21, ['EEE'])]
REV[ALU]['leg'] = {'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F5', 'L': 'F3', 'E': 'E11'}

# ---- Louise: olhos grandes magenta, pálpebra preta, brilho branco; o rosto fica liso
REV['Louise (Zero no Tsukaima, chibi)'] = eyes(15, 15, 15, 22, 'F7', 'D13', 'E4', skin='E11')
# ---- Yusuke (cartão): sobrancelhas grossas e olhos escuros com brilho; rosto sem o caramelo manchado
REV['Yusuke Urameshi (Yu Yu Hakusho, chibi, cartão)'] = eyes(11, 4, 11, 10, 'H6', 'H5', 'H4', skin='E14', tl=['KKK', 'WHD', 'WDD'], tr=['KKK', 'DHW', 'DDW'], pre=[
    ('map', 10, 13, 3, 13, {'M9': 'E14', 'H3': 'E14', 'H2': 'E14'}), ('block', 10, 3, ['EEEEEEEEEEE']), ('block', 10, 4, ['KKK   KKK'])])
# ---- Sion Glenn: olho direito grande (castanho-avermelhado) e o esquerdo menor, perto da franja
REV['Sion Glenn (Wistoria, chibi)'] = eyes(13, 8, 13, 12, 'G8', 'F11', 'F4', skin='E14', tl=E3L, tr=E3R, pre=[('map', 13, 16, 7, 14, {'M9': 'E14', 'H3': 'E14', 'H2': 'E14'})])

# ---- Wistoria
REV['Colette Loire (Wistoria, chibi)'] = eyes(13, 7, 13, 13, 'C9', 'C8', 'C7', skin='E14', pre=[('map', 12, 16, 7, 16, {'M9': 'E14', 'H3': 'E14', 'H2': 'E14', 'H6': 'E14', 'E8': 'E14'})])
REV['Elfaria (Wistoria, chibi)'] = eyes(12, 13, 12, 19, 'C9', 'C8', 'C7', skin='E11', pre=[
    ('map', 12, 16, 12, 22, {'M9': 'E11', 'M12': 'E11', 'E8': 'E11', 'H2': 'E11', 'C9': 'E11', 'H4': 'E11', 'H7': 'E11', 'C14': 'E11'})])
REV['Elfo de cabelo verde (Wistoria, chibi)'] = eyes(13, 7, 13, 14, 'B15', 'B12', 'B8', skin='E14', pre=[
    ('map', 13, 16, 7, 17, {'M9': 'E14', 'H2': 'E14', 'H3': 'E14', 'B15': 'E14', 'H7': 'E14'})])
REV['Garoto de cabelo verde-água (Wistoria, chibi)'] = eyes(13, 8, 13, 14, 'C9', 'C8', 'C7', skin='E11', pre=[
    ('map', 13, 16, 8, 17, {'M9': 'E11', 'H7': 'E11', 'C9': 'E11', 'C11': 'E11', 'C2': 'E11'})])
REV['Garoto de óculos e cabelo azul-escuro (Wistoria, chibi)'] = eyes(16, 6, 16, 12, 'D21', 'D13', 'D12', skin='E14', pre=[
    ('map', 17, 19, 6, 16, {'H7': 'E14', 'H6': 'E14', 'M9': 'E14', 'G1': 'E14', 'D15': 'E14', 'H2': 'E14'}),
    ('map', 18, 23, 7, 15, {'G1': 'E14', 'M9': 'E14', 'A12': 'E14'})])

# ---- Soul Eater
REV['Maka Albarn (Soul Eater, chibi, livro)'] = dict(leg={'H': 'H2'}, ops=[('map', 0, 15, 0, 26, {'B11': 'M9'}), ('block', 14, 7, ['H']), ('block', 12, 16, ['H'])])
REV['Maka Albarn (Soul Eater, chibi, versão 2)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'B15', 'M': 'B12', 'E': 'E11'}, ops=[
    ('map', 0, 14, 0, 31, {'B11': 'M9'}), ('map', 12, 15, 9, 22, {'G14': 'E11', 'G7': 'E11', 'H3': 'E11'}),
    ('block', 14, 11, ['EE']), ('block', 11, 11, ['KKK', 'DHD', 'WMM']), ('block', 11, 17, ['KKK', 'DHD', 'MMW'])])
REV['Soul Eater Evans (Soul Eater, chibi)'] = eyes(18, 12, 19, 21, 'G8', 'F8', 'F5', skin='E14', tl=E4L(), tr=['KKKK', 'DHDK', 'MMMW'],
                                                   pre=[('map', 16, 21, 10, 21, {'M9': 'E14'})])
REV['Death the Kid (Soul Eater, chibi)'] = eyes(15, 5, 16, 15, 'G7', 'A13', 'A13', skin='E11', tl=['KKKKK', 'WDHDD', 'WMMMM', ' LLLL'], tr=['KKKK', 'DHDW', 'MMMW'],
                                                pre=[('map', 13, 19, 11, 19, {'M9': 'E11'}), ('map', 18, 18, 5, 5, {'M9': 'E11'})])
REV['Blair (Soul Eater, gata)'] = dict(leg={'K': 'H7', 'Y': 'A3', 'F': 'F12', 'S': 'H6'}, ops=[
    ('block', 28, 14, ['KKK']), ('block', 29, 14, ['YKY']), ('block', 28, 19, ['KKK']), ('block', 29, 19, ['YKY']),
    ('block', 28, 13, ['S']), ('block', 28, 22, ['SS']), ('block', 29, 22, ['F'])])
REV['Crona (Soul Eater, chibi, com Ragnarok)'] = dict(leg={}, ops=[('map', 15, 27, 13, 28, {'M9': 'E11'})])

# ---- Slam Dunk (olhos em branco sem pupila: pálpebra preta e pupila; sobrancelhas bravas onde a arte tem)
REV['Hanamichi Sakuragi (Slam Dunk, chibi, bola de basquete)'] = dict(leg={'K': 'H7'}, ops=[
    ('map', 13, 15, 8, 19, {'M9': 'E14'}), ('block', 14, 9, ['KKKK']), ('block', 15, 11, ['K']), ('block', 14, 16, ['KKK']), ('block', 15, 17, ['K'])])
REV['Hanamichi Sakuragi (Slam Dunk, chibi, Shohoku 10)'] = dict(leg={'K': 'H7', 'W': 'H2', 'E': 'E14', 'P': 'F14'}, ops=[
    ('map', 10, 15, 4, 17, {'M9': 'E14', 'G2': 'E14', 'E11': 'E14'}), ('block', 12, 11, ['E']),
    ('block', 14, 5, ['KKKK']), ('block', 15, 5, ['WWKW']), ('block', 14, 12, ['KKKK']), ('block', 15, 12, ['WKWW']),
    ('block', 12, 5, ['KK']), ('block', 13, 7, ['KK']), ('block', 13, 12, ['KK']), ('block', 12, 14, ['KK']),
    ('block', 16, 6, ['PP']), ('block', 16, 13, ['PP'])])
REV['Hanamichi Sakuragi (Slam Dunk, chibi, mãos nos bolsos)'] = dict(leg={'K': 'H7'}, ops=[
    ('map', 14, 14, 2, 14, {'H1': 'H2'}), ('block', 13, 3, ['KKK']), ('block', 14, 4, ['K']), ('block', 13, 11, ['KK']), ('block', 14, 11, ['K'])])
REV['Hanamichi Sakuragi (Slam Dunk, chibi, fantasia de macaco)'] = dict(leg={'K': 'H7', 'W': 'H2', 'S': 'G9'}, ops=[
    ('block', 13, 9, ['S']), ('block', 14, 7, ['SSS']), ('block', 15, 8, ['SS']),
    ('block', 13, 10, ['KKKK']), ('block', 14, 10, ['WWKW']), ('block', 13, 14, ['S']), ('block', 14, 14, ['S']),
    ('block', 14, 15, ['WKWW']), ('block', 15, 15, ['SSS']),
    ('block', 11, 9, ['KK']), ('block', 12, 11, ['KK']), ('block', 12, 16, ['KK']), ('block', 11, 18, ['KK'])])
REV['Ryota Miyagi (Slam Dunk, chibi)'] = dict(leg={'K': 'H7', 'W': 'H2', 'E': 'E14'}, ops=[
    ('map', 18, 21, 9, 24, {'M9': 'E14', 'H3': 'H2'}),
    ('block', 18, 10, ['KKKKK']), ('block', 19, 10, ['WWKWW']), ('block', 20, 10, ['WWKWW']),
    ('block', 18, 19, ['KKKKK']), ('block', 19, 19, ['WWKWW']), ('block', 20, 19, ['WWKWW']), ('block', 21, 20, ['EEE']),
    ('block', 16, 10, ['KK']), ('block', 17, 12, ['KK']), ('block', 16, 22, ['KK'])])
# Rukawa (olho fechado: traço preto) e Sakuragi (olho apertado ">" como na arte, sem a boca aberta, §4.8)
REV['Rukawa e Sakuragi (Slam Dunk, chibi, toque de mãos)'] = dict(leg={'K': 'H7', 'E': 'E11', 'S': 'E1', 'P': 'F14'}, ops=[
    ('block', 12, 14, ['KKE']), ('block', 14, 13, ['PP']),
    ('map', 9, 17, 27, 30, {'G14': 'E1', 'H2': 'E1'}),
    ('block', 11, 29, ['K']), ('block', 12, 30, ['K']), ('block', 13, 29, ['K']), ('block', 13, 31, ['PP'])])          # o ">" uma coluna para dentro: na coluna 28 ele colava no contorno do rosto

# ---- Coelho: o olho esquerdo tinha virado anel cinza; os dois olhos redondos (contorno preto, brilho branco à esquerda, pupila escura, íris laranja embaixo)
REV['Coelho branco de cartola (chibi)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'G8', 'M': 'F6', 'L': 'F2', 'I': 'H1'}, ops=[
    ('block', 11, 21, [' KKI', 'KHDK', 'KMLK', ' KK ']),
    ('block', 13, 14, [' KK ', 'KHDK', 'KMLK', ' KK '])])
# ---- Ram: olho maior como na arte (íris de 3 contas, pálpebra preta, branco do lado de fora, brilho)
REV['Ram (Re:Zero, chibi, capuz de gato)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F8', 'L': 'F5'}, ops=[
    ('block', 17, 9, ['KKKKK', 'WDHDK', 'WMMMK', ' LLLK'])])
# ---- Shalltear: rosto branco (era H1, que é a conta TRANSPARENTE) e olhos vermelhos de 2 contas (escuro em cima, vermelho e um brilho rosa embaixo)
REV['Shalltear Bloodfallen (Overlord, chibi)'] = dict(leg={'K': 'H7', 'D': 'G8', 'M': 'F8', 'L': 'F5', 'P': 'F14', 'W': 'H2'}, ops=[
    ('map', 14, 20, 6, 14, {'H1': 'H2'}), ('block', 18, 6, ['W']), ('block', 20, 8, ['WW W']),
    ('block', 14, 7, ['KK']), ('block', 15, 6, ['K']), ('block', 15, 7, ['DD', 'DD', 'MM', 'LP']),
    ('block', 14, 12, ['KK']), ('block', 15, 14, ['K']), ('block', 15, 12, ['DD', 'DD', 'MM', 'LP'])])
# ---- Kanna: olhos grandes azuis sem a caixa preta (pálpebra, íris escura -> média -> clara, brilho à esquerda, branco do lado de fora); manchas M9 da franja viram cabelo
REV["Kanna Kamui (Miss Kobayashi's Dragon Maid, chibi)"] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'C9', 'M': 'C8', 'L': 'C13', 'E': 'E11', 'P': 'E1'}, ops=[
    ('map', 15, 16, 8, 17, {'M9': 'D8', 'M12': 'D8'}),
    ('block', 17, 9, ['KKKK']), ('block', 18, 8, ['KHDDD', 'WDMMD', 'EMLLM', ' ELLE']),
    ('block', 16, 18, ['KKKK']), ('block', 17, 18, ['HDDDW', 'DMMDW', 'ELLM ', 'EEP'])])
# ---- Sunraku: os buracos da máscara tinham sumido no preto: pele clara com a íris do lado de dentro (os dois olham para a frente)
REV['Sunraku (Shangri-La Frontier, chibi)'] = dict(leg={'K': 'H7', 'S': 'E8', 'I': 'F11'}, ops=[
    ('block', 8, 14, ['S']), ('block', 9, 13, ['IS']),
    ('block', 9, 10, ['KK']), ('block', 10, 10, ['SI'])])

# ---- Kuroko no Basket
# Akashi (olhos semicerrados, um vermelho e outro dourado como na arte): pálpebra preta, branco dos dois lados, íris de 2 tons
REV['Seijuro Akashi (Kuroko no Basket, chibi, bola)'] = dict(leg={'K': 'H7', 'W': 'H2', 'O': 'A10', 'G': 'A13', 'R': 'F8', 'P': 'E3'}, ops=[
    ('block', 15, 15, ['KKKW']), ('block', 16, 15, ['WOG']),
    ('block', 17, 7, ['KKK']), ('block', 18, 7, ['WRPW'])])
# Kise (cartão): os dois olhos eram mancha preta com cinza; pálpebra, íris castanho-escura em cima, caramelo, brilho, dourado embaixo
REV['Ryota Kise (Kuroko no Basket, chibi, cartão)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'G8', 'M': 'G7', 'L': 'G9', 'E': 'E14'}, ops=[
    ('block', 20, 17, [' KKKKK', 'KDDDDK', 'EMHMME', ' LLL  ']),
    ('block', 22, 8, ['KKKKK', ' DDDD', ' HMMM', '  LL '])])
# Kagami (bola): olhos vermelhos com pálpebra inclinada, íris escura -> vermelha -> coral, brilho do mesmo lado nos dois
REV['Taiga Kagami (Kuroko no Basket, chibi, bola)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F8', 'L': 'F12', 'E': 'E11'}, ops=[
    ('block', 16, 17, ['KKKKK', 'DDHDK', 'DMMMK', 'WLLLK']),
    ('block', 20, 6, ['  KKK ', 'KWDDHK', 'EWDMMK', '  MLLK'])])
# Kise (piscando): o olho fechado tinha sumido (era só pele): traço preto descendo para dentro; no aberto, íris com brilho e dourado embaixo
REV['Ryota Kise (Kuroko no Basket, chibi, piscando)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'F11', 'L': 'A11'}, ops=[
    ('block', 18, 6, ['KKK']), ('block', 19, 9, ['KK']),
    ('block', 19, 17, ['DHD']), ('block', 21, 17, ['LLL'])])
# Kuroko (bola): os dois olham para a direita; íris de 3 tons (azul-marinho, azul, azul-claro) com brilho e o branco do lado de fora
REV['Tetsuya Kuroko (Kuroko no Basket, chibi, bola)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'D15', 'M': 'C8', 'L': 'D17', 'E': 'E1'}, ops=[
    ('block', 16, 12, ['KK']), ('block', 17, 12, ['DH']), ('block', 18, 12, ['MM', 'LL']),
    ('block', 16, 18, ['WWDH', 'WWMM']), ('block', 18, 19, ['ELL'])])
# Kuroko (cartão): os olhos eram blocos pretos: íris azul-marinho -> azul -> azul-claro com brilho; mancha caramelo da bochecha vira pele
REV['Tetsuya Kuroko (Kuroko no Basket, chibi, cartão)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'D15', 'M': 'C9', 'L': 'C8', 'A': 'A12'}, ops=[
    ('block', 19, 7, ['KKKKK', ' DDHD', ' MMMM', '  LL ']),
    ('block', 20, 17, ['KKKK', 'DDHDK', 'MMMMK', ' LLL ']),
    ('block', 22, 7, ['AA']), ('block', 23, 8, ['AA'])])
# Murasakibara: olhos semicerrados roxos (eram pretos): pálpebra, íris roxo-escuro com brilho, lilás embaixo, branco nos cantos
REV['Atsushi Murasakibara (Kuroko no Basket, chibi, cartão)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'D15', 'M': 'D7', 'L': 'D18', 'E': 'E1'}, ops=[
    ('map', 17, 19, 12, 12, {'G14': 'D21'}), ('map', 19, 20, 12, 13, {'G14': 'E1'}),          # a mecha entre os olhos era caramelo (parecia mancha marrom): roxo como o cabelo
    ('block', 19, 7, ['KKKKK']), ('block', 20, 8, ['HDDW', 'MLLW']),
    ('block', 21, 16, ['KKKKKK']), ('block', 22, 17, ['KHDDW', ' MLLE'])])          # brilho em cima à esquerda nos dois (como na arte)
# Midorima: armação dos óculos preta e contínua (estava em M9, parecia mancha), olho esquerdo verde com brilho, verde-claro embaixo no direito
REV['Shintaro Midorima (Kuroko no Basket, chibi, bola)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'B15', 'M': 'B5', 'L': 'B13'}, ops=[
    ('map', 15, 18, 12, 16, {'M9': 'E11'}),
    ('block', 16, 11, ['K']), ('block', 17, 8, ['KDMHW']),
    ('block', 18, 8, ['K']), ('block', 18, 12, ['KK']),
    ('block', 17, 13, ['KKKK']), ('block', 17, 20, ['K']),
    ('block', 16, 18, ['ML'])])

# ---- Hibari: olhos cinza-azulados sob a pálpebra pesada (eram preto com 1 conta cinza): branco dos lados, íris escura com brilho, cinza embaixo
REV['Kyoya Hibari (Katekyo Hitman Reborn, chibi)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'H6', 'M': 'H5', 'L': 'H4', 'E': 'E11'}, ops=[
    ('map', 16, 17, 5, 18, {'M9': 'E11'}), ('block', 18, 16, ['K']), ('block', 18, 20, ['K']),
    ('block', 19, 6, ['KDHDK', 'WMLMW']), ('block', 19, 15, ['KKDHDK', ' WMLMW'])])          # modelo da Rei: o branco embaixo, nunca colado no brilho
# ---- Garoto loiro de bandana: íris ciano com o topo mais escuro e um brilho acima da pupila nos dois olhos; pálpebra do olho esquerdo preta
REV['Garoto loiro de bandana 01 (chibi)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'C11', 'M': 'C17', 'G': 'H3', 'L': 'C13'}, ops=[
    ('block', 24, 19, ['G DDD']), ('block', 25, 21, ['H']),
    ('block', 27, 9, ['KK']), ('block', 28, 11, ['DD']), ('block', 30, 11, ['L'])])
# ---- Leorio (sobre o molde que ele ajustou): sobrancelhas bravas, olhos com pálpebra, íris castanho-escura e brilho (eram blocos pretos), aro dos óculos inteiro
REV['Leorio Paradinight (Hunter x Hunter, chibi)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'E': 'E14'}, ops=[
    ('block', 13, 7, ['KK']), ('block', 14, 9, ['KK']),
    ('block', 15, 15, ['KK']), ('block', 14, 17, ['KK']),
    ('block', 17, 8, ['KDHD']),
    ('block', 16, 18, ['K']), ('block', 17, 16, ['DHD']),
    ('block', 19, 15, ['K']), ('block', 20, 16, ['K']), ('block', 18, 19, ['E'])])
# ---- Máquina Vigia: as 3 lentes azuis redondas e iguais (cruz de 3x3 com o miolo claro), como na arte
REV['Máquina Vigia (Horizon)'] = dict(leg={'K': 'H7', 'M': 'C7', 'L': 'C13'}, ops=[
    ('block', 9, 21, ['K'] ), ('block', 11, 21, ['K']), ('block', 13, 18, ['K']), ('block', 13, 22, ['K']),
    ('block', 9, 21, [' M ', 'MLM', ' M ']),
    ('block', 11, 18, [' M ', 'MLM', ' M ']),
    ('block', 13, 20, [' M ', 'MLM', ' M '])])

# ---- os 3 chibis da folha de "deitados" (ele os pôs de pé no app; as coordenadas são do molde GIRADO dele; posições medidas na arte girada igual)
# loiro de óculos: íris amarela com o brilho no lugar da pupila (era laranja/preto), branco do lado de fora; o esquerdo (3/4) com 2 contas de íris
REV['Chibi loiro de óculos e jaleco (folha, deitado)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'M': 'A4', 'L': 'A3'}, ops=[
    ('block', 14, 22, ['MHM']), ('block', 15, 21, ['WMLM']),
    ('block', 16, 15, ['WMH']), ('block', 17, 15, ['WML'])])
# cabelo branco: íris vermelha de 3x2 com brilho no direito; o esquerdo (3/4) com 2 de largura, branco à esquerda (era quase todo preto)
REV['Chibi de cabelo branco e olhos vermelhos (folha, deitado)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F5', 'L': 'F12'}, ops=[
    ('block', 14, 15, ['DHD']), ('block', 15, 15, ['MML']),
    ('block', 15, 9, ['DH']), ('block', 16, 8, ['WMM']), ('block', 17, 9, ['LL'])])
# cabelo vermelho: olhos verdes com o topo escuro, brilho no meio e verde-claro embaixo (o direito estava todo claro, sem pupila)
REV['Chibi de cabelo vermelho e olhos verdes (folha, deitado)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'B15', 'M': 'B5', 'L': 'B13', 'E': 'E8'}, ops=[
    ('block', 14, 13, ['K']), ('block', 15, 13, ['DD']), ('block', 16, 13, ['MHD']), ('block', 17, 13, ['LL']),
    ('block', 15, 20, ['DD']), ('block', 16, 20, ['MHM']), ('block', 17, 20, ['LLE'])])

# ---- Momo (folha): olhos com íris coral (era vermelho F13), pupila escura em cima, brilho branco embaixo como na arte, branco do olho em H2 (era H1, a conta transparente);
# a boca aberta grande (salmão) tinha escapado da limpeza da remessa: sai (regra 4.8, sem boca aberta em ilustração)
REV['Momo Ayase (Dan Da Dan, chibi, folha)'] = dict(leg={'K': 'H7', 'H': 'H2', 'W': 'H2', 'D': 'G8', 'M': 'F3', 'E': 'E1'}, ops=[
    ('map', 16, 21, 18, 23, {'A12': 'E11', 'G7': 'E11', 'M9': 'E11'}),
    ('block', 12, 17, ['D']), ('block', 13, 15, ['WWM DM']), ('block', 14, 15, ['WWMMH']), ('block', 15, 15, ['E']),
    ('block', 15, 25, ['DM']), ('block', 16, 25, ['MH'])])
# ---- Okarun transformado (folha), "ajustar um pouquinho da coloração": manchas caramelo (M9) no rosto eram o aro fino dos óculos misturado com a pele -> cinza H4 no aro,
# branco no vidro, pele ou rosa onde a arte é pele; manchas cinza-escuras (H5) no cabelo branco -> a sombra lilás clara da arte (H3/H4); pontos cinza no branco -> branco;
# olhos laranja com brilho (estavam quase sumidos atrás dos óculos)
_OKA_HAIR = {(4, 7): 'H2', (4, 27): 'H2', (6, 6): 'H2', (7, 9): 'H2', (8, 10): 'H2', (8, 12): 'H2', (8, 14): 'H2', (8, 22): 'H4', (10, 21): 'H4', (10, 23): 'H2', (10, 24): 'H2',
             (12, 16): 'H4', (13, 10): 'H3', (13, 12): 'H4', (13, 13): 'H4', (13, 14): 'H4', (13, 24): 'H2', (14, 12): 'H3', (14, 13): 'H4', (15, 12): 'H3', (15, 27): 'H3', (15, 28): 'H4',
             (15, 29): 'H4', (15, 30): 'H3', (15, 31): 'H3', (15, 32): 'H3', (15, 33): 'H4', (16, 22): 'H2', (17, 32): 'H4', (17, 33): 'H4', (18, 1): 'H3', (18, 26): 'H2', (19, 28): 'H3',
             (19, 33): 'H4', (20, 30): 'H4'}
_OKA_FACE = {(19, 16): 'E11', (19, 17): 'H4', (20, 16): 'H4', (21, 26): 'E11', (23, 25): 'H4', (24, 7): 'E8', (25, 15): 'H2', (25, 16): 'H2', (25, 22): 'H2', (25, 23): 'H3',
             (26, 14): 'H4', (26, 16): 'H2', (26, 19): 'H2', (26, 20): 'H4', (26, 21): 'H4', (26, 22): 'H4', (27, 14): 'E11', (27, 16): 'H4', (27, 22): 'F14', (28, 12): 'H2',
             (28, 17): 'H4', (28, 18): 'H2', (28, 22): 'E7', (29, 19): 'E11'}
REV['Okarun transformado (Dan Da Dan, chibi, folha)'] = dict(leg={'K': 'H7', 'H': 'H2', 'D': 'F10', 'M': 'A7', 'L': 'E14'}, ops=[
    ('set', _OKA_HAIR), ('set', _OKA_FACE),
    ('block', 23, 21, ['HD']), ('block', 24, 21, ['ML']),
    ('block', 23, 13, ['K']), ('block', 24, 12, ['HD']), ('block', 25, 12, ['ML'])])
# ---- Kallen: embaixo da íris o degradê azul da arte (azul-petróleo -> azul-claro) no lugar do cinza H5 e do branco solto; branco do canto de dentro dos olhos; contorno de baixo do direito
REV['Kallen Kozuki (Code Geass, chibi, traje de piloto)'] = dict(leg={'K': 'H7', 'W': 'H2', 'M': 'C11', 'L': 'C3'}, ops=[
    ('block', 19, 13, ['M LW']), ('block', 19, 23, ['WM LK']), ('block', 20, 25, ['K'])])
