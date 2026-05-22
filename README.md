<<<<<<< HEAD
﻿
=======
﻿# Otimizador - QuantVision

Projeto MVP para comparacao de algoritmos de otimizacao de carteira com ativos da B3, com frontend web e backend publicado na AWS.

## O que este projeto entrega

- Site frontend para executar analises e baixar resultados
- API de otimizacao na AWS (Lambda + API Gateway)
- Exportacao de resultados (JSON/CSV)
- Geracao de relatorio em PDF via endpoint
- Suporte a cache de dados para reduzir falhas do Yahoo Finance

## Arquitetura (AWS)

O sistema esta publicado com:

1. API Gateway (HTTP de entrada)
2. AWS Lambda (handlers de dados, otimizacao, relatorio e status)
3. Amazon S3 (artefatos e cache de precos)
4. CloudWatch Logs (observabilidade e debug)

Fluxo principal:

1. Usuario acessa o site
2. Site chama o endpoint `/optimize`
3. Lambda tenta ler cache (local em `/tmp/cache`, opcionalmente vindo do S3)
4. Se necessario, consulta yfinance
5. Retorna comparacao entre LP, GA e SA

## Frontend (site)

Arquivo principal do site:

- `frontend/index.html`

A tela permite:

- definir URL da API
- selecionar ativos e parametros
- executar otimizacao
- comparar algoritmos
- exportar CSV/JSON
- gerar PDF

## URL da API AWS

Exemplo (ambiente atual):

- `https://rqdwpiwn5b.execute-api.us-east-2.amazonaws.com/prod`

Endpoints usados pelo frontend:

- `GET /status`
- `POST /optimize`
- `POST /export`
- `POST /report/pdf`

## Cache de dados (AWS)

Para reduzir erro de "Download vazio no yfinance", o projeto usa cache CSV.

Variaveis recomendadas na Lambda de otimizacao:

- `OTIMIZADOR_CACHE_DIR=/tmp/cache`
- `OTIMIZADOR_S3_CACHE_BUCKET=<seu-bucket>`
- `OTIMIZADOR_S3_CACHE_PREFIX=cache`

Formato do nome do arquivo de cache:

- `<SYMBOLS>_<START>_<END>_<INTERVAL>.csv`
- Exemplo:
  - `PETR4_SA__VALE3_SA__ITUB4_SA_20150101_20251231_1d.csv`

Key no S3 (exemplo):

- `cache/PETR4_SA__VALE3_SA__ITUB4_SA_20150101_20251231_1d.csv`

Permissoes IAM minimas para a role da Lambda:

- `s3:ListBucket` no bucket
- `s3:GetObject` em `cache/*`

## Rodar localmente (sem Docker)

1. Instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

2. Subir API local:

```powershell
$env:PYTHONPATH='src'
python -m uvicorn otimizador.infrastructure.local_api:app --host 0.0.0.0 --port 8000 --reload
```

3. Subir frontend local:

```powershell
cd frontend
python -m http.server 8080
```

4. Abrir no navegador:

- `http://localhost:8080`

## Estrutura do projeto

```text
src/otimizador/
  algorithms/
  data/
  domain/
  infrastructure/

frontend/
  index.html

tests/

scripts/

docs/

cache/
```

## Testes

```powershell
$env:PYTHONPATH='src'
pytest -q
```

## Observacao academica

Este repositorio foi organizado para demonstrar:

- comparacao de tecnicas de otimizacao
- arquitetura cloud com AWS
- frontend web integrado ao backend
- reproducibilidade via cache e exportacao de resultados
>>>>>>> 0f0ec324b47543b5f38b2d62b93c4c660c75cd4a
