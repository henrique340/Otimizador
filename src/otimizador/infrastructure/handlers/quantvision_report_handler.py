"""Handler para relatório consolidado de execução."""

from __future__ import annotations

from otimizador.application import run_full_experiment
from otimizador.infrastructure.http import response


def lambda_handler(event, context):  # noqa: ARG001
    data = run_full_experiment()
    report = {
        "symbol": data["symbol"],
        "winner": data["comparison"]["winner"],
        "ranking": data["comparison"]["ranking"],
        "results_count": len(data["results"]),
    }
    return response(200, report)
