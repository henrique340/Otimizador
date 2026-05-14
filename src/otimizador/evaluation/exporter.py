"""Exporta resultados do experimento para JSON e CSV."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def _slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def export_experiment_results(
    report: dict[str, Any],
    output_dir: str | Path = "examples/exports",
    run_id: str | None = None,
) -> dict[str, str]:
    export_dir = Path(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    stamp = run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base = f"otimizador_{stamp}"

    raw_path = export_dir / f"{base}_full_report.json"
    raw_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary_rows = []
    weights_rows = []
    for result in report.get("results", []):
        metadata = result.get("metadata", {})
        summary_rows.append(
            {
                "algorithm": result.get("algorithm"),
                "symbol": result.get("symbol"),
                "objective_value": result.get("objective_value"),
                "expected_return": result.get("expected_return"),
                "portfolio_volatility": metadata.get("portfolio_volatility"),
                "sharpe_ratio": metadata.get("sharpe_ratio"),
                "elapsed_ms": result.get("elapsed_ms"),
            }
        )

        for asset, weight in result.get("weights", {}).items():
            weights_rows.append(
                {
                    "algorithm": result.get("algorithm"),
                    "asset": asset,
                    "weight": weight,
                }
            )

    summary_path = export_dir / f"{base}_comparison_summary.csv"
    weights_path = export_dir / f"{base}_weights_by_algorithm.csv"
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    pd.DataFrame(weights_rows).to_csv(weights_path, index=False)

    slug_symbols = _slug(",".join(report.get("symbols", [])))
    latest_json = export_dir / f"{slug_symbols}_latest.json"
    latest_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "full_report_json": str(raw_path.resolve()),
        "comparison_summary_csv": str(summary_path.resolve()),
        "weights_by_algorithm_csv": str(weights_path.resolve()),
        "latest_json": str(latest_json.resolve()),
    }

