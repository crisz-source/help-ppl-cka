# Aplicação não responde

> **Versão do Kubernetes:** v1.37 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 4 cenários

Os Pods estão `Running`, mas a chamada à aplicação falha. O teste é sempre de **dentro** do cluster, com um Pod temporário:

```bash
kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 3 http://api
```

O erro do `wget` já aponta a camada:

| Erro | Camada | Cenário |
|---|---|---|
| `bad address 'api'` | DNS | [Nome de outro namespace](#nome-de-outro-namespace) |
| `Connection refused` | Service | [Selector errado](#service-sem-endpoints-selector-errado) ou [targetPort errado](#targetport-errado) |
| `download timed out` | NetworkPolicy | [Tráfego bloqueado](#networkpolicy-bloqueando) |

Neste laboratório (kubeadm v1.37.1, Calico), o Deployment `api` (nginx, porta 80, label `app=api`) roda no namespace `ts`.

## Service sem endpoints: selector errado

1. **Sintoma:** `wget: can't connect to remote host (10.111.191.15): Connection refused`.
2. **Primeiro comando:** `kubectl get endpointslices -l kubernetes.io/service-name=api-errado`
3. **Evidência:** a lista de endpoints está vazia, e o selector não bate com os labels dos Pods:

    ```console
    $ kubectl get endpointslices -l kubernetes.io/service-name=api-errado
    NAME               ADDRESSTYPE   PORTS     ENDPOINTS   AGE
    api-errado-ngr4v   IPv4          <unset>   <unset>     3s
    $ kubectl describe svc api-errado | grep -E 'Selector|Endpoints'
    Selector:                 app=api-errado
    Endpoints:
    $ kubectl get pods -l app=api --show-labels
    NAME                   READY   STATUS    RESTARTS   AGE   LABELS
    api-7c5b468964-qh27q   1/1     Running   0          4s    app=api,pod-template-hash=7c5b468964
    ```

4. **Causas prováveis:** selector com outro label (o `kubectl create service` inventa `app=<nome-do-service>`), Service em outro namespace, ou Pods que não estão Ready (readinessProbe falhando).
5. **Correção:** `kubectl patch svc api-errado -p '{"spec":{"selector":{"app":"api"}}}'`
6. **Validar:** o EndpointSlice passa a listar os IPs dos Pods (`10.244.190.127,10.244.80.214`) e o `wget` devolve a página.

## targetPort errado

1. **Sintoma:** também `Connection refused`.
2. **Primeiro comando:** o mesmo, `kubectl get endpointslices -l kubernetes.io/service-name=api-porta`
3. **Evidência:** agora **há** endpoints, mas na porta errada (o nginx escuta na 80):

    ```console
    $ kubectl get endpointslices -l kubernetes.io/service-name=api-porta
    NAME              ADDRESSTYPE   PORTS   ENDPOINTS                      AGE
    api-porta-4pkkd   IPv4          8080    10.244.190.127,10.244.80.214   7s
    ```

4. **Causas prováveis:** `targetPort` diferente da porta em que o container escuta. Sem `targetPort`, ele assume o valor de `port`.
5. **Correção:** `kubectl patch svc api-porta -p '{"spec":{"ports":[{"port":80,"targetPort":80}]}}'`
6. **Validar:** a coluna `PORTS` mostra `80` e o `wget` responde.

A diferença entre os dois cenários está toda no EndpointSlice: **vazio** = selector; **com IPs, porta errada** = targetPort.

## Nome de outro namespace

1. **Sintoma:** de um Pod no namespace `default`: `wget: bad address 'api'`.
2. **Primeiro comando:** `cat /etc/resolv.conf` dentro do Pod de teste.
3. **Evidência:** a busca começa pelo namespace **do Pod**:

    ```console
    search default.svc.cluster.local svc.cluster.local cluster.local j0nzkcbsfnuubgfdcrqy4sr45f.nx.internal.cloudapp.net
    nameserver 10.96.0.10
    options ndots:5
    ```

    `api` vira `api.default.svc.cluster.local`, que não existe. (O último domínio é o da rede da Azure, herdado do nó.)

4. **Causas prováveis:** nome curto usado a partir de outro namespace, ou nome do Service digitado errado.
5. **Correção:** usar `api.ts` (Service + namespace) ou o FQDN `api.ts.svc.cluster.local`.
6. **Validar:** `wget -qO- -T 3 http://api.ts` devolve a página.

Cuidado com o `nslookup` do busybox: no teste, `nslookup api.ts` também respondeu `NXDOMAIN`, enquanto o `wget` resolveu o mesmo nome. Para testar DNS com `nslookup`, use o FQDN completo.

## NetworkPolicy bloqueando

1. **Sintoma:** `wget: download timed out`. O `wget` espera e desiste; não há recusa.
2. **Primeiro comando:** `kubectl get networkpolicy -n ts` e `kubectl describe networkpolicy <nome>`
3. **Evidência:**

    ```console
    $ kubectl describe networkpolicy api-so-frontend
      PodSelector:     app=api
      Allowing ingress traffic:
        To Port: 80/TCP
        From:
          PodSelector: papel=frontend
      Not affecting egress traffic
      Policy Types: Ingress
    ```

    Só Pods com o label `papel=frontend` podem chegar aos Pods `app=api`.

4. **Causas prováveis:** a origem não tem o label liberado, está em outro namespace sem `namespaceSelector`, ou a política libera a porta do Service em vez da porta do container.
5. **Correção:** depende do enunciado. Dar à origem o label liberado, ou acrescentar uma regra para ela. Não apague a política se a questão não pedir.
6. **Validar:** o Pod de teste com o label passa: `kubectl run tmp --rm -it --restart=Never --image=busybox:1.36 --labels=papel=frontend -- wget -qO- -T 5 http://api`.

## Ingress ou Gateway mal configurado

Esses dois não foram reproduzidos aqui, porque precisam de um controller instalado. As respostas do controller dizem a causa: **404** = nenhuma regra casou (host ou path); **503** = a regra casou, mas o Service não tem endpoints. Veja [Ingress](../../03-services-networking/ingress.md) e, para HTTPRoute, as condições `Accepted` e `ResolvedRefs` em [Gateway API](../../03-services-networking/gateway-api.md).

## Reproduzir

```bash
kubectl create namespace ts
kubectl -n ts create deployment api --image=nginx:1.27 --replicas=2
kubectl -n ts create service clusterip api-errado --tcp=80:80                            # selector app=api-errado
kubectl -n ts expose deployment api --name=api-porta --port=80 --target-port=8080        # porta errada
kubectl -n ts expose deployment api --port=80                                            # o certo, para comparar
```

??? example "NetworkPolicy do cenário"

    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata: {name: api-so-frontend, namespace: ts}
    spec:
      podSelector: {matchLabels: {app: api}}
      policyTypes: [Ingress]
      ingress:
      - from: [{podSelector: {matchLabels: {papel: frontend}}}]
        ports: [{port: 80}]
    ```
