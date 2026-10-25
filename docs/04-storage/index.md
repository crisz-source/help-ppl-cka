# 4. Storage (10%)

O menor domínio da prova, mas com questões rápidas de pontuar: **onde os dados de um Pod ficam e quanto tempo sobrevivem**. Do volume que morre com o Pod (`emptyDir`) ao disco persistente pedido por PVC e criado sob demanda por uma StorageClass.

## Itens do currículo e onde estão

| Item do currículo | Página |
|---|---|
| Implement storage classes and dynamic volume provisioning | [StorageClass e provisionamento dinâmico](storageclass.md) |
| Configure volume types, access modes and reclaim policies | [Volumes em Pods: emptyDir e hostPath](volumes-emptydir-hostpath.md) · [PV e PVC](pv-pvc.md) (accessModes) · [reclaimPolicy](reclaim-policy.md) |
| Manage persistent volumes and persistent volume claims | [PV e PVC](pv-pvc.md) · [Expansão de PVC](expansao-pvc.md) |

Itens conferidos com o currículo oficial `CKA_Curriculum_v1.37.pdf` (<https://github.com/cncf/curriculum>) em 2026-10-25.

## Ordem sugerida de estudo

1. **Volumes em Pods (emptyDir, hostPath)**: o conceito de volume sem nenhuma outra peça.
2. **PV e PVC**: separar quem oferece disco de quem pede; binding e accessModes.
3. **StorageClass**: o PV criado sob demanda, e a classe padrão.
4. **reclaimPolicy**: o que acontece com os dados quando o PVC some.
5. **Expansão de PVC**: aumentar sem recriar.

## Quanto tempo o dado vive

| Onde o dado está | Sobrevive a restart do container | Sobrevive à remoção do Pod | Sobrevive à remoção do PVC |
|---|---|---|---|
| Sistema de arquivos do container | Não | Não | — |
| `emptyDir` | Sim | Não | — |
| `hostPath` | Sim | Sim (só naquele nó) | — |
| PVC → PV com `Delete` | Sim | Sim | **Não** |
| PVC → PV com `Retain` | Sim | Sim | **Sim** |
