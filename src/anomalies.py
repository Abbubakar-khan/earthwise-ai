"""Seasonal anomaly calculations for monthly climate observations.

The baseline is calculated from the selected dataset itself, separately for each
calendar month. These are within-period departures, not standard 30-year normals.
"""
from __future__ import annotations
import pandas as pd

def seasonal_anomalies(monthly: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Return monthly departures from selected-period calendar-month means."""
    columns = ["date", "year", "month", variable, "climatology", "anomaly", "standardized_anomaly"]
    if not {"date", variable}.issubset(monthly.columns):
        return pd.DataFrame(columns=columns)
    frame = monthly[["date", variable]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame[variable] = pd.to_numeric(frame[variable], errors="coerce")
    frame = frame.dropna(subset=["date", variable]).sort_values("date")
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame["year"] = frame["date"].dt.year
    frame["month"] = frame["date"].dt.month
    grouped = frame.groupby("month")[variable]
    frame["climatology"] = frame["month"].map(grouped.mean())
    month_std = grouped.std(ddof=1)
    frame["anomaly"] = frame[variable] - frame["climatology"]
    frame["standardized_anomaly"] = frame["anomaly"] / frame["month"].map(month_std).replace(0, float("nan"))
    return frame.reset_index(drop=True)
