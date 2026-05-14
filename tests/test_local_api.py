from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from otimizador.infrastructure.local_api import app


def test_report_pdf_endpoint_returns_pdf(mocker, tmp_path: Path):
    client = TestClient(app)
    fake_pdf = tmp_path / "relatorio.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    mocker.patch(
        "otimizador.infrastructure.local_api.run_full_experiment",
        return_value={
            "symbol": "PETR4.SA,VALE3.SA",
            "symbols": ["PETR4.SA", "VALE3.SA"],
            "objective": "linear_risk_adjusted_return",
            "period": "2y",
            "start_date": "2015-01-01",
            "end_date": "2025-12-31",
            "interval": "1d",
            "results": [],
            "comparison": {"winner": "linear_programming", "summary": []},
        },
    )
    mocker.patch("otimizador.infrastructure.local_api.export_experiment_results")
    mocker.patch("otimizador.infrastructure.local_api.subprocess.run")
    mocker.patch(
        "otimizador.infrastructure.local_api.generate_pdf_report",
        return_value=fake_pdf.resolve(),
    )

    response = client.post(
        "/report/pdf",
        json={
            "algorithm": "all",
            "symbols": ["PETR4.SA", "VALE3.SA"],
            "start_date": "2015-01-01",
            "end_date": "2025-12-31",
            "interval": "1d",
            "max_weight": 0.6,
            "regenerate_charts": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
