from __future__ import annotations

import pandas as pd

from otimizador.data.features import build_feature_set


def test_build_feature_set_generates_expected_vectors():
    index = pd.date_range("2024-01-01", periods=90, freq="D")
    prices = pd.DataFrame(
        {
            "PETR4.SA": [100 + (i * 0.2) for i in range(90)],
            "VALE3.SA": [70 + (i * 0.1) for i in range(90)],
            "ITUB4.SA": [30 + (i * 0.05) for i in range(90)],
        },
        index=index,
    )

    features = build_feature_set(["PETR4.SA", "VALE3.SA", "ITUB4.SA"], prices)

    assert features.symbol == "PETR4.SA,VALE3.SA,ITUB4.SA"
    assert features.feature_names == ["PETR4.SA", "VALE3.SA", "ITUB4.SA"]
    assert len(features.expected_returns) == 3
    assert len(features.volatility) == 3
