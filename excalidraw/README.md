# Diagramas

Abrir com a extensão Excalidraw do VS Code. Cada diagrama tem um script gerador (edite só a seção `DIAGRAMA`):

| Arquivo | Gerador | Assunto |
|---|---|---|
| `01-dominio1-operar-cluster.excalidraw` | `python gerar_excalidraw.py 01-dominio1-operar-cluster.excalidraw` | Domínio 1 do CKA em uma página: RBAC, etcd, Helm/Kustomize, upgrade e drain, com a janela de upgrade em 5 passos |
| `02-kubeadm-certs.excalidraw` | `python gerar_02_kubeadm_certs.py 02-kubeadm-certs.excalidraw` | Certificados com kubeadm: quem assina, quem usa e como renovar em 5 passos |
