"""Executa o experimento MVP localmente e salva resultados em examples/."""

from __future__ import annotations

import json
from pathlib import Path

from otimizador.application import run_full_experiment


def main() -> None:
    output = run_full_experiment()
    examples_dir = Path("examples")
    examples_dir.mkdir(parents=True, exist_ok=True)

    full_path = examples_dir / "petr4_full_report.json"
    full_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    for result in output["results"]:
        path = examples_dir / f"{result['algorithm']}.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Relatório salvo em: {full_path}")


if __name__ == "__main__":
    main()
