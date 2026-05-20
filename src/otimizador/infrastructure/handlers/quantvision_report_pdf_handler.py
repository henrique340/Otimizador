"""Handler para gerar relatorio PDF de otimização na AWS Lambda."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from otimizador.application import run_full_experiment
from otimizador.evaluation.exporter import export_experiment_results
from otimizador.evaluation.report_pdf import generate_pdf_report
from otimizador.infrastructure.http import response


def _payload_from_event(event: dict | None) -> dict:
    if not isinstance(event, dict):
        return {}
    body = event.get("body")
    if isinstance(body, str) and body.strip():
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}
    if isinstance(body, dict):
        return body
    return {}


def lambda_handler(event, context):  # noqa: ARG001
    # Lambda permite escrita apenas em /tmp.
    os.environ.setdefault("OTIMIZADOR_CACHE_DIR", "/tmp/cache")

    payload = _payload_from_event(event)
    try:
        result = run_full_experiment(
            symbols=payload.get("symbols"),
            period=payload.get("period"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            interval=payload.get("interval"),
            max_weight=payload.get("max_weight"),
        )

        export_dir = payload.get("export_dir", "/tmp/exports")
        figures_dir = payload.get("figures_dir", "/tmp/figures")
        output_pdf = payload.get("output_pdf", "/tmp/relatorio_otimizador.pdf")

        export_experiment_results(report=result, output_dir=export_dir)
        pdf_path = generate_pdf_report(
            export_dir=export_dir,
            figures_dir=figures_dir,
            output=output_pdf,
        )

        pdf_bytes = Path(pdf_path).read_bytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{Path(pdf_path).name}"',
            },
            "isBase64Encoded": True,
            "body": pdf_b64,
        }
    except Exception as exc:
        return response(
            502,
            {
                "error": "report_pdf_failed",
                "message": str(exc),
                "tip": "Verifique logs no CloudWatch e o cache em /tmp.",
            },
        )
