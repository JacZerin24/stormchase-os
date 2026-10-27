# Changelog

## 2026-10-27 — Severe convection and upper-air HRRR expansion

- Verified **69/69 actual NODD HRRR wrfsfc GRIB field+level+forecast-interval identifiers** for one 17Z f02 cycle. Registry spans upper-level winds and height/temperature, surface/mixed/most-unstable CAPE/CIN, SRH and shear components, simulated convective morphology, hourly UH, updrafts/hail, moisture, and accumulation-aware precipitation. This is an inventory verification, not proof all were decoded.
- Produced seven **real, historical** georeferenced images using eight NOAA GRIB2 message acquisitions from 17Z Oct 27: simulated composite reflectivity, hourly 2–5km UH, 17–20Z 2–5km UH maximum swath, 500-hPa height, 700-hPa temperature, SB CAPE and 0–1km SRH. Native run/valid/step and grid/units checks, sampled geographic QA, and source/image SHA checks included. UH GRIB units are unresolved by ecCodes local parameters; published NCEP unit interpretation is separately attributed.
- Added an optional map-based archived convective field selector, fixed per-variable scales, temporal/provenance labels, weak-UH transparency warning, and explicit distinction between simulated reflectivity, hourly UH swaths and measured radar/storm tracks. Desktop/mobile Chromium QA passed; current-cycle public model publication remains **unimplemented**.
- Added [full convection architecture and validation plan](docs/HRRR_CONVECTION_ROADMAP.md), including actual 250/300/500/700/850 charts with contours/vectors, effective-layer diagnostics, UH/reflectivity forecast object association, full vertical `wrfprs` soundings, multi-cycle trends, and observation/model verification.

## 2026-10-27 — Meteorological integration and provenance milestones

- Merged official SPC categorical Day 1–3 map controls, enhanced NOAA/NWS source/valid time parsing, stale/error health states and bounded retries, with official HTTPS and desktop/mobile Chromium testing. Actual active-event NWS warning revisions/cancellations and human polygon geometry QA remain open.
- Merged real October 27 HRRR archived test case: two NOAA GRIB2 runs valid at the same time; geographically matched Plains temperature images and COGs with pixel-reference QA and browser controls for per-run and difference mode. Not an independently skill-verified forecast and not current data.
- Verified public GitHub Pages HTML, JS and all archived NOAA HRRR assets with HTTP 200 and matching SHA-256 hashes. The deployment is not an official warning delivery system.
- Implemented research-only hourly HRRR f03/f02 index availability checks and an independently persisted, bounded observation ledger on a separate branch, distinguishing first observed HTTP200 from NOAA actual publication time. No scheduled bulk GRIB download and no hourly Pages rebuild.
- Verified the one-shot near-current two-model-run HRRR scientific staging pipeline against real NOAA inventories and GRIB message bytes: 2,360,308 source bytes, 184,351 derived bytes and 29.925 seconds Python processing in one sampled run; output is an ephemeral research artifact, not a live public map.
- Surveyed official SPC probability/CIG layer metadata; full conditional-intensity graphic/legend semantics and actual probability overlays remain incomplete. Verified provider-specific RAP NOMADS inventory for 2-m temperature (no RAP GRIB decoding or geographic comparison).
- **Remaining scientific gates:** independent model-reference field and bitmap validation, real-world human map polygon comparisons, cost-aware immutable model asset storage/publication, real-time latency characterization, CAPE/thermodynamic profile QC, RAP model-grid validation and hazard-specific SPC probability/CIG overlays.
- Source of truth: reviewed GitHub changes, test runs and docs; older entries below capture status as originally written and may now be superseded.
## 2026-10-27 — Dual-theme visual identity (reviewed deployment change)

- Reworked the application visual language around Barlow Condensed/IBM Plex fonts, squared field-instrument panels and neutral graphite/copper styling.
- Added warm light and charcoal dark themes, persistent theme preference (with OS-first default), and matched CARTO Positron/Dark Matter map styles.
- Preserved live SPC and NWS overlay metadata, risk colors and refresh semantics across theme changes; added theme resolver tests and manual QA checklist.
- Deployment and real-browser checks are tracked separately; this entry does not certify data-feed availability or operational reliability.

## Unreleased — v0.1 foundation (2026-10-27)

- Created charter-aligned repository architecture, roadmap, scientific research/verification standards, data-source catalog and development guide.
- Committed responsive React/TypeScript/Vite/MapLibre map-first CONUS workspace with NOAA SPC categorical and NWS active warning adapters.
- Added source/retrieval timestamps, explicit errors, stale/expired layer hiding, layer toggles, source links, and refresh behavior.
- Added GitHub Actions PR checks and Pages deployment workflow.
- Web CI run #2 **passed**: dependency installation, TypeScript, 7 adapter unit tests and Vite build (commit `3bd1eba`).
- Temporary npm 10 peer resolver workaround in `web/.npmrc`; track removal after a committed lockfile and controlled upgrade.
- Draft PR #1 remains open. **Browser-based live NOAA checks and GitHub Pages production deployment are not verified.** Release criteria and follow-up tracked in issue #2.
