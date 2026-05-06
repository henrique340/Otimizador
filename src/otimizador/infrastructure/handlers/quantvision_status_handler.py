"""Handler de status/healthcheck para Lambda."""

from __future__ import annotations

from otimizador.infrastructure.http import response


def lambda_handler(event, context):  # noqa: ARG001
    return response(
        200,
        {
            "service": "otimizador",
            "status": "ok",
            "message": "Serviço disponível.",
        },
    )
