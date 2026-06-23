from __future__ import annotations
import numpy as np
import pandas as pd

GROUP_COLS = ["Property Name", "State", "City", "Utility", "Bill Month"]


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in GROUP_COLS if c in df.columns]
    agg = df.groupby(cols, dropna=False).agg(
        Provider=("Provider", "first") if "Provider" in df.columns else ("Utility", "first"),
        Total_Cost=("$ Amount", "sum"),
        Total_Usage=("Usage", "sum"),
        Treatments=("# Treatments", "max"),
        Days_Billed=("Number Days Billed", "sum"),
        Last_Bill_Date=("Billing Date", "max"),
    ).reset_index()
    agg["Cost_per_Treatment"] = agg["Total_Cost"] / agg["Treatments"].replace({0: np.nan})
    agg["Usage_per_Treatment"] = agg["Total_Usage"] / agg["Treatments"].replace({0: np.nan})
    agg = agg.sort_values(["Property Name", "Utility", "Bill Month"])
    for metric in ["Total_Cost", "Total_Usage", "Treatments", "Cost_per_Treatment", "Usage_per_Treatment"]:
        agg[f"{metric}_Prev"] = agg.groupby(["Property Name", "Utility"])[metric].shift(1)
        agg[f"{metric}_Change"] = (agg[metric] - agg[f"{metric}_Prev"]) / agg[f"{metric}_Prev"].replace({0: np.nan})
    return agg


def filter_df(df: pd.DataFrame, states=None, properties=None, utilities=None, date_range=None) -> pd.DataFrame:
    out = df.copy()
    if states and "All" not in states and "State" in out.columns:
        out = out[out["State"].isin(states)]
    if properties and "All" not in properties and "Property Name" in out.columns:
        out = out[out["Property Name"].isin(properties)]
    if utilities and "All" not in utilities and "Utility" in out.columns:
        out = out[out["Utility"].isin(utilities)]
    if date_range and "Bill Month" in out.columns and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        out = out[(out["Bill Month"] >= start) & (out["Bill Month"] <= end)]
    return out


def latest_month(df: pd.DataFrame):
    if df.empty or "Bill Month" not in df.columns:
        return None
    return df["Bill Month"].max()


def pct_fmt(x):
    if pd.isna(x): return "—"
    return f"{x:+.1%}"


def money_fmt(x):
    if pd.isna(x): return "—"
    return f"${x:,.0f}"


def num_fmt(x):
    if pd.isna(x): return "—"
    return f"{x:,.0f}"
