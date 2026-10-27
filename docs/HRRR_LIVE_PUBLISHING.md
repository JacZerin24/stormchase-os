# Phase 1 — Controlled near-current HRRR publishing

**Research-beta status:** a scientifically source/geometry-checked regional MODEL FORECAST, not NEXRAD, an NWS warning service, forecast skill verification or calibrated severe-weather guidance.

## Scope

The first public pilot is 225 × 160 pixels covering the previously tested Southern Plains box (103°W to 94°W, 33°N to 39.4°N). It displays two real source-run 2-m temperature forecasts valid at the same hour (older f03 and newer f02) and the newer-minus-older temperature forecast difference. This is deliberately smaller than the 69-field HRRR convective catalog. Automatic REFC/UH/CAPE/upper-level publishing must pass separate source-mask/physical-unit and independent-reference scientific gates before expansion.

## Data provenance and safety checks

The existing stage uses actual NOAA NODD HRRR GRIB2 indexed byte-range fetches, init/lead/valid match, native Kelvin units, geographic nearest native point registration, COG and PNG integrity and ecCodes independent geographic assignment spot checks. Candidate validation rejects missing/mismatched images or hashes, wrong region/CRS, incomplete geographic coverage, invalid cycles, old (>2h) valid times and >1h future valid times. It retains observed inventory check time distinct from source initialization, forecast valid time and unknown original publication time. Independent forecast-skill validation, native bitmap correctness and actual observational temperature error are NOT asserted by these checks.

## Low-cost publishing and rollback

An hourly GitHub Actions schedule at minute 48 UTC (best-effort) attempts exactly two temperature GRIB message downloads. On scientific-source failure it stops before deploying, leaving the last successful static website artifact in place. A successful result makes a regional cache of six immutable forecast valid-hour snapshots, with per-image SHA256s, a validity/initialization catalog and explicit scientific disclaimers. That cache lives in a seven-day GitHub Actions artifact, NOT in hourly commits to GitHub source control. The whole cache is limited to 4 MB and each newly staged candidate to 850 KB. A successful job builds/deploys a new GitHub Pages artifact containing that cache under /live/hrrr/.

Ordinary main-branch source deployments must retrieve the latest successful model artifact to avoid removing currently published assets. The browser must show data age and stop calling any model overlay current after its age threshold. GitHub scheduled workflows may be delayed, dropped or disabled; this does not meet NWS operational uptime standards. Forecast maps are not watches, warnings or chase routing guidance. Review actual GitHub Actions minute consumption and deploy/hosting limits before scaling to many parameters/forecast hours/large domains.

Before operational expansion: independent native bitmap/mask QA, reference-field verification, rate and latency sampling, domain/tiling scalability, storage/CDN retention and billing, and a more reliable scheduler with monitoring.
