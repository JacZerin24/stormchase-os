# HRRR one-message live and ecCodes QA evidence

This workflow is **one-shot experimental** and targets the already selected NOAA NODD HRRR 2026-10-27 12Z +6h 2-m temperature message. It downloads the *.idx inventory, checks run/field/byte-range metadata, transfers only the specified GRIB message (64 MB cap), then decodes that GRIB via ecCodes and validates broad metadata/level/unit/run/valid/grid consistency plus finite-value temperature sanity bounds. SHA256, bytes and numeric bounds are saved; the original full national grid is **not committed or uploaded**.

A passing run is evidence of a real GRIB decode from one run/field, not evidence that multi-field operational ingestion, geospatial rendering, mesoscale-analysis algorithms or meteorological performance are verified. Later gates: independent field-value comparisons, null-mask/bitmap checks, spatial reprojection against known gridpoint coordinates, small-domain COG/tiles, multi-run comparison, latency and dollar-cost benchmark.

This is not scheduled to run repeatedly; avoid unbounded downloads. NODD NOAA remains the data provider and must be attributed. Reference: https://registry.opendata.aws/noaa-hrrr-pds/ .


## Observed successful test — 2026-10-27

[GitHub Actions run 40553115115](https://github.com/JacZerin24/stormchase-os/actions/runs/40553115115) completed successfully. It retrieved and ecCodes-decoded a real NOAA HRRR CONUS 12Z cycle, forecast hour 6, valid 18Z, two-meter temperature (`paramId=167`, `shortName=2t`, units K, `heightAboveGround=2`, Lambert projection). The 1,182,603-byte message contained 1,905,141 decoded finite grid points; observed minimum/maximum were approximately 261.003–307.378 K. Exact content SHA-256: `183e75c9d4d036953c915dba02971861c7b5872f937c707f56d38f71c0bd18b1`.

**Interpretation:** successful GRIB transport, identity checks, decoding, and broad physical sanity only. This does **not** establish independent gridded forecast accuracy, spatial coordinate alignment, area-weighted statistics, forecast verification, or operational first-publication latency. No graphics, tiles or live viewer were deployed.
