"""Implementação de algoritmo genético simples e determinístico."""

from __future__ import annotations

import numpy as np

from otimizador.algorithms.common import build_result, normalize_weights, timed_run
from otimizador.domain.models import AlgorithmResult, OptimizationRequest
from otimizador.domain.objective import ObjectiveFunction


def _fitness(
    candidate: np.ndarray, request: OptimizationRequest, objective: ObjectiveFunction
) -> float:
    normalized = normalize_weights(candidate, max_weight=request.max_weight)
    return objective.evaluate(
        normalized,
        request.expected_returns,
        request.volatility,
        request.covariance_matrix,
    )


def _tournament_selection(population: np.ndarray, fitness: np.ndarray) -> np.ndarray:
    idx = np.random.randint(0, len(population), size=3)
    best_idx = idx[np.argmax(fitness[idx])]
    return population[best_idx]


@timed_run
def _solve_ga(
    request: OptimizationRequest, objective: ObjectiveFunction, population_size: int, generations: int
) -> np.ndarray:
    np.random.seed(request.seed)
    dimension = len(request.feature_names)
    population = np.array(
        [
            normalize_weights(
                np.random.dirichlet(np.ones(dimension)), max_weight=request.max_weight
            )
            for _ in range(population_size)
        ]
    )

    for _ in range(generations):
        fit = np.array([_fitness(ind, request, objective) for ind in population])
        next_generation = []
        elite = population[np.argmax(fit)]
        next_generation.append(elite.copy())

        while len(next_generation) < population_size:
            parent1 = _tournament_selection(population, fit)
            parent2 = _tournament_selection(population, fit)
            alpha = np.random.rand()
            child = alpha * parent1 + (1.0 - alpha) * parent2
            mutation = np.random.normal(0.0, 0.05, size=dimension)
            child = normalize_weights(child + mutation, max_weight=request.max_weight)
            next_generation.append(child)

        population = np.array(next_generation)

    final_fitness = np.array([_fitness(ind, request, objective) for ind in population])
    return population[np.argmax(final_fitness)]


def run_genetic_algorithm(
    request: OptimizationRequest,
    objective: ObjectiveFunction,
    population_size: int,
    generations: int,
) -> AlgorithmResult:
    weights, elapsed_ms = _solve_ga(request, objective, population_size, generations)
    return build_result(
        algorithm="genetic_algorithm",
        request=request,
        weights=weights,
        objective=objective,
        elapsed_ms=elapsed_ms,
        extra_metadata={
            "population_size": population_size,
            "generations": generations,
            "seed": request.seed,
        },
    )
