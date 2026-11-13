# EARTHWISE AI — Competition Pitch Deck Content

**Target:** 12 slides | 16:9 | 5–7 minute presentation  
**Visual direction:** deep navy background, restrained cyan/teal accents, white typography, subtle Earth-data motifs. Use actual product screenshots only after capturing the tested app. Keep each slide focused; use speaker notes for detail.

## Slide 1 — Title
**EARTHWISE AI**  
*Pakistan-first climate intelligence workspace*

Subtitle: Explore climate evidence. Understand uncertainty.  
Presenter: Muhammad Abubakar  
Visual: Authentic Mission Control screenshot or a restrained Earth visual.

**Speaker note:** Introduce EARTHWISE AI as a research and decision-support prototype that brings climate data, Earth observation and analytical workflows together.

## Slide 2 — The problem
**Climate evidence is fragmented and difficult to interpret.**
- Scientific datasets, weather services and satellite imagery live across separate tools.
- Data coverage, units and uncertainty can be difficult for non-specialists to assess.
- Pakistan-focused exploration needs a clear location-based workflow.

**Speaker note:** Do not claim quantified national losses or market statistics unless separately sourced and cited.

## Slide 3 — Our solution
**One workspace. Five connected workflows.**
- Mission Control
- Climate Intelligence
- AI Earth Scientist
- Earth Explorer
- Data Library

Visual: Real screenshot of the app navigation and landing view.

## Slide 4 — Mission Control
**Start with a place, not a pile of data.**
- Pakistan city selection and regional context.
- Current model-based conditions.
- Shared city and indicator context across workspaces.

**Accuracy note:** Open-Meteo conditions are model-based estimates, not guaranteed station observations or emergency warnings.

Visual: Actual Mission Control screenshot.

## Slide 5 — Climate Intelligence
**Turn historical records into interpretable evidence.**
- NASA POWER daily point data.
- Monthly aggregation and coverage checks.
- Time-series visualisation.
- Kendall tau and Sen’s slope analysis.
- Downloadable source and aggregate data.

**Accuracy note:** NASA POWER values are gridded satellite/model-assisted estimates. Current Kendall testing does not correct for monthly seasonality or serial autocorrelation. Trends are not forecasts or causal attribution.

Visual: Actual chart, coverage metrics and methodology panel.

## Slide 6 — Earth Explorer
**Connect climate analysis to the geography of Pakistan.**
- Interactive 3D Earth.
- Date-selectable NASA GIBS VIIRS imagery.
- Curated Pakistan city atlas: 101 mapped urban centres.

**Accuracy note:** VIIRS is a daily composite, not live video. The city atlas is not the full PBS 657-locality directory.

Visual: Actual globe and map screenshots.

## Slide 7 — AI Earth Scientist
**Ask questions about the evidence.**
- Conversational explanations of climate indicators.
- Context from selected city, period and loaded analysis.
- Clear uncertainty and safety boundaries.

**Accuracy note:** This is an API-powered assistant, not an independently trained foundation model. Show a real answer only after successful live inference. Otherwise label it as an integration awaiting deployment credentials.

Visual: Actual AI workspace screenshot; do not include secrets.

## Slide 8 — Data Library
**Bring your own environmental data.**
- CSV, XLSX, XLS, XLSM and JSON parsing.
- Validation, preview and row/column safeguards.
- PostgreSQL JSONB persistence with workspace recovery key.
- Reopen, preview, export and delete workflows.

**Accuracy note:** Persistent storage requires configured PostgreSQL and the migration. Do not claim live persistence until upload → save → reopen → export passes in the deployed app.

Visual: Actual upload and saved dataset screenshots, using synthetic non-sensitive sample data.

## Slide 9 — How it works
**A clear technical pipeline**
1. User selects a Pakistan city, indicator and period.
2. NASA POWER supplies historical daily records.
3. Cleaning and monthly aggregation prepare the series.
4. Statistical methods summarise trends and coverage.
5. AI provider can explain the supplied context when configured.
6. PostgreSQL stores user uploads when configured.

**Technology:** Python · Streamlit · NASA POWER · Open-Meteo · NASA GIBS · Neon PostgreSQL · Neon AI Gateway / OpenAI API.

Visual: Simple architecture diagram. Mark optional/credential-dependent services clearly.

## Slide 10 — Pakistan use cases and intended impact
**Designed to support exploration and communication**
- Students and educators exploring local climate indicators.
- Researchers reviewing historical gridded climate evidence.
- Analysts comparing coverage and trends across mapped locations.
- Local organisations communicating data limitations and uncertainty.

**Speaker note:** Present these as intended use cases, not proven deployments, partnerships or measured impact.

## Slide 11 — Limitations and responsible use
**Trust requires clear boundaries.**
- Gridded estimates are not local station measurements.
- Current conditions are not emergency-grade warnings.
- Historical trends are not forecasts or proof of causation.
- 101 mapped urban centres are a curated subset.
- AI can make mistakes and requires primary-source checking.
- Prototype is not an official emergency alert service.

## Slide 12 — Roadmap and closing
**From a focused prototype to a more capable climate workspace**
- Verify deployment, persistence and AI reliability.
- Expand geographic coverage with validated sources.
- Improve seasonal and autocorrelation-aware trend methods.
- Evaluate official, timestamped hazard feeds with freshness and uncertainty controls.
- Add scenario modelling and production observability only after validation.

**Closing line:**  
“EARTHWISE AI — Explore the evidence. Understand the uncertainty.”

## Evidence required before final judging
- [ ] Verified live app URL and clean launch.
- [ ] Real NASA POWER retrieval for a selected city and period.
- [ ] Actual screenshots of all five workspaces.
- [ ] Real AI request/response if demonstrated.
- [ ] Full upload → save → reopen → export proof if persistence is claimed.
- [ ] Test report and current limitations.
- [ ] No secrets, private keys or workspace recovery codes in slides or recording.

## Design and delivery rules
- Use one headline and no more than 3–5 short bullets per slide.
- Prefer full-width authentic screenshots with small callouts.
- Use consistent typography and spacing; avoid excessive animation.
- Keep all chart units, sources and periods visible.
- Include speaker notes rather than crowding slide content.
- Distinguish implemented features, verified features and roadmap items.
