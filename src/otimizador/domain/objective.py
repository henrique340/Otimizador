"""Função objetivo comum para todos os algoritmos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class ObjectiveFunction(Protocol):
    def evaluate(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        volatility: np.ndarray,
        covariance_matrix: np.ndarray | None = None,
    ) -> float:
        ...


@dataclass(frozen=True)
class LinearRiskAdjustedObjective:
    """Objetivo linear: retorno esperado menos penalidade por volatilidade."""

    risk_aversion: float

    def evaluate(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        volatility: np.ndarray,
        covariance_matrix: np.ndarray | None = None,
    ) -> float:
        covariance = covariance_matrix
        if covariance is None:
            covariance = np.diag(np.square(volatility))
        covariance = np.asarray(covariance, dtype=float)
        portfolio_variance = float(weights @ covariance @ weights)
        portfolio_variance = max(portfolio_variance, 0.0)
        portfolio_volatility = float(np.sqrt(portfolio_variance))

        expected_portfolio_return = float(np.dot(weights, expected_returns))
        return expected_portfolio_return - (self.risk_aversion * portfolio_volatility)
