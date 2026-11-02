# Prompt para passar a outro agente (Bead Studio)

> Cole o bloco abaixo como primeira mensagem. Ele resume o jeito de trabalhar; o detalhe completo está no `CLAUDE.md` da pasta do projeto.

```
Você vai continuar o projeto "Bead Studio" (editor de moldes para contas de fusão Hama/Pindou), na pasta
C:\Users\vinic\OneDrive\Documentos\Hama beads  (repositório https://github.com/CarlosAraujo7/beads-studio, branch main).
Responda SEMPRE em pt-BR. O dono é um hobbista, direto, que confere tudo OLHANDO AS IMAGENS: nunca diga que
algo ficou bom sem ter renderizado e olhado (e diga com franqueza o que ficou fraco).

ANTES DE QUALQUER COISA
1. Leia o CLAUDE.md inteiro (é o manual: formato do templates.js, pipeline de conversão, regras do usuário,
   histórico de cada remessa e as lições de cada correção). Leia também a memória do agente se existir.
2. O catálogo (templates.js) é do USUÁRIO. Ele exclui moldes e edita desenhos no app o tempo todo. Por isso:
   - antes de qualquer lote, compare com o templates.js ATUAL (ids e linhas), nunca com o que você lembra;
   - NUNCA recoloque o que ele excluiu; NUNCA sobrescreva o que ele editou (pule e avise);
   - o catálogo é "definitivo": só acrescente (add_templates.py, sem --replace) ou faça o que ele pedir
     explicitamente, e mexa só nos moldes que ele citou. Duplicata de arte: pergunte antes.
3. Nunca baixe imagens da internet; só as que ele coloca nas pastas "remessa N".
4. Nunca contas soltas (tools/loose.py); nunca faça commit/push sem ele pedir ou aprovar; sem linha de
   co-autor/atribuição do Claude nos commits. Não mate processos em massa.

COMO TRABALHAMOS (o ciclo que funciona)
- Ele manda uma lista de moldes ("esse ficou estranho", "olhos grandes demais", "pernas esquisitas") ou uma
  pasta "remessa N" nova. Você: (a) acha o molde e a imagem de origem (tools/faces_src.py, r*_exfinal.py);
  (b) gera uma FOLHA fonte × molde com a MESMA grade e números de linha/coluna (tools/faces_sheets.py) e OLHA;
  (c) conserta; (d) renderiza antes/depois e OLHA de novo, em zoom (render_flat); (e) só então grava.
- Rosto é o que faz um molde ficar bonito: olhos bem feitos (pálpebra, esclera, íris, pupila, 1 brilho), boca
  discreta. Olho de chibi: no máximo ~4-5 contas de lado, salvo arte de olhos gigantes. Simetria só onde a
  arte é simétrica (espelho completo de rosto com cabelo fica "espelhado"; capacete/olhos sim).
- Antes de converter uma imagem, MEÇA o pixel nativo (autocorrelação do gradiente): sprites pixel-art devem ser
  convertidos no tamanho nativo ou perto de 50; reduzir demais joga o detalhe fora (lição dos chibis de One Piece).
- Regra de tamanho: de toda imagem nova faz-se a versão de 1 placa (≤ 50x50) e, onde ajuda, um irmão
  "Nome (grande)" de 2-4 placas ({"plates": N}).
- Ferramentas principais: tools/illus5.py (convert5: cores lisas, melhor que convert4 para rostos),
  tools/faces_apply.py + faces_fix.py (consertos por molde, com cópia de segurança e proteção contra edições
  do usuário), tools/facetools.py, tools/c5var.py (variantes lado a lado), tools/add_templates.py (acrescentar),
  tools/loose.py (contas soltas). Paleta de 120 cores: BEADPAL=120 em todo comando Python.
- Verificação: node --check templates.js; python tools/loose.py; teste no navegador com um .claude/launch.json
  temporário (python -m http.server 8765), conferir window.TEMPLATES.length e abrir 2-3 moldes, depois
  localStorage.clear(), parar o servidor e apagar a pasta .claude. Suba o carimbo `var b=` do index.html a cada
  mudança do templates.js feita por fora e diga ao usuário para recarregar com Ctrl+F5.
- No fim de cada trabalho: atualize o CLAUDE.md (seção do que foi feito + tabela do §10) e a memória, e
  responda em pt-BR com: o que mudou, o que NÃO mudou e por quê (ex.: ele editou/excluiu), limites honestos,
  e pergunte antes de commitar/dar push.

Seu primeiro passo: ler o CLAUDE.md, rodar `git status` e `git log -5`, conferir quantos moldes o templates.js
tem hoje, e perguntar ao usuário o que ele quer fazer agora.
```
