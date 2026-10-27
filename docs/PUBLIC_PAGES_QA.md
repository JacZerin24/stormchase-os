# Public production Pages route and archived map QA

This is a one-time public HTTPS *delivery* check for the GitHub Pages site. It fetches the Pages root HTML, follows one or more generated Vite JavaScript assets from the proper `/stormchase-os/` base, and retrieves the archived NOAA HRRR model manifest, both COGs, both PNGs and the same-valid-time difference PNG. Each retrieved asset must match its manifest SHA-256. A passing run proves those immutable bundled assets were served intact at the check time, not that a current forecast is operational or accurate.

A failure is actionable: Pages custom domain/routing, wrong Vite base or incomplete asset deployment. The workflow retains a concise error JSON even if HTTP requests fail. It does not need private tokens, does not poll, and has no scheduled trigger. Source NOAA data are public, forecast times are explicitly historical, and this QA does not test browser rendering, map geometry, current NWS warnings or SPC correctness.

## Verified production result — 2026-10-27, 18:45 UTC

[One-shot public-site QA run 40562849051](https://github.com/JacZerin24/stormchase-os/actions/runs/40562849051) **completed successfully** on GitHub Actions against the actual published URL:

- `https://jaczerin24.github.io/stormchase-os/` returned HTTP **200**, with expected HTML.
- The compiled Vite JavaScript asset under `/stormchase-os/assets/` returned HTTP **200**, preserving the correct repository-relative base.
- `pilot/hrrr-20261027-18z/manifest.json`, both HRRR temperature PNGs, both Cloud Optimized GeoTIFFs, and the equal-valid-time cycle-difference PNG each returned HTTP **200**.
- The five delivered image/GeoTIFF bytes matched the SHA-256 digests in the published manifest. This demonstrates byte-for-byte integrity of the historical pilot assets at that check time.

**Limits:** This is delivery/integrity verification, not an independent forecast skill evaluation or current model feed. Earlier Chromium tests ran against a local Vite server, not an end-user browser at the public Pages domain. Human geometric map inspection and real active-warning case verification remain open.
