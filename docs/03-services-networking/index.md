# 3. Services & Networking (20%)

Um quinto da prova. É o domínio de **como o tráfego chega aos Pods**: endereço estável (Service), nome (DNS), regras de quem pode falar com quem (NetworkPolicy) e entrada de tráfego externo (Ingress e Gateway API).

## Itens do currículo e onde estão

| Item do currículo | Página |
|---|---|
| Use ClusterIP, NodePort, LoadBalancer service types and endpoints | [Services e Endpoints](services-endpoints.md) |
| Understand and use CoreDNS | [DNS do cluster](dns.md) |
| Understand connectivity between Pods | *a fazer* |
| Define and enforce Network Policies | *a fazer* |
| Use the Gateway API to manage Ingress traffic | *a fazer* |
| Know how to use Ingress controllers and Ingress resources | *a fazer* |

<!-- VERIFICAR: conferir a lista acima contra a versão atual do currículo em https://github.com/cncf/curriculum -->

## Ordem sugerida de estudo

1. **Services e Endpoints**: base de todo o resto. Ingress, Gateway e DNS apontam para Services.
2. **DNS do cluster**: como os Pods acham os Services pelo nome.
3. **Conectividade entre Pods / CNI**: o modelo de rede "todo Pod fala com todo Pod".
4. **NetworkPolicy**: restringir esse "todo mundo fala com todo mundo".
5. **Ingress** e **Gateway API**: tráfego HTTP vindo de fora.
