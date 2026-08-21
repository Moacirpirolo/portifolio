"""
Coleta de dados do SIMQUA (CETESB) para as estacoes automaticas do Rio Tiete.

Fonte publica, sem token: https://simqua.cetesb.sp.gov.br
O CSV vem em latin-1, separador ';', decimal com virgula, e a primeira linha
traz ate quando o dado foi validado pela CETESB.
"""

import csv
import io
import re
import json
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

BASE = "https://simqua.cetesb.sp.gov.br"

# Estacoes automaticas no Rio Tiete, na ordem do rio (nascente -> foz).
# 'id' e o codigo interno usado pelo SIMQUA no parametro 'e'.
ESTACOES = [
    {"id": 2,  "codigo": "EF01", "nome": "Mogi das Cruzes",  "municipio": "Mogi das Cruzes", "trecho": "Alto Tietê (montante da capital)"},
    {"id": 25, "codigo": "EF29", "nome": "Penha",            "municipio": "Guarulhos",       "trecho": "Região metropolitana"},
    {"id": 1,  "codigo": "EF02", "nome": "Rasgão",           "municipio": "Pirapora do Bom Jesus", "trecho": "Saída da região metropolitana"},
    {"id": 20, "codigo": "EF28", "nome": "Itu",              "municipio": "Itu",             "trecho": "Médio Tietê"},
    {"id": 3,  "codigo": "EF03", "nome": "Laranjal Paulista","municipio": "Laranjal Paulista", "trecho": "Médio Tietê"},
    {"id": 30, "codigo": "EF35", "nome": "Barra Bonita",     "municipio": "Barra Bonita",    "trecho": "Reservatório de Barra Bonita"},
    {"id": 32, "codigo": "EF36", "nome": "Promissão",        "municipio": "Promissão",       "trecho": "Baixo Tietê"},
]

# Codigos de parametro do SIMQUA
PARAMETROS = {
    "oxigenio": {"cod": 2, "rotulo": "Oxigênio dissolvido", "unidade": "mg/L"},
    "ph": {"cod": 1, "rotulo": "pH", "unidade": ""},
    "condutividade": {"cod": 3, "rotulo": "Condutividade elétrica", "unidade": "uS/cm"},
    "turbidez": {"cod": 4, "rotulo": "Turbidez", "unidade": "NTU"},
    "temperatura": {"cod": 5, "rotulo": "Temperatura da água", "unidade": "C"},
}

# Como o cabecalho do CSV nomeia cada parametro
COLUNA_PARA_CHAVE = {
    "oxigenio dissolvido": "oxigenio",
    "ph": "ph",
    "condutividade eletrica": "condutividade",
    "turbidez": "turbidez",
    "temperatura": "temperatura",
}

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def _sem_acento(txt):
    tabela = str.maketrans("áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ", "aaaaeeiooouucAAAAEEIOOOUUC")
    return txt.translate(tabela)


def _get(caminho, params, binario=False):
    url = BASE + caminho + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (coleta-tiete)"})
    with urllib.request.urlopen(req, timeout=60, context=_CTX) as r:
        dados = r.read()
    return dados if binario else dados.decode("utf-8", "replace")


def serie(estacao_id, tipo="dia", dias=30, params=None):
    """Baixa a serie de uma estacao. tipo: min, hor, dia, mes, ano."""
    params = params or list(PARAMETROS)
    fim = datetime.now()
    ini = fim - timedelta(days=dias)
    bruto = _get("/dados/", {
        "e": estacao_id,
        "p": ",".join(str(PARAMETROS[p]["cod"]) for p in params),
        "ini": ini.strftime("%d/%m/%YT%H:00"),
        "fim": fim.strftime("%d/%m/%YT%H:00"),
        "tipo": tipo,
        "hora": "all",
        "classif": 1,
        "tabela": 0,
        "formato": "csv",
    }, binario=True).decode("latin-1")

    linhas = bruto.splitlines()
    if not linhas or not linhas[0].startswith("Entidade"):
        return {"validado_ate": None, "registros": []}

    validado = linhas[0].split("validados até")[-1].strip() if "validados até" in linhas[0] else None
    leitor = csv.reader(io.StringIO("\n".join(linhas[1:])), delimiter=";")
    cabecalho = next(leitor, [])

    # mapeia posicao da coluna -> chave interna do parametro
    mapa = {}
    for i, col in enumerate(cabecalho[1:], start=1):
        nome = _sem_acento(col.split("(")[0].strip().lower())
        if nome in COLUNA_PARA_CHAVE:
            mapa[i] = COLUNA_PARA_CHAVE[nome]

    registros = []
    for linha in leitor:
        if not linha or not linha[0].strip():
            continue
        reg = {"data": linha[0].strip()}
        for i, chave in mapa.items():
            valor = linha[i].strip() if i < len(linha) else ""
            reg[chave] = float(valor.replace(",", ".")) if valor else None
        registros.append(reg)

    return {"validado_ate": validado, "registros": registros}


_PADRAO_PONTO = re.compile(
    r"ol\.geom\.Point\(\[(-?\d+\.\d+), (-?\d+\.\d+)\]\).*?"
    r"nome: '([^']+)'.*?pk: (\d+),\s*cidade: '([^']+)',\s*corpo_agua: '([^']+)',"
    r"\s*status_operacional: '([^']+)'", re.S)


def coordenadas():
    """Le latitude e longitude das estacoes no webgis do SIMQUA."""
    pagina = _get("/webgis/inicio/", {})
    mapa = {}
    for lon, lat, nome, pk, cidade, corpo, status in _PADRAO_PONTO.findall(pagina):
        mapa[int(pk)] = {
            "lat": float(lat), "lon": float(lon),
            "corpo_agua": corpo, "status_operacional": status,
        }
    return mapa


def coletar(dias_diario=90, dias_horario=7):
    """Coleta serie diaria e horaria de todas as estacoes do Tiete."""
    resultado = {
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "dias_diario": dias_diario,
        "dias_horario": dias_horario,
        "estacoes": [],
    }
    print("  coordenadas das estacoes...", end=" ", flush=True)
    try:
        coords = coordenadas()
        print(f"{len(coords)} pontos")
    except Exception as erro:
        coords = {}
        print(f"FALHOU ({erro})")

    for est in ESTACOES:
        print(f"  {est['codigo']} {est['nome']}...", end=" ", flush=True)
        try:
            diario = serie(est["id"], tipo="dia", dias=dias_diario)
            horario = serie(est["id"], tipo="hor", dias=dias_horario)
            item = dict(est)
            item.update(coords.get(est["id"], {"lat": None, "lon": None}))
            item["validado_ate"] = diario["validado_ate"]
            item["diario"] = diario["registros"]
            item["horario"] = horario["registros"]
            resultado["estacoes"].append(item)
            print(f"{len(diario['registros'])} dias, {len(horario['registros'])} horas")
        except Exception as erro:
            print(f"FALHOU ({erro})")
            item = dict(est)
            item.update({"validado_ate": None, "diario": [], "horario": [], "erro": str(erro)})
            resultado["estacoes"].append(item)
    return resultado


if __name__ == "__main__":
    dados = coletar()
    with open("dados_tiete.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    print("dados_tiete.json gravado")
