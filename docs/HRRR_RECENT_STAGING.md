# HRRR recent-cycle staging

**Experimental staging only; never automatically publishes forecast maps to GitHub Pages.** The job checks the latest NOAA NODD HRRR f03/f02 inventory pair valid at the same UTC time, acquires just the 2-m TMP GRIB2 messages with verified byte ranges, decodes and spatially checks each with ecCodes, and creates two small regional COG/PNG images plus a same-valid-time forecast difference. The region/thermal palettes are the same as the earlier October 27 archive research pilot.

The validation blocks stale inventory (>10 min), old valid times (>2h), implausibly far-future valid times (>1h), wrong model init/lead/valid metadata, changes to byte ranges, invalid geodetic matching, missing spatial coverage and any derived assets exceeding 1 MB. Per-field GRIB transfer is capped at 64 MB, and only two messages are permitted.

The manifest records actual checked, process, cycle and valid times, transfer byte sizes and measured end-to-end runtime. It keeps provider first release, original first-seen, exact publication latency and independent forecast validation **unknown**. A passing build is an engineering QA step, not meteorological forecast skill evidence.

**Storage policy:** The generated images are ephemeral Actions artifacts (7-day retention) and are NOT automatically deployed or committed. No recurring bulk GRIB download is scheduled. Before enabling an automatic public model viewer: record several cycles of availability, establish an object-store/archive retention and budget, confirm independent geographic/GRIB bitmap QC, benchmark cost, build source/staleness-aware frontend controls, and review against native official NOAA fields.

Manual command with pinned scientific dependencies: python -m pipelines.hrrr_stage --out reports/recent-hrrr

Sources: https://registry.opendata.aws/noaa-hrrr-pds/ and NOAA EMC HRRR documentation.

## Verified real NOAA execution — October 27, 2026

GitHub Actions run: https://github.com/JacZerin24/stormchase-os/actions/runs/40566089453

At the check time, the source inventory selected genuine hourly HRRR 16Z f03 and 17Z f02 temperature fields, both valid 19Z. The pinned ecCodes/rasterio/scipy stack passed 19 deterministic tests, then performed a real two-message byte-range acquisition, decoded the values, georegistered the existing Southern Plains domain, and generated the COG/PNG images and forecast-cycle difference.

Measured in this run: source message transfer **2,360,308 bytes**; total raster and PNG assets (excluding manifest) **184,351 bytes**; Python end-to-end execution walltime **29.925 seconds**. These are workload observations, NOT a complete estimate of future Github Actions billing or network egress. The dependencies installation, queue time, Pages deployment and user serving are not included in that walltime metric. External independent forecast-field accuracy verification is still outstanding.

The complete artifacts are intentionally retained for seven days rather than promoted to public current-model maps. Publication/source latency cannot be established from one opportunistic index observation.