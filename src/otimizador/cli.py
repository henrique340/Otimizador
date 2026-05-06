#!/usr/bin/env python3
"""CLI simples para execução local do MVP."""

from __future__ import annotations

import json

from otimizador.application import run_full_experiment


def main() -> None:
    payload = run_full_experiment()
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
