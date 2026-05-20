from __future__ import annotations

import json

import pandas as pd

from otimizador.infrastructure.handlers import (
    quantvision_data_handler,
    quantvision_optimize_handler,
    quantvision_report_pdf_handler,
    quantvision_report_handler,
    quantvision_status_handler,
)


def test_status_handler_returns_ok():
    response = quantvision_status_handler.lambda_handler({}, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["status"] == "ok"


def test_optimize_handler_uses_application(mocker):
    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_optimize_handler.run_full_experiment",
        return_value={"symbol": "PETR4.SA,VALE3.SA", "symbols": ["PETR4.SA", "VALE3.SA"], "results": [], "comparison": {}},
    )
    response = quantvision_optimize_handler.lambda_handler({}, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["symbol"] == "PETR4.SA,VALE3.SA"


def test_data_handler_returns_rows(mocker):
    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_data_handler.fetch_prices",
        return_value=pd.DataFrame({"PETR4.SA": [10.0] * 15, "VALE3.SA": [70.0] * 15}),
    )
    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_data_handler.load_config_from_env",
        return_value=mocker.MagicMock(data=mocker.MagicMock(symbols=["PETR4.SA", "VALE3.SA"])),
    )

    response = quantvision_data_handler.lambda_handler({}, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["symbols"] == ["PETR4.SA", "VALE3.SA"]


def test_report_handler_returns_winner(mocker):
    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_report_handler.run_full_experiment",
        return_value={
            "symbol": "PETR4.SA,VALE3.SA",
            "symbols": ["PETR4.SA", "VALE3.SA"],
            "results": [1, 2, 3],
            "comparison": {"winner": "linear_programming", "ranking": ["linear_programming"]},
        },
    )

    response = quantvision_report_handler.lambda_handler({}, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["winner"] == "linear_programming"


def test_report_pdf_handler_returns_base64(mocker, tmp_path):
    fake_pdf = tmp_path / "report.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\nmock")

    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_report_pdf_handler.run_full_experiment",
        return_value={
            "symbol": "PETR4.SA,VALE3.SA",
            "symbols": ["PETR4.SA", "VALE3.SA"],
            "results": [],
            "comparison": {"winner": "linear_programming", "ranking": []},
        },
    )
    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_report_pdf_handler.export_experiment_results",
        return_value={},
    )
    mocker.patch(
        "otimizador.infrastructure.handlers.quantvision_report_pdf_handler.generate_pdf_report",
        return_value=fake_pdf,
    )

    response = quantvision_report_pdf_handler.lambda_handler({}, None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["content_type"] == "application/pdf"
    assert body["filename"] == "report.pdf"
    assert isinstance(body["pdf_base64"], str)
