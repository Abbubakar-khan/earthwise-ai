# EARTHWISE AI — Methodology

## Research question
Across selected Pakistani locations, how have near-surface air temperature and corrected precipitation changed over the selected historical period, how large are the estimated trends, and are they statistically distinguishable from no monotonic trend under the selected test?

## MVP design
- Locations: Lahore (31.5204, 74.3587), Islamabad (33.6844, 73.0479), Karachi (24.8607, 67.0011).
- Data: NASA POWER Daily API, T2M and PRECTOTCORR.
- Period: 2001–2025 requested; actual returned coverage must be reported per request.
- Aggregation: monthly mean for T2M; monthly sum of daily PRECTOTCORR.
- Trend magnitude: Sen's median slope, reported per decade.
- Trend test: Kendall rank correlation between elapsed time and values; p<0.05 is labelled significant for this unadjusted test.

## Interpretation
A positive temperature slope means the selected POWER point series increased over the analysis period. It does not establish why. A negative precipitation slope means the monthly precipitation total declined in that series; it does not alone prove drought risk.

## Limitations
1. POWER is gridded/model-derived analysis-ready data; it is not equivalent to a local station record.
2. A point query is not a province/district average or Pakistan-wide map.
3. Monthly aggregation reduces daily noise but does not remove seasonal structure.
4. Serial autocorrelation can inflate apparent significance. For publication-grade analysis, use seasonal Mann–Kendall and variance correction/pre-whitening where appropriate, plus sensitivity analysis.
5. Multi-city/multi-variable testing creates multiple-comparison concerns; apply an FDR procedure before making a large set of claims.
6. Precipitation is skewed and intermittent; report distribution/quantiles and inspect extremes in addition to monotonic trend.
7. No causal inference or guaranteed future prediction is made.
8. Validate a subset against PMD station data if permission/access is obtained.

## Data quality rules
- Preserve original raw response unchanged where practical.
- Record API request URL, coordinates, parameter codes, retrieval time and requested period.
- Treat values <= -900 as missing sentinel values.
- Report missingness and actual start/end dates.
- Do not silently fill missing observations.
