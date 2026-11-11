# EARTHWISE AI — Project Checkpoint
Date: 2026-11-12
Organization: FORGE CYBER LAB

## Verified repository state
- Repository: https://github.com/Abbubakar-khan/earthwise-ai
- Branch: main
- Latest verified CI run: https://github.com/Abbubakar-khan/earthwise-ai/actions/runs/43099700804
- CI conclusion: success
- Verified job steps: checkout, Python setup, dependency installation, and pytest all completed successfully.

## Current implementation
- NASA POWER daily point API client exists in `src/nasa_power.py`.
- Streamlit application exists in `app/main.py`.
- Current app fetches NASA POWER daily T2M and PRECTOTCORR for configured locations, then aggregates and analyzes trends.
- Core tests cover monthly temperature mean, monthly precipitation sum, and a synthetic upward trend.
- Scientific method currently uses Kendall tau and Theil-Sen slope; it does not yet correct for monthly seasonality, autocorrelation, or multiple testing.

## Important data status
- No verified live NASA POWER city dataset is currently tracked in the repository.
- `data/raw/*` and `data/processed/*` are intentionally excluded by `.gitignore`; raw/processed data must be backed up separately if they are downloaded.
- Do not report any real Lahore, Islamabad, or Karachi trend values until live API data have been fetched and quality-checked.
- GPM IMERG and MODIS integrations remain planned/documented, not implemented in the current MVP.

## Next steps
1. Run the Streamlit app and fetch NASA POWER data for Lahore first.
2. Verify API response, date range, parameter units, missing-value handling, and coverage.
3. Save the downloaded CSV and metadata to a separate backup or an approved data-storage location; do not commit large raw datasets without reviewing repository size and data policy.
4. Repeat for Islamabad and Karachi.
5. Validate trend methodology before presenting results as scientific findings.

## Scope and claims
This is a research prototype, not a forecast or an operational disaster-alert system. CI success confirms the automated tests pass; it does not by itself validate live NASA data access, scientific accuracy, or deployment.
