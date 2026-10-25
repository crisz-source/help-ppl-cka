# Estudo CKA em público

**CKA em português: comandos, YAML, troubleshooting e prática.**

Você já conhece Linux e containers? [Comece pelo Domínio 1](01-cluster-architecture/index.md) e avance pelos 29 tópicos em ordem.

Currículo conferido em **outubro de 2026** (CKA v1.37) · Kubernetes nos laboratórios: **v1.37**

## Escolha uma trilha

<div class="grid cards" markdown>

-   **[Começar do zero](trilhas/iniciante.md)**

    Fundamentos de Kubernetes e preparação gradual para a CKA.

    *12 passos, cada um com uma tarefa prática*

-   **[Revisão rápida](trilhas/revisao-rapida.md)**

    Comandos, sintaxe e pegadinhas para revisar antes da prova.

    *Um cartão por tópico, pelo peso na prova*

-   **[Treinar troubleshooting](trilhas/troubleshooting/index.md)**

    Diagnóstico de Pods, nós, rede, storage e control plane.

    *23 cenários reproduzidos, por sintoma*

</div>

## Quem escreve e por que confiar

Sou o **Cristhian Ramos** e trabalho como **DevOps**. Este site é a minha preparação para a CKA feita em público: escrevo cada página enquanto estudo e organizo o material para ajudar quem está no mesmo caminho.

O que dá para conferir:

- **Saídas reais.** Todo bloco de saída foi copiado do terminal de um cluster kubeadm **v1.37.1** (1 control plane + 2 workers). Quando uma linha é cortada, a página avisa.
- **Erros reais.** As pegadinhas foram provocadas no lab, com a mensagem de erro que o Kubernetes devolve. Ao testar tudo numa VM depois do cluster local (kind), oito afirmações se mostraram diferentes e foram corrigidas.
- **Fonte oficial.** Cada página aponta onde o assunto está em kubernetes.io/docs, a documentação permitida na prova, e o conteúdo segue o [currículo oficial da CNCF](https://github.com/cncf/curriculum).
- **Código aberto.** Todo o texto está no [GitHub](https://github.com/crisz-source/help-ppl-cka), sob licença MIT. Achou algo errado ou quer ajudar? Veja [como contribuir](https://github.com/crisz-source/help-ppl-cka/blob/main/CONTRIBUTING.md).

## Para quem é

Profissionais que já conhecem o básico de Linux e containers e querem passar na CKA. É gratuito e open source.

## Como o conteúdo está organizado

Pelos cinco domínios do currículo oficial:

| # | Domínio | Peso |
|---|---|---|
| 1 | [Cluster Architecture, Installation & Configuration](01-cluster-architecture/index.md) | 25% |
| 2 | [Workloads & Scheduling](02-workloads-scheduling/index.md) | 15% |
| 3 | [Services & Networking](03-services-networking/index.md) | 20% |
| 4 | [Storage](04-storage/index.md) | 10% |
| 5 | [Troubleshooting](05-troubleshooting/index.md) | 30% |

Toda página segue o mesmo formato: **o que é → como funciona por dentro → comandos essenciais → YAML de referência → onde achar na documentação oficial → pegadinhas → exercício no estilo da prova**.

## Ambiente de prática

- Lab próprio com **kubeadm**: 1 control plane + 2 workers em VMs Azure (Ubuntu 24.04, containerd 2.2.1, Calico). Criado em **v1.36.5** e atualizado para **v1.37.1** seguindo a própria página de upgrade. Todas as páginas foram testadas nesse cluster em outubro de 2026.
- [Killercoda](https://killercoda.com/) para cenários rápidos e descartáveis.

!!! info "Versões"
    Cada página informa a versão do Kubernetes em que foi revisada. O currículo do CKA muda: confira sempre o [currículo oficial da CNCF](https://github.com/cncf/curriculum).
