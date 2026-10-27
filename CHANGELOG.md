# Changelog

## Unreleased — v0.1 foundation (2026-10-27)

- Created charter-aligned repository architecture, roadmap, scientific research/verification standards, data-source catalog and development guide.
- Committed responsive React/TypeScript/Vite/MapLibre map-first CONUS workspace with NOAA SPC categorical and NWS active warning adapters.
- Added source/retrieval timestamps, explicit errors, stale/expired layer hiding, layer toggles, source links, and refresh behavior.
- Added GitHub Actions PR checks and Pages deployment workflow.
- Web CI run #2 **passed**: dependency installation, TypeScript, 7 adapter unit tests and Vite build (commit `3bd1eba`).
- Temporary npm 10 peer resolver workaround in `web/.npmrc`; track removal after a committed lockfile and controlled upgrade.
- Draft PR #1 remains open. **Browser-based live NOAA checks and GitHub Pages production deployment are not verified.** Release criteria and follow-up tracked in issue #2.
