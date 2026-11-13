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

## Verified live test — 2026-11-14 00:30 PKT (real, not sample)
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
python -m pytest tests/ -q                 # 11 passed
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
