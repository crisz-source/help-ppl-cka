# Agendamento: Pod não vai para nenhum nó

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 4 cenários

O Pod fica `Pending` e o scheduler explica por quê no evento `FailedScheduling`. A mensagem tem sempre o mesmo formato: **quantos nós existem** e **o motivo de cada grupo de nós ter sido descartado**.

```console
0/2 nodes are available: 1 node(s) didn't match Pod's node affinity/selector, 1 node(s) had untolerated taint(s).
```

Leia como: "dos 2 nós, 1 foi descartado pelo seletor e 1 pelo taint". No laboratório (kind), o nó `cka-control-plane` tem o taint padrão do control plane, por isso ele aparece como `untolerated taint` em quase todas as mensagens.

O primeiro comando é sempre `kubectl describe pod <nome>`. Recursos insuficientes (`Insufficient cpu`) estão em [Pod não inicia](pod-nao-inicia.md#pending-recursos-insuficientes).

**Depois da correção, o Pod `Pending` é agendado sozinho.** Não é preciso recriar: o scheduler tenta de novo. Nos quatro cenários abaixo, o Pod foi para `Running` sem nenhum `delete`.

## nodeSelector sem nó correspondente

1. **Sintoma:** `Pending`.
2. **Primeiro comando:** `kubectl describe pod seletor`
3. **Evidência:**

    ```console
    Warning  FailedScheduling  default-scheduler  0/2 nodes are available: 1 node(s) didn't match Pod's node affinity/selector, 1 node(s) had untolerated taint(s).
    ```

4. **Causas prováveis:** nenhum nó tem o label pedido (`disco=ssd`), ou o label foi digitado diferente. Confira com `kubectl get nodes --show-labels`.
5. **Correção:** rotular o nó certo (`kubectl label node cka-worker disco=ssd`) ou corrigir o seletor, conforme o enunciado.
6. **Validar:** `kubectl get pod seletor -o wide` → `Running` no `cka-worker`.

## Taint sem toleration

1. **Sintoma:** `Pending`.
2. **Primeiro comando:** `kubectl describe pod taint`
3. **Evidência:** todos os nós descartados por taint:

    ```console
    Warning  FailedScheduling  default-scheduler  0/2 nodes are available: 2 node(s) had untolerated taint(s).
    ```

    O taint aplicado no worker era `manutencao=sim:NoSchedule`; para ver os taints de um nó, use `kubectl describe node <nó> | grep Taints`.

4. **Causas prováveis:** o nó recebeu um taint e o Pod não tem a toleration correspondente.
5. **Correção:** acrescentar a toleration ao Pod, ou remover o taint (`kubectl taint nodes cka-worker manutencao=sim:NoSchedule-`), conforme o enunciado.
6. **Validar:** depois de remover o taint, o Pod foi para `Running` sozinho.

## Nó com cordon

1. **Sintoma:** `Pending`, e o nó aparece como `Ready,SchedulingDisabled`.
2. **Primeiro comando:** `kubectl describe pod cordon` e `kubectl get nodes`
3. **Evidência:**

    ```console
    Warning  FailedScheduling  default-scheduler  0/2 nodes are available: 1 node(s) had untolerated taint(s), 1 node(s) were unschedulable.
    ```

    `were unschedulable` = cordon.

4. **Causas prováveis:** alguém fez `kubectl cordon` ou `kubectl drain` e esqueceu o `uncordon`.
5. **Correção:** `kubectl uncordon cka-worker`
6. **Validar:** `kubectl get nodes` volta a `Ready`, e o Pod vai para `Running`.

## PVC que não existe

1. **Sintoma:** `Pending`.
2. **Primeiro comando:** `kubectl describe pod sempvc`
3. **Evidência:**

    ```console
    Warning  FailedScheduling  default-scheduler  0/2 nodes are available: persistentvolumeclaim "dados-app" not found. not found
    ```

4. **Causas prováveis:** o `claimName` não bate com nenhum PVC do namespace (às vezes é o nome do PV no lugar do PVC), ou o PVC foi criado em outro namespace.
5. **Correção:** criar o PVC com esse nome no namespace do Pod, ou corrigir o `claimName` (recriando o Pod).
6. **Validar:** com o PVC criado, o Pod foi para `Running` sozinho.

## Reproduzir

```bash
kubectl taint nodes cka-worker manutencao=sim:NoSchedule                       # depois: mesmo comando com - no fim
kubectl run seletor --image=nginx:1.27 --overrides='{"spec":{"nodeSelector":{"disco":"ssd"}}}'
kubectl cordon cka-worker                                                      # depois: kubectl uncordon cka-worker
```

??? example "Pod com PVC inexistente"

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata: {name: sempvc}
    spec:
      containers: [{name: c, image: nginx:1.27, volumeMounts: [{name: d, mountPath: /d}]}]
      volumes: [{name: d, persistentVolumeClaim: {claimName: dados-app}}]
    ```
