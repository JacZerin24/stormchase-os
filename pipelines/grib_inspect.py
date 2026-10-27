"""Decode one downloaded GRIB2 message using ecCodes and report metadata/QC.

An initial physical-bound check is not independent forecast verification. This
does not create maps, calculate diagnostics, or validate source publication time.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import eccodes as ec


def inspect(path: Path, expected_run: datetime, expected_lead: int) -> dict:
    data = path.read_bytes()
    if not data.startswith(b"GRIB") or not data.endswith(b"7777"):
        raise ValueError("Invalid GRIB framing")
    with path.open("rb") as stream:
        gid = ec.codes_grib_new_from_file(stream)
        if gid is None:
            raise ValueError("ecCodes failed to decode the GRIB message")
        try:
            keys = {
                "edition": int(ec.codes_get(gid,"edition")),
                "centre": str(ec.codes_get(gid,"centre")),
                "paramId": int(ec.codes_get(gid,"paramId")),
                "shortName": str(ec.codes_get(gid,"shortName")),
                "name": str(ec.codes_get(gid,"name")),
                "units": str(ec.codes_get(gid,"units")),
                "typeOfLevel": str(ec.codes_get(gid,"typeOfLevel")),
                "level": int(ec.codes_get(gid,"level")),
                "gridType": str(ec.codes_get(gid,"gridType")),
                "numberOfPoints": int(ec.codes_get(gid,"numberOfPoints")),
                "dataDate": int(ec.codes_get(gid,"dataDate")),
                "dataTime": int(ec.codes_get(gid,"dataTime")),
                "validityDate": int(ec.codes_get(gid,"validityDate")),
                "validityTime": int(ec.codes_get(gid,"validityTime")),
                "stepType": str(ec.codes_get(gid,"stepType")),
                "stepRange": str(ec.codes_get(gid,"stepRange")),
            }
            values = np.asarray(ec.codes_get_values(gid), dtype=np.float64)
        finally:
            ec.codes_release(gid)
    if keys["edition"] != 2:
        raise ValueError("Expected GRIB2")
    if keys["typeOfLevel"] != "heightAboveGround" or keys["level"] != 2:
        raise ValueError("Wrong vertical level for TMP2m")
    if keys["units"] != "K":
        raise ValueError("Temperature units mismatch")
    if keys["dataDate"] != int(expected_run.strftime("%Y%m%d")) or keys["dataTime"] != int(expected_run.strftime("%H%M")):
        raise ValueError("GRIB initialization does not match requested run")
    valid = expected_run + timedelta(hours=expected_lead)
    if keys["validityDate"] != int(valid.strftime("%Y%m%d")) or keys["validityTime"] != int(valid.strftime("%H%M")):
        raise ValueError("GRIB valid time does not match run + lead")
    if len(values) != keys["numberOfPoints"]:
        raise ValueError("GRIB grid count does not match decoded values")
    finite = np.isfinite(values) & (np.abs(values) < 1e20)
    if not finite.any():
        raise ValueError("No finite gridded values")
    known=values[finite]
    minimum=float(known.min())
    maximum=float(known.max())
    if minimum < 150 or maximum > 350:
        raise ValueError("2m temperature fails broad physical sanity bounds (not forecast verification)")
    return {
        "status":"decoded_ecCodes_metadata_and_sanity_passed",
        "scientific_validation":"not_independently_verified",
        "sha256":hashlib.sha256(data).hexdigest(),
        "bytes":len(data),
        "run_at":expected_run.isoformat().replace("+00:00","Z"),
        "valid_at":valid.isoformat().replace("+00:00","Z"),
        "lead_hours":expected_lead,
        "grib_metadata":keys,
        "min_K":minimum,"max_K":maximum,
        "finite_cells":int(finite.sum()),"total_cells":int(len(values)),
        "unknown_or_missing_cells":int((~finite).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path",type=Path,required=True)
    parser.add_argument("--run",required=True)
    parser.add_argument("--lead",type=int,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    from pipelines.hrrr_subset import utc_cycle
    meta=inspect(args.path,utc_cycle(args.run),args.lead)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))


if __name__=="__main__":
    main()
