# Diagramas

Abrir com a extensão Excalidraw do VS Code. Cada diagrama tem um script gerador (edite só a seção `DIAGRAMA`):

| Arquivo | Gerador | Assunto |
|---|---|---|
| `01-dominio1-operar-cluster.excalidraw` | `python gerar_excalidraw.py 01-dominio1-operar-cluster.excalidraw` | Domínio 1 do CKA em uma página: RBAC, etcd, Helm/Kustomize, upgrade e drain, com a janela de upgrade em 5 passos |
| `02-kubeadm-certs.excalidraw` | `python gerar_02_kubeadm_certs.py 02-kubeadm-certs.excalidraw` | Certificados com kubeadm: quem assina, quem usa e como renovar em 5 passos |
| `03-services-dns.excalidraw` | `python gerar_03_services_dns.py 03-services-dns.excalidraw` | Services e DNS: do nome (CoreDNS) ao IP fixo (Service) e ao Pod que atende (EndpointSlice + kube-proxy) |
| `04-trafego-entrada-networkpolicy.excalidraw` | `python gerar_04_trafego_entrada.py 04-trafego-entrada-networkpolicy.excalidraw` | Tráfego de fora até o Pod: Ingress ou Gateway + HTTPRoute escolhem o Service; a NetworkPolicy decide se o Pod aceita |
| `05-um-conteudo-dois-layouts.excalidraw` | `python gerar_05_dois_layouts.py 05-um-conteudo-dois-layouts.excalidraw` | Um conteúdo, dois sites: docs/ → MkDocs (clássico) e sync-docs → Astro (interativo, /v2/) |
| `07-workloads-scheduling.excalidraw` | `python gerar_07_workloads_scheduling.py 07-workloads-scheduling.excalidraw` | Do YAML ao Pod no nó certo: quota, controlador, scheduler (requests, taints, affinity), kubelet com limits e ConfigMap/Secret, HPA |
| `08-storage.excalidraw` | `python gerar_08_storage.py 08-storage.excalidraw` | Onde o dado mora: Pod → PVC → PV (pronto ou criado pela StorageClass) → disco, emptyDir e reclaimPolicy |
| `09-troubleshooting.excalidraw` | `python gerar_09_troubleshooting.py 09-troubleshooting.excalidraw` | Sintoma → onde olhar → causa típica, e o roteiro de primeira olhada em 5 passos |
