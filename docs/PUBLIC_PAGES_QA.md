# Public production Pages route and archived map QA

This is a one-time public HTTPS *delivery* check for the GitHub Pages site. It fetches the Pages root HTML, follows one or more generated Vite JavaScript assets from the proper `/stormchase-os/` base, and retrieves the archived NOAA HRRR model manifest, both COGs, both PNGs and the same-valid-time difference PNG. Each retrieved asset must match its manifest SHA-256. A passing run proves those immutable bundled assets were served intact at the check time, not that a current forecast is operational or accurate.

A failure is actionable: Pages custom domain/routing, wrong Vite base or incomplete asset deployment. The workflow retains a concise error JSON even if HTTP requests fail. It does not need private tokens, does not poll, and has no scheduled trigger. Source NOAA data are public, forecast times are explicitly historical, and this QA does not test browser rendering, map geometry, current NWS warnings or SPC correctness.
