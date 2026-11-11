# Research brief — EARTHWISE AI
**FORGE CYBER LAB | The Intelligent Earth Trend Observatory**

## Abstract
EARTHWISE AI is a Pakistan-first Earth-system trend exploration prototype. It is designed to combine NASA Earth science datasets, transparent statistical trend estimation, regional comparisons, and evidence-bound explanations. The minimum viable implementation focuses on daily NASA POWER point time series for near-surface air temperature (T2M) and corrected precipitation (PRECTOTCORR) in Lahore, Islamabad, and Karachi. Daily values are aggregated to monthly summaries, then analyzed using Sen's slope and a Kendall monotonic association test. Results are presented with period, sample size, data coverage, and caveats. GPM IMERG precipitation and MODIS vegetation indices are planned extensions, not claimed as completed integrations.

## Problem
Environmental data are distributed across products with different spatial and temporal resolutions. Users need to identify what is changing, where, by how much, and whether a trend is statistically significant. A single dashboard chart or chatbot is insufficient without reproducible data provenance and statistical evidence.

## Innovation
The Earth Trend Fingerprint summarizes temperature and precipitation trend direction, magnitude, significance, and data quality for a selected location. Opposite Earth compares locations under the same variable and period. The AI Earth Scientist translates computed statistics into plain language while explicitly avoiding unsupported causal claims.

## MVP research question
How have near-surface air temperature and corrected precipitation changed in Lahore, Islamabad, and Karachi over the requested 2001–2025 period, and what are the estimated trend magnitudes and unadjusted Kendall-test significance levels?

## Expected outputs
- Daily source CSV and request metadata for each city.
- Monthly time series for each variable.
- Sen slope per decade, Kendall tau, p-value, and coverage.
- City comparison table.
- Evidence-bound explanatory text and downloadable CSV.

## Results status
No observed trend values are asserted in this brief because live NASA POWER requests have not yet been executed in the user's runtime. The software is prepared to fetch and calculate them. Fill this section only with actual retrieved outputs.

## Scope boundaries
This MVP is not a forecasting system, disaster alert service, causal attribution study, or national gridded assessment. City point samples cannot be generalized to all of Pakistan.
