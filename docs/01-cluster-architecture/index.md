# 1. Cluster Architecture, Installation & Configuration (25%)

Um quarto da prova. É o domínio de quem **opera** o cluster: quem pode fazer o quê, como instalar e atualizar, como tirar um nó de serviço e como instalar componentes com Helm e Kustomize.

## Itens do currículo e onde estão

| Item do currículo | Página |
|---|---|
| Manage role based access control (RBAC) | [RBAC](rbac.md) |
| Manage the lifecycle of Kubernetes clusters | [Upgrade com kubeadm](upgrade-kubeadm.md), [Drain, cordon e uncordon](drain-cordon-uncordon.md) |
| Use Helm and Kustomize to install cluster components | [Helm e Kustomize](helm-kustomize.md) |
| *(fora da lista explícita atual, ver aviso na página)* | [Backup e restore do etcd](etcd-backup-restore.md) |
| Create and manage Kubernetes clusters using kubeadm | [Adicionar um nó com kubeadm join](kubeadm-join.md), [Certificados com kubeadm](kubeadm-certs.md) |

Itens conferidos com o currículo oficial `CKA_Curriculum_v1.37.pdf` (<https://github.com/cncf/curriculum>) em 2026-10-25.

## Ordem sugerida de estudo

1. **RBAC**: aparece em quase toda prova e é rápido de pontuar.
2. **Drain/cordon/uncordon**: pré-requisito do upgrade.
3. **Upgrade com kubeadm**: tarefa longa, vale treinar até virar rotina.
4. **kubeadm join**: dois comandos; o que pesa é reconhecer os erros (token vencido, hash errado).
5. **Certificados com kubeadm**: complementa o upgrade, que renova os certificados, e é base para Troubleshooting do control plane.
6. **Helm e Kustomize**: comandos curtos, fáceis de errar por detalhe.
7. **Backup e restore do etcd**: mesmo fora da lista explícita, ensina a anatomia do control plane e ajuda no Troubleshooting.
