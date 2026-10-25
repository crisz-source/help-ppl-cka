"""Hook do MkDocs: tira da busca a linha "Versão do Kubernetes · Última revisão" do topo das páginas.

Sem isso, o trecho mostrado em quase todo resultado da busca é essa linha, igual em todas as páginas,
e no celular ela ocupa o espaço do texto que interessa.
"""
import re

LINHA_DE_VERSAO = re.compile(r"<blockquote>(\s*<p><strong>Versão do Kubernetes:)")


def on_page_content(html, **kwargs):
    return LINHA_DE_VERSAO.sub(r"<blockquote data-search-exclude>\1", html, count=1)
