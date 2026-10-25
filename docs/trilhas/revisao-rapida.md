# Revisão rápida

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · Trilha para quem já estudou e quer revisar antes da prova

**Já conhece Kubernetes?** Revise os comandos e as pegadinhas mais importantes numa sequência curta, organizada pelo peso de cada domínio na prova. Cada cartão tem o que lembrar, um comando-chave e a pegadinha que mais derruba. O detalhe e os testes estão na página completa de cada tópico.

Para os comandos que valem em qualquer questão (contexto, `explain`, jsonpath, labels), use a folha de [Comandos de memória](comandos-de-memoria.md).

## 5. Troubleshooting (30%)

### Logs e eventos

[Página completa](../05-troubleshooting/logs-eventos.md)

**Lembre:** Pod que nunca rodou (Pending, ImagePullBackOff, CreateContainerConfigError) não tem log: a resposta está nos Events. Evento some depois de 1 hora.

**Comando-chave:** `kubectl get events --sort-by=.lastTimestamp`

**Pegadinha:** sem `--sort-by`, os eventos não saem em ordem cronológica. Em Pod com vários containers, `kubectl logs` sem `-c` pode mostrar o container errado.

### Pods: Pending, CrashLoopBackOff, ImagePullBackOff

[Página completa](../05-troubleshooting/pods.md)

**Lembre:** `describe` primeiro, `logs` depois. `0/1 Running` com 0 restarts é readiness falhando; muitos restarts com `Running` é liveness matando o container.

**Comando-chave:** `kubectl describe pod <nome>` (seção Events) e `kubectl logs <nome> --previous`

**Pegadinha:** Pod de Deployment se corrige no Deployment. Apagar ou editar o Pod não adianta, porque o ReplicaSet recria igual.

### Nó NotReady

[Página completa](../05-troubleshooting/no-notready.md)

**Lembre:** quase sempre é o kubelet (parado, desabilitado, configuração errada) ou o container runtime. A resposta está no `journalctl -u kubelet`.

**Comando-chave:** `systemctl status kubelet` e `journalctl -u kubelet | grep -iE 'error|fail' | tail`

**Pegadinha:** `systemctl start` não basta se o serviço estiver desabilitado. Use `systemctl enable --now kubelet`, e `daemon-reload` se mexeu em unidade do systemd.

### Control plane fora

[Página completa](../05-troubleshooting/control-plane.md)

**Lembre:** os componentes são static Pods em `/etc/kubernetes/manifests/`. Se o `kubectl` não responde, vá direto para o `crictl` no control plane.

**Comando-chave:** `crictl ps -a --name kube-apiserver` e `crictl logs <id>`

**Pegadinha:** backup do manifesto **fora** da pasta de manifestos. Um `.bak` lá dentro vira outro static Pod e engole a sua correção.

## 1. Cluster Architecture (25%)

### RBAC

[Página completa](../01-cluster-architecture/rbac.md)

**Lembre:** Role é de um namespace; ClusterRole vale no cluster todo. RoleBinding pode usar uma ClusterRole. `roleRef` é imutável: para trocar, apague e recrie.

**Comando-chave:** `kubectl auth can-i list pods --as=system:serviceaccount:shop:leitor -n shop`

**Pegadinha:** RoleBinding com ClusterRole **não** vira permissão global, vale só no namespace do binding. E ClusterRoleBinding não aceita Role.

### Upgrade com kubeadm

[Página completa](../01-cluster-architecture/upgrade-kubeadm.md)

**Lembre:** um minor por vez, control plane antes dos workers. No primeiro control plane: `kubeadm upgrade apply`; nos outros nós: `kubeadm upgrade node`. Depois, kubelet e kubectl, e restart do kubelet.

**Comando-chave:** `kubeadm upgrade plan` e `kubeadm upgrade apply v1.37.Y`

**Pegadinha:** esquecer de trocar o repositório apt para o minor novo: `apt-cache madison kubeadm` só mostra versões do minor atual.

### Adicionar um nó com kubeadm join

[Página completa](../01-cluster-architecture/kubeadm-join.md)

**Lembre:** o comando é gerado no control plane e rodado como root no nó novo. Token vale 24 horas.

**Comando-chave:** `kubeadm token create --print-join-command`

**Pegadinha:** token vencido não dá erro na hora: o join fica tentando por 5 minutos. Gere outro comando em vez de esperar.

### Certificados com kubeadm

[Página completa](../01-cluster-architecture/kubeadm-certs.md)

**Lembre:** CAs valem 10 anos, certificados folha 1 ano. `kubeadm certs renew` não renova as CAs.

**Comando-chave:** `kubeadm certs check-expiration` e `kubeadm certs renew all`

**Pegadinha:** renovar e não reiniciar. O apiserver continua servindo o certificado antigo até os static Pods serem recriados.

### Drain, cordon e uncordon

[Página completa](../01-cluster-architecture/drain-cordon-uncordon.md)

**Lembre:** `cordon` só para de agendar; `drain` faz cordon e expulsa os Pods; `uncordon` libera de novo.

**Comando-chave:** `kubectl drain node01 --ignore-daemonsets --delete-emptydir-data`

**Pegadinha:** `uncordon` não traz os Pods de volta. E `--force` apaga para sempre Pods sem controller.

### Backup e restore do etcd

[Página completa](../01-cluster-architecture/etcd-backup-restore.md)

**Lembre:** backup com `etcdctl snapshot save` e os certificados de `/etc/kubernetes/pki/etcd/`. Restore com `etcdutl` para uma pasta **nova**, depois aponte o `hostPath` do manifesto do etcd para ela.

**Comando-chave:** `etcdutl snapshot restore /opt/snap.db --data-dir /var/lib/etcd-restore`

**Pegadinha:** no etcd 3.6+, `etcdctl snapshot restore` responde `unknown flag: --data-dir`. Não é flag errada: o subcomando passou para o `etcdutl`.

### Helm e Kustomize

[Página completa](../01-cluster-architecture/helm-kustomize.md)

**Lembre:** `helm install <release> <chart>`, nessa ordem. Kustomize se aplica com `-k`, nunca com `-f`.

**Comando-chave:** `helm install web bitnami/nginx -n web --create-namespace` e `kubectl apply -k overlays/prod`

**Pegadinha:** `--set` com chave inexistente é ignorado em silêncio. Confira o nome com `helm show values`.

## 3. Services & Networking (20%)

### Services e Endpoints

[Página completa](../03-services-networking/services-endpoints.md)

**Lembre:** `port` é a do Service, `targetPort` a do container, `nodePort` a do nó (30000-32767). O selector precisa bater com os labels do **template do Pod**.

**Comando-chave:** `kubectl expose deployment web --port=80 --target-port=8080` e `kubectl get endpointslices -l kubernetes.io/service-name=web`

**Pegadinha:** `kubectl create service` inventa o selector `app=<nome>`. Se o Deployment usa outro label, o Service fica sem endpoints.

### DNS do cluster

[Página completa](../03-services-networking/dns.md)

**Lembre:** Service: `<svc>.<ns>.svc.cluster.local`. Pod: o IP com hifens, `10-244-1-5.<ns>.pod.cluster.local`. O Service do CoreDNS se chama `kube-dns`.

**Comando-chave:** `kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 -- nslookup web.shop.svc.cluster.local`

**Pegadinha:** nome curto só resolve no mesmo namespace. De outro namespace, use `web.shop` ou o FQDN.

### NetworkPolicy

[Página completa](../03-services-networking/network-policy.md)

**Lembre:** a política seleciona Pods do próprio namespace. Não existe "deny": tudo que não está liberado fica bloqueado para os Pods selecionados.

**Comando-chave:** `kubectl describe networkpolicy <nome>`

**Pegadinha:** `namespaceSelector` e `podSelector` no mesmo item é E; com `-` nos dois é OU. E restringir egress sem liberar a porta 53 quebra o DNS.

### Ingress

[Página completa](../03-services-networking/ingress.md)

**Lembre:** Ingress sem controller não faz nada. O `ingressClassName` vem de `kubectl get ingressclass`.

**Comando-chave:** `kubectl create ingress web --class=nginx --rule="app.exemplo.com/api*=api:80"`

**Pegadinha:** sem `*`, o `pathType` vira `Exact` e `/api` não atende `/api/users`. 404 do controller = nenhuma regra casou; 503 = Service sem endpoints.

### Gateway API

[Página completa](../03-services-networking/gateway-api.md)

**Lembre:** GatewayClass → Gateway → HTTPRoute → Service. A rota se liga ao Gateway por `parentRefs`.

**Comando-chave:** `kubectl describe httproute <nome>` (condições `Accepted` e `ResolvedRefs`)

**Pegadinha:** Service em outro namespace exige `ReferenceGrant` no namespace **do Service**. Sem ele: `RefNotPermitted`.

## 2. Workloads & Scheduling (15%)

### Deployments: rollout, rollback e scale

[Página completa](../02-workloads-scheduling/deployments-rollout.md)

**Lembre:** `set image` usa o nome do **container**. `scale` não gera revisão. `rollout undo` volta a revisão anterior com um número novo.

**Comando-chave:** `kubectl set image deploy/web nginx=nginx:1.28` e `kubectl rollout undo deploy/web`

**Pegadinha:** `selector` é imutável. Para mudar, apague e recrie o Deployment.

### ConfigMap e Secret

[Página completa](../02-workloads-scheduling/configmap-secret.md)

**Lembre:** base64 não é criptografia. Variável de ambiente não atualiza sozinha; volume sem `subPath` atualiza.

**Comando-chave:** `kubectl get secret s1 -o jsonpath='{.data.senha}' | base64 -d`

**Pegadinha:** ConfigMap ou Secret inexistente deixa o Pod em `CreateContainerConfigError` (env) ou `ContainerCreating` (volume).

### Requests, limits e QoS

[Página completa](../02-workloads-scheduling/requests-limits-qos.md)

**Lembre:** o scheduler usa **requests**. Memória acima do limit mata (OOMKilled, exit 137); CPU acima do limit só deixa lento.

**Comando-chave:** `kubectl describe node <nó>` (seção Allocated resources)

**Pegadinha:** `memory: 128m` é 0,128 byte, não 128 MB. O certo é `128Mi`.

### ResourceQuota

[Página completa](../02-workloads-scheduling/resourcequota.md)

**Lembre:** quota é por namespace. Quota de CPU/memória obriga todo Pod novo a declarar esses valores.

**Comando-chave:** `kubectl describe quota -n <ns>`

**Pegadinha:** Deployment `0/N` sem erro no `apply`: a recusa aparece no `kubectl describe rs`, não no Deployment.

### Taints, tolerations e nodeSelector

[Página completa](../02-workloads-scheduling/taints-tolerations-nodeselector.md)

**Lembre:** taint afasta, toleration permite, nodeSelector atrai. Só `NoExecute` expulsa Pods que já rodam.

**Comando-chave:** `kubectl taint nodes w1 dedicado=gpu:NoSchedule` (o `-` no fim remove)

**Pegadinha:** toleration não atrai. "Só no nó X" precisa de nodeSelector ou node affinity.

### Affinity e anti-affinity

[Página completa](../02-workloads-scheduling/affinity.md)

**Lembre:** `required` é obrigatório, `preferred` é preferência com `weight`. Pod affinity olha labels de **Pods** e precisa de `topologyKey`.

**Comando-chave:** `kubectl explain pod.spec.affinity --recursive` (os nomes são longos: copie em vez de digitar)

**Pegadinha:** anti-affinity `required` com mais réplicas que nós deixa as réplicas que sobram em `Pending`.

### DaemonSet, Job, CronJob e StatefulSet

[Página completa](../02-workloads-scheduling/daemonset-job-cronjob-statefulset.md)

**Lembre:** não existe `kubectl create daemonset`: gere um Deployment, troque o `kind` e apague `replicas` e `strategy`. CronJob tem três níveis de `spec`.

**Comando-chave:** `kubectl create job teste --from=cronjob/<nome>` (testa o CronJob sem esperar)

**Pegadinha:** DaemonSet sem a toleration do control plane não roda lá.

### HPA

[Página completa](../02-workloads-scheduling/hpa.md)

**Lembre:** a porcentagem é do **request**. Precisa de metrics-server. API atual: `autoscaling/v2`.

**Comando-chave:** `kubectl autoscale deployment web --cpu=50% --min=2 --max=5` (`--cpu-percent` ainda funciona, mas está descontinuada)

**Pegadinha:** `TARGETS <unknown>` = falta metrics-server, falta `requests` no container ou a métrica ainda não chegou.

## 4. Storage (10%)

### Volumes em Pods: emptyDir e hostPath

[Página completa](../04-storage/volumes-emptydir-hostpath.md)

**Lembre:** `emptyDir` sobrevive a restart do container, não à remoção do Pod. `hostPath` é do nó onde o Pod roda.

**Comando-chave:** `kubectl explain pod.spec.volumes.hostPath`

**Pegadinha:** `type: Directory` com caminho inexistente deixa o Pod em `ContainerCreating`. Use `DirectoryOrCreate`.

### PV e PVC

[Página completa](../04-storage/pv-pvc.md)

**Lembre:** PV não tem namespace; PVC tem. Ligam quando `storageClassName`, `accessModes` e tamanho são compatíveis.

**Comando-chave:** `kubectl get pv,pvc` e `kubectl describe pvc <nome>` (Events)

**Pegadinha:** PVC sem `storageClassName` num cluster com classe padrão recebe a classe padrão e não liga num PV sem classe.

### StorageClass e provisionamento dinâmico

[Página completa](../04-storage/storageclass.md)

**Lembre:** a StorageClass cria o PV sozinha quando o PVC pede. `reclaimPolicy` padrão é `Delete`.

**Comando-chave:** `kubectl get sc` (a padrão aparece com `(default)`)

**Pegadinha:** PVC `Pending` com `WaitForFirstConsumer` não é erro: liga quando um Pod usar o PVC.

### reclaimPolicy: Retain × Delete

[Página completa](../04-storage/reclaim-policy.md)

**Lembre:** no PV o campo é `persistentVolumeReclaimPolicy`; na StorageClass, `reclaimPolicy`. PV `Released` não liga em PVC novo até remover o `claimRef`.

**Comando-chave:** `kubectl patch pv <pv> -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'`

**Pegadinha:** para preservar os dados, mude para `Retain` **antes** de apagar o PVC.

### Expansão de PVC

[Página completa](../04-storage/expansao-pvc.md)

**Lembre:** só PVC de StorageClass com `allowVolumeExpansion: true`. O pedido é feito no PVC, nunca no PV. Diminuir não existe.

**Comando-chave:** `kubectl patch pvc <pvc> -p '{"spec":{"resources":{"requests":{"storage":"2Gi"}}}}'`

**Pegadinha:** `CAPACITY` não mudou? A condição `FileSystemResizePending` pede para reiniciar o Pod que usa o volume.
