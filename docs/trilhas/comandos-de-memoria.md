# Comandos de memória

> **Versão do Kubernetes:** v1.37 · **Última revisão:** 2026-10-25 · Folha de revisão para a semana da prova

Os comandos que aparecem em quase toda questão. Cada um foi rodado no lab (kubeadm v1.37.1, 1 control plane + 2 workers); as páginas dos domínios explicam o contexto de cada um.

## Contexto e namespace

Toda questão da prova começa dizendo em qual cluster trabalhar. **Rode o comando de troca de contexto que vem no enunciado antes de qualquer outra coisa.**

```bash
kubectl config get-contexts                          # lista; o * marca o atual
kubectl config use-context <contexto>                # troca de cluster
kubectl config set-context --current --namespace=shop  # namespace padrão do contexto atual
kubectl config view --minify -o jsonpath='{..namespace}'  # qual namespace está valendo
```

## Descobrir campos e recursos

```bash
kubectl explain pod.spec.containers.resources        # documentação de um campo
kubectl explain deploy.spec.strategy --recursive     # árvore completa de campos
kubectl api-resources                                # nome curto, apiVersion, se é namespaced
kubectl api-resources --namespaced=false             # recursos do cluster inteiro (nodes, pv...)
```

`kubectl explain` é a documentação offline: serve quando você lembra do objeto, mas não do nome exato do campo.

## Ver objetos

```bash
kubectl get pods -o wide                             # IP e nó de cada Pod
kubectl get pods -A                                  # todos os namespaces
kubectl get pod db -o yaml                           # o objeto completo, como está no cluster
kubectl describe pod db                              # estado + Events no final
kubectl get pods -w                                  # acompanhar mudanças (Ctrl+C sai)
```

## Gerar YAML sem escrever do zero

```bash
kubectl run web --image=nginx --dry-run=client -o yaml > pod.yaml
kubectl create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml
kubectl expose deployment web --port=80 --target-port=8080 --type=NodePort --dry-run=client -o yaml
kubectl create configmap cm --from-literal=a=1 --dry-run=client -o yaml
kubectl create secret generic s1 --from-literal=senha=abc123 --dry-run=client -o yaml
kubectl create job j --image=busybox --dry-run=client -o yaml -- echo oi
kubectl create cronjob c --image=busybox --schedule='*/5 * * * *' --dry-run=client -o yaml -- date
kubectl create role ler-pods --verb=get,list --resource=pods --dry-run=client -o yaml
kubectl create rolebinding leitor-ler --role=ler-pods --serviceaccount=shop:leitor --dry-run=client -o yaml
```

Atalho para digitar menos: `export do="--dry-run=client -o yaml"` e depois `kubectl run web --image=nginx $do`.

## Mudar objetos

```bash
kubectl apply -f arquivo.yaml
kubectl set image deploy/web nginx=nginx:1.28        # nginx = nome do container
kubectl scale deploy/web --replicas=3
kubectl rollout status deploy/web
kubectl rollout history deploy/web
kubectl rollout undo deploy/web                      # volta para a revisão anterior
kubectl replace --force -f pod.yaml                  # apaga e recria (campo imutável)
```

A maioria dos campos de um Pod não muda depois de criado. O `apply` recusa com esta mensagem (saída real, v1.37.1, depois de acrescentar uma porta ao container; o diff que o kubectl imprime em seguida foi cortado):

```console
$ kubectl apply -f e.yaml
The Pod "e" is invalid: spec: Forbidden: pod updates may not change fields other than `spec.containers[*].image`,`spec.initContainers[*].image`,`spec.activeDeadlineSeconds`,`spec.tolerations` (only additions to existing tolerations),`spec.terminationGracePeriodSeconds` (allow it to be set to 1 if it was previously negative)
```

Nesse caso, `kubectl replace --force -f` apaga o Pod e cria de novo com o arquivo.

Um arquivo tirado de `kubectl get pod db -o yaml` traz `resourceVersion`, `uid` e `status`. Editar esse arquivo e rodar `apply` costuma dar `Error from server (Conflict)`. Para recriar, use `replace --force`. Para um objeto novo, gere o YAML com `--dry-run=client -o yaml`.

## Labels e seletores

```bash
kubectl get pods --show-labels
kubectl get pods -l app=web                          # igual
kubectl get pods -l app!=web                         # diferente
kubectl get pods -l 'app in (web,db)'                # um dos valores
kubectl get pods -L app,tier                         # label como coluna
kubectl label pod db env=prod                        # adicionar
kubectl label pod db env=dev --overwrite             # trocar (sem --overwrite dá erro)
kubectl label pod db env-                            # remover (o "-" no fim)
```

## Logs, exec e Pod temporário

```bash
kubectl logs db                                      # container único
kubectl logs db -c sidecar                           # Pod com mais de um container
kubectl logs db --previous                           # execução anterior (CrashLoopBackOff)
kubectl logs -l app=web --tail=20 --prefix           # todos os Pods do label
kubectl logs deploy/web                              # ATENÇÃO: só um dos Pods
kubectl exec db -- redis-cli ping                    # comando avulso
kubectl exec -it db -- sh                            # shell
kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 3 http://web
kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 -- nslookup web.shop.svc.cluster.local
```

O Pod temporário (`--rm`) testa Service e DNS de dentro do cluster e é apagado no fim. `logs deploy/web` avisa `Found 2 pods, using pod/web-...` e mostra só um. Para ver todos, use `-l`.

## Eventos

```bash
kubectl get events --sort-by=.lastTimestamp          # do mais antigo para o mais novo
kubectl get events --field-selector type=Warning     # só problemas
kubectl events --for pod/quebrado                    # eventos de um objeto
```

## Permissões (RBAC)

```bash
kubectl auth can-i list pods --as=system:serviceaccount:shop:leitor   # yes / no
kubectl auth can-i list pods -n default --as=system:serviceaccount:shop:leitor
kubectl auth can-i --list --as=system:serviceaccount:shop:leitor      # tudo o que pode
kubectl auth can-i create deployments --as=maria -n shop              # usuário
```

O formato de uma ServiceAccount no `--as` é `system:serviceaccount:<namespace>:<nome>`.

## jsonpath e colunas

```bash
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\n"}{end}'
kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'
kubectl get pod db -o jsonpath='{.spec.containers[0].image}'
kubectl get secret s1 -o jsonpath='{.data.senha}' | base64 -d
kubectl get pods -o custom-columns=NOME:.metadata.name,NO:.spec.nodeName
kubectl get pods --sort-by=.metadata.creationTimestamp
```

Saída real do `range` (nome e nó, um por linha):

```console
$ kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\n"}{end}'
db	w1
web-69c6f74b8b-l7c92	w2
web-69c6f74b8b-w2cfw	w1
```

Para descobrir o caminho de um campo, rode `kubectl get <objeto> -o yaml` e siga a indentação: `spec:` → `containers:` (lista, por isso `[0]`) → `image:`.

## Pegadinhas

- **Contexto errado.** Resposta certa no cluster errado vale zero.
- **Namespace esquecido.** Sem `-n`, o comando vai para o namespace do contexto. Confira com `kubectl config view --minify`.
- **`--dry-run` sem `=client`.** Use sempre `--dry-run=client -o yaml`.
- **`--` antes do comando** em `kubectl run`, `create job` e `exec`: tudo depois do `--` é o comando do container.
- **Gravar a saída no arquivo pedido.** "Write the result to /opt/..." confere o arquivo: `kubectl ... > /opt/arquivo`.
