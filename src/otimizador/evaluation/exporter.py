"""Exportacao de resultados para JSON e CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def _safe_name(raw: str) -> str:
    text = raw.strip().replace(".SA", "_SA").replace(".", "_")
    for char in ["/", "\\", ":", " ", ",", ";"]:
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or "report"


def _build_base_name(report: dict, run_id: str | None) -> str:
    if run_id:
        return _safe_name(run_id)
    symbols = report.get("symbols") or []
    symbols_key = "__".join(symbols) if symbols else "report"
    start = report.get("start_date") or "none"
    end = report.get("end_date") or "none"
    interval = report.get("interval") or "1d"
    return _safe_name(f"{symbols_key}_{start}_{end}_{interval}")


def _write_comparison_summary(path: Path, report: dict) -> None:
    rows = (report.get("comparison") or {}).get("summary") or []
    headers = [
        "algorithm",
        "objective_value",
        "expected_return",
        "portfolio_volatility",
        "sharpe_ratio",
        "elapsed_ms",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in headers})


def _write_weights_by_algorithm(path: Path, report: dict) -> None:
    results = report.get("results") or []
    symbols: list[str] = sorted(
        {
            symbol
            for result in results
            for symbol in (result.get("weights") or {}).keys()
        }
    )
    headers = ["algorithm", *symbols]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        for result in results:
            weights = result.get("weights") or {}
            writer.writerow([result.get("algorithm"), *[weights.get(symbol, 0.0) for symbol in symbols]])


def export_experiment_results(
    report: dict,
    output_dir: str | Path = "examples/exports",
    run_id: str | None = None,
) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_name = _build_base_name(report, run_id)
    full_report_path = out_dir / f"{base_name}_full_report.json"
    comparison_path = out_dir / f"{base_name}_comparison_summary.csv"
    weights_path = out_dir / f"{base_name}_weights_by_algorithm.csv"

    full_report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_comparison_summary(comparison_path, report)
    _write_weights_by_algorithm(weights_path, report)

    return {
        "full_report_json": str(full_report_path),
        "comparison_summary_csv": str(comparison_path),
        "weights_by_algorithm_csv": str(weights_path),
    }

