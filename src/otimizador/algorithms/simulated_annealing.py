"""Implementação de simulated annealing para pesos normalizados."""

from __future__ import annotations

import math

import numpy as np

from otimizador.algorithms.common import build_result, normalize_weights, timed_run
from otimizador.domain.models import AlgorithmResult, OptimizationRequest
from otimizador.domain.objective import ObjectiveFunction


def _energy(
    candidate: np.ndarray, request: OptimizationRequest, objective: ObjectiveFunction
) -> float:
    normalized = normalize_weights(candidate, max_weight=request.max_weight)
    return -objective.evaluate(
        normalized,
        request.expected_returns,
        request.volatility,
        request.covariance_matrix,
    )


@timed_run
def _solve_sa(
    request: OptimizationRequest,
    objective: ObjectiveFunction,
    iterations: int,
    initial_temperature: float,
    cooling_rate: float,
) -> np.ndarray:
    rng = np.random.default_rng(request.seed)
    dimension = len(request.feature_names)
    current = normalize_weights(
        rng.dirichlet(np.ones(dimension)), max_weight=request.max_weight
    )
    current_energy = _energy(current, request, objective)
    best = current.copy()
    best_energy = current_energy
    temperature = initial_temperature

    for _ in range(iterations):
        proposal = normalize_weights(
            current + rng.normal(0.0, 0.05, size=dimension),
            max_weight=request.max_weight,
        )
        proposal_energy = _energy(proposal, request, objective)

        if proposal_energy < current_energy:
            accept = True
        else:
            delta = proposal_energy - current_energy
            accept = rng.random() < math.exp(-delta / max(temperature, 1e-12))

        if accept:
            current = proposal
            current_energy = proposal_energy
            if current_energy < best_energy:
                best = current.copy()
                best_energy = current_energy

        temperature *= cooling_rate
    return best


def run_simulated_annealing(
    request: OptimizationRequest,
    objective: ObjectiveFunction,
    iterations: int,
    initial_temperature: float,
    cooling_rate: float,
) -> AlgorithmResult:
    weights, elapsed_ms = _solve_sa(
        request=request,
        objective=objective,
        iterations=iterations,
        initial_temperature=initial_temperature,
        cooling_rate=cooling_rate,
    )
    return build_result(
        algorithm="simulated_annealing",
        request=request,
        weights=weights,
        objective=objective,
        elapsed_ms=elapsed_ms,
        extra_metadata={
            "iterations": iterations,
            "initial_temperature": initial_temperature,
            "cooling_rate": cooling_rate,
            "seed": request.seed,
        },
    )
