# Changelog

## 2026-10-27 — Meteorological integration and provenance milestones

- Merged official SPC categorical Day 1–3 map controls, enhanced NOAA/NWS source/valid time parsing, stale/error health states and bounded retries, with official HTTPS and desktop/mobile Chromium testing. Actual active-event NWS warning revisions/cancellations and human polygon geometry QA remain open.
- Merged real October 27 HRRR archived test case: two NOAA GRIB2 runs valid at the same time; geographically matched Plains temperature images and COGs with pixel-reference QA and browser controls for per-run and difference mode. Not an independently skill-verified forecast and not current data.
- Verified public GitHub Pages HTML, JS and all archived NOAA HRRR assets with HTTP 200 and matching SHA-256 hashes. The deployment is not an official warning delivery system.
- Implemented research-only hourly HRRR f03/f02 index availability checks and an independently persisted, bounded observation ledger on a separate branch, distinguishing first observed HTTP200 from NOAA actual publication time. No scheduled bulk GRIB download and no hourly Pages rebuild.
- Verified the one-shot near-current two-model-run HRRR scientific staging pipeline against real NOAA inventories and GRIB message bytes: 2,360,308 source bytes, 184,351 derived bytes and 29.925 seconds Python processing in one sampled run; output is an ephemeral research artifact, not a live public map.
- Surveyed official SPC probability/CIG layer metadata; full conditional-intensity graphic/legend semantics and actual probability overlays remain incomplete. Began RAP provider-specific NOMADS inventory research (review pending).
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
