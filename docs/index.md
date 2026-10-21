# Estudo CKA em público

Este site documenta minha preparação para a **CKA (Certified Kubernetes Administrator)** e organiza o conteúdo para ajudar quem está no mesmo caminho. É gratuito e open source.

## Para quem é

Profissionais que já conhecem o básico de Linux e containers e querem passar no CKA.

## Como o conteúdo está organizado

Pelos cinco domínios do currículo oficial:

| # | Domínio | Peso |
|---|---|---|
| 1 | Cluster Architecture, Installation & Configuration | 25% |
| 2 | Workloads & Scheduling | 15% |
| 3 | Services & Networking | 20% |
| 4 | Storage | 10% |
| 5 | Troubleshooting | 30% |

Toda página segue o mesmo formato: **o que é → como funciona por dentro → comandos essenciais → YAML de referência → onde achar na documentação oficial → pegadinhas → exercício no estilo da prova**.

## Ambiente de prática

- Lab próprio com **kubeadm**: 1 control plane + 2 workers em VMs Azure.
- [Killercoda](https://killercoda.com/) para cenários rápidos e descartáveis.

!!! info "Versões"
    Cada página informa a versão do Kubernetes em que foi revisada. O currículo do CKA muda: confira sempre o [currículo oficial da CNCF](https://github.com/cncf/curriculum).
