"""Helpers para respostas compatíveis com API Gateway HTTP API proxy."""

from __future__ import annotations

import json
from typing import Any


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
