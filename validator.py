"""
validator.py
============
Carga y valida el CSV de ventas. Detecta registros incorrectos y devuelve:
- DataFrame con las filas válidas y normalizadas
- DataFrame con las filas descartadas y su motivo de rechazo
- Resumen de validación (totales, motivos, ejemplos)

Reglas aplicadas
----------------
1. order_id no vacío y único dentro del archivo.
2. date en formato ISO (YYYY-MM-DD) y convertible a fecha real.
3. product, region, seller, customer_email no vacíos.
4. quantity entero > 0.
5. unit_price numérico > 0.
6. customer_email con formato válido (regex simple).

Las filas que rompen alguna regla se devuelven en ``rejected`` con la
columna ``reason`` describiendo el motivo (puede combinar varios).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS = [
    "order_id",
    "date",
    "product",
    "category",
    "quantity",
    "unit_price",
    "region",
    "seller",
    "customer_email",
]

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y")


@dataclass
class ValidationSummary:
    total_rows: int = 0
    accepted_rows: int = 0
    rejected_rows: int = 0
    reasons: dict[str, int] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        data = {
            "Métrica": [
                "Filas leídas",
                "Filas aceptadas",
                "Filas rechazadas",
            ],
            "Valor": [
                self.total_rows,
                self.accepted_rows,
                self.rejected_rows,
            ],
        }
        df = pd.DataFrame(data)
        if self.reasons:
            reasons_df = (
                pd.DataFrame(
                    [{"Motivo": k, "Conteo": v} for k, v in self.reasons.items()]
                )
                .sort_values("Conteo", ascending=False)
                .reset_index(drop=True)
            )
            df = pd.concat(
                [df, pd.DataFrame([["---"] * 2], columns=df.columns), reasons_df],
                ignore_index=True,
            )
        return df


def _try_parse_date(value: object) -> str | None:
    """Devuelve la fecha en formato ISO si se puede parsear, si no ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return pd.to_datetime(text, format=fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    # Última instancia: dejar que pandas intente
    try:
        return pd.to_datetime(text, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return None


def _coerce_int(value: object) -> tuple[int | None, str | None]:
    if pd.isna(value) or str(value).strip() == "":
        return None, "quantity vacía"
    try:
        number = int(float(value))
        return number, None
    except (ValueError, TypeError):
        return None, f"quantity no numérica ({value!r})"


def _coerce_float(value: object) -> tuple[float | None, str | None]:
    if pd.isna(value) or str(value).strip() == "":
        return None, "unit_price vacía"
    try:
        number = float(value)
        return number, None
    except (ValueError, TypeError):
        return None, f"unit_price no numérico ({value!r})"


def load_and_validate(csv_path: str) -> tuple[pd.DataFrame, pd.DataFrame, ValidationSummary]:
    """Carga el CSV, valida cada fila y devuelve válidos, rechazados y resumen."""
    raw = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    summary = ValidationSummary(total_rows=len(raw))

    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(
            f"El CSV no contiene las columnas requeridas: {', '.join(missing)}"
        )

    accepted_records: list[dict] = []
    rejected_records: list[dict] = []

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()

    for idx, row in raw.iterrows():
        reasons: list[str] = []

        # order_id
        order_id = str(row["order_id"]).strip() if not pd.isna(row["order_id"]) else ""
        if not order_id:
            reasons.append("order_id vacío")
        elif order_id in seen_ids:
            reasons.append(f"order_id duplicado ({order_id})")
            duplicate_ids.add(order_id)
        else:
            seen_ids.add(order_id)

        # date
        date_iso = _try_parse_date(row["date"])
        if date_iso is None:
            reasons.append(f"fecha inválida ({row['date']!r})")

        # product
        product = str(row["product"]).strip() if not pd.isna(row["product"]) else ""
        if not product or product.lower() == "nan":
            reasons.append("product vacío")

        # category (opcional pero se conserva si está)
        category = (
            str(row["category"]).strip()
            if not pd.isna(row["category"])
            else "Sin categoría"
        )

        # region
        region = str(row["region"]).strip() if not pd.isna(row["region"]) else ""
        if not region:
            reasons.append("region vacía")

        # seller
        seller = str(row["seller"]).strip() if not pd.isna(row["seller"]) else ""
        if not seller:
            reasons.append("seller vacío")

        # email
        email = (
            str(row["customer_email"]).strip()
            if not pd.isna(row["customer_email"])
            else ""
        )
        if not email:
            reasons.append("customer_email vacío")
        elif not _EMAIL_RE.match(email):
            reasons.append(f"email inválido ({email})")

        # quantity
        quantity, qty_err = _coerce_int(row["quantity"])
        if qty_err:
            reasons.append(qty_err)
        elif quantity is not None and quantity <= 0:
            reasons.append(f"quantity <= 0 ({quantity})")

        # unit_price
        price, price_err = _coerce_float(row["unit_price"])
        if price_err:
            reasons.append(price_err)
        elif price is not None and price <= 0:
            reasons.append(f"unit_price <= 0 ({price})")

        if reasons:
            rejected_records.append(
                {
                    "row_number": int(idx) + 2,  # +2: header + 1-indexed
                    "order_id": order_id or "",
                    "date": str(row["date"]) if not pd.isna(row["date"]) else "",
                    "product": product or "",
                    "quantity": str(row["quantity"]) if not pd.isna(row["quantity"]) else "",
                    "unit_price": str(row["unit_price"]) if not pd.isna(row["unit_price"]) else "",
                    "customer_email": email or "",
                    "motivos": "; ".join(reasons),
                }
            )
            for r in reasons:
                # Contamos el motivo principal (antes del paréntesis)
                main = r.split(" (")[0]
                summary.reasons[main] = summary.reasons.get(main, 0) + 1
            continue

        accepted_records.append(
            {
                "order_id": order_id,
                "date": date_iso,
                "product": product,
                "category": category or "Sin categoría",
                "quantity": quantity,
                "unit_price": float(price),
                "region": region,
                "seller": seller,
                "customer_email": email,
            }
        )

    accepted = pd.DataFrame(accepted_records)
    if not accepted.empty:
        accepted["date"] = pd.to_datetime(accepted["date"])
        accepted["revenue"] = accepted["quantity"] * accepted["unit_price"]

    rejected = pd.DataFrame(rejected_records)

    summary.accepted_rows = len(accepted)
    summary.rejected_rows = len(rejected)
    return accepted, rejected, summary


__all__ = ["load_and_validate", "ValidationSummary", "REQUIRED_COLUMNS"]
