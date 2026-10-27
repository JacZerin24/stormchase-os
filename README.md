# StormChase OS

A map-first severe-weather intelligence and storm-chasing decision-support platform. **Early development: not an official warning service or safety/navigation system.**

## v0.1 scope

- React + TypeScript + Vite and MapLibre GL JS; responsive dark-mode CONUS map.
- Official NOAA/SPC Day 1 categorical outlook and NWS active tornado/severe-thunderstorm alert geometry, with source attribution, issuance/validity information where available, fetch-time status and explicit errors.
- Tests, CI, and a GitHub Pages deployment workflow. Deployment requires repo settings and a successful main-branch workflow run.

This project begins from a clean repository. v0.1 intentionally has no chase-target scores, automated routing, radar, soundings, or forecast-model interpretation.

## Run locally

Requires Node.js 22 or newer.

```bash
cd web
npm install
npm run dev
npm run typecheck
npm test
npm run build
```

The Vite development server prints the local address. A web browser with WebGL and access to the third-party basemap and NOAA endpoints is required. The site remains usable for basic navigation when a weather feed fails, but missing/stale weather layers are identified.

## Project reference documents

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap and prioritized feature inventory](docs/ROADMAP.md)
- [Scientific research and verification](docs/RESEARCH.md)
- [Data-source catalog and limitations](docs/DATA_SOURCES.md)
- [Decisions and operational limitations](docs/DECISIONS.md)
- [Development and deployment guide](docs/DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)

## Deployment

Merge a reviewed PR to `main` after passing `Web CI`. In **Settings → Pages**, choose **GitHub Actions** as the publishing source. The `Deploy Pages` workflow should build `web/dist` and deploy to https://jaczerin24.github.io/stormchase-os/ when GitHub Pages is enabled and the workflow succeeds. Do not assume that a commit or PR alone means the website is live.

## Important limitations

StormChase OS is experimental decision-support software. For protective decisions, use official NWS/SPC sources directly; no data completeness, alert delivery time, or safe route is guaranteed. NOAA data-service outages, CORS, rate limiting, alert features without polygons, basemap outages, and browser/network restrictions may reduce map availability. See the data catalog for provider usage notes.
