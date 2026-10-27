# Model field viewer contract and comparison logic

Implemented here: a strict TypeScript metadata validator plus same-valid-time/different-run comparison utility, with deterministic unit tests. These functions **do not fetch, decode, or render actual GRIB fields**. They are intended to prevent the future map from showing nonvalidated assets as legitimate meteorological data.

Fields retain: model ID, parameter/level, units, forecast cycle, lead, valid instant, accumulation time bounds, original source URL, geospatial asset reference, CRS, SHA256, pipeline version, first-observed publication availability proxy, missing fraction, and processing state. First-seen time is NOT synonymous with upstream actual first publication time.

Only validated entries with QA'd units/CRS/hash/asset can be offered to future renderer. The compareRuns function never makes up missing model cycles and aligns the *forecast valid time*, rather than cycle number.

Remaining gates: a true real-source HRRR/RAP/RRFS ingest producing decoded and spatially benchmarked forecast assets; HTTP serving/cache/asset manifest; UI source/valid time controls and localized legend; independent field-unit and geometry checks; real-browser map rendering with missing data masks. No dummy forecast graphics should appear on the published website.

See docs/WEATHER_DATA_CONTRACT.md and docs/HRRR_INGEST_PILOT.md on the applicable integration branches.
