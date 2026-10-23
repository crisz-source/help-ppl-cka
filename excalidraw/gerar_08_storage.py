"""Gerador de diagramas Excalidraw (.excalidraw, JSON v2) no estilo "limpo" aprovado pelo usuario.

Uso: python gerar_08_storage.py <saida.excalidraw>
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
text(60, 30, "Onde o dado do Pod mora e quanto tempo vive", size=36)
text(60, 85, "O Pod pede disco por um PVC; o PVC se liga a um PV, pronto ou criado na hora pela StorageClass.", size=20, color=CINZA)

text(60, 160, "1. QUEM USA", size=22, color=LARANJA)
pod = box(60, 230, 300, 130, "Pod — quem grava\nMonta o volume\nnum caminho", fill=LARANJA_F, stroke=LARANJA)
ed = box(60, 470, 300, 140, "emptyDir — a gaveta da mesa\nVazia ao nascer;\nsome junto com o Pod", fill=LARANJA_F, stroke=LARANJA)

text(440, 160, "2. O PEDIDO", size=22, color=AZUL)
frame(440, 200, 460, 520, "", AZUL_F, AZUL)
pvc = box(470, 240, 400, 130, "PVC — o pedido\n5Gi, um nó por vez,\nclasse rápida", fill="#ffffff", stroke=AZUL)
sc = box(470, 520, 400, 140, "StorageClass — o catálogo\nSem PV pronto, cria um\ndo tamanho exato", fill="#ffffff", stroke=AZUL)

text(980, 160, "3. O DISCO", size=22, color=VERDE)
pv = box(980, 240, 380, 130, "PV — o disco reservado\nLigado a um PVC só", fill=VERDE_F, stroke=VERDE)
disco = box(980, 430, 380, 110, "Disco real\nNuvem, NFS ou pasta do nó", fill=VERDE_F, stroke=VERDE)
rec = box(980, 590, 380, 130, "reclaimPolicy\no que fazer no fim\nRetain guarda · Delete apaga", fill=AMARELO_F, stroke=AMARELO)

arrow(pod, pvc, color=LARANJA, label="pede por nome")
arrow(pod, ed, color=LARANJA)
arrow(pvc, pv, color=AZUL, label="liga 1 para 1")
arrow(pvc, sc, color=AZUL, label="sem PV pronto")
arrow(sc, pv, color=AZUL, label="cria")
arrow(pv, disco, color=VERDE)
arrow(disco, rec, color=AMARELO, label="PVC apagado")

text(60, 780, "Do pedido ao fim do disco, passo a passo", size=24)
passos(60, 830, ["1. Pod aponta\npara o PVC", "2. PVC procura PV\n(ou a classe cria)", "3. Ligação 1 para 1:\nPVC fica Bound", "4. Pod monta\ne grava", "5. PVC apagado:\nRetain guarda, Delete apaga"],
       [(LARANJA, LARANJA_F), (AZUL, AZUL_F), (AZUL, AZUL_F), (VERDE, VERDE_F), (AMARELO, AMARELO_F)])
text(60, 960, "Precisa de mais espaço? Aumente o número no PVC; só funciona se a StorageClass permitir expansão.", size=18)
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
