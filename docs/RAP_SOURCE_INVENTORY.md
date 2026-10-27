# RAP operational inventory — provider-specific research

RAP is NOT the HRRR dataset; its native grid, product-field inventory, provider HTTP behavior and revision cadence must be checked separately. [NCEP NOMADS public RAP directory](https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/) documents filenames with rap.YYYYMMDD/rap.tHHz.awp130bgrbfNN.grib2.idx. The RAP index is plain-text; the survey checks the exact TMP/2 m above-ground message and bounded byte range in at most three recent index files.

This is one bounded, manually triggered/live feature-branch research probe. It does not retrieve RAP GRIB data, interpolate between HRRR/RAP, estimate first publication, or implement a RAP model layer. If NOMADS rate-limits access, an HTTP failure is shown as an upstream failure and not reported as missing meteorological forecast data. NOMADS may have different provider rate restrictions from NOAA's public HRRR NODD S3 archive.

Next scientific gates: verify current index availability and exact GRIB2 message bytes; check RAP ecCodes native geometry/pressure/surface level and forecast reference time; spatially align to a common grid only with error budget and independent reference checks; compare same-valid-time and same-parameter without claiming numeric agreement or model forecast skill.

RAP discovery is intentionally not scheduled until source terms and actual cadence have been validated and provider load/cost have been reviewed.