"""Gerador de diagramas Excalidraw (.excalidraw, JSON v2) no estilo "limpo" aprovado pelo usuario.

Uso: python gerar_07_workloads_scheduling.py <saida.excalidraw>
Edite somente a secao DIAGRAMA. Helpers:
  text(x, y, "texto", size)                      texto solto
  box(x, y, w, h, "Nome — papel\\nfrase", fill, stroke)   caixa com texto vinculado (centralizado)
  frame(x, y, w, h, "TITULO", fill, stroke)       area tracejada com titulo (agrupa caixas)
  arrow(a, b, color, label)                       seta presa a duas caixas
  passos(x, y, ["1. ...", "2. ..."], cores)       fluxo numerado em linha
Ao final valida ids, bindings, contagem (<= 80) e tamanho do canvas.
"""
import json, random, sys, time
from pathlib import Path

random.seed(7)
ELEMENTS = []
NOW = int(time.time() * 1000)
FONT = 1  # 1 = Virgil (mao livre), 2 = Helvetica, 3 = Cascadia


def _id():
    return "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(16))


def _base(kind, x, y, w, h, **kw):
    e = {"id": _id(), "type": kind, "x": x, "y": y, "width": w, "height": h, "angle": 0,
         "strokeColor": "#1e1e1e", "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2,
         "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
         "roundness": {"type": 3} if kind == "rectangle" else None, "seed": random.randint(1, 2**31), "version": 1,
         "versionNonce": random.randint(1, 2**31), "isDeleted": False, "boundElements": [], "updated": NOW,
         "link": None, "locked": False}
    e.update(kw)
    ELEMENTS.append(e)
    return e


def text(x, y, s, size=18, color="#1e1e1e", align="left", w=None, container=None, valign="top"):
    lines = s.split("\n")
    est_w = w or max(len(l) for l in lines) * size * 0.55
    est_h = len(lines) * size * 1.25
    return _base("text", x, y, est_w, est_h, text=s, fontSize=size, fontFamily=FONT, textAlign=align,
                 verticalAlign=valign, baseline=size, containerId=container, originalText=s, lineHeight=1.25,
                 strokeColor=color, roundness=None)


def box(x, y, w, h, label, fill="#ffffff", stroke="#1e1e1e", size=17, color="#1e1e1e", dashed=False):
    r = _base("rectangle", x, y, w, h, backgroundColor=fill, strokeColor=stroke,
              strokeStyle="dashed" if dashed else "solid")
    th = len(label.split("\n")) * size * 1.25
    t = text(x + 10, y + (h - th) / 2, label, size=size, align="center", w=w - 20, container=r["id"],
             valign="middle", color=color)
    r["boundElements"].append({"id": t["id"], "type": "text"})
    return r


def frame(x, y, w, h, title, fill, stroke, size=20):
    r = _base("rectangle", x, y, w, h, backgroundColor=fill, strokeColor=stroke, strokeStyle="dashed")
    text(x + 15, y + 10, title, size=size, color=stroke)
    return r


def arrow(a, b, color="#1e1e1e", label=None, size=16):
    def c(e):
        return e["x"] + e["width"] / 2, e["y"] + e["height"] / 2

    def port(e, tx, ty):
        cx, cy = c(e)
        dx, dy = tx - cx, ty - cy
        if abs(dx) * e["height"] > abs(dy) * e["width"]:
            return (e["x"] + e["width"] if dx > 0 else e["x"]), cy
        return cx, (e["y"] + e["height"] if dy > 0 else e["y"])

    ax, ay = c(a); bx, by = c(b)
    sx, sy = port(a, bx, by); ex, ey = port(b, ax, ay)
    ar = _base("arrow", sx, sy, ex - sx, ey - sy, points=[[0, 0], [ex - sx, ey - sy]], lastCommittedPoint=None,
               startBinding={"elementId": a["id"], "focus": 0, "gap": 4}, endBinding={"elementId": b["id"], "focus": 0, "gap": 4},
               startArrowhead=None, endArrowhead="arrow", strokeColor=color, strokeWidth=3, roundness={"type": 2})
    a["boundElements"].append({"id": ar["id"], "type": "arrow"})
    b["boundElements"].append({"id": ar["id"], "type": "arrow"})
    if label:
        tw = len(label) * size * 0.55 + 10
        th = size * 1.25
        t = text((sx + ex) / 2 - tw / 2, (sy + ey) / 2 - th / 2, label, size=size, align="center", w=tw,
                 container=ar["id"], valign="middle", color=color)
        ar["boundElements"].append({"id": t["id"], "type": "text"})
    return ar


def passos(x, y, itens, cores, w=290, h=100, gap=40, size=17):
    """Fluxo numerado: caixas em linha ligadas por setas. cores = lista de (stroke, fill)."""
    caixas = []
    for i, (p, (s, f)) in enumerate(zip(itens, cores)):
        caixas.append(box(x + i * (w + gap), y, w, h, p, fill=f, stroke=s, size=size))
    for a, b in zip(caixas, caixas[1:]):
        arrow(a, b, color="#495057")
    return caixas


# paleta (3 papeis + 1 destaque)
LARANJA, LARANJA_F = "#e8590c", "#fff4e6"   # quem pede / app
AZUL, AZUL_F = "#1971c2", "#e7f5ff"         # quem decide / controle
VERDE, VERDE_F = "#2f9e44", "#ebfbee"       # quem executa
AMARELO, AMARELO_F = "#e67700", "#fff3bf"   # destaque unico (ex.: banco/caderno)
CINZA = "#495057"

# =============================================================== DIAGRAMA (edite daqui)
text(60, 30, "Do YAML ao Pod rodando no nó certo", size=36)
text(60, 85, "O controlador mantém as cópias, o scheduler escolhe o nó pelas reservas e regras, e o kubelet faz rodar com limites e configuração.", size=20, color=CINZA)

text(60, 160, "1. QUEM PEDE", size=22, color=LARANJA)
voce = box(60, 230, 300, 130, "Você — kubectl apply\nDeployment, DaemonSet,\nJob, CronJob, StatefulSet", fill=LARANJA_F, stroke=LARANJA)
hpa = box(60, 470, 300, 130, "HPA — o termostato\nMede a CPU e muda\no número de réplicas", fill=AZUL_F, stroke=AZUL)

text(440, 160, "2. QUEM DECIDE", size=22, color=AZUL)
frame(440, 200, 460, 520, "", AZUL_F, AZUL)
api = box(470, 230, 400, 120, "API Server + Quota — a portaria\nRecusa o que estoura o teto\ndo namespace", fill="#ffffff", stroke=AZUL)
ctrl = box(470, 390, 400, 120, "Controlador — o gerente\nMantém N cópias e\nrecria o que morre", fill="#ffffff", stroke=AZUL)
sched = box(470, 550, 400, 140, "Scheduler — quem distribui\nRequests, taints, nodeSelector\ne affinity escolhem o nó", fill="#ffffff", stroke=AZUL)

text(980, 160, "3. QUEM EXECUTA", size=22, color=VERDE)
cfg = box(980, 230, 380, 120, "ConfigMap e Secret\na ficha de instruções\nVariáveis e arquivos do app", fill=AMARELO_F, stroke=AMARELO)
kubelet = box(980, 400, 380, 120, "kubelet — o encarregado do nó\nAplica limits e QoS", fill=VERDE_F, stroke=VERDE)
pod = box(980, 570, 380, 120, "Pod rodando\nno nó escolhido", fill=VERDE_F, stroke=VERDE)

arrow(voce, api, color=LARANJA)
arrow(api, ctrl, color=AZUL)
arrow(hpa, ctrl, color=AZUL, label="ajusta réplicas")
arrow(ctrl, sched, color=AZUL, label="cria Pods")
arrow(sched, kubelet, color=AZUL, label="escolhe o nó")
arrow(cfg, kubelet, color=AMARELO, label="entrega")
arrow(kubelet, pod, color=VERDE)

text(60, 770, "Um Deployment novo, passo a passo", size=24)
passos(60, 820, ["1. Você aplica\no Deployment", "2. Quota confere\no teto do namespace", "3. Controlador cria\nos Pods que faltam", "4. Scheduler acha\num nó que caiba", "5. kubelet sobe com\nlimits e config"],
       [(LARANJA, LARANJA_F), (AZUL, AZUL_F), (AZUL, AZUL_F), (AZUL, AZUL_F), (VERDE, VERDE_F)])
text(60, 950, "Pod Pending quase sempre é o passo 4: falta reserva livre, sobra taint ou nenhuma regra de affinity casa.", size=18)
# =============================================================== fim do DIAGRAMA


def main(out):
    doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": ELEMENTS,
           "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    # validacao
    ids = {e["id"] for e in ELEMENTS}
    assert len(ids) == len(ELEMENTS), "ids duplicados"
    quebradas = [e["id"] for e in ELEMENTS if e.get("containerId") and e["containerId"] not in ids]
    quebradas += [e["id"] for e in ELEMENTS if e["type"] == "arrow" for k in ("startBinding", "endBinding") if e[k] and e[k]["elementId"] not in ids]
    quebradas += [e["id"] for e in ELEMENTS for be in e["boundElements"] if be["id"] not in ids]
    assert not quebradas, f"referencias quebradas: {quebradas}"
    W = int(max(e["x"] + e["width"] for e in ELEMENTS)); H = int(max(e["y"] + e["height"] for e in ELEMENTS))
    n = len(ELEMENTS)
    aviso = " (ACIMA DO TETO: simplifique ou divida)" if n > 80 or W > 1700 or H > 1400 else ""
    print(f"{out}: {n} elementos, canvas {W}x{H}{aviso}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "diagrama.excalidraw")
