# EARTHWISE AI — Premium Rebuild Notes

Built 2026-11-14 for the NASA Space Apps Hackathon (demo: 2026-11-15).
Original repo inspected in full: `app/main.py` (768 lines), `src/*.py` (9 files),
`tests/*.py`, `docs/*.md`, `requirements.txt`, `runtime.txt`.

## What was preserved — untouched
- `src/nasa_power.py`, `src/cleaning.py`, `src/statistics.py`, `src/anomalies.py`,
  `src/ai_engine.py`, `src/live_weather.py`, `src/regions.py`, `src/comparisons.py`
  — byte-for-byte logic preserved. No backend behaviour changed.
- Data model: no database. Raw NASA POWER CSV + JSON metadata in `data/raw/`
  (git-ignored, as in the original). No user data existed in the repo to migrate.
- All real APIs, no fake data: NASA POWER, Open-Meteo weather, NASA GIBS,
  Globe.gl / Leaflet. No sample / synthetic numbers anywhere in the UI.

## What was added
| Module | Purpose | Data |
|---|---|---|
| `src/air_quality.py` | **NEW — Air Quality page**: live US AQI gauge, PM2.5/PM10, O₃, NO₂, SO₂, CO, European AQI, dominant pollutant, 24 h PM2.5 chart | Open-Meteo Air Quality API (CAMS), free, **no key** |
| `src/risk.py` | **NEW — Risk & Outlook**: composite screening score from Sen slope + latest anomaly + live heat + live AQI; 10-year straight-line Sen-slope projection with 95% CI | Derived only from already-computed real data |
| `src/ai_assistant.py` | **NEW — AI Assistant page**: evidence-bound, rule-based assistant. Answers weather / AQI / trend / anomaly / risk / forecast / sources only from data loaded on the page; says when data is missing instead of inventing it | No LLM, no key, no hallucination |
| `app/main.py` | **REWRITTEN — premium SaaS dashboard**: sidebar navigation (7 pages), glass/KPI cards, animated live indicator, responsive mobile layout, reduced-motion support, loading spinners, `safe()` error handling on every live call, multi-city comparison (real fetches, max 3), 12-month rolling mean, downloads on every page | Same Streamlit 1.66 stack |
| `tests/test_new_modules.py` | 5 new tests (AQI bands, dominant pollutant, risk, projection, assistant) | — |
| `.streamlit/config.toml` | Dark theme, headless server defaults | — |
| `.env.example` | Documents the one optional variable | — |

## Pages
1. **Overview** — hero, 4 live KPIs (temp / AQI / trend / risk), current conditions + AQI snapshot, climate preview
2. **Climate Analytics** — coverage, Sen slope, Kendall p, time series, 12-month rolling mean, seasonal anomalies, AI Earth Scientist, compare up to 3 cities
3. **Air Quality** — US AQI gauge, pollutant cards, 24 h PM2.5 chart, EPA bands
4. **Weather & Maps** — 7-day forecast cards, 24 h temperature, national conditions map, 3D globe, NASA GIBS satellite (VIIRS / IMERG), city directory
5. **AI Assistant** — chat with suggested questions, evidence-bound answers
6. **Risk & Outlook** — composite screening, 10-year Sen-slope projection chart + table + CSV
7. **Data & Downloads** — monthly table, CSV downloads, API/configuration table

## Live animations — 2026-11-14 (last work before submission)
New module `src/animations.py` (pure helpers, no new dependencies, CSS only):
- **Live ticker** — Overview + Weather & Maps: scrolling strip of REAL live values for the selected city (temperature, condition, US AQI, PM2.5, provider time). CSS `translateX` marquee, pauses on hover, duplicates items for a seamless loop. Missing values are omitted, never faked.
- **Animated hero** — shimmering gradient + floating weather symbol that changes with the real Open-Meteo `weather_code` (clear = slow spin, cloud = drift, rain = falling, snow = gentle float, storm = flicker, fog = fade).
- **KPI cards** — fade/slide-up on load, staggered 0 / 80 / 160 / 240 ms on Overview; LIVE dot pulses stronger (`livePulse`); all Plotly charts fade in.
- **Live clock** — "LIVE · Updated <provider time> · Open-Meteo / CAMS" line under the hero.
- All animations respect the existing `@media (prefers-reduced-motion: reduce)` rule and the mobile `max-width: 700px` layout. No JavaScript, so nothing new breaks old Chrome beyond what Streamlit 1.66 already does.

## Button audit — 2026-11-14 (all buttons checked with Streamlit AppTest, real runs)
| Button / control | What it does | Result |
|---|---|---|
| Sidebar "Retrieve climate data" | Fetches NASA POWER for city + indicator + period, saves CSV, toast on success | PASS by code + shared fetch verified live via Compare (Retrieve itself not clicked live, to avoid overwriting the 2015–2025 Lahore demo CSV) |
| Sidebar "Refresh live weather / AQI" | Clears live caches, reruns, toast "Live weather / AQI refreshed" | **FIXED** — my first toast used icon `↻`, which Streamlit rejects as not an emoji and raised `StreamlitAPIException`; changed to 🌍, re-tested, toast now shows |
| Sidebar city search | Filters city list | **FIXED** — a non-matching search used to `st.stop()` and blank the whole app; now warns and shows all cities |
| Sidebar navigation radio, province/city/indicator selectboxes, year inputs | Switch page / city / indicator / period | PASS — all 7 pages render, no exception |
| Climate Analytics "Compare selected cities" | Fetches up to 3 cities live, shows Sen slope table | **FIXED** — with no city selected it silently did nothing; now warns "Select at least one city first" and toasts on success. Live test: Lahore −1.34/decade vs Karachi +0.20/decade |
| AI Assistant 4 suggested questions | Append Q + evidence-bound answer | PASS — tested, answer shows real AQI 173 |
| AI Assistant chat input | Asks free question, answers from loaded data only | PASS — tested, answered with real AQI 173 — Unhealthy |
| AI Assistant "Clear conversation" | Clears chat, reruns | PASS |
| Weather & Maps download snapshot CSV | Downloads national city weather CSV | PASS — now shows an info message instead of nothing when the national map fails to load |
| Risk "Download 10-year projection (CSV)" | Downloads projection CSV | PASS |
| Data & Downloads monthly / anomalies / projection CSVs | Download CSVs | PASS — missing-data cases now show a caption ("unavailable — needs a valid trend") instead of a silently missing button |
| Tabs, selectboxes, slider, date input (Weather & Maps) | Switch layers / opacity / satellite date | PASS |

**Other bugs found & fixed:** (1) `meta` could be `None` after a failed climate analysis while pages still read `meta['first_date']` → crash; now the app shows the fetch prompt instead. (2) Risk page could read `risk['scores']` when `risk` was `None`; now guarded with an error + stop. (3) Weather hourly chart read `forecast["hourly"]` directly → `KeyError` if missing; now guarded with try/except + empty-data message. (4) `proj_df.round(3)` / `anomaly_df.round(3)` warned on datetime columns; now round numeric columns only. (5) Overview trend KPI printed `p=None` when p-value was unavailable; now prints "p unavailable".

**Still open / not a bug:** (a) Streamlit 1.66 prints a deprecation warning that `use_container_width` will be removed after 2025-12-31 — harmless on the pinned 1.66.0, but the app should migrate to `width='stretch'` before upgrading Streamlit. (b) On old Chrome (<110) Streamlit's own frontend still shows `Object.keys(...).toSorted is not a function` — that is the browser, not this app; update Chrome or use Edge / a phone. (c) The 3D globe and GIBS satellite tiles need internet/CDN access; they degrade to a message when offline.

## Interface polish — 2026-11-14
Same dark premium weather.com-like look (`#7ee8d6` / `#060f18`), no new dependencies: KPI/chart entrance animations use `backwards` fill so hover lift still works after the animation; buttons get a press scale (0.98) + visible focus outline; cards get a subtle hover border; download buttons are full-width; `.ew-sub2` contrast raised to `#b0c2ce`; "Compare selected cities" is now the primary button on that section. Mobile layout unchanged and checked at `max-width: 700px` (ticker + hero symbol shrink).

## Verified live test — 2026-11-14 01:30 PKT (real, not sample)
- Open-Meteo Lahore: **19.2 °C**, 70% humidity, feels like 19.5 °C, weather code 0 (Clear sky), wind 6.1 km/h, provider time 2026-11-14T01:30
- Open-Meteo Air Quality Lahore: PM2.5 **62.4 µg/m³**, PM10 72.9, **US AQI 173 — Unhealthy**, European AQI 66
- NASA POWER live (2025-01-01 → 2025-06-30): 181 rows, T2M mean 25.96 °C — API reachable
- NASA POWER Lahore T2M 2015-01-01 → 2025-12-31 (cached demo file): 4,018 rows, **100% coverage**, 132 monthly obs
- Trend: **decreasing, Sen slope −1.34 °C/decade, Kendall p = 0.52 (not significant)** — report this honestly; the simple test does not correct for seasonality/autocorrelation, and the result depends on the period chosen. Do NOT claim a warming trend for Lahore from this run.
- Latest anomaly (Dec 2025): +0.58 °C vs same-month mean in the selected dataset
- Risk composite for that run: 29.4/100 — Moderate (driven mainly by AQI)
- `pytest`: **17 passed** (11 original + 6 new animation tests)
- `streamlit run app/main.py`: **HTTP 200**, server log clean, no errors/tracebacks; Streamlit AppTest ran all 7 pages with **no exception**
- Open-Meteo Lahore: 19.4 °C, 69% humidity — live
- Open-Meteo Air Quality Lahore: PM2.5 67.8 µg/m³, PM10 77.8, **US AQI 175 — Unhealthy**
- NASA POWER Lahore T2M 2015-01-01 → 2025-12-31: 4,018 rows, **100% coverage**, 132 monthly obs
- Trend: **decreasing, Sen slope −1.34 °C/decade, Kendall p = 0.52 (not significant)** — report this honestly; the simple test does not correct for seasonality/autocorrelation, and the result depends on the period chosen. Do NOT claim a warming trend for Lahore from this run.
- Latest anomaly (Dec 2025): +0.58 °C vs same-month mean in the selected dataset
- Risk composite for that run: 29.4/100 — Moderate (driven mainly by AQI)
- `pytest`: **11 passed** (6 original + 5 new)
- `streamlit run app/main.py`: **HTTP 200**, no errors in the server log

A demo dataset is included: `data/raw/lahore_t2m_nasa_power_daily.csv` (+ metadata JSON), so the
Analytics / Risk pages load instantly for Lahore + T2M without a fetch. Delete it to start clean.

## APIs & credentials — what you need
| Service | Key needed? |
|---|---|
| NASA POWER | No |
| Open-Meteo weather (evaluation) | No |
| Open-Meteo Air Quality (CAMS) | No |
| NASA GIBS | No |
| **Open-Meteo commercial** | **Only `OPEN_METEO_API_KEY` — needed ONLY if you run this commercially / monetise it.** Set it as an env var or in Streamlit Cloud Secrets. Never commit it. Without it the app uses the free evaluation endpoint, exactly as the original did. |

**No other credentials are missing. There is no database password, no NASA key, no LLM key.**

## Run / deploy
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app/main.py        # http://localhost:8501
python -m pytest tests/ -q                 # 25 passed (2026-11-14, incl. intro splash)
```
Streamlit Cloud: repo → branch `main` → main file `app/main.py` (Python 3.12, see `runtime.txt`).
Optional secret: `OPEN_METEO_API_KEY` (commercial use only).

## Honest limitations (keep these in your demo)
- NASA POWER = gridded/model estimates, not station observations.
- Open-Meteo weather/AQI = model (CAMS) estimates, not station measurements.
- Trend test = simple Kendall + Sen; no seasonality / autocorrelation correction.
- Risk = screening signal, not a PMD/health warning, flood forecast or disaster alert.
- 10-year outlook = straight-line extrapolation, not a climate-model projection.
- GIBS imagery = satellite tiles, not live video.

## Opening intro splash (2026-11-14 01:48 PKT)
- Full-screen intro on app open, instead of a blank loading screen: spinning globe with orbiting dot, EARTHWISE AI title, 'Pakistan Earth Intelligence', loading bar, sources NASA POWER / Open-Meteo / CAMS / NASA GIBS.
- Pure CSS, no JavaScript, no fake data. Shows once per session (~3s), then the main app loads. Reduced-motion users see a near-static splash.
- Files: src/animations.py (INTRO_CSS + intro_html), app/main.py (wired in), tests/test_animations.py (new test).

## Old-Chrome fix — 2026-11-14 (so every visitor can use the app)
On old Chrome (<110) the live app showed a popup: "Bad message format / Object.keys(...).toSorted is not a function". Root cause: Streamlit's own frontend JS, not EarthWise code — Streamlit 1.64.0+ uses `Array.prototype.toSorted` (ES2023, Chrome 110+). Verified empirically by downloading the wheels for Streamlit 1.25–1.66 and grepping their bundled frontend JS: `toSorted` appears 0 times up to 1.63.0 and 7 times from 1.64.0 on (in `utils.*.js` — `Object.keys(e).toSorted()`, exactly the reported error — and in the DataFrame JS). Fix: pin `streamlit==1.63.0` in `requirements.txt` (newest version with a toSorted-free frontend). No other ES2023-only array methods in 1.63.0's bundle (`toReversed` 0, `findLast(` 0, `toSpliced` 0; the few `.with(` hits are VS Code's `Uri.with()`, not `Array.with`). Python stays 3.12 (`runtime.txt` unchanged — 1.63.0 requires Python ≥3.10). App code needed NO changes: every Streamlit API the app uses (`st.chat_input`, `st.toast`, `st.status`, `st.rerun`, `st.divider`, `use_container_width`, `st.components.v1.html`) already existed in 1.63.0. New browsers run older Streamlit code without any problem, so modern visitors lose nothing — the only trade-off is staying off Streamlit 1.64+ features until the minimum browser is newer. (`use_container_width` deprecation warnings still appear on 1.63.0 too — harmless warnings only, the parameter still works.) Residual note: the 1.63.0 bundle still uses `structuredClone` (Chrome 98+), which the reported error never mentioned and the app already relied on under 1.66.0.

**Files changed this round:** `requirements.txt` (streamlit 1.66.0 → 1.63.0), `REBUILD_NOTES.md` (this section).

## Professional design fix — 2026-11-14 (live site did not look professional)
The live Streamlit site (still the pre-animations version — the new files had never been uploaded to GitHub) was inspected in a modern browser 01:40–01:42 PKT. Problems found and fixed in this round, all in the local code so they take effect after the next GitHub upload + Streamlit redeploy:

1. **Header clipped (every page)** — "EARTHWISEAI / PAKISTAN INTELLIGENCE" was low-contrast and cut in half by the Streamlit toolbar; the LIVE pill was half cut off. Fixed: `.block-container` top padding raised to 3.4rem (2.8rem mobile), solid `#060f18` header background, brand text now `EARTHWISE AI` with explicit bright `#eef6f9` colour and a lighter `/ PAKISTAN INTELLIGENCE` sub-label. Streamlit header itself is not hidden.
2. **Hero was a large empty panel** — the right half and bottom were dead space. Fixed: hero is now two columns; the right panel shows the LIVE weather visual — big temperature, animated weather symbol for the real condition, condition + feels-like, humidity / wind / AQI mini-stats. Shimmer + symbol animations kept.
3. **First-load blank pages (biggest "unfinished" signal)** — Trend/Risk KPIs showed "—" and Climate/Risk/Data were ~85% blank. Root cause found: `.gitignore` excluded `data/raw/*`, so the Lahore demo CSV never reached GitHub/Streamlit Cloud. Fixed three ways: (a) `.gitignore` now has exceptions for `data/raw/lahore_t2m_nasa_power_daily.csv` + its metadata JSON — **these files MUST be uploaded to GitHub with the code**; (b) default sidebar period changed 2001–2025 → **2015–2025** to match the demo file exactly; (c) safety net: if the file is still missing, the app auto-fetches the same real Lahore T2M 2015–2025 range from NASA POWER once per session (verified in a clean copy with the CSV deleted). The demo is labelled on every page that uses it: "Demo dataset: Lahore T2M 2015–2025 · NASA POWER (included file)". No data invented.
4. **Wind truncation** — "6.1 km…" in a narrow metric tile. Fixed: Overview Current Conditions + AQI snapshot now use compact HTML stat tiles (`.ew-stat`, wrapping values, 1.05rem) instead of `st.metric` in 4-across columns; checked at desktop and mobile widths.
5. **Disjointed cards** — "Current conditions" / "Air quality snapshot" were tall empty header boxes with content spilling below. Fixed: each is now ONE card containing header + stats + source line (`.ew-live-card`).
6. **Weather forecast fractured grid (4+3)** — Fixed: one responsive grid, 7 columns desktop / 4 tablet / 2 mobile (`forecast_cards_html()` in `src/animations.py`), all 7 days in a single strip; pollutant/AQI content stays on the Air Quality page. Hourly chart + Earth observation section follow below, clearly separated.
7. **AI Assistant void** — large empty teal card + blank space above the chat input. Fixed: a starter assistant greeting on first visit, a "What I can answer" card, and a real example answer (computed live from the loaded data, e.g. the current AQI) next to it. Evidence-bound behaviour unchanged; `st.chat_input` is pinned to the bottom by Streamlit itself.
8. **Navigation bug found during testing** — the sidebar radio used `index=` derived from `st.session_state`, which made it snap back to the previous page on some reruns (reproduced in a minimal app). Fixed: keyed radio (`key="page"`), Streamlit owns the state; verified by navigating all 7 pages back and forth in AppTest.
9. **Empty states redesigned** — Climate Analytics / Risk / Data no longer show a bare blue notice; they show a designed card with steps + a working "Fetch {city} climate data now" button (real NASA POWER fetch, toast on success).

**Files changed this round:** `app/main.py`, `src/animations.py` (new `hero_now_html`, `forecast_cards_html`, `demo_is_default`, `DESIGN_CSS`), `tests/test_design.py` (new, 7 tests), `.gitignore` (demo CSV exceptions), `REBUILD_NOTES.md` (this section). Plus the intro splash from the parallel 01:48 PKT work (`INTRO_CSS` + `intro_html`, once per session ~3s).

**Verified — 2026-11-14 01:50 PKT (real, not sample):**
- `pytest`: **25 passed** (11 original + 6 animation + 7 design + 1 splash)
- `streamlit run app/main.py`: **HTTP 200**, server log clean
- Streamlit AppTest, all 7 pages, no exception: default landing (Lahore/T2M) shows Trend **−1.34 °C/decade** and Risk **28.2/100** (not "—"); Climate Analytics shows 3 charts; Risk shows Composite 28.2/100 (Trend 33, AQI 58, Heat 10); Data shows the monthly table; Weather shows the 7-card forecast strip; AI Assistant greets, lists capabilities and answers the AQI question with the real value; a suggested-question click answers with real AQI.
- No-file fallback verified: in a clean copy with the demo CSV deleted, the landing auto-fetches Lahore T2M 2015–2025 from NASA POWER and still shows Trend −1.34 and a Risk score.
- Live at 01:50 PKT: Open-Meteo Lahore **19.1 °C**, Clear sky (code 0), humidity 71%, wind 6.1 km/h, provider 01:45; CAMS AQI **173 — Unhealthy**, PM2.5 62.4 µg/m³, PM10 72.9, provider 01:00.
- **Still open / not bugs:** The red "Hosted with Streamlit" badge is Streamlit Cloud's own branding and was left alone. (The old-Chrome `toSorted` error listed here earlier is now fixed by the 2026-11-14 Old-Chrome fix above — Streamlit pinned to 1.63.0.)

## Intro fly-in + top navigation — 2026-11-14 (last work before submission)
Two changes after the user checked the live site on his phone (02:25 PKT, Lahore 18.8 °C / AQI 171 — everything else looked good):

1. **Intro title now flies in.** The "EARTHWISE AI" title on the opening splash is letter-by-letter spans (`ew-intro-letter`, new `introFlyIn` keyframe in `src/animations.py`): each letter flies in from above with a slight overshoot, staggered ~70 ms apart, "AI" in accent teal; the tagline, loading bar and source line fade in just after. Pure CSS, no JavaScript, no new dependencies. Reduced-motion users get no stagger (`animation-delay:0ms` in the reduced-motion rule) — near-static, as before.
2. **Why the splash was not seen before — fixed.** The old code did `time.sleep(3.0)` + `st.rerun()` on the server. The splash's CSS fade-out timer starts when the *browser paints* the element, but the rerun fired ~3 s after the server *sent* it — on slow connections (mobile 4G, cold Streamlit start ~30 s) the rerun could replace the page before the splash was ever painted, so it flashed or never appeared (live checks at 02:00 and 02:19 PKT never caught it). Fixed: the splash is now rendered in the *same first run* as the app, overlaying it with `position:fixed`, and its CSS fade-out (3.1 s + 0.6 s fade) runs from paint — no server sleep, no rerun, no blank gap while the app loads behind it. Still once per session (`intro_seen` in session state).
3. **Top navigation bar (mobile fix).** On phones the Streamlit sidebar is collapsed, so mobile users saw NO Home/page buttons at the top. Added a navigation bar under the header, above the hero, on every page: buttons for all 7 pages (Overview, Climate Analytics, Air Quality, Weather & Maps, AI Assistant, Risk & Outlook, Data & Downloads) in two rows (4 + 3) so they stay tap-friendly on a phone; the active page is highlighted with the primary button style. Sync: the buttons are plain `st.button`s — a tap stores the target in `st.session_state["_nav_target"]` and reruns, and the app applies it *before* the keyed sidebar radio (`key="page"`) is created, so the radio adopts the new page and the two always agree. The keyed-radio fix from the design round is untouched, and the radio still works the other way (verified both directions in AppTest).

**Files changed this round:** `app/main.py` (intro: sleep/rerun removed; top nav bar + `_nav_target` hand-off), `src/animations.py` (`introFlyIn` keyframe, `.ew-intro-letter`, fade-out 2.85 s → 3.1 s, reduced-motion delay reset), `tests/test_topnav.py` (new, 4 AppTest tests), `tests/test_animations.py` (fly-in test + intro test updated for letter spans), `REBUILD_NOTES.md` (this section).

**Verified — 2026-11-14 ~02:35 PKT (real, not sample):**
- `pytest`: **30 passed** (26 previous + 4 new top-nav tests)
- `streamlit run app/main.py`: **HTTP 200**, server log clean, no server left running
- Streamlit AppTest: intro splash HTML (with `ew-intro-letter` spans) present on first load; all 7 top-nav buttons exist and each switches the page with the sidebar radio following it, no exception; sidebar radio still switches pages both ways; all 7 pages render.
- Live at ~02:34 PKT: Open-Meteo Lahore **18.6 °C**, Clear sky, feels like 18.9 °C; CAMS AQI **171 — Unhealthy**, PM2.5 60.5 µg/m³.
- Still open / not verified locally: the splash timing on a real phone can only be confirmed on the live site — the CSS timing is correct by construction, but a slow 4G load can still make the ~3 s splash overlap the app's own loading time.

## Auto location detect — 2026-11-14
The user could not find any location search on his phone (the city picker lives only in the sidebar, which is hidden on mobile) and had to select manually. Now the app asks for location permission and auto-detects the visitor's location on first load.

1. **Auto-detect on first load — two channels, one apply step.** A vendored **custom component** (`components/geolocation/`) asks the browser via `navigator.geolocation.getCurrentPosition` and returns the coordinates through Streamlit's own postMessage bridge (`Streamlit.setComponentValue`), which reruns the app. It also fires automatically on first load (`request=True` while no detection has been attempted yet), and a prominent **"📍 Use my location"** button (in the location bar under the top nav, visible on mobile) re-arms it on tap (`request_id` increments so the persistent iframe serves a fresh attempt). Detection runs at most once per session; denial / timeout / unavailable falls back silently to the manual picker with a small note ("Location access declined — pick a city below."), never an error popup.
2. **Why a custom component, not a `components.html` snippet (verified).** The snippet iframe's sandbox (`allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-downloads`) has no `allow-top-navigation`, and its allow list does include `geolocation`. A file:// harness in headless Chromium (Muse Browser 157) with Streamlit's exact sandbox/allow attributes proved it: `navigator.geolocation` IS available in the iframe, but assigning `window.parent.location.href` throws "Failed to set the 'href' property on 'Location': The current window does not have permission to navigate the target frame", and `window.open` without a user gesture returns null — so coordinates cannot be passed back via `?geo_lat=` query params from a snippet. The custom component's postMessage bridge is not blocked by the sandbox. No new pip dependency: `components/geolocation/streamlit.js` is the official `streamlit-component-lib` 2.0.0 `dist/streamlit.js` vendored verbatim (Apache-2.0), plus a tiny local `ArrowTable.js` stub (the component never passes dataframes, so the stub's constructor throws if ever used — it only exists so the static import resolves without the large `apache-arrow` package).
3. **Coordinates → city (`src/geolocation.py`, pure logic, no Streamlit).** Reverse-geocode first via the free no-key BigDataCloud client endpoint (`https://api.bigdatacloud.net/data/reverse-geocode-client`, 8 s timeout, never raises), then match the locality to the nearest city in `REGIONS` (haversine; exact → unique whole-word → difflib ≥ 0.8, so "Karimabad" → "Hunza (Karimabad)" and "Faislabad" → "Faisalabad", while ambiguous "Dera" or foreign "London" match nothing). The locality is trusted only if its catalogue city is within 150 km of the detected point, otherwise the app falls back to pure haversine-nearest REGIONS city and says so ("Nearest city in our catalogue: X"). **Live weather/AQI use the EXACT detected coordinates** (more accurate than the city centre); **climate history uses the matched REGIONS city**. A second channel, `?geo_lat=&geo_lon=&geo_status=` query params, feeds the same apply step (used by tests and by links carrying a position) and is cleared from the URL immediately so coordinates never stay in a shareable link.
4. **Manual city search is now visible on mobile too.** A location bar under the top navigation, on every page: a "Find a city" search box + city selectbox synced with the sidebar picker in both directions (`on_change` callbacks; the sidebar selectbox now has `key="City"`), so a visitor never has to open the sidebar to change city. The sidebar picker works exactly as before. When detection is active the bar shows "📍 Detected near: <city> · live weather uses your exact position (lat° N, lon° E)" (or the "Nearest city in our catalogue" variant) with a **"✕ Change"** button that drops the exact-position override and keeps the city; picking a different city manually also drops the override. Privacy line under the bar: "Your location stays in this browser session — used only to pick your city and fetch its weather (Open-Meteo / CAMS). It is never stored, uploaded or shared." No new API keys, no new paid services, no new dependencies.

**Files changed/added this round:** `src/geolocation.py` (new, 218 lines), `components/geolocation/index.html` (new, component JS), `components/geolocation/streamlit.js` (new, vendored streamlit-component-lib 2.0.0), `components/geolocation/ArrowTable.js` (new, stub), `app/main.py` (geo block before the sidebar, component declaration, location bar, picker sync callbacks, exact-coords override for live data, `time` import already removed in the fly-in round), `tests/test_geolocation.py` (new, 37 tests), `REBUILD_NOTES.md` (this section). **Upload note: the new `components/geolocation/` files must be uploaded to GitHub with the code, or the feature will not work live.**

**Verified — 2026-11-14 ~04:00 PKT (real, not sample):**
- `pytest`: **67 passed** (30 previous + 37 new: haversine, nearest-city, reverse-geocode parsing with mocked requests, locality matching incl. typo/ambiguous/foreign, resolve logic, query-params parsing, component files, and 8 AppTest tests)
- Streamlit AppTest: `?geo_lat=31.55&geo_lon=74.40&geo_status=ok` switches the city to Lahore, shows "Detected near: Lahore", clears the query params from the URL, and the live calls receive the exact (31.55, 74.40) — not the city centre; `geo_status=denied` falls back to the default picker with the declined note and no error; mid-Atlantic coords (0, −30) resolve to nearest Gwadar with the "Nearest city in our catalogue" line; main picker ↔ sidebar picker sync both directions; "Use my location" arms `geo_request=True` / `request_id=1`; "Change" clears the detection and keeps the city.
- `streamlit run app/main.py`: **HTTP 200**, server log clean, no server left running. All 7 pages render (AppTest navigation suite).
- **NOT verified locally — needs a live check:** the real browser permission prompt and the component JS end-to-end. The custom component's JS could not be exercised in a browser here: headless Chromium in this sandbox blocks navigations to localhost (`ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`), so no real browser session could run the app. The JS follows the streamlit-component-lib 2.0.0 protocol exactly as read from its source (`setComponentReady` → `streamlit:render` with `args` → `setComponentValue` → rerun), and the Python side is fully AppTest-verified, but the prompt itself can only be confirmed on the live site.
