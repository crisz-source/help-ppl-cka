# Control plane com problema

> **Versão do Kubernetes:** v1.37 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 3 cenários

Num cluster kubeadm, o kube-apiserver, o kube-scheduler, o kube-controller-manager e o etcd são **static Pods**: o kubelet do control plane os cria a partir dos arquivos em `/etc/kubernetes/manifests/`. Mexer nesses arquivos é o jeito de quebrar e de consertar.

| Componente fora | Sintoma | Pista |
|---|---|---|
| kube-scheduler | Pods novos ficam `Pending` | **`Events: <none>`**: ninguém tentou agendar |
| kube-controller-manager | Deployment criado, mas `0/1` e sem ReplicaSet | `kubectl get rs` não mostra nada |
| kube-apiserver | `kubectl` não responde | `crictl ps -a`: container `Exited` |

A página [Control plane fora](../../05-troubleshooting/control-plane.md) do Domínio 5 explica a leitura do `crictl` e tem o teste do `.bak` dentro da pasta de manifestos.

**Backup sempre fora da pasta:** `cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/`. O kubelet lê todo arquivo da pasta de manifestos.

## kube-scheduler fora

1. **Sintoma:** `kubectl run` funciona, mas o Pod fica `Pending`.
2. **Primeiro comando:** `kubectl describe pod sem-scheduler`
3. **Evidência:** não há evento nenhum. Quando o scheduler existe e não acha nó, aparece `FailedScheduling`:

    ```console
    $ kubectl get pod sem-scheduler
    NAME            READY   STATUS    RESTARTS   AGE
    sem-scheduler   0/1     Pending   0          15s
    $ kubectl describe pod sem-scheduler | sed -n '/^Events:/,$p'
    Events:                      <none>
    $ kubectl -n kube-system get pods | grep scheduler
    ```

    O último comando não devolve nada: o Pod `kube-scheduler-<nó>` sumiu.

4. **Causas prováveis:** manifesto fora da pasta (ou com outro nome), ou manifesto com erro que impede o container de subir.
5. **Correção:** devolver ou corrigir `/etc/kubernetes/manifests/kube-scheduler.yaml`.
6. **Validar:** `crictl ps --name kube-scheduler` → `Running`; o Pod `Pending` é agendado sozinho.

## kube-controller-manager fora

1. **Sintoma:** `kubectl create deployment` responde `created`, mas nada roda.
2. **Primeiro comando:** `kubectl get deploy` e `kubectl get rs`
3. **Evidência:**

    ```console
    $ kubectl get deploy sem-cm
    NAME     READY   UP-TO-DATE   AVAILABLE   AGE
    sem-cm   0/1     0            0           15s
    $ kubectl get rs -l app=sem-cm
    No resources found in ts namespace.
    ```

    O API server gravou o Deployment, mas quem cria o ReplicaSet é o controller-manager.

4. **Causas prováveis:** as mesmas do scheduler, no arquivo `kube-controller-manager.yaml`.
5. **Correção:** devolver ou corrigir o manifesto.
6. **Validar:** o ReplicaSet aparece (`sem-cm-7d99d6cdf8   1   1   1`) e o Deployment fica `1/1`.

## kube-apiserver com erro no manifesto

1. **Sintoma:** o `kubectl` para de responder. Rodando no próprio control plane (saída real, lab v1.37.1), a mensagem muda conforme o momento em que o container está:

    ```console
    Unable to connect to the server: context deadline exceeded (Client.Timeout exceeded while awaiting headers)
    The connection to the server 10.0.1.4:6443 was refused - did you specify the right host or port?
    ```

    A primeira aparece enquanto o container está subindo; a segunda, entre um restart e outro.

2. **Primeiro comando:** no control plane, `crictl ps -a --name kube-apiserver`
3. **Evidência:** o container sobe e morre (`Exited`, `ATTEMPT` subindo), e o log diz por quê:

    ```console
    $ crictl ps -a --name kube-apiserver
    CONTAINER           IMAGE               CREATED             STATE               NAME                ATTEMPT             POD ID              POD                 NAMESPACE
    dd06c7e1c6a3b       82ae6c548117f       3 seconds ago       Running             kube-apiserver      2                   5288acca24cd7       kube-apiserver-cp   kube-system
    7f27ff138218a       82ae6c548117f       34 seconds ago      Exited              kube-apiserver      1                   5288acca24cd7       kube-apiserver-cp   kube-system
    $ crictl logs --tail 40 <id>
    W1025 09:59:20.243160       1 logging.go:55] [core] [Channel #3 SubChannel #4] grpc: addrConn.createTransport failed to connect to {Addr: "127.0.0.1:2380", ServerName: "127.0.0.1:2380", }. Err: connection error: desc = "transport: Error while dialing: dial tcp 127.0.0.1:2380: connect: connection refused"
    ```

    O apiserver tentava falar com o etcd na porta **2380** (a porta entre membros do etcd); a porta de clientes é a **2379**.

4. **Causas prováveis:** flag com valor errado (porta, caminho de certificado), flag que não existe, ou YAML inválido. Com YAML inválido, o container nem aparece no `crictl ps -a`: olhe o `journalctl -u kubelet`.
5. **Correção:** corrigir a flag em `/etc/kubernetes/manifests/kube-apiserver.yaml` (aqui, `--etcd-servers=https://127.0.0.1:2379`) e esperar o kubelet recriar o container.
6. **Validar:** `watch crictl ps` até o `kube-apiserver` ficar `Running`; depois `kubectl get nodes`.

Certificado vencido ou trocado também derruba o control plane. Os casos estão em [Certificados com kubeadm](../../01-cluster-architecture/kubeadm-certs.md).

## Reproduzir

No nó do control plane (`ssh cp`, depois `sudo -i`):

```bash
# scheduler e controller-manager fora
mv /etc/kubernetes/manifests/kube-scheduler.yaml /etc/kubernetes/manifests/kube-controller-manager.yaml /root/
# depois: mv /root/kube-scheduler.yaml /root/kube-controller-manager.yaml /etc/kubernetes/manifests/

# apiserver apontando para a porta errada do etcd
cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/kube-apiserver.yaml.bak
sed -i 's#--etcd-servers=https://127.0.0.1:2379#--etcd-servers=https://127.0.0.1:2380#' /etc/kubernetes/manifests/kube-apiserver.yaml
# depois: cp /root/kube-apiserver.yaml.bak /etc/kubernetes/manifests/kube-apiserver.yaml
```
