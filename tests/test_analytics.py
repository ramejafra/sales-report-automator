"""Tests unitarios del módulo analytics.py."""

from __future__ import annotations

import unittest

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


def sample_df() -> pd.DataFrame:
    """DataFrame válido tal como lo entrega el validador (con `revenue` y `date` como datetime)."""
    return pd.DataFrame(
        {
            "order_id": ["A-1", "A-2", "A-3", "A-2", "A-1"],
            "date": pd.to_datetime(
                [
                    "2024-01-05",
                    "2024-02-10",
                    "2024-02-15",
                    "2024-03-01",
                    "2024-03-20",
                ]
            ),
            "product": ["Producto A", "Producto B", "Producto A", "Producto B", "Producto C"],
            "category": ["Cat1", "Cat1", "Cat1", "Cat1", "Cat2"],
            "quantity": [2, 5, 1, 3, 4],
            "unit_price": [10.0, 20.0, 10.0, 20.0, 30.0],
            "region": ["Norte", "Centro", "Norte", "Sur", "Sur"],
            "seller": ["S1", "S2", "S1", "S2", "S1"],
            "customer_email": [
                "a@x.com",
                "b@x.com",
                "c@x.com",
                "b@x.com",
                "a@x.com",
            ],
            "revenue": [20.0, 100.0, 10.0, 60.0, 120.0],
        }
    )


class KpiOverviewTest(unittest.TestCase):
    def test_valores_calculados(self):
        kpi = kpi_overview(sample_df())
        valores = dict(zip(kpi["Indicador"], kpi["Valor"]))

        self.assertEqual(valores["Ingresos totales"], "$310.00")
        self.assertEqual(valores["Órdenes únicas"], "3")  # A-1, A-2, A-3
        self.assertEqual(valores["Unidades vendidas"], "15")
        self.assertEqual(valores["Ticket medio"], "$62.00")
        self.assertEqual(valores["Período"], "2024-01-05 a 2024-03-20")

    def test_dataframe_vacio(self):
        empty = pd.DataFrame(
            {
                "revenue": [],
                "order_id": [],
                "quantity": [],
                "unit_price": [],
                "date": [],
            }
        )
        kpi = kpi_overview(empty)
        valores = dict(zip(kpi["Indicador"], kpi["Valor"]))
        self.assertEqual(valores["Ingresos totales"], 0)
        self.assertEqual(valores["Período"], "—")


class GroupByTablesTest(unittest.TestCase):
    def test_sales_by_product_ordenado_por_ingresos(self):
        out = sales_by_product(sample_df())
        self.assertEqual(out["product"].iloc[0], "Producto B")  # B: 100+60=160 > C:120 > A:30
        self.assertEqual(out["ingresos"].iloc[0], 160.0)

    def test_sales_by_category_participacion_suma_100(self):
        out = sales_by_category(sample_df())
        self.assertAlmostEqual(out["% participación"].sum(), 100.0, places=6)

    def test_sales_by_region(self):
        out = sales_by_region(sample_df())
        self.assertEqual(set(out["region"]), {"Norte", "Centro", "Sur"})
        self.assertAlmostEqual(out["ingresos"].sum(), 310.0)

    def test_sales_by_seller_ticket_medio(self):
        out = sales_by_seller(sample_df())
        s1 = out[out["seller"] == "S1"].iloc[0]
        # S1: revenue 20 + 10 + 120 = 150 en 3 filas → ticket 50
        self.assertAlmostEqual(s1["ticket_medio"], 50.0)

    def test_sales_over_time_mensual(self):
        out = sales_over_time(sample_df())
        self.assertEqual(len(out), 3)  # 2024-01, 2024-02, 2024-03
        self.assertEqual(out["mes"].iloc[0], "2024-01")

    def test_top_customers_limite(self):
        out = top_customers(sample_df(), n=2)
        self.assertLessEqual(len(out), 2)
        self.assertEqual(out["customer_email"].iloc[0], "b@x.com")  # 160 > 140


class DataQualityReportTest(unittest.TestCase):
    def test_rejected_vacio(self):
        out = data_quality_report(pd.DataFrame({"motivos": [], "row_number": [], "order_id": []}))
        self.assertIn("Sin rechazos", out["Motivo"].iloc[0])

    def test_resumen_de_motivos(self):
        rejected = pd.DataFrame(
            {
                "row_number": [2, 5, 6],
                "order_id": ["A-1", "A-2", "A-3"],
                "motivos": ["quantity <= 0; fecha inválida", "quantity <= 0", "email inválido"],
            }
        )
        out = data_quality_report(rejected)
        self.assertEqual(out["Motivo"].iloc[0], "quantity <= 0")  # 2 ocurrencias (motivo principal)
        self.assertIn("A-1", out["Ejemplos"].iloc[0])


if __name__ == "__main__":
    unittest.main()
