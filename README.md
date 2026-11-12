# EARTHWISE AI — Earth Intelligence Platform

**Pakistan-first climate intelligence · Research product**

EARTHWISE AI is a Pakistan-first platform for exploring historical climate evidence, model-based current conditions, NASA satellite imagery, and conversational Earth-science assistance.

## Product workspaces

- **Mission Control:** location overview, model-based current conditions, selected dataset summary, and a clear entry point into the platform.
- **Climate Intelligence:** NASA POWER historical data, monthly aggregation, coverage metrics, time-series visualization, Kendall tau, Sen's slope, confidence interval display, methodology and CSV exports.
- **AI Earth Scientist:** a conversational assistant that can explain climate concepts and interpret the selected location and loaded dataset. It uses the OpenAI Responses API with a server-side API key supplied by the app owner.
- **Earth Explorer:** interactive textured 3D Earth, date-selectable NASA GIBS VIIRS imagery, and a Pakistan city atlas. Only the selected visualization is mounted to reduce unnecessary browser work.
- **Data Library:** inspect and export daily and monthly records with source metadata.

## Data coverage and limitations

- The catalogue contains 101 mapped urban centres across Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, Islamabad Capital Territory, Gilgit-Baltistan and Azad Jammu & Kashmir. It is not the complete 657-locality PBS 2023 directory. Coordinates are approximate city-centre points for gridded data extraction.
- Seven NASA POWER variables are supported: mean, maximum and minimum 2 m air temperature; relative humidity; corrected precipitation; 10 m wind speed; and all-sky surface shortwave irradiance.
- NASA POWER point values are gridded satellite/model-assisted estimates, not measurements from a local weather station.
- Daily precipitation is summed into monthly totals; other supported daily variables are averaged into monthly means.
- The current Kendall trend test does not correct for monthly seasonality or serial autocorrelation. Interpret p-values cautiously.
- Historical trends are not forecasts, climate projections, attribution studies, or disaster predictions.
- NASA GIBS VIIRS imagery is a satellite-derived daily composite, not live video. Cloud cover, acquisition gaps and processing latency can affect imagery availability.
- Open-Meteo current conditions are model-based estimates, not guaranteed local station observations or emergency-grade warnings. Requests are cached for 15 minutes. See [Open-Meteo documentation](https://open-meteo.com/en/docs).
- The no-key Open-Meteo endpoint is for non-commercial evaluation only. Before commercial operation, configure `OPEN_METEO_API_KEY` with a valid commercial subscription. See [Open-Meteo pricing and terms](https://open-meteo.com/en/pricing).
- Conversational AI is an API-powered feature, not a separately trained EARTHWISE foundation model. The assistant can make mistakes and must not be used as an emergency authority or as independent scientific validation.

## Configure private app secrets

In Streamlit Community Cloud, open **App settings → Secrets** and add the following TOML entries:

```toml
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_MODEL = "gpt-4.1-mini"

# Optional: only when using an eligible Open-Meteo commercial subscription
OPEN_METEO_API_KEY = "your-open-meteo-commercial-key"
```

The OpenAI key activates the conversational AI. Without it, the rest of the application remains usable and the AI workspace displays setup instructions. Never paste keys into source code, commit them to GitHub, or share them in chat. API usage is billed by the provider under the account that owns the key.

Create an OpenAI API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and review [API billing](https://platform.openai.com/settings/organization/billing).

## Run locally

Python 3.12–3.14 is supported by the current dependency set.

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app/main.py
```

For local secrets, create `.streamlit/secrets.toml` (do not commit it):

```toml
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_MODEL = "gpt-4.1-mini"
```

## Deploy on Streamlit Community Cloud

1. Connect the GitHub repository `Abbubakar-khan/earthwise-ai`.
2. Select the deployment branch configured for the release.
3. Set the main file path to `app/main.py`.
4. Select Python 3.12 in Advanced settings.
5. Add the private secrets above in **App settings → Secrets**.
6. Deploy and inspect the app logs and the live UI after startup.

The app requires outbound internet access for NASA POWER, Open-Meteo, NASA GIBS tiles, the globe CDN, and the configured AI provider.

## Project structure

- `app/main.py`: Streamlit product interface and navigation
- `src/ai_assistant.py`: server-side conversational AI integration
- `src/ai_engine.py`: evidence-constrained statistical explanation
- `src/regions.py`: Pakistan city coordinates and climate variables
- `src/nasa_power.py`: NASA POWER API client
- `src/live_weather.py`: Open-Meteo current model conditions
- `src/cleaning.py`: missing-value handling and monthly aggregation
- `src/statistics.py`: Kendall tau and Sen's slope
- `tests/`: core calculation tests

## Planned work

Full PBS locality coverage, verified multi-source disaster feeds, multi-city comparisons, seasonal/autocorrelation-aware trend methods, scenario modelling, user accounts, and production observability are not implemented yet. Any future hazard feed must display official source, event timestamp, freshness, uncertainty, and clear instructions to follow local authorities.
