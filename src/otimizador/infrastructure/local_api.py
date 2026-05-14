import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from otimizador.application import run_full_experiment
from otimizador.evaluation.exporter import export_experiment_results
from otimizador.evaluation.report_pdf import generate_pdf_report

ALGORITHM_OPTIONS = {
    "linear_programming",
    "genetic_algorithm",
    "simulated_annealing",
    "all",
}

app = FastAPI(title="Otimizador API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    algorithm: Literal[
        "linear_programming", "genetic_algorithm", "simulated_annealing", "all"
    ] = "linear_programming"
    symbols: list[str] | None = None
    period: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    interval: str | None = None
    max_weight: float | None = None
    export_results: bool = False
    export_dir: str = "examples/exports"


class PdfReportRequest(OptimizeRequest):
    figures_dir: str = "docs/figures"
    output_pdf: str = "docs/reports/relatorio_otimizador.pdf"
    regenerate_charts: bool = True


@app.get("/status")
def status():
    return {"status": "ok", "service": "otimizador"}


@app.post("/optimize")
def optimize(payload: OptimizeRequest):
    if payload.algorithm not in ALGORITHM_OPTIONS:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_algorithm",
                "message": f"Algoritmo invalido: {payload.algorithm}",
                "allowed": sorted(ALGORITHM_OPTIONS),
            },
        )

    try:
        result = run_full_experiment(
            symbols=payload.symbols,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            interval=payload.interval,
            max_weight=payload.max_weight,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={
                "error": "data_ingestion_failed",
                "message": str(exc),
                "tip": "Verifique internet para Yahoo Finance ou adicione cache CSV local em /cache.",
            },
        )

    if payload.export_results:
        result["export_files"] = export_experiment_results(
            report=result,
            output_dir=payload.export_dir,
        )

    if payload.algorithm == "all":
        return result

    selected = next(
        (item for item in result["results"] if item["algorithm"] == payload.algorithm),
        None,
    )
    if selected is None:
        return JSONResponse(
            status_code=500,
            content={
                "error": "algorithm_not_found",
                "message": f"Resultado nao encontrado para {payload.algorithm}",
            },
        )

    return {
        "symbol": result["symbol"],
        "symbols": result["symbols"],
        "objective": result["objective"],
        "period": result.get("period"),
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
        "interval": result.get("interval"),
        "result": selected,
        "comparison": result["comparison"],
        "export_files": result.get("export_files"),
    }


@app.post("/export")
def export(payload: OptimizeRequest):
    try:
        result = run_full_experiment(
            symbols=payload.symbols,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            interval=payload.interval,
            max_weight=payload.max_weight,
        )
        export_files = export_experiment_results(
            report=result,
            output_dir=payload.export_dir,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={
                "error": "export_failed",
                "message": str(exc),
            },
        )

    return {
        "message": "Export concluido",
        "symbol": result["symbol"],
        "symbols": result["symbols"],
        "period": result.get("period"),
        "start_date": result.get("start_date"),
        "end_date": result.get("end_date"),
        "interval": result.get("interval"),
        "export_files": export_files,
    }


@app.post("/report/pdf")
def report_pdf(payload: PdfReportRequest):
    try:
        result = run_full_experiment(
            symbols=payload.symbols,
            period=payload.period,
            start_date=payload.start_date,
            end_date=payload.end_date,
            interval=payload.interval,
            max_weight=payload.max_weight,
        )
        export_experiment_results(
            report=result,
            output_dir=payload.export_dir,
        )

        if payload.regenerate_charts:
            project_root = Path(__file__).resolve().parents[3]
            figures_path = (project_root / payload.figures_dir).resolve()
            cmd = [
                sys.executable,
                str((project_root / "scripts" / "generate_tcc_charts.py").resolve()),
                "--output-dir",
                payload.figures_dir,
            ]
            if payload.symbols:
                cmd.extend(["--symbols", ",".join(payload.symbols)])
            if payload.start_date:
                cmd.extend(["--start-date", payload.start_date])
            if payload.end_date:
                cmd.extend(["--end-date", payload.end_date])
            if payload.interval:
                cmd.extend(["--interval", payload.interval])
            if payload.max_weight is not None:
                cmd.extend(["--max-weight", str(payload.max_weight)])

            env = os.environ.copy()
            env["PYTHONPATH"] = "src"
            chart_run = subprocess.run(
                cmd,
                check=False,
                env=env,
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            if chart_run.returncode != 0:
                has_existing_charts = figures_path.exists() and any(
                    figures_path.glob("*.png")
                )
                if not has_existing_charts:
                    detail = chart_run.stderr.strip() or chart_run.stdout.strip()
                    raise RuntimeError(
                        "Falha ao gerar graficos para o relatorio. "
                        f"Detalhes: {detail}"
                    )

        pdf_path = generate_pdf_report(
            export_dir=payload.export_dir,
            figures_dir=payload.figures_dir,
            output=payload.output_pdf,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={
                "error": "pdf_report_failed",
                "message": str(exc),
            },
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )
