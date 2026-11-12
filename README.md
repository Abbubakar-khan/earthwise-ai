# EARTHWISE AI — The Intelligent Earth Trend Observatory

**FORGE CYBER LAB | Pakistan-first | Research prototype**

EARTHWISE AI is a Pakistan-first climate data explorer. It retrieves historical daily point data from NASA POWER, aggregates the selected variable to monthly values, calculates a simple trend, and provides a cautious plain-language explanation.

## Current MVP features

- Nine Pakistan locations: Islamabad, Lahore, Karachi, Peshawar, Quetta, Faisalabad, Multan, Skardu and Gilgit.
- Seven NASA POWER variables: mean, maximum and minimum 2 m air temperature; relative humidity; corrected precipitation; 10 m wind speed; and all-sky surface shortwave irradiance.
- Historical date-range selection and NASA POWER API retrieval.
- Monthly aggregation, data-coverage reporting, trend visualization, Kendall tau p-value and Sen's slope.
- Downloadable monthly CSV and local raw-data/metadata files.

## Important scientific limitations

- NASA POWER point values are gridded satellite/model-assisted estimates, not measurements from a local weather station.
- This MVP analyzes historical data. It is not a weather forecast, climate projection, or disaster prediction system.
- Daily precipitation values are summed into monthly totals. Other supported daily variables are averaged into monthly means.
- The simple Kendall trend test does not correct for monthly seasonality or serial autocorrelation. Interpret p-values cautiously.
- The AI explanation is based on computed trend fields; it should not be treated as an independent scientific validation.
- Data availability and completeness depend on NASA POWER. Recent dates may be incomplete.

## Run locally

Python 3.12–3.14 is supported by the current deployment dependency set. Streamlit Community Cloud currently defaults to Python 3.12; if creating a fresh deployment, select Python 3.12 in Advanced settings for the most conservative option.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app/main.py
```

Then open the local URL shown in the terminal, normally http://localhost:8501.

On Windows, the Python launcher can be used instead:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app/main.py
```

## Deploy on Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with the GitHub account that can access this repository.
2. Create a new app and select repository `Abbubakar-khan/earthwise-ai`.
3. Select branch `compat/streamlit-launch`.
4. Set the main file path to `app/main.py`.
5. Deploy. The first run installs the dependencies and may take several minutes.

The app fetches NASA POWER data when a user presses the fetch button, so the deployed app needs outbound internet access. Do not commit passwords, tokens, or private API keys.

## Project structure

- `app/main.py`: Streamlit interface
- `src/regions.py`: Pakistan city coordinates and supported variables
- `src/nasa_power.py`: NASA POWER daily API client and local CSV/metadata saving
- `src/cleaning.py`: missing-value handling and monthly aggregation
- `src/statistics.py`: Kendall tau and Sen's slope
- `src/ai_engine.py`: evidence-constrained explanation templates
- `tests/`: core calculation tests
- `docs/`: methodology, sources, validation and roadmap

## Roadmap (not yet implemented)

Interactive 3D globe, satellite imagery layers, earthquake/fire/flood monitoring, forecast feeds, historical city comparisons, and future climate scenarios are planned modules. They must be integrated with clear source attribution and uncertainty labels before being presented as operational features.
