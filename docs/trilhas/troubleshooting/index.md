# Treinar troubleshooting

> **Versão do Kubernetes:** v1.36 · **Última revisão:** 2026-10-25 · Trilha para quem já sabe criar recursos, mas trava quando algo não funciona

**Você já sabe os objetos, mas precisa ganhar velocidade no diagnóstico?** Treine por sintomas: comece pelo estado que você observa e descubra qual evidência procurar. Troubleshooting é **30% da prova**, o maior domínio.

Todos os 23 cenários desta trilha foram quebrados de propósito num cluster kind v1.36.4 (1 control plane + 1 worker). As mensagens são as saídas reais, recortadas no que importa (sem colunas de idade, por exemplo).

## O roteiro

Todo cenário segue a mesma ordem:

1. **Sintoma:** o que você vê.
2. **Primeiro comando:** onde olhar.
3. **Evidência:** a linha que conta a causa.
4. **Causas prováveis.**
5. **Correção.**
6. **Como validar.**

O roteiro existe para você não pular etapas. Corrigir antes de achar a evidência costuma resolver o problema errado.

## Primeiro comando por sintoma

| Você vê | Primeiro comando | Página |
|---|---|---|
| Pod `Pending`, `ImagePullBackOff`, `CreateContainerConfigError`, `ContainerCreating` | `kubectl describe pod <nome>` (seção Events) | [Pod não inicia](pod-nao-inicia.md) |
| Pod `CrashLoopBackOff` ou `OOMKilled` | `kubectl logs <nome>` e `kubectl describe pod <nome>` (Last State) | [Pod não inicia](pod-nao-inicia.md) |
| A aplicação não responde | `kubectl get endpointslices -l kubernetes.io/service-name=<svc>` e um Pod de teste | [Aplicação não responde](aplicacao-nao-responde.md) |
| Pod `Pending` com `FailedScheduling` | `kubectl describe pod <nome>` (a mensagem diz quantos nós foram descartados e por quê) | [Agendamento](agendamento.md) |
| PVC `Pending` ou volume que não monta | `kubectl describe pvc <nome>` | [Armazenamento](armazenamento.md) |
| Nó `NotReady` | `kubectl describe node <nó>` (condição Ready) | [Nó NotReady](no-notready.md) |
| `kubectl` não responde, ou Pods sem evento nenhum | `crictl ps -a` no control plane | [Control plane](control-plane.md) |

## Três pistas que resolvem muita coisa

- **Pod que nunca rodou não tem log.** Em `Pending`, `ImagePullBackOff` e `CreateContainerConfigError`, a resposta está nos Events do `describe`.
- **Muita coisa se resolve sozinha depois da correção.** Pod `Pending` volta a ser agendado e Pod esperando ConfigMap sobe assim que ele existe. Recriar só é preciso quando o campo é imutável.
- **O erro do teste de rede diz a camada:**

| Erro no `wget` de dentro do cluster | Causa provável |
|---|---|
| `bad address 'api'` | DNS: o nome não existe no namespace de onde você testa |
| `Connection refused` | Service sem endpoints ou `targetPort` errado |
| `download timed out` | NetworkPolicy descartando o tráfego |

## Como treinar

Cada página tem os comandos para quebrar o cluster do mesmo jeito. Num cluster de estudo (kind, minikube ou o lab), crie o cenário sem ler a solução, siga o roteiro e só depois compare.
