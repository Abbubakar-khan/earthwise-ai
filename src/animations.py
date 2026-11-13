"""Live animations for EarthWise AI — pure helpers, no Streamlit, no new deps.

CSS-only animation: the classes / HTML here are rendered by app/main.py.
Every ticker item comes from real live data passed in by the caller;
nothing here invents a temperature, AQI or time. Missing values are
simply omitted, never replaced with a sample number.
"""
from __future__ import annotations

import html

# Weather-code -> CSS animation class (Open-Meteo WMO codes).
# 0 clear, 1-2 mainly/partly cloudy, 3 overcast, 45/48 fog,
# 51-67 + 80-82 rain/drizzle, 71-77 + 85-86 snow, 95-99 thunderstorm.
def weather_animation_class(code) -> str:
    try:
        c = int(code)
    except (TypeError, ValueError):
        return "wx-partly"
    if c == 0:
        return "wx-clear"
    if c in (1, 2):
        return "wx-partly"
    if c == 3:
        return "wx-cloud"
    if c in (45, 48):
        return "wx-fog"
    if 51 <= c <= 67 or 80 <= c <= 82:
        return "wx-rain"
    if 71 <= c <= 77 or 85 <= c <= 86:
        return "wx-snow"
    if 95 <= c <= 99:
        return "wx-storm"
    return "wx-partly"


def _fmt_temp(v):
    try:
        return f"{float(v):.1f} °C"
    except (TypeError, ValueError):
        return None


def _fmt_int(v):
    try:
        return f"{float(v):.0f}"
    except (TypeError, ValueError):
        return None


def build_ticker_items(ctx: dict | None) -> list[str]:
    """Build ticker strings from real live context. ctx keys (all optional):
    city, temperature, condition, us_aqi, aqi_label, pm2_5, provider_time.
    Returns [] when nothing real is available — caller shows a fallback.
    """
    if not isinstance(ctx, dict):
        return []
    items: list[str] = []
    city = ctx.get("city")
    temp = _fmt_temp(ctx.get("temperature"))
    condition = ctx.get("condition")
    if city and temp:
        items.append(f"{city} — {temp}" + (f" · {condition}" if condition else ""))
    elif city and condition:
        items.append(f"{city} — {condition}")
    aqi = _fmt_int(ctx.get("us_aqi"))
    if aqi is not None:
        label = ctx.get("aqi_label")
        items.append(f"US AQI {aqi}" + (f" — {label}" if label else ""))
    pm25 = ctx.get("pm2_5")
    try:
        items.append(f"PM2.5 {float(pm25):.1f} µg/m³")
    except (TypeError, ValueError):
        pass
    when = ctx.get("provider_time")
    if when:
        items.append(f"Updated {when}")
    items.append("Live data · NASA POWER · Open-Meteo · CAMS")
    return items


def ticker_html(items: list[str]) -> str:
    """Seamless scrolling ticker. Items are duplicated so the loop has no gap.
    Returns '' when there is nothing to show.
    """
    clean = [str(i).strip() for i in (items or []) if str(i).strip()]
    if not clean:
        return ""
    # Duplicate the set so translateX(-50%) loops seamlessly.
    doubled = clean + clean
    spans = "".join(
        f'<span class="ew-ticker-item">{html.escape(t)}</span>'
        f'<span class="ew-ticker-dot">●</span>'
        for t in doubled
    )
    return (
        '<div class="ew-ticker" role="status" aria-label="Live updates">'
        '<div class="ew-ticker-track">' + spans + "</div></div>"
    )


def hero_symbol_html(code, symbol: str) -> str:
    """Floating weather symbol for the hero. `symbol` is the emoji already
    chosen by main.weather_symbol(); the CSS class animates it by condition.
    """
    cls = weather_animation_class(code)
    return (
        f'<div class="wx-hero-symbol {cls}" aria-hidden="true">'
        f'<span class="wx-float">{html.escape(str(symbol or "🌤️"))}</span></div>'
    )


def weather_emoji(code) -> str:
    """Emoji for an Open-Meteo WMO weather code (same mapping as main.py)."""
    try:
        c = int(code)
    except (TypeError, ValueError):
        return "🌤️"
    if c == 0:
        return "☀️"
    if c in (1, 2):
        return "🌤️"
    if c == 3:
        return "☁️"
    if c in (45, 48):
        return "🌫️"
    if 51 <= c <= 67:
        return "🌧️"
    if 71 <= c <= 77:
        return "❄️"
    if 80 <= c <= 82:
        return "🌦️"
    if 85 <= c <= 86:
        return "🌨️"
    if 95 <= c <= 99:
        return "⛈️"
    return "🌤️"


def demo_is_default(city, variable) -> bool:
    """True when the selection is the shipped demo dataset: Lahore + T2M."""
    return city == "Lahore" and variable == "T2M"


def _fmt_num(v, ndigits=1):
    try:
        return f"{float(v):.{ndigits}f}"
    except (TypeError, ValueError):
        return None


def hero_now_html(weather, aqi) -> str:
    """Right-hand live panel for the hero: big temperature, symbol,
    condition, feels-like and mini stats. All values real; '' when the
    live weather call failed so the hero falls back to text only.
    """
    if not isinstance(weather, dict):
        return ""
    temp = _fmt_num(weather.get("temperature_2m"))
    if temp is None:
        return ""
    code = weather.get("weather_code")
    condition = weather.get("condition_text") or ""
    feels = _fmt_num(weather.get("apparent_temperature"))
    hum = _fmt_num(weather.get("relative_humidity_2m"), 0)
    wind = _fmt_num(weather.get("wind_speed_10m"))
    aqi_txt = ""
    if isinstance(aqi, dict) and isinstance(aqi.get("current"), dict):
        aqi_v = _fmt_int(aqi["current"].get("us_aqi"))
        if aqi_v is not None:
            aqi_txt = f" · AQI {aqi_v} {html.escape(str(aqi.get('aqi_label') or ''))}".strip()
    stats = []
    if hum is not None:
        stats.append(f"Humidity {hum}%")
    if wind is not None:
        stats.append(f"Wind {wind} km/h")
    if aqi_txt:
        stats.append(aqi_txt.replace(" · ", ""))
    return (
        '<div class="ew-hero-right">'
        + hero_symbol_html(code, weather_emoji(code))
        + f'<div class="ew-now-temp">{temp}°</div>'
        + f'<div class="ew-now-cond">{html.escape(str(condition))}'
        + (f" · Feels like {feels}°" if feels is not None else "")
        + "</div>"
        + (f'<div class="ew-now-stats">{" · ".join(html.escape(s) for s in stats)}</div>' if stats else "")
        + "</div>"
    )


def forecast_cards_html(daily) -> str:
    """7-day forecast as one responsive grid (7 cols desktop, 4 tablet,
    2 mobile). Pure function: returns '' when daily data is missing.
    Values are real Open-Meteo daily values; missing fields render as '—'.
    """
    if not isinstance(daily, dict):
        return ""
    times = daily.get("time") or []
    n = min(7, len(times))
    if n == 0:
        return ""
    import datetime as _dt

    def _val(key, i, nd=0):
        vals = daily.get(key) or []
        if i >= len(vals) or vals[i] is None:
            return None
        try:
            return f"{float(vals[i]):.{nd}f}"
        except (TypeError, ValueError):
            return None

    cards = []
    for i in range(n):
        try:
            day = _dt.datetime.fromisoformat(str(times[i])).strftime("%a, %d %b")
        except (TypeError, ValueError):
            day = str(times[i])
        code = (daily.get("weather_code") or [None] * n)[i]
        cond = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Rime fog"}.get(code, "Conditions")
        if isinstance(code, (int, float)) and 51 <= code <= 99:
            cond = "Rain / showers" if code < 71 else ("Snow" if code < 85 else "Storm")
        hi, lo = _val("temperature_2m_max", i), _val("temperature_2m_min", i)
        rain = _val("precipitation_probability_max", i)
        rain_mm = _val("precipitation_sum", i, 1)
        wind = _val("wind_speed_10m_max", i)
        uv = _val("uv_index_max", i, 1)
        cards.append(
            '<div class="ew-fc">'
            f'<div class="ew-fc-day">{html.escape(day)}</div>'
            f'<div class="ew-fc-sym">{weather_emoji(code)}</div>'
            f'<div class="ew-fc-cond">{html.escape(str(cond))}</div>'
            f'<div class="ew-fc-temp">{hi or "—"}° <span>/ {lo or "—"}°</span></div>'
            f'<div class="ew-fc-meta">Rain {rain or "—"}% · {rain_mm or "—"} mm<br>'
            f"Wind {wind or '—'} km/h · UV {uv or '—'}</div>"
            "</div>"
        )
    return '<div class="ew-forecast-grid">' + "".join(cards) + "</div>"


ANIMATION_CSS = """
/* --- Live animations (CSS only; respects prefers-reduced-motion below) --- */
@keyframes heroShimmer{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes kpiIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes chartIn{from{opacity:0}to{opacity:1}}
@keyframes tickerScroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes livePulse{0%{box-shadow:0 0 0 0 rgba(126,232,214,.55)}70%{box-shadow:0 0 0 9px rgba(126,232,214,0)}100%{box-shadow:0 0 0 0 rgba(126,232,214,0)}}
@keyframes wxFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
@keyframes wxSpin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes wxDrift{0%,100%{transform:translateX(0)}50%{transform:translateX(14px)}}
@keyframes wxRain{0%{transform:translateY(-4px)}50%{transform:translateY(8px)}100%{transform:translateY(-4px)}}
@keyframes wxStorm{0%,100%{opacity:1}50%{opacity:.55}}
.ew-hero-anim{background:linear-gradient(120deg,rgba(16,42,61,.92),rgba(9,24,36,.88),rgba(16,58,64,.9),rgba(9,24,36,.88));background-size:220% 220%;animation:heroShimmer 14s ease infinite}
.ew-hero{position:relative;overflow:hidden}
.wx-hero-symbol{position:absolute;top:18px;right:22px;font-size:3.1rem;line-height:1;filter:drop-shadow(0 6px 18px rgba(126,232,214,.25));pointer-events:none}
.wx-hero-symbol .wx-float{display:inline-block;animation:wxFloat 4s ease-in-out infinite}
.wx-hero-symbol.wx-clear .wx-float{animation:wxSpin 16s linear infinite}
.wx-hero-symbol.wx-partly .wx-float,.wx-hero-symbol.wx-cloud .wx-float{animation:wxDrift 5s ease-in-out infinite}
.wx-hero-symbol.wx-rain .wx-float{animation:wxRain 1.6s ease-in-out infinite}
.wx-hero-symbol.wx-snow .wx-float{animation:wxFloat 3s ease-in-out infinite}
.wx-hero-symbol.wx-storm .wx-float{animation:wxStorm 1.8s ease-in-out infinite}
.wx-hero-symbol.wx-fog .wx-float{animation:wxStorm 4s ease-in-out infinite}
.ew-ticker{overflow:hidden;border:1px solid var(--border);border-radius:999px;background:rgba(13,31,46,.75);margin:0 0 16px;padding:9px 0}
.ew-ticker-track{display:inline-flex;align-items:center;gap:14px;white-space:nowrap;width:max-content;animation:tickerScroll 30s linear infinite}
.ew-ticker:hover .ew-ticker-track{animation-play-state:paused}
.ew-ticker-item{color:#cfe8ef;font-size:.78rem;font-weight:600;letter-spacing:.02em}
.ew-ticker-dot{color:var(--accent);font-size:.5rem}
.ew-live i{animation:livePulse 1.6s infinite}
.live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent);animation:livePulse 1.6s infinite;vertical-align:middle;margin-right:6px}
.ew-updated{color:var(--muted);font-size:.74rem;margin:0 0 14px}
.kpi{animation:kpiIn .55s cubic-bezier(.2,.7,.3,1) backwards}
[data-testid="stPlotlyChart"]{animation:chartIn .6s ease backwards}
.stButton>button,.stDownloadButton>button{transition:transform .12s,background .15s,border-color .15s,box-shadow .15s}
.stButton>button:active,.stDownloadButton>button:active{transform:scale(.98)}
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media(max-width:700px){.wx-hero-symbol{font-size:2.1rem;top:14px;right:14px}.ew-ticker-item{font-size:.7rem}.ew-ticker-track{animation-duration:22s}}
"""

INTRO_CSS = """
/* --- Opening intro splash: full-screen, CSS only, fades out --- */
@keyframes introGlobeSpin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes introOrbit{from{transform:rotate(0deg) translateX(74px) rotate(0deg)}to{transform:rotate(360deg) translateX(74px) rotate(-360deg)}}
@keyframes introRise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes introFlyIn{0%{opacity:0;transform:translateY(-56px) scale(.92)}60%{opacity:1;transform:translateY(5px) scale(1.02)}100%{opacity:1;transform:translateY(0) scale(1)}}
@keyframes introBar{from{width:4%}to{width:100%}}
@keyframes introGlow{0%,100%{box-shadow:0 0 0 0 rgba(126,232,214,.35)}50%{box-shadow:0 0 44px 6px rgba(126,232,214,.28)}}
@keyframes introFadeOut{to{opacity:0;visibility:hidden}}
.ew-intro{position:fixed;inset:0;z-index:999999;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:radial-gradient(900px 500px at 50% 18%,rgba(64,190,220,.22),transparent 62%),radial-gradient(700px 420px at 50% 110%,rgba(126,232,214,.14),transparent 60%),#060f18;color:#eef6f9;animation:introFadeOut .6s ease 3.1s forwards}
.ew-intro-globe{position:relative;width:148px;height:148px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:radial-gradient(circle at 34% 30%,#1d4a63,#0b1d2d 68%);border:1px solid rgba(126,232,214,.35);animation:introGlow 2.2s ease-in-out infinite}
.ew-intro-globe .ew-intro-earth{font-size:4.4rem;line-height:1;animation:introGlobeSpin 9s linear infinite}
.ew-intro-orbit{position:absolute;top:50%;left:50%;width:0;height:0}
.ew-intro-orbit i{position:absolute;top:-5px;left:-5px;width:10px;height:10px;border-radius:50%;background:#7ee8d6;box-shadow:0 0 12px #7ee8d6;animation:introOrbit 2.4s linear infinite}
.ew-intro-title{margin-top:30px;font:700 clamp(2rem,6vw,3.1rem)/1.05 'Space Grotesk',sans-serif;letter-spacing:.06em}
.ew-intro-letter{display:inline-block;animation:introFlyIn .55s cubic-bezier(.2,.7,.3,1) backwards}
.ew-intro-title .ew-intro-ai{color:#7ee8d6}
.ew-intro-tag{margin-top:12px;color:#b0c2ce;font-size:.92rem;font-weight:600;letter-spacing:.22em;text-transform:uppercase;animation:introRise .7s .35s cubic-bezier(.2,.7,.3,1) backwards}
.ew-intro-sub{margin-top:10px;color:#8299a8;font-size:.8rem;animation:introRise .7s .5s cubic-bezier(.2,.7,.3,1) backwards}
.ew-intro-bar{width:min(280px,72vw);height:4px;margin-top:30px;border-radius:999px;background:rgba(164,193,211,.18);overflow:hidden;animation:introRise .7s .6s backwards}
.ew-intro-bar i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#35cce8,#7ee8d6);animation:introBar 2.5s ease forwards}
.ew-intro-src{margin-top:16px;color:#6d8594;font-size:.68rem;letter-spacing:.14em;animation:introRise .7s .7s backwards}
@media(prefers-reduced-motion:reduce){.ew-intro *{animation-duration:.01ms!important;animation-delay:0ms!important}}
"""


def _intro_title_html() -> str:
    """Title letters fly in one by one (staggered delays); 'AI' in accent.
    Letters are literal strings, so no escaping is needed."""
    spans = []
    for i, ch in enumerate("EARTHWISE"):
        spans.append(
            f'<span class="ew-intro-letter" style="animation-delay:{50 + i * 70}ms">{ch}</span>'
        )
    spans.append(" ")
    for j, ch in enumerate("AI"):
        spans.append(
            f'<span class="ew-intro-letter ew-intro-ai" style="animation-delay:{700 + j * 70}ms">{ch}</span>'
        )
    return "".join(spans)


def intro_html() -> str:
    """Opening splash shown once per session instead of a blank loading
    screen. Pure CSS animation, no JavaScript, no network, no fake data:
    it only brands the app and names its real live sources."""
    return (
        '<div class="ew-intro" role="status" aria-label="EarthWise AI loading">'
        '<div class="ew-intro-globe"><span class="ew-intro-earth">🌍</span>'
        '<span class="ew-intro-orbit"><i></i></span></div>'
        '<div class="ew-intro-title">' + _intro_title_html() + "</div>"
        '<div class="ew-intro-tag">Pakistan Earth Intelligence</div>'
        '<div class="ew-intro-sub">Climate · Weather · Air Quality — live, for every city</div>'
        '<div class="ew-intro-bar"><i></i></div>'
        '<div class="ew-intro-src">NASA POWER &nbsp;·&nbsp; OPEN-METEO &nbsp;·&nbsp; CAMS &nbsp;·&nbsp; NASA GIBS</div>'
        "</div>"
    )


# --- Professional design fix (2026-11-14): header clearance, hero layout,
# stat tiles that never truncate, forecast grid, designed empty states. ---
DESIGN_CSS = """
/* Header clears the Streamlit toolbar; brand is bright, not grey-on-navy */
.block-container{padding-top:3.4rem!important}
[data-testid="stHeader"]{background:#060f18!important}
.ew-top{margin-top:2px;padding-top:10px}
.ew-brand{color:#eef6f9}
.ew-brand-sub{color:#b0c2ce;font-weight:500}
/* Hero: two-column, live panel fills the right half — no dead space */
.ew-hero{display:flex;gap:28px;align-items:center;justify-content:space-between}
.ew-hero-left{flex:1;min-width:0}
.ew-hero-right{flex:0 0 240px;text-align:center;padding:6px 4px;border-left:1px solid rgba(164,193,211,.14)}
.ew-hero-right .wx-hero-symbol{position:static;font-size:3.8rem;display:block;margin-bottom:2px}
.ew-now-temp{font:700 3.1rem/1 'Space Grotesk',sans-serif;letter-spacing:-.04em;color:#eef6f9}
.ew-now-cond{color:#cfe8ef;font-size:.86rem;font-weight:600;margin-top:6px}
.ew-now-stats{color:#9db2c0;font-size:.72rem;margin-top:8px;line-height:1.6}
/* Compact stat tiles — values wrap, never truncate ("6.1 km/h" fits) */
.ew-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
.ew-stats.cols-3{grid-template-columns:repeat(3,1fr)}
.ew-stat{padding:12px 10px;border:1px solid var(--border);border-radius:10px;background:rgba(255,255,255,.02)}
.ew-stat-label{color:#9db2c0;font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
.ew-stat-value{font:600 1.05rem 'Space Grotesk',sans-serif;color:#eef6f9;margin-top:5px;white-space:normal;overflow-wrap:break-word}
.ew-card-head b{font-size:.95rem}
.ew-card-head span{display:block;color:#9db2c0;font-size:.76rem;margin-top:3px}
.ew-card-foot{color:#9db2c0;font-size:.74rem;margin-top:12px;line-height:1.6}
.ew-live-card{display:flex;flex-direction:column}
.ew-live-card .ew-stats{flex:1}
/* Forecast: one clean strip — 7 cols desktop, 4 tablet, 2 mobile */
.ew-forecast-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin:8px 0 16px}
.ew-fc{padding:14px 12px;border:1px solid var(--border);border-radius:12px;background:linear-gradient(180deg,var(--surface2),var(--surface));min-height:168px}
.ew-fc:hover{border-color:rgba(126,232,214,.35)}
.ew-fc-day{color:#9db2c0;font-size:.64rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase}
.ew-fc-sym{font-size:1.5rem;margin:10px 0 4px}
.ew-fc-cond{font-size:.8rem;font-weight:600;color:#e8f1f5;min-height:2.1em;line-height:1.25}
.ew-fc-temp{font:600 1.35rem 'Space Grotesk',sans-serif;margin-top:6px}
.ew-fc-temp span{color:#9db2c0;font-size:.95rem}
.ew-fc-meta{color:#9db2c0;font-size:.68rem;line-height:1.6;margin-top:8px}
@media(max-width:1100px){.ew-forecast-grid{grid-template-columns:repeat(4,1fr)}}
@media(max-width:700px){.ew-forecast-grid{grid-template-columns:repeat(2,1fr)}.ew-stats{grid-template-columns:repeat(2,1fr)}.ew-hero{flex-direction:column;align-items:flex-start}.ew-hero-right{flex:none;width:100%;text-align:left;border-left:none;border-top:1px solid rgba(164,193,211,.14);padding-top:14px}.block-container{padding:2.8rem .75rem 1.8rem!important}}
/* Designed empty state — a card with steps, not a bare blue notice */
.ew-empty{padding:24px 22px;border:1px dashed rgba(126,232,214,.4);border-radius:16px;background:linear-gradient(135deg,rgba(16,42,61,.85),rgba(9,24,36,.85));margin:10px 0 14px}
.ew-empty h3{margin:0 0 8px;font-size:1.05rem}
.ew-empty p{color:#b0c2ce;font-size:.85rem;line-height:1.7;margin:0 0 6px}
.ew-empty .ew-step{color:#e8f1f5;font-size:.82rem;font-weight:600;margin-top:10px}
.ew-assistant-cap{padding:16px 18px;border:1px solid var(--border);border-radius:12px;background:var(--surface)}
.ew-assistant-cap b{color:#7ee8d6;font-size:.66rem;letter-spacing:.12em;text-transform:uppercase}
.ew-assistant-cap ul{margin:8px 0 0;padding-left:18px;color:#b0c2ce;font-size:.82rem;line-height:1.8}
"""
