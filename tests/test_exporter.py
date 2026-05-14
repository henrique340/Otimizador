from __future__ import annotations

import json
from pathlib import Path

from otimizador.evaluation.exporter import export_experiment_results


def test_export_experiment_results_creates_files(tmp_path: Path):
    report = {
        "symbol": "PETR4.SA,VALE3.SA",
        "symbols": ["PETR4.SA", "VALE3.SA"],
        "results": [
            {
                "algorithm": "linear_programming",
                "symbol": "PETR4.SA,VALE3.SA",
                "objective_value": 0.12,
                "expected_return": 0.01,
                "weights": {"PETR4.SA": 0.5, "VALE3.SA": 0.5},
                "elapsed_ms": 10.0,
                "metadata": {"portfolio_volatility": 0.02, "sharpe_ratio": 0.5},
            }
        ],
    }

    files = export_experiment_results(report, output_dir=tmp_path, run_id="test_run")

    for file_path in files.values():
        assert Path(file_path).exists()

    content = json.loads(Path(files["full_report_json"]).read_text(encoding="utf-8"))
    assert content["symbols"] == ["PETR4.SA", "VALE3.SA"]
