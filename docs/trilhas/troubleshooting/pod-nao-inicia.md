# Pod não inicia

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · Trilha de troubleshooting · 6 cenários

Seis motivos para um Pod não chegar a `Running`, cada um com o roteiro **sintoma → primeiro comando → evidência → causas → correção → validação**. A explicação de cada estado está em [Pods: Pending, CrashLoopBackOff, ImagePullBackOff](../../05-troubleshooting/pods.md).

```console
$ kubectl get pods
NAME     READY   STATUS                       RESTARTS      AGE
crash    0/1     Error                        3 (61s ago)   75s
grande   0/1     Pending                      0             75s
imagem   0/1     ImagePullBackOff             0             75s
oom      0/1     OOMKilled                    3 (56s ago)   75s
semcm    0/1     CreateContainerConfigError   0             75s
semvol   0/1     ContainerCreating            0             75s
```

## Pending: recursos insuficientes

1. **Sintoma:** `STATUS Pending`, sem nenhum restart.
2. **Primeiro comando:** `kubectl describe pod grande`
3. **Evidência:**

    ```console
    Warning  FailedScheduling  default-scheduler  0/2 nodes are available: 1 Insufficient cpu, 1 node(s) had untolerated taint(s).
    ```

4. **Causas prováveis:** o `requests` do container é maior do que sobra em qualquer nó. Aqui eram 64 CPUs. O scheduler compara com os **requests** já reservados, não com o uso real.
5. **Correção:** baixar o `requests`. Em Pod avulso, `resources` não muda depois de criado: corrija o YAML e use `kubectl replace --force -f pod.yaml`. Em Deployment, edite o Deployment.
6. **Validar:** `kubectl get pod grande -w` até `Running`. Para ver o espaço livre: `kubectl describe node <nó>` → `Allocated resources`.

## ImagePullBackOff

1. **Sintoma:** `ErrImagePull` e depois `ImagePullBackOff`.
2. **Primeiro comando:** `kubectl describe pod imagem`
3. **Evidência:**

    ```console
    Warning  Failed   kubelet  Failed to pull image "nginx:1.27-naoexiste": rpc error: code = NotFound desc = failed to pull and unpack image ... not found
    Warning  Failed   kubelet  Error: ErrImagePull
    Normal   BackOff  kubelet  Back-off pulling image "nginx:1.27-naoexiste"
    ```

4. **Causas prováveis:** tag ou nome errados (`not found`), ou registry privado sem `imagePullSecrets` (`unauthorized` / `pull access denied`).
5. **Correção:** a imagem é um dos poucos campos que mudam num Pod: `kubectl set image pod/imagem c=nginx:1.27`. Em Deployment: `kubectl set image deploy/<nome> <container>=<imagem>`.
6. **Validar:** `kubectl get pod imagem` → `Running`.

## CreateContainerConfigError: ConfigMap ou Secret faltando

1. **Sintoma:** `CreateContainerConfigError`.
2. **Primeiro comando:** `kubectl describe pod semcm`
3. **Evidência:**

    ```console
    Warning  Failed  kubelet  spec.containers{c}: Error: configmap "config-app" not found
    ```

4. **Causas prováveis:** o ConfigMap ou Secret usado em `env`/`envFrom` não existe, está em outro namespace ou a chave tem outro nome.
5. **Correção:** criar o objeto no namespace do Pod: `kubectl create configmap config-app --from-literal=modo=prod`.
6. **Validar:** o Pod sobe **sozinho**, sem recriar: o kubelet tenta de novo. `kubectl exec semcm -- printenv X` mostrou `prod`.

## ContainerCreating: volume que não monta

1. **Sintoma:** `ContainerCreating` por muito tempo.
2. **Primeiro comando:** `kubectl describe pod semvol`
3. **Evidência:**

    ```console
    Warning  FailedMount  kubelet  MountVolume.SetUp failed for volume "v" : configmap "config-app" not found
    ```

4. **Causas prováveis:** ConfigMap, Secret ou PVC do volume não existe. Também aparece com `hostPath` de `type: Directory` inexistente (ver [Armazenamento](armazenamento.md)).
5. **Correção:** criar o objeto que falta.
6. **Validar:** também sobe sozinho. `kubectl exec semvol -- cat /cfg/modo` mostrou `prod`.

## CrashLoopBackOff: o processo termina

1. **Sintoma:** `Error` e `CrashLoopBackOff` se alternando, com `RESTARTS` subindo.
2. **Primeiro comando:** `kubectl logs crash` (e `kubectl describe pod crash` para o exit code)
3. **Evidência:**

    ```console
    $ kubectl logs crash
    erro: variavel DB_HOST nao definida
    ```

    No `describe`: `Last State: Terminated`, `Reason: Error`, `Exit Code: 1`.

4. **Causas prováveis:** a aplicação falha ao iniciar (variável, arquivo de configuração, comando errado). Exit code 0 com restarts significa que o comando terminou com sucesso, mas um Pod de Deployment precisa de um processo que continue rodando.
5. **Correção:** o que o log pedir. Aqui, acrescentar `env: DB_HOST` ao container e recriar com `kubectl replace --force -f`.
6. **Validar:** `kubectl get pod crash` → `Running` com 0 restarts; `kubectl logs crash` → `conectando em db.shop`.

## OOMKilled: memória acima do limit

1. **Sintoma:** `OOMKilled` e depois `CrashLoopBackOff`.
2. **Primeiro comando:** `kubectl describe pod oom`
3. **Evidência:**

    ```console
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Limits:
      memory:  64Mi
    ```

4. **Causas prováveis:** o processo usa mais memória que o `limits.memory`. CPU acima do limit não mata, só deixa lento.
5. **Correção:** aumentar o limit (aqui, de `64Mi` para `512Mi`) e recriar o Pod. Em Deployment, edite o Deployment.
6. **Validar:** `kubectl get pod oom` → `Running` e `RESTARTS` parado.

## Reproduzir

??? example "YAML dos seis Pods quebrados"

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata: {name: grande}
    spec: {containers: [{name: c, image: nginx:1.27, resources: {requests: {cpu: "64"}}}]}
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: imagem}
    spec: {containers: [{name: c, image: nginx:1.27-naoexiste}]}
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: semcm}
    spec: {containers: [{name: c, image: nginx:1.27, env: [{name: X, valueFrom: {configMapKeyRef: {name: config-app, key: modo}}}]}]}
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: semvol}
    spec:
      containers: [{name: c, image: nginx:1.27, volumeMounts: [{name: v, mountPath: /cfg}]}]
      volumes: [{name: v, configMap: {name: config-app}}]
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: crash}
    spec:
      containers:
      - name: c
        image: busybox:1.36
        command: [sh, -c, 'if [ -z "$DB_HOST" ]; then echo "erro: variavel DB_HOST nao definida" >&2; exit 1; fi; echo "conectando em $DB_HOST"; sleep 3600']
    ---
    apiVersion: v1
    kind: Pod
    metadata: {name: oom}
    spec: {containers: [{name: c, image: python:3.12-alpine, command: [python, -c, "x=bytearray(200*1024*1024); import time; time.sleep(60)"], resources: {limits: {memory: 64Mi}}}]}
    ```
