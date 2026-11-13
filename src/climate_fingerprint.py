"""Seasonality-aware monthly anomaly fingerprints for climate exploration."""
from __future__ import annotations

import pandas as pd


def build_climate_fingerprint(
    monthly: pd.DataFrame, variable: str, min_years: int = 3
) -> pd.DataFrame:
    """Return year-by-calendar-month standardized anomalies (z-scores).

    Each calendar month is compared only with the same calendar month in the
    selected record. This avoids treating normal seasonal cycles as anomalies.
    Months with fewer than min_years valid observations or zero variance
    are left blank rather than manufacturing a signal.
    """
    required = {"date", variable}
    if not required.issubset(monthly.columns):
        raise ValueError(f"Monthly data must contain date and {variable}")

    work = monthly[["date", variable]].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work[variable] = pd.to_numeric(work[variable], errors="coerce")
    work = work.dropna(subset=["date", variable]).copy()
    if work.empty or work["date"].dt.year.nunique() < min_years:
        return pd.DataFrame()

    work["year"] = work["date"].dt.year
    work["month"] = work["date"].dt.month
    grouped = work.groupby("month")[variable]
    counts = grouped.transform("count")
    means = grouped.transform("mean")
    deviations = grouped.transform("std").fillna(0.0)
    usable = (counts >= min_years) & (deviations > 0)
    work["anomaly_z"] = float("nan")
    work.loc[usable, "anomaly_z"] = (
        (work.loc[usable, variable] - means.loc[usable]) / deviations.loc[usable]
    )

    matrix = work.pivot_table(
        index="year", columns="month", values="anomaly_z", aggfunc="mean"
    )
    matrix = matrix.reindex(columns=range(1, 13))
    matrix.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    matrix.index.name = "Year"
    return matrix.sort_index()
