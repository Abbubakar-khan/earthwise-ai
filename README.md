# EARTHWISE AI — Earth Intelligence Platform

**Pakistan-first climate intelligence · Research product**

EARTHWISE AI is a Pakistan-first platform for exploring historical climate evidence, model-based current conditions, NASA satellite imagery, and conversational Earth-science assistance.

## Product workspaces

- **Mission Control:** location overview, model-based current conditions, selected dataset summary, and a clear entry point into the platform.
- **Climate Intelligence:** NASA POWER historical data, monthly aggregation, coverage metrics, time-series visualization, Kendall tau, Sen's slope, confidence interval display, methodology and CSV exports.
- **AI Earth Scientist:** a conversational assistant that can explain climate concepts and interpret the selected location and loaded dataset. It prefers the branch-scoped Neon AI Gateway and supports a server-side direct OpenAI Responses API fallback; provider credentials are supplied privately by the app owner.
- **Earth Explorer:** interactive textured 3D Earth, date-selectable NASA GIBS VIIRS imagery, and a Pakistan city atlas. Only the selected visualization is mounted to reduce unnecessary browser work.
- **Data Library:** inspect and export NASA POWER records; upload, validate, privately store, reopen, download and delete user datasets in CSV, Excel (`.xlsx`, `.xls`, `.xlsm`) and JSON formats. Uploads are stored as PostgreSQL JSONB records, not on the ephemeral app filesystem.

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
# Preferred: Neon AI Gateway (branch-scoped credential)
NEON_AI_GATEWAY_BASE_URL = "https://YOUR-BRANCH-api.ai.YOUR-REGION.aws.neon.tech"
NEON_AI_GATEWAY_TOKEN = "your-neon-scoped-credential"
NEON_AI_MODEL = "gpt-5-mini"

# Required for persistent uploads; use your Neon PostgreSQL connection string
EARTHWISE_DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"

# Optional fallback if Neon AI Gateway is not configured
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_MODEL = "gpt-4.1-mini"

# Optional: only when using an eligible Open-Meteo commercial subscription
OPEN_METEO_API_KEY = "your-open-meteo-commercial-key"
```

When both Neon Gateway settings are present, conversational AI uses the branch-scoped Neon AI Gateway; otherwise it falls back to the direct OpenAI Responses API when `OPENAI_API_KEY` is present. The rest of the application remains usable if neither AI provider is configured. The Gateway base URL is the bare host; the app adds `/openai/v1/responses`. Use a model ID enabled for your branch (check the branch's `/v1/models` catalog). Never paste keys into source code, commit them to GitHub, or share them in chat. Gateway usage draws down the Neon organization's prepaid AI credits; direct OpenAI usage is billed by OpenAI.

Create a Neon scoped credential with the `ai_gateway:invoke` capability for the app's branch. Keep its token private. For direct OpenAI fallback, create a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and review [API billing](https://platform.openai.com/settings/organization/billing).

## Persistent user dataset storage

User uploads require a hosted PostgreSQL database. Streamlit Community Cloud's local filesystem is not a durable database, so EARTHWISE AI does not claim persistence when this setting is absent.

1. Create a PostgreSQL database with a managed provider such as [Neon](https://neon.tech/) or [Supabase](https://supabase.com/).
2. Copy the database connection string. Prefer TLS/SSL, typically with `sslmode=require`.
3. In Streamlit Community Cloud, open **App settings → Secrets** and add:

```toml
EARTHWISE_DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Apply the SQL migration in `migrations/0001_user_datasets.sql` once to the same Neon branch/database used by the app, using an admin/migration role. The runtime app role only needs the required table privileges for SELECT, INSERT and DELETE. The application no longer attempts to create or alter database schema at runtime. Do not commit this connection string or paste it into the app interface.

For the current integration work, the isolated Neon branch `dev-neon-integration` already has this table and index. Production was not modified.

### Upload and privacy safeguards

- Supported formats: CSV, XLSX, XLS, XLSM and JSON. Excel imports the first worksheet.
- Maximum upload size: 15 MB; maximum 100,000 rows and 100 columns.
- Files are parsed and validated in memory. Empty rows are dropped; missing cells are retained and counted in the preview.
- Column names must be non-empty and unique (case-insensitive). JSON must contain row objects or a `data`/`records` array.
- Each workspace uses a high-entropy recovery key. Only its SHA-256 hash is stored with the dataset records; the raw key is shown to the workspace owner and must be kept private.
- Anyone holding a workspace recovery key can read and delete that workspace's uploads. This is bearer-key access, not a full user-account or team-permission system. Do not use it for regulated or highly sensitive personal data.
- Uploads are stored as normalized tabular records in PostgreSQL JSONB (not as the original workbook binary, styling, or formulas) and remain available across app restarts while the database and its backups remain available. Database retention, backups, and provider costs are controlled by the database owner.
- The app does not silently upload files to GitHub or commit them into the repository.

## Competition demo plan

Use the following short, evidence-led flow for a live judging demo:

1. **Mission Control:** select a Pakistan city (for example Lahore) and explain that current conditions are model-based Open-Meteo output, not a local weather-station observation.
2. **Climate Intelligence:** retrieve NASA POWER daily records for the selected city and period; show coverage, monthly trend, and the statistical method. Explain that gridded satellite/reanalysis data is not a substitute for station measurements.
3. **Earth Explorer:** show the interactive globe and date-selectable NASA GIBS imagery.
4. **AI Earth Scientist:** ask it to explain the selected climate variable and distinguish observed data from uncertainty. This requires a working Neon AI Gateway or OpenAI credential in private app Secrets.
5. **Data Library (optional):** demonstrate CSV upload, validation, persistent save, reopen and export only after a real end-to-end test against the configured database.

### Submission claims and limitations

- Do not claim a live AI response unless the deployed app has successfully completed a real request.
- Do not claim persistent uploads unless the deployed app has successfully saved and reopened a test file.
- The Pakistan city catalogue contains 101 mapped urban centres, not the full PBS 657-locality directory.
- The platform is a research and decision-support prototype, not an official emergency alert system or a replacement for local authorities.
- Planned features listed below are not implemented and must not be presented as completed capabilities.

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
