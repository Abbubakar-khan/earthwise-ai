# EARTHWISE AI — The Intelligent Earth Trend Observatory
**FORGE CYBER LAB | Pakistan-first | NASA Space Apps 2026**

EARTHWISE AI is a research prototype for exploring environmental time-series, estimating trends, comparing locations, and explaining computed results with transparent caveats.

## Important status
This package is a **reproducible starter implementation**, not proof that all live data have already been downloaded or that every module has been independently validated against ground stations. The app fetches NASA POWER data at runtime. GPM IMERG and MODIS are documented as next-stage integrations; they are not falsely represented as already integrated.

## Quick start (Android/mobile)
You can inspect/edit files on mobile, but running Python + Streamlit locally is awkward. Use **GitHub Codespaces** or **Replit** in your mobile browser:
1. Create a GitHub repository named `earthwise-ai`.
2. Upload/extract this ZIP into the repository.
3. Open the repo in Codespaces (or import into Replit).
4. In the terminal run:
   ```bash
   pip install -r requirements.txt
   streamlit run app/main.py --server.address 0.0.0.0
   ```
5. Open the forwarded Streamlit port (usually 8501).
6. Select a city, fetch NASA POWER data, then run the trend analysis.

## Local setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

## Project structure
- `app/main.py`: Streamlit interface
- `src/nasa_power.py`: NASA POWER daily API client
- `src/cleaning.py`: validation and monthly aggregation
- `src/statistics.py`: Mann–Kendall-style Kendall tau test + Sen slope
- `src/comparisons.py`: multi-location trend table
- `src/ai_engine.py`: evidence-constrained explanation templates
- `docs/`: methodology, sources, validation and roadmap
- `tests/`: automated tests

## Science safeguards
- POWER point values are gridded/reanalysis-derived products, not local weather-station observations.
- Temperature and precipitation are analyzed separately.
- Daily precipitation is summed to monthly totals; daily temperature is averaged to monthly means.
- Mann–Kendall significance can be affected by seasonality/autocorrelation. The MVP reports a simple Kendall tau p-value and Sen slope; it does **not** claim a seasonality-corrected trend test.
- A trend is not a forecast, and correlation does not prove causation.
- Missing/sentinel values are excluded; the app reports coverage.
- The AI explanation uses only computed result fields; it does not invent causes.

## Current supported scope
NASA POWER daily point data for Lahore, Islamabad, Karachi (T2M and PRECTOTCORR). Add other sources only after this core path is stable.
