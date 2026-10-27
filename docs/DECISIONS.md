# Architecture Decision Log

## ADR-001 — Static map-first client first (2026-10-27)

Decision: React, TypeScript, Vite, MapLibre GL JS; GitHub Pages for initial hosting. Reason: low cost and early browser-usable functionality. Consequence: live feeds depend on browser network access, upstream CORS and provider responsiveness. No reliable push alerts and no scheduled background ingestion.

## ADR-002 — Official geometry sources and explicit provenance

Decision: NOAA SPC official FeatureServer Day 1 categorical polygons plus NWS active alert GeoJSON. Each is isolated in an adapter, with separate errors and retrieval/product timestamps. Show missing geometry limitation. Do not invent data.

## ADR-003 — No premature forecasting scores or routing

Decision: no chase target probability or route guarantees in v0.1. Scientific baselines and independent holdouts are release gates for later targeting functionality.

## ADR-004 — Third-party dark basemap as provisional dependency

Decision: provisionally use CARTO hosted dark-matter style to ship a polished, dark visual foundation with attribution. Before sustained public traffic, confirm contractual suitability, traffic limits and fallback strategy. A basemap failure must not be mistaken for lack of hazards.

## ADR-005 — Source-of-truth and PR process

Decision: GitHub `main` reflects reviewed code; feature work on branches/PRs; CI/build/deploy results are separately verified. Branch protection and Pages publishing selection require owner action if connector cannot administer settings.
