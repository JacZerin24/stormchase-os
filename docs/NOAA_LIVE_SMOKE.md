# One-shot NOAA upstream test: interpretation and release requirements

The script `tools/noaa_source_smoke.py` runs bounded requests against authoritative SPC ArcGIS GeoJSON and NWS single-event active-alert feeds and saves **aggregated metadata**, not personal or event-level warning content.

The workflow runs on changes to the test branch (and on manual dispatch once present on the default branch). It deliberately *fails* if transport, schema, event-filter or count response tests fail, even if upstream service is inaccessible. A passing test establishes only that those upstream HTTPS queries succeeded **from the GitHub runner at the reported timestamp**. It does **not** establish browser JavaScript access, MapLibre geometry alignment, actual latest issuance relative to the authoritative web products, polygon completeness, API User-Agent compliance for browsers, or alert-delivery reliability.

Run locally (with outbound HTTPS) using `python -m tools.noaa_source_smoke --out reports/noaa-source-smoke.json`. Offline report-unit tests: `python -m unittest discover -s tools/tests -v`.

Checks: SPC service layer IDs 1/9/17, count endpoint, sampled first ten categorical features, source timestamps and category codes; NWS individual TOR/SVR event filters, feature geometry counts and response headers; HTTP Origin response header is informational and **not actual browser CORS validation**. Real-browser and mobile checks in Issue #12 remain required.

Do not store full raw active alert response or publish a current alert map from this report. NOAA warning/product timing can change between requests. Official NWS warning source remains authoritative for safety.
