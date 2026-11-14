"""Climate story in one line — plain-language summary from computed stats.

Pure logic, no Streamlit, no network: it takes the trend already computed
by src/statistics.analyze_trend and the monthly table already built by
src/cleaning.monthly_aggregate, and turns them into honest sentences.

Honesty is the whole point:
- A trend is only called "significant" when the Kendall p-value is < 0.05.
- When p is not significant, the story says so plainly and never claims
  warming or cooling — e.g. Lahore T2M 2015–2025: decreasing, Sen slope
  -1.34 °C/decade, p = 0.52, NOT significant, so the data do not show a
  clear trend either way.
- Hottest/coldest (or wettest/driest for precipitation) months come from
  the monthly means in the loaded dataset, never from a guess.
- Missing or insufficient data returns "unavailable", never a sentence.
"""
from __future__ import annotations

import calendar

_MONTH_NAMES = list(calendar.month_name)  # index 1..12


def _fmt_mag(value, unit):
    """Magnitude with sensible precision: 1 decimal normally, 2 when small."""
    try:
        v = abs(float(value))
    except (TypeError, ValueError):
        return None
    if v >= 1:
        return f"{v:.1f}"
    return f"{v:.2f}"


def _fmt_p(p_value):
    try:
        p = float(p_value)
    except (TypeError, ValueError):
        return None
    if p < 0.001:
        return "< 0.001"
    return f"{p:.2g}"


def _month_extremes(monthly, variable, unit):
    """(hottest, coldest) or (wettest, driest) month from monthly means.

    Returns {"hot": (name, value), "cold": (name, value), "kind": "temp"|"rain"}
    or None when the monthly table cannot support it.
    """
    if monthly is None:
        return None
    try:
        import pandas as pd

        work = monthly.copy()
        if "month" not in work.columns:
            work["date"] = pd.to_datetime(work["date"], errors="coerce")
            work["month"] = work["date"].dt.month
        work[variable] = pd.to_numeric(work[variable], errors="coerce")
        work = work.dropna(subset=["month", variable])
        if work.empty or work["month"].nunique() < 2:
            return None
        means = work.groupby("month")[variable].mean()
        hot_month = int(means.idxmax())
        cold_month = int(means.idxmin())
        is_rain = "mm" in str(unit)
        return {
            "hot": (_MONTH_NAMES[hot_month], float(means.loc[hot_month])),
            "cold": (_MONTH_NAMES[cold_month], float(means.loc[cold_month])),
            "kind": "rain" if is_rain else "temp",
        }
    except Exception:
        return None


def climate_story(city, variable, variable_label, unit, trend, monthly=None):
    """One-line climate story + supporting detail for a loaded city.

    city: city name. variable: NASA POWER key (e.g. "T2M",
    "PRECTOTCORR"). variable_label/unit: display label and unit.
    trend: dict from analyze_trend (must have status "ok").
    monthly: monthly-aggregate DataFrame (optional; enables the
    hottest/coldest or wettest/driest month sentence).

    Returns {"status": "ok"|"unavailable", "line": str, "detail": str,
    "direction": str|None, "significant": bool|None}.
    """
    if not isinstance(trend, dict) or trend.get("status") != "ok":
        return {"status": "unavailable", "line": "", "detail": "",
                "direction": None, "significant": None}
    slope = trend.get("sen_slope_per_decade")
    p_value = trend.get("p_value")
    n = trend.get("n")
    try:
        slope_f = float(slope)
    except (TypeError, ValueError):
        return {"status": "unavailable", "line": "", "detail": "",
                "direction": None, "significant": None}
    direction = trend.get("direction") or ("increasing" if slope_f > 0 else
                                           "decreasing" if slope_f < 0 else
                                           "approximately stable")
    try:
        p_f = float(p_value) if p_value is not None else None
    except (TypeError, ValueError):
        p_f = None
    significant = bool(p_f is not None and p_f < 0.05)
    first = str(trend.get("first_month", ""))[:4]
    last = str(trend.get("last_month", ""))[:4]
    years = f"{first}–{last}" if first and last else "this period"
    mag = _fmt_mag(slope_f, unit)
    label = str(variable_label or "climate")
    p_txt = _fmt_p(p_f)
    verb = {"increasing": "rose", "decreasing": "fell"}.get(direction, "changed")
    if direction == "approximately stable" or mag in (None, "0.00", "0.0"):
        line = (f"Over {years}, {city}'s {label} changed very little — "
                f"about {mag or '0'} {unit} per decade, "
                f"which is no clear trend either way.")
    elif significant:
        trend_word = "warming" if slope_f > 0 else "cooling"
        line = (f"Over {years}, {city}'s {label} {verb} by about {mag} {unit} "
                f"per decade — a statistically significant {trend_word} trend"
                + (f" (p = {p_txt})." if p_txt else "."))
    else:
        line = (f"Over {years}, {city}'s {label} drifted {direction} by about "
                f"{mag} {unit} per decade — but with "
                + (f"p = {p_txt} " if p_txt else "no p-value computed ")
                + "this is not statistically significant, so the data do not "
                f"show a clear {direction} trend.")
    # Detail: seasonal extremes + how much data the story rests on.
    detail_bits = []
    extremes = _month_extremes(monthly, variable, unit)
    if extremes:
        hot_name, hot_val = extremes["hot"]
        cold_name, cold_val = extremes["cold"]
        dec = 0 if extremes["kind"] == "rain" else 1
        if extremes["kind"] == "rain":
            detail_bits.append(
                f"{hot_name} is typically the wettest month "
                f"(~{hot_val:.{dec}f} {unit}) and {cold_name} the driest "
                f"(~{cold_val:.{dec}f} {unit}).")
        else:
            detail_bits.append(
                f"{hot_name} is typically the hottest month "
                f"(~{hot_val:.{dec}f} {unit}) and {cold_name} the coldest "
                f"(~{cold_val:.{dec}f} {unit}).")
    if n:
        detail_bits.append(
            f"Based on {int(n):,} monthly observations"
            + (f" from {trend.get('first_month')} to {trend.get('last_month')}"
               if trend.get("first_month") and trend.get("last_month") else "")
            + ".")
    detail_bits.append(
        "A straight-line Sen-slope summary — it does not correct for "
        "seasonality or autocorrelation, and it is not a forecast.")
    return {"status": "ok", "line": line, "detail": " ".join(detail_bits),
            "direction": direction, "significant": significant}
