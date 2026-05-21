"""Geracao de relatorio PDF a partir de arquivos exportados e graficos."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def _find_latest_report(export_dir: Path) -> Path:
    candidates = sorted(export_dir.glob("*_full_report.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Nenhum arquivo *_full_report.json encontrado em {export_dir}")
    return candidates[0]


def _draw_header(pdf: canvas.Canvas, title: str) -> None:
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(2 * cm, 28 * cm, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(2 * cm, 27.3 * cm, "Relatorio gerado automaticamente pelo Otimizador")


def generate_pdf_report(
    export_dir: str | Path = "examples/exports",
    figures_dir: str | Path = "docs/figures",
    output: str | Path = "docs/reports/relatorio_otimizador.pdf",
) -> Path:
    export_path = Path(export_dir)
    figures_path = Path(figures_dir)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_file = _find_latest_report(export_path)
    report = json.loads(report_file.read_text(encoding="utf-8"))

    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    _draw_header(pdf, "Relatorio de Otimizacao de Carteira")

    symbols = ", ".join(report.get("symbols") or [])
    comparison = report.get("comparison") or {}
    winner = comparison.get("winner") or "-"

    pdf.setFont("Helvetica", 11)
    pdf.drawString(2 * cm, 25.8 * cm, f"Ativos: {symbols or '-'}")
    pdf.drawString(2 * cm, 25.1 * cm, f"Vencedor: {winner}")
    pdf.drawString(2 * cm, 24.4 * cm, f"Periodo: {report.get('period') or '-'}")
    pdf.drawString(2 * cm, 23.7 * cm, f"Janela: {report.get('start_date') or '-'} ate {report.get('end_date') or '-'}")

    y = 22.4 * cm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2 * cm, y, "Resumo por algoritmo")
    y -= 0.7 * cm

    pdf.setFont("Helvetica", 10)
    for row in comparison.get("summary") or []:
        text = (
            f"- {row.get('algorithm')}: retorno={row.get('expected_return')}, "
            f"vol={row.get('portfolio_volatility')}, sharpe={row.get('sharpe_ratio')}"
        )
        pdf.drawString(2 * cm, y, text[:110])
        y -= 0.55 * cm
        if y < 3 * cm:
            pdf.showPage()
            _draw_header(pdf, "Relatorio de Otimizacao de Carteira (continua)")
            y = 25.8 * cm
            pdf.setFont("Helvetica", 10)

    figure_candidates = sorted(figures_path.glob("*.png"))
    if figure_candidates:
        pdf.showPage()
        _draw_header(pdf, "Graficos")
        y = 25.6 * cm
        for image_path in figure_candidates[:3]:
            pdf.setFont("Helvetica", 10)
            pdf.drawString(2 * cm, y + 0.3 * cm, image_path.name)
            try:
                pdf.drawImage(str(image_path), 2 * cm, y - 5.2 * cm, width=16 * cm, height=5 * cm, preserveAspectRatio=True, anchor="n")
            except Exception:
                pdf.drawString(2 * cm, y - 0.3 * cm, "Falha ao carregar imagem no PDF.")
            y -= 6.3 * cm
            if y < 4 * cm:
                break

    pdf.save()
    return output_path

