# Weather-data acceptance and verification plan

**Status: proposed checks; none in this document are marked completed.** Draft PR #1 has synthetic unit fixtures and CI, **not** a validated browser/operational NOAA integration. Follow current release gate [issue #2](https://github.com/JacZerin24/stormchase-os/issues/2).

## v0.1 live acceptance tests (capture exact date/time, response headers, anonymized sample and screenshots in an issue)

| Test | Expected evidence | Failure rule |
| --- | --- | --- |
| SPC service query | Actual `FeatureCollection` with polygon/multipolygon and expected `dn`, issue/valid/expire; inspect requests and browser CORS. Compare product boundaries/label/time with [SPC official outlook](https://www.spc.noaa.gov/products/outlook/). | Do not deploy incorrectly aligned or stale polygons; log provider status and sample. |
| SPC nonsevere/empty case | Zero features can mean no returned polygons; distinguish server/schema/filter errors and inaccessible source. | An ArcGIS error JSON object is **not** an empty forecast. |
| NWS API filter and alert identity | Compare filtered request with unfiltered active list in at least two conditions; confirm both warning event names selected, unique alert ids, `sent/effective/expires/ends`, and null-geometry counts. | Unsupported multi-event query must be replaced with a proven strategy; map is not complete alert inventory. |
| NWS revisions and expiry | Validate active/updated/cancelled behavior, warning geometry vs official products, no expired warnings displayed as live. | Reject silent retention of superseded warning polygon. |
| Timestamp and latency | Compare issued, valid, expired, original source GIS ingest and client retrieval; test UTC midnight rollover and explicit timezone parsing. | Missing/ambiguous timestamps remain null and flagged; do not use local now as a source timestamp. |
| Network resilience | Simulate CORS denial, HTTP 429/503, timeout, malformed JSON, aborted reload and offline reconnection; show error/stale prominently. | A blank map must not masquerade as no severe weather. |
| Rendering | Desktop/mobile MapLibre polygon placement over geographic reference, nested categories, alert overlay ordering, toggles, popups, zoom and keyboard navigation. | Incorrect CRS, geometry or visual layering blocks release. |
| Performance | Time request payload, parsing, map draw and memory on phone + laptop at sampled alert load. | Set performance budget only after measurement and optimize/clip as needed. |

## Deterministic tests to add before GRIB/model integration

- **Run/valid alignment**: model runs initialized at different UTC times with matching forecast valid time are compared using their individual lead time. Forecast initialization missing, changed or inferred from filename alone must be explicit.
- **Accumulated vs instantaneous**: 1-h precip or UH fields with start/end intervals are never labeled simply as valid at the end without interval provenance.
- **Missing grids**: missing vs actual zero vs below-threshold vs no-storm labels are independent states; mask and data coverage count accompany tiles.
- **Unit conversion**: knots/meters per second, Pa/hPa, K/C, geopotential m vs geometric height, storm-relative wind calculations tested on analytical and external reference cases.
- **Vertical profiles**: monotonic pressure profile checks, interpolated levels, parcel definition, virtual correction, storm-motion assumptions, layers above ground, surface elevation, missing data and validation against reference calculations.
- **Model schedule drift**: cycles published in a provider list are verified from current file inventories; do not infer that a model is available simply because an expected cycle passed.
- **Observation revisions**: retain scan/acquisition time, QC flags, provider-revised observations, representative footprint, bad/missing station reports and metadata history.
- **Historical replay**: an event simulation requesting a past decision time must not see forecasts or reports first published later. Record provider availability where provable; distinguish reconstructed estimates from observed historical availability.
- **Independent scientific checks**: derived composites/forecast fields benchmarked against MetPy/reference inputs, and any chase-target index evaluated using event-grouped independent holdouts, lead-time stratification, confidence intervals and baseline comparisons.

## Ingestion observability minimum

For each source and product: upstream URL/version, last attempt, last HTTP success, source issue/run, valid range, latest upstream update, first seen, last fetched, retry/backoff, bytes/features read, null geometry/missing grid counts, cached asset lineage/checksum, HTTP/error/parse issue and freshness policy status. Sample source latency distributions (p50/p90/p99 and missingness) **before** setting provider-specific freshness limits. Explicitly segregate simulated, experimental and official records.

## Release decision

**Pass requires:** observable real browser NOAA fetch + correct map overlay + genuine timestamps + two-provider failure isolation + working controls + completed CI + reviewed PR + actual GitHub Pages deployment test. A successful source documentation lookup or unit test alone is not passing evidence.
