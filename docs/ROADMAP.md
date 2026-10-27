# Feature Inventory and Roadmap

## Convection Desk expansion — October 27, 2026

The HRRR workstream is expanded from temperature-only research to a complete severe-convection field architecture (see [HRRR CONVECTION ROADMAP](HRRR_CONVECTION_ROADMAP.md)). Official NCEP/NODD actual `wrfsfc` index testing matched **69/69 configured field, level and time-window identities** on the audited 17Z f02 run. This includes REFC, hourly 2–5 and 0–2 km UH max/min, updraft, CAPE/CIN variants, storm-relative helicity, vertical shear components, 250/300/500/700/850/925 hPa data, precipitation windows and near-surface parameters.

A separate *archived* real-data example now stages simulated composite reflectivity, hourly and contiguous 3-hour UH swaths, 500-hPa height, 700-hPa temperature, SB CAPE and 0–1 km SRH. All seven archived PNG layers passed local Chromium desktop/mobile interaction checks; latest generation/native-unit QA remains its separate feature-branch acceptance gate. **69 source index records are not 69 published forecast maps.**

Next priority is not additional arbitrary model parameters; it is a source-time-aware, bounded near-current HRRR map production/asset cache, real upper-level charts (contours, wind vectors and moisture), UH swath/object evolution with scientifically distinct track labels, point soundings with complete vertical data, and independent reference verification. Do not promote these archived examples to operational current guidance.

## Implementation status verified October 27, 2026

| Workstream | Evidence-backed state | Remaining blocker |
| --- | --- | --- |
| SPC/NWS polygons | Day 1–3 categorical and TOR/SVR browser feeds implemented; real-source and browser QA | Active-event warning revisions, manual official geographic comparison and source latency reliability |
| Historical HRRR | Two genuine same-valid-time runs, COG and PNG geographic outputs with reference pixel checks; Pages asset SHA verified | Independent gridded numerical/bitmap QA and dynamic current model publishing |
| HRRR inventory | Hourly `.idx` source checks; five-day durable first-observed index ledger on separate telemetry branch | Do not confuse HTTP index observation with first published GRIB; measure more cycles and reliability |
| Recent HRRR staging | Genuine recent f03/f02 same-valid-time temperature pipeline, measured 2.36 MB transfer / 184 KB derived assets / 29.9 s Python walltime in one run | Storage/retention/egress budget and independent field QA before enabling live public maps |
| SPC probabilities/CIG | Real official layer attribute schema sampled, labels and DN semantics distinguished | Complete probability and CIG graphic/geometry/definitions and live overlay tests |
| RAP | Official NOMADS RAP f02/2-m temperature inventory verified, including dotted GRIB submessages | Full RAP GRIB decoding, numerical/geospatial QA and HRRR alignment not verified; no RAP map |
| Soundings/hodographs | Experimental wind-only diagnostics compared to pinned MetPy synthetic profiles | Observed/model profile provenance, thermodynamics and observed-case verification |

**Caveat:** Production Pages and CI success do not by themselves demonstrate operational accuracy or warning delivery. Experimental assets are deliberately identified, and no model outputs are presented as independently calibrated severe-weather probabilities.
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
