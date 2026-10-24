"""Gera os diagramas do site CKA (help-ppl-cka) em draw.io, com os ícones oficiais do Kubernetes
que vêm no draw.io (stencil mxgraph.kubernetes.icon).

Cada diagrama redesenha um bloco ```mermaid do site mantendo os mesmos textos; só o desenho muda.
Um arquivo .drawio por diagrama: <NN do domínio>-<página de origem>.drawio.

Uso:
    python gerar_cka_drawio.py <pasta de saída> [nome ...]     (sem nome = todos)
"""
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

K8S_AZUL = "#326CE5"  # azul oficial do logotipo do Kubernetes

# Paleta sóbria: (preenchimento, borda) por papel.
COR = {
    "comando": ("#f1f3f5", "#495057"),   # o que você digita (CLI)
    "arquivo": ("#fff9db", "#e67700"),   # arquivo em disco
    "k8s": ("#e7f5ff", K8S_AZUL),        # fronteiras ligadas ao cluster
    "neutro": ("#ffffff", "#868e96"),    # etapa, ferramenta ou coisa fora do Kubernetes
    "conceito": ("#ffffff", K8S_AZUL),   # objeto do Kubernetes sem ícone oficial
    "externo": ("#fff4e6", "#e8590c"),   # cliente / mundo de fora
    "erro": ("#fff5f5", "#c92a2a"),      # recusa, falha
    "espera": ("#fff3bf", "#e67700"),    # estado de espera (Pending)
    "ok": ("#ebfbee", "#2f9e44"),        # deu certo
    "disco": ("#f8f9fa", "#495057"),     # disco / armazenamento real
}
FONTE_MONO = "Consolas"
SETA_COR = "#343a40"


class Pagina:
    def __init__(self, nome: str, largura: int, altura: int):
        self.nome, self.largura, self.altura = nome, largura, altura
        self.celulas: list[str] = []
        self._n = 0

    def _id(self) -> str:
        self._n += 1
        return f"c{self._n}"

    def _vertice(self, valor: str, estilo: str, x, y, w, h) -> str:
        i = self._id()
        self.celulas.append(
            f'<mxCell id="{i}" value={quoteattr(valor)} style={quoteattr(estilo)} vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    # ------------------------------------------------------------------ textos e áreas
    def texto(self, x, y, w, h, html: str, tamanho=12, cor="#1e1e1e", alinhar="left"):
        return self._vertice(html, f"text;html=1;whiteSpace=wrap;align={alinhar};verticalAlign=top;"
                                   f"fontSize={tamanho};fontColor={cor};", x, y, w, h)

    def cabecalho(self, titulo: str, subtitulo: str):
        self.texto(30, 15, self.largura - 60, 34, f"<b>{titulo}</b>", tamanho=22)
        self.texto(30, 50, self.largura - 60, 24, subtitulo, tamanho=12, cor="#495057")

    def fronteira(self, x, y, w, h, titulo: str, papel="neutro", tracejada=True, icone=None):
        """Área com título no canto. `icone` = prIcon do Kubernetes desenhado ao lado do título."""
        fill, stroke = COR[papel]
        recuo = 40 if icone else 8
        caixa = self._vertice(
            titulo,
            f"rounded=1;arcSize=3;html=1;whiteSpace=wrap;align=left;verticalAlign=top;spacingLeft={recuo};"
            f"spacingTop=6;fontSize=13;fontStyle=1;fontColor={stroke};strokeColor={stroke};"
            f"fillColor={fill};dashed={1 if tracejada else 0};", x, y, w, h)
        if icone:
            self.icone(icone, x + 8, y + 5, "", tam=26)
        return caixa

    # ------------------------------------------------------------------ formas (canto superior esquerdo)
    def icone(self, pr_icon: str, x, y, rotulo: str, tam=64, pos="bottom"):
        """Ícone oficial do Kubernetes; `pos` = onde fica o rótulo (bottom, top, left, right)."""
        lugar = {
            "bottom": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
            "top": "verticalLabelPosition=top;verticalAlign=bottom;align=center;",
            "left": "labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;spacingRight=4;",
            "right": "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=4;",
        }[pos]
        return self._vertice(
            rotulo,
            f"shape=mxgraph.kubernetes.icon;prIcon={pr_icon};fillColor={K8S_AZUL};strokeColor=#ffffff;"
            f"aspect=fixed;html=1;points=[];fontSize=12;fontColor=#1e1e1e;labelBackgroundColor=none;{lugar}",
            x, y, tam, tam)

    def comando(self, x, y, w, h, html: str):
        """Caixa de comando de terminal (texto em fonte monoespaçada)."""
        fill, stroke = COR["comando"]
        return self._vertice(html, f"rounded=1;html=1;whiteSpace=wrap;fontFamily={FONTE_MONO};fontSize=13;"
                                   f"fillColor={fill};strokeColor={stroke};fontColor=#1e1e1e;", x, y, w, h)

    def arquivo(self, x, y, w, h, html: str):
        """Arquivo em disco (folha com canto dobrado)."""
        fill, stroke = COR["arquivo"]
        return self._vertice(html, f"shape=note;size=16;html=1;whiteSpace=wrap;fontFamily={FONTE_MONO};"
                                   f"fontSize=13;fillColor={fill};strokeColor={stroke};fontColor=#1e1e1e;", x, y, w, h)

    # ------------------------------------------------------------------ formas pelo centro (cx, cy)
    def I(self, pr_icon, cx, cy, rotulo, tam=56, pos="bottom"):
        return self.icone(pr_icon, cx - tam / 2, cy - tam / 2, rotulo, tam, pos)

    def B(self, cx, cy, w, h, html, papel="neutro", mono=False):
        """Caixa genérica: etapa, ferramenta, estado ou objeto sem ícone."""
        fill, stroke = COR[papel]
        fonte = f"fontFamily={FONTE_MONO};" if mono else ""
        negrito = "fontStyle=1;" if papel in ("erro", "espera", "ok") else ""
        return self._vertice(html, f"rounded=1;html=1;whiteSpace=wrap;fontSize=13;{fonte}{negrito}"
                                   f"fillColor={fill};strokeColor={stroke};fontColor=#1e1e1e;",
                             cx - w / 2, cy - h / 2, w, h)

    def CMD(self, cx, cy, w, h, html):
        return self.comando(cx - w / 2, cy - h / 2, w, h, html)

    def ARQ(self, cx, cy, w, h, html):
        return self.arquivo(cx - w / 2, cy - h / 2, w, h, html)

    def DEC(self, cx, cy, w, h, html):
        """Decisão (losango)."""
        fill, stroke = COR["neutro"]
        return self._vertice(html, f"rhombus;html=1;whiteSpace=wrap;fontSize=13;fillColor={fill};"
                                   f"strokeColor={SETA_COR};fontColor=#1e1e1e;", cx - w / 2, cy - h / 2, w, h)

    def DISCO(self, cx, cy, w, h, html):
        """Disco / armazenamento real (cilindro)."""
        fill, stroke = COR["disco"]
        return self._vertice(html, f"shape=cylinder3;boundedLbl=1;size=10;html=1;whiteSpace=wrap;fontSize=13;"
                                   f"fillColor={fill};strokeColor={stroke};fontColor=#1e1e1e;",
                             cx - w / 2, cy - h / 2, w, h)

    # ------------------------------------------------------------------ setas
    def seta(self, origem: str, destino: str, rotulo="", saida=(1, 0.5), entrada=(0, 0.5), pontos=(),
             tracejada=False, ortho=False, cor=SETA_COR, ponta=True, pos_rotulo=0):
        """Seta presa às formas; pontos de saída e entrada fixos evitam que o draw.io escolha um
        caminho por cima de ícones e rótulos. `pontos` (ou `ortho`) = rota em ângulo reto."""
        i = self._id()
        roteada = bool(pontos) or ortho
        estilo = (f"edgeStyle={'orthogonalEdgeStyle' if roteada else 'none'};rounded=1;html=1;"
                  f"endArrow={'block' if ponta else 'none'};endFill=1;strokeWidth=2;strokeColor={cor};"
                  f"fontSize=12;fontColor={cor};labelBackgroundColor=#ffffff;dashed={1 if tracejada else 0};"
                  f"exitX={saida[0]};exitY={saida[1]};exitDx=0;exitDy=0;"
                  f"entryX={entrada[0]};entryY={entrada[1]};entryDx=0;entryDy=0;")
        dobras = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pontos)
        corpo = f'<Array as="points">{dobras}</Array>' if pontos else ""
        self.celulas.append(
            f'<mxCell id="{i}" value={quoteattr(rotulo)} style={quoteattr(estilo)} edge="1" parent="1" '
            f'source="{origem}" target="{destino}"><mxGeometry x="{pos_rotulo}" relative="1" as="geometry">'
            f'{corpo}</mxGeometry></mxCell>')
        return i

    def seta_xy(self, x1, y1, x2, y2, rotulo="", tracejada=False, cor=SETA_COR, ponta=True, largura=2):
        """Seta solta entre dois pontos (diagrama de sequência, linhas de vida)."""
        i = self._id()
        estilo = (f"html=1;endArrow={'block' if ponta else 'none'};endFill=1;strokeWidth={largura};"
                  f"strokeColor={cor};fontSize=12;fontColor={cor};labelBackgroundColor=#ffffff;"
                  f"dashed={1 if tracejada else 0};")
        self.celulas.append(
            f'<mxCell id="{i}" value={quoteattr(rotulo)} style={quoteattr(estilo)} edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
            f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/></mxGeometry></mxCell>')
        return i

    def xml(self) -> str:
        return (f'<mxfile host="gerar_cka_drawio.py"><diagram name={quoteattr(self.nome)} id="d1">'
                f'<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
                f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.largura}" pageHeight="{self.altura}" '
                f'background="#ffffff" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
                + "".join(self.celulas) + "</root></mxGraphModel></diagram></mxfile>")


# ====================================================================== Domínio 1
def rbac() -> Pagina:
    # Origem: docs/01-cluster-architecture/rbac.md. As três etapas ficam dentro do kube-apiserver.
    p = Pagina("RBAC: o caminho de uma requisição", 1180, 470)
    p.cabecalho("RBAC: o caminho de uma requisição", "Toda requisição passa por três etapas dentro do kube-apiserver")
    quem = p.I("user", 70, 210, "kubectl / Pod")
    p.fronteira(250, 110, 700, 190, "kube-apiserver", "k8s", tracejada=False, icone="api")
    autn = p.B(370, 210, 190, 64, "Autenticação<br>quem é você?", "conceito")
    autz = p.B(600, 210, 190, 64, "Autorização<br>Node, RBAC...", "conceito")
    adm = p.B(830, 210, 190, 64, "Admission control<br>mutação e validação", "conceito")
    etcd = p.I("etcd", 1070, 210, "etcd")
    negado = p.B(600, 400, 190, 56, "403 Forbidden", "erro")
    p.seta(quem, autn, "requisição HTTPS")
    p.seta(autn, autz)
    p.seta(autz, adm)
    p.seta(adm, etcd)
    p.seta(autz, negado, "nenhuma regra permite", saida=(0.5, 1), entrada=(0.5, 0), tracejada=True, cor="#c92a2a")
    return p


def upgrade_kubeadm() -> Pagina:
    # Origem: docs/01-cluster-architecture/upgrade-kubeadm.md. Coluna do 1º control plane à esquerda,
    # workers à direita; o losango marca a passagem de um para o outro.
    p = Pagina("Upgrade com kubeadm", 1180, 790)
    p.cabecalho("Upgrade com kubeadm", "Primeiro o control plane, um nó por vez; depois os workers")
    p.fronteira(40, 100, 460, 670, "1º control plane", "k8s", tracejada=False, icone="master")
    passos = [
        (60, "Trocar repositório apt<br>para o novo minor", False),
        (56, "Atualizar pacote kubeadm", False),
        (56, "kubeadm upgrade plan", True),
        (64, "kubeadm upgrade apply v1.37.Y<br>só no 1º control plane", True),
        (56, "drain do nó", False),
        (64, "Atualizar kubelet + kubectl<br>daemon-reload + restart kubelet", False),
        (56, "uncordon", False),
    ]
    ids, y = [], 150
    for h, txt, cmd in passos:
        ids.append(p.CMD(270, y + h / 2, 360, h, txt) if cmd else p.B(270, y + h / 2, 360, h, txt))
        y += h + 28
    for a, b in zip(ids, ids[1:]):
        p.seta(a, b, saida=(0.5, 1), entrada=(0.5, 0))
    workers = p.DEC(640, 686, 150, 90, "Workers")
    p.fronteira(760, 400, 400, 370, "Cada worker", "k8s", tracejada=False, icone="node")
    i1 = p.B(960, 490, 340, 64, "Atualizar kubeadm<br>kubeadm upgrade node")
    j1 = p.B(960, 640, 340, 64, "drain → kubelet/kubectl → uncordon")
    p.seta(ids[-1], workers)
    p.seta(workers, i1, saida=(0.5, 0), entrada=(0, 0.5), pontos=[(640, 490)])
    p.seta(i1, j1, saida=(0.5, 1), entrada=(0.5, 0))
    return p


def kubeadm_certs() -> Pagina:
    # Origem: docs/01-cluster-architecture/kubeadm-certs.md. Árvore: cada CA à esquerda assina os
    # certificados à direita. Tudo mora em /etc/kubernetes/pki (os kubeconfigs, em /etc/kubernetes).
    p = Pagina("Certificados do kubeadm", 1100, 720)
    p.cabecalho("Certificados do kubeadm", "Três CAs; cada uma assina os certificados ligados a ela")
    p.fronteira(20, 90, 1060, 610, "/etc/kubernetes/pki", "neutro", tracejada=False, icone="master")
    ca = p.ARQ(200, 250, 260, 64, "<b>ca.crt</b><br>CA do cluster")
    apis = p.ARQ(700, 150, 420, 56, "apiserver.crt<br>servidor HTTPS do API server")
    akc = p.ARQ(700, 240, 420, 56, "apiserver-kubelet-client.crt<br>API server → kubelet")
    kc = p.ARQ(700, 350, 420, 90, "admin.conf, controller-manager.conf,<br>scheduler.conf, kubelet.conf<br>"
                                  "certificados dentro dos kubeconfigs")
    eca = p.ARQ(200, 500, 260, 64, "<b>etcd/ca.crt</b><br>CA do etcd")
    es = p.ARQ(700, 470, 420, 50, "etcd/server.crt e etcd/peer.crt")
    aec = p.ARQ(700, 545, 420, 56, "apiserver-etcd-client.crt<br>API server → etcd")
    fca = p.ARQ(200, 640, 260, 64, "<b>front-proxy-ca.crt</b><br>CA do agregador")
    fpc = p.ARQ(700, 640, 420, 50, "front-proxy-client.crt")
    for pai, filhos in ((ca, (apis, akc, kc)), (eca, (es, aec)), (fca, (fpc,))):
        for f in filhos:
            p.seta(pai, f, ortho=True)
    return p


def drain() -> Pagina:
    # Origem: docs/01-cluster-architecture/drain-cordon-uncordon.md (diagrama de sequência).
    p = Pagina("kubectl drain: a sequência", 1200, 600)
    p.cabecalho("kubectl drain: a sequência", "O drain não move Pods: marca o nó e pede a expulsão de cada Pod")
    xs = {"U": 150, "API": 470, "S": 790, "RS": 1080}
    p.CMD(xs["U"], 130, 200, 50, "kubectl drain")
    p.I("api", xs["API"], 130, "kube-apiserver", pos="right")
    p.I("sched", xs["S"], 130, "kube-scheduler", pos="right")
    p.I("c_m", xs["RS"], 130, "controller<br>(ReplicaSet)", pos="right")
    for x in xs.values():
        p.seta_xy(x, 165, x, 570, tracejada=True, cor="#adb5bd", ponta=False, largura=1)
    msgs = [
        ("U", "API", "PATCH node (unschedulable=true)", False),
        ("U", "API", "POST Eviction (para cada Pod)", False),
        ("API", "U", "aceito, ou 429 se violar PDB", True),
        ("API", "RS", "Pod removido", False),
        ("RS", "API", "cria Pod substituto", False),
        ("S", "API", "agenda o Pod em outro nó", False),
    ]
    for n, (de, para, txt, volta) in enumerate(msgs):
        y = 220 + 58 * n
        p.seta_xy(xs[de], y, xs[para], y, txt, tracejada=volta)
    return p


def etcd_backup_restore() -> Pagina:
    # Origem: docs/01-cluster-architecture/etcd-backup-restore.md, "Como funciona por dentro".
    # Duas faixas (Backup em cima, Restore embaixo); o snapshot.db fica entre elas, porque é o
    # que o backup produz e o que o restore consome.
    p = Pagina("Backup e restore do etcd", 1180, 640)
    p.cabecalho("Backup e restore do etcd", "Num cluster kubeadm, tudo acontece no nó do control plane")
    p.fronteira(20, 90, 1140, 530, "Nó do control plane", "k8s", tracejada=False, icone="master")

    p.fronteira(50, 140, 1080, 150, "Backup", "neutro")
    save = p.comando(80, 190, 280, 56, "etcdctl snapshot save")
    etcd = p.icone("etcd", 640, 184, "etcd rodando")

    snap = p.arquivo(110, 318, 220, 56, "snapshot.db")

    p.fronteira(50, 400, 1080, 200, "Restore", "neutro")
    restore = p.comando(80, 450, 280, 76, "etcdutl snapshot restore<br>--data-dir /var/lib/etcd-restore")
    yaml_ = p.arquivo(420, 450, 230, 76, "Editar etcd.yaml:<br>hostPath → nova pasta")
    kubelet = p.icone("kubelet", 730, 456, "kubelet recria<br>o Pod do etcd")
    api = p.icone("api", 960, 456, "kube-apiserver lê<br>o estado restaurado")

    p.seta(save, etcd, "TLS :2379")
    p.seta(save, snap, saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(snap, restore, saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(restore, yaml_)
    p.seta(yaml_, kubelet)
    p.seta(kubelet, api)
    return p


def helm_kustomize() -> Pagina:
    # Origem: docs/01-cluster-architecture/helm-kustomize.md. Uma faixa por ferramenta.
    p = Pagina("Helm e Kustomize", 1160, 560)
    p.cabecalho("Helm e Kustomize", "Dois jeitos de chegar ao YAML que vai para o cluster")
    p.fronteira(30, 100, 1100, 220, "Helm", "neutro")
    chart = p.ARQ(170, 190, 220, 64, "Chart + values")
    render = p.CMD(470, 190, 220, 56, "helm renderiza")
    api1 = p.I("api", 800, 165, "kube-apiserver", pos="right")
    sec = p.I("secret", 800, 265, "Secret da release<br>histórico", pos="right")
    p.seta(chart, render)
    p.seta(render, api1, saida=(1, 0.3))
    p.seta(render, sec, saida=(1, 0.7))
    p.fronteira(30, 350, 1100, 180, "Kustomize", "neutro")
    base = p.ARQ(170, 440, 220, 64, "base/ YAML puro")
    kus = p.ARQ(450, 440, 240, 64, "kustomization.yaml<br>overlay")
    final = p.ARQ(730, 440, 200, 64, "YAML final")
    api2 = p.I("api", 960, 440, "kube-apiserver", pos="right")
    p.seta(base, kus)
    p.seta(kus, final)
    p.seta(final, api2)
    return p


# ====================================================================== Domínio 2
def workloads_visao_geral() -> Pagina:
    # Origem: docs/02-workloads-scheduling/index.md.
    p = Pagina("Workloads & Scheduling: visão geral", 1180, 520)
    p.cabecalho("Workloads & Scheduling: visão geral", "Do kubectl apply ao Pod rodando no nó")
    u = p.CMD(120, 280, 180, 50, "kubectl apply")
    api = p.I("api", 400, 280, "kube-apiserver<br>admissão: ResourceQuota,<br>LimitRange")
    c = p.I("c_m", 720, 170, "Controladores<br>Deployment, DaemonSet, Job...", pos="top")
    h = p.I("hpa", 1040, 170, "HPA", pos="top")
    s = p.I("sched", 720, 400, "kube-scheduler<br>requests, taints, affinity")
    k = p.I("kubelet", 1040, 400, "kubelet<br>aplica limits, QoS,<br>ConfigMap/Secret")
    p.seta(u, api)
    p.seta(api, c, saida=(1, 0.2), entrada=(0, 0.5))
    p.seta(c, api, "cria Pods", saida=(0.5, 1), entrada=(1, 0.5), pontos=[(720, 280)])
    p.seta(api, s, saida=(1, 0.85), entrada=(0, 0.5))
    p.seta(s, k, "escolhe o nó")
    p.seta(h, c, "ajusta replicas", saida=(0, 0.5), entrada=(1, 0.5))
    return p


def deployments_rollout() -> Pagina:
    # Origem: docs/02-workloads-scheduling/deployments-rollout.md.
    p = Pagina("Deployment: rollout", 1060, 500)
    p.cabecalho("Deployment: rollout", "Cada revisão é um ReplicaSet; o rollout troca as réplicas de um para o outro")
    d = p.I("deploy", 130, 280, "Deployment web<br>replicas: 3")
    rs1 = p.I("rs", 520, 170, "ReplicaSet web-abc<br>nginx:1.27 · 3 → 0")
    rs2 = p.I("rs", 520, 380, "ReplicaSet web-def<br>nginx:1.28 · 0 → 3")
    p1 = p.I("pod", 880, 170, "Pods antigos")
    p2 = p.I("pod", 880, 380, "Pods novos")
    p.seta(d, rs1, "revisão 1")
    p.seta(d, rs2, "revisão 2")
    p.seta(rs1, p1)
    p.seta(rs2, p2)
    return p


def configmap_secret() -> Pagina:
    # Origem: docs/02-workloads-scheduling/configmap-secret.md.
    p = Pagina("ConfigMap e Secret: do etcd ao container", 1200, 470)
    p.cabecalho("ConfigMap e Secret: do etcd ao container", "Variável é copiada uma vez; volume é atualizado")
    cm = p.I("cm", 110, 260, "ConfigMap / Secret<br>no etcd")
    api = p.I("api", 340, 260, "kube-apiserver")
    k = p.I("kubelet", 660, 260, "kubelet")
    p.fronteira(840, 120, 330, 300, "Container", "k8s", tracejada=False, icone="pod")
    v = p.B(1005, 200, 260, 56, "variáveis do container", "conceito")
    f = p.ARQ(1005, 340, 260, 56, "/etc/config/CHAVE")
    p.seta(cm, api)
    p.seta(api, k, "kubelet busca ao criar o Pod")
    p.seta(k, v, "env: copiado na partida", saida=(1, 0.3))
    p.seta(k, f, "volume: arquivo por chave<br>atualizado periodicamente", saida=(1, 0.7))
    return p


def requests_limits_qos() -> Pagina:
    # Origem: docs/02-workloads-scheduling/requests-limits-qos.md. Em cima, o agendamento (requests);
    # embaixo, o que o kubelet faz com os limits.
    p = Pagina("Requests, limits e QoS", 1320, 560)
    p.cabecalho("Requests, limits e QoS", "Requests decidem onde o Pod cabe; limits decidem até onde ele pode ir")
    pod = p.I("pod", 90, 200, "Pod com requests")
    s = p.I("sched", 300, 200, "kube-scheduler")
    n = p.I("node", 610, 200, "nó")
    k = p.I("kubelet", 820, 200, "kubelet")
    ev = p.B(1210, 200, 150, 50, "eviction", "erro")
    c = p.B(820, 440, 160, 50, "container", "conceito")
    oom = p.B(1210, 440, 150, 50, "OOMKilled", "erro")
    p.seta(pod, s)
    p.seta(s, n, "soma dos requests cabe<br>no Allocatable do nó?")
    p.seta(n, k)
    p.seta(k, ev, "nó sem memória: expulsa<br>BestEffort → Burstable", pos_rotulo=0)
    p.seta(k, c, "limits viram cgroups", saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(c, oom, "passou do limit<br>de memória")
    return p


def resourcequota() -> Pagina:
    # Origem: docs/02-workloads-scheduling/resourcequota.md.
    p = Pagina("ResourceQuota: a checagem na admissão", 1180, 520)
    p.cabecalho("ResourceQuota: a checagem na admissão", "Quem passa do teto do namespace é recusado na hora")
    u = p.CMD(130, 220, 200, 50, "kubectl apply Pod")
    api = p.I("api", 380, 220, "kube-apiserver", pos="top")
    d = p.DEC(720, 220, 140, 90, "cabe?")
    sim = p.B(1010, 140, 260, 64, "grava no etcd<br>e soma em status.used", "ok")
    nao = p.B(1010, 320, 260, 64, "403 Forbidden<br>exceeded quota", "erro")
    rc = p.I("rs", 380, 430, "ReplicaSet / Job", pos="right")
    p.seta(u, api)
    p.seta(api, d, "admissão ResourceQuota:<br>usado + novo cabe no hard?")
    p.seta(d, sim, "sim", saida=(0.5, 0), entrada=(0, 0.5), pontos=[(720, 140)])
    p.seta(d, nao, "não", saida=(0.5, 1), entrada=(0, 0.5), pontos=[(720, 320)])
    p.seta(rc, api, "cria Pods pela API", saida=(0.5, 0), entrada=(0.5, 1))
    return p


def taints() -> Pagina:
    # Origem: docs/02-workloads-scheduling/taints-tolerations-nodeselector.md.
    p = Pagina("Taints, tolerations e nodeSelector", 1300, 500)
    p.cabecalho("Taints, tolerations e nodeSelector", "O scheduler filtra os nós em etapas antes de escolher")
    pod = p.I("pod", 90, 200, "Pod pendente")
    s = p.I("sched", 300, 200, "kube-scheduler")
    f = p.I("node", 580, 200, "nós com os labels")
    t = p.I("node", 900, 200, "nós que aceitam")
    n = p.I("node", 1190, 200, "nó escolhido", pos="top")
    k = p.I("kubelet", 1190, 410, "kubelet / node controller", pos="left")
    p.seta(pod, s)
    p.seta(s, f, "1. filtra por nodeSelector")
    p.seta(f, t, "2. filtra por taints<br>NoSchedule sem toleration sai")
    p.seta(t, n, "3. pontua e escolhe")
    p.seta(k, n, "NoExecute expulsa<br>Pods já rodando", saida=(0.5, 0), entrada=(0.5, 1), tracejada=True,
           cor="#c92a2a")
    return p


def affinity() -> Pagina:
    # Origem: docs/02-workloads-scheduling/affinity.md.
    p = Pagina("Affinity: filtro e pontuação", 1240, 330)
    p.cabecalho("Affinity: filtro e pontuação", "required filtra; preferred só pontua")
    pod = p.I("pod", 90, 190, "Pod pendente")
    s = p.I("sched", 300, 190, "kube-scheduler")
    f = p.I("node", 580, 190, "nós possíveis")
    r = p.B(880, 190, 140, 50, "ranking", "conceito")
    n = p.I("node", 1140, 190, "nó com maior nota")
    p.seta(pod, s)
    p.seta(s, f, "filtro: required")
    p.seta(f, r, "pontuação: preferred<br>soma dos weight")
    p.seta(r, n)
    return p


def controllers() -> Pagina:
    # Origem: docs/02-workloads-scheduling/daemonset-job-cronjob-statefulset.md. Uma linha por controlador.
    p = Pagina("DaemonSet, Job, CronJob e StatefulSet", 1180, 600)
    p.cabecalho("DaemonSet, Job, CronJob e StatefulSet", "Cada controlador cria Pods com uma regra diferente")
    ds = p.I("ds", 110, 160, "DaemonSet")
    nos = p.I("node", 480, 160, "w1 · w2 · cp*")
    cj = p.I("cronjob", 110, 330, "CronJob")
    job = p.I("job", 480, 330, "Job")
    pt = p.I("pod", 880, 330, "Pods que terminam")
    ss = p.I("sts", 110, 500, "StatefulSet")
    pf = p.I("pod", 480, 500, "Pods com nome fixo")
    pvc = p.I("pvc", 880, 500, "um PVC por Pod<br>data-db-0, data-db-1")
    p.seta(ds, nos, "1 Pod em cada nó")
    p.seta(cj, job, "no horário")
    p.seta(job, pt, "até completions sucessos")
    p.seta(ss, pf, "db-0, depois db-1, db-2")
    p.seta(pf, pvc)
    return p


def hpa() -> Pagina:
    # Origem: docs/02-workloads-scheduling/hpa.md.
    p = Pagina("HPA: como as réplicas mudam", 1240, 480)
    p.cabecalho("HPA: como as réplicas mudam", "O HPA lê a métrica e grava o número de réplicas no Deployment")
    ms = p.I("deploy", 120, 170, "metrics-server<br>coleta do kubelet")
    api = p.I("api", 440, 170, "metrics.k8s.io", pos="top")
    h = p.I("hpa", 440, 370, "HPA controller<br>a cada 15 s")
    d = p.I("deploy", 760, 370, "Deployment<br>subrecurso scale")
    rs = p.I("rs", 960, 370, "ReplicaSet")
    pods = p.I("pod", 1140, 370, "Pods")
    p.seta(ms, api)
    p.seta(h, api, "lê uso dos Pods", saida=(0.5, 0), entrada=(0.5, 1))
    p.seta(h, d, "calcula e grava replicas")
    p.seta(d, rs)
    p.seta(rs, pods)
    return p


# ====================================================================== Domínio 3
def services_endpoints() -> Pagina:
    # Origem: docs/03-services-networking/services-endpoints.md. Em cima o control plane, embaixo um nó.
    p = Pagina("Services e EndpointSlices", 1240, 640)
    p.cabecalho("Services e EndpointSlices", "O control plane mantém a lista de Pods; o kube-proxy vira isso em regras no nó")
    p.fronteira(40, 100, 1160, 190, "Control plane", "k8s", tracejada=False, icone="master")
    epc = p.I("c_m", 240, 200, "EndpointSlice controller<br>no kube-controller-manager")
    api = p.I("api", 720, 200, "kube-apiserver", pos="right")
    p.fronteira(40, 330, 880, 290, "Cada nó", "k8s", tracejada=False, icone="node")
    kp = p.I("k_proxy", 720, 400, "kube-proxy", pos="right")
    r = p.B(720, 550, 280, 56, "regras iptables / nftables / IPVS", "conceito")
    c = p.I("pod", 200, 550, "Pod cliente")
    alvo = p.I("pod", 1110, 550, "Pod do Service")
    p.seta(epc, api, "observa Services e Pods prontos", saida=(1, 0.3), entrada=(0, 0.3))
    p.seta(epc, api, "grava EndpointSlices", saida=(1, 0.75), entrada=(0, 0.75))
    p.seta(kp, api, "observa Services e EndpointSlices", saida=(0.5, 0), entrada=(0.5, 1))
    p.seta(kp, r, saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(c, r, "10.96.x.x:80")
    p.seta(r, alvo, "DNAT para IP:targetPort")
    return p


def dns() -> Pagina:
    # Origem: docs/03-services-networking/dns.md.
    p = Pagina("DNS no cluster", 1200, 460)
    p.cabecalho("DNS no cluster", "O Pod pergunta ao Service kube-dns; o CoreDNS responde com o que leu da API")
    pod = p.I("pod", 110, 250, "Pod<br>/etc/resolv.conf")
    svc = p.I("svc", 420, 250, "Service kube-dns<br>10.96.0.10:53")
    core = p.I("pod", 700, 250, "Pods do CoreDNS<br>Deployment em kube-system")
    api = p.I("api", 1060, 120, "kube-apiserver")
    fora = p.B(1060, 250, 220, 56, "DNS do nó / internet", "externo")
    p.seta(pod, svc, "consulta web-svc")
    p.seta(svc, core)
    p.seta(core, api, "plugin kubernetes:<br>observa Services e EndpointSlices", saida=(1, 0.2))
    p.seta(core, fora, "nomes de fora: plugin forward")
    return p


def network_policy() -> Pagina:
    # Origem: docs/03-services-networking/network-policy.md.
    p = Pagina("NetworkPolicy: quem aplica a regra", 1100, 600)
    p.cabecalho("NetworkPolicy: quem aplica a regra", "A API só guarda a política; quem bloqueia é o CNI, em cada nó")
    api = p.I("api", 150, 160, "kube-apiserver<br>NetworkPolicy gravada")
    cni = p.I("ds", 560, 160, "Agente do CNI em cada nó<br>Calico, Cilium...", pos="right")
    no = p.I("node", 560, 380, "Nó")
    a = p.I("pod", 150, 380, "Pod frontend")
    b = p.I("pod", 950, 380, "Pod api")
    x = p.I("pod", 150, 530, "Pod qualquer")
    p.seta(api, cni, "observa")
    p.seta(cni, no, "regras iptables / eBPF", saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(a, no, "egress de A permite?", entrada=(0, 0.35))
    p.seta(no, b, "ingress de B permite?")
    p.seta(x, no, "bloqueado", saida=(1, 0.5), entrada=(0, 0.85), pontos=[(460, 530), (460, 400)],
           tracejada=True, cor="#c92a2a")
    return p


def ingress() -> Pagina:
    # Origem: docs/03-services-networking/ingress.md.
    p = Pagina("Ingress: do cliente ao Pod", 1220, 520)
    p.cabecalho("Ingress: do cliente ao Pod", "O controller lê os Ingress da API e roteia por host e path")
    u = p.B(110, 310, 160, 56, "Cliente externo", "externo")
    lb = p.I("svc", 380, 310, "LoadBalancer ou NodePort<br>do controller")
    ic = p.I("pod", 640, 310, "Pods do Ingress controller<br>proxy reverso")
    api = p.I("api", 640, 130, "kube-apiserver", pos="right")
    s1 = p.I("svc", 930, 230, "Service api")
    s2 = p.I("svc", 930, 410, "Service web")
    p1 = p.I("pod", 1130, 230, "Pods api")
    p2 = p.I("pod", 1130, 410, "Pods web")
    p.seta(u, lb, "loja.exemplo.com/api")
    p.seta(lb, ic)
    p.seta(ic, api, "observa Ingress, IngressClass,<br>Services, EndpointSlices", saida=(0.5, 0), entrada=(0.5, 1))
    p.seta(ic, s1, "host + path batem", saida=(1, 0.3))
    p.seta(ic, s2, "outro path", saida=(1, 0.7))
    p.seta(s1, p1)
    p.seta(s2, p2)
    return p


def gateway_api() -> Pagina:
    # Origem: docs/03-services-networking/gateway-api.md. Em cima os objetos que você escreve
    # (sem ícone oficial: caixas azuis); embaixo o controller e o proxy que ele cria.
    p = Pagina("Gateway API: objetos e controller", 1240, 700)
    p.cabecalho("Gateway API: objetos e controller", "Você escreve os objetos; o controller lê e configura o proxy")
    gc = p.B(160, 150, 220, 64, "GatewayClass<br>controllerName", "conceito")
    gw = p.B(520, 150, 240, 80, "Gateway<br>listener HTTP :80<br>listener HTTPS :443", "conceito")
    r1 = p.B(520, 340, 240, 64, "HTTPRoute<br>parentRefs: gateway", "conceito")
    s1 = p.I("svc", 920, 290, "Service app-v1", pos="right")
    s2 = p.I("svc", 920, 410, "Service app-v2", pos="right")
    api = p.I("api", 160, 580, "kube-apiserver")
    ctrl = p.I("deploy", 520, 580, "Controller da Gateway API")
    dp = p.B(860, 580, 260, 64, "Proxy de dados<br>Pods + Service LoadBalancer/NodePort", "conceito")
    u = p.B(1140, 580, 140, 56, "Cliente externo", "externo")
    p.seta(gc, gw)
    p.seta(r1, gw, "se liga a", saida=(0.5, 0), entrada=(0.5, 1))
    p.seta(r1, s1, "backendRefs, peso 90", saida=(1, 0.3))
    p.seta(r1, s2, "backendRefs, peso 10", saida=(1, 0.7))
    p.seta(ctrl, api, "observa os recursos", saida=(0, 0.5), entrada=(1, 0.5))
    p.seta(ctrl, dp, "cria e configura")
    p.seta(u, dp, saida=(0, 0.5), entrada=(1, 0.5))
    return p


# ====================================================================== Domínio 4
def volumes() -> Pagina:
    # Origem: docs/04-storage/volumes-emptydir-hostpath.md.
    p = Pagina("emptyDir e hostPath", 1000, 580)
    p.cabecalho("emptyDir e hostPath", "emptyDir vive e morre com o Pod; hostPath é uma pasta do nó")
    p.fronteira(40, 100, 560, 260, "Pod", "k8s", tracejada=False, icone="pod")
    app = p.B(170, 180, 200, 50, "container app", "conceito")
    side = p.B(170, 290, 200, 50, "container sidecar", "conceito")
    ed = p.I("vol", 480, 235, "emptyDir")
    fim = p.B(820, 235, 120, 50, "fim")
    ag = p.B(170, 470, 200, 50, "container agente", "conceito")
    hp = p.I("vol", 480, 470, "hostPath<br>/var/log")
    disco = p.DISCO(820, 470, 180, 80, "disco do nó<br>fica depois do Pod")
    p.seta(app, ed, "/cache", entrada=(0, 0.3))
    p.seta(side, ed, "/cache", entrada=(0, 0.7))
    p.seta(ed, fim, "apagado junto com o Pod", tracejada=True)
    p.seta(ag, hp, "/var/log do nó")
    p.seta(hp, disco, ponta=False)
    return p


def pv_pvc() -> Pagina:
    # Origem: docs/04-storage/pv-pvc.md.
    p = Pagina("PV e PVC", 1200, 330)
    p.cabecalho("PV e PVC", "O Pod pede pelo PVC; o PVC se liga a um PV compatível")
    pod = p.I("pod", 150, 180, "Pod<br>volumes: persistentVolumeClaim")
    pvc = p.I("pvc", 440, 180, "PVC<br>5Gi · RWO · classe X")
    pv = p.I("pv", 800, 180, "PV<br>10Gi · RWO · classe X")
    disco = p.DISCO(1060, 180, 180, 80, "disco real<br>NFS, hostPath, CSI...")
    p.seta(pod, pvc)
    p.seta(pvc, pv, "controlador de PV<br>procura PV compatível")
    p.seta(pv, disco)
    return p


def storageclass() -> Pagina:
    # Origem: docs/04-storage/storageclass.md. O rótulo do PVC fica em cima para a seta "bound"
    # poder chegar por baixo.
    p = Pagina("StorageClass e provisionamento dinâmico", 1340, 500)
    p.cabecalho("StorageClass e provisionamento dinâmico", "Sem PV pronto, o provisionador da classe cria um")
    pod = p.I("pod", 110, 260, "Pod")
    pvc = p.I("pvc", 380, 260, "PVC<br>storageClassName: rapido", pos="top")
    pr = p.B(700, 260, 240, 64, "provisionador da classe<br>CSI controller", "conceito")
    disco = p.DISCO(1040, 150, 170, 76, "disco real")
    pv = p.I("pv", 1040, 380, "PV<br>tamanho exato ·<br>reclaimPolicy da classe", pos="right")
    p.seta(pod, pvc)
    p.seta(pvc, pr)
    p.seta(pr, disco, "cria", saida=(1, 0.3))
    p.seta(pr, pv, "cria", saida=(1, 0.7))
    p.seta(pv, pvc, "bound", saida=(0.5, 1), entrada=(0.5, 1), pontos=[(1040, 450), (380, 450)])
    return p


def reclaim_policy() -> Pagina:
    # Origem: docs/04-storage/reclaim-policy.md.
    p = Pagina("reclaimPolicy: Retain × Delete", 1180, 460)
    p.cabecalho("reclaimPolicy: Retain × Delete", "O que acontece com o PV e o disco quando o PVC é apagado")
    cmd = p.CMD(140, 240, 200, 50, "kubectl delete pvc")
    d = p.DEC(420, 240, 180, 100, "reclaimPolicy<br>do PV")
    r = p.I("pv", 740, 150, "PV Released<br>claimRef antigo continua<br>dados intactos")
    a = p.I("pv", 1060, 150, "PV Available<br>pode ligar de novo")
    x = p.B(740, 370, 260, 64, "provisionador apaga o disco<br>PV removido", "erro")
    p.seta(cmd, d)
    p.seta(d, r, "Retain", saida=(0.5, 0), entrada=(0, 0.5), pontos=[(420, 150)])
    p.seta(d, x, "Delete", saida=(0.5, 1), entrada=(0, 0.5), pontos=[(420, 370)])
    p.seta(r, a, "admin limpa claimRef")
    return p


def expansao_pvc() -> Pagina:
    # Origem: docs/04-storage/expansao-pvc.md.
    p = Pagina("Expansão de PVC", 1440, 330)
    p.cabecalho("Expansão de PVC", "Aumentar o número no PVC dispara o disco e depois o filesystem")
    e = p.CMD(130, 180, 220, 64, "kubectl edit/patch PVC<br>5Gi → 10Gi")
    a = p.I("api", 390, 180, "kube-apiserver<br>admissão confere<br>allowVolumeExpansion")
    r = p.B(650, 180, 200, 64, "resizer do CSI<br>aumenta o disco real", "conceito")
    pv = p.I("pv", 900, 180, "PV com 10Gi")
    k = p.I("kubelet", 1110, 180, "kubelet do nó<br>aumenta o filesystem")
    c = p.I("pvc", 1330, 180, "PVC<br>status.capacity 10Gi")
    for o, d in ((e, a), (a, r), (r, pv), (pv, k), (k, c)):
        p.seta(o, d)
    return p


# ====================================================================== Domínio 5
def troubleshooting_visao_geral() -> Pagina:
    # Origem: docs/05-troubleshooting/index.md. Perguntas na coluna da esquerda, respostas à direita.
    p = Pagina("Troubleshooting: por onde começar", 1220, 820)
    p.cabecalho("Troubleshooting: por onde começar", "Cada pergunta elimina uma camada")
    a = p.DEC(220, 160, 220, 100, "kubectl responde?")
    b = p.DEC(220, 360, 240, 120, "kubectl get nodes:<br>algum NotReady?")
    c = p.DEC(220, 560, 220, 100, "Pod com problema")
    cp = p.B(760, 160, 340, 80, "Control plane:<br>ssh cp, crictl ps -a,<br>/var/log/pods, manifestos")
    p.I("master", 980, 160, "")
    n = p.B(760, 360, 340, 80, "Nó: ssh, systemctl status kubelet,<br>journalctl -u kubelet, containerd")
    p.I("node", 980, 360, "")
    lg = p.B(760, 560, 340, 64, "kubectl logs --previous<br>+ exit code")
    s = p.B(760, 740, 340, 64, "Service, Endpoints,<br>DNS, NetworkPolicy")
    e = p.B(220, 740, 300, 56, "kubectl describe pod → Events")
    p.I("pod", 60, 560, "")
    p.seta(a, cp, "não")
    p.seta(a, b, "sim", saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(b, n, "sim")
    p.seta(b, c, "não", saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(c, e, "Pending / ImagePull / Config", saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(c, lg, "CrashLoopBackOff")
    p.seta(c, s, "Running mas não atende", saida=(0.75, 0.75), entrada=(0, 0.5),
           pontos=[(480, 585), (480, 740)])
    return p


def logs_eventos() -> Pagina:
    # Origem: docs/05-troubleshooting/logs-eventos.md. Uma linha por fonte de informação.
    p = Pagina("Logs e eventos: onde procurar o quê", 1200, 580)
    p.cabecalho("Logs e eventos: onde procurar o quê", "Três fontes diferentes, cada uma com o seu comando")
    app = p.B(150, 170, 230, 56, "app no container<br>stdout / stderr", "conceito")
    rt = p.ARQ(500, 170, 260, 56, "containerd grava em<br>/var/log/pods/...")
    kl = p.CMD(960, 120, 200, 46, "kubectl logs")
    cr = p.CMD(960, 220, 200, 46, "crictl logs")
    k8s = p.B(150, 360, 230, 56, "scheduler, kubelet,<br>controladores", "conceito")
    ev = p.CMD(960, 360, 260, 56, "kubectl get events<br>kubectl describe")
    ku = p.B(150, 500, 230, 56, "kubelet e containerd<br>serviços systemd")
    j = p.CMD(960, 500, 200, 46, "journalctl -u ...")
    p.seta(app, rt)
    p.seta(rt, kl, "kubelet lê", saida=(1, 0.3))
    p.seta(rt, cr, "no nó", saida=(1, 0.7))
    p.seta(k8s, ev, "objetos Event")
    p.seta(ku, j)
    return p


def pods() -> Pagina:
    # Origem: docs/05-troubleshooting/pods.md. Perguntas na linha de cima; cada "não" desce para o estado.
    p = Pagina("Pods: de criado a Running", 1380, 520)
    p.cabecalho("Pods: de criado a Running", "Cada estado de erro mostra em que etapa o Pod parou")
    a = p.I("pod", 90, 200, "Pod criado")
    s = p.DEC(320, 200, 180, 100, "scheduler<br>achou nó?")
    k = p.DEC(660, 200, 200, 110, "kubelet: volume,<br>rede, imagem")
    r = p.DEC(1000, 200, 180, 100, "processo<br>continua vivo?")
    ok = p.B(1260, 200, 140, 50, "Running", "ok")
    pend = p.B(320, 430, 160, 50, "Pending", "espera")
    img = p.B(540, 430, 200, 50, "ImagePullBackOff", "erro")
    cfg = p.B(800, 430, 260, 50, "CreateContainerConfigError", "erro")
    cl = p.B(1100, 430, 200, 50, "CrashLoopBackOff", "erro")
    p.seta(a, s)
    p.seta(s, k, "sim")
    p.seta(k, r, "ok")
    p.seta(r, ok, "sim")
    p.seta(s, pend, "não", saida=(0.5, 1), entrada=(0.5, 0))
    p.seta(k, img, "imagem falhou", saida=(0.3, 0.85), entrada=(0.5, 0))
    p.seta(k, cfg, "config falhou", saida=(0.7, 0.85), entrada=(0.5, 0))
    p.seta(r, cl, "morre e reinicia", saida=(0.5, 1), entrada=(0.5, 0), pontos=[(1000, 360), (1100, 360)])
    return p


def no_notready() -> Pagina:
    # Origem: docs/05-troubleshooting/no-notready.md. Em cima o nó; embaixo o que o control plane faz.
    p = Pagina("Nó NotReady: a cadeia do kubelet", 1200, 620)
    p.cabecalho("Nó NotReady: a cadeia do kubelet", "Se qualquer elo cai, o nó para de dar notícia")
    p.fronteira(30, 100, 1140, 230, "Nó", "k8s", tracejada=False, icone="node")
    sd = p.B(150, 210, 160, 50, "systemd")
    k = p.I("kubelet", 440, 210, "kubelet<br>/var/lib/kubelet/config.yaml")
    c = p.B(760, 210, 180, 50, "containerd")
    pc = p.I("pod", 1040, 210, "containers dos Pods")
    p.fronteira(30, 370, 1140, 220, "Control plane", "k8s", tracejada=False, icone="master")
    api = p.I("api", 440, 470, "kube-apiserver")
    nc = p.I("c_m", 760, 470, "node controller<br>sem notícia ~50 s: Unknown")
    e = p.B(1040, 470, 220, 50, "Pods saem após 300 s", "erro")
    p.seta(sd, k, "inicia")
    p.seta(k, c, "CRI socket")
    p.seta(c, pc)
    p.seta(k, api, "kubelet.conf + cert do cliente", saida=(0.5, 1), entrada=(0.5, 0), pos_rotulo=-0.2)
    p.seta(api, nc)
    p.seta(nc, e, "taint not-ready /<br>unreachable")
    return p


def control_plane() -> Pagina:
    # Origem: docs/05-troubleshooting/control-plane.md.
    p = Pagina("Control plane: static Pods", 1460, 470)
    p.cabecalho("Control plane: static Pods", "O kubelet roda o control plane a partir de arquivos; a API só vê um espelho")
    m = p.ARQ(170, 190, 280, 64, "/etc/kubernetes/manifests/<br>kube-apiserver.yaml ...")
    k = p.I("kubelet", 500, 190, "kubelet do control plane")
    c = p.B(790, 190, 220, 56, "containers via containerd")
    lg = p.ARQ(1260, 190, 340, 56, "/var/log/pods/ns_pod_uid/container/N.log")
    api = p.I("api", 500, 380, "kube-apiserver", pos="left")
    v = p.CMD(900, 380, 340, 50, "kubectl get pods -n kube-system")
    p.seta(m, k, "observa a pasta")
    p.seta(k, c, "cria")
    p.seta(c, lg, "stdout/stderr")
    p.seta(api, v, "só um espelho<br>mirror Pod", tracejada=True)
    return p


DIAGRAMAS = {
    "01-rbac": rbac,
    "01-upgrade-kubeadm": upgrade_kubeadm,
    "01-kubeadm-certs": kubeadm_certs,
    "01-drain-cordon-uncordon": drain,
    "01-etcd-backup-restore": etcd_backup_restore,
    "01-helm-kustomize": helm_kustomize,
    "02-visao-geral": workloads_visao_geral,
    "02-deployments-rollout": deployments_rollout,
    "02-configmap-secret": configmap_secret,
    "02-requests-limits-qos": requests_limits_qos,
    "02-resourcequota": resourcequota,
    "02-taints-tolerations-nodeselector": taints,
    "02-affinity": affinity,
    "02-daemonset-job-cronjob-statefulset": controllers,
    "02-hpa": hpa,
    "03-services-endpoints": services_endpoints,
    "03-dns": dns,
    "03-network-policy": network_policy,
    "03-ingress": ingress,
    "03-gateway-api": gateway_api,
    "04-volumes-emptydir-hostpath": volumes,
    "04-pv-pvc": pv_pvc,
    "04-storageclass": storageclass,
    "04-reclaim-policy": reclaim_policy,
    "04-expansao-pvc": expansao_pvc,
    "05-visao-geral": troubleshooting_visao_geral,
    "05-logs-eventos": logs_eventos,
    "05-pods": pods,
    "05-no-notready": no_notready,
    "05-control-plane": control_plane,
}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    saida = Path(sys.argv[1])
    nomes = sys.argv[2:] or list(DIAGRAMAS)
    desconhecidos = [n for n in nomes if n not in DIAGRAMAS]
    if desconhecidos:
        print(f"diagrama desconhecido: {', '.join(desconhecidos)}; existem: {', '.join(DIAGRAMAS)}")
        return 1
    saida.mkdir(parents=True, exist_ok=True)
    for nome in nomes:
        arq = saida / f"{nome}.drawio"
        arq.write_text(DIAGRAMAS[nome]().xml(), encoding="utf-8")
        print(f"gerado: {arq}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
