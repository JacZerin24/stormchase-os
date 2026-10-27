# StormChase OS

A map-first severe-weather intelligence and storm-chasing decision-support platform. **Early development: not an official warning service or safety/navigation system.**

## Implemented and independently checkable

- React + TypeScript + Vite + MapLibre GL JS; responsive dark/light CONUS map, regional presets, geographic controls and browser-failure states.
- NOAA/SPC **Days 1–3 categorical** polygon layer and active NWS tornado/severe-thunderstorm warning polygons, each with appropriate source/validity/retrieval metadata. These feeds are decision support, not guaranteed warning delivery.
- One **historical October 27, 2026 HRRR research case**: real NOAA 2-m temperature from 12Z f06 and 15Z f03, both valid 18Z; small Plains-domain geographic images, COGs and newer-minus-older forecast comparison. Map layer is labeled archived/not current.
- Verified GitHub Pages delivery (HTTP 200 and SHA-256 integrity), real NOAA source checks and desktop/mobile Chromium local-browser QA.
- Behind the scenes: **hourly index-only HRRR availability checks** and a **separate five-day observation-history branch**, plus a manually dispatched, research-only near-current HRRR two-run GRIB-to-raster staging pipeline. Neither automatically publishes current HRRR fields to the map.
- SPC probability/conditional-intensity layers remain research-only (schema surveyed), not public hazard maps. RAP source inventory has a verified NOMADS field index; RAP GRIB content and grid remain unvalidated.

No calibrated chase-target probabilities, automated routing, live model-data publication service, production soundings, radar/MRMS or independent model forecast skill validation are claimed.

## Run locally

Requires Node.js 22 or newer.

```bash
cd web
npm ci
npm run dev
npm run typecheck
npm test
npm run build
```

The locked Vite development server prints the local address. A web browser with WebGL and access to the third-party basemap and NOAA endpoints is required. The site remains usable for basic navigation when a weather feed fails, but missing/stale weather layers are identified.

## Project reference documents

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap and prioritized feature inventory](docs/ROADMAP.md)
- [Scientific research and verification](docs/RESEARCH.md)
- [Data-source catalog and limitations](docs/DATA_SOURCES.md)
- [Decisions and operational limitations](docs/DECISIONS.md)
- [Development and deployment guide](docs/DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)
- [Recent-model staging and cost measurements](docs/HRRR_RECENT_STAGING.md)
- [Hourly HRRR availability monitor](docs/HRRR_INVENTORY_MONITOR.md)
- [Bounded observed-availability history](docs/HRRR_AVAILABILITY_HISTORY.md)
- [Georeferenced historical HRRR research case](docs/HRRR_GEOREFERENCING_PILOT.md)
- [NOAA live browser QA limitations](docs/NOAA_BROWSER_QA.md)

## Deployment

The site is published at https://jaczerin24.github.io/stormchase-os/. Main-branch GitHub Pages deployments and public HTTPS/asset-hash checks have passed. Merge a reviewed PR only after its relevant CI/scientific acceptance gates; future deployments and NOAA provider outages can still fail. GitHub Actions scheduled data monitoring is best-effort, not an operational NOAA service.

## Important limitations

StormChase OS is experimental decision-support software. For protective decisions, use official NWS/SPC sources directly; no data completeness, alert delivery time, or safe route is guaranteed. NOAA data-service outages, CORS, rate limiting, alert features without polygons, basemap outages, and browser/network restrictions may reduce map availability. See the data catalog for provider usage notes.
