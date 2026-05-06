"""Comparacao padronizada entre resultados de algoritmos."""

from __future__ import annotations

from typing import Any

from otimizador.domain.models import AlgorithmResult


def rank_results(results: list[AlgorithmResult]) -> list[AlgorithmResult]:
    return sorted(results, key=lambda r: r.objective_value, reverse=True)


def build_comparison_report(results: list[AlgorithmResult]) -> dict[str, Any]:
    ordered = rank_results(results)
    return {
        "ranking": [result.algorithm for result in ordered],
        "summary": [
            {
                "algorithm": result.algorithm,
                "objective_value": result.objective_value,
                "expected_return": result.expected_return,
                "elapsed_ms": result.elapsed_ms,
                "portfolio_volatility": result.metadata.get("portfolio_volatility"),
                "sharpe_ratio": result.metadata.get("sharpe_ratio"),
                "weights": result.weights,
                "risk_contribution_pct": result.metadata.get("risk_contribution_pct", {}),
            }
            for result in ordered
        ],
        "winner": ordered[0].algorithm if ordered else None,
    }
