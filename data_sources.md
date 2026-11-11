# Data source register

| Priority | Dataset | Variables | Resolution / cadence | Role | Status in this package |
|---|---|---|---|---|---|
| 1 | NASA POWER Daily API | T2M, PRECTOTCORR | Parameter-dependent native grid; daily | Core point time-series | Implemented client; live retrieval must be run |
| 2 | GPM IMERG V07/V07B | precipitationCal | ~0.1° / ~10 km; half-hourly and aggregates | Independent precipitation layer | Research plan only |
| 3 | MODIS MOD13Q1 V061 | NDVI, EVI, DetailedQA | 250 m; 16-day | Vegetation greenness | Research plan only |
| 4 | NASA FIRMS | active fire detections | Sensor/product dependent | Context only | Optional; not implemented |

## Official references
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA POWER temporal API overview: https://power.larc.nasa.gov/docs/services/api/temporal/
- NASA GPM data directory: https://gpm.nasa.gov/data/directory
- NASA IMERG V07 technical documentation: https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation
- MODIS MOD13Q1 V061 catalogue: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1/
- NASA Space Apps 2026 challenge: https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/

## Notes
POWER Daily API docs state daily data are available from 1981 to near-real-time and default time standard is LST unless UTC is requested. This client explicitly requests UTC. Check the returned header/parameter metadata and actual units for each run.
IMERG V07B documentation lists ~10 km / 0.1° and coverage back to January 1998, with latency dependent on product stream.
MOD13Q1 V061 provides NDVI/EVI at 250 m every 16 days and includes quality information; apply QA masking and scale factor 0.0001 before analysis.
