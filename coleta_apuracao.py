#!/usr/bin/env python3
"""Coleta a apuração de 2026 no TSE e grava dados.json para o painel.

Sem dependências externas (só biblioteca padrão). Roda no GitHub Actions a cada 5 minutos.

Endpoints (mesma API pública que os portais de notícia usam). Em 2026 o arquivo completo é o "-u.json":
  Presidente  ele2026/6257/dados/br/br-c0001-e006257-u.json
  Governador  ele2026/6259/dados/sp/sp-c0003-e006259-u.json
  Dep. fed.   ele2026/6259/dados/sp/sp-c0006-e006259-u.json
  Dep. est.   ele2026/6259/dados/sp/sp-c0007-e006259-u.json
Estrutura: raiz (dg, hg, s.pst, v.vv...) -> carg[] -> agr[] (agremiação) -> par[] (sg = sigla) -> cand[]
(n, nmu/nm, vap, pvap, st, e). Se o -u.json falhar, tenta o formato simplificado de 2022 (-r.json).
6257 = Eleição Ordinária Federal 2026, 6259 = Eleição Ordinária Estadual 2026 (config/ele-c.json).
"""
import json, os, sys, time, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

BASE = "https://resultados.tse.jus.br/oficial/ele2026"
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados.json")
BRT = timezone(timedelta(hours=-3))

def urls(ele, uf, cargo):
    e = f"e{int(ele):06d}"; c = f"c{int(cargo):04d}"
    return [f"{BASE}/{ele}/dados/{uf}/{uf}-{c}-{e}-u.json",
            f"{BASE}/{ele}/dados-simplificados/{uf}/{uf}-{c}-{e}-r.json"]


FONTES = {
    "presidente": urls(6257, "br", 1),
    "governador": urls(6259, "sp", 3),
    "dep_federal": urls(6259, "sp", 6),
    "dep_estadual": urls(6259, "sp", 7),
}

ACOMPANHADOS = {
    "anistaldo": {"fonte": "dep_estadual", "numero": "20147", "nome": "Pastor Anistaldo",
                   "cargo": "Deputado estadual", "partido": "Podemos", "vagas": 94},
    "davi": {"fonte": "dep_federal", "numero": "1122", "nome": "Davi Sacer",
              "cargo": "Deputado federal", "partido": "PP", "vagas": 70},
    # número de urna não confirmado: localiza pelo nome de urna e grava o número encontrado
    "marangoni": {"fonte": "dep_federal", "numero": None, "busca": "MARANGONI", "nome": "Fernando Marangoni",
                   "cargo": "Deputado federal", "partido": "Podemos", "vagas": 70},
}


def num(v):
    """'12.915.526' / '12915526' / '51,07' -> número."""
    if v is None or v == "":
        return 0
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if "," in s:
        return float(s.replace(".", "").replace(",", "."))
    try:
        return int(s.replace(".", ""))
    except ValueError:
        return 0


def baixa(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (painel-apuracao)",
                                               "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def _varre(o, partido, out):
    """Percorre carg -> agr -> par -> cand guardando a sigla do partido mais próxima."""
    if isinstance(o, list):
        for x in o:
            _varre(x, partido, out)
    elif isinstance(o, dict):
        sg = o.get("sg") or (o.get("cc") if "cand" in o else None)
        p = sg if isinstance(sg, str) and sg else partido
        lista = o.get("cand")
        if isinstance(lista, list):
            for c in lista:
                if isinstance(c, dict) and "n" in c:
                    out.append({
                        "n": str(c.get("n", "")),
                        "sq": str(c.get("sqcand") or c.get("sq") or ""),
                        "nm": c.get("nmu") or c.get("nm") or "",
                        "cc": c.get("cc") or p or "",
                        "vap": num(c.get("vap")),
                        "pvap": num(c.get("pvap")),
                        "st": c.get("st", "") or "",
                        "e": c.get("e", "") or "",
                    })
        for k, v in o.items():
            if k != "cand" and isinstance(v, (dict, list)):
                _varre(v, p, out)


def cands(j):
    out = []
    _varre(j, None, out)
    vistos, unicos = set(), []
    for c in out:
        if c["n"] not in vistos:
            vistos.add(c["n"]); unicos.append(c)
    unicos.sort(key=lambda c: c["vap"], reverse=True)
    return unicos


def _campo(j, sub, *chaves):
    for fonte in (j.get(sub) if isinstance(j.get(sub), dict) else {}, j):
        for k in chaves:
            if fonte.get(k) not in (None, ""):
                return fonte.get(k)
    return None


def cabecalho(j):
    return {
        "pst": num(_campo(j, "s", "pst")),   # % de seções totalizadas
        "dg": j.get("dg", ""), "hg": j.get("hg", ""),  # data/hora da totalização no TSE
        "vb": num(_campo(j, "v", "vb")), "vn": num(_campo(j, "v", "tvn", "vn")),
        "vv": num(_campo(j, "v", "vv")), "a": num(_campo(j, "e", "a")),
    }


# --- votação do Anistaldo por município (um arquivo -u.json por cidade no TSE) ---
CONFIG_MUN = [f"{BASE}/6259/config/mun-e006259-cm.json",
              "https://resultados.tse.jus.br/oficial/ele2026/6259/config/mun-e006259-cm.json"]


def _sem_acento(t):
    return "".join(ch for ch in unicodedata.normalize("NFD", str(t).upper()) if unicodedata.category(ch) != "Mn")


def municipios_sp():
    for url in CONFIG_MUN:
        try:
            j = baixa(url)
        except Exception:  # noqa: BLE001
            continue
        for b in j.get("abr", []):
            if str(b.get("cd", "")).upper() == "SP":
                return [(m["cd"], m["nm"]) for m in b.get("mu", [])]
    return []


def anistaldo_por_cidade(numero="20147"):
    muns = municipios_sp()
    if not muns:
        return None, "lista de municípios do TSE indisponível"
    def um(item):
        cod, nome = item
        url = f"{BASE}/6259/dados/sp/sp{cod}-c0007-e006259-u.json"
        for _ in range(2):
            try:
                j = baixa(url)
                vv = num(cabecalho(j).get("vv"))
                pst = num(cabecalho(j).get("pst"))
                for c in cands(j):
                    if c["n"] == numero:
                        return nome, c["vap"], vv, pst
                return nome, 0, vv, pst
            except Exception:  # noqa: BLE001
                time.sleep(1)
        return nome, None, None, None
    with ThreadPoolExecutor(max_workers=24) as ex:
        res = list(ex.map(um, muns))
    linhas, falhas = [], 0
    for nome, v, vv, pst in res:
        if v is None:
            falhas += 1
            continue
        if v:
            linhas.append({"m": nome, "v": v, "p": round(100 * v / vv, 2) if vv else 0, "pst": pst})
    linhas.sort(key=lambda x: x["v"], reverse=True)
    return {"cidades": linhas, "falhas": falhas, "total_municipios": len(muns),
            "com_voto": sum(1 for x in linhas if x["v"])}, None


def main():
    anterior = {}
    if os.path.exists(SAIDA):
        try:
            anterior = json.load(open(SAIDA, encoding="utf-8"))
        except Exception:
            anterior = {}

    brutos, erros, diag = {}, [], {}
    for chave, lista in FONTES.items():
        falhas = []
        for url in lista:
            for tentativa in range(2):
                try:
                    j = baixa(url)
                    if cands(j):
                        brutos[chave] = j
                        diag[chave] = {"url": url, "chaves": sorted(j.keys())[:20]}
                    else:
                        falhas.append(f"{url.rsplit('/', 1)[-1]}: sem candidatos (chaves {sorted(j.keys())[:12]})")
                    break
                except Exception as e:  # noqa: BLE001
                    if tentativa == 1:
                        falhas.append(f"{url.rsplit('/', 1)[-1]}: {e}")
                    time.sleep(2)
            if chave in brutos:
                break
        if chave not in brutos:
            erros.append(f"{chave}: " + " | ".join(falhas))
            print(f"! {chave}: {falhas}", file=sys.stderr)

    saida = {
        "atualizado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "fonte": "TSE - resultados.tse.jus.br",
        "erros": erros,
        "diagnostico": diag,
        "majoritarios": dict(anterior.get("majoritarios", {})),
        "acompanhados": dict(anterior.get("acompanhados", {})),
    }

    for chave in ("presidente", "governador"):
        if chave in brutos:
            j = brutos[chave]
            saida["majoritarios"][chave] = {**cabecalho(j), "cand": cands(j)[:12]}

    for chave, cfg in ACOMPANHADOS.items():
        j = brutos.get(cfg["fonte"])
        if not j:
            continue
        lista = cands(j)
        if cfg.get("numero"):
            pos = next((i for i, c in enumerate(lista) if c["n"] == cfg["numero"]), None)
        else:
            alvo_nome = cfg["busca"].upper()
            pos = next((i for i, c in enumerate(lista) if c["nm"].upper() == alvo_nome), None)
            if pos is None:
                pos = next((i for i, c in enumerate(lista) if alvo_nome in c["nm"].upper()), None)
        alvo = lista[pos] if pos is not None else None
        corte = lista[cfg["vagas"] - 1]["vap"] if len(lista) >= cfg["vagas"] else None
        saida["acompanhados"][chave] = {
            **{k: cfg[k] for k in ("numero", "nome", "cargo", "partido", "vagas")},
            "numero": cfg.get("numero") or (alvo["n"] if alvo else ""),
            **cabecalho(j),
            "encontrado": alvo is not None,
            "vap": alvo["vap"] if alvo else 0,
            "pvap": alvo["pvap"] if alvo else 0,
            "st": alvo["st"] if alvo else "",
            "sq": alvo.get("sq", "") if alvo else "",
            "posicao": (pos + 1) if pos is not None else None,
            "total_candidatos": len(lista),
            "corte_vap": corte,
            "lider": {"nm": lista[0]["nm"], "cc": lista[0]["cc"], "vap": lista[0]["vap"]} if lista else None,
            "partido_top": [
                {"nm": c["nm"], "vap": c["vap"], "pos": i + 1}
                for i, c in enumerate(lista) if c["cc"] and alvo and c["cc"] == alvo["cc"]
            ][:5],
        }

    if "anistaldo" in saida["acompanhados"]:
        try:
            cid, erro = anistaldo_por_cidade()
        except Exception as e:  # noqa: BLE001
            cid, erro = None, str(e)
        anterior_cid = (anterior.get("acompanhados", {}).get("anistaldo") or {}).get("por_cidade")
        if cid:
            saida["acompanhados"]["anistaldo"]["por_cidade"] = cid
        else:
            erros.append(f"anistaldo por cidade: {erro}")
            if anterior_cid:
                saida["acompanhados"]["anistaldo"]["por_cidade"] = anterior_cid

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)

    resumo = {k: v.get("pst") for k, v in {**saida["majoritarios"], **saida["acompanhados"]}.items()}
    print(f"ok {saida['atualizado_em']} | % seções: {resumo} | erros: {len(erros)}")
    # código de saída 2 = tudo 100% totalizado (o workflow para o laço)
    if resumo and all((p or 0) >= 100 for p in resumo.values()) and len(resumo) == 5:
        sys.exit(2)
    if len(erros) == len(FONTES):
        sys.exit(1)


if __name__ == "__main__":
    main()
