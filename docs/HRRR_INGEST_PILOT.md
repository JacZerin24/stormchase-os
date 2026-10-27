# HRRR GRIB2 acquisition pilot

**Experimental transport, not verified live model ingestion, decoded meteorological data, or a working map.**

This narrow Python standard-library pilot targets NOAA NODD's public AWS HRRR CONUS surface GRIB2 bucket and index. It retrieves one exact indexed message via HTTP byte range, validates its reference time and byte span, requires HTTP 206 and GRIB framing, and writes an immutable file plus JSON manifest. No scheduled ingestion and no bulk downloader.

## Commands

Run deterministic offline unit tests from the repository root:

    python -m unittest discover -s pipelines/tests -v

Query a real inventory without downloading GRIB data (this requires internet connectivity):

    python -m pipelines.hrrr_subset --run 2026-10-27T12:00:00Z --lead 6 --variable TMP --level "2 m above ground" --out /tmp/hrrr_f06_tmp.grib2 --dry-run

Remove --dry-run to perform the bounded message acquisition. The example's availability is not guaranteed; choose an actually published run.

## Scientific limitations

- This is a full-grid GRIB message subset by byte range, NOT a regional geospatial crop.
- Fields allowed: TMP/DPT at 2 m and UGRD/VGRD at 10 m, matched by exact index strings.
- GRIB metadata/units, geographical CRS, grid geometry, missing-value mask, scientific values and actual source publication time are deliberately unknown. The manifest records nulls, never invented values.
- The requested cycle and lead determine the valid time, but first operational publication availability is NOT established by this process. No hindsight-safe historical replay is claimed.
- Need ecCodes/wgrib2 decoding, real-source validation, QA versus independent reference data, reprojection/tiling, per-field latency measurements, retention limits and hosting-cost benchmarks before any meteorological map.
- This proof of concept intentionally makes no assertion that RRFS/REFS have begun operations. Per the NWS October 15 update to SCN26-48, operational implementation was scheduled for November 3, 2026.

Sources: https://registry.opendata.aws/noaa-hrrr-pds/ ; https://www.weather.gov/notification ; https://nomads.ncep.noaa.gov/info.php?page=gribfilter ; https://herbie.readthedocs.io/en/stable/user_guide/background/grib2.html .
