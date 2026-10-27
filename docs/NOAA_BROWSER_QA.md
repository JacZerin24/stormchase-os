# Chromium browser QA (experimental and repeatable)

PR #7 adds a GitHub Actions **actual headless Chromium** test of the local Vite application, separate from the upstream-only source checks. It installs Playwright Chromium, starts a local dev server, waits for SPC/NWS feed statuses, performs browser-side cross-origin fetches, runs desktop/mobile viewports, and saves aggregate status plus screenshots for human review. Network/API/sandbox issues fail the job rather than being treated as a clean map.

Limitations: this does not validate the GitHub Pages production domain, geographically inspect polygon alignment, establish accurate product issuance against text graphics, verify alert coverage or replacement/cancellation with an active outbreak, or replace a human mobile check. Compare screenshot artifacts to authoritative SPC maps and manually review layer toggles, basemap attribution, mobile controls, and time rollovers before declaring v0.1 released.

Run on the PR #7 branch by modifying its smoke script, or dispatch the workflow when available on the default branch. This automated job has optional software-download cost and should not run as a recurring production alert service.
