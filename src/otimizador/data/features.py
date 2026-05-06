"""Feature engineering desacoplado da ingestao."""

from __future__ import annotations

import numpy as np
import pandas as pd

from otimizador.domain.models import FeatureSet


def build_feature_set(symbols: list[str], prices: pd.DataFrame) -> FeatureSet:
    if prices.empty:
        raise ValueError("Nao ha dados de preco para gerar features.")

    returns = prices.pct_change().dropna()
    if returns.empty:
        raise ValueError("Nao ha dados suficientes para geracao de features.")

    feature_names = list(returns.columns)
    expected_returns = returns.mean().to_numpy(dtype=float)
    volatility = returns.std(ddof=0).replace(0, np.nan).fillna(1e-8).to_numpy(dtype=float)
    covariance_matrix = returns.cov().to_numpy(dtype=float)

    return FeatureSet(
        symbol=",".join(symbols),
        feature_names=feature_names,
        expected_returns=expected_returns,
        volatility=volatility,
        covariance_matrix=covariance_matrix,
        frame=returns,
    )
