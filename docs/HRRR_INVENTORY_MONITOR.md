# HRRR lightweight availability monitor and measured latency gates

Status: **metadata-only source inventory**, not a scheduled GRIB publisher or operational severe-weather guidance. [NOAA's HRRR](https://emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/hrrr.php) is hourly, but individual forecast-hour/parameter files may arrive at variable times. This monitor reads only up to ten ~10-KB-sized `.idx` inventories on NOAA NODD's public S3 source per check (five pairs, two leads each), and seeks **two distinct model initializations valid at the same hour**: older cycle f03 and newer cycle f02. It checks an exact TMP/2-m field inventory and a bounded byte range, **not the GRIB message**.

## What the output proves

A successful state `pair_inventory_observed` establishes both required index records were accessible at the **`checkedAt` observation timestamp**. It does not establish that their byte ranges were downloadable or decoded, when the model completed, when the field first appeared, the real source issuance time, model numerical accuracy, or publication latency. `firstSeenAt` and `actualUpstreamFirstPublicationAt` deliberately remain `null`. The S3 Last-Modified header is recorded as object metadata and is **not** a guaranteed original publication time.

A `no_verified_pair` report is not interpreted as a model forecast of zero, and no invalid/HTTP 404/source-error input is promoted to map-ready. Candidate valid times range from the current UTC hour to at most +1 h initially, falling back four hours; no arbitrarily ancient map is automatically reused. Changes on scheduled jobs can be delayed/skipped under GitHub infrastructure load. This code has **no run-to-run persistent state**, so it cannot assert first-seen publication latency until durable observations are implemented.

## Execution and operating cost

`python -m unittest pipelines.tests.test_hrrr_inventory -v`

`python -m pipelines.hrrr_inventory --out reports/hrrr-inventory.json`

On `main`, GitHub Actions checks once/hour at minute 37 UTC. There is **no data write to the repository**, no Pages deployment trigger, no user-facing layer update, and no repetitive NOAA GRIB bulk download. Artifacts are retained 14 days for inspection. At worst 24 jobs/day × ten small index requests; actual requests stop early when a valid pair is found. Scheduled actions and their latency are not an operational or alerting uptime contract. The workflow is intentionally cheap; exact GitHub compute/bandwidth costs vary by account and should be monitored before adding decode/publish jobs.

**Next gates:** real probe results, persist first-seen records without rewrite, attempt two bounded indexed message acquisitions, full ecCodes time/unit/spatial/bitmap checks, compare values independently, benchmark CPU/egress and archive size, and decide storage/CDN before any genuinely updating model field enters the public website. Rap/RRFS inventory remains a **separate source validation task**; do not assume identical file naming.
