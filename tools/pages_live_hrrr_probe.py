"""Public HTTPS acceptance: published real HRRR images and scientific metadata.

Read-only test. Separately verifies GitHub Pages delivery from the server;
it does not establish model skill, observed weather or warning completeness.
"""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
import argparse
import json
import re
import time

ORIGIN="https://jaczerin24.github.io/stormchase-os/"
PREFIX="live/hrrr/"
MAX_BYTES=2_000_000
UA="StormChaseOS/0.2 public model delivery QA (github.com/JacZerin24/stormchase-os)"


def read(path:str)->tuple[bytes,dict]:
    if not re.fullmatch(r"[a-zA-Z0-9_./-]+",path) or ".." in path:
        raise ValueError("Untrusted relative public asset path")
    url=urljoin(ORIGIN,PREFIX+path)
    if not url.startswith(ORIGIN+PREFIX):
        raise ValueError("Source URL escapes audited model path")
    with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"application/json,image/png,image/tiff"}),timeout=20) as response:
        buf=response.read(MAX_BYTES+1)
        metadata={"url":response.geturl(),"status":response.status,
                  "bytes":len(buf),"contentType":response.headers.get("Content-Type")}
    if metadata["status"]!=200 or len(buf)>MAX_BYTES:
        raise ValueError("Model asset unavailable or over byte cap")
    return buf,metadata


def check()->dict:
    latest_raw,latest_response=read("latest.json")
    latest=json.loads(latest_raw)
    if latest.get("schema")!="stormchase-hrrr-pages-catalog/1" or latest.get("forecastSkillVerified") is not False:
        raise ValueError("Public model catalog incorrectly promises validated skill")
    records=latest.get("snapshots",[])
    if not isinstance(records,list) or not 1<=len(records)<=6:
        raise ValueError("Public catalog has no verified model snapshots")
    actual=datetime.now(timezone.utc)
    files=[latest_response]
    for rec in records:
        ident=rec["id"]
        if not re.fullmatch(r"\d{8}T\d\dZ",ident):
            raise ValueError("Malformed snapshot id")
        if rec["manifest"]!=f"runs/{ident}/candidate.json":
            raise ValueError("Manifest URL mismatch")
        body,info=read(rec["manifest"])
        files.append(info)
        candidate=json.loads(body)
        if candidate.get("schema")!="stormchase-hrrr-live-candidate/1" or \
           candidate.get("status")!="geographic_QA_passed_forecast_skill_not_verified" or \
           candidate.get("calibratedSevereWeatherProbability") is not False or \
           candidate.get("validAt")!=rec["validAt"] or \
           candidate.get("latestRunAt")!=rec["runAt"]:
            raise ValueError("Published source provenance inconsistent")
        for entry in candidate["images"]:
            if entry["file"] not in ("older.png","newer.png") or \
               entry["cog"] not in ("older.tif","newer.tif"):
                raise ValueError("Unexpected product path")
            for name,hashname in ((entry["file"],"sha256"),(entry["cog"],"cogSha256")):
                raw,resp=read("runs/"+ident+"/"+name)
                if sha256(raw).hexdigest()!=entry[hashname]:
                    raise ValueError("Production image/COG SHA mismatch")
                files.append(resp)
        diff=candidate["difference"]
        if diff["file"]!="difference.png":
            raise ValueError("Unreviewed difference field")
        raw,resp=read("runs/"+ident+"/difference.png")
        if sha256(raw).hexdigest()!=diff["sha256"]:
            raise ValueError("Forecast difference content changed")
        files.append(resp)
    valid=datetime.fromisoformat(records[0]["validAt"].replace("Z","+00:00"))
    lag=(actual-valid).total_seconds()/3600
    if lag>3 or lag< -1:
        raise ValueError("Newest public forecast is stale or excessively future dated")
    return {
        "result":"public_HTTP200_and_content_hash_verified",
        "checkedAt":actual.isoformat(timespec="seconds").replace("+00:00","Z"),
        "scope":"published model integrity and times; not independent forecast verification",
        "latestValidAt":records[0]["validAt"],"latestRunAt":records[0]["runAt"],
        "validHourAge":round(lag,3),"snapshotCount":len(records),
        "files":files,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    # Pages CDN propagation can take time; transient 404 is not silently
    # converted into success. Retry a bounded window then fail with evidence.
    result=None
    last_error=""
    for attempt in range(4):
        try:
            result=check()
            break
        except Exception as exc:
            last_error=f"{type(exc).__name__}: {str(exc)[:180]}"
            if attempt<3:time.sleep(10)
    if result is None:
        result={"result":"failed","checkedAt":datetime.now(timezone.utc).isoformat(),
                "error":last_error,"origin":ORIGIN}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0 if result["result"]=="public_HTTP200_and_content_hash_verified" else 1

if __name__=="__main__":
    raise SystemExit(main())
