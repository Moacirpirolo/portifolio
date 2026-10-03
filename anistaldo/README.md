# Painel de campanha — Pastor Anistaldo (20147)

Página única, sem dependência de servidor, que junta três coisas:

1. **A votação apurada de 2022** para Deputado Estadual em São Paulo, direto da API pública de
   divulgação de resultados do TSE. 40.718 votos em 318 municípios, conferido contra o total oficial.
2. **A operação de campo de 2026**: as cidades sob coordenação própria, divididas em três regionais,
   com equipe e piso/teto de votos por cidade.
3. **A meta de 80 mil votos**, repartida entre os 318 municípios em dois cenários alternáveis.

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | O painel inteiro. Abre direto no navegador, sem build e sem servidor. Imagens e dados embutidos. |
| `coleta_tse.py` | Coletor da apuração de 2022 no TSE. Varre os 645 municípios de SP em paralelo e gera o CSV. |
| `dados_2022_meta.json` | Os 318 municípios com voto: apurado de 2022, % dos válidos e a meta nos dois cenários. |
| `coordenacao_campo.json` | As cidades coordenadas: piso, teto, pessoas e regional. |

## Coleta no TSE

```bash
pip install requests
python3 coleta_tse.py
```

A API de divulgação é a mesma que os portais de notícia consomem. Sem token.
Para a eleição de 2022, 1º turno:

```
https://resultados.tse.jus.br/oficial/ele2022/546/dados/sp/sp{COD_MUNICIPIO}-c0007-e000546-v.json
```

`546` é o pleito (Ordinária Estadual 2022), `c0007` o cargo de Deputado Estadual e `e000546` a eleição.
A lista de códigos de município sai de `config/mun-e000546-cm.json`. Em 2026 esses códigos mudam.

## Como a meta de 80 mil é dividida

Nenhum dos dois cenários é previsão eleitoral. São hipóteses de trabalho.

- **Proporcional**: cada cidade multiplica sua votação de 2022 por 1,96. O mapa de 2022 fica intacto.
  Guarulhos precisaria de 45.601 votos, 7,1% dos válidos da cidade, contra 3,6% em 2022.
- **Expansão**: o peso de cada cidade é a votação de 2022 elevada a 0,9, com teto de 3× sobre o
  resultado anterior e a sobra redistribuída para as praças maiores. Guarulhos fica em 39.360.

## Trocar pela apuração real de 2026

O vetor `DADOS` no início do script de `index.html` guarda tudo. Cada item tem `m` (município),
`a` (votos 2022), `p` (% dos válidos 2022), `b` (meta proporcional) e `c` (meta expansão).
Trocar os valores recalcula a página inteira.

## Notas técnicas

- Roxo e azul da identidade não funcionam juntos como cores de dado: ΔE 3,5 para deuteranopia,
  abaixo do mínimo de 8. Por isso os gráficos usam roxo e dourado, e o azul fica só na identidade.
- Fontes carregam sem bloquear a renderização; a página aparece com as fontes do sistema e troca depois.
- Todo movimento respeita `prefers-reduced-motion`.
