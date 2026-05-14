"""Executa o experimento MVP localmente e salva resultados em examples/."""

from __future__ import annotations

import argparse

from otimizador.application import run_full_experiment
from otimizador.evaluation.exporter import export_experiment_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executa experimento local.")
    parser.add_argument("--symbols", type=str, default=None)
    parser.add_argument("--period", type=str, default=None)
    parser.add_argument("--start-date", type=str, default=None)
    parser.add_argument("--end-date", type=str, default=None)
    parser.add_argument("--interval", type=str, default=None)
    parser.add_argument("--max-weight", type=float, default=None)
    parser.add_argument("--export-dir", type=str, default="examples/exports")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    symbols = None
    if args.symbols:
        symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]

    output = run_full_experiment(
        symbols=symbols,
        period=args.period,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval,
        max_weight=args.max_weight,
    )
    files = export_experiment_results(output, output_dir=args.export_dir, run_id="manual_run")
    print("Arquivos exportados:")
    for key, value in files.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
