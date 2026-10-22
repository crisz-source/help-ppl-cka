"""Gerador de diagramas Excalidraw (.excalidraw, JSON v2) no estilo "limpo" aprovado pelo usuario.

Uso: python gerar_excalidraw.py <saida.excalidraw>
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
text(60, 30, "Services e DNS: como um Pod acha outro", size=36)
text(60, 85, "O DNS troca o nome por um IP fixo (o Service), e o kube-proxy troca esse IP pelo de um Pod que está pronto.", size=20, color=CINZA)

text(60, 160, "1. QUEM CHAMA", size=22, color=LARANJA)
cli = box(60, 200, 320, 140, "Pod cliente\nChama http://web-svc\npelo nome", fill=LARANJA_F, stroke=LARANJA)

text(460, 160, "2. QUEM TRADUZ", size=22, color=AZUL)
frame(460, 200, 440, 480, "", AZUL_F, AZUL)
dns = box(490, 230, 380, 110, "CoreDNS — a lista telefônica\nTroca o nome pelo IP do Service", fill="#ffffff", stroke=AZUL)
svc = box(490, 370, 380, 120, "Service — o número fixo\nIP que não muda, escolhe\nos Pods pelo selector (labels)", fill="#ffffff", stroke=AZUL)
eps = box(490, 520, 380, 130, "EndpointSlice\na lista de quem atende\nIPs dos Pods prontos, atualizada\nsozinha", fill=AMARELO_F, stroke=AMARELO)

text(990, 160, "3. QUEM ENTREGA", size=22, color=VERDE)
kp = box(990, 200, 360, 140, "kube-proxy — o telefonista\nEscreve regras em cada nó:\nIP do Service → IP de um Pod", fill=VERDE_F, stroke=VERDE)
pods = box(990, 420, 360, 140, "Pods do app\nquem atende\nRecebem na targetPort", fill=VERDE_F, stroke=VERDE)

arrow(cli, dns, color=LARANJA, label="qual o IP?")
arrow(svc, eps, color=AMARELO, label="selector")
arrow(eps, kp, color=VERDE, label="lê a lista")
arrow(kp, pods, color=VERDE, label="encaminha")

text(60, 720, "Uma chamada, passo a passo", size=24)
passos(60, 770, ["1. Pod pergunta\no nome ao CoreDNS", "2. Recebe o IP\ndo Service", "3. Envia para\nesse IP:port", "4. Regra do kube-proxy\ntroca por um Pod", "5. Pod responde\nna targetPort"],
       [(LARANJA, LARANJA_F), (AZUL, AZUL_F), (LARANJA, LARANJA_F), (VERDE, VERDE_F), (VERDE, VERDE_F)])
text(60, 900, "Service sem endpoints = selector errado ou Pods não prontos: o nome resolve, mas ninguém atende.", size=18)
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
