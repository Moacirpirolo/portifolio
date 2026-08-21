# Painel do Rio Tietê

Painel público da qualidade da água do Rio Tietê, montado a partir das estações
automáticas da CETESB. Abra o `index.html` — ele é autônomo, sem CDN e funciona offline.

O rio é desenhado com a geometria real da Base Hidrográfica Ottocodificada da ANA
(115 trechos encadeados da nascente à foz), e cada trecho é pintado pela medição da
estação mais próxima. Um farol no topo mostra o estado do rio pelo pior trecho medido.

## Uso

    python3 painel.py           # coleta tudo e gera rio_tiete.html
    python3 painel.py --cache   # regenera o HTML com o que já está em disco
    python3 coleta.py           # só as medições  -> dados_tiete.json
    python3 geo.py              # só a geometria  -> geo_tiete.json

## Arquivos

- `coleta.py` — cliente do SIMQUA: estações, parâmetros, coordenadas e parse do CSV (latin-1, `;`, vírgula decimal).
- `geo.py` — traçado do rio na base da ANA/SNIRH, afluentes e contorno do estado (IBGE). Encadeia os 115 trechos da nascente à foz, simplifica por Douglas-Peucker e calcula o km acumulado.
- `mapa.py` — projeta a geometria em SVG: mapa geral e detalhe do Alto Tietê, com cada segmento marcado pela estação mais próxima.
- `estilo.py` — a folha de estilo.
- `painel.py` — junta tudo e escreve o HTML.
- `dados_tiete.json` / `geo_tiete.json` — cache das duas coletas.
- `index.html` — o painel gerado. Abre direto no navegador, funciona offline.
  (o script escreve `rio_tiete.html`; aqui ele está renomeado para servir pelo GitHub Pages)

## O que dá para mexer

- Janela de dados: `coletar(dias_diario=90, dias_horario=7)` em `coleta.py`.
- Faixas de classificação e textos: a lista `PARAMETROS` no topo de `painel.py`.
- Posição dos rótulos no mapa: `ROTULOS_GERAL` e `ROTULOS_METRO` em `mapa.py`.

## Fonte

`https://simqua.cetesb.sp.gov.br/dados/` — endpoint público, sem token.
Parâmetros: `e` estação, `p` parâmetros, `ini`/`fim` no formato `dd/mm/aaaaTHH:MM`,
`tipo` (min, hor, dia, mes, ano), `classif=1` para dado validado, `formato` (csv, xls, pdf).

Estações do Tietê: EF01 Mogi das Cruzes (2), EF29 Penha (25), EF02 Rasgão (1),
EF28 Itu (20), EF03 Laranjal Paulista (3), EF35 Barra Bonita (30), EF36 Promissão (32).

Para trocar o parâmetro em destaque, mude `chave="oxigenio"` nas funções `sparkline`
e `grafico_horario` para `turbidez`, `ph`, `condutividade` ou `temperatura`.

## Leitura dos valores

Oxigênio dissolvido, Resolução CONAMA 357 (água doce): acima de 6 mg/L classe 1,
acima de 5 classe 2, acima de 4 classe 3, acima de 2 classe 4. Valores acima de
10 mg/L costumam indicar supersaturação por floração de algas, não água melhor.

## Fontes

- Medições: [SIMQUA/CETESB](https://simqua.cetesb.sp.gov.br), endpoint público `/dados/`, sem autenticação.
- Traçado do rio e afluentes: Base Hidrográfica Ottocodificada 2017 (ANA/SNIRH).
- Contorno do estado: malha territorial do IBGE.

Todos os dados são públicos. Valores mais recentes que a data de validação da CETESB
ainda passam por consistência técnica e podem mudar.
