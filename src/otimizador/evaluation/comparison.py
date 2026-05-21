"""Comparacao entre resultados de algoritmos."""

from __future__ import annotations

from otimizador.domain.models import AlgorithmResult


def _summary_item(result: AlgorithmResult) -> dict:
    metadata = result.metadata or {}
    return {
        "algorithm": result.algorithm,
        "symbol": result.symbol,
        "objective_value": result.objective_value,
        "expected_return": result.expected_return,
        "elapsed_ms": result.elapsed_ms,
        "weights": result.weights,
        "portfolio_volatility": metadata.get("portfolio_volatility"),
        "sharpe_ratio": metadata.get("sharpe_ratio"),
        "risk_contribution_pct": metadata.get("risk_contribution_pct", {}),
    }


def build_comparison_report(results: list[AlgorithmResult]) -> dict:
    if not results:
        return {"winner": None, "ranking": [], "summary": []}

    sorted_results = sorted(results, key=lambda item: item.objective_value, reverse=True)
    return {
        "winner": sorted_results[0].algorithm,
        "ranking": [item.algorithm for item in sorted_results],
        "summary": [_summary_item(item) for item in sorted_results],
    }

