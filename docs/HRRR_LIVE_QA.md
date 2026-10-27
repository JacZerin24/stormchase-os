# HRRR one-message live and ecCodes QA evidence

This workflow is **one-shot experimental** and targets the already selected NOAA NODD HRRR 2026-10-27 12Z +6h 2-m temperature message. It downloads the *.idx inventory, checks run/field/byte-range metadata, transfers only the specified GRIB message (64 MB cap), then decodes that GRIB via ecCodes and validates broad metadata/level/unit/run/valid/grid consistency plus finite-value temperature sanity bounds. SHA256, bytes and numeric bounds are saved; the original full national grid is **not committed or uploaded**.

A passing run is evidence of a real GRIB decode from one run/field, not evidence that multi-field operational ingestion, geospatial rendering, mesoscale-analysis algorithms or meteorological performance are verified. Later gates: independent field-value comparisons, null-mask/bitmap checks, spatial reprojection against known gridpoint coordinates, small-domain COG/tiles, multi-run comparison, latency and dollar-cost benchmark.

This is not scheduled to run repeatedly; avoid unbounded downloads. NODD NOAA remains the data provider and must be attributed. Reference: https://registry.opendata.aws/noaa-hrrr-pds/ .
