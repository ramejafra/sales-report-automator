"""
analytics.py
============
Calcula los indicadores clave a partir del DataFrame validado de ventas.

Todos los métodos devuelven ``pandas.DataFrame`` listos para escribir en
una hoja Excel o para alimentar las gráficas.
"""

from __future__ import annotations

import pandas as pd


def kpi_overview(df: pd.DataFrame) -> pd.DataFrame:
    """KPIs de alto nivel: ingresos, órdenes, unidades, ticket medio, período."""
    if df.empty:
        return pd.DataFrame(
            {
                "Indicador": [
                    "Ingresos totales",
                    "Órdenes",
                    "Unidades vendidas",
                    "Ticket medio",
                    "Precio unitario medio",
                    "Período",
                ],
                "Valor": [0, 0, 0, 0, 0, "—"],
            }
        )

    ingresos = float(df["revenue"].sum())
    ordenes = int(df["order_id"].nunique())
    unidades = int(df["quantity"].sum())
    ticket = float(df["revenue"].mean())
    pu_medio = float(df["unit_price"].mean())
    fecha_min = df["date"].min().strftime("%Y-%m-%d")
    fecha_max = df["date"].max().strftime("%Y-%m-%d")
    periodo = f"{fecha_min} a {fecha_max}"

    return pd.DataFrame(
        {
            "Indicador": [
                "Ingresos totales",
                "Órdenes únicas",
                "Unidades vendidas",
                "Ticket medio",
                "Precio unitario medio",
                "Período",
            ],
            "Valor": [
                f"${ingresos:,.2f}",
                f"{ordenes:,}",
                f"{unidades:,}",
                f"${ticket:,.2f}",
                f"${pu_medio:,.2f}",
                periodo,
            ],
        }
    )


def sales_by_product(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("product", as_index=False)
        .agg(
            unidades=("quantity", "sum"),
            ingresos=("revenue", "sum"),
            órdenes=("order_id", "nunique"),
            precio_promedio=("unit_price", "mean"),
        )
        .sort_values("ingresos", ascending=False)
        .reset_index(drop=True)
    )
    out["precio_promedio"] = out["precio_promedio"].round(2)
    out["ingresos"] = out["ingresos"].round(2)
    return out


def sales_by_category(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("category", as_index=False)
        .agg(
            unidades=("quantity", "sum"),
            ingresos=("revenue", "sum"),
            órdenes=("order_id", "nunique"),
        )
        .sort_values("ingresos", ascending=False)
        .reset_index(drop=True)
    )
    out["ingresos"] = out["ingresos"].round(2)
    out["% participación"] = (out["ingresos"] / out["ingresos"].sum() * 100).round(2)
    return out


def sales_by_region(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("region", as_index=False)
        .agg(
            unidades=("quantity", "sum"),
            ingresos=("revenue", "sum"),
            órdenes=("order_id", "nunique"),
        )
        .sort_values("ingresos", ascending=False)
        .reset_index(drop=True)
    )
    out["ingresos"] = out["ingresos"].round(2)
    out["% participación"] = (out["ingresos"] / out["ingresos"].sum() * 100).round(2)
    return out


def sales_by_seller(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("seller", as_index=False)
        .agg(
            unidades=("quantity", "sum"),
            ingresos=("revenue", "sum"),
            órdenes=("order_id", "nunique"),
            ticket_medio=("revenue", "mean"),
        )
        .sort_values("ingresos", ascending=False)
        .reset_index(drop=True)
    )
    out["ingresos"] = out["ingresos"].round(2)
    out["ticket_medio"] = out["ticket_medio"].round(2)
    return out


def sales_over_time(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.assign(mes=df["date"].dt.to_period("M").astype(str))
        .groupby("mes", as_index=False)
        .agg(
            ingresos=("revenue", "sum"),
            unidades=("quantity", "sum"),
            órdenes=("order_id", "nunique"),
        )
        .sort_values("mes")
        .reset_index(drop=True)
    )
    monthly["ingresos"] = monthly["ingresos"].round(2)
    return monthly


def top_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    out = (
        df.groupby("customer_email", as_index=False)
        .agg(
            órdenes=("order_id", "nunique"),
            unidades=("quantity", "sum"),
            ingresos=("revenue", "sum"),
            último_pedido=("date", "max"),
        )
        .sort_values("ingresos", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
    out["ingresos"] = out["ingresos"].round(2)
    out["último_pedido"] = pd.to_datetime(out["último_pedido"]).dt.strftime("%Y-%m-%d")
    return out


def data_quality_report(rejected: pd.DataFrame) -> pd.DataFrame:
    """Resumen de motivos de rechazo y ejemplos."""
    if rejected.empty:
        return pd.DataFrame(
            {
                "Motivo": ["Sin rechazos"],
                "Conteo": [0],
                "Ejemplos": ["—"],
            }
        )

    out = (
        rejected.assign(motivo_principal=rejected["motivos"].str.split(";").str[0].str.strip())
        .groupby("motivo_principal", as_index=False)
        .agg(
            conteo=("row_number", "count"),
            ejemplos=("order_id", lambda s: ", ".join(s.head(3).astype(str))),
        )
        .sort_values("conteo", ascending=False)
        .rename(columns={"motivo_principal": "Motivo", "conteo": "Conteo", "ejemplos": "Ejemplos"})
        .reset_index(drop=True)
    )
    return out


__all__ = [
    "kpi_overview",
    "sales_by_product",
    "sales_by_category",
    "sales_by_region",
    "sales_by_seller",
    "sales_over_time",
    "top_customers",
    "data_quality_report",
]
