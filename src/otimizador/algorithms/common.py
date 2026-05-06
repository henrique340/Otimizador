"""Utilitarios compartilhados pelos algoritmos."""

from __future__ import annotations

import time

import numpy as np

from otimizador.domain.models import AlgorithmResult, OptimizationRequest
from otimizador.domain.objective import ObjectiveFunction


def normalize_weights(weights: np.ndarray, max_weight: float = 1.0) -> np.ndarray:
    if max_weight <= 0 or max_weight > 1:
        raise ValueError("max_weight deve estar no intervalo (0, 1].")

    clipped = np.clip(weights, 0.0, None)
    total = float(np.sum(clipped))
    if total == 0:
        clipped = np.full_like(clipped, 1.0 / len(clipped), dtype=float)
    else:
        clipped = clipped / total

    n_assets = len(clipped)
    if max_weight * n_assets < 1.0 - 1e-12:
        raise ValueError(
            "max_weight inviavel para a quantidade de ativos: max_weight * n_assets < 1."
        )

    if max_weight >= 1.0:
        return clipped

    weights_proj = clipped.copy()
    free = np.ones(n_assets, dtype=bool)
    fixed = np.zeros(n_assets, dtype=float)

    for _ in range(n_assets * 2):
        over = free & (weights_proj > max_weight + 1e-12)
        if not np.any(over):
            break
        fixed[over] = max_weight
        free[over] = False
        remaining = 1.0 - float(np.sum(fixed))
        if remaining < 0:
            remaining = 0.0
        if not np.any(free):
            break
        free_values = weights_proj[free]
        free_sum = float(np.sum(free_values))
        if free_sum <= 0:
            weights_proj[free] = remaining / int(np.sum(free))
        else:
            weights_proj[free] = (free_values / free_sum) * remaining

    weights_proj[~free] = fixed[~free]
    weights_proj = np.clip(weights_proj, 0.0, max_weight)
    final_sum = float(np.sum(weights_proj))
    if final_sum == 0:
        return np.full_like(weights_proj, 1.0 / n_assets, dtype=float)
    return weights_proj / final_sum


def _risk_metrics(request: OptimizationRequest, normalized: np.ndarray) -> dict[str, object]:
    covariance = request.covariance_matrix
    if covariance is None:
        covariance = np.diag(np.square(request.volatility))

    covariance = np.asarray(covariance, dtype=float)
    portfolio_var = float(normalized @ covariance @ normalized)
    portfolio_var = max(portfolio_var, 0.0)
    portfolio_vol = float(np.sqrt(portfolio_var))

    cov_times_w = covariance @ normalized
    if portfolio_vol > 0:
        risk_contrib = (normalized * cov_times_w) / portfolio_vol
    else:
        risk_contrib = np.zeros_like(normalized)

    total_rc = float(np.sum(risk_contrib))
    if total_rc > 0:
        risk_contrib_pct = risk_contrib / total_rc
    else:
        risk_contrib_pct = np.zeros_like(risk_contrib)

    expected_return = float(np.dot(normalized, request.expected_returns))
    sharpe = float(expected_return / portfolio_vol) if portfolio_vol > 0 else 0.0

    return {
        "portfolio_volatility": portfolio_vol,
        "sharpe_ratio": sharpe,
        "asset_volatility": {
            name: float(value)
            for name, value in zip(request.feature_names, request.volatility)
        },
        "risk_contribution": {
            name: float(value)
            for name, value in zip(request.feature_names, risk_contrib)
        },
        "risk_contribution_pct": {
            name: float(value)
            for name, value in zip(request.feature_names, risk_contrib_pct)
        },
    }


def build_result(
    algorithm: str,
    request: OptimizationRequest,
    weights: np.ndarray,
    objective: ObjectiveFunction,
    elapsed_ms: float,
    extra_metadata: dict | None = None,
) -> AlgorithmResult:
    normalized = normalize_weights(weights, max_weight=request.max_weight)
    expected_return = float(np.dot(normalized, request.expected_returns))
    objective_value = objective.evaluate(
        normalized,
        request.expected_returns,
        request.volatility,
        request.covariance_matrix,
    )

    metadata = {"risk_aversion": request.risk_aversion}
    metadata.update(_risk_metrics(request, normalized))

    if extra_metadata:
        metadata.update(extra_metadata)

    return AlgorithmResult(
        algorithm=algorithm,
        symbol=request.symbol,
        objective_value=objective_value,
        expected_return=expected_return,
        weights={
            name: float(value) for name, value in zip(request.feature_names, normalized)
        },
        elapsed_ms=elapsed_ms,
        metadata=metadata,
    )


def timed_run(fn):
    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        value = fn(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return value, elapsed_ms

    return wrapped
