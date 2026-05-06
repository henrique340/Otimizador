"""Modelos de dominio para entrada e saida dos algoritmos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureSet:
    symbol: str
    feature_names: list[str]
    expected_returns: np.ndarray
    volatility: np.ndarray
    covariance_matrix: np.ndarray | None
    frame: pd.DataFrame


@dataclass(frozen=True)
class OptimizationRequest:
    symbol: str
    feature_names: list[str]
    expected_returns: np.ndarray
    volatility: np.ndarray
    risk_aversion: float
    max_weight: float = 1.0
    covariance_matrix: np.ndarray | None = None
    seed: int = 42
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AlgorithmResult:
    algorithm: str
    symbol: str
    objective_value: float
    expected_return: float
    weights: dict[str, float]
    elapsed_ms: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "symbol": self.symbol,
            "objective_value": self.objective_value,
            "expected_return": self.expected_return,
            "weights": self.weights,
            "elapsed_ms": self.elapsed_ms,
            "metadata": self.metadata,
        }
