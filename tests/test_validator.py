"""Tests unitarios del validador de ventas."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validator import load_and_validate


CSV_CONTENT = """order_id,date,product,category,quantity,unit_price,region,seller,customer_email
A-1,2024-01-05,Producto A,Cat1,2,10.00,Norte,Seller 1,cliente1@example.com
A-2,2024-01-06,Producto B,Cat1,5,20.50,Centro,Seller 2,cliente2@example.com
A-3,malafecha,Producto A,Cat1,1,10.00,Norte,Seller 1,cliente3@example.com
A-4,2024-01-07,Producto C,Cat2,0,15.00,Sur,Seller 3,cliente4@example.com
A-5,2024-01-08,Producto D,Cat2,3,-5.00,Sur,Seller 3,cliente5@example.com
A-6,2024-01-09,Producto E,Cat1,2,15.00,Norte,Seller 1,correo_malo
A-6,2024-01-10,Producto F,Cat1,1,15.00,Centro,Seller 2,cliente7@example.com
A-8,2024-01-11,,Cat1,2,15.00,Norte,Seller 1,cliente8@example.com
A-9,2024-01-12,Producto A,Cat1,dos,15.00,Norte,Seller 1,cliente9@example.com
A-10,2024-01-13,Producto A,Cat1,1,abc,Norte,Seller 1,cliente10@example.com
"""


def _make_temp_csv(content: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=".csv", text=True)
    import os

    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return Path(name)


class ValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.path = _make_temp_csv(CSV_CONTENT)

    def tearDown(self) -> None:
        self.path.unlink(missing_ok=True)

    def test_separa_validas_y_rechazadas(self) -> None:
        valid, rejected, summary = load_and_validate(str(self.path))
        # Solo A-1 y A-2 son completamente correctas.
        self.assertEqual(summary.total_rows, 10)
        self.assertEqual(summary.accepted_rows, 2)
        self.assertEqual(summary.rejected_rows, 8)
        self.assertEqual(set(valid["order_id"]), {"A-1", "A-2"})
        self.assertIn("fecha inválida", "; ".join(rejected["motivos"]))
        self.assertIn("quantity <= 0", "; ".join(rejected["motivos"]))
        self.assertIn("unit_price <= 0", "; ".join(rejected["motivos"]))
        self.assertIn("email inválido", "; ".join(rejected["motivos"]))
        self.assertIn("order_id duplicado", "; ".join(rejected["motivos"]))

    def test_kpis_con_dataset_vacio(self) -> None:
        empty = self.path.with_name("empty.csv")
        empty.write_text(
            "order_id,date,product,category,quantity,unit_price,region,seller,customer_email\n",
            encoding="utf-8",
        )
        try:
            valid, rejected, summary = load_and_validate(str(empty))
        finally:
            empty.unlink(missing_ok=True)
        self.assertEqual(summary.total_rows, 0)
        self.assertTrue(valid.empty)
        self.assertTrue(rejected.empty)


if __name__ == "__main__":
    unittest.main()
