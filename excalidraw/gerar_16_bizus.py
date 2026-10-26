"""Gerador de diagramas Excalidraw (.excalidraw, JSON v2) no estilo "limpo" aprovado pelo usuario.

Uso: python gerar_13_trilhas.py <saida.excalidraw>
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
text(60, 30, "Três dicas de quem passou, testadas antes de entrar no site", size=36)
text(60, 85, "Cada dica virou uma seção com saída real: o lab foi recriado na Azure só para isso.", size=20, color=CINZA)

text(60, 160, "1. A DICA", size=22, color=LARANJA)
dica1 = box(60, 230, 340, 110, "kubectl explain\nsalvar só um trecho", fill=LARANJA_F, stroke=LARANJA)
dica2 = box(60, 380, 340, 110, "ServiceAccount\nnos Pods", fill=LARANJA_F, stroke=LARANJA)
dica3 = box(60, 530, 340, 110, "Receitas de\nNetworkPolicy (14)", fill=LARANJA_F, stroke=LARANJA)

text(480, 160, "2. O LAB — a bancada", size=22, color=VERDE)
lab = box(480, 330, 400, 200, "Cluster kubeadm v1.37.1\n3 VMs na Azure\nrecriadas igual às antigas\nCalico para a política valer", fill=VERDE_F, stroke=VERDE)

text(960, 160, "3. A PÁGINA", size=22, color=AZUL)
pag1 = box(960, 230, 400, 110, "Comandos de memória\n+ treino de explain", fill=AZUL_F, stroke=AZUL)
pag2 = box(960, 380, 400, 110, "RBAC\n+ seção ServiceAccount", fill=AZUL_F, stroke=AZUL)
pag3 = box(960, 530, 400, 110, "NetworkPolicy\n+ tabela das receitas", fill=AZUL_F, stroke=AZUL)

arrow(dica1, lab, color=LARANJA)
arrow(dica2, lab, color=LARANJA)
arrow(dica3, lab, color=LARANJA)
arrow(lab, pag1, color=VERDE)
arrow(lab, pag2, color=VERDE, label="saída real")
arrow(lab, pag3, color=VERDE)

text(60, 690, "Como cada dica entrou", size=24)
passos(60, 740, ["1. Ouve a dica\nde quem passou", "2. Monta o cenário\nno lab", "3. Roda e confere\no resultado", "4. Cola a saída\nna página", "5. Builds e\nscreenshots"],
       [(LARANJA, LARANJA_F), (VERDE, VERDE_F), (VERDE, VERDE_F), (AZUL, AZUL_F), (AZUL, AZUL_F)])
text(60, 870, "Achado do caminho: com o kubeconfig do admin, o --token não troca de usuário; o certificado vence. Virou aviso na página.", size=18)
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
