"""Handler de otimização para Lambda."""

from __future__ import annotations

from otimizador.application import run_full_experiment
from otimizador.infrastructure.http import response


def lambda_handler(event, context):  # noqa: ARG001
    result = run_full_experiment()
    return response(200, result)
