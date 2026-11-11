# EARTHWISE AI — Research Freeze & Implementation Runbook
Date: 2026-11-12
Repository: https://github.com/Abbubakar-khan/earthwise-ai
Purpose: Freeze research decisions so the next work session starts with implementation, not repeated planning.

## 1. Current verified baseline (repository inspection)
- NASA POWER daily point client exists: `src/nasa_power.py`.
- Streamlit app exists: `app/main.py`.
- Cleaning/aggregation, trend statistics, comparisons and deterministic explanation modules exist.
- Existing tests passed in the latest recorded CI run (see project checkpoint).
- No verified live Lahore/Islamabad/Karachi datasets are stored in the repository.
- GPM IMERG and MODIS NDVI/EVI are research-planned only, not integrated.
- The app and API have not yet been locally run and verified in this session.

## 2. Frozen MVP scope
First deliverable: a working, reproducible Pakistan-first environmental trend explorer for three pilot point locations:
- Lahore: 31.5204, 74.3587
- Islamabad: 33.6844, 73.0479
- Karachi: 24.8607, 67.0011

Period requested: 2001-01-01 to 2025-12-31. Always display actual returned coverage, not just requested dates.
Core variables:
- NASA POWER T2M: monthly mean of daily values (°C; confirm response metadata).
- NASA POWER PRECTOTCORR: monthly sum of daily precipitation values (confirm units/metadata before display).

Do not label point samples as district, province, or national averages. Broader geography requires official boundaries and defensible spatial aggregation.

## 3. Data-source decisions
### Core: NASA POWER Daily Point API
- Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point
- Use `time-standard=UTC` explicitly (API otherwise defaults to LST).
- Daily data documented from 1981-01-01 to near-real-time.
- Maximum 20 parameters per single-point request; regional requests limited to one parameter.
- Preserve raw JSON if practical, normalized CSV, request URL, retrieval timestamp, coordinates, parameter codes, requested and actual date range, units and coverage/missingness.
- Existing code requests T2M and PRECTOTCORR together and converts values <= -900 to missing. Verify actual API response, units, headers and date range at runtime.
- Do not repeatedly hammer the same point/API; cache successful downloads and reuse them.

### Secondary precipitation: NASA GPM IMERG V07
- Product: IMERG V07; half-hourly 0.1° x 0.1° fields (~10 km).
- Early and Late are near-real-time streams; Final is satellite-gauge product and arrives about 3.5 months after month end.
- For historical comparison prefer Final where available; record product/run type and version.
- Aggregate half-hourly rates/accumulations only according to the product variable's documented units; never assume units.
- Treat as an independent precipitation perspective, not ground truth. Compare against POWER and available gauges where possible.
- Integration deferred until POWER MVP is verified.

### Vegetation: MODIS Terra MOD13Q1 V061
- NDVI and EVI, 250 m, 16-day composite; quality layers included.
- Apply DetailedQA quality masking before calculating summaries.
- Apply scale factor 0.0001 to NDVI/EVI after handling fill values and QA.
- Use area-weighted valid-pixel summaries for a named boundary; point/pixel results must be labelled as such.
- Integration deferred until core app is stable.

### Optional context: NASA FIRMS
- Active-fire/thermal-anomaly detections from MODIS/VIIRS; optional context only.
- A hotspot is not proof of a fire at the full pixel footprint; clouds, view geometry and confidence affect detections.
- Never use FIRMS for life/property safety decisions or claim it is a fire alarm.
- Not part of MVP.

## 4. Statistical method — honest MVP and next upgrade
MVP already implemented:
- Daily -> monthly aggregation: T2M mean; precipitation sum.
- Trend magnitude: Theil-Sen slope, reported per year and per decade with 95% interval.
- Direction/significance: Kendall tau test, nominal p < 0.05.
- Minimum 24 valid monthly observations in current function.
- Always report n, actual first/last month, missingness/coverage, units and caveat.

Important limitations:
- Ordinary Kendall test assumes serial independence; monthly seasonal structure and autocorrelation are not automatically removed by monthly aggregation.
- The current p-value is unadjusted; do not describe it as seasonality- or autocorrelation-corrected.
- For the next scientific upgrade: inspect seasonal Mann-Kendall or monthly-season stratification, assess autocorrelation and apply an appropriate variance correction/pre-whitening sensitivity analysis; use Benjamini-Hochberg FDR when testing many locations/variables/pixels.
- Precipitation is skewed/intermittent: include distribution/quantiles and extremes, not trend slope alone.
- No causal inference, no guaranteed forecast, no operational warning claim.

## 5. Earth Trend Fingerprint™ definition
For each location and variable, display:
- Direction: increasing / decreasing / approximately stable.
- Magnitude: Sen slope per decade with units.
- Statistical result: nominal significant / not significant / insufficient.
- Confidence interval and valid observation count.
- Data coverage/quality: good / limited / insufficient, using explicit thresholds defined during implementation.
- Source, spatial support and analysis period.
Never collapse temperature, precipitation and vegetation into one opaque score without a documented normalization/weighting scheme.

## 6. Seven components — exact implementation order
1. NASA POWER collection: run cached live fetch for each pilot city; inspect units, metadata, missing values and dates.
2. Data cleaning: validate date continuity, duplicates, sentinels, missingness and monthly aggregation.
3. Hidden Trend Detective: run tests on verified data; expose slope, interval, tau, p-value and caveats.
4. Pakistan Explorer: show pilot locations first; label point data accurately. Add boundaries only when verified.
5. Earth Trend Fingerprint: connect computed outputs and quality flags; no hard-coded example results.
6. AI Earth Scientist: deterministic evidence-grounded narrative only; every statement traceable to computed values; say when evidence is insufficient.
7. Streamlit dashboard: run end-to-end, handle API errors/loading/cache, test comparison, export and mobile layout.

## 7. Next work session — no repeated research
A. Check environment and install dependencies.
B. Run `python -m pytest -v`.
C. Run app and fetch Lahore only.
D. Inspect raw response, units, date range, missingness; save raw JSON + CSV + metadata.
E. Repeat Islamabad and Karachi, caching results.
F. Generate monthly processed tables and trend outputs.
G. Wire the 3-city results into fingerprint, explanations and dashboard.
H. Re-run tests and record screenshots/logs/results.
I. Only after this baseline works, decide whether time permits IMERG/MODIS integration.

Suggested commands:
```bash
python --version
git clone https://github.com/Abbubakar-khan/earthwise-ai.git
cd earthwise-ai
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
streamlit run app/main.py
```
If the laptop OS/Python version is unsupported, do not waste time forcing installs; use a compatible cloud dev environment (e.g. Codespaces) after checking access.

## 8. Data storage and backup
- Raw/processed files are excluded by `.gitignore` under `data/raw/*` and `data/processed/*`.
- Keep reproducible research notes and code in GitHub.
- Keep downloaded raw datasets in a separate local backup/cloud drive; record checksums if possible.
- Do not commit large raw datasets without checking repository size, licensing and policy.
- Never place secrets/API keys in the repository.

## 9. Competition integrity
- 2026 participant terms page: https://www.spaceappschallenge.org/legal/
- Participant's specific question about pre-existing codebase use is awaiting organizer clarification.
- Do not infer permission or prohibition from generic terms alone. Keep the email and response; follow organizer's written guidance and disclose existing code honestly if required.
- Solo participation and pre-existing-code permission are separate questions.

## 10. Judge-safe claims
Safe: "EARTHWISE AI analyzes NASA Earth-observation-derived time series and explains observed historical trends with transparent uncertainty and data limitations."
Not safe until proven: "real-time AI prediction", "district-level coverage", "NASA-validated", "predicts disasters", "all Pakistan live monitoring", "vegetation and GPM fully integrated".
Current app uses deterministic evidence-constrained explanations, not a generative LLM.

## 11. Primary references (official / technical)
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA POWER parameter list: https://power.larc.nasa.gov/docs/services/api/temporal/
- NASA POWER multi-point tutorial: https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/
- NASA GPM IMERG V07 technical documentation: https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation
- NASA GPM documents / latest ATBD listing: https://gpm.nasa.gov/resources/documents
- MODIS MOD13Q1 V061 catalogue and QA/scale information: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1
- NASA Earthdata MOD13Q1 V061: https://doi.org/10.5067/MODIS/MOD13Q1.061
- NASA FIRMS API: https://firms.modaps.eosdis.nasa.gov/api/
- NASA FIRMS active-fire limitations: https://firms.modaps.eosdis.nasa.gov/map/
- NASA Space Apps 2026 terms: https://www.spaceappschallenge.org/legal/
- Mann-Kendall / Sen slope autocorrelation and seasonality discussion: https://amt.copernicus.org/articles/13/6945/2020/
- Australian Government monitoring guidance on rank-based trends/autocorrelation: https://www.waterquality.gov.au/anz-guidelines/monitoring/data-analysis/data-assess-change

---
This document freezes the research decisions; it does not claim that integrations, live retrieval, or runtime validation have already happened.
