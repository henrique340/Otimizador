from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pandas as pd

from otimizador.data.ingestion import fetch_prices
from otimizador.domain.config import DataConfig


def _test_cache_dir() -> Path:
    path = Path("cache") / f"test_{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_fetch_prices_download_and_cache(mocker):
    cache_dir = _test_cache_dir()
    index = pd.date_range("2025-01-01", periods=3, freq="D")
    columns = pd.MultiIndex.from_product([["Close"], ["PETR4.SA", "VALE3.SA"]])
    mocked_frame = pd.DataFrame(
        [[10.0, 70.0], [10.5, 70.5], [10.2, 70.2]], index=index, columns=columns
    )
    mocker.patch("otimizador.data.ingestion.yf.download", return_value=mocked_frame)
    mocker.patch("otimizador.data.ingestion.yf.Ticker")

    config = DataConfig(symbols=["PETR4.SA", "VALE3.SA"], period="1mo", interval="1d", cache_dir=str(cache_dir))
    output = fetch_prices(config)

    assert len(output) == 3
    assert set(output.columns) == {"PETR4.SA", "VALE3.SA"}
    assert list(cache_dir.glob("*.csv"))


def test_fetch_prices_fallback_to_cache(mocker):
    cache_dir = _test_cache_dir()
    index = pd.date_range("2025-01-01", periods=2, freq="D")
    cached = pd.DataFrame(
        {
            "PETR4.SA": [11.0, 11.2],
            "VALE3.SA": [68.0, 68.5],
        },
        index=index,
    )
    cache_file = cache_dir / "PETR4_SA__VALE3_SA_1mo_1d.csv"
    cached.to_csv(cache_file, index=True)

    mocker.patch("otimizador.data.ingestion.yf.download", side_effect=RuntimeError("network"))
    mocker.patch("otimizador.data.ingestion.yf.Ticker", side_effect=RuntimeError("network"))
    config = DataConfig(symbols=["PETR4.SA", "VALE3.SA"], period="1mo", interval="1d", cache_dir=str(cache_dir))
    output = fetch_prices(config)

    assert len(output) == 2
    assert set(output.columns) == {"PETR4.SA", "VALE3.SA"}
