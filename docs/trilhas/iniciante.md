# Começar do zero

> **Versão do Kubernetes:** v1.37 · **Última revisão:** 2026-10-25 · Trilha para quem conhece Linux e containers, mas ainda não tem segurança com Kubernetes

**Objetivo:** construir a base antes de entrar nos detalhes da prova. São 12 passos. Cada um aponta para a página que ensina o assunto e termina com uma tarefa curta para fazer num cluster de estudo (kind, minikube ou Killercoda).

Na primeira leitura, fique com "O que é", "Comandos essenciais" e o exercício de cada página. Os blocos recolhidos (YAML completo, "No lab") podem esperar a segunda volta.

Todas as tarefas foram feitas no lab (kubeadm v1.37.1, 1 control plane + 2 workers, Calico, local-path-provisioner); as soluções são os comandos usados.

## 1. Fundamentos: Pod, namespace, labels, Deployment e Service

**Leia:** [Fundamentos](fundamentos.md)

> **Tarefa:** crie um Deployment com 3 réplicas, exponha-o com um Service e apague um Pod para ver o Deployment repor.

A solução está no fim da própria página.

## 2. ConfigMap e Secret

**Leia:** [ConfigMap e Secret](../02-workloads-scheduling/configmap-secret.md)

> **Tarefa:** crie um ConfigMap `app-config` com `COR=azul` e um Pod que receba todas as chaves dele como variáveis de ambiente e imprima `COR`.

??? success "Solução"
    ```bash
    kubectl -n estudo create configmap app-config --from-literal=COR=azul
    ```

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata: {name: cfg, namespace: estudo}
    spec:
      restartPolicy: Never
      containers:
      - name: cfg
        image: busybox:1.36
        command: [sh, -c, 'echo COR=$COR; sleep 3600']
        envFrom: [{configMapRef: {name: app-config}}]
    ```

    `kubectl -n estudo logs cfg` mostra `COR=azul`.

## 3. Volumes, PV e PVC

**Leia:** [Volumes em Pods](../04-storage/volumes-emptydir-hostpath.md), [PV e PVC](../04-storage/pv-pvc.md) e [StorageClass](../04-storage/storageclass.md)

> **Tarefa:** crie um PVC `notas` e um Pod que acrescente a data num arquivo do volume ao iniciar. Apague o Pod, crie de novo e confira que o arquivo tem as duas linhas.

??? success "Solução"
    ```yaml
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata: {name: notas, namespace: estudo}
    spec: {accessModes: [ReadWriteOnce], resources: {requests: {storage: 1Gi}}}
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: escritor, namespace: estudo}
    spec:
      containers:
      - name: c
        image: busybox:1.36
        command: [sh, -c, 'date >> /dados/notas.txt; sleep 3600']
        volumeMounts: [{name: d, mountPath: /dados}]
      volumes: [{name: d, persistentVolumeClaim: {claimName: notas}}]
    ```

    ```console
    $ kubectl -n estudo exec escritor -- cat /dados/notas.txt
    Sun Oct 25 09:48:00 UTC 2026
    Sun Oct 25 09:48:06 UTC 2026
    ```

    A segunda linha veio do Pod novo: o dado ficou no PVC, não no Pod.

## 4. Requests, limits e QoS

**Leia:** [Requests, limits e QoS](../02-workloads-scheduling/requests-limits-qos.md)

> **Tarefa:** crie um Pod com classe de QoS `Guaranteed` e outro `BestEffort`, e confira a classe de cada um.

??? success "Solução"
    `Guaranteed` exige requests iguais aos limits, de CPU e memória:

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata: {name: qos, namespace: estudo}
    spec:
      containers:
      - name: qos
        image: nginx:1.27
        resources:
          requests: {cpu: 100m, memory: 64Mi}
          limits: {cpu: 100m, memory: 64Mi}
    ```

    ```bash
    kubectl -n estudo run qos2 --image=nginx:1.27                       # sem resources = BestEffort
    kubectl -n estudo get pod qos -o jsonpath='{.status.qosClass}'      # Guaranteed
    kubectl -n estudo get pod qos2 -o jsonpath='{.status.qosClass}'     # BestEffort
    ```

## 5. kubectl essencial

**Leia:** [Comandos de memória](comandos-de-memoria.md)

> **Tarefa:** liste o nome e o nó de cada Pod do namespace `estudo`, um por linha, e descubra com `kubectl explain` o nome do campo que define a política de reinício de um Pod.

??? success "Solução"
    ```bash
    kubectl -n estudo get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\n"}{end}'
    kubectl explain pod.spec | grep -i restart      # restartPolicy
    ```

## 6. Deployments: rollout, rollback e scale

**Leia:** [Deployments: rollout, rollback e scale](../02-workloads-scheduling/deployments-rollout.md)

> **Tarefa:** atualize o Deployment `loja` para `nginx:1.28`, acompanhe o rollout e depois volte para a versão anterior.

??? success "Solução"
    ```bash
    kubectl -n estudo set image deploy/loja nginx=nginx:1.28
    kubectl -n estudo rollout status deploy/loja
    kubectl -n estudo rollout history deploy/loja
    kubectl -n estudo rollout undo deploy/loja
    kubectl -n estudo get deploy loja -o jsonpath='{.spec.template.spec.containers[0].image}'   # nginx:1.27
    ```

    O `nginx` em `nginx=nginx:1.28` é o nome do **container**, que o `kubectl create deployment` tirou da imagem.

## 7. Services e DNS

**Leia:** [Services e Endpoints](../03-services-networking/services-endpoints.md) e [DNS do cluster](../03-services-networking/dns.md)

> **Tarefa:** a partir de um Pod no namespace `default`, chame o Service `loja` do namespace `estudo`. Primeiro pelo nome curto (deve falhar), depois do jeito certo.

??? success "Solução"
    ```bash
    kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 3 http://loja         # bad address 'loja'
    kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 3 http://loja.estudo  # responde
    ```

    O nome curto só resolve no mesmo namespace. De fora, use `<service>.<namespace>`.

## 8. Scheduling: nodeSelector, taints e affinity

**Leia:** [Taints, tolerations e nodeSelector](../02-workloads-scheduling/taints-tolerations-nodeselector.md) e [Affinity](../02-workloads-scheduling/affinity.md)

> **Tarefa:** rotule um worker com `disco=ssd` e crie um Pod que só possa rodar em nós com esse label.

??? success "Solução"
    ```bash
    kubectl label node <worker> disco=ssd
    kubectl -n estudo run ssd --image=nginx:1.27 --overrides='{"spec":{"nodeSelector":{"disco":"ssd"}}}'
    kubectl -n estudo get pod ssd -o wide     # NODE = o worker rotulado
    ```

    Sem nenhum nó com o label, o Pod fica `Pending` com `didn't match Pod's node affinity/selector`.

## 9. RBAC

**Leia:** [RBAC](../01-cluster-architecture/rbac.md)

> **Tarefa:** crie uma ServiceAccount `leitor` que só possa listar e ler Pods no namespace `estudo`, e prove com `kubectl auth can-i`.

??? success "Solução"
    ```bash
    kubectl -n estudo create serviceaccount leitor
    kubectl -n estudo create role ler-pods --verb=get,list --resource=pods
    kubectl -n estudo create rolebinding leitor-ler --role=ler-pods --serviceaccount=estudo:leitor
    kubectl auth can-i list pods -n estudo --as=system:serviceaccount:estudo:leitor     # yes
    kubectl auth can-i delete pods -n estudo --as=system:serviceaccount:estudo:leitor   # no
    kubectl auth can-i list pods -n default --as=system:serviceaccount:estudo:leitor    # no
    ```

## 10. NetworkPolicy

**Leia:** [NetworkPolicy](../03-services-networking/network-policy.md)

> **Tarefa:** faça os Pods `app=loja` aceitarem tráfego só de Pods com o label `papel=frontend`. Teste com e sem o label.

??? success "Solução"
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata: {name: loja-so-frontend, namespace: estudo}
    spec:
      podSelector: {matchLabels: {app: loja}}
      policyTypes: [Ingress]
      ingress:
      - from: [{podSelector: {matchLabels: {papel: frontend}}}]
        ports: [{port: 80}]
    ```

    ```bash
    kubectl -n estudo run t1 --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 5 http://loja                       # download timed out
    kubectl -n estudo run t2 --rm -it --restart=Never --image=busybox:1.36 --labels=papel=frontend -- wget -qO- -T 5 http://loja # responde
    ```

    O CNI precisa aplicar NetworkPolicy (o Calico do lab aplica; o Flannel sozinho não). Sem isso, a política é criada e não tem efeito.

## 11. Troubleshooting

**Leia:** a trilha [Treinar troubleshooting](troubleshooting/index.md), começando por [Pod não inicia](troubleshooting/pod-nao-inicia.md)

> **Tarefa:** crie um Pod com a imagem `nginx:1.27-naoexiste`, descubra pelo `describe` por que ele não sobe e corrija sem apagar o Pod.

??? success "Solução"
    ```bash
    kubectl -n estudo run quebrado --image=nginx:1.27-naoexiste
    kubectl -n estudo describe pod quebrado | tail -5          # Failed to pull image ... not found
    kubectl -n estudo set image pod/quebrado quebrado=nginx:1.27
    kubectl -n estudo get pod quebrado                         # Running
    ```

    O `kubectl run` usa o nome do Pod como nome do container, por isso `quebrado=nginx:1.27`.

## 12. Operar o cluster: etcd, upgrade, Helm e Kustomize

**Leia:** [Backup e restore do etcd](../01-cluster-architecture/etcd-backup-restore.md), [Upgrade com kubeadm](../01-cluster-architecture/upgrade-kubeadm.md) e [Helm e Kustomize](../01-cluster-architecture/helm-kustomize.md)

Backup do etcd e upgrade precisam de um cluster kubeadm com acesso aos nós (o lab ou o Killercoda). A tarefa abaixo funciona em qualquer cluster.

> **Tarefa:** com Kustomize, gere a partir de um Deployment `loja` uma versão com prefixo `prod-`, no namespace `estudo` e com o label `ambiente=prod`, e aplique.

??? success "Solução"
    ```bash
    mkdir -p kz/base
    kubectl create deployment loja --image=nginx:1.27 --dry-run=client -o yaml > kz/base/deploy.yaml
    cat > kz/kustomization.yaml <<'EOF'
    resources:
    - base/deploy.yaml
    namePrefix: prod-
    namespace: estudo
    labels:
    - pairs:
        ambiente: prod
    EOF
    kubectl kustomize kz          # mostra o YAML final sem aplicar
    kubectl apply -k kz
    kubectl -n estudo get deploy prod-loja --show-labels   # ambiente=prod,app=loja
    ```

## E depois?

Com os 12 passos feitos, siga pelos domínios na ordem do menu, ou vá para a [Revisão rápida](revisao-rapida.md) quando a prova estiver perto.
