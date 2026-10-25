# Adicionar um nó com kubeadm join

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · **Domínio:** Cluster Architecture, Installation & Configuration (25%)

## O que é

`kubeadm join` coloca uma máquina num cluster que já existe. Na prova o cluster vem pronto, e a tarefa típica é: "o nó `node01` já tem kubeadm, kubelet e container runtime instalados; faça ele entrar no cluster".

São dois comandos, em dois nós diferentes:

1. **No control plane:** `kubeadm token create --print-join-command` gera um token novo e imprime o comando completo de join.
2. **No nó novo:** rodar esse comando como root.

O comando tem três partes:

| Parte | Para quê |
|---|---|
| `<control-plane>:6443` | Endereço do API server |
| `--token abcdef.0123456789abcdef` | Token de bootstrap: autoriza o nó a se apresentar ao cluster. Validade padrão de **24 horas** |
| `--discovery-token-ca-cert-hash sha256:...` | Hash da chave pública da CA do cluster: o nó confere que está falando com o cluster certo, e não com um impostor |

## Como funciona por dentro

[![kubeadm join](../assets/diagramas/01-kubeadm-join.svg)](../assets/diagramas/01-kubeadm-join.svg "Abrir o diagrama em tamanho real")

O join tem três etapas no nó novo:

1. **Preflight.** Confere portas, arquivos que não podem existir ainda, kubelet, swap e container runtime.
2. **Descoberta.** O nó baixa o ConfigMap `cluster-info` do namespace `kube-public`, que é público. Ele traz a CA do cluster e uma assinatura feita com cada token válido. O nó confere duas coisas:
    - a assinatura do **token** existe, ou seja, o token vale;
    - o **hash** da CA bate com o `--discovery-token-ca-cert-hash`.
3. **TLS bootstrap.** O kubelet usa o token para enviar um pedido de certificado (CSR). O kubeadm já deixa o cluster configurado para aprovar esse CSR sozinho. O kubelet recebe o certificado, grava o `/etc/kubernetes/kubelet.conf` e o nó aparece em `kubectl get nodes`.

Testado num cluster kind v1.36.4. O CSR do worker aparece aprovado, pedido pelo usuário do token (`system:bootstrap:<id do token>`):

```console
$ kubectl get csr
NAME        AGE   SIGNERNAME                                    REQUESTOR                        REQUESTEDDURATION   CONDITION
csr-fcqh6   10s   kubernetes.io/kube-apiserver-client-kubelet   system:bootstrap:6223ak          <none>              Approved,Issued
```

## Comandos essenciais

```bash
# No CONTROL PLANE: token novo + comando pronto (o mais rápido na prova)
kubeadm token create --print-join-command

# Token com outra validade
kubeadm token create --ttl 2h --print-join-command

# Tokens existentes e validade
kubeadm token list

# Apagar um token
kubeadm token delete <token>

# Calcular o hash da CA à mão (se tiver o token, mas não o hash)
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt \
  | openssl rsa -pubin -outform der 2>/dev/null \
  | openssl dgst -sha256 -hex | sed 's/^.* //'

# No NÓ NOVO, como root: colar o comando gerado
kubeadm join <control-plane>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>

# No nó novo: kubelet ligado e habilitado para subir no boot
systemctl enable --now kubelet

# De volta ao control plane: conferir
kubectl get nodes
```

Saída real do `--print-join-command` e do join (kind v1.36.4; o hash calculado com `openssl` deu o mesmo valor):

```console
$ kubeadm token create --print-join-command
kubeadm join join-control-plane:6443 --token 6223ak.1ta2rae1rjkrzmeo --discovery-token-ca-cert-hash sha256:87e1c4a544b7c753826f23aeda7e3a909511724fa3b9c3f8fe242bef2bb19c0c
```

```console
$ kubeadm join join-control-plane:6443 --token 6223ak.1ta2rae1rjkrzmeo --discovery-token-ca-cert-hash sha256:87e1c4a5...
[preflight] Running pre-flight checks
[preflight] Reading configuration from the "kubeadm-config" ConfigMap in namespace "kube-system"...
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Starting the kubelet
[kubelet-check] The kubelet is healthy after 500.886387ms
[kubelet-start] Waiting for the kubelet to perform the TLS Bootstrap

This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.

Run 'kubectl get nodes' on the control-plane to see this node join the cluster.
```

**Tirar um nó e colocar de novo** (útil para treinar no lab):

```bash
# No control plane
kubectl drain node01 --ignore-daemonsets --delete-emptydir-data
kubectl delete node node01

# No node01: desfaz o join (apaga kubelet.conf, pki/ca.crt e para o kubelet)
kubeadm reset -f

# Depois: gerar um comando novo no control plane e rodar no node01
```

`--dry-run=client -o yaml` não se aplica aqui: nenhum desses comandos cria um objeto que você escreveria em YAML.

## Na documentação oficial

- **Página principal:** *kubeadm join*. Link: <https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-join/>
- **Complementar:** *Adding Linux worker nodes*. Link: <https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/adding-linux-nodes/>
- **Complementar:** *kubeadm token*. Link: <https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-token/>
- **Busca rápida:** `kubeadm join`
- **Ctrl+F dentro da página principal:**
    - `print-join-command`: gerar o comando pronto.
    - `discovery-token-ca-cert-hash`: o que é o hash e o comando `openssl` para calculá-lo.

## Pegadinhas da prova

- **Rodar o join no nó errado.** `token create` roda no control plane; `join` roda no nó **novo**. Rodar o join no próprio control plane falha no preflight, porque `kubelet.conf` e `pki/ca.crt` já existem.
- **Rodar o join duas vezes.** O segundo join falha no preflight. Saída real:

    ```console
    [preflight] Some fatal errors occurred:
    	[ERROR FileAvailable--etc-kubernetes-kubelet.conf]: /etc/kubernetes/kubelet.conf already exists
    	[ERROR Port-10250]: Port 10250 is in use
    	[ERROR FileAvailable--etc-kubernetes-pki-ca.crt]: /etc/kubernetes/pki/ca.crt already exists
    ```

    Se o nó já aparece em `kubectl get nodes`, não há nada para fazer. Se é preciso refazer, rode `kubeadm reset -f` no nó antes.

- **Token vencido ou apagado.** O join **não falha na hora**: fica tentando por **5 minutos** e só então desiste. Na prova isso parece travado. Gere outro comando com `--print-join-command`. Saída real depois dos 5 minutos:

    ```console
    error: error execution phase preflight: couldn't validate the identity of the API Server: could not find a JWS signature in the cluster-info ConfigMap for token ID "6223ak"
    ```

- **Hash errado** (copiado pela metade, por exemplo). Esse falha na hora:

    ```console
    error: error execution phase preflight: couldn't validate the identity of the API Server: cluster CA found in cluster-info ConfigMap is invalid: none of the public keys "sha256:87e1c4a5..." are pinned
    ```

- **kubelet não habilitado.** O join funciona e o nó fica Ready, mas o kubelet não sobe sozinho depois de um reboot. O preflight avisa e segue em frente:

    ```console
    [WARNING Service-kubelet]: kubelet service is not enabled, please run 'systemctl enable kubelet.service'
    ```

    Rode `systemctl enable kubelet` no nó.

- **Esquecer `sudo`.** `kubeadm join` precisa de root.
- **Esquecer de voltar ao control plane para conferir.** No nó novo normalmente não há kubeconfig de admin, então o `kubectl get nodes` roda no control plane (ou na máquina de onde você opera o cluster).
- **ip_forward não bloqueia o join na v1.36.** Muito material antigo diz que o preflight falha com `/proc/sys/net/ipv4/ip_forward` em 0. No teste com kubeadm v1.36.4, o join entrou normalmente com `ip_forward=0`, e a lista de verificações do preflight do join (vista com `--v=5`) não tem essa checagem. A documentação de *Container Runtimes* continua pedindo `net.ipv4.ip_forward = 1` na preparação do nó, porque a rede dos Pods depende disso.

## Pratique

**Enunciado (como na prova):**

> The node `node01` has kubeadm, kubelet and containerd installed but is not part of the cluster. Join `node01` to the cluster and make sure it is `Ready`.

**Tradução:** o nó `node01` tem kubeadm, kubelet e containerd instalados, mas não faz parte do cluster. Coloque o `node01` no cluster e garanta que ele fique `Ready`.

??? success "Solução"
    ```bash
    # 1. No control plane: gerar o comando
    ssh controlplane
    sudo kubeadm token create --print-join-command
    # copiar a linha impressa

    # 2. No nó novo: rodar o comando como root
    ssh node01
    sudo kubeadm join <control-plane>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
    sudo systemctl enable kubelet
    exit
    ```

**Como verificar:**

```bash
# No control plane
kubectl get nodes          # node01 aparece e fica Ready em alguns segundos
kubectl get csr            # CSR com REQUESTOR system:bootstrap:<id> e CONDITION Approved,Issued
```

Se o nó aparece mas fica `NotReady`, o problema já não é o join: veja [Nó NotReady](../05-troubleshooting/no-notready.md).

??? tip "No lab / Killercoda"

    - Num cluster kind com um worker (`kind create cluster --config` com `role: worker`), os nós são containers: `docker exec -it <nome>-worker bash` faz o papel do `ssh node01`. O roteiro desta página (drain, delete, `kubeadm reset`, novo join) foi testado assim.
    - Apague o token com `kubeadm token delete` e tente o join: veja a espera de 5 minutos e a mensagem final.
    - Troque um caractere do hash e compare: esse erro aparece na hora.
    - Rode `kubeadm join ... --v=5` para ver cada verificação do preflight e cada tentativa da descoberta.
