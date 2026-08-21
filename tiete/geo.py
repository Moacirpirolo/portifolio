"""
Geometria do Rio Tiete e do contexto do mapa.

Fontes publicas:
  - ANA / SNIRH, Base Hidrografica Ottocodificada 2017 50K (trecho de drenagem)
  - IBGE, malha do estado de Sao Paulo

Gera geo_tiete.json com o traçado do rio ja encadeado da nascente para a foz,
os afluentes de contexto e a silhueta do estado.
"""

import gzip
import json
import math
import ssl
import urllib.parse
import urllib.request

ARCGIS = ("https://www.snirh.gov.br/arcgis/rest/services/SPR/"
          "BHO2017_50K_TRECHODRENAGEM/FeatureServer/0/query")
IBGE = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/35"
        "?formato=application/vnd.geo+json&qualidade=intermediaria")

AFLUENTES = [
    ("Rio Pinheiros", "NORIOCOMP='Rio Pinheiros'"),
    ("Rio Piracicaba", "NORIOCOMP='Rio Piracicaba'"),
    ("Rio Sorocaba", "NORIOCOMP='Rio Sorocaba'"),
    ("Rio Jundiai", "NORIOCOMP='Rio Jundiaí'"),
]

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def _json(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (mapa-tiete)"})
    with urllib.request.urlopen(req, timeout=180, context=_CTX) as r:
        bruto = r.read()
    if bruto[:2] == b"\x1f\x8b":
        bruto = gzip.decompress(bruto)
    return json.loads(bruto.decode("utf-8"))


def _linhas(geojson):
    """Extrai listas de coordenadas de qualquer geometria de linha."""
    saida = []
    for f in geojson.get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "LineString":
            saida.append((f.get("properties", {}), g["coordinates"]))
        elif g.get("type") == "MultiLineString":
            for parte in g["coordinates"]:
                saida.append((f.get("properties", {}), parte))
    return saida


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def encadear(trechos):
    """Junta os trechos num traçado unico, da nascente para a foz.

    A base da ANA traz NUDISTCDAG, a distancia do trecho ao longo do curso.
    Ordenar por ela do maior para o menor da a direcao nascente -> foz;
    a orientacao de cada trecho e corrigida pela ponta mais proxima.
    """
    trechos = sorted(trechos, key=lambda t: -t[0].get("NUDISTCDAG", 0))
    caminho = list(trechos[0][1])
    if len(trechos) > 1:
        # garante que o primeiro trecho comeca na ponta mais longe do proximo
        proximo = trechos[1][1]
        if _dist(caminho[0], proximo[0]) < _dist(caminho[-1], proximo[0]):
            caminho.reverse()
    for _, coords in trechos[1:]:
        pontos = list(coords)
        if _dist(caminho[-1], pontos[-1]) < _dist(caminho[-1], pontos[0]):
            pontos.reverse()
        caminho.extend(pontos)
    return caminho


def simplificar(pontos, tolerancia):
    """Douglas-Peucker em coordenadas geograficas."""
    if len(pontos) < 3:
        return list(pontos)

    def reta(p, a, b):
        if a == b:
            return _dist(p, a)
        t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / \
            ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)
        t = max(0, min(1, t))
        proj = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        return _dist(p, proj)

    pilha, manter = [(0, len(pontos) - 1)], {0, len(pontos) - 1}
    while pilha:
        ini, fim = pilha.pop()
        pior, indice = 0, None
        for i in range(ini + 1, fim):
            d = reta(pontos[i], pontos[ini], pontos[fim])
            if d > pior:
                pior, indice = d, i
        if indice is not None and pior > tolerancia:
            manter.add(indice)
            pilha.append((ini, indice))
            pilha.append((indice, fim))
    return [pontos[i] for i in sorted(manter)]


def km_acumulado(pontos):
    """Distancia acumulada em km ao longo do traçado (aproximacao local)."""
    acumulado, total = [0.0], 0.0
    for i in range(1, len(pontos)):
        lon1, lat1 = pontos[i - 1]
        lon2, lat2 = pontos[i]
        dx = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
        dy = (lat2 - lat1) * 110.57
        total += math.hypot(dx, dy)
        acumulado.append(total)
    return acumulado


def baixar():
    print("  Rio Tiete (ANA/SNIRH)...", end=" ", flush=True)
    tiete = _json(ARCGIS, {
        "where": "NORIOCOMP='Rio Tietê' AND NUCOMPCDA>1000",
        "outFields": "COTRECHO,NUCOMPTREC,NUDISTCDAG",
        "outSR": 4326, "f": "geojson",
    })
    traçado = encadear(_linhas(tiete))
    traçado = simplificar(traçado, 0.004)
    print(f"{len(traçado)} pontos")

    afluentes = []
    for nome, filtro in AFLUENTES:
        print(f"  {nome}...", end=" ", flush=True)
        dados = _json(ARCGIS, {"where": filtro, "outFields": "NUDISTCDAG",
                               "outSR": 4326, "f": "geojson"})
        linhas = _linhas(dados)
        if not linhas:
            print("sem geometria")
            continue
        # afluente nao e encadeado: cada trecho vira uma linha propria, senao
        # ramos distantes viram um risco reto atravessando o mapa
        partes = [simplificar(coords, 0.006) for _, coords in linhas]
        partes = [p for p in partes if len(p) > 1]
        afluentes.append({"nome": nome, "partes": partes})
        print(f"{len(partes)} trechos")

    print("  Estado de Sao Paulo (IBGE)...", end=" ", flush=True)
    sp = _json(IBGE)
    aneis = []
    for f in sp["features"]:
        g = f["geometry"]
        poligonos = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poli in poligonos:
            anel = simplificar(poli[0], 0.01)
            if len(anel) > 12:
                aneis.append(anel)
    print(f"{len(aneis)} contornos")

    return {
        "tiete": traçado,
        "km": km_acumulado(traçado),
        "afluentes": afluentes,
        "estado": aneis,
    }


if __name__ == "__main__":
    dados = baixar()
    with open("geo_tiete.json", "w", encoding="utf-8") as f:
        json.dump(dados, f)
    print("geo_tiete.json gravado")
