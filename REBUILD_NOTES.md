# EARTHWISE AI — Premium Rebuild Notes

Built 2026-11-14 for the NASA Space Apps Hackathon (demo: 2026-11-15).
Original repo inspected in full: `app/main.py` (768 lines), `src/*.py` (9 files),
`tests/*.py`, `docs/*.md`, `requirements.txt`, `runtime.txt`.

## What was preserved — untouched
- `src/nasa_power.py`, `src/cleaning.py`, `src/statistics.py`, `src/anomalies.py`,
  `src/ai_engine.py`, `src/live_weather.py`, `src/regions.py`, `src/comparisons.py`
  — byte-for-byte logic preserved. No backend behaviour changed.
- Data model: no database. Raw NASA POWER CSV + JSON metadata in `data/raw/`
  (git-ignored, as in the original). No user data existed in the repo to migrate.
- All real APIs, no fake data: NASA POWER, Open-Meteo weather, NASA GIBS,
  Globe.gl / Leaflet. No sample / synthetic numbers anywhere in the UI.

## What was added
| Module | Purpose | Data |
|---|---|---|
| `src/air_quality.py` | **NEW — Air Quality page**: live US AQI gauge, PM2.5/PM10, O₃, NO₂, SO₂, CO, European AQI, dominant pollutant, 24 h PM2.5 chart | Open-Meteo Air Quality API (CAMS), free, **no key** |
| `src/risk.py` | **NEW — Risk & Outlook**: composite screening score from Sen slope + latest anomaly + live heat + live AQI; 10-year straight-line Sen-slope projection with 95% CI | Derived only from already-computed real data |
| `src/ai_assistant.py` | **NEW — AI Assistant page**: evidence-bound, rule-based assistant. Answers weather / AQI / trend / anomaly / risk / forecast / sources only from data loaded on the page; says when data is missing instead of inventing it | No LLM, no key, no hallucination |
| `app/main.py` | **REWRITTEN — premium SaaS dashboard**: sidebar navigation (7 pages), glass/KPI cards, animated live indicator, responsive mobile layout, reduced-motion support, loading spinners, `safe()` error handling on every live call, multi-city comparison (real fetches, max 3), 12-month rolling mean, downloads on every page | Same Streamlit 1.66 stack |
| `tests/test_new_modules.py` | 5 new tests (AQI bands, dominant pollutant, risk, projection, assistant) | — |
| `.streamlit/config.toml` | Dark theme, headless server defaults | — |
| `.env.example` | Documents the one optional variable | — |

## Pages
1. **Overview** — hero, 4 live KPIs (temp / AQI / trend / risk), current conditions + AQI snapshot, climate preview
2. **Climate Analytics** — coverage, Sen slope, Kendall p, time series, 12-month rolling mean, seasonal anomalies, AI Earth Scientist, compare up to 3 cities
3. **Air Quality** — US AQI gauge, pollutant cards, 24 h PM2.5 chart, EPA bands
4. **Weather & Maps** — 7-day forecast cards, 24 h temperature, national conditions map, 3D globe, NASA GIBS satellite (VIIRS / IMERG), city directory
5. **AI Assistant** — chat with suggested questions, evidence-bound answers
6. **Risk & Outlook** — composite screening, 10-year Sen-slope projection chart + table + CSV
7. **Data & Downloads** — monthly table, CSV downloads, API/configuration table

## Live animations — 2026-11-14 (last work before submission)
New module `src/animations.py` (pure helpers, no new dependencies, CSS only):
- **Live ticker** — Overview + Weather & Maps: scrolling strip of REAL live values for the selected city (temperature, condition, US AQI, PM2.5, provider time). CSS `translateX` marquee, pauses on hover, duplicates items for a seamless loop. Missing values are omitted, never faked.
- **Animated hero** — shimmering gradient + floating weather symbol that changes with the real Open-Meteo `weather_code` (clear = slow spin, cloud = drift, rain = falling, snow = gentle float, storm = flicker, fog = fade).
- **KPI cards** — fade/slide-up on load, staggered 0 / 80 / 160 / 240 ms on Overview; LIVE dot pulses stronger (`livePulse`); all Plotly charts fade in.
- **Live clock** — "LIVE · Updated <provider time> · Open-Meteo / CAMS" line under the hero.
- All animations respect the existing `@media (prefers-reduced-motion: reduce)` rule and the mobile `max-width: 700px` layout. No JavaScript, so nothing new breaks old Chrome beyond what Streamlit 1.66 already does.

## Button audit — 2026-11-14 (all buttons checked with Streamlit AppTest, real runs)
| Button / control | What it does | Result |
|---|---|---|
| Sidebar "Retrieve climate data" | Fetches NASA POWER for city + indicator + period, saves CSV, toast on success | PASS by code + shared fetch verified live via Compare (Retrieve itself not clicked live, to avoid overwriting the 2015–2025 Lahore demo CSV) |
| Sidebar "Refresh live weather / AQI" | Clears live caches, reruns, toast "Live weather / AQI refreshed" | **FIXED** — my first toast used icon `↻`, which Streamlit rejects as not an emoji and raised `StreamlitAPIException`; changed to 🌍, re-tested, toast now shows |
| Sidebar city search | Filters city list | **FIXED** — a non-matching search used to `st.stop()` and blank the whole app; now warns and shows all cities |
| Sidebar navigation radio, province/city/indicator selectboxes, year inputs | Switch page / city / indicator / period | PASS — all 7 pages render, no exception |
| Climate Analytics "Compare selected cities" | Fetches up to 3 cities live, shows Sen slope table | **FIXED** — with no city selected it silently did nothing; now warns "Select at least one city first" and toasts on success. Live test: Lahore −1.34/decade vs Karachi +0.20/decade |
| AI Assistant 4 suggested questions | Append Q + evidence-bound answer | PASS — tested, answer shows real AQI 173 |
| AI Assistant chat input | Asks free question, answers from loaded data only | PASS — tested, answered with real AQI 173 — Unhealthy |
| AI Assistant "Clear conversation" | Clears chat, reruns | PASS |
| Weather & Maps download snapshot CSV | Downloads national city weather CSV | PASS — now shows an info message instead of nothing when the national map fails to load |
| Risk "Download 10-year projection (CSV)" | Downloads projection CSV | PASS |
| Data & Downloads monthly / anomalies / projection CSVs | Download CSVs | PASS — missing-data cases now show a caption ("unavailable — needs a valid trend") instead of a silently missing button |
| Tabs, selectboxes, slider, date input (Weather & Maps) | Switch layers / opacity / satellite date | PASS |

**Other bugs found & fixed:** (1) `meta` could be `None` after a failed climate analysis while pages still read `meta['first_date']` → crash; now the app shows the fetch prompt instead. (2) Risk page could read `risk['scores']` when `risk` was `None`; now guarded with an error + stop. (3) Weather hourly chart read `forecast["hourly"]` directly → `KeyError` if missing; now guarded with try/except + empty-data message. (4) `proj_df.round(3)` / `anomaly_df.round(3)` warned on datetime columns; now round numeric columns only. (5) Overview trend KPI printed `p=None` when p-value was unavailable; now prints "p unavailable".

**Still open / not a bug:** (a) Streamlit 1.66 prints a deprecation warning that `use_container_width` will be removed after 2025-12-31 — harmless on the pinned 1.66.0, but the app should migrate to `width='stretch'` before upgrading Streamlit. (b) On old Chrome (<110) Streamlit's own frontend still shows `Object.keys(...).toSorted is not a function` — that is the browser, not this app; update Chrome or use Edge / a phone. (c) The 3D globe and GIBS satellite tiles need internet/CDN access; they degrade to a message when offline.

## Interface polish — 2026-11-14
Same dark premium weather.com-like look (`#7ee8d6` / `#060f18`), no new dependencies: KPI/chart entrance animations use `backwards` fill so hover lift still works after the animation; buttons get a press scale (0.98) + visible focus outline; cards get a subtle hover border; download buttons are full-width; `.ew-sub2` contrast raised to `#b0c2ce`; "Compare selected cities" is now the primary button on that section. Mobile layout unchanged and checked at `max-width: 700px` (ticker + hero symbol shrink).

## Verified live test — 2026-11-14 01:30 PKT (real, not sample)
- Open-Meteo Lahore: **19.2 °C**, 70% humidity, feels like 19.5 °C, weather code 0 (Clear sky), wind 6.1 km/h, provider time 2026-11-14T01:30
- Open-Meteo Air Quality Lahore: PM2.5 **62.4 µg/m³**, PM10 72.9, **US AQI 173 — Unhealthy**, European AQI 66
- NASA POWER live (2025-01-01 → 2025-06-30): 181 rows, T2M mean 25.96 °C — API reachable
- NASA POWER Lahore T2M 2015-01-01 → 2025-12-31 (cached demo file): 4,018 rows, **100% coverage**, 132 monthly obs
- Trend: **decreasing, Sen slope −1.34 °C/decade, Kendall p = 0.52 (not significant)** — report this honestly; the simple test does not correct for seasonality/autocorrelation, and the result depends on the period chosen. Do NOT claim a warming trend for Lahore from this run.
- Latest anomaly (Dec 2025): +0.58 °C vs same-month mean in the selected dataset
- Risk composite for that run: 29.4/100 — Moderate (driven mainly by AQI)
- `pytest`: **17 passed** (11 original + 6 new animation tests)
- `streamlit run app/main.py`: **HTTP 200**, server log clean, no errors/tracebacks; Streamlit AppTest ran all 7 pages with **no exception**
- Open-Meteo Lahore: 19.4 °C, 69% humidity — live
- Open-Meteo Air Quality Lahore: PM2.5 67.8 µg/m³, PM10 77.8, **US AQI 175 — Unhealthy**
- NASA POWER Lahore T2M 2015-01-01 → 2025-12-31: 4,018 rows, **100% coverage**, 132 monthly obs
- Trend: **decreasing, Sen slope −1.34 °C/decade, Kendall p = 0.52 (not significant)** — report this honestly; the simple test does not correct for seasonality/autocorrelation, and the result depends on the period chosen. Do NOT claim a warming trend for Lahore from this run.
- Latest anomaly (Dec 2025): +0.58 °C vs same-month mean in the selected dataset
- Risk composite for that run: 29.4/100 — Moderate (driven mainly by AQI)
- `pytest`: **11 passed** (6 original + 5 new)
- `streamlit run app/main.py`: **HTTP 200**, no errors in the server log

A demo dataset is included: `data/raw/lahore_t2m_nasa_power_daily.csv` (+ metadata JSON), so the
Analytics / Risk pages load instantly for Lahore + T2M without a fetch. Delete it to start clean.

## APIs & credentials — what you need
| Service | Key needed? |
|---|---|
| NASA POWER | No |
| Open-Meteo weather (evaluation) | No |
| Open-Meteo Air Quality (CAMS) | No |
| NASA GIBS | No |
| **Open-Meteo commercial** | **Only `OPEN_METEO_API_KEY` — needed ONLY if you run this commercially / monetise it.** Set it as an env var or in Streamlit Cloud Secrets. Never commit it. Without it the app uses the free evaluation endpoint, exactly as the original did. |

**No other credentials are missing. There is no database password, no NASA key, no LLM key.**

## Run / deploy
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app/main.py        # http://localhost:8501
python -m pytest tests/ -q                 # 25 passed (2026-11-14, incl. intro splash)
```
Streamlit Cloud: repo → branch `main` → main file `app/main.py` (Python 3.12, see `runtime.txt`).
Optional secret: `OPEN_METEO_API_KEY` (commercial use only).

## Honest limitations (keep these in your demo)
- NASA POWER = gridded/model estimates, not station observations.
- Open-Meteo weather/AQI = model (CAMS) estimates, not station measurements.
- Trend test = simple Kendall + Sen; no seasonality / autocorrelation correction.
- Risk = screening signal, not a PMD/health warning, flood forecast or disaster alert.
- 10-year outlook = straight-line extrapolation, not a climate-model projection.
- GIBS imagery = satellite tiles, not live video.

## Opening intro splash (2026-11-14 01:48 PKT)
- Full-screen intro on app open, instead of a blank loading screen: spinning globe with orbiting dot, EARTHWISE AI title, 'Pakistan Earth Intelligence', loading bar, sources NASA POWER / Open-Meteo / CAMS / NASA GIBS.
- Pure CSS, no JavaScript, no fake data. Shows once per session (~3s), then the main app loads. Reduced-motion users see a near-static splash.
- Files: src/animations.py (INTRO_CSS + intro_html), app/main.py (wired in), tests/test_animations.py (new test).
