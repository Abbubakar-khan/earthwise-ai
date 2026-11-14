"""Transparent climate-risk screening — derived ONLY from real computed data.

No invented forecasts. Scores combine:
  * the Sen's-slope trend already computed from NASA POWER monthly data,
  * the latest seasonal anomaly,
  * live model weather (heat / rain) and live CAMS air quality.
Every score is labelled a *screening* signal, not an official warning.
Projections are a straight-line Sen-slope extrapolation, with its CI,
and are labelled as such — they are not a climate model.
"""
from __future__ import annotations

import pandas as pd


def _score_from_slope(slope_per_decade, unit_scale, invert=False):
    """0-100 score from a per-decade slope, scaled so 1 unit-scale = ~50 pts."""
    if slope_per_decade is None:
        return None
    try:
        s = abs(float(slope_per_decade)) / float(unit_scale) * 50.0
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    v = max(0.0, min(100.0, s))
    return v if not invert else v


def risk_level(score):
    if score is None:
        return "Unknown"
    if score < 25:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 75:
        return "High"
    return "Very high"


def compute_risk(monthly, variable, trend, latest_anomaly=None,
                 current_temp=None, us_aqi=None):
    """Return a dict of screening scores. All inputs may be None."""
    out = {"variable": variable, "scores": {}, "notes": []}
    if trend and trend.get("status") == "ok":
        slope = trend.get("sen_slope_per_decade")
        # Scale: 2 degC/decade or 100 mm/decade precipitation = high trend signal.
        scale = 2.0 if variable in ("T2M", "T2M_MAX", "T2M_MIN") else (
            100.0 if variable == "PRECTOTCORR" else 10.0)
        s = _score_from_slope(slope, scale)
        out["scores"]["trend"] = s
        out["scores"]["trend_direction"] = trend.get("direction")
        out["scores"]["trend_label"] = risk_level(s)
        _p = trend.get("p_value")
        _p_text = f"{_p:.2f}" if isinstance(_p, (int, float)) else "unavailable"
        out["notes"].append(
            f"Trend signal from Sen's slope {slope:+.3g} per decade "
            f"(Kendall p={_p_text}, n={trend.get('n')} months).")
    if latest_anomaly is not None:
        try:
            a = abs(float(latest_anomaly))
            out["scores"]["anomaly"] = max(0.0, min(100.0, a * 20.0))
            out["scores"]["anomaly_label"] = risk_level(out["scores"]["anomaly"])
        except (TypeError, ValueError):
            pass
    if current_temp is not None:
        try:
            t = float(current_temp)
            out["scores"]["heat_now"] = 100.0 if t >= 45 else 75.0 if t >= 40 else 50.0 if t >= 35 else 25.0 if t >= 30 else 10.0
            out["scores"]["heat_now_label"] = risk_level(out["scores"]["heat_now"])
        except (TypeError, ValueError):
            pass
    if us_aqi is not None:
        try:
            aqi = float(us_aqi)
            out["scores"]["air_quality"] = max(0.0, min(100.0, aqi / 3.0))
            out["scores"]["air_quality_label"] = risk_level(out["scores"]["air_quality"])
        except (TypeError, ValueError):
            pass
    parts = [v for k, v in out["scores"].items()
             if isinstance(v, (int, float)) and k in ("trend", "anomaly", "heat_now", "air_quality")]
    out["composite"] = round(sum(parts) / len(parts), 1) if parts else None
    out["composite_label"] = risk_level(out["composite"])
    out["notes"].append(
        "Screening only: this is not a PMD / health-authority warning, "
        "flood forecast or disaster alert. Verify with official sources.")
    return out


def project_trend(monthly, variable, trend, years_ahead=10):
    """Linear Sen-slope extrapolation. Returns rows or an empty frame + note."""
    if not trend or trend.get("status") != "ok" or monthly is None or monthly.empty:
        return pd.DataFrame(), "Projection needs a valid trend (at least 24 monthly observations)."
    last = monthly.dropna(subset=[variable]).sort_values("date")
    if last.empty:
        return pd.DataFrame(), "No valid monthly observations to project from."
    last_date = pd.to_datetime(last["date"].iloc[-1])
    last_val = float(last[variable].iloc[-1])
    slope_year = float(trend["sen_slope_per_year"])
    lo, hi = trend.get("slope_ci95_per_year", [slope_year, slope_year])
    rows = []
    for y in range(1, years_ahead + 1):
        d = last_date + pd.DateOffset(years=y)
        rows.append({
            "date": d, "year": d.year,
            "projected": last_val + slope_year * y,
            "low_95": last_val + float(lo) * y,
            "high_95": last_val + float(hi) * y,
        })
    note = (f"Straight-line extrapolation of Sen's slope "
            f"({slope_year:+.4g} per year) from the last observed month "
            f"({last_date.date()}, {last_val:.2f}). Not a climate-model projection.")
    return pd.DataFrame(rows), note
