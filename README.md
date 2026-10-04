# Dobrada Anistaldo + Davi Sacer — apuração 2026

Pastor Anistaldo (20147), Davi Sacer (1122), governador de SP e presidente, com dados da API pública do TSE.

- `index.html`: o painel. Lê `dados.json` deste branch e se recarrega a cada 5 minutos.
- `coleta_apuracao.py`: baixa os arquivos `-u.json` do TSE (eleições 6257 e 6259) e grava `dados.json`.
- A automação fica em `.github/workflows/apuracao-2026.yml` no `main` (agendamentos do GitHub só rodam a partir do branch principal) e faz commit aqui a cada 5 minutos.

Este branch fica separado do `main` de propósito: o `main` é publicado no site da CriaSite e o painel não deve aparecer lá.

Para abrir: https://htmlpreview.github.io/?https://github.com/Moacirpirolo/portifolio/blob/apuracao-2026/index.html
