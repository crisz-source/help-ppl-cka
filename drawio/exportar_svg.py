"""Exporta os .drawio desta pasta para SVG prontos para o site (docs/assets/diagramas/).

Uso:
    python exportar_svg.py <pasta de saída> [nome.drawio ...]     (sem nome = todos)

O SVG do draw.io sai com três coisas que não servem para o site, e este script corrige:
1. Uma imagem PNG de reserva para cada rótulo (para visualizadores sem foreignObject). Os
   navegadores usam o texto HTML, então as PNGs só pesam (~290 KB de 330 KB num diagrama).
2. `color-scheme: light dark`: dentro de <img> o SVG segue o tema do sistema, não o botão
   claro/escuro do site, e o diagrama ficaria escuro numa página clara. Fica sempre claro.
3. Fontes sem alternativa (Consolas, Helvetica): quem não tem a fonte cai na serifada padrão.
"""
import re
import subprocess
import sys
import tempfile
import xml.dom.minidom
from pathlib import Path

DRAWIO = Path.home() / "AppData/Local/Programs/draw.io/draw.io.exe"
PASTA = Path(__file__).resolve().parent

PNG_RESERVA = re.compile(r'<image [^>]*xlink:href="data:image/png;base64,[^"]*"[^>]*/>')
FONTES = {
    "Consolas": "Consolas, 'Courier New', monospace",
    "Helvetica": "Helvetica, Arial, sans-serif",
}


def ajustar(svg: str) -> str:
    svg = PNG_RESERVA.sub("", svg)
    svg = svg.replace("color-scheme: light dark;", "color-scheme: light;")
    for fonte, pilha in FONTES.items():
        svg = svg.replace(f"font-family: {fonte};", f"font-family: {pilha};")
        svg = svg.replace(f'font-family="{fonte}"', f'font-family="{pilha}"')
    return svg


def exportar(origem: Path, destino: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        bruto = Path(tmp) / "bruto.svg"
        r = subprocess.run([str(DRAWIO), "-x", "-f", "svg", "-o", str(bruto), str(origem)],
                           capture_output=True, text=True)
        if not bruto.exists():
            raise RuntimeError(f"draw.io não gerou SVG para {origem.name}: {r.stdout}{r.stderr}")
        svg = ajustar(bruto.read_text(encoding="utf-8"))
    xml.dom.minidom.parseString(svg.encode("utf-8"))  # falha alto se o ajuste quebrou o XML
    if "data:image/png" in svg:
        raise RuntimeError(f"{origem.name}: sobrou PNG de reserva no SVG")
    destino.write_text(svg, encoding="utf-8")
    return len(svg.encode("utf-8"))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    saida = Path(sys.argv[1])
    saida.mkdir(parents=True, exist_ok=True)
    nomes = [PASTA / n for n in sys.argv[2:]] or sorted(PASTA.glob("*.drawio"))
    for origem in nomes:
        tamanho = exportar(origem, saida / f"{origem.stem}.svg")
        print(f"{tamanho / 1024:6.1f} KB  {origem.stem}.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
