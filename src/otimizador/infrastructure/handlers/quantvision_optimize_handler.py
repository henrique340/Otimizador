"""Handler de otimização para Lambda."""

from __future__ import annotations

import json

from otimizador.application import run_full_experiment
from otimizador.infrastructure.http import response


def lambda_handler(event, context):  # noqa: ARG001
    payload = {}
    body = event.get("body") if isinstance(event, dict) else None
    if isinstance(body, str) and body.strip():
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}
    elif isinstance(body, dict):
        payload = body

    try:
        result = run_full_experiment(
            symbols=payload.get("symbols"),
            period=payload.get("period"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            interval=payload.get("interval"),
            max_weight=payload.get("max_weight"),
        )
        return response(200, result)
    except Exception as exc:
        return response(
            502,
            {
                "error": "optimize_failed",
                "message": str(exc),
                "tip": "Verifique CloudWatch Logs e configure OTIMIZADOR_CACHE_DIR=/tmp/cache.",
            },
        )
