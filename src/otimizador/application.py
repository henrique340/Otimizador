"""Orquestracao ponta a ponta do experimento local."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from otimizador.algorithms.genetic import run_genetic_algorithm
from otimizador.algorithms.linear_programming import run_linear_programming
from otimizador.algorithms.simulated_annealing import run_simulated_annealing
from otimizador.data.features import build_feature_set
from otimizador.data.ingestion import fetch_prices
from otimizador.domain.config import AppConfig, load_config_from_env
from otimizador.domain.models import OptimizationRequest
from otimizador.domain.objective import LinearRiskAdjustedObjective
from otimizador.domain.schema import validate_algorithm_output
from otimizador.evaluation.comparison import build_comparison_report


def build_optimization_request(config: AppConfig) -> OptimizationRequest:
    prices = fetch_prices(config.data)
    features = build_feature_set(config.data.symbols, prices)
    return OptimizationRequest(
        symbol=features.symbol,
        feature_names=features.feature_names,
        expected_returns=features.expected_returns,
        volatility=features.volatility,
        covariance_matrix=features.covariance_matrix,
        risk_aversion=config.optimizer.risk_aversion,
        max_weight=config.optimizer.max_weight,
        seed=config.optimizer.random_seed,
        metadata={
            "symbols": config.data.symbols,
            "period": config.data.period,
            "interval": config.data.interval,
            "samples": len(features.frame),
            "max_weight": config.optimizer.max_weight,
        },
    )


def run_full_experiment(
    config: AppConfig | None = None,
    symbols: list[str] | None = None,
    period: str | None = None,
    interval: str | None = None,
    max_weight: float | None = None,
) -> dict[str, Any]:
    cfg = config or load_config_from_env()

    data_cfg = cfg.data
    if symbols:
        parsed = [item.strip().upper() for item in symbols if item and item.strip()]
        if parsed:
            data_cfg = replace(data_cfg, symbols=parsed)
    if period:
        data_cfg = replace(data_cfg, period=period)
    if interval:
        data_cfg = replace(data_cfg, interval=interval)

    cfg = replace(cfg, data=data_cfg)
    if max_weight is not None:
        cfg = replace(cfg, optimizer=replace(cfg.optimizer, max_weight=max_weight))

    request = build_optimization_request(cfg)
    objective = LinearRiskAdjustedObjective(risk_aversion=request.risk_aversion)

    results = [
        run_linear_programming(request, objective),
        run_genetic_algorithm(
            request=request,
            objective=objective,
            population_size=cfg.optimizer.ga_population_size,
            generations=cfg.optimizer.ga_generations,
        ),
        run_simulated_annealing(
            request=request,
            objective=objective,
            iterations=cfg.optimizer.sa_iterations,
            initial_temperature=cfg.optimizer.sa_initial_temperature,
            cooling_rate=cfg.optimizer.sa_cooling_rate,
        ),
    ]

    payload_results = []
    for result in results:
        result_dict = result.to_dict()
        result_dict["metadata"].update(request.metadata)
        validate_algorithm_output(result_dict)
        payload_results.append(result_dict)

    return {
        "symbol": request.symbol,
        "symbols": cfg.data.symbols,
        "objective": "linear_risk_adjusted_return",
        "results": payload_results,
        "comparison": build_comparison_report(results),
    }
