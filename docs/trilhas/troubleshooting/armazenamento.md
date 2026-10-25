# Armazenamento não funciona

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 3 cenários

O PVC fica `Pending` ou o Pod fica preso em `ContainerCreating`. O primeiro comando é `kubectl describe pvc <nome>` (ou `describe pod`, se o problema for o volume no Pod). No laboratório (kind), a StorageClass padrão é `standard`, com o provisionador `rancher.io/local-path` e `WaitForFirstConsumer`.

```console
$ kubectl get sc
NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
standard (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  10m
```

**`Pending` nem sempre é erro.** Com `WaitForFirstConsumer`, o PVC espera um Pod que o use. O evento diz isso:

```console
Normal  WaitForFirstConsumer  persistentvolume-controller  waiting for first consumer to be created before binding
```

**Quase nada num PVC muda depois de criado.** Trocar `storageClassName` ou `accessModes` com `patch` é recusado (saída real):

```console
The PersistentVolumeClaim "pvc-classe" is invalid: spec: Forbidden: spec is immutable after creation except resources.requests and volumeAttributesClassName for bound claims
```

A correção é apagar e recriar o PVC (`kubectl replace --force -f pvc.yaml`).

## StorageClass que não existe

1. **Sintoma:** PVC `Pending`.
2. **Primeiro comando:** `kubectl describe pvc pvc-classe`
3. **Evidência:**

    ```console
    Warning  ProvisioningFailed  persistentvolume-controller  storageclass.storage.k8s.io "rapido" not found
    ```

4. **Causas prováveis:** nome da classe digitado errado, ou classe de outro cluster. Confira com `kubectl get sc`.
5. **Correção:** recriar o PVC com uma classe existente (aqui, `standard`).
6. **Validar:** o PVC passa a `WaitForFirstConsumer` e liga (`Bound`) quando um Pod o usa.

## accessMode que o provisionador não suporta

1. **Sintoma:** PVC `Pending` e o Pod que o usa também `Pending`.
2. **Primeiro comando:** `kubectl describe pvc pvc-rwx`
3. **Evidência:**

    ```console
    Warning  ProvisioningFailed  rancher.io/local-path_...  failed to provision volume with StorageClass "standard": NodePath only supports ReadWriteOnce and ReadWriteOncePod (1.22+) access modes
    ```

4. **Causas prováveis:** `ReadWriteMany` num armazenamento local, que só serve um nó. Com PV criado à mão, o equivalente é o PV não oferecer o modo pedido: o PVC não liga.
5. **Correção:** recriar o PVC com `ReadWriteOnce`, ou usar uma classe que suporte `ReadWriteMany`, conforme o enunciado.
6. **Validar:** `kubectl get pvc pvc-rwx` → `Bound`, `RWO`; o Pod foi para `Running` sem ser recriado.

## hostPath que não existe

1. **Sintoma:** Pod em `ContainerCreating`.
2. **Primeiro comando:** `kubectl describe pod hostpath`
3. **Evidência:**

    ```console
    Warning  FailedMount  kubelet  MountVolume.SetUp failed for volume "d" : hostPath type check failed: /srv/dados is not a directory
    ```

4. **Causas prováveis:** `type: Directory` exige que o diretório já exista no nó onde o Pod caiu. Num cluster com vários workers, ele pode existir em um nó e não no outro.
5. **Correção:** criar o diretório no nó, ou trocar para `type: DirectoryOrCreate` e recriar o Pod (`kubectl replace --force -f`).
6. **Validar:** `kubectl get pod hostpath` → `Running`.

Mais casos de PV e PVC (classe vazia, tamanho maior que o PV, `claimRef` de PV `Released`) estão em [PV e PVC](../../04-storage/pv-pvc.md) e [reclaimPolicy](../../04-storage/reclaim-policy.md).

## Reproduzir

??? example "YAML dos três cenários"

    ```yaml
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata: {name: pvc-classe}
    spec: {storageClassName: rapido, accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
    ---
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata: {name: pvc-rwx}
    spec: {accessModes: [ReadWriteMany], resources: {requests: {storage: 1Gi}}}
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: usa-rwx}
    spec:
      containers: [{name: c, image: nginx:1.27, volumeMounts: [{name: d, mountPath: /d}]}]
      volumes: [{name: d, persistentVolumeClaim: {claimName: pvc-rwx}}]
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: hostpath}
    spec:
      containers: [{name: c, image: nginx:1.27, volumeMounts: [{name: d, mountPath: /d}]}]
      volumes: [{name: d, hostPath: {path: /srv/dados, type: Directory}}]
    ```
