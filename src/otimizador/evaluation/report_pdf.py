"""Geracao de relatorio PDF com resultados e graficos."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _latest_file(directory: Path, pattern: str) -> Path:
    matches = sorted(
        directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not matches:
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado para {pattern} em {directory}"
        )
    return matches[0]


def _fmt_num(value: float | int | str | None, digits: int = 6) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _build_summary_table(summary_df: pd.DataFrame) -> Table:
    data = [
        [
            "Algoritmo",
            "Objective",
            "Retorno",
            "Volatilidade",
            "Sharpe",
            "Tempo (ms)",
        ]
    ]

    for _, row in summary_df.iterrows():
        data.append(
            [
                str(row.get("algorithm", "-")),
                _fmt_num(row.get("objective_value"), 8),
                _fmt_num(row.get("expected_return"), 8),
                _fmt_num(row.get("portfolio_volatility"), 8),
                _fmt_num(row.get("sharpe_ratio"), 6),
                _fmt_num(row.get("elapsed_ms"), 2),
            ]
        )

    table = Table(
        data,
        colWidths=[4.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 2.6 * cm, 2.6 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def _chart_image(path: Path) -> Image:
    image = Image(str(path))
    image._restrictSize(17.0 * cm, 11.5 * cm)
    return image


def generate_pdf_report(
    export_dir: str | Path = "examples/exports",
    figures_dir: str | Path = "docs/figures",
    output: str | Path = "docs/reports/relatorio_otimizador.pdf",
) -> Path:
    export_path = Path(export_dir)
    figures_path = Path(figures_dir)
    output_pdf = Path(output)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    summary_csv = _latest_file(export_path, "*_comparison_summary.csv")
    report_json = _latest_file(export_path, "*_full_report.json")

    summary_df = pd.read_csv(summary_csv)
    report_data = json.loads(report_json.read_text(encoding="utf-8"))

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18)
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"], spaceBefore=8, spaceAfter=6
    )
    text_style = ParagraphStyle(
        "Text", parent=styles["BodyText"], fontSize=10, leading=14
    )

    story = []
    story.append(Paragraph("Relatorio de Otimizacao de Carteira", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Projeto: Otimizador (LP, GA, SA)", text_style))
    story.append(
        Paragraph(f"Simbolos: {', '.join(report_data.get('symbols', []))}", text_style)
    )
    story.append(
        Paragraph(
            (
                f"Janela: {report_data.get('start_date') or '-'} ate "
                f"{report_data.get('end_date') or '-'} | Intervalo: "
                f"{report_data.get('interval') or '-'}"
            ),
            text_style,
        )
    )
    story.append(Spacer(1, 10))

    winner = report_data.get("comparison", {}).get("winner", "-")
    story.append(Paragraph("Resumo Executivo", heading_style))
    story.append(Paragraph(f"Algoritmo vencedor: <b>{winner}</b>", text_style))
    story.append(Paragraph(f"Fonte dos dados exportados: {summary_csv.name}", text_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tabela de Comparacao", heading_style))
    story.append(_build_summary_table(summary_df))
    story.append(PageBreak())

    chart_order = [
        "01_precos_normalizados.png",
        "04_heatmap_correlacao.png",
        "05_pesos_algoritmos.png",
        "06_metricas_algoritmos.png",
        "07_fronteira_risco_retorno.png",
        "09_backtest_acumulado.png",
        "10_drawdown_algoritmos.png",
    ]

    for chart_name in chart_order:
        chart_path = figures_path / chart_name
        if not chart_path.exists():
            continue
        story.append(
            Paragraph(
                chart_name.replace("_", " ").replace(".png", ""), heading_style
            )
        )
        story.append(_chart_image(chart_path))
        story.append(PageBreak())

    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4)
    doc.build(story)
    return output_pdf.resolve()

