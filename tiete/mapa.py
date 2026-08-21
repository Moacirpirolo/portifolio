"""
Desenha o Rio Tiete em SVG a partir da geometria da ANA e do IBGE.

O rio e cortado em segmentos; cada segmento guarda a estacao mais proxima ao
longo do curso, para o JS poder pintar o rio conforme o parametro escolhido
sem precisar redesenhar nada.

Sao dois mapas: o geral, com os 950 km, e o detalhe da regiao metropolitana,
onde quatro estacoes ficam a poucos quilometros uma da outra.
"""

import math

# deslocamento (dx, dy) do rotulo de cada estacao em cada mapa
ROTULOS_GERAL = {
    "EF35": (-16, 34),
    "EF36": (0, -22),
}
ROTULOS_METRO = {
    "EF01": (-4, -26),
    "EF29": (-10, 36),
    "EF02": (6, -26),
    "EF28": (-16, 38),
}


def mercator(lon, lat):
    return math.radians(lon), math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


class Projecao:
    """Encaixa um conjunto de coordenadas na area do desenho, sem distorcer."""

    def __init__(self, pontos, largura, altura, margem):
        proj = [mercator(*p) for p in pontos]
        self.x0, self.x1 = min(p[0] for p in proj), max(p[0] for p in proj)
        self.y0, self.y1 = min(p[1] for p in proj), max(p[1] for p in proj)
        util_x = largura - margem["esq"] - margem["dir"]
        util_y = altura - margem["topo"] - margem["base"]
        largura_geo = max(self.x1 - self.x0, 1e-9)
        altura_geo = max(self.y1 - self.y0, 1e-9)
        self.escala = min(util_x / largura_geo, util_y / altura_geo)
        self.dx = margem["esq"] + (util_x - largura_geo * self.escala) / 2
        self.dy = margem["topo"] + (util_y - altura_geo * self.escala) / 2

    def __call__(self, lon, lat):
        x, y = mercator(lon, lat)
        return (self.dx + (x - self.x0) * self.escala,
                self.dy + (self.y1 - y) * self.escala)


def caminho(pontos, proj, fechar=False):
    if not pontos:
        return ""
    d = [f"{'M' if i == 0 else 'L'}{proj(p[0], p[1])[0]:.1f} {proj(p[0], p[1])[1]:.1f}"
         for i, p in enumerate(pontos)]
    return "".join(d) + ("Z" if fechar else "")


def suavizar(pontos, proj):
    """Bezier quadratica entre os pontos medios: o rio nao fica anguloso."""
    pts = [proj(p[0], p[1]) for p in pontos]
    if len(pts) < 3:
        return caminho(pontos, proj)
    d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d.append(f"Q{pts[i][0]:.1f} {pts[i][1]:.1f} {mx:.1f} {my:.1f}")
    d.append(f"L{pts[-1][0]:.1f} {pts[-1][1]:.1f}")
    return "".join(d)


def indice_mais_proximo(pontos, lon, lat):
    melhor, indice = None, 0
    for i, (plon, plat) in enumerate(pontos):
        d = (plon - lon) ** 2 + (plat - lat) ** 2
        if melhor is None or d < melhor:
            melhor, indice = d, i
    return indice


def _dentro(pontos, proj, largura, altura, folga=40):
    """Descarta partes de geometria de contexto que caem fora do enquadramento."""
    visiveis = []
    atual = []
    for p in pontos:
        x, y = proj(p[0], p[1])
        if -folga <= x <= largura + folga and -folga <= y <= altura + folga:
            atual.append(p)
        else:
            if len(atual) > 1:
                visiveis.append(atual)
            atual = []
    if len(atual) > 1:
        visiveis.append(atual)
    return visiveis


def montar(geo, estacoes, faixa=None, largura=1000, altura=520, margem=None,
           rotulos=None, com_estado=True, prefixo="g", marcos=True, anotacoes=None):
    """Devolve (svg, metadados). `faixa` recorta o rio por indice de vertice."""
    margem = margem or {"esq": 30, "dir": 30, "topo": 40, "base": 40}
    rotulos = rotulos if rotulos is not None else ROTULOS_GERAL
    rio_todo = [tuple(p) for p in geo["tiete"]]
    km_todo = geo["km"]
    ini, fim = faixa or (0, len(rio_todo))
    rio, km = rio_todo[ini:fim], km_todo[ini:fim]
    proj = Projecao(rio, largura, altura, margem)

    ancoras = []
    for est in estacoes:
        if est.get("lat") is None:
            continue
        i = indice_mais_proximo(rio_todo, est["lon"], est["lat"])
        if ini <= i < fim:
            ancoras.append({"codigo": est["codigo"], "indice": i - ini,
                            "km": round(km_todo[i], 1), "estacao": est})
    ancoras.sort(key=lambda a: a["indice"])

    passo = max(2, len(rio) // 90)
    segmentos = []
    for a in range(0, len(rio) - 1, passo):
        b = min(a + passo, len(rio) - 1)
        meio = (a + b) // 2
        dono = min(ancoras, key=lambda x: abs(x["indice"] - meio)) if ancoras else None
        segmentos.append({"d": suavizar(rio[a:b + 1], proj),
                          "estacao": dono["codigo"] if dono else None,
                          "km": round(km[meio], 1)})

    partes = []
    if com_estado:
        for anel in geo.get("estado", []):
            partes.append(f'<path class="uf" d="{caminho(anel, proj, fechar=True)}"/>')

    for afl in geo.get("afluentes", []):
        for parte in afl.get("partes", []):
            for visivel in _dentro([tuple(p) for p in parte], proj, largura, altura):
                partes.append(f'<path class="afluente" d="{suavizar(visivel, proj)}">'
                              f'<title>{afl["nome"]}</title></path>')

    partes.append(f'<path class="leito" d="{suavizar(rio, proj)}"/>')
    for i, seg in enumerate(segmentos):
        alvo = f' data-estacao="{seg["estacao"]}"' if seg["estacao"] else ""
        partes.append(f'<path class="trecho" id="{prefixo}-trecho-{i}"{alvo} '
                      f'data-km="{seg["km"]}" d="{seg["d"]}"/>')
    partes.append(f'<path class="correnteza" d="{suavizar(rio, proj)}"/>')

    if marcos:
        nx, ny = proj(*rio[0])
        fx, fy = proj(*rio[-1])
        partes.append(f'<circle class="marco" cx="{nx:.1f}" cy="{ny:.1f}" r="3"/>')
        partes.append(f'<text class="marco-txt" x="{nx - 4:.1f}" y="{ny + 30:.1f}" '
                      f'text-anchor="end">nascente · Salesópolis</text>')
        partes.append(f'<circle class="marco" cx="{fx:.1f}" cy="{fy:.1f}" r="3"/>')
        partes.append(f'<text class="marco-txt" x="{fx - 8:.1f}" y="{fy + 20:.1f}" '
                      f'text-anchor="end">foz · rio Paraná</text>')

    for ancora in ancoras:
        est = ancora["estacao"]
        x, y = proj(*rio[ancora["indice"]])
        rot = rotulos.get(est["codigo"])
        marcacao = (f'<g class="pino" data-estacao="{est["codigo"]}" tabindex="0" '
                    f'role="button" aria-label="{est["codigo"]} {est["nome"]}">')
        if rot:
            dx, dy = rot
            anc = "middle" if abs(dx) < 12 else ("start" if dx > 0 else "end")
            marcacao += (f'<line class="guia" x1="{x:.1f}" y1="{y:.1f}" '
                         f'x2="{x + dx * 0.8:.1f}" y2="{y + dy * 0.66:.1f}"/>')
        marcacao += (f'<circle class="halo" cx="{x:.1f}" cy="{y:.1f}" r="12"/>'
                     f'<circle class="ponto" cx="{x:.1f}" cy="{y:.1f}" r="6"/>')
        if rot:
            marcacao += (f'<text class="cod" x="{x + dx:.1f}" y="{y + dy:.1f}" '
                         f'text-anchor="{anc}">{est["codigo"]}</text>'
                         f'<text class="cidade" x="{x + dx:.1f}" '
                         f'y="{y + dy + (13 if dy > 0 else -13):.1f}" '
                         f'text-anchor="{anc}">{est["nome"]}</text>')
        partes.append(marcacao + "</g>")

    for nota in (anotacoes or []):
        x, y = proj(nota["lon"], nota["lat"])
        anc = nota.get("anc", "start")
        dx, dy = nota.get("dx", 0), nota.get("dy", 0)
        partes.append(f'<line class="guia-nota" x1="{x:.1f}" y1="{y:.1f}" '
                      f'x2="{x + dx:.1f}" y2="{y + dy:.1f}"/>')
        for i, linha in enumerate(nota["texto"].split("|")):
            partes.append(f'<text class="nota" x="{x + dx + (6 if anc == "start" else -6):.1f}" '
                          f'y="{y + dy + i * 14:.1f}" text-anchor="{anc}">{linha}</text>')

    svg = (f'<svg viewBox="0 0 {largura} {altura}" class="mapa" role="img" '
           f'aria-label="Rio Tietê e as estações automáticas da CETESB">'
           + "".join(partes) + "</svg>")
    meta = {"km_inicio": round(km[0], 1), "km_fim": round(km[-1], 1),
            "estacoes": [a["codigo"] for a in ancoras],
            "segmentos": [{"id": f"{prefixo}-trecho-{i}", "estacao": s["estacao"], "km": s["km"]}
                          for i, s in enumerate(segmentos)]}
    return svg, meta


def faixa_metropolitana(geo, estacoes, folga=6):
    """Indices do traçado que cobrem da nascente ate a ultima estacao do Alto Tiete."""
    rio = [tuple(p) for p in geo["tiete"]]
    indices = [indice_mais_proximo(rio, e["lon"], e["lat"])
               for e in estacoes
               if e.get("lat") is not None and e["codigo"] in ROTULOS_METRO]
    if not indices:
        return (0, len(rio))
    return (0, min(len(rio), max(indices) + folga))
