"""Farmer crop-planting guide — which crops to sow right now, and why.

Pure logic, no Streamlit, no network: it takes the live data the app
already fetched (current weather, 7-day Open-Meteo forecast, and the
loaded NASA POWER monthly climate history when available) and returns a
per-crop verdict for the selected place.

Crops covered: wheat, rice (basmati), cotton, maize, sugarcane, onion,
tomato, potato — the crops most Pakistani farmers actually grow.

How a verdict is reached (all from real numbers, never a guess):
- **Sowing window**: conservative planting months for the Punjab / Sindh
  plains, the country's main cropping belt. Windows are the *core* of the
  usual season, not its edges, so "sow now" is only said inside the safe
  middle of the season. Northern areas, high valleys (Gilgit-Baltistan,
  Chitral, Murree) and coastal Sindh run 2–4 weeks later / earlier — the
  app says this next to the guide.
- **This week's weather**: 7-day forecast min/max temperatures, rain and
  frost/heat days. A crop in its window still gets a warning when frost
  (night ≤ 2 °C), heat (day ≥ 40 °C) or heavy rain (≥ 20 mm/day) is
  coming in the next 7 days.
- **This month's climate**: when the NASA POWER monthly history is
  loaded for T2M, the average temperature of this calendar month across
  the loaded years is shown as context ("usually ~24 °C in November").

Statuses:
- "sow_now" — inside the core sowing window; go ahead if the week's
  weather has no warning for this crop.
- "coming_soon" — the window opens within the next month; prepare seed,
  land and water now.
- "too_late" — this season's window has closed; wait for the next season
  (the next window month is named).
- "wait" — outside any window and the next window is more than a month
  away.

Honesty: this is general planning guidance from a model forecast and
historical averages — NOT agronomy advice and NOT an official warning.
Variety, soil, water availability and local conditions change everything;
confirm with the local agriculture department / extension worker before
sowing. The app shows this disclaimer next to the guide.
"""
from __future__ import annotations

from datetime import date

# Conservative core sowing windows (month numbers, Punjab/Sindh plains).
# "window" = months in which sowing is normally safe; "ideal_tmax"/"ideal_tmin"
# = day/night temperatures the crop likes while establishing; "frost" /
# "heat" = the crop is harmed by frost / by day heat above this.
# Sources: standard Pakistan cropping calendars (Punjab Agriculture
# Department / PARC guidance as commonly published); windows are narrowed
# to the safe core on purpose — an edge-of-season sowing is never called
# "sow now" here.
CROPS = [
    {
        "key": "wheat", "name": "Wheat", "name_ur": "گندم",
        "season": "Rabi (winter)", "window": (10, 11, 12),
        "window_text": "Late Oct – mid Dec (best: November)",
        "ideal_tmax": (20, 30), "ideal_tmin": (8, 18),
        "frost_sensitive": True, "heat_limit": 35,
        "water": "Needs irrigation at crown-root, tillering and grain filling.",
        "note": "Pakistan's main food crop. Late sowing (after Dec) cuts yield sharply.",
    },
    {
        "key": "rice", "name": "Rice (Basmati)", "name_ur": "چاول (باسمتی)",
        "season": "Kharif (summer)", "window": (5, 6, 7),
        "window_text": "Nursery May–Jun, transplant Jun–Jul",
        "ideal_tmax": (28, 38), "ideal_tmin": (20, 28),
        "frost_sensitive": True, "heat_limit": 42,
        "water": "Needs standing water; transplant only when fields stay wet.",
        "note": "Needs warm nights — cold below 15 °C at flowering harms grain.",
    },
    {
        "key": "cotton", "name": "Cotton", "name_ur": "کپاس",
        "season": "Kharif (summer)", "window": (3, 4, 5),
        "window_text": "March – May (Sindh Mar–Apr, Punjab Apr–May)",
        "ideal_tmax": (28, 38), "ideal_tmin": (18, 27),
        "frost_sensitive": True, "heat_limit": 45,
        "water": "Needs regular irrigation; rain at picking time spoils the lint.",
        "note": "No frost at all — one frost night can kill young plants.",
    },
    {
        "key": "maize", "name": "Maize", "name_ur": "مکئی",
        "season": "Spring + Autumn", "window": (2, 3, 7, 8),
        "window_text": "Spring Feb–Mar, autumn Jul–Aug",
        "ideal_tmax": (24, 34), "ideal_tmin": (14, 24),
        "frost_sensitive": True, "heat_limit": 40,
        "water": "Needs water at tasselling and grain filling; hates waterlogging.",
        "note": "Two seasons a year — spring and autumn — with a gap in between.",
    },
    {
        "key": "sugarcane", "name": "Sugarcane", "name_ur": "گنا",
        "season": "Perennial", "window": (2, 3, 9, 10),
        "window_text": "Spring Feb–Mar, autumn Sep–Oct",
        "ideal_tmax": (26, 38), "ideal_tmin": (18, 28),
        "frost_sensitive": True, "heat_limit": 42,
        "water": "Thirstiest crop here — needs water all year, most at tillering.",
        "note": "A 12–14 month crop; plant once, harvest after a year.",
    },
    {
        "key": "onion", "name": "Onion", "name_ur": "پیاز",
        "season": "Rabi (winter)", "window": (10, 11, 12),
        "window_text": "Nursery Oct–Nov, transplant Dec–Jan",
        "ideal_tmax": (20, 30), "ideal_tmin": (8, 18),
        "frost_sensitive": False, "heat_limit": 35,
        "water": "Light, frequent watering; no waterlogging or bulbs rot.",
        "note": "Cool-season crop — heat above 35 °C stops bulb growth.",
    },
    {
        "key": "tomato", "name": "Tomato", "name_ur": "ٹماٹر",
        "season": "Autumn + Spring", "window": (2, 3, 8, 9),
        "window_text": "Nursery Aug–Sep and Feb–Mar",
        "ideal_tmax": (22, 32), "ideal_tmin": (14, 24),
        "frost_sensitive": True, "heat_limit": 38,
        "water": "Even watering — dry then wet splits the fruit.",
        "note": "Frost kills it; flowers drop in heat above 38 °C.",
    },
    {
        "key": "potato", "name": "Potato", "name_ur": "آلو",
        "season": "Rabi (winter)", "window": (10, 11),
        "window_text": "October – November (plains)",
        "ideal_tmax": (18, 28), "ideal_tmin": (8, 18),
        "frost_sensitive": True, "heat_limit": 32,
        "water": "Needs moist soil at tuber formation; avoid waterlogging.",
        "note": "Cool-season crop — frost damages leaves, heat stops tubers.",
    },
]

DISCLAIMER = (
    "General planning guidance from the 7-day model forecast and historical "
    "averages — not agronomy advice and not an official warning. Variety, "
    "soil, water and local conditions change everything: confirm with your "
    "local agriculture department or extension worker before sowing. "
    "Windows are for the Punjab / Sindh plains; northern and high areas "
    "run 2–4 weeks later."
)


def _num(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _forecast_days(forecast):
    """Normalise the Open-Meteo daily dict into a list of day dicts."""
    if not isinstance(forecast, dict):
        return []
    daily = forecast.get("daily")
    if not isinstance(daily, dict):
        return []
    times = daily.get("time") or []
    if not times:
        return []
    keys = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum",
            "weather_code")
    n = len(times)
    for key in keys:
        vals = daily.get(key)
        if isinstance(vals, (list, tuple)):
            n = min(n, len(vals))
    days = []
    for i in range(n):
        def _at(key):
            vals = daily.get(key)
            if isinstance(vals, (list, tuple)) and i < len(vals):
                return _num(vals[i])
            return None
        days.append({"tmax": _at("temperature_2m_max"),
                     "tmin": _at("temperature_2m_min"),
                     "rain_mm": _at("precipitation_sum"),
                     "code": _at("weather_code")})
    return days


def _typical_month_temp(monthly, variable):
    """Mean temperature of the current calendar month across the loaded
    NASA POWER history (T2M only). Returns None when unavailable."""
    if monthly is None or variable != "T2M":
        return None
    try:
        import pandas as pd
        df = monthly
        if "T2M" not in df.columns or "month" not in df.columns:
            return None
        this_month = df[df["month"] == date.today().month]["T2M"]
        this_month = pd.to_numeric(this_month, errors="coerce").dropna()
        if this_month.empty:
            return None
        return float(this_month.mean())
    except Exception:
        return None


def _window_status(crop, month):
    """(status, reason) for a crop in a given calendar month."""
    window = crop["window"]
    if month in window:
        return ("sow_now",
                f"Sowing window is open now ({crop['window_text']}).")
    # Next window month (wrapping into next year).
    future = sorted(m for m in window if m > month) or sorted(window)
    next_m = future[0]
    months_away = (next_m - month) % 12 or 12
    if months_away == 1:
        return ("coming_soon",
                f"Sowing window opens next month ({crop['window_text']}) — "
                "prepare seed, land and water now.")
    # Months since the last window month (circular): if the window closed
    # within the last 3 months, this season is just missed — say so plainly.
    months_since = min((month - m) % 12 for m in window)
    if 1 <= months_since <= 3:
        return ("too_late",
                f"This season's sowing window ({crop['window_text']}) "
                f"has closed — next chance is month {next_m}.")
    return ("wait",
            f"Not sowing time — window is {crop['window_text']} "
            f"(next opens in about {months_away} month{'s' if months_away != 1 else ''}).")


def crop_planting_guide(forecast, weather=None, monthly=None, variable=None,
                        today=None):
    """Per-crop planting verdicts for the selected place.

    forecast: get_weather_forecast dict (may be None). weather: current
    conditions dict (may be None). monthly: monthly-aggregated NASA POWER
    dataframe (may be None). today: date for testing (defaults to today).
    Returns {"status": "ok"|"unavailable", "crops": [...], ...}.
    Never raises on bad input.
    """
    days = _forecast_days(forecast)
    if not days:
        return {"status": "unavailable", "crops": [], "disclaimer": DISCLAIMER,
                "typical_month_temp_c": None}
    now = today or date.today()
    month = now.month
    current_temp = _num((weather or {}).get("temperature_2m"))
    tmax_week = [d["tmax"] for d in days if d["tmax"] is not None]
    tmin_week = [d["tmin"] for d in days if d["tmin"] is not None]
    rain_week = [d["rain_mm"] for d in days if d["rain_mm"] is not None]
    week_max = max(tmax_week) if tmax_week else None
    week_min = min(tmin_week) if tmin_week else None
    week_rain = sum(rain_week) if rain_week else 0.0
    frost_days = sum(1 for d in days
                     if d["tmin"] is not None and d["tmin"] <= 2)
    heavy_rain_days = sum(1 for d in days
                          if d["rain_mm"] is not None and d["rain_mm"] >= 20)
    typical = _typical_month_temp(monthly, variable)

    crops = []
    for crop in CROPS:
        status, reason = _window_status(crop, month)
        watch = []
        if status == "sow_now":
            if crop["frost_sensitive"] and frost_days:
                watch.append(f"Frost in the next 7 days ({frost_days} night"
                             f"{'s' if frost_days != 1 else ''} ≤ 2 °C) — "
                             "young plants can die; wait for the frost to pass.")
            if week_max is not None and week_max >= crop["heat_limit"]:
                watch.append(f"Heat up to {week_max:.0f} °C this week "
                             f"(limit {crop['heat_limit']} °C) — sow in the "
                             "evening and water well.")
            if heavy_rain_days:
                watch.append(f"Heavy rain on {heavy_rain_days} day"
                             f"{'s' if heavy_rain_days != 1 else ''} this week "
                             "— do not sow on wet, waterlogged fields.")
            if not watch:
                watch.append("This week's weather looks fine for sowing — "
                             "no frost, heat or heavy-rain warning.")
        # Temperature fit, from the real week ahead.
        temp_note = None
        if week_max is not None and week_min is not None:
            lo, hi = crop["ideal_tmax"]
            if week_max > hi + 5:
                temp_note = (f"Days up to {week_max:.0f} °C — hotter than "
                             f"this crop likes ({lo}–{hi} °C days).")
            elif week_min < crop["ideal_tmin"][0] - 5:
                temp_note = (f"Nights down to {week_min:.0f} °C — colder "
                             "than this crop likes.")
        crops.append({
            "key": crop["key"], "name": crop["name"],
            "name_ur": crop["name_ur"], "season": crop["season"],
            "status": status, "reason": reason,
            "window_text": crop["window_text"], "water": crop["water"],
            "note": crop["note"], "watch": watch,
            "temp_note": temp_note,
        })
    summary = {
        "sow_now": sum(1 for c in crops if c["status"] == "sow_now"),
        "coming_soon": sum(1 for c in crops if c["status"] == "coming_soon"),
    }
    return {
        "status": "ok", "crops": crops, "disclaimer": DISCLAIMER,
        "month": month, "current_temp_c": current_temp,
        "week_max_c": week_max, "week_min_c": week_min,
        "week_rain_mm": week_rain, "frost_days": frost_days,
        "heavy_rain_days": heavy_rain_days,
        "typical_month_temp_c": typical,
        "summary": summary,
    }
