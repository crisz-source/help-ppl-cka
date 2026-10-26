# RBAC

> **Versão do Kubernetes:** v1.37 · **Última revisão:** 2026-10-25 · **Domínio:** Cluster Architecture, Installation & Configuration (25%)

## O que é

RBAC (Role-Based Access Control) é o modelo de **autorização** padrão do Kubernetes. Ele responde a uma pergunta: *"este usuário/ServiceAccount pode fazer este verbo neste recurso, neste namespace?"*.

São quatro objetos, em dois pares:

| Define permissões | Concede permissões | Escopo |
|---|---|---|
| `Role` | `RoleBinding` | Um namespace |
| `ClusterRole` | `ClusterRoleBinding` | O cluster inteiro |

- **Role / ClusterRole** = lista de regras (*quais verbos em quais recursos*). Não diz para quem.
- **RoleBinding / ClusterRoleBinding** = liga um papel a **sujeitos** (`User`, `Group` ou `ServiceAccount`).

RBAC é **somente aditivo**: não existe regra de "negar". Se nenhuma regra permite, a ação é negada.

Na prova, RBAC costuma aparecer como: "crie uma ServiceAccount, dê permissão X em um namespace e confirme".

## Como funciona por dentro

Toda requisição passa pelo **kube-apiserver** em três etapas, nesta ordem:

[![RBAC: o caminho de uma requisição](../assets/diagramas/01-rbac.svg)](../assets/diagramas/01-rbac.svg "Abrir o diagrama em tamanho real")

1. **Autenticação**: o API server identifica o sujeito (certificado de cliente, token de ServiceAccount, OIDC). Kubernetes **não tem objeto `User`**: usuário é só um nome que vem do certificado (campo `CN`) ou do token. Grupos vêm do campo `O` do certificado.
2. **Autorização**: os autorizadores configurados em `--authorization-mode` (no kubeadm: `Node,RBAC`) avaliam a requisição. O RBAC lê os Roles e Bindings, que ficam no etcd como qualquer outro objeto.
3. **Admission**: só depois de autorizada a requisição passa pelos admission controllers.

ServiceAccounts são autenticadas com o nome `system:serviceaccount:<namespace>:<nome>`. Isso importa para o `--as` do `kubectl auth can-i`.

Um detalhe que cai muito: um **RoleBinding pode referenciar uma ClusterRole**. As permissões valem só no namespace do RoleBinding. Assim você reaproveita papéis prontos como `view` e `edit` sem recriá-los em cada namespace.

## Comandos essenciais

```bash
# Criar uma ServiceAccount
kubectl create serviceaccount app-sa -n dev

# Role: verbos separados por vírgula, recursos no plural
kubectl create role pod-reader --verb=get,list,watch --resource=pods -n dev

# Role para recursos de outro apiGroup (deployments estão em "apps")
kubectl create role deploy-mgr --verb=get,list,create,update --resource=deployments -n dev

# Restringir a um objeto específico pelo nome
kubectl create role cm-reader --verb=get --resource=configmaps --resource-name=app-config -n dev

# Subrecurso (ler logs de pods)
kubectl create role log-reader --verb=get --resource=pods/log -n dev

# ClusterRole (sem -n: é cluster-scoped)
kubectl create clusterrole node-reader --verb=get,list,watch --resource=nodes

# RoleBinding para um usuário
kubectl create rolebinding jane-pod-reader --role=pod-reader --user=jane -n dev

# RoleBinding para uma ServiceAccount (formato namespace:nome)
kubectl create rolebinding app-sa-reader --role=pod-reader --serviceaccount=dev:app-sa -n dev

# RoleBinding apontando para uma ClusterRole: permissão vale só em "dev"
kubectl create rolebinding app-sa-view --clusterrole=view --serviceaccount=dev:app-sa -n dev

# ClusterRoleBinding: permissão em todos os namespaces
kubectl create clusterrolebinding ops-nodes --clusterrole=node-reader --group=ops

# Testar permissões se passando por outro sujeito
kubectl auth can-i list pods -n dev --as=jane
kubectl auth can-i create deployments -n dev --as=system:serviceaccount:dev:app-sa

# Listar tudo o que um sujeito pode fazer no namespace
kubectl auth can-i --list -n dev --as=system:serviceaccount:dev:app-sa

# Gerar YAML para revisar/editar antes de aplicar
kubectl create role pod-reader --verb=get,list --resource=pods -n dev --dry-run=client -o yaml > role.yaml

# Descobrir o apiGroup e o nome exato de um recurso
kubectl api-resources | grep -i deploy
```

Use `--dry-run=client -o yaml` quando o enunciado pedir algo que os flags imperativos não cobrem, como várias regras com apiGroups diferentes no mesmo Role. Gere a base e edite.

## YAML de referência

??? example "YAML completo: Role + RoleBinding"

    ```yaml
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: deploy-mgr
      namespace: dev              # Role sempre tem namespace
    rules:
      - apiGroups: ["apps"]       # "" = core (pods, services, configmaps...); "apps" = deployments, statefulsets...
        resources: ["deployments"]
        verbs: ["get", "list", "create", "update"]
      - apiGroups: [""]
        resources: ["pods", "pods/log"]   # subrecurso usa "recurso/subrecurso"
        verbs: ["get", "list"]
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: deploy-mgr-binding
      namespace: dev              # a permissão vale neste namespace
    subjects:
      - kind: ServiceAccount
        name: app-sa
        namespace: dev            # obrigatório para ServiceAccount
      - kind: User
        name: jane                # User e Group usam apiGroup rbac.authorization.k8s.io
        apiGroup: rbac.authorization.k8s.io
    roleRef:                      # imutável depois de criado
      kind: Role                  # ou ClusterRole
      name: deploy-mgr
      apiGroup: rbac.authorization.k8s.io
    ```

## ServiceAccount nos Pods

O RBAC diz **o que** a ServiceAccount pode fazer. Esta parte mostra **como um Pod usa** a ServiceAccount, assunto da página oficial *Configure Service Accounts for Pods*. Tudo abaixo foi rodado no lab (v1.37.1, namespace `sa-lab`).

**Todo Pod tem uma ServiceAccount.** Sem `serviceAccountName`, ele usa a `default`, que existe em todo namespace, e recebe um token montado em `/var/run/secrets/kubernetes.io/serviceaccount`:

```console
$ kubectl -n sa-lab create serviceaccount app-sa
serviceaccount/app-sa created
$ kubectl -n sa-lab get serviceaccounts
NAME      AGE
app-sa    0s
default   0s
$ kubectl -n sa-lab get pod sem-sa -o jsonpath='{.spec.serviceAccountName}{"\n"}'
default
$ kubectl -n sa-lab exec sem-sa -- ls /var/run/secrets/kubernetes.io/serviceaccount
ca.crt
namespace
token
```

O token não é um Secret: vem de um volume `projected`, com validade curta, que o kubelet renova sozinho:

```console
$ kubectl -n sa-lab get pod sem-sa -o yaml | sed -n '/^  volumes:/,/^status:/p'
  volumes:
  - name: kube-api-access-4ls6m
    projected:
      defaultMode: 420
      sources:
      - serviceAccountToken:
          expirationSeconds: 3607
          path: token
      - configMap:
          items:
          - key: ca.crt
            path: ca.crt
          name: kube-root-ca.crt
      - downwardAPI:
          items:
          - fieldRef:
              apiVersion: v1
              fieldPath: metadata.namespace
            path: namespace
status:
```

**Usar outra ServiceAccount** é um campo do `spec` do Pod:

```yaml
apiVersion: v1
kind: Pod
metadata: {name: cliente, namespace: sa-lab}
spec:
  serviceAccountName: app-sa          # precisa existir antes do Pod
  containers:
  - name: c
    image: curlimages/curl:8.11.1
    command: [sleep, "3600"]
```

De dentro do Pod, o token autentica na API como `system:serviceaccount:sa-lab:app-sa`. Sem RBAC, só a autenticação passa; a ação é negada:

```console
$ kubectl -n sa-lab exec cliente -- sh -c 'TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token); curl -s --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/sa-lab/pods'
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "pods is forbidden: User \"system:serviceaccount:sa-lab:app-sa\" cannot list resource \"pods\" in API group \"\" in the namespace \"sa-lab\"",
  "reason": "Forbidden",
  "details": {
    "kind": "pods"
  },
  "code": 403
}
```

Com `kubectl create role pod-reader --verb=get,list --resource=pods` e um RoleBinding para `sa-lab:app-sa`, a mesma chamada passa a devolver a lista (`"kind": "PodList"`).

**Trocar a ServiceAccount** de um Pod que já existe não funciona: o campo é imutável. Em Deployment funciona, porque o template muda e os Pods são recriados:

```console
$ kubectl -n sa-lab set serviceaccount pod/sem-sa app-sa
error: failed to patch ServiceAccountName Pod "sem-sa" is invalid: spec: Forbidden: pod updates may not change fields other than `spec.containers[*].image`,`spec.initContainers[*].image`,`spec.activeDeadlineSeconds`,`spec.tolerations` (only additions to existing tolerations),`spec.terminationGracePeriodSeconds` (allow it to be set to 1 if it was previously negative)
$ kubectl -n sa-lab set serviceaccount deployment/web app-sa
deployment.apps/web serviceaccount updated
$ kubectl -n sa-lab get pods -l app=web -o jsonpath='{.items[*].spec.serviceAccountName}{"\n"}'
app-sa
```

(O `set serviceaccount` no Pod também imprime um diff do `spec`, cortado aqui.)

**Não montar o token**, para Pods que não falam com a API: `automountServiceAccountToken: false` na ServiceAccount ou no Pod. Se os dois disserem coisas diferentes, **vale o do Pod**. No lab, com a ServiceAccount `sem-token` marcada como `false`, o Pod `p1` ficou sem a pasta e o `p2`, com `automountServiceAccountToken: true` no próprio spec, recebeu o token:

```console
$ kubectl -n sa-lab exec p1 -- ls /var/run/secrets/kubernetes.io/serviceaccount
ls: cannot access '/var/run/secrets/kubernetes.io/serviceaccount': No such file or directory
command terminated with exit code 2
$ kubectl -n sa-lab exec p2 -- ls /var/run/secrets/kubernetes.io/serviceaccount
ca.crt
namespace
token
```

**Token para usar fora do cluster:** `kubectl create token` emite um token com validade (padrão de 1 hora; `--duration` muda). O conteúdo do token mostra para quem ele foi emitido:

```console
$ TOKEN=$(kubectl -n sa-lab create token app-sa --duration=10m)
$ echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
{
    "aud": [
        "https://kubernetes.default.svc.cluster.local"
    ],
    "exp": 1792973427,
    "iat": 1792972827,
    "iss": "https://kubernetes.default.svc.cluster.local",
    "jti": "20b5658b-9ce4-485e-a24c-fc7eb29f9d05",
    "kubernetes.io": {
        "namespace": "sa-lab",
        "serviceaccount": {
            "name": "app-sa",
            "uid": "c5a48ef3-e21b-457d-929d-d5e055ab3d2f"
        }
    },
    "nbf": 1792972827,
    "sub": "system:serviceaccount:sa-lab:app-sa"
}
```

Para testar esse token com o `kubectl`, use um kubeconfig vazio. Com o kubeconfig do admin, o certificado de cliente dele continua sendo enviado e **vence o `--token`**: o `auth whoami` respondeu `kubernetes-admin`. Do jeito certo:

```console
$ kubectl --kubeconfig=/dev/null --server=https://10.0.1.4:6443 --certificate-authority=/etc/kubernetes/pki/ca.crt --token="$TOKEN" auth whoami
ATTRIBUTE                                           VALUE
Username                                            system:serviceaccount:sa-lab:app-sa
UID                                                 c5a48ef3-e21b-457d-929d-d5e055ab3d2f
Groups                                              [system:serviceaccounts system:serviceaccounts:sa-lab system:authenticated]
Extra: authentication.kubernetes.io/credential-id   [JTI=76356014-3a5c-483c-8c79-065bf6b03a47]
```

O token que esse `whoami` usou foi emitido logo antes, com o mesmo comando; por isso o `JTI` é outro.

**Token de longa duração**, sem validade, quando um sistema externo precisa: um Secret do tipo `kubernetes.io/service-account-token` com a anotação da ServiceAccount. O controlador preenche `token`, `ca.crt` e `namespace`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-sa-token
  namespace: sa-lab
  annotations:
    kubernetes.io/service-account.name: app-sa
type: kubernetes.io/service-account-token
```

```console
$ kubectl -n sa-lab get secret app-sa-token
NAME           TYPE                                  DATA   AGE
app-sa-token   kubernetes.io/service-account-token   3      2s
```

Se a anotação aponta para uma ServiceAccount que não existe, o `apply` responde `created`, mas o controlador apaga o Secret em seguida: 3 segundos depois, `kubectl get secret` deu `NotFound`.

## Na documentação oficial

- **Página:** *Using RBAC Authorization*. Link: <https://kubernetes.io/docs/reference/access-authn-authz/rbac/>
- **Busca rápida:** `rbac`
- **Ctrl+F dentro da página:**
    - `kind: Role`: exemplo de Role pronto para copiar.
    - `kind: RoleBinding`: exemplo de binding com `subjects` e `roleRef`.
    - `kubectl create role`: seção com os comandos imperativos.
    - `system:serviceaccount`: formato do nome de ServiceAccount.
    - `User-facing roles`: tabela das ClusterRoles padrão (`cluster-admin`, `admin`, `edit`, `view`).
- **Página:** *Configure Service Accounts for Pods*. Link: <https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/>
- **Ctrl+F dentro da página:**
    - `automountServiceAccountToken`: desligar o token montado (na ServiceAccount ou no Pod).
    - `serviceAccountName`: usar outra ServiceAccount no Pod.
    - `kubectl create token`: token com validade.
    - `service-account-token`: Secret com token de longa duração.
    - `serviceAccountToken`: volume projetado com `audience` e `expirationSeconds` próprios.

## Pegadinhas da prova

- **`roleRef` é imutável.** Para trocar o papel de um binding, apague e recrie. `kubectl edit` ou `patch` falham (saída real, v1.37.1):

    ```console
    The RoleBinding "jane-pod-reader" is invalid: roleRef: Invalid value: {"APIGroup":"rbac.authorization.k8s.io","Kind":"Role","Name":"deploy-mgr"}: field is immutable
    ```

- **ClusterRoleBinding não aceita Role**, só ClusterRole. Já o RoleBinding aceita os dois. A API recusa:

    ```console
    The ClusterRoleBinding "crb-com-role" is invalid: roleRef.kind: Unsupported value: "Role": supported values: "ClusterRole"
    ```

- **apiGroup errado.** `deployments` fica em `apps`, não em `""`. Se `can-i` responder `no` quando deveria ser `yes`, confira o apiGroup com `kubectl api-resources`.
- **Recurso no singular.** Em YAML o campo `resources` usa o plural minúsculo (`pods`, não `Pod`).
- **`--serviceaccount` usa `namespace:nome`**, não só o nome. E `--as` usa `system:serviceaccount:namespace:nome`.
- **`serviceAccountName` de Pod é imutável.** Para trocar, recrie o Pod (`kubectl replace --force -f pod.yaml`) ou mude no Deployment (`kubectl set serviceaccount deployment/<nome> <sa>`).
- **ServiceAccount inexistente** impede a criação do Pod: `pods "x" is forbidden: error looking up service account sa-lab/nao-existe: serviceaccount "nao-existe" not found`. Crie a ServiceAccount primeiro.
- **`automountServiceAccountToken` no Pod vence o da ServiceAccount.** Se a questão pede "este Pod não deve ter token", ponha `false` no Pod.
- **Namespace esquecido** no Role ou no RoleBinding: os objetos vão para `default` e a permissão não vale onde a questão pediu.
- **Contexto do kubectl.** Toda questão começa com um `kubectl config use-context ...`. Rode antes de qualquer coisa.
- **PodSecurityPolicy** aparece em material antigo como "controle de acesso de Pods". Foi **removida na v1.25** e substituída por **Pod Security Admission** (labels `pod-security.kubernetes.io/*` no namespace). Não é RBAC.

## Pratique

**Enunciado (como na prova):**

> Create a new ServiceAccount named `deploy-bot` in the namespace `ops`. Create a Role named `deploy-bot-role` in the same namespace that allows only `get`, `list`, `create` and `update` on `deployments`. Bind the Role to the ServiceAccount using a RoleBinding named `deploy-bot-binding`.

**Tradução:** crie uma ServiceAccount `deploy-bot` no namespace `ops`. Crie um Role `deploy-bot-role` no mesmo namespace que permita somente `get`, `list`, `create` e `update` em `deployments`. Ligue o Role à ServiceAccount com um RoleBinding chamado `deploy-bot-binding`.

??? success "Solução"
    ```bash
    kubectl create namespace ops   # só se ainda não existir
    kubectl create serviceaccount deploy-bot -n ops
    kubectl create role deploy-bot-role -n ops \
      --verb=get,list,create,update --resource=deployments
    kubectl create rolebinding deploy-bot-binding -n ops \
      --role=deploy-bot-role --serviceaccount=ops:deploy-bot
    ```

**Como verificar:**

```bash
kubectl auth can-i create deployments -n ops --as=system:serviceaccount:ops:deploy-bot   # yes
kubectl auth can-i delete deployments -n ops --as=system:serviceaccount:ops:deploy-bot   # no
kubectl auth can-i list deployments -n default --as=system:serviceaccount:ops:deploy-bot # no
kubectl describe role deploy-bot-role -n ops   # o recurso aparece como deployments.apps
```

??? tip "No lab / Killercoda"

    - Gere um certificado de usuário com a API `CertificateSigningRequest` (`kubectl certificate approve`), monte um kubeconfig para ele e teste o RBAC de verdade, sem `--as`.
    - Crie um Pod com `serviceAccountName: deploy-bot` e, de dentro dele, chame a API com o token montado em `/var/run/secrets/kubernetes.io/serviceaccount/token`.
    - Faça um RoleBinding para a ClusterRole `view` e compare `kubectl auth can-i --list` antes e depois.
