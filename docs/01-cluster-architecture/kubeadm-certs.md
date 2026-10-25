# Certificados com kubeadm

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-23 · **Domínio:** Cluster Architecture, Installation & Configuration (25%)

## O que é

Todo componente do Kubernetes se comunica por **TLS mútuo**: cada lado apresenta um certificado assinado por uma **CA** (autoridade certificadora) em que o outro confia. O kubeadm cria essa estrutura (a *PKI* do cluster) no `kubeadm init` e oferece o subcomando `kubeadm certs` para administrá-la.

O que importa para a prova:

- **Onde ficam** os certificados e qual componente usa cada um.
- **Ver a validade**: `kubeadm certs check-expiration` ou `openssl`.
- **Renovar**: `kubeadm certs renew`, e depois **reiniciar** os componentes do control plane.
- **Ler um certificado**: emissor, validade e SANs (os nomes/IPs para os quais o certificado vale).

Validade padrão no kubeadm:

| Tipo | Validade | Renovação |
|---|---|---|
| CAs (`ca.crt`, `etcd/ca.crt`, `front-proxy-ca.crt`) | 10 anos | Manual e trabalhosa: fora do escopo do `kubeadm certs renew` |
| Certificados "folha" (apiserver, etcd server, kubeconfigs...) | 1 ano | `kubeadm certs renew`, ou automática a cada `kubeadm upgrade apply` |

Se o cluster passa um ano sem upgrade nem renovação, os certificados vencem e o `kubectl` para de funcionar com erro `x509: certificate has expired`.

## Como funciona por dentro

Um cluster kubeadm tem **três CAs**, cada uma com seu grupo de certificados:

[![Certificados do kubeadm](../assets/diagramas/01-kubeadm-certs.svg)](../assets/diagramas/01-kubeadm-certs.svg "Abrir o diagrama em tamanho real")

Arquivos em `/etc/kubernetes/pki/` (control plane):

| Arquivo | Quem usa | Para quê |
|---|---|---|
| `ca.crt` / `ca.key` | Todos | CA principal: assina os demais e valida clientes |
| `apiserver.crt` | kube-apiserver | Certificado de **servidor** HTTPS (os SANs listam IPs e nomes do API server) |
| `apiserver-kubelet-client.crt` | kube-apiserver | **Cliente** ao falar com o kubelet (`logs`, `exec`) |
| `apiserver-etcd-client.crt` | kube-apiserver | **Cliente** ao falar com o etcd |
| `etcd/server.crt`, `etcd/peer.crt` | etcd | Servidor para clientes e comunicação entre membros do etcd |
| `etcd/healthcheck-client.crt` | probe do etcd | Cliente para health check |
| `front-proxy-client.crt` | kube-apiserver | API aggregation (ex.: metrics-server) |
| `sa.key` / `sa.pub` | apiserver, controller-manager | Par de chaves que assina tokens de ServiceAccount. **Não é certificado e não expira.** |

Os kubeconfigs em `/etc/kubernetes/` (`admin.conf`, `super-admin.conf`, `controller-manager.conf`, `scheduler.conf`) têm o certificado de cliente **embutido em base64**. Por isso o `kubeadm certs renew` também regenera esses arquivos.

**Reinício após renovar**: os componentes do control plane são static Pods e só leem os certificados ao iniciar. O kubelet **não** recria o Pod quando um `.crt` muda, só quando o manifest em `/etc/kubernetes/manifests/` muda. Depois de renovar, você precisa reiniciar o apiserver, o controller-manager, o scheduler e o etcd.

**kubelet**: o certificado de cliente do kubelet (`/var/lib/kubelet/pki/kubelet-client-current.pem`) é **rotacionado automaticamente** pelo próprio kubelet (`rotateCertificates: true` na configuração gerada pelo kubeadm). Por isso o `kubelet.conf` aponta para esse arquivo em vez de embutir o certificado. Por isso também o `kubeadm certs check-expiration` **não lista** o `kubelet.conf` (conferido na v1.36.4).

## Comandos essenciais

```bash
# Validade de todos os certificados gerenciados pelo kubeadm (rodar no control plane, como root)
kubeadm certs check-expiration

# Renovar TODOS os certificados folha (não renova as CAs)
kubeadm certs renew all

# Renovar só um
kubeadm certs renew apiserver
kubeadm certs renew admin.conf
kubeadm certs renew etcd-server

# Ver os nomes aceitos pelo renew
kubeadm certs renew --help

# Depois de renovar: reiniciar os static Pods do control plane.
# Tirar os manifests da pasta faz o kubelet parar os Pods; devolver faz recriar.
mkdir -p /tmp/manifests
mv /etc/kubernetes/manifests/*.yaml /tmp/manifests/
sleep 20                      # o kubelet verifica a pasta a cada ~20s
mv /tmp/manifests/*.yaml /etc/kubernetes/manifests/
crictl ps                     # conferir que voltaram

# Se o admin.conf foi renovado, atualizar o kubeconfig do usuário
cp /etc/kubernetes/admin.conf ~/.kube/config
```

**Ler um certificado com openssl** (funciona para qualquer `.crt`, gerenciado pelo kubeadm ou não):

```bash
# Validade (notBefore / notAfter)
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -dates

# Só a data de expiração
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate

# Emissor (quem assinou) e sujeito (CN = nome, O = grupo)
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -issuer -subject

# SANs: nomes e IPs para os quais o certificado vale
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -text | grep -A1 "Subject Alternative Name"

# Certificado embutido num kubeconfig: decodificar o base64 e ler
grep client-certificate-data /etc/kubernetes/admin.conf | awk '{print $2}' | base64 -d | openssl x509 -noout -enddate -subject
```

**Descobrir qual arquivo cada componente usa** (essencial em Troubleshooting):

```bash
grep -E '\-file|cafile|certfile|keyfile|certificate' /etc/kubernetes/manifests/kube-apiserver.yaml
```

`--dry-run=client -o yaml` não se aplica aqui: nenhum desses comandos cria objeto Kubernetes.

## YAML de referência

Flags de certificado no `/etc/kubernetes/manifests/kube-apiserver.yaml`. São elas que você corrige quando o apiserver não sobe por caminho errado:

```yaml
spec:
  containers:
    - name: kube-apiserver
      command:
        - kube-apiserver
        - --client-ca-file=/etc/kubernetes/pki/ca.crt                     # CA que valida clientes (kubectl, kubelet...)
        - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt                # certificado de servidor
        - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
        - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
        - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
        - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt                    # CA do etcd, NÃO a ca.crt principal
        - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
        - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
        - --service-account-key-file=/etc/kubernetes/pki/sa.pub            # valida tokens de ServiceAccount
        - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key    # assina tokens
```

Configuração do kubeadm que influencia os certificados (usada no `kubeadm init --config`):

```yaml
apiVersion: kubeadm.k8s.io/v1beta4
kind: ClusterConfiguration
apiServer:
  certSANs:                       # nomes/IPs extras no apiserver.crt (ex.: IP público, DNS do load balancer)
    - "k8s.meulab.exemplo"
    - "20.0.0.10"
certificateValidityPeriod: 8760h0m0s     # validade dos certificados folha (padrão 1 ano)
caCertificateValidityPeriod: 87600h0m0s  # validade das CAs (padrão 10 anos)
```

<!-- VERIFICAR: certificateValidityPeriod e caCertificateValidityPeriod existem a partir da API v1beta4 (kubeadm v1.31); conferir na referência "kubeadm Configuration (v1beta4)" -->

## Na documentação oficial

- **Página principal:** *Certificate Management with kubeadm*. Link: <https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/>
- **Complementar:** *PKI certificates and requirements* (lista de todos os certificados e caminhos). Link: <https://kubernetes.io/docs/setup/best-practices/certificates/>
- **Busca rápida:** `kubeadm certs`
- **Ctrl+F dentro da página principal:**
    - `check-expiration`: comando e exemplo de saída.
    - `renew all`: renovação manual.
    - `restart the control plane Pods`: o aviso de que é preciso reiniciar (e como).
    - `automatic certificate renewal`: renovação automática no upgrade.
- **Ctrl+F na página de PKI:** `apiserver-etcd-client` (tabela "certificate paths", com o arquivo de cada flag).

## Pegadinhas da prova

- **Renovar e não reiniciar.** `check-expiration` mostra a data nova, mas o apiserver continua servindo o certificado antigo até reiniciar.
- **`kubectl` quebra depois do renew.** O `admin.conf` foi renovado e o `~/.kube/config` ainda tem o certificado antigo. Copie de novo.
- **`renew` não renova as CAs.** CA vencida exige outro procedimento. Na prova, o que costuma cair é renovar certificado folha.
- **CA errada nas flags.** `--etcd-cafile` usa `etcd/ca.crt`, não `ca.crt`. Trocar uma pela outra deixa o apiserver sem falar com o etcd, uma questão clássica de Troubleshooting.
- **`.crt` × `.key` trocados** em flags com nome parecido (`--tls-cert-file` × `--tls-private-key-file`, `--etcd-certfile` × `--etcd-keyfile`).
- **Rodar no nó errado.** `kubeadm certs` funciona no **control plane**, onde está `/etc/kubernetes/pki`. Em worker não há nada para renovar.
- **Esquecer `sudo`.** As chaves privadas só são legíveis por root.
- **Gravar o resultado no lugar pedido.** Questões do tipo "write the expiration date to /opt/..." conferem o arquivo. Grave só o que foi pedido, no caminho exato.

## Pratique

**Enunciado (como na prova):**

> On the control plane node `controlplane`, find the expiration date of the kube-apiserver serving certificate and write it to `/opt/apiserver-expiry.txt`. Then renew the kube-apiserver serving certificate using kubeadm and make sure the API server is using the new certificate.

**Tradução:** no nó `controlplane`, descubra a data de expiração do certificado de servidor do kube-apiserver e grave em `/opt/apiserver-expiry.txt`. Depois renove esse certificado com kubeadm e garanta que o API server está usando o certificado novo.

??? success "Solução"
    ```bash
    ssh controlplane
    sudo -i

    # 1. Data de expiração (qualquer uma das duas formas)
    openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate > /opt/apiserver-expiry.txt
    # ou: kubeadm certs check-expiration | grep '^apiserver ' > /opt/apiserver-expiry.txt
    cat /opt/apiserver-expiry.txt

    # 2. Renovar
    kubeadm certs renew apiserver

    # 3. Reiniciar o apiserver (static Pod)
    mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
    sleep 20
    mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
    ```

**Como verificar:**

```bash
# Data do arquivo em disco
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate

# Data do certificado que o apiserver está SERVINDO agora: precisa ser igual à de cima
echo | openssl s_client -connect 127.0.0.1:6443 2>/dev/null | openssl x509 -noout -enddate

kubectl get nodes   # API respondendo normalmente
```

??? tip "No lab / Killercoda"

    - No lab Azure, adicione o **IP público** da VM do control plane ao `apiserver.crt` para usar o `kubectl` de fora. Sem isso, o erro é `x509: certificate is valid for 10.x.x.x, not 20.x.x.x`. Procedimento: incluir o IP em `certSANs`, remover `apiserver.crt`/`apiserver.key` e rodar `kubeadm init phase certs apiserver --config <arquivo>`. <!-- VERIFICAR: conferir o procedimento atual na página "Certificate Management with kubeadm" -->
    - Rode `kubeadm certs renew all` **sem** reiniciar nada e compare `openssl s_client` (o que é servido) com o arquivo em disco. Assim você vê na prática por que o reinício é obrigatório.
    - Troque `--etcd-cafile` por `/etc/kubernetes/pki/ca.crt` no manifest do apiserver e investigue com `crictl logs`. É treino direto de Troubleshooting. Depois desfaça.
    - Antes de qualquer experimento, faça backup de `/etc/kubernetes/` (`cp -a /etc/kubernetes /root/k8s-backup`).
