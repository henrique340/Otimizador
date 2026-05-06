from __future__ import annotations

from otimizador.domain.models import AlgorithmResult
from otimizador.evaluation.comparison import build_comparison_report


def test_build_comparison_report_sorts_by_objective():
    low = AlgorithmResult(
        algorithm="low",
        symbol="PETR4.SA",
        objective_value=0.2,
        expected_return=0.3,
        weights={"a": 1.0},
        elapsed_ms=10.0,
        metadata={},
    )
    high = AlgorithmResult(
        algorithm="high",
        symbol="PETR4.SA",
        objective_value=0.5,
        expected_return=0.4,
        weights={"a": 1.0},
        elapsed_ms=8.0,
        metadata={},
    )

    report = build_comparison_report([low, high])

    assert report["winner"] == "high"
    assert report["ranking"] == ["high", "low"]
