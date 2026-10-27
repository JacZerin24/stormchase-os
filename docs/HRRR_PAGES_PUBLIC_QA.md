# Production QA for recent HRRR model imagery

The read-only GitHub Actions tester downloads the actual publicly deployed GitHub Pages recent HRRR catalog and every preserved model candidate manifest, 2m-temperature PNG, COG and cycle-difference PNG. It checks live HTTP 200 responses, immutable SHA256 checksums, exact model run/valid-time identity and an age gate on the latest published forecast. Browser screenshots and model source checks are separate from this test; **passing does not indicate observed temperature accuracy or officially verified forecast skill**. The test retains exact public URL/time evidence and fails visibly on absent, malformed, overlarge or modified assets. No API tokens, raw GRIB data or local browser fixture substitutes for public-site verification.


## Continuous Phase 1 quality monitor

The read-only public URL and SHA-256 audit now runs after **every completed main-branch regional HRRR publisher workflow** if that publisher succeeds; a failed/cancelled publisher run generates its own failing GitHub Actions check and cannot be mistaken for a fresh model update. An additional independent check runs every three hours to detect old/missing public model assets even if the GitHub publisher cron is delayed or skipped. GitHub's schedules and workflow-run events are best-effort; this is alerting by workflow status only, not a guaranteed notification, service-level agreement, nor a replacement for NOAA/NWS.

The frontend now distinguishes `latest.json` catalog retrieval failures from individual source-qualified candidate manifest failures. When the latest catalog refresh fails, the live model overlay is hidden immediately and an explicit source-health error appears; successful subsequent retrieval clears the error. The last successful **catalog retrieval** is displayed separately from NOAA's model initialization, forecast valid hour, first observed index, and processing time. This prevents a cached PNG from quietly impersonating a recently verified source during a provider or Pages failure.

GitHub Pages uses a fixed model-valid-age threshold and conservative regional field selection. The hourly publisher currently transfers only two 2-m temperature GRIB messages; broader convective fields, scales, multihour animations, and independent skill verification remain Phase 2+.
