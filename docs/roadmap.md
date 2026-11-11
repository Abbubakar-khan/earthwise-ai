# Delivery roadmap

## Phase 1 — reliable MVP
- [x] Establish project identity and research question.
- [x] Implement NASA POWER daily point client.
- [x] Implement cleaning and monthly aggregation.
- [x] Implement Sen slope and Kendall test.
- [x] Implement evidence-constrained explanations.
- [x] Implement Streamlit MVP and tests.
- [ ] Run live requests for all three cities.
- [ ] Review actual API metadata, missingness, and returned units.
- [ ] Capture genuine result tables/plots.

## Phase 2 — scientific strengthening
- Add seasonal Mann–Kendall / autocorrelation-aware inference.
- Add false-discovery-rate correction across city-variable comparisons.
- Add PMD station validation if access is granted.
- Add a transparent region/grid sampling design; do not call three city points Pakistan-wide coverage.

## Phase 3 — extra data layers
- GPM IMERG: download a consistent V07/V07B retrospective product and aggregate carefully.
- MODIS: obtain MOD13Q1 V061 NDVI/EVI plus DetailedQA; apply QA masks and 0.0001 scale factor.
- FIRMS: optional hotspot context only; detections are not confirmed fire reports.

## Final submission assets
Research report, technical report, source/data register, demo recording, screenshots, README, reproducible app and limitations statement.
