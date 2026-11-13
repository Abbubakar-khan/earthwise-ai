# EARTHWISE AI — 3-Minute Competition Demo Video Script

**Target duration:** 2:45–3:00  
**Format:** 16:9 screen recording, 1080p, clear voice-over, restrained background music  
**Recording rule:** Record the real deployed/local application only after the release candidate is tested. Never substitute mockups for product footage.

## Pre-recording checklist

- [ ] Confirm the intended app URL opens and all five workspaces render.
- [ ] Use a clean browser window at 100% zoom; hide personal tabs and notifications.
- [ ] Select Lahore (or another verified Pakistan city) and a supported historical period.
- [ ] Retrieve the NASA POWER dataset before recording; verify its source, units, date range and coverage.
- [ ] Test the 3D globe and NASA GIBS imagery; keep a fallback clip ready if an external CDN/tile service is unavailable.
- [ ] Demonstrate AI only after a real provider request succeeds.
- [ ] Demonstrate saved uploads only after upload → validate → save → reopen → export succeeds on the configured database.
- [ ] Hide all credentials, connection strings, recovery keys and personal data.
- [ ] Capture clean footage with cursor movements kept deliberate and pauses trimmed.

## Timed narration and screen direction

### 0:00–0:20 — Opening / problem
**Screen:** EARTHWISE AI title and Mission Control landing view.

**Voice-over:**  
“Climate information is available across many scientific portals, weather services and data tools — but it is often difficult to explore and interpret in one place. EARTHWISE AI brings Pakistan-focused climate data, Earth observation and analytical tools into one workspace.”

**On-screen text:**  
EARTHWISE AI | Pakistan-first climate intelligence

### 0:20–0:48 — Mission Control
**Screen:** Select a Pakistan city. Show the current-conditions panel and the platform overview.

**Voice-over:**  
“Mission Control gives users a location-focused starting point. Current conditions are sourced from Open-Meteo and are model-based estimates, not direct readings from a local weather station. The same workspace keeps the selected city and climate indicator in view as users explore the platform.”

### 0:48–1:25 — Climate Intelligence
**Screen:** Retrieve the prepared NASA POWER dataset. Show coverage metrics, monthly chart, trend summary and methodology.

**Voice-over:**  
“Climate Intelligence retrieves historical daily data from NASA POWER, checks coverage, aggregates observations by month and visualises the selected indicator. Users can examine trend statistics and export the underlying records. NASA POWER values are gridded satellite and model-assisted estimates, so they should not be confused with local station observations. A historical trend is not a forecast or proof of causation.”

**On-screen text:**  
NASA POWER · coverage · monthly analysis · export

### 1:25–1:55 — Earth Explorer
**Screen:** Rotate the 3D Earth, then switch to NASA satellite imagery and the Pakistan city atlas.

**Voice-over:**  
“Earth Explorer connects the analytical view to geography. Users can explore a 3D Earth, view date-selectable NASA GIBS VIIRS daily imagery, and locate the platform’s mapped Pakistan urban centres. Satellite imagery is a daily composite — not live video.”

### 1:55–2:25 — AI Earth Scientist
**Screen:** Ask one prepared question that uses the selected city and dataset. Show the real answer and any uncertainty language.

**Voice-over:**  
“AI Earth Scientist helps users ask questions about climate indicators and interpret the selected evidence. It uses a configured model provider and the current analytical context. It is an API-powered assistant, not an independently trained scientific model, and its answers should be checked against primary sources.”

**Fallback if live inference is not verified:**  
“AI Earth Scientist is the conversational layer designed to explain climate indicators and supplied evidence. Live responses are enabled only when the deployment has valid provider credentials and a successful model connection.”  
Do not show a fabricated answer.

### 2:25–2:45 — Data Library
**Screen:** Show a small, non-sensitive sample file being validated, saved, reopened and exported — only if the complete workflow passed.

**Voice-over:**  
“Data Library lets users validate and work with their own tabular datasets. When PostgreSQL storage is configured, uploads can be saved to a private workspace, reopened and exported.”

**Fallback if persistence is not verified:**  
“Data Library includes validated multi-format upload and a PostgreSQL-backed persistence workflow. We are showing the upload interface here; we do not claim persistent storage until the live save-and-reopen test has passed.”

### 2:45–3:00 — Closing
**Screen:** Return to the brand/hero screen. Show repository or competition title only if appropriate.

**Voice-over:**  
“EARTHWISE AI is a research and decision-support prototype built to make climate evidence easier to explore and communicate in a Pakistan-focused context. Explore the evidence. Understand the uncertainty. Make better-informed decisions.”

**End card:**  
EARTHWISE AI — Earth Intelligence for Pakistan

## Editing and accessibility notes

- Use short, clean cuts; avoid fast zooms and decorative transitions.
- Add accurate captions and spell provider names correctly.
- Keep chart labels, units and date ranges readable.
- Use subtle music under narration; narration must remain clear.
- Do not show API keys, Neon credentials, database URLs, recovery keys or personal information.
- Do not imply the platform is an official alert service.
- Replace fallback narration only after the relevant live test has passed.
