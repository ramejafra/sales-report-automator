"""
sales_report_automator.py
=========================
CLI principal: recibe un CSV de ventas, lo limpia, calcula indicadores,
genera gráficas y exporta un Excel y un PDF con los resultados.

Uso básico
----------
    python sales_report_automator.py --input data/sample_sales_data.csv \\
        --output output

Salidas generadas (en ``--output``)
------------------------------------
- reporte_ventas.xlsx
- reporte_ventas.pdf
- charts/*.png  (gráficas individuales)
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pandas as pd

from analytics import (
    data_quality_report,
    kpi_overview,
    sales_by_category,
    sales_by_product,
    sales_by_region,
    sales_by_seller,
    sales_over_time,
    top_customers,
)
from charts import (
    chart_category_pie,
    chart_region_sales,
    chart_sales_over_time,
    chart_seller_performance,
    chart_top_products,
)
from excel_exporter import export_excel
from pdf_exporter import export_pdf
from validator import REQUIRED_COLUMNS, load_and_validate


BANNER = "=" * 70


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automatizador de Reportes de Ventas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """\
            Ejemplos:
              python sales_report_automator.py -i data/sample_sales_data.csv -o output
              python sales_report_automator.py -i mis_ventas.csv -o ./reportes --no-pdf
            """
        ),
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Ruta al CSV de ventas (debe incluir las columnas requeridas).",
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Carpeta donde se guardarán los reportes (por defecto: ./output).",
    )
    parser.add_argument(
        "--company",
        default="Reporte de Ventas",
        help="Título de la empresa o reporte que aparece en portada.",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Si está presente, no genera el archivo PDF.",
    )
    parser.add_argument(
        "--top-customers",
        type=int,
        default=10,
        help="Cantidad de clientes principales a mostrar (por defecto: 10).",
    )
    parser.add_argument(
        "--top-products",
        type=int,
        default=10,
        help="Cantidad de productos principales a graficar (por defecto: 10).",
    )
    return parser.parse_args(argv)


def _print_summary(summary, kpis: pd.DataFrame, rejected: pd.DataFrame) -> None:
    print(BANNER)
    print(f"Filas leídas:      {summary.total_rows}")
    print(f"Filas aceptadas:   {summary.accepted_rows}")
    print(f"Filas rechazadas:  {summary.rejected_rows}")
    if summary.total_rows:
        pct = summary.accepted_rows / summary.total_rows * 100
        print(f"% Aceptadas:       {pct:.2f}%")
    print(BANNER)

    if summary.reasons:
        print("Motivos de rechazo:")
        for motivo, conteo in sorted(
            summary.reasons.items(), key=lambda kv: kv[1], reverse=True
        ):
            print(f"  - {motivo}: {conteo}")
        print(BANNER)

    if not rejected.empty:
        print("Ejemplos de filas descartadas:")
        cols = ["row_number", "order_id", "product", "motivos"]
        print(rejected[cols].head(5).to_string(index=False))
        print(BANNER)

    print("KPIs generales:")
    print(kpis.to_string(index=False))
    print(BANNER)


def _build_charts(df: pd.DataFrame, charts_dir: Path, top_n_products: int) -> dict[str, Path]:
    charts: dict[str, Path] = {
        "chart_sales_over_time": chart_sales_over_time(df, charts_dir),
        "chart_top_products": chart_top_products(df, charts_dir, top_n=top_n_products),
        "chart_category_pie": chart_category_pie(df, charts_dir),
        "chart_region_sales": chart_region_sales(df, charts_dir),
        "chart_seller_performance": chart_seller_performance(df, charts_dir),
    }
    return charts


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_dir = Path(args.output)
    if not input_path.exists():
        print(f"[ERROR] No existe el archivo de entrada: {input_path}")
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = output_dir / "charts"

    print(f"[INFO] Cargando y validando: {input_path}")
    try:
        valid, rejected, summary = load_and_validate(str(input_path))
    except ValueError as err:
        print(f"[ERROR] {err}")
        print(f"        Columnas requeridas: {', '.join(REQUIRED_COLUMNS)}")
        return 2
    except Exception as err:  # pragma: no cover
        print(f"[ERROR] Fallo al leer el CSV: {err}")
        return 2

    if valid.empty:
        print("[ERROR] Ninguna fila válida en el CSV. Revisa los datos de entrada.")
        return 3

    kpis = kpi_overview(valid)
    _print_summary(summary, kpis, rejected)

    print("[INFO] Calculando indicadores...")
    analysis_sheets: dict[str, pd.DataFrame] = {
        "Ventas por producto": sales_by_product(valid),
        "Ventas por categoría": sales_by_category(valid),
        "Ventas por región": sales_by_region(valid),
        "Ventas por vendedor": sales_by_seller(valid),
        "Ventas por mes": sales_over_time(valid),
        "Top clientes": top_customers(valid, n=args.top_customers),
    }
    print("[INFO] Generando gráficas...")
    charts = _build_charts(valid, charts_dir, args.top_products)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = output_dir / f"reporte_ventas_{timestamp}.xlsx"
    pdf_path = output_dir / f"reporte_ventas_{timestamp}.pdf"

    # También generamos una copia "latest" sin timestamp para conveniencia.
    excel_latest = output_dir / "reporte_ventas.xlsx"
    pdf_latest = output_dir / "reporte_ventas.pdf"

    print(f"[INFO] Escribiendo Excel en {excel_path} ...")
    export_excel(
        output_path=excel_path,
        kpis=kpis,
        summary=summary,
        rejected=rejected,
        analysis_sheets=analysis_sheets,
        charts=charts,
    )

    if not args.no_pdf:
        print(f"[INFO] Escribiendo PDF en {pdf_path} ...")
        export_pdf(
            output_path=pdf_path,
            kpis=kpis,
            summary=summary,
            analysis_sheets=analysis_sheets,
            charts=charts,
            company_name=args.company,
        )

    # Copia "latest"
    try:
        excel_latest.write_bytes(excel_path.read_bytes())
        if not args.no_pdf:
            pdf_latest.write_bytes(pdf_path.read_bytes())
    except OSError as exc:
        print(f"[AVISO] No se pudo crear el enlace 'latest': {exc}")

    print(BANNER)
    print(f"[OK] Reporte Excel: {excel_path}")
    if not args.no_pdf:
        print(f"[OK] Reporte PDF:   {pdf_path}")
    print(f"[OK] Gráficas:      {charts_dir}/")
    print(BANNER)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
