"""Gerador de diagramas Excalidraw (.excalidraw, JSON v2) no estilo "limpo" aprovado pelo usuario.

Uso: python gerar_04_trafego_entrada.py <saida.excalidraw>
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
text(60, 30, "Do lado de fora até o Pod: quem leva e quem deixa entrar", size=36)
text(60, 85, "Ingress ou Gateway escolhem o Service pelo host e caminho; a NetworkPolicy decide se o Pod aceita a conexão.", size=20, color=CINZA)

text(60, 160, "1. QUEM CHEGA", size=22, color=LARANJA)
cli = box(60, 360, 300, 140, "Cliente de fora\nAbre loja.exemplo.com/api\nno navegador", fill=LARANJA_F, stroke=LARANJA)

text(440, 160, "2. A PORTA DE ENTRADA (um dos dois)", size=22, color=AZUL)
frame(440, 200, 460, 520, "", AZUL_F, AZUL)
ing = box(470, 230, 400, 130, "Ingress — a portaria clássica\nRegras de host e caminho\nnum objeto só", fill="#ffffff", stroke=AZUL)
gw = box(470, 410, 400, 110, "Gateway — a porta\nPorta, protocolo e certificado", fill="#ffffff", stroke=AZUL)
route = box(470, 560, 400, 130, "HTTPRoute — a placa de direção\nHost, caminho, cabeçalho e peso\n→ qual Service", fill="#ffffff", stroke=AZUL)

text(980, 160, "3. QUEM DEIXA ENTRAR", size=22, color=VERDE)
svc = box(980, 230, 380, 120, "Service — o número fixo\nAcha os Pods pelos labels", fill=AZUL_F, stroke=AZUL)
np = box(980, 400, 380, 140, "NetworkPolicy\na lista de convidados\nQuem pode entrar e sair;\no plugin de rede aplica", fill=AMARELO_F, stroke=AMARELO)
pods = box(980, 590, 380, 120, "Pods do app — quem atende\nSó recebe o que a lista permite", fill=VERDE_F, stroke=VERDE)

arrow(cli, ing, color=LARANJA)
arrow(cli, gw, color=LARANJA)
arrow(gw, route, color=AZUL, label="rotas se ligam")
arrow(ing, svc, color=AZUL)
arrow(route, svc, color=AZUL)
arrow(svc, np, color=AMARELO, label="confere a origem")
arrow(np, pods, color=VERDE, label="liberado")

text(60, 770, "Uma requisição, passo a passo", size=24)
passos(60, 820, ["1. Cliente chama\nloja.exemplo.com/api", "2. Ingress ou Gateway\nlê host e caminho", "3. A regra que casa\nescolhe o Service", "4. NetworkPolicy\nconfere quem chama", "5. Pod responde\n(ou a conexão expira)"],
       [(LARANJA, LARANJA_F), (AZUL, AZUL_F), (AZUL, AZUL_F), (AMARELO, AMARELO_F), (VERDE, VERDE_F)])
text(60, 950, "Sem controller, Ingress e Gateway são só papel; sem plugin de rede que aplique, a NetworkPolicy também.", size=18)
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
