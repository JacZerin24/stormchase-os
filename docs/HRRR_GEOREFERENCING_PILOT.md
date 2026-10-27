# HRRR real-geography / equal-valid-time pilot (archived test case)

**Stage:** Experimental real HRRR 2-m temperature mapping and cycle comparison, not operational model display. The entire workflow uses official NODD HRRR GRIB2 source files; both inputs must be independently downloaded by the bounded `pipelines.hrrr_subset` downloader, validated by ecCodes, and must refer to different runs with the same valid time.

Target domain: `[-103°,33°,-94°,39.4°]`, roughly the southern/central Plains, NOT a chase-target recommendation. Output: EPSG:4326 north-up, nearest-neighbor sampled 0.04° grid, and a small Cloud Optimized GeoTIFF (COG) plus geographically registered RGBA PNG for MapLibre ImageSource. Color bins in degrees Fahrenheit are fixed across runs. Pixels more than 5 km from a native valid GRIB gridpoint become transparent; the pipeline refuses geographic coverage below 97%. Uses ecCodes original latitude/longitude/value arrays and an independent internal ecCodes nearest-point spot check. No invented forecast values or spatial filling. The difference image uses **15Z f03 minus 12Z f06**, aligned at 18Z October 27, 2026; pixelwise difference is derived only from valid pairs.

This proves the **technical georeferencing mechanism** but is NOT independent map accuracy validation. A geodesic nearest-neighbor regrid from original native Lambert grid to geographic pixel coordinates does not add numerical resolution. Pixel size is nominal, variable geodesic area because EPSG:4326. Before operational use compare independent HRRR authoritative reference fields at fixed coordinates, validate bitmap/missing flags, analyze regridding choice, edge impacts, dynamic run/valid publication availability and spatial error distribution. Processing metadata and GRIB source SHA hashes are preserved and no raw national GRIB files are committed.

The one-shot GitHub Action on the feature branch is deliberately bounded to two old forecast messages, ≤64MB each, and commits only derived maps/manifests to a reviewable branch. It is not a live or scheduled fetch. Frontend must visibly label results **ARCHIVED TEST CASE · NOT CURRENT** and never confuse them with a current forecast or alert service.

Data use references: ECMWF ecCodes geographic-coordinate access; GDAL Cloud Optimized GeoTIFF driver; NOAA HRRR NODD public archive. Provider timestamps are not true first publication timestamps and do not support hindsight-safe replay.


## Verified real-source and browser milestones — 2026-10-27

- [Real two-run geospatial QA job](https://github.com/JacZerin24/stormchase-os/actions/runs/40562092750): completed with authentic NOAA HRRR GRIB2 fields from 2026-10-27 12Z f06 and 15Z f03, both valid 18Z. Native data remain unaltered; source and derived asset SHA256s recorded in the committed JSON manifest.
- **Regional grid:** EPSG:4326, north-up, 225 columns × 160 rows, bounds 103°W–94°W and 33°N–39.4°N. Both runs achieved 100% matching coverage under a 5 km distance cap, no unmatched output pixels, maximum spherical closest-point distance 2.10646 km and 95th percentile 1.79613 km.
- **Independent geolocation algorithm check, same data:** a separate ecCodes nearest lookup at 16 output pixel centers per run agreed with the array/KD-tree regrid to **0 K** residual at those points; maximum ecCodes geodetic distance was 1.96382 km. This validates representative source-coordinate assignment but is **NOT independent atmospheric forecast verification** and does not cover every pixel.
- Derived 12Z f06 temperatures ranged 281.066–300.628 K in the pilot region; derived 15Z f03 temperatures ranged 281.487–300.299 K. Their 15Z-minus-12Z difference ranged −2.891 to +3.609 K (identical numerical increments to Celsius; multiply 1.8 for degrees Fahrenheit differences).
- [Chromium desktop/mobile browser QA](https://github.com/JacZerin24/stormchase-os/actions/runs/40561656374) passed for all three map images, archived-valid-time labeling, panel interaction and basemap theme switch, using a local Vite server.
- Product manifest and packaged image/COG hashes are checked as part of web CI, so missing or mutated forecast assets block the build.

**Not yet verified:** independent NOAA gridded reference comparison, native-grid mask flags, entire-map pixel-by-pixel spot check, exact production-domain asset retrieval, meteorological skill or current-cycle latency. Do not advertise the archived images as the latest HRRR forecasts.
