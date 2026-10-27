# Weather-data contract and time semantics

**Status (2026-10-27): proposed interface specification, NOT a deployed API.** Coordinate future frontend/backend changes against this document. Current draft PR #1 uses local browser adapters in `web/src/data/weather.ts` and the `useWeather` hook; those exports remain the **implemented** v0.1 contract until an explicit migration PR.

## Contracts in draft v0.1

- SPC categorical: `fetchOutlook(signal): Promise<OutlookData>`. `OutlookData` includes `geometry` (Polygon/MultiPolygon GeoJSON FeatureCollection), `times.issued`, `times.valid`, `times.expires`, `times.gisIngested`, `sourceFile`. Numeric `dn` is the categorical key: 2/TSTM, 3/MRGL, 4/SLGT, 5/ENH, 6/MDT, 8/HIGH.
- NWS warnings: `fetchAlerts(signal): Promise<AlertData>`. `AlertData` includes `geometry`, `totalMatchingCount`, `missingGeometryCount`, `newestSent`. Only polygon/multipolygon geometries can be drawn. An unmapped alert MUST NOT be interpreted as an absent alert.
- `FeedState<T>` has `data`, `state: loading|ready|error`, `lastSuccess`, `error`. A successful browser fetch time is not the product's issue time. The current app refreshes at 5-minute intervals and suppresses data after a failed fetch or when retrieval is older than 15 minutes. These numbers are **current client behavior**, not measured NOAA product latency or a universal freshness policy.
- Provider queries are built by `spcUrl()` and `alertUrl()`. SPC is `SPC_wx_outlks/FeatureServer/1/query` with GeoJSON; NWS is `/alerts/active` requesting GeoJSON. Live CORS, parameter behavior, completeness and cross-browser response handling **remain unverified**.

## Proposed provider-independent product envelope (v0.2+)

Use a *versioned*, schema-validated DTO rather than exposing GRIB, BUFR, CAP, upstream ArcGIS properties, or opaque derived arrays to map components. Proposed TypeScript interface:

```ts
type ProductKind = 'official_forecast' | 'official_warning' | 'observation' |
  'model_forecast' | 'analysis' | 'derived_experimental';
type Quality = 'ok' | 'partial' | 'missing' | 'stale' | 'error' | 'unknown';
type IsoUtc = string; // parse and validate exact UTC ISO-8601 instants

interface WeatherProductEnvelope<T> {
  schema_version: 'weather-product/1';
  product_id: string;           // stable provider+product identity
  product_kind: ProductKind;
  source: { provider: string; dataset: string; product: string;
    url: string; license_url?: string | null; };
  version: { upstream_id: string | null; revision: string | null;
    content_hash: string | null; };
  time: {
    issued_at: IsoUtc | null;             // when forecast/message issued
    forecast_reference_at: IsoUtc | null; // NWP model cycle; NOT fetch time
    valid_start_at: IsoUtc | null;
    valid_end_at: IsoUtc | null;
    observed_at: IsoUtc | null;           // observed time, scan or launch
    source_ingested_at: IsoUtc | null;    // upstream publication/ingest
    first_seen_at: IsoUtc | null;         // first successfully observed by us
    retrieved_at: IsoUtc;                 // our most recent successful retrieval
  };
  spatial: { crs: string; bbox: [number,number,number,number] | null;
    geometry_role: 'forecast_area' | 'alert_polygon' | 'grid' |
      'observation_location' | 'coverage' | 'none'; };
  quality: { state: Quality; age_seconds: number | null;
    missing_reason: string | null; notes: string[];
    missing_geometry_count?: number; upstream_feature_count?: number; };
  data: T; // GeoJSON for polygons, reference to tiled/array asset for grids
}
```

Exact field names, dimensional metadata and serialization remain subject to frontend review and a fixture/validator implementation. Do **not** claim this interface is available at a runtime URL yet.

## Future HTTP API (proposed, not implemented)

- `GET /api/v1/catalog`: available providers/products, units, domains, release status, supported parameters, update policy.
- `GET /api/v1/products/{product_id}?valid_at=<UTC>&run_at=<UTC>`: an immutable product revision or typed error; `run_at` required for NWP; never silently change model cycle.
- `GET /api/v1/layers/{layer_id}/manifest?run_at=<UTC>&valid_at=<UTC>`: tile/COG/GeoJSON asset metadata, color scale, CRS, missing pixels, source hash and spatial coverage.
- `GET /api/v1/runs?model=<id>&available_before=<UTC>`: cycle inventory with `expected`, `available`, `partial`, `failed` status and first-publication time.
- `GET /api/v1/profiles?model=<id>&run_at=<UTC>&valid_at=<UTC>&lat=<...>&lon=<...>`: versioned vertical profile with pressure, height, T, Td, u/v, units, gridpoint/interpolation/QC method.
- `GET /api/v1/health`: per-feed last successful ingest, last attempt, last source update, lag, error, completeness and status. These are API designs, not live endpoints.

HTTP errors: 404 unavailable product, 422 invalid combination, 503 upstream unavailable, 200 with `quality.state='partial'` only for known partial data. Do not map errors, missing pixels or no upstream response to zero weather risk.

## Scientific invariants and storage keys

1. All instants normalized to timezone-aware UTC. Retain original provider field/value in raw immutable records. Reject ambiguous timezone-less times except explicitly documented formats from a particular adapter.
2. `valid_at = forecast_reference_at + step` for a point-valid NWP field; interval-accumulation products require **both interval bounds**. The comparison UI aligns *valid* times but **never discards source run times**, lead times, ensemble member, grid/projection or processing lineage.
3. For a real-time alert, `sent`, `effective`, `onset`, `expires`, `ends`, and CAP update/revision chains have different meanings. A CAP geometry can be null. Retain authoritative alert ID, affected zones and links even if a polygon cannot be rendered.
4. For a grid variable record GRIB discipline/category/parameter, level and level type, units, interval processing, grid spacing/CRS, forecast model/version, member ID and ensemble statistic. Record which lead fields did not arrive.
5. For an observed layer, `observed_at` is the scan/station/launch timestamp, not the time the client downloaded it. For satellite distinguish scan start/end, processing, product publication and tile generation. Display estimated latency only when measured; do not fabricate a clock.
6. Cache key: `provider/product/version/run/valid/window/level/parameter/member/grid/processing_version`. Do not overwrite old runs with the newest. Latest is an **alias** to a resolved immutable revision with last-known publication time.
7. Historical replay must enforce `first_seen_at <= decision_at` and, when known, upstream publication availability too. Current reprocessed products are disallowed in an as-issued reconstruction unless clearly tagged retrospective.
8. Derived diagnostics: pressure interpolation, parcel definition, wet-bulb/virtual-temperature choice, storm-motion estimate, Bunkers/SRH algorithm, effective-layer rules, units, missing-level policy, and software version are required provenance.

## Client behavior agreed for implementation

- Every layer has visible provider/product and valid time; details show issue/run, last retrieval, and errors.
- Quality `missing`, `partial`, `stale`, `error` must be visually distinct from a meteorological zero. Expired warnings are not presented as currently active.
- The renderer accepts only validated WGS84-lon/lat GeoJSON or tiles with an explicit projection; never silently reinterpret NAD83 or model projection coordinates.
- Layer failures are isolated. Cache may preserve last-known data for inspection but **never re-label old data as current**.
- Continue showing direct links to authoritative NWS/SPC products; StormChase OS remains supplementary decision support.

## Release checks

Current v0.1: verify actual NOAA responses and CORS in a real browser; compare SPC category/issue/valid/expiry to official text/graphics; verify NWS event filtering and null geometry; simulate malformed JSON/HTTP failure/empty feeds; test UTC display, time rollover, cache expiry and MapLibre rendering. Future: add schema fixtures and golden GRIB metadata tests, interval accumulation tests and replay cutoff tests.

Reference: [SPC service](https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer), [SPC layer 1](https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer/1), [NWS API](https://www.weather.gov/documentation/services-web-api), [NWS alerts](https://www.weather.gov/documentation/services-web-alerts).
