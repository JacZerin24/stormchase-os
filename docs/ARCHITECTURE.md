# System Architecture — Architecture Baseline

Status: proposed v0.1 baseline. Decisions are revised by PR with evidence.

```text
web/ — React + TypeScript + Vite
  ├── MapLibre map shell and responsive weather-analysis panels
  ├── adapters/ — official upstream response parsing + provenance normalization
  ├── weather-data hook — refresh, state, errors, stale indication
  └── layers — source-driven map overlays
         │
         ├── NOAA SPC ArcGIS FeatureServer (Day 1 categorical GeoJSON)
         ├── api.weather.gov (active alerts GeoJSON)
         └── CARTO hosted dark basemap style / tiles
.github/workflows/ — PR CI and main-branch GitHub Pages build/deploy
future:
api/         — FastAPI data access only when client-side feeds insufficient
pipelines/   — reproducible bulk ingestion and derived fields
research/    — versioned experiments, independent evaluation
tests/       — integration and contract fixtures
```

## Design rules

1. Weather products are typed by source, product, issuance, valid start/end, retrieval time, geometry semantics, and status. **Retrieval time is NOT issuance time.** Unknown timestamps stay unknown.
2. Adapter boundaries isolate provider changes; never assume geographic coverage just because an endpoint returns a FeatureCollection.
3. Layers are additive and can fail individually. Show unavailable, stale, and partial data distinctly. Refresh requests are abortable; retain last successful data with a visible error flag.
4. Model run/valid time pairing, unit transformations, projections, and probability semantics must be tested before environmental products are introduced.
5. Current v0.1 deploy is static, with no database and no server-side authentication. Browser calls cannot supply the NOAA API's recommended custom User-Agent; if necessary, migrate to an identifiable small proxy with conditional requests/caching.
6. Do not allow map style, basemap provider, alert geometry, or a renderer to silently stand in for safety guidance.
7. Prefer narrow vertical slices: e.g. one official field with full provenance + controls + tests before adding many fields.

## Future back-end boundaries

- `api/`: FastAPI endpoint contracts; request constraints; conservative caching; health metrics.
- `pipelines/`: provider adapters, normalization, timestamping, lineage, provenance checks, idempotent ingest.
- `research/`: experimental analysis wholly separated from operational data presentation and forecast verification.
- PostGIS/object storage only when persistence, spatial indexing, archival replay, or data-volume needs justify costs.
- Reliability-critical updates should not depend solely on scheduled GitHub Actions or a browser remaining open.

## Planned operational observability

Every feed: product, URL/provider, last fetch attempt, last success, issued/valid/expire, cache age, error, feature count, missing-geometry count, and completeness caveats. For v0.1 this is client-side only; centralized metrics and retries come later.
