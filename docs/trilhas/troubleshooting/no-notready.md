# Nó NotReady

> **Versão do Kubernetes:** v1.37 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 3 cenários

O nó aparece `NotReady` em `kubectl get nodes`. O primeiro comando é `kubectl describe node <nó>`: a condição `Ready` mostra o status e o motivo, e cada causa tem uma assinatura diferente.

| Condição `Ready` | Motivo | Causa |
|---|---|---|
| `Unknown` | `Kubelet stopped posting node status.` | kubelet parado |
| `False` | `container runtime is down` | containerd parado |
| `False` | `container runtime network not ready ... cni plugin not initialized` | CNI sem configuração |

A diferença entre `Unknown` e `False`: com `Unknown`, o kubelet parou de falar com o API server, que não sabe o estado do nó. Com `False`, o kubelet está vivo e **conta** o que está errado.

O passo seguinte é sempre entrar no nó (`ssh <nó>`, depois `sudo -i`). A página [Nó NotReady](../../05-troubleshooting/no-notready.md) do Domínio 5 tem os outros casos testados no lab (porta errada no `kubelet.conf`, swap ligado, `cgroupDriver`).

Os três cenários foram feitos no lab (VMs Azure, kubeadm v1.37.1, containerd 2.2.1, Calico): `w1` para kubelet e containerd, `w2` para o CNI.

## kubelet parado

1. **Sintoma:** `w1   NotReady`. No teste, cerca de 42 segundos entre parar o kubelet e o nó virar `NotReady`.
2. **Primeiro comando:** `kubectl describe node w1`
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
2. **Primeiro comando:** `kubectl describe node w1`
3. **Evidência:**

    ```console
    Ready   False   KubeletNotReady   container runtime is down
    ```

    No nó, o `crictl` não conecta:

    ```console
    $ crictl ps
    time="2026-10-25T09:59:59Z" level=fatal msg="validate service connection: validate CRI v1 runtime API for endpoint \"unix:///run/containerd/containerd.sock\": rpc error: code = Unavailable desc = connection error: desc = \"transport: Error while dialing: dial unix /run/containerd/containerd.sock: connect: no such file or directory\""
    ```

4. **Causas prováveis:** containerd parado, ou configuração do containerd com erro (o serviço não sobe).
5. **Correção:** `systemctl enable --now containerd`. Se não subir, `journalctl -u containerd` mostra o erro.
6. **Validar:** `kubectl get nodes` → `Ready`.

## CNI sem configuração

1. **Sintoma:** `NotReady`, com kubelet e containerd rodando.
2. **Primeiro comando:** `kubectl describe node w2`
3. **Evidência:**

    ```console
    Ready   False   KubeletNotReady   container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized
    ```

    No nó, `/etc/cni/net.d/` estava vazio.

4. **Causas prováveis:** o Pod do plugin de rede (DaemonSet do CNI em `kube-system`) não roda nesse nó, ou o arquivo de configuração em `/etc/cni/net.d/` foi apagado.
5. **Correção:** conferir o DaemonSet do CNI (`kubectl -n kube-system get ds` e `get pods -o wide`) e fazer o Pod dele voltar a rodar no nó. Normalmente é o próprio plugin que grava o arquivo em `/etc/cni/net.d/`.
6. **Validar:** com o `calico-node` rodando de novo no `w2`, os arquivos voltaram (`10-calico.conflist` e `calico-kubeconfig`) e o nó voltou a `Ready`.

## Outras causas

Disco cheio e falta de memória no nó aparecem como condições próprias (`DiskPressure`, `MemoryPressure`) no mesmo `kubectl describe node`. Não foram reproduzidas aqui, porque provocá-las derruba o que mais roda no nó.

## Reproduzir

No nó (por SSH):

```bash
sudo systemctl disable --now kubelet       # depois: sudo systemctl enable --now kubelet
sudo systemctl stop containerd             # depois: sudo systemctl start containerd
```

Para o CNI, o teste acrescentou ao DaemonSet `calico-node` uma `nodeAffinity` que exclui o `w2` e moveu os arquivos de `/etc/cni/net.d/` do `w2` para outra pasta (com `sudo sh -c 'mv /etc/cni/net.d/* /root/cni-bak/'`: sem o `sh -c`, o `*` é expandido pelo usuário comum, que não lê a pasta). Remover a affinity fez o `calico-node` voltar e regravar os arquivos.
