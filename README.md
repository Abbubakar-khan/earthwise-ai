# EARTHWISE AI — The Intelligent Earth Trend Observatory

**FORGE CYBER LAB | Pakistan-first | Research prototype**

EARTHWISE AI is a Pakistan-first climate data explorer. It retrieves historical daily point data from NASA POWER, aggregates the selected variable to monthly values, calculates a simple trend, and provides a cautious plain-language explanation.

## Current MVP features

- Searchable directory of 101 mapped urban centres across Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, Islamabad Capital Territory, Gilgit-Baltistan and Azad Jammu & Kashmir. Coordinates are approximate city-centre points for NASA POWER grid extraction. This is not the complete set of 657 urban localities recorded by the PBS 2023 Census; locality names and validated point coordinates are separate data tasks.
- PBS 2023 Census reference: [National Census Report](https://www.pbs.gov.pk/sites/default/files/population/2023/reports/National%20Census%20Report-2023.pdf) and [Table 2 — Urban Localities](https://www.pbs.gov.pk/wp-content/uploads/census_tables/tables/table_2_national.pdf).
- Seven NASA POWER variables: mean, maximum and minimum 2 m air temperature; relative humidity; corrected precipitation; 10 m wind speed; and all-sky surface shortwave irradiance.
- Province/region filtering, searchable city selection, a Pakistan-wide model-weather map with temperature, rainfall, humidity and wind layers across the mapped city directory, and a textured, rotatable 3D Earth globe with city markers.
- NASA GIBS VIIRS Suomi-NPP corrected-reflectance true-colour daily satellite imagery, date-selectable and overlaid with Pakistan city markers.
- Model-based current weather conditions from Open-Meteo (temperature, apparent temperature, humidity, wind, precipitation and cloud cover), cached for 15 minutes.
- Seven-day daily model forecast and next-24-hour temperature outlook from Open-Meteo, cached for 30 minutes and refreshed with the weather refresh control. A separate 20-minute cached multi-city snapshot powers the Pakistan weather map.
- Premium responsive weather-dashboard interface with ordered weather, forecast, Earth observation and climate-analysis sections, subtle motion, hover states, and reduced-motion accessibility.
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
- Open-Meteo current conditions are model-based estimates, not guaranteed local weather-station observations or emergency-grade warnings. The provider timestamp and source are displayed in the app; requests are cached for 15 minutes. See [Open-Meteo documentation](https://open-meteo.com/en/docs).
- The no-key Open-Meteo endpoint is only for non-commercial evaluation. Before commercial operation, configure the `OPEN_METEO_API_KEY` environment variable using a valid commercial subscription. See [Open-Meteo pricing and commercial terms](https://open-meteo.com/en/pricing). Weather data attribution is required under CC BY 4.0.
- NASA GIBS VIIRS imagery is a satellite-derived daily composite, not live video. Cloud cover, acquisition gaps and processing latency can affect the image. See [NASA GIBS access documentation](https://nasa-gibs.github.io/gibs-api-docs/access-basics/).

## Run locally

The deployment is pinned to Python 3.12 in `runtime.txt`. Use Python 3.12 locally for the closest match to the deployed environment.

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
3. Select branch `main` (the maintained deployment branch).
4. Set the main file path to `app/main.py`.
5. Deploy. The first run installs the dependencies and may take several minutes.

The app fetches NASA POWER data when a user presses the fetch button, so the deployed app needs outbound internet access. Do not commit passwords, tokens, or private API keys. For commercial weather use, add `OPEN_METEO_API_KEY` to Streamlit Community Cloud app Secrets (TOML format) or the deployment environment; never put the key in Git. Without a commercial key, the weather panel uses the non-commercial evaluation endpoint only.

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

Earthwise now includes a 3D globe, NASA GIBS satellite imagery and model-based current weather. Earthquake/fire/flood alert feeds, validated full PBS urban-locality coverage, multi-city comparisons, rigorous seasonal trend methods and future climate scenarios remain planned modules. The animated system status is a visual UI indicator, not a claim of live environmental telemetry.
