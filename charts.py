"""
charts.py
=========
Genera las gráficas del reporte en archivos PNG usando matplotlib.

Funciones devuelven la ruta del archivo creado para incrustarla en el
Excel y/o en el PDF.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin GUI, seguro para CI
import matplotlib.pyplot as plt
import pandas as pd

# Estilo consistente
plt.rcParams.update(
    {
        "figure.figsize": (10, 5.5),
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    }
)

PALETTE = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9", "#ec4899", "#14b8a6"]


def _save(fig: plt.Figure, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_sales_over_time(df: pd.DataFrame, out_dir: Path) -> Path | None:
    monthly = (
        df.assign(mes=df["date"].dt.to_period("M").astype(str))
        .groupby("mes", as_index=False)
        .agg(ingresos=("revenue", "sum"))
        .sort_values("mes")
    )
    if monthly.empty:
        return None
    fig, ax = plt.subplots()
    ax.plot(monthly["mes"], monthly["ingresos"], marker="o", color=PALETTE[0], linewidth=2)
    ax.fill_between(monthly["mes"], monthly["ingresos"], color=PALETTE[0], alpha=0.12)
    ax.set_title("Evolución mensual de ingresos")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Ingresos (USD)")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    return _save(fig, out_dir, "01_ventas_mensuales")


def chart_top_products(df: pd.DataFrame, out_dir: Path, top_n: int = 10) -> Path | None:
    top = (
        df.groupby("product", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )
    if top.empty:
        return None
    fig, ax = plt.subplots()
    bars = ax.barh(
        top["product"][::-1],
        top["revenue"][::-1],
        color=PALETTE[1],
    )
    ax.set_title(f"Top {len(top)} productos por ingresos")
    ax.set_xlabel("Ingresos (USD)")
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width,
            bar.get_y() + bar.get_height() / 2,
            f"${width:,.0f}",
            va="center",
            ha="left",
            fontsize=9,
        )
    return _save(fig, out_dir, "02_top_productos")


def chart_category_pie(df: pd.DataFrame, out_dir: Path) -> Path | None:
    by_cat = df.groupby("category", as_index=False)["revenue"].sum()
    if by_cat.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        by_cat["revenue"],
        labels=by_cat["category"],
        autopct="%1.1f%%",
        startangle=90,
        colors=PALETTE * (len(by_cat) // len(PALETTE) + 1),
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    ax.set_title("Distribución de ingresos por categoría")
    return _save(fig, out_dir, "03_categorias")


def chart_region_sales(df: pd.DataFrame, out_dir: Path) -> Path | None:
    by_region = (
        df.groupby("region", as_index=False)["revenue"].sum().sort_values("revenue")
    )
    if by_region.empty:
        return None
    fig, ax = plt.subplots()
    bars = ax.bar(
        by_region["region"],
        by_region["revenue"],
        color=PALETTE[3],
    )
    ax.set_title("Ingresos por región")
    ax.set_xlabel("Región")
    ax.set_ylabel("Ingresos (USD)")
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"${bar.get_height():,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    return _save(fig, out_dir, "04_regiones")


def chart_seller_performance(df: pd.DataFrame, out_dir: Path, top_n: int = 10) -> Path | None:
    top = (
        df.groupby("seller", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )
    if top.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, max(4, len(top) * 0.5)))
    bars = ax.barh(
        top["seller"][::-1],
        top["revenue"][::-1],
        color=PALETTE[4],
    )
    ax.set_title(f"Top {len(top)} vendedores por ingresos")
    ax.set_xlabel("Ingresos (USD)")
    for bar in bars:
        ax.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f"${bar.get_width():,.0f}",
            va="center",
            ha="left",
            fontsize=9,
        )
    return _save(fig, out_dir, "05_vendedores")


__all__ = [
    "chart_sales_over_time",
    "chart_top_products",
    "chart_category_pie",
    "chart_region_sales",
    "chart_seller_performance",
]
