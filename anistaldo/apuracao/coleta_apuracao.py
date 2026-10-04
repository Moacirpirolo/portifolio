#!/usr/bin/env python3
"""Coleta a apuração de 2026 no TSE e grava dados.json para o painel.

Sem dependências externas (só biblioteca padrão). Roda no GitHub Actions a cada 2 minutos.

Endpoints (mesma API pública que os portais de notícia usam):
  Presidente  ele2026/6257/dados-simplificados/br/br-c0001-e006257-r.json
  Governador  ele2026/6259/dados-simplificados/sp/sp-c0003-e006259-r.json
  Dep. fed.   ele2026/6259/dados-simplificados/sp/sp-c0006-e006259-r.json
  Dep. est.   ele2026/6259/dados-simplificados/sp/sp-c0007-e006259-r.json
6257 = Eleição Ordinária Federal 2026, 6259 = Eleição Ordinária Estadual 2026 (config/ele-c.json).
"""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

BASE = "https://resultados.tse.jus.br/oficial/ele2026"
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados.json")
BRT = timezone(timedelta(hours=-3))

FONTES = {
    "presidente": f"{BASE}/6257/dados-simplificados/br/br-c0001-e006257-r.json",
    "governador": f"{BASE}/6259/dados-simplificados/sp/sp-c0003-e006259-r.json",
    "dep_federal": f"{BASE}/6259/dados-simplificados/sp/sp-c0006-e006259-r.json",
    "dep_estadual": f"{BASE}/6259/dados-simplificados/sp/sp-c0007-e006259-r.json",
}

ACOMPANHADOS = {
    "anistaldo": {"fonte": "dep_estadual", "numero": "20147", "nome": "Pastor Anistaldo",
                   "cargo": "Deputado estadual", "partido": "Podemos", "vagas": 94},
    "davi": {"fonte": "dep_federal", "numero": "1122", "nome": "Davi Sacer",
              "cargo": "Deputado federal", "partido": "PP", "vagas": 70},
}


def num(v):
    """'12.915.526' / '12915526' / '51,07' -> número."""
    if v is None or v == "":
        return 0
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


def cands(j):
    out = []
    for c in j.get("cand", []) or []:
        out.append({
            "n": str(c.get("n", "")),
            "nm": c.get("nm", ""),
            "cc": c.get("cc", ""),
            "vap": num(c.get("vap")),
            "pvap": num(c.get("pvap")),
            "st": c.get("st", ""),
            "e": c.get("e", ""),
        })
    out.sort(key=lambda c: c["vap"], reverse=True)
    return out


def cabecalho(j):
    return {
        "pst": num(j.get("pst")),          # % de seções totalizadas
        "dg": j.get("dg", ""), "hg": j.get("hg", ""),  # data/hora da totalização no TSE
        "vb": num(j.get("vb")), "vn": num(j.get("vn") or j.get("tvn")),
        "vv": num(j.get("vv")), "a": num(j.get("a")),
    }


def main():
    anterior = {}
    if os.path.exists(SAIDA):
        try:
            anterior = json.load(open(SAIDA, encoding="utf-8"))
        except Exception:
            anterior = {}

    brutos, erros = {}, []
    for chave, url in FONTES.items():
        for tentativa in range(3):
            try:
                brutos[chave] = baixa(url)
                break
            except Exception as e:  # noqa: BLE001
                if tentativa == 2:
                    erros.append(f"{chave}: {e}")
                    print(f"! {chave}: {e}", file=sys.stderr)
                time.sleep(3)

    saida = {
        "atualizado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "fonte": "TSE - resultados.tse.jus.br",
        "erros": erros,
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
        pos = next((i for i, c in enumerate(lista) if c["n"] == cfg["numero"]), None)
        alvo = lista[pos] if pos is not None else None
        corte = lista[cfg["vagas"] - 1]["vap"] if len(lista) >= cfg["vagas"] else None
        saida["acompanhados"][chave] = {
            **{k: cfg[k] for k in ("numero", "nome", "cargo", "partido", "vagas")},
            **cabecalho(j),
            "encontrado": alvo is not None,
            "vap": alvo["vap"] if alvo else 0,
            "pvap": alvo["pvap"] if alvo else 0,
            "st": alvo["st"] if alvo else "",
            "posicao": (pos + 1) if pos is not None else None,
            "total_candidatos": len(lista),
            "corte_vap": corte,
            "lider": {"nm": lista[0]["nm"], "cc": lista[0]["cc"], "vap": lista[0]["vap"]} if lista else None,
            "partido_top": [
                {"nm": c["nm"], "vap": c["vap"], "pos": i + 1}
                for i, c in enumerate(lista) if c["cc"] and alvo and c["cc"] == alvo["cc"]
            ][:5],
        }

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)

    resumo = {k: v.get("pst") for k, v in {**saida["majoritarios"], **saida["acompanhados"]}.items()}
    print(f"ok {saida['atualizado_em']} | % seções: {resumo} | erros: {len(erros)}")
    # código de saída 2 = tudo 100% totalizado (o workflow para o laço)
    if resumo and all((p or 0) >= 100 for p in resumo.values()) and len(resumo) == 4:
        sys.exit(2)
    if len(erros) == len(FONTES):
        sys.exit(1)


if __name__ == "__main__":
    main()
