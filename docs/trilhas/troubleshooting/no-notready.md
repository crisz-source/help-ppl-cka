# Nó NotReady

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 3 cenários

O nó aparece `NotReady` em `kubectl get nodes`. O primeiro comando é `kubectl describe node <nó>`: a condição `Ready` mostra o status e o motivo, e cada causa tem uma assinatura diferente.

| Condição `Ready` | Motivo | Causa |
|---|---|---|
| `Unknown` | `Kubelet stopped posting node status.` | kubelet parado |
| `False` | `container runtime is down` | containerd parado |
| `False` | `container runtime network not ready ... cni plugin not initialized` | CNI sem configuração |

A diferença entre `Unknown` e `False`: com `Unknown`, o kubelet parou de falar com o API server, que não sabe o estado do nó. Com `False`, o kubelet está vivo e **conta** o que está errado.

O passo seguinte é sempre entrar no nó (`ssh <nó>`, depois `sudo -i`). A página [Nó NotReady](../../05-troubleshooting/no-notready.md) do Domínio 5 tem os casos de configuração do kubelet (binário no caminho errado, `cgroupDriver`, certificados) testados no lab.

## kubelet parado

1. **Sintoma:** `cka-worker   NotReady`. No teste, levou cerca de 47 segundos entre parar o kubelet e o nó virar `NotReady`.
2. **Primeiro comando:** `kubectl describe node cka-worker`
3. **Evidência:**

    ```console
    Ready   Unknown   NodeStatusUnknown   Kubelet stopped posting node status.
    ```

    No nó:

    ```console
    $ systemctl is-active kubelet
    inactive
    ```

4. **Causas prováveis:** serviço parado ou desabilitado, ou kubelet que não sobe por erro de configuração (aí o `journalctl -u kubelet` mostra o motivo).
5. **Correção:** `systemctl enable --now kubelet`. O `enable` garante que ele volte depois de um reboot.
6. **Validar:** `kubectl get nodes` (no control plane) → `Ready` em alguns segundos.

## containerd parado

1. **Sintoma:** `NotReady`, mais rápido que no caso do kubelet (cerca de 30 segundos no teste).
2. **Primeiro comando:** `kubectl describe node cka-worker`
3. **Evidência:**

    ```console
    Ready   False   KubeletNotReady   container runtime is down
    ```

    No nó, o `crictl` não conecta e o log do kubelet diz o mesmo:

    ```console
    $ crictl ps
    ... validate CRI v1 runtime API for endpoint "unix:///run/containerd/containerd.sock": ... connect: no such file or directory
    $ journalctl -u kubelet | grep "runtime is down"
    ... "Skipping pod synchronization" err="container runtime is down"
    ```

4. **Causas prováveis:** containerd parado, ou configuração do containerd com erro (o serviço não sobe).
5. **Correção:** `systemctl enable --now containerd`. Se não subir, `journalctl -u containerd` mostra o erro.
6. **Validar:** `kubectl get nodes` → `Ready`.

## CNI sem configuração

1. **Sintoma:** `NotReady`, com kubelet e containerd rodando.
2. **Primeiro comando:** `kubectl describe node cka-worker`
3. **Evidência:**

    ```console
    Ready   False   KubeletNotReady   container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized
    ```

    No nó, `/etc/cni/net.d/` estava vazio.

4. **Causas prováveis:** o Pod do plugin de rede (DaemonSet do CNI em `kube-system`) não roda nesse nó, ou o arquivo de configuração em `/etc/cni/net.d/` foi apagado.
5. **Correção:** conferir o DaemonSet do CNI (`kubectl -n kube-system get ds` e `get pods -o wide`) e fazer o Pod dele voltar a rodar no nó. Normalmente é o próprio plugin que grava o arquivo em `/etc/cni/net.d/`.
6. **Validar:** com o Pod do CNI rodando de novo, o arquivo voltou (`10-kindnet.conflist`) e o nó voltou a `Ready`.

## Outras causas

Disco cheio e falta de memória no nó aparecem como condições próprias (`DiskPressure`, `MemoryPressure`) no mesmo `kubectl describe node`. Não foram reproduzidas aqui, porque provocá-las no kind afeta a máquina inteira.

## Reproduzir

No kind, o nó é um container com systemd:

```bash
docker exec cka-worker systemctl stop kubelet          # depois: systemctl enable --now kubelet
docker exec cka-worker systemctl stop containerd       # depois: systemctl start containerd
```

Para o CNI, o teste tirou o DaemonSet `kindnet` do nó (um `nodeSelector` que nenhum nó tem) e moveu o arquivo de `/etc/cni/net.d/`. Desfazer o `nodeSelector` fez o kindnet voltar e regravar o arquivo.
