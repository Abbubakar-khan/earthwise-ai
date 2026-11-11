"""Transparent trend metrics: Kendall tau significance + Sen's median slope."""
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, theilslopes

def analyze_trend(monthly: pd.DataFrame, variable: str) -> dict:
    work = monthly[["date", variable]].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work[variable] = pd.to_numeric(work[variable], errors="coerce")
    work = work.dropna().sort_values("date")
    if len(work) < 24:
        return {"status": "insufficient", "n": int(len(work)),
                "message": "At least 24 valid monthly observations are required for this MVP."}
    # x is elapsed years, so Sen slope is expressed in variable-units/year.
    x = (work["date"] - work["date"].iloc[0]).dt.days.to_numpy(dtype=float) / 365.2425
    y = work[variable].to_numpy(dtype=float)
    tau, p_value = kendalltau(x, y, nan_policy="omit")
    slope, intercept, low, high = theilslopes(y, x, alpha=0.95)
    if slope > 0:
        direction = "increasing"
    elif slope < 0:
        direction = "decreasing"
    else:
        direction = "approximately stable"
    return {
        "status": "ok", "n": int(len(y)), "direction": direction,
        "sen_slope_per_year": float(slope),
        "sen_slope_per_decade": float(slope * 10),
        "slope_ci95_per_year": [float(low), float(high)],
        "kendall_tau": float(tau) if np.isfinite(tau) else None,
        "p_value": float(p_value) if np.isfinite(p_value) else None,
        "significant_005": bool(p_value < 0.05) if np.isfinite(p_value) else None,
        "first_month": str(work["date"].iloc[0].date()),
        "last_month": str(work["date"].iloc[-1].date()),
        "caveat": "Simple Kendall test; monthly seasonality and serial autocorrelation are not corrected."
    }
