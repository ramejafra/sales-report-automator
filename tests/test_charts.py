"""Tests unitarios de charts.py: cada gráfica genera un PNG válido."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import matplotlib

from charts import (
    chart_category_pie,
    chart_region_sales,
    chart_sales_over_time,
    chart_seller_performance,
    chart_top_products,
)

# Reusar el fixture de test_analytics
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).parent.resolve()))
from test_analytics import sample_df  # noqa: E402


class ChartsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.out_dir = Path(tempfile.mkdtemp())
        self.df = sample_df()

    def _assert_png(self, path: Path):
        self.assertTrue(path.exists(), f"no se creó {path.name}")
        content = path.read_bytes()
        self.assertGreater(len(content), 500, f"{path.name} vacío")
        self.assertTrue(content.startswith(b"\x89PNG"), f"{path.name} no es un PNG válido")

    def test_ventas_mensuales(self):
        self._assert_png(chart_sales_over_time(self.df, self.out_dir))

    def test_top_productos(self):
        self._assert_png(chart_top_products(self.df, self.out_dir, top_n=3))

    def test_pie_categorias(self):
        self._assert_png(chart_category_pie(self.df, self.out_dir))

    def test_regiones(self):
        self._assert_png(chart_region_sales(self.df, self.out_dir))

    def test_vendedores(self):
        self._assert_png(chart_seller_performance(self.df, self.out_dir))


if __name__ == "__main__":
    unittest.main()
