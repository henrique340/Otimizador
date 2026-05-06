"""Ingestao de dados de mercado via yfinance com cache local em CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

from otimizador.domain.config import DataConfig


def _cache_file_path(config: DataConfig) -> Path:
    cache_dir = Path(config.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    symbols_key = "__".join(config.symbols).replace(".", "_")
    filename = f"{symbols_key}_{config.period}_{config.interval}.csv"
    return cache_dir / filename


def _normalize_price_frame(frame: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    normalized = frame.copy()

    if isinstance(normalized.columns, pd.MultiIndex):
        if "Close" in normalized.columns.get_level_values(0):
            normalized = normalized["Close"]
        else:
            close_cols = [col for col in normalized.columns if col[-1] == "Close"]
            if not close_cols:
                raise ValueError("Dataset nao contem coluna 'Close'.")
            normalized = normalized.loc[:, close_cols]
            normalized.columns = [col[0] for col in close_cols]
    else:
        if "Close" in normalized.columns:
            single_symbol = symbols[0]
            normalized = normalized[["Close"]].rename(columns={"Close": single_symbol})

    available = [symbol for symbol in symbols if symbol in normalized.columns]
    if not available:
        raise ValueError("Nenhum simbolo solicitado foi encontrado no dataset baixado.")

    return normalized[available].dropna()


def _download_from_yfinance(config: DataConfig) -> pd.DataFrame:
    """Try different yfinance paths to reduce empty-download failures."""
    symbols = config.symbols
    tickers = " ".join(symbols)

    attempts: list[pd.DataFrame | None] = []
    attempts.append(
        yf.download(
            tickers=tickers,
            period=config.period,
            interval=config.interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    )

    series_by_symbol: dict[str, pd.Series] = {}
    for symbol in symbols:
        try:
            frame_history = yf.Ticker(symbol).history(
                period=config.period,
                interval=config.interval,
                auto_adjust=True,
            )
            if frame_history is not None and not frame_history.empty and "Close" in frame_history.columns:
                series_by_symbol[symbol] = frame_history["Close"]
        except Exception:
            continue

    if series_by_symbol:
        attempts.append(pd.DataFrame(series_by_symbol))

    for candidate in attempts:
        if candidate is not None and not candidate.empty:
            normalized = _normalize_price_frame(candidate, symbols)
            if not normalized.empty:
                return normalized

    raise ValueError(
        f"Download vazio no yfinance para symbols={symbols}, "
        f"period={config.period}, interval={config.interval}."
    )


def fetch_prices(config: DataConfig) -> pd.DataFrame:
    cache_path = _cache_file_path(config)
    try:
        normalized = _download_from_yfinance(config)
        normalized.to_csv(cache_path, index=True)
        return normalized
    except Exception as exc:
        if not cache_path.exists():
            raise ValueError(
                f"Falha na ingestao sem cache local. Detalhes: {exc}"
            ) from exc
        cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return _normalize_price_frame(cached, config.symbols)
