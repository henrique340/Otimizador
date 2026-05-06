"""Script utilitário para invocar handlers localmente."""

from __future__ import annotations

import json

from otimizador.infrastructure.handlers.quantvision_data_handler import lambda_handler as data_handler
from otimizador.infrastructure.handlers.quantvision_optimize_handler import lambda_handler as optimize_handler
from otimizador.infrastructure.handlers.quantvision_report_handler import lambda_handler as report_handler
from otimizador.infrastructure.handlers.quantvision_status_handler import lambda_handler as status_handler


def main() -> None:
    handlers = {
        "status": status_handler,
        "data": data_handler,
        "optimize": optimize_handler,
        "report": report_handler,
    }
    for name, fn in handlers.items():
        print(f"=== {name} ===")
        response = fn({}, None)
        print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
