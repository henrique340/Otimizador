"""Ingestao de dados de mercado via yfinance com cache local em CSV."""

from __future__ import annotations

import os
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from otimizador.domain.config import DataConfig


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _cache_file_path(config: DataConfig) -> Path:
    cache_dir = Path(config.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    symbols_key = "__".join(config.symbols).replace(".", "_")
    if config.start_date or config.end_date:
        start_key = (config.start_date or "none").replace("-", "")
        end_key = (config.end_date or "none").replace("-", "")
        window_key = f"{start_key}_{end_key}"
    else:
        window_key = config.period
    filename = f"{symbols_key}_{window_key}_{config.interval}.csv"
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


def _resolve_date_index(config: DataConfig) -> pd.DatetimeIndex:
    if config.start_date or config.end_date:
        start = config.start_date or "2018-01-01"
        end = config.end_date or pd.Timestamp.today().strftime("%Y-%m-%d")
        idx = pd.date_range(start=start, end=end, freq="B")
        if len(idx) >= 2:
            return idx

    period_map = {
        "1mo": 22,
        "3mo": 66,
        "6mo": 132,
        "1y": 252,
        "2y": 504,
        "5y": 1260,
        "10y": 2520,
        "max": 2520,
    }
    size = period_map.get((config.period or "").lower(), 504)
    end = pd.Timestamp.today().normalize()
    return pd.date_range(end=end, periods=size, freq="B")


def _generate_synthetic_prices(config: DataConfig) -> pd.DataFrame:
    idx = _resolve_date_index(config)
    data: dict[str, np.ndarray] = {}
    for i, symbol in enumerate(config.symbols):
        # Deterministico por simbolo para facilitar reproducao em demos.
        seed = abs(hash(symbol)) % (2**32)
        rng = np.random.default_rng(seed)
        base_price = 80.0 + (i * 20.0)
        daily_mu = 0.0004 + (i * 0.00005)
        daily_sigma = 0.018 + (i * 0.0015)
        returns = rng.normal(loc=daily_mu, scale=daily_sigma, size=len(idx))
        path = base_price * np.exp(np.cumsum(returns))
        data[symbol] = path
    return pd.DataFrame(data, index=idx)


def _run_download_with_retries(
    *,
    tickers: str,
    interval: str,
    period: str | None,
    date_kwargs: dict[str, str],
    auto_adjust: bool,
    retries: int = 3,
) -> pd.DataFrame:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            result = yf.download(
                tickers=tickers,
                interval=interval,
                auto_adjust=auto_adjust,
                progress=False,
                threads=False,
                **({"period": period} if (period and not date_kwargs) else {}),
                **date_kwargs,
            )
            if result is not None and not result.empty:
                return result
        except Exception as exc:  # noqa: PERF203
            last_exc = exc
        # backoff curto para evitar bursts/rate-limit
        time.sleep(0.6 * (attempt + 1))

    if last_exc is not None:
        raise last_exc
    return pd.DataFrame()


def _fallback_period_for_range(start_date: str | None, end_date: str | None) -> str:
    if not start_date:
        return "max"
    try:
        start = pd.Timestamp(start_date).date()
        end = pd.Timestamp(end_date).date() if end_date else date.today()
        years = max(1, int((end - start).days / 365) + 1)
        # Yahoo aceita 1y,2y,5y,10y,max etc. Para ranges longos, max é mais robusto.
        if years <= 2:
            return "2y"
        if years <= 5:
            return "5y"
        if years <= 10:
            return "10y"
        return "max"
    except Exception:
        return "max"


def _download_from_yfinance(config: DataConfig) -> pd.DataFrame:
    """Try different yfinance paths to reduce empty-download failures."""
    symbols = config.symbols
    tickers = " ".join(symbols)
    date_kwargs: dict[str, str] = {}
    if config.start_date:
        date_kwargs["start"] = config.start_date
    if config.end_date:
        date_kwargs["end"] = config.end_date

    attempts: list[pd.DataFrame | None] = []
    # 1) Download em lote com auto_adjust=True
    attempts.append(
        _run_download_with_retries(
            tickers=tickers,
            interval=config.interval,
            period=config.period,
            date_kwargs=date_kwargs,
            auto_adjust=True,
        )
    )
    # 2) Mesmo request sem auto_adjust (alguns ativos falham só com adjust)
    attempts.append(
        _run_download_with_retries(
            tickers=tickers,
            interval=config.interval,
            period=config.period,
            date_kwargs=date_kwargs,
            auto_adjust=False,
        )
    )
    # 3) Fallback: usar period robusto e filtrar intervalo depois
    period_fallback = _fallback_period_for_range(config.start_date, config.end_date)
    attempts.append(
        _run_download_with_retries(
            tickers=tickers,
            interval=config.interval,
            period=period_fallback,
            date_kwargs={},
            auto_adjust=True,
        )
    )

    series_by_symbol: dict[str, pd.Series] = {}
    for symbol in symbols:
        try:
            frame_history = yf.Ticker(symbol).history(
                interval=config.interval,
                auto_adjust=True,
                **({"period": config.period} if not date_kwargs else {}),
                **date_kwargs,
            )
            if frame_history is None or frame_history.empty:
                frame_history = yf.Ticker(symbol).history(
                    interval=config.interval,
                    auto_adjust=True,
                    period=period_fallback,
                )
            if (
                frame_history is not None
                and not frame_history.empty
                and (config.start_date or config.end_date)
            ):
                frame_history = frame_history.loc[
                    config.start_date or frame_history.index.min() : config.end_date
                    or frame_history.index.max()
                ]
            if frame_history is not None and not frame_history.empty and "Close" in frame_history.columns:
                series_by_symbol[symbol] = frame_history["Close"]
        except Exception:
            continue

    if series_by_symbol:
        attempts.append(pd.DataFrame(series_by_symbol))

    for candidate in attempts:
        if candidate is not None and not candidate.empty:
            normalized = _normalize_price_frame(candidate, symbols)
            if config.start_date or config.end_date:
                normalized = normalized.loc[
                    config.start_date or normalized.index.min() : config.end_date
                    or normalized.index.max()
                ]
            if not normalized.empty:
                return normalized

    raise ValueError(
        f"Download vazio no yfinance para symbols={symbols}, "
        f"period={config.period}, start={config.start_date}, "
        f"end={config.end_date}, interval={config.interval}."
    )


def fetch_prices(config: DataConfig) -> pd.DataFrame:
    cache_path = _cache_file_path(config)
    try:
        normalized = _download_from_yfinance(config)
        normalized.to_csv(cache_path, index=True)
        return normalized
    except Exception as exc:
        if _env_flag("OTIMIZADOR_ALLOW_SYNTHETIC_DATA", default=False):
            synthetic = _generate_synthetic_prices(config)
            synthetic.to_csv(cache_path, index=True)
            return synthetic
        if not cache_path.exists():
            raise ValueError(
                f"Falha na ingestao sem cache local. Detalhes: {exc}"
            ) from exc
        cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return _normalize_price_frame(cached, config.symbols)
