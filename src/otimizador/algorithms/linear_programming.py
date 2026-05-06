"""Implementacao do otimizador com restricoes de alocacao."""

from __future__ import annotations

import numpy as np

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

    rng = np.random.default_rng(request.seed)

    def score(weights: np.ndarray) -> float:
        return objective.evaluate(
            weights,
            request.expected_returns,
            request.volatility,
            request.covariance_matrix,
        )

    # Busca multi-start leve para manter compatibilidade com Lambda sem scipy.
    best = normalize_weights(np.ones(n_assets), max_weight=request.max_weight)
    best_score = score(best)

    samples = max(1200, 400 * n_assets)
    for _ in range(samples):
        candidate = normalize_weights(
            rng.dirichlet(np.ones(n_assets)), max_weight=request.max_weight
        )
        candidate_score = score(candidate)
        if candidate_score > best_score:
            best = candidate
            best_score = candidate_score

    # Refinamento local simples (hill climbing)
    for step in [0.08, 0.04, 0.02, 0.01]:
        improved = True
        while improved:
            improved = False
            for i in range(n_assets):
                for j in range(n_assets):
                    if i == j:
                        continue
                    proposal = best.copy()
                    proposal[i] += step
                    proposal[j] -= step
                    proposal = normalize_weights(proposal, max_weight=request.max_weight)
                    proposal_score = score(proposal)
                    if proposal_score > best_score + 1e-12:
                        best = proposal
                        best_score = proposal_score
                        improved = True
    return best


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
        extra_metadata={"solver": "numpy_multistart_hillclimb"},
    )
