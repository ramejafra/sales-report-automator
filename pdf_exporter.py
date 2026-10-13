"""
pdf_exporter.py
===============
Genera un PDF ejecutivo con KPIs, tabla de calidad de datos y gráficas
embebidas. Usa reportlab y mantiene el tamaño en una sola página A4 por
sección siempre que sea posible.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_PRIMARY = colors.HexColor("#1F2937")
_ACCENT = colors.HexColor("#2563EB")
_OK = colors.HexColor("#065F46")
_BAD = colors.HexColor("#991B1B")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            textColor=_PRIMARY,
            fontSize=22,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            textColor=_ACCENT,
            fontSize=14,
            spaceAfter=6,
            spaceBefore=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#6B7280"),
        ),
    }


def _kpi_table(kpis) -> Table:
    data = [["Indicador", "Valor"]]
    for row in kpis.itertuples(index=False):
        data.append([str(row[0]), str(row[1])])

    table = Table(data, colWidths=[7 * cm, 9 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ]
        )
    )
    return table


def _df_table(df, max_rows: int = 12) -> Table:
    if df.empty:
        return Table([["Sin datos"]])
    head = [list(df.columns)]
    body = []
    for _, row in df.head(max_rows).iterrows():
        body.append([str(row[c]) for c in df.columns])
    data = head + body

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _quality_summary_table(summary) -> Table:
    data = [
        ["Métrica", "Valor"],
        ["Filas leídas", str(summary.total_rows)],
        ["Filas aceptadas", str(summary.accepted_rows)],
        ["Filas rechazadas", str(summary.rejected_rows)],
        [
            "% Aceptadas",
            f"{(summary.accepted_rows / max(summary.total_rows, 1) * 100):.2f}%",
        ],
    ]
    table = Table(data, colWidths=[7 * cm, 9 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _quality_reasons_table(summary) -> Table | None:
    if not summary.reasons:
        return None
    data = [["Motivo de rechazo", "Conteo"]]
    for motivo, conteo in sorted(
        summary.reasons.items(), key=lambda kv: kv[1], reverse=True
    ):
        data.append([motivo, str(conteo)])
    table = Table(data, colWidths=[12 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _BAD),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def export_pdf(
    output_path: Path,
    kpis,
    summary,
    analysis_sheets: Mapping[str, object],
    charts: Mapping[str, Path],
    company_name: str = "Reporte de Ventas",
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=company_name,
        author="Sales Report Automator",
    )
    styles = _styles()
    flow: list = []

    # --- Portada ----------------------------------------------------------
    flow.append(Paragraph(company_name, styles["title"]))
    flow.append(Paragraph("Reporte ejecutivo automatizado", styles["body"]))
    flow.append(Spacer(1, 6 * mm))

    flow.append(Paragraph("Indicadores generales", styles["h2"]))
    flow.append(_kpi_table(kpis))
    flow.append(Spacer(1, 6 * mm))

    flow.append(Paragraph("Calidad de los datos", styles["h2"]))
    flow.append(_quality_summary_table(summary))
    flow.append(Spacer(1, 3 * mm))

    reason_tbl = _quality_reasons_table(summary)
    if reason_tbl is not None:
        flow.append(Paragraph("Motivos de rechazo", styles["h2"]))
        flow.append(reason_tbl)
        flow.append(Spacer(1, 4 * mm))
    else:
        flow.append(
            Paragraph(
                "No se rechazó ninguna fila del archivo de origen.",
                styles["body"],
            )
        )

    # --- Páginas de tablas ------------------------------------------------
    analysis_order = [
        "Ventas por producto",
        "Ventas por categoría",
        "Ventas por región",
        "Ventas por vendedor",
        "Ventas por mes",
        "Top clientes",
    ]
    flow.append(PageBreak())
    flow.append(Paragraph("Detalle de ventas", styles["h2"]))
    for name in analysis_order:
        if name not in analysis_sheets:
            continue
        flow.append(Spacer(1, 2 * mm))
        flow.append(Paragraph(name, styles["h2"]))
        flow.append(_df_table(analysis_sheets[name]))
        flow.append(Spacer(1, 4 * mm))

    # --- Páginas de gráficas ---------------------------------------------
    charts_order = [
        ("Evolución mensual de ingresos", "chart_sales_over_time"),
        ("Top productos por ingresos", "chart_top_products"),
        ("Ingresos por región", "chart_region_sales"),
        ("Top vendedores", "chart_seller_performance"),
        ("Distribución por categoría", "chart_category_pie"),
    ]
    flow.append(PageBreak())
    flow.append(Paragraph("Gráficas", styles["h2"]))
    for title, key in charts_order:
        path = charts.get(key)
        if path is None or not Path(path).exists():
            continue
        flow.append(Spacer(1, 3 * mm))
        flow.append(Paragraph(title, styles["h2"]))
        try:
            img = Image(str(path))
            max_w = 18 * cm
            if img.imageWidth > max_w:
                ratio = max_w / img.imageWidth
                img.drawWidth = max_w
                img.drawHeight = img.imageHeight * ratio
            flow.append(img)
        except Exception:
            flow.append(Paragraph(f"[No se pudo incrustar {path}]", styles["small"]))

    doc.build(flow)
    return output_path


__all__ = ["export_pdf"]
