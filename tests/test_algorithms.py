from __future__ import annotations

import numpy as np

from otimizador.algorithms.genetic import run_genetic_algorithm
from otimizador.algorithms.linear_programming import run_linear_programming
from otimizador.algorithms.simulated_annealing import run_simulated_annealing
from otimizador.domain.models import OptimizationRequest
from otimizador.domain.objective import LinearRiskAdjustedObjective


def _request() -> OptimizationRequest:
    return OptimizationRequest(
        symbol="PETR4.SA,VALE3.SA,ITUB4.SA",
        feature_names=["PETR4.SA", "VALE3.SA", "ITUB4.SA"],
        expected_returns=np.array([0.0010, 0.0008, 0.0006]),
        volatility=np.array([0.012, 0.009, 0.007]),
        risk_aversion=0.3,
        max_weight=0.6,
        seed=7,
    )


def test_algorithms_return_normalized_weights():
    request = _request()
    objective = LinearRiskAdjustedObjective(risk_aversion=request.risk_aversion)

    results = [
        run_linear_programming(request, objective),
        run_genetic_algorithm(request, objective, population_size=16, generations=10),
        run_simulated_annealing(
            request,
            objective,
            iterations=50,
            initial_temperature=1.0,
            cooling_rate=0.95,
        ),
    ]

    for result in results:
        assert result.objective_value == result.objective_value
        assert result.elapsed_ms >= 0.0
        assert abs(sum(result.weights.values()) - 1.0) < 1e-6
        assert set(result.weights.keys()) == {"PETR4.SA", "VALE3.SA", "ITUB4.SA"}
        assert max(result.weights.values()) <= request.max_weight + 1e-6
