# Como contribuir

Obrigado por querer ajudar. Este site é o material que estou usando para me preparar para a CKA, e toda correção ajuda quem estuda por ele.

## Jeitos de ajudar

- **Achou um erro?** Abra uma [issue](https://github.com/crisz-source/help-ppl-cka/issues) com o link da página, o que está escrito e o que você viu acontecer. Se possível, informe a versão do Kubernetes (`kubectl version`) e cole a saída do terminal.
- **Comando com saída diferente na sua versão?** Abra uma issue com a saída real. Isso é muito útil: o site mostra o que acontece de verdade, e versões novas mudam mensagens.
- **Sugestão de tópico ou de pegadinha?** Abra uma issue antes de escrever, para combinarmos onde ela entra.
- **Quer corrigir você mesmo?** Mande um pull request (veja abaixo).

## Regras do conteúdo

1. **Saída real, nunca inventada.** Todo bloco de saída precisa ter sido copiado de um terminal. Informe a versão e o ambiente onde rodou (kubeadm, kind, Killercoda…). Se precisar cortar, corte linhas inteiras e diga na página que cortou; não encurte uma linha no meio.
2. **Escreva só em `docs/`.** Os layouts são gerados a partir dessa pasta. Página nova também entra no `nav` do `mkdocs.yml`.
3. **Siga o formato das páginas:** o que é → como funciona por dentro → comandos essenciais → YAML de referência → onde achar na documentação oficial → pegadinhas → exercício no estilo da prova.
4. **Saída de comando vai em bloco ```` ```console ````**, com o prompt `$ ` antes de cada comando.
5. **Português do Brasil, direto e técnico.** Termos do Kubernetes ficam em inglês (Pod, Deployment, taint).
6. **Fonte oficial:** aponte onde o assunto está em kubernetes.io/docs, a documentação permitida na prova.

## Pull request, passo a passo

1. Faça um fork do repositório e crie uma branch (`git checkout -b corrige-dns`).
2. Edite os arquivos em `docs/`.
3. Confira se o site compila sem aviso:

   ```bash
   pip install -r requirements.txt
   mkdocs build --strict
   ```

   Para ver o resultado no navegador, use `mkdocs serve` e abra <http://127.0.0.1:8000>.

4. Abra o pull request explicando o que mudou e onde você testou (versão e ambiente).

## Licença

Ao contribuir, você concorda que sua contribuição seja distribuída sob a [licença MIT](LICENSE) do projeto.
