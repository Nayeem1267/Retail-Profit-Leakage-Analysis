"""Reproduce the retail profit leakage summaries from a CSV export.

Expected CSV columns:
OrderID, OrderDate, Region, Category, ProductName, NetSales, Profit, DiscountRate

The script reads the CSV only. It does not connect to or modify the database.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED = {
    "OrderID", "OrderDate", "Region", "Category", "ProductName",
    "NetSales", "Profit", "DiscountRate",
}


def summarize(frame: pd.DataFrame) -> dict[str, object]:
    df = frame.copy()
    df.columns = [str(column).strip() for column in df.columns]
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))

    for column in ("NetSales", "Profit", "DiscountRate"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce")
    df = df.dropna(subset=["OrderID", "NetSales", "Profit", "DiscountRate"])
    if df.empty:
        raise ValueError("No usable transaction rows were found in the CSV.")

    # Mirror the Tableau/SQL transaction grain: one row per OrderID.
    txn = (
        df.groupby("OrderID", dropna=False, as_index=False)
        .agg(
            OrderDate=("OrderDate", "min"),
            Region=("Region", "max"),
            Category=("Category", "max"),
            ProductName=("ProductName", "max"),
            NetSales=("NetSales", "sum"),
            Profit=("Profit", "sum"),
            DiscountRate=("DiscountRate", "mean"),
        )
    )

    def rollup(grouped: pd.core.groupby.DataFrameGroupBy) -> pd.DataFrame:
        result = grouped.agg(
            Transactions=("OrderID", "size"),
            NetSales=("NetSales", "sum"),
            Profit=("Profit", "sum"),
            AvgDiscountRate=("DiscountRate", "mean"),
            LossTransactions=("Profit", lambda values: int((values < 0).sum())),
        ).reset_index()
        result["ProfitMarginPct"] = np.where(
            result["NetSales"] != 0,
            100 * result["Profit"] / result["NetSales"],
            np.nan,
        )
        result["AvgDiscountPct"] = 100 * result["AvgDiscountRate"]
        return result

    category = rollup(txn.groupby("Category", dropna=False))
    category = category.sort_values("Category", kind="stable")

    # Match SQL NTILE(4): first remainder buckets receive one extra row.
    ordered = txn.sort_values(["DiscountRate", "OrderID"], kind="stable").reset_index(drop=True)
    n = len(ordered)
    if n < 4:
        raise ValueError("At least four transactions are needed for discount quartiles.")
    quotient, remainder = divmod(n, 4)
    positions = np.arange(n)
    first_groups_size = (quotient + 1) * remainder
    quartile = np.where(
        positions < first_groups_size,
        positions // (quotient + 1) + 1,
        remainder + (positions - first_groups_size) // quotient + 1,
    )
    ordered["DiscountQuartile"] = quartile
    discount = rollup(ordered.groupby("DiscountQuartile", dropna=False))
    discount["DiscountQuartile"] = discount["DiscountQuartile"].map(lambda value: f"Q{int(value)}")
    discount = discount.sort_values("DiscountQuartile", kind="stable")

    product = rollup(txn.groupby("ProductName", dropna=False))
    product = product[product["LossTransactions"] > 0].sort_values(
        ["LossTransactions", "Profit"], ascending=[False, True], kind="stable"
    )

    dated = txn.dropna(subset=["OrderDate"]).copy()
    dated["SalesMonth"] = dated["OrderDate"].dt.to_period("M").astype(str)
    monthly = rollup(dated.groupby("SalesMonth", dropna=False)).sort_values("SalesMonth")

    total_sales = float(txn["NetSales"].sum())
    total_profit = float(txn["Profit"].sum())
    overall = {
        "transactions": int(len(txn)),
        "net_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin_pct": round(100 * total_profit / total_sales, 2) if total_sales else None,
        "average_discount_pct": round(100 * float(txn["DiscountRate"].mean()), 2),
        "loss_transactions": int((txn["Profit"] < 0).sum()),
        "data_start": str(dated["OrderDate"].min().date()) if not dated.empty else None,
        "data_end": str(dated["OrderDate"].max().date()) if not dated.empty else None,
    }
    return {
        "overall": overall,
        "category": category,
        "discount_quartiles": discount,
        "loss_products": product,
        "monthly": monthly,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize retail profit leakage from a CSV export.")
    parser.add_argument("csv_path", type=Path, help="CSV export of the retail_sales table")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for summary files (default: beside the CSV)")
    args = parser.parse_args()
    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")

    output_dir = args.output_dir or args.csv_path.parent / "retail_analysis_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = summarize(pd.read_csv(args.csv_path))
    overall = result.pop("overall")
    for name, table in result.items():
        table.to_csv(output_dir / f"{name}.csv", index=False, float_format="%.2f")
    (output_dir / "overall_kpis.json").write_text(
        json.dumps(overall, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(overall, indent=2, ensure_ascii=False))
    print(f"\nWrote summaries to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
