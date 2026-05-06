"""Implementacao do otimizador com restricoes de alocacao."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from otimizador.algorithms.common import build_result, normalize_weights, timed_run
from otimizador.domain.models import AlgorithmResult, OptimizationRequest
from otimizador.domain.objective import ObjectiveFunction


@timed_run
def _solve_lp(request: OptimizationRequest, objective: ObjectiveFunction) -> np.ndarray:
    n_assets = len(request.feature_names)
    if request.max_weight * n_assets < 1.0 - 1e-12:
        raise ValueError(
            "Configuracao invalida: max_weight * quantidade_de_ativos deve ser >= 1."
        )

    initial = normalize_weights(np.ones(n_assets), max_weight=request.max_weight)

    def negative_objective(weights: np.ndarray) -> float:
        return -objective.evaluate(
            weights,
            request.expected_returns,
            request.volatility,
            request.covariance_matrix,
        )

    result = minimize(
        fun=negative_objective,
        x0=initial,
        method="SLSQP",
        bounds=[(0.0, request.max_weight)] * n_assets,
        constraints=[{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}],
    )

    if not result.success or result.x is None:
        raise ValueError(f"Falha na otimizacao com restricoes: {result.message}")
    return normalize_weights(result.x, max_weight=request.max_weight)


def run_linear_programming(
    request: OptimizationRequest, objective: ObjectiveFunction
) -> AlgorithmResult:
    weights, elapsed_ms = _solve_lp(request, objective)
    return build_result(
        algorithm="linear_programming",
        request=request,
        weights=weights,
        objective=objective,
        elapsed_ms=elapsed_ms,
        extra_metadata={"solver": "scipy.optimize.minimize.slsqp"},
    )
