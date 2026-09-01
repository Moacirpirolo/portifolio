#!/usr/bin/env python3
import csv, sys
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter

BASE="https://resultados.tse.jus.br/oficial/ele2022"
PLEITO="546"; ELEICAO="e000546"; CARGO="c0007"; UF="sp"; NUMERO="20147"
H={"User-Agent":"Mozilla/5.0"}

s=requests.Session()
s.mount("https://",HTTPAdapter(pool_connections=32,pool_maxsize=32,max_retries=3))
s.headers.update(H)

r=s.get(f"{BASE}/{PLEITO}/config/mun-{ELEICAO}-cm.json",timeout=60); r.raise_for_status()
muns=[(m["cd"],m["nm"]) for b in r.json()["abr"] if b["cd"].upper()==UF.upper() for m in b["mu"]]
print(f"{len(muns)} municipios em SP",file=sys.stderr)

def busca(item):
    cod,nome=item
    url=f"{BASE}/{PLEITO}/dados/{UF}/{UF}{cod}-{CARGO}-{ELEICAO}-v.json"
    try:
        r=s.get(url,timeout=60)
        if r.status_code!=200: return (nome,None,None)
        b=r.json()["abr"][0]
        vv=int(b.get("vv",0) or 0)
        for c in b.get("cand",[]):
            if c.get("n")==NUMERO: return (nome,int(c.get("vap",0) or 0),vv)
        return (nome,0,vv)
    except Exception as e:
        print(f"  ! {nome}: {e}",file=sys.stderr); return (nome,None,None)

with ThreadPoolExecutor(max_workers=24) as ex:
    res=list(ex.map(busca,muns))

linhas=[];total=0;falhas=0
for nome,v,vv in res:
    if v is None: falhas+=1; continue
    if v:
        linhas.append({"municipio":nome,"votos":v,"pct_validos":round(100*v/vv,4) if vv else 0})
        total+=v
linhas.sort(key=lambda x:x["votos"],reverse=True)
with open("votos_anistaldo_2022.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=["municipio","votos","pct_validos"]); w.writeheader(); w.writerows(linhas)
print(f"\nTOTAL: {total} votos em {len(linhas)} municipios  (falhas: {falhas})")
print("(o esperado sao 40.718 votos)\n")
print("Top 15:")
for l in linhas[:15]:
    print(f"  {l['municipio']:<32} {l['votos']:>7}  {l['pct_validos']:>6.2f}%")
