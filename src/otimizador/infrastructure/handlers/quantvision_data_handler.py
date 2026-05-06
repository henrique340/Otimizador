"""Handler de ingestao de dados para Lambda."""

from __future__ import annotations

from otimizador.data.ingestion import fetch_prices
from otimizador.domain.config import load_config_from_env
from otimizador.infrastructure.http import response


def lambda_handler(event, context):  # noqa: ARG001
    config = load_config_from_env()
    frame = fetch_prices(config.data)
    return response(
        200,
        {
            "symbols": config.data.symbols,
            "rows": len(frame),
            "columns": list(frame.columns),
            "message": "Dados carregados com sucesso.",
        },
    )
