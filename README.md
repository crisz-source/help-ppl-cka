# help-ppl-cka

Estudo em público para a certificação **CKA (Certified Kubernetes Administrator)**, em português do Brasil. Gratuito e open source.

O mesmo conteúdo (`docs/`) é publicado em dois layouts:

| Layout | Ferramenta | Endereço |
|---|---|---|
| Clássico | MkDocs Material | <https://crisz-source.github.io/help-ppl-cka/> |
| Interativo (terminal animado, progresso de estudo) | Astro Starlight, em `v2/` | <https://crisz-source.github.io/help-ppl-cka/v2/> |

## Rodar localmente

Layout clássico:

```bash
pip install -r requirements.txt
mkdocs serve
```

Abra <http://127.0.0.1:8000>.

Layout interativo (Node 24):

```bash
cd v2
npm ci
npm run dev
```

Abra <http://localhost:4321/help-ppl-cka/v2/>.

## Estrutura

- `docs/<numero-dominio>-<nome-dominio>/<topico>.md`: uma página por tópico, organizadas pelos domínios do currículo. **É a única fonte do conteúdo**: os dois layouts são gerados a partir daqui.
- `mkdocs.yml`: configuração do layout clássico. O `nav` também define o menu do layout interativo.
- `v2/`: layout interativo. `v2/scripts/sync-docs.mjs` copia `docs/` antes de cada build e converte a sintaxe do MkDocs Material (avisos `!!!`, soluções `???`, Mermaid, links, imagens de `docs/assets/`). Não edite `v2/src/content/docs/`: ele é gerado.
- `docs/assets/diagramas/`: os diagramas das páginas (SVG). Não edite à mão: são exportados de `drawio/`.
- `drawio/`: fonte dos diagramas das páginas (draw.io, ícones oficiais do Kubernetes) e os scripts para gerar e exportar. Veja `drawio/README.md`.
- `excalidraw/`: diagramas editáveis (extensão Excalidraw do VS Code).

## Escrevendo conteúdo

Escreva só em `docs/`, como sempre. Para mostrar a saída de um comando, use um bloco ```` ```console ```` com o prompt `$ `: o layout clássico mostra o bloco como código, e o interativo digita o comando e mostra a saída em seguida.

```console
$ kubectl get svc web-svc
NAME      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
web-svc   ClusterIP   10.96.45.12    <none>        80/TCP    5m
```
