# Data Source Catalog — v0.1

## NOAA/NWS Storm Prediction Center — Day 1 categorical outlook

- Source: NOAA/NWS ArcGIS FeatureServer, `outlooks/SPC_wx_outlks/FeatureServer/1`.
- Documentation: https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer/1
- Query: `/query?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=geojson`.
- Geometry: polygons and multipolygons where returned. Renderer uses `dn`: 2=TSTM, 3=MRGL, 4=SLGT, 5=ENH, 6=MDT, 8=HIGH.
- Advertised fields: `issue`, `valid`, `expire`, `idp_source`, `idp_filedate`, `idp_ingestdate`; not all are guaranteed populated.
- Provider/usage: official NOAA service; source data open to use, but production quotas, CORS and reliability must still be browser-tested; no uptime guarantee. Validate categorical nested polygons and geometry alignment.
- Future: separate layers are required for 2026 conditional intensity groups (CIG1–3) and probabilities. Do not treat old hatched-significant polygons as equivalent.

## NWS Active Alerts API

- Source: https://api.weather.gov/alerts/active
- Documentation: https://www.weather.gov/documentation/services-web-api and https://www.weather.gov/documentation/services-web-alerts
- Initial selection: `event=Tornado Warning,Severe Thunderstorm Warning`; GeoJSON via `Accept: application/geo+json`; display only polygons with geometry.
- HTTP: modest request rates. NWS recommends polling **no more often than every 30 s**; v0.1 refresh interval 5 min. API may rate-limit. The NWS recommends an identifiable User-Agent, which browser fetch disallows customizing; migrate to backend proxy if operational use requires compliance/identification.
- Important: zone/county-oriented alert features can have `geometry: null`. Map polygon coverage is *not* a complete alert inventory. This is not an alert-delivery guarantee.
- An active alert listing and its current geometry cannot stand in for current NWS warning products accessed directly.

## Basemap

- CARTO dark-matter GL hosted style: https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json .
- Third-party background cartography, **not** meteorological information. Hosted CDN bandwidth, attribution, license and permitted sustained use must be checked before large-scale public traffic. No guaranteed offline support or uptime.
- MapLibre GL JS renderer: https://maplibre.org/maplibre-gl-js/docs/ .

## Metadata and failure semantics

- Source issue/valid/expire values always take precedence over local client clock.
- `last successful retrieval` records browser fetch, not product issuance.
- A network/CORS or parsing failure retains last success only with explicit failure/stale warning; do not disguise an error as a current map layer.
- Zero features can be genuine; malformed data must be an error, not rendered as zero risk.
- Geographic coverage is CONUS-focused; service footprints and null geometry can differ from full hazard impact area.

## Deferred candidates (research required)

RAP/HRRR/NBM/GEFS/SREF/RRFS/REFS, MRMS/radar, GOES imagery, METAR/MADIS/mesonet, NOMADS/AWS NOAA data, ERA5, Storm Events, OSM road graphs, elevation/land cover. For each: document endpoint, acquisition strategy, license, redistribution, rate/size, age, CRS, units and QA before integration.
