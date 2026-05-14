"""Gera relatorio PDF com resultados e graficos do otimizador."""

from __future__ import annotations

import argparse
from pathlib import Path

from otimizador.evaluation.report_pdf import generate_pdf_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera relatorio PDF com graficos")
    parser.add_argument("--export-dir", default="examples/exports", help="Diretorio dos arquivos exportados")
    parser.add_argument("--figures-dir", default="docs/figures", help="Diretorio com graficos PNG")
    parser.add_argument("--output", default="docs/reports/relatorio_otimizador.pdf", help="Arquivo PDF de saida")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_pdf = generate_pdf_report(
        export_dir=Path(args.export_dir),
        figures_dir=Path(args.figures_dir),
        output=Path(args.output),
    )
    print(f"Relatorio PDF gerado em: {output_pdf}")


if __name__ == "__main__":
    main()
