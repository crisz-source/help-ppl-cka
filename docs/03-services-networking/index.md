# 3. Services & Networking (20%)

Um quinto da prova. É o domínio de **como o tráfego chega aos Pods**: endereço estável (Service), nome (DNS), regras de quem pode falar com quem (NetworkPolicy) e entrada de tráfego externo (Ingress e Gateway API).

## Itens do currículo e onde estão

| Item do currículo | Página |
|---|---|
| Use ClusterIP, NodePort, LoadBalancer service types and endpoints | [Services e Endpoints](services-endpoints.md) |
| Understand and use CoreDNS | [DNS do cluster](dns.md) |
| Define and enforce Network Policies | [NetworkPolicy](network-policy.md) |
| Use the Gateway API to manage Ingress traffic | [Gateway API](gateway-api.md) |
| Know how to use Ingress controllers and Ingress resources | [Ingress](ingress.md) |

<!-- VERIFICAR: conferir a lista acima contra a versão atual do currículo em https://github.com/cncf/curriculum -->

## Ordem sugerida de estudo

1. **Services e Endpoints**: base de todo o resto. Ingress, Gateway e DNS apontam para Services.
2. **DNS do cluster**: como os Pods acham os Services pelo nome.
3. **NetworkPolicy**: por padrão todo Pod fala com todo Pod; a NetworkPolicy restringe isso.
4. **Ingress** e **Gateway API**: tráfego HTTP vindo de fora.
