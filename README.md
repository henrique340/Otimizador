# otimizador

MVP em Python para comparar três algoritmos de otimização em séries temporais financeiras usando `PETR4.SA` (Yahoo Finance via `yfinance`), com execução local e caminho claro para AWS Lambda + API Gateway + S3 + DynamoDB + EventBridge + Step Functions.

## Visão geral

O projeto compara:
1. Programação linear
2. Algoritmo genético
3. Simulated annealing

Todos os algoritmos:
- usam o mesmo dataset,
- usam a mesma função objetivo,
- retornam o mesmo schema JSON.

## Arquitetura

```text
src/otimizador/
  domain/          # contratos, modelos e configuração
  data/            # ingestão e feature engineering
  algorithms/      # LP, GA, SA
  evaluation/      # ranking/comparação
  infrastructure/  # HTTP helpers e handlers Lambda
tests/             # testes unitários rápidos
docs/              # documentação do experimento
scripts/           # execução local e empacotamento
examples/          # exemplos de saída JSON
```

Escolha de MVP: com apenas um ativo (`PETR4.SA`), os pesos são distribuídos entre horizontes de retorno (`ret_1d`, `ret_5d`, `ret_21d`) para permitir comparação real dos algoritmos sem overengineering.

## Função objetivo comum

`linear_risk_adjusted_return`:

`objective = dot(weights, expected_returns - risk_aversion * volatility)`

## Variáveis de ambiente

Copie `.env.example` e ajuste se necessário:

- `OTIMIZADOR_SYMBOL` (default: `PETR4.SA`)
- `OTIMIZADOR_PERIOD` (default: `2y`)
- `OTIMIZADOR_START_DATE` (opcional, ex: `2015-01-01`)
- `OTIMIZADOR_END_DATE` (opcional, ex: `2025-12-31`)
- `OTIMIZADOR_INTERVAL` (default: `1d`)
- `OTIMIZADOR_CACHE_DIR` (default: `cache`)
- `OTIMIZADOR_RISK_AVERSION` (default: `0.35`)
- `OTIMIZADOR_RANDOM_SEED` (default: `42`)
- `OTIMIZADOR_GA_POPULATION` (default: `32`)
- `OTIMIZADOR_GA_GENERATIONS` (default: `50`)
- `OTIMIZADOR_SA_ITERATIONS` (default: `250`)
- `OTIMIZADOR_SA_INITIAL_TEMPERATURE` (default: `1.0`)
- `OTIMIZADOR_SA_COOLING_RATE` (default: `0.98`)

## Como rodar localmente

1. Criar ambiente e instalar dependências:

```bash
python -m venv .venv
source .venv/bin/activate  # linux/mac
# .venv\\Scripts\\activate   # windows powershell
pip install -r requirements.txt -r requirements-dev.txt
```

2. Executar experimento ponta a ponta:

```bash
python -m otimizador
```

3. Gerar exemplos JSON:

```bash
python scripts/run_local_experiment.py
```

## Como testar

```bash
pytest -q
```

## Como executar cada algoritmo

Use `run_full_experiment()` em `src/otimizador/application.py`, ou chame:
- `run_linear_programming`
- `run_genetic_algorithm`
- `run_simulated_annealing`

Todos recebem `OptimizationRequest` + `ObjectiveFunction`.

## AWS / Lambda

Handlers criados:
- `quantvision-data-handler`
- `quantvision-optimize-handler`
- `quantvision-report-handler`
- `quantvision-status-handler`

Módulos:
- `src/otimizador/infrastructure/handlers/quantvision_data_handler.py`
- `src/otimizador/infrastructure/handlers/quantvision_optimize_handler.py`
- `src/otimizador/infrastructure/handlers/quantvision_report_handler.py`
- `src/otimizador/infrastructure/handlers/quantvision_status_handler.py`

Template SAM base: `infrastructure.template.yaml`

## Empacotamento para deploy

Linux/macOS:

```bash
bash scripts/package_lambda.sh
```

Windows PowerShell:

```powershell
./scripts/package_lambda.ps1
```

Artefato gerado: `dist/otimizador-lambda.zip`

## CI/CD (Jenkins)

Pipeline mínimo em `Jenkinsfile`:
1. Instala dependências
2. Roda lint (`ruff`)
3. Roda testes (`pytest`)
4. Gera artefato zip

## Exemplos JSON

- `examples/linear_programming.json`
- `examples/genetic_algorithm.json`
- `examples/simulated_annealing.json`
- `examples/petr4_full_report.json`

## Front-end com Docker

1. Suba a API local (porta 8000):

```bash
set PYTHONPATH=src
python -m uvicorn otimizador.infrastructure.local_api:app --host 0.0.0.0 --port 8000 --reload
```

2. Em outro terminal, suba o front com Docker:

```bash
docker compose up --build frontend
```

3. Abra no navegador:

- `http://localhost:8080`

O front ja vem apontando para `http://localhost:8000`.

### Multi-ativos via API local

No endpoint `POST /optimize`, envie:

```json
{
  "algorithm": "linear_programming",
  "symbols": ["PETR4.SA", "VALE3.SA", "ITUB4.SA"],
  "start_date": "2015-01-01",
  "end_date": "2025-12-31",
  "interval": "1d",
  "max_weight": 0.6,
  "period": "2y"
}
```

### Exportacao de resultados

Endpoint `POST /export` cria artefatos em CSV/JSON para analise:
- `*_full_report.json`
- `*_comparison_summary.csv`
- `*_weights_by_algorithm.csv`

Exemplo de uso:

```json
{
  "algorithm": "all",
  "symbols": ["PETR4.SA", "VALE3.SA", "ITUB4.SA"],
  "start_date": "2015-01-01",
  "end_date": "2025-12-31",
  "interval": "1d",
  "max_weight": 0.6,
  "export_dir": "examples/exports"
}
```

### Relatorio em PDF com graficos

Com os arquivos de `examples/exports` e `docs/figures` gerados:

```powershell
$env:PYTHONPATH='src'
python scripts/generate_pdf_report.py --export-dir examples/exports --figures-dir docs/figures --output docs/reports/relatorio_otimizador_2015_2025.pdf
```

Ou via API/Frontend:
- Endpoint `POST /report/pdf` gera o PDF e retorna o arquivo para download.
- No frontend, use o botao `Gerar PDF`.

## GitHub Actions (CI/CD)

Workflow criado em `.github/workflows/ci-cd-lambda.yml` com:
- CI em `pull_request`/`push` na `main` (ruff + pytest)
- Deploy automatico da Lambda `dev` em `push` na `main`

### Configuracoes no GitHub

1. `Settings -> Environments -> dev` (opcional: approval manual)
2. `Settings -> Secrets and variables -> Actions`

Secrets:
- `AWS_ROLE_ARN`: ARN da role assumida via OIDC

Variables:
- `AWS_REGION`: ex. `sa-east-1`
- `LAMBDA_FUNCTION_NAME`: ex. `quantvision-optimize-handler-dev`
- `LAMBDA_DEPLOY_BUCKET`: bucket S3 para upload do zip de deploy

### Observacao OIDC

A role da AWS precisa confiar no provedor OIDC do GitHub e permitir:
- `s3:PutObject` no bucket de deploy
- `lambda:update-function-code`
- `lambda:invokeFunction`

## Graficos para TCC

Script unico para gerar 10 graficos em `docs/figures`:

```bash
PYTHONPATH=src python scripts/generate_tcc_charts.py --symbols PETR4.SA,VALE3.SA,ITUB4.SA --period 2y --interval 1d
```

Windows PowerShell:

```powershell
$env:PYTHONPATH='src'
python scripts/generate_tcc_charts.py --symbols PETR4.SA,VALE3.SA,ITUB4.SA --start-date 2015-01-01 --end-date 2025-12-31 --interval 1d
```

Saidas principais:
- `01_precos_normalizados.png`
- `02_distribuicao_retornos.png`
- `03_volatilidade_movel.png`
- `04_heatmap_correlacao.png`
- `05_pesos_algoritmos.png`
- `06_metricas_algoritmos.png`
- `07_fronteira_risco_retorno.png`
- `08_convergencia_algoritmos.png`
- `09_backtest_acumulado.png`
- `10_drawdown_algoritmos.png`
