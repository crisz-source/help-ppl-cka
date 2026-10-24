# Diagramas (draw.io)

Fonte dos diagramas das páginas do site. Cada `.drawio` vira um SVG em `docs/assets/diagramas/`,
que as duas versões do site (MkDocs e `/v2/`) mostram como imagem.

| Arquivo | Para quê |
|---|---|
| `NN-<página>.drawio` | Um diagrama por página. `NN` é o domínio do currículo; `visao-geral` é o índice do domínio |
| `gerar_cka_drawio.py` | Gera os `.drawio` com os ícones oficiais do Kubernetes (stencil do draw.io) |
| `exportar_svg.py` | Exporta para SVG e ajusta para a web: sem PNG de reserva, sempre claro, fontes com alternativa |

## Mudar um diagrama

1. Edite o `.drawio` no draw.io, ou a função dele em `gerar_cka_drawio.py` e regenere:
   `python gerar_cka_drawio.py . 03-dns`. O gerador **sobrescreve** o `.drawio`; se ele foi
   editado à mão, mexa só no arquivo.
2. Exporte para o site (precisa do draw.io desktop instalado):
   `python exportar_svg.py ../docs/assets/diagramas 03-dns.drawio`
3. Confira com `mkdocs build --strict` e `npm run build` em `v2/`.
