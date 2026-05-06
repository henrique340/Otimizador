"""Schema JSON padronizado para saída dos algoritmos."""

from __future__ import annotations

from typing import Any


ALGORITHM_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "algorithm",
        "symbol",
        "objective_value",
        "expected_return",
        "weights",
        "elapsed_ms",
        "metadata",
    ],
    "properties": {
        "algorithm": {"type": "string"},
        "symbol": {"type": "string"},
        "objective_value": {"type": "number"},
        "expected_return": {"type": "number"},
        "weights": {
            "type": "object",
            "additionalProperties": {"type": "number"},
            "minProperties": 1,
        },
        "elapsed_ms": {"type": "number", "minimum": 0},
        "metadata": {"type": "object"},
    },
}


def validate_algorithm_output(payload: dict[str, Any]) -> None:
    required = ALGORITHM_OUTPUT_SCHEMA["required"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Campos ausentes no payload: {missing}")
    if not isinstance(payload["weights"], dict) or not payload["weights"]:
        raise ValueError("Campo 'weights' precisa ser um objeto não vazio.")
