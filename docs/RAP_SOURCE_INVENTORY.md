# RAP operational inventory — provider-specific research

RAP is NOT the HRRR dataset; its native grid, product-field inventory, provider HTTP behavior and revision cadence must be checked separately. [NCEP NOMADS public RAP directory](https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/) documents filenames with rap.YYYYMMDD/rap.tHHz.awp130bgrbfNN.grib2.idx. The RAP index is plain-text; the survey checks the exact TMP/2 m above-ground message and bounded byte range in at most three recent index files.

This is one bounded, manually triggered/live feature-branch research probe. It does not retrieve RAP GRIB data, interpolate between HRRR/RAP, estimate first publication, or implement a RAP model layer. If NOMADS rate-limits access, an HTTP failure is shown as an upstream failure and not reported as missing meteorological forecast data. NOMADS may have different provider rate restrictions from NOAA's public HRRR NODD S3 archive.

Next scientific gates: verify current index availability and exact GRIB2 message bytes; check RAP ecCodes native geometry/pressure/surface level and forecast reference time; spatially align to a common grid only with error budget and independent reference checks; compare same-valid-time and same-parameter without claiming numeric agreement or model forecast skill.

RAP discovery is intentionally not scheduled until source terms and actual cadence have been validated and provider load/cost have been reviewed.
## Real-source discovery (Oct 27, 2026)

The first NOAA NOMADS workflow returned HTTP 200 and real RAP .idx data but exposed a concrete format difference: index line 15.1:588937:d=2026102717:UGRD:1 hybrid level:2 hour fcst:. RAP records can have dotted GRIB submessage numbers and repeat byte offsets; the HRRR sequential-index parser therefore cannot be reused without change. The source response was never treated as an available independent forecast field until a RAP-aware parser was implemented.

A provider-specific parser now accepts dotted submessage identifiers, non-decreasing rather than strictly increasing offsets, exact source cycle and forecast-step identity, an exactly matched 2-m TMP field, and an upper byte bound found at the next strictly larger message offset. It marks hasSharedGribMessage if other indexed variables occupy the same byte range. Such a range is a *containing GRIB message*, not proof of a standalone meteorological field; decoding may require extracting a GRIB2 submessage. No RAP GRIB values or geographic field mapping are claimed verified.

Source evidence: https://github.com/JacZerin24/stormchase-os/actions/runs/40568189784. Further tests must validate the latest provider response and whether 2-m TMP is a standalone or submessage field.

## Verified RAP NOMADS metadata result — 2026-10-27 19:25:23 UTC

Following provider-specific support for dotted GRIB submessages, the official live survey succeeded (GitHub Actions run https://github.com/JacZerin24/stormchase-os/actions/runs/40568941440). The source path was RAP 2026-10-27 17Z, forecast hour f02, valid 19Z; the awp130bgrb index had 1,015 records. The precise TMP/2-m AGL record was #928 at byte 37,301,683 through 37,371,405 inclusive (69,723 bytes) with no shared byte offset for this selected field. NOMADS returned HTTP 200 and a Last-Modified header of 17:47:44Z; this is provider object metadata, NOT a verified original publication time.

Seven synthetic RAP inventory tests passed. **No RAP GRIB bytes were requested or decoded, no native grid was inspected, and no RAP map or HRRR/RAP numerical comparison was produced.** Those remain explicit next scientific gates.