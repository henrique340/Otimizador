"""Handler para gerar relatorio PDF de otimização na AWS Lambda."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
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
        regenerate_charts = payload.get("regenerate_charts", True)

        export_experiment_results(report=result, output_dir=export_dir)

        if regenerate_charts:
            project_root = Path("/var/task")
            figures_path = Path(figures_dir)
            figures_path.mkdir(parents=True, exist_ok=True)
            script_path = project_root / "scripts" / "generate_tcc_charts.py"
            if not script_path.exists():
                raise FileNotFoundError(
                    "Script de graficos nao encontrado no pacote da Lambda: "
                    f"{script_path}"
                )

            cmd = [
                sys.executable,
                str(script_path),
                "--output-dir",
                figures_dir,
            ]
            if payload.get("symbols"):
                cmd.extend(["--symbols", ",".join(payload["symbols"])])
            if payload.get("period"):
                cmd.extend(["--period", payload["period"]])
            if payload.get("start_date"):
                cmd.extend(["--start-date", payload["start_date"]])
            if payload.get("end_date"):
                cmd.extend(["--end-date", payload["end_date"]])
            if payload.get("interval"):
                cmd.extend(["--interval", payload["interval"]])
            if payload.get("max_weight") is not None:
                cmd.extend(["--max-weight", str(payload["max_weight"])])

            chart_run = subprocess.run(
                cmd,
                check=False,
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            if chart_run.returncode != 0:
                has_existing_charts = any(figures_path.glob("*.png"))
                if not has_existing_charts:
                    detail = chart_run.stderr.strip() or chart_run.stdout.strip()
                    raise RuntimeError(
                        "Falha ao gerar graficos para o relatorio PDF. "
                        f"Detalhes: {detail}"
                    )

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
