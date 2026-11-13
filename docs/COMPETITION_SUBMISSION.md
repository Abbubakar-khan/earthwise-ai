# EARTHWISE AI — Competition Submission Brief

## One-line pitch

EARTHWISE AI is a Pakistan-first climate intelligence workspace that turns trusted Earth-observation and weather datasets into understandable, location-specific climate insights.

## The problem

Climate information is fragmented across scientific data portals, weather services and technical analysis tools. Students, researchers and local decision-makers need a clearer way to explore historical climate patterns, understand current model conditions and communicate uncertainty.

## The solution

EARTHWISE AI brings five workflows into one Streamlit workspace:

1. **Mission Control** — selected-city overview and model-based current conditions.
2. **Climate Intelligence** — NASA POWER daily records, monthly aggregation, coverage checks, trend analysis and downloadable results.
3. **AI Earth Scientist** — conversational explanations grounded in the selected city and climate context; requires a configured model provider.
4. **Earth Explorer** — interactive Earth visualization, date-selectable NASA GIBS imagery and a Pakistan city atlas.
5. **Data Library** — validated CSV/Excel/JSON uploads with private workspace recovery keys and PostgreSQL persistence when a database is configured.

## Suggested 3-minute judging demo

- **0:00–0:25 — Problem and pitch:** explain fragmented climate data and Pakistan-first focus.
- **0:25–0:55 — Mission Control:** choose Lahore; explain source and model-based nature of current conditions.
- **0:55–1:40 — Climate Intelligence:** retrieve a period, show data coverage, monthly chart and trend method. Explain what the trend does and does not establish.
- **1:40–2:05 — Earth Explorer:** show the globe and NASA imagery.
- **2:05–2:35 — AI Earth Scientist:** ask one question such as “Explain the long-term temperature trend for this city and describe the uncertainty.” Only demonstrate a live answer after a successful provider request.
- **2:35–3:00 — Impact and roadmap:** describe how clearer climate evidence can support research and planning; distinguish implemented features from planned disaster feeds and scenario modelling.

## Architecture

- **Interface:** Python + Streamlit.
- **Historical climate data:** NASA POWER API.
- **Current model conditions:** Open-Meteo.
- **Satellite imagery:** NASA GIBS.
- **AI:** Neon AI Gateway (preferred when configured) with direct OpenAI Responses API fallback.
- **User datasets:** PostgreSQL on Neon, JSONB records, SHA-256 hashed workspace recovery keys.
- **Quality:** pytest suite and GitHub Actions CI.

## Demo safety and accuracy checklist

- [ ] App opens successfully from the intended competition URL.
- [ ] Select one city and retrieve climate data successfully.
- [ ] Show the provider/source and requested period.
- [ ] Show AI only after a real successful request; otherwise describe it as configured code awaiting credentials.
- [ ] Show dataset persistence only after a real upload → save → reopen → export test.
- [ ] Never expose database URLs, API keys, Neon tokens or workspace recovery keys on screen.
- [ ] Do not imply the product is an official disaster-warning system.
- [ ] Do not claim complete Pakistan locality coverage: the catalogue currently contains 101 mapped urban centres, not the full PBS 657-locality directory.
- [ ] Keep the presentation focused on what is implemented today; label roadmap items as planned.

## Known limitations to disclose

- AI chat depends on private provider credentials and a model enabled for the selected Neon branch.
- Persistent user uploads depend on a configured PostgreSQL connection and the explicit SQL migration.
- The Pakistan city catalogue is a curated 101-centre subset.
- Full PBS locality coverage, verified multi-source disaster feeds, scenario modelling, user accounts and production observability are planned work, not current features.
- This is a research and decision-support prototype, not an official emergency alert service.

## Final submission links

- Repository: https://github.com/Abbubakar-khan/earthwise-ai
- Neon integration PR: https://github.com/Abbubakar-khan/earthwise-ai/pull/3
- Deployment URL (verify before presenting): https://earthwise-ai-ewfgtmabmm65y3lqw6mxhm.streamlit.app/
