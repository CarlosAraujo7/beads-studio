# Bead Studio

Editor local de moldes para contas de fusão (hama/Pindou), em português do Brasil: desenhe, escolha um molde do catálogo, converta uma imagem em contas, veja quantas contas de cada cor precisa e monte linha por linha.

**Usar online:** https://carlosaraujo7.github.io/beads-studio/

Não precisa instalar nada. O site é só HTML + JavaScript (`index.html` e o catálogo `templates.js`); também funciona abrindo o `index.html` com duplo clique. Seu desenho, seus ajustes e seus moldes próprios ficam guardados **no seu navegador** (nada é enviado a servidor nenhum).

## O que tem aqui

| Caminho | O que é |
|---|---|
| `index.html` | O app inteiro (sem build) |
| `templates.js` | O catálogo de moldes (gerado por `tools/add_templates.py` ou pelo botão "Gravar no catálogo" do app) |
| `tools/` | Scripts em Python que convertem imagens em moldes e os dados-fonte (`tools/data`) |
| `CLAUDE.md` | Descrição detalhada do projeto e do processo de conversão |

As imagens originais (pastas `remessa N`) não estão no repositório.
