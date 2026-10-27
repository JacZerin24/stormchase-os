# Feature Inventory and Roadmap

Status: planning priorities, not implementation claims. Check individual PRs/CI and deployed site for current state.

| Priority | Release | Feature | Acceptance evidence |
| --- | --- | --- | --- |
| P0 | 0.1 | React/TS/Vite foundation | Typecheck, build and CI pass |
| P0 | 0.1 | Responsive dark MapLibre CONUS workspace | Working browser map on desktop/mobile |
| P0 | 0.1 | NOAA SPC Day 1 categorical map | GeoJSON overlay, correct legend, issue/valid/expire provenance, error state |
| P0 | 0.1 | Active NWS tornado/SVR warnings | Polygon overlay; excluded null geometries explicitly counted |
| P0 | 0.1 | GitHub PR checks and Pages deploy | Successful build/tests, verified live production URL |
| P0 | 0.1 | Documentation and provider limits | Source catalog, architecture, development guide, scientific checklist |
| P1 | 0.2 | SPC Days 1–3 hazard probabilities and CIG layers | Verify 2026 product schema, thresholds, interpretation |
| P1 | 0.2 | Mesoscale discussions, watches, alert details | Product linkage, geometry and timing checks |
| P1 | 0.2 | Data health + provenance inspection panel | Last successful update, latency, stale thresholds |
| P1 | 0.3 | Surface analysis, HRRR/RAP pilot domain | Unit and valid-time alignment checks |
| P1 | 0.3 | Soundings/hodographs/thermodynamic parameters | Validated MetPy/parcel algorithms, interactive plots |
| P2 | 0.4 | Model comparisons, CAM run trends/ensemble spreads | Cross-run valid-time pairing and provider QA |
| P2 | 0.5 | Radar/MRMS/satellite and observations | Latency/scan time, resource limits and licensing |
| P2 | 0.6 | Terrain/land-cover/road-network pilot | Documented coverage, CRS, road classes, closure age |
| P2 | 0.6 | Chase practicality context and routing | No safety guarantee, verified graph and legal constraints |
| P3 | 0.7+ | Historical analogs and calibrated targeting research | Independent holdouts, honest baselines, uncertainty |
| P3 | 0.8+ | Historical replay and forecast verification | Information-available-at-time filtering |
| P3 | 0.9+ | Mobile offline-aware live companion | Disconnection/reconnect and stale-data test matrix |

## v0.1 definition of done

PR merged after required tests; production Pages build succeeded; at least one authentic official overlay demonstrably renders in a real browser; all time fields sourced (not invented); map controls and responsive behavior smoke-tested; failures are disclosed instead of silent. A created PR alone does not satisfy this definition.

## Implementation slices

A. Commit docs/tooling and a map-first UI.
B. Load and render SPC categorical layer with official service provenance and geometry tests.
C. Load and render polygon-representable NWS alerts and show coverage limits.
D. Review CI, enable GitHub Pages, merge, run production browser smoke test, log discovered failures.
E. Only then advance to Days 2–3, probabilistic products, and conditional intensity.

## Next research gates

Check source availability/CORS/license/update cadence for every prospective service. Establish geographic truth sets, event-grouped/temporal holdouts, independent baseline methods, simulation replay cutoff enforcement, scoring/verification definitions, and reproducibility policies before any target-ranking claims.
