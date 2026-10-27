"""Bounded HRRR Pages cache backed by short-lived GitHub Actions artifacts.

Stores only recent, verified GRIB-derived images; NO git data commits and no
long-running object-storage bills. Each successful publisher workflow reuses
the previous Actions artifact cache and redeploys at most six valid hours.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
from hashlib import sha256
import argparse
import json
import re
import shutil
from pipelines.hrrr_live_pack import validate_stage

SCHEMA="stormchase-hrrr-pages-catalog/1"
MAX_SNAPSHOTS=6
MAX_CACHE_BYTES=4_000_000

def when(text:str)->datetime:
    if not isinstance(text,str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ",text):
        raise ValueError("UTC timestamp expected")
    dt=datetime.fromisoformat(text.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset()!=timedelta():raise ValueError("Must be UTC")
    return dt

def hashfile(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()

def checked_candidate(source:Path,now:datetime)->dict:
    validated=validate_stage(source,now)
    original=json.loads((source/"candidate.json").read_text())
    if original!=validated:
        raise ValueError("Prepared candidate diverges from verified model products")
    return validated

def catalog(cache:Path)->dict:
    src=cache/"latest.json"
    if not src.exists():
        return {"schema":SCHEMA,"updatedAt":None,"snapshots":[],"forecastSkillVerified":False}
    value=json.loads(src.read_text())
    if value.get("schema")!=SCHEMA or value.get("forecastSkillVerified") is not False:
        raise ValueError("Unrecognized or falsely calibrated model cache")
    if not isinstance(value.get("snapshots"),list) or len(value["snapshots"])>MAX_SNAPSHOTS:
        raise ValueError("Bad cache catalog length")
    return value

def update(cache:Path,source:Path,now:datetime)->dict:
    if now.tzinfo is None or now.utcoffset()!=timedelta():
        raise ValueError("UTC check timestamp required")
    q=checked_candidate(source,now)
    existing=catalog(cache)
    valid=when(q["validAt"])
    identity=valid.strftime("%Y%m%dT%HZ")
    if existing["snapshots"]:
        newest=when(existing["snapshots"][0]["validAt"])
        if valid<newest:
            raise ValueError("Older model valid time cannot replace recent forecast")
    target=cache/"runs"/identity
    if target.exists():
        # Idempotence: never rewrite an immutable forecast snapshot; even if
        # a provider later revises files, do not silently mutate a past result.
        old=json.loads((target/"candidate.json").read_text())
        if old["validAt"]!=q["validAt"] or old["images"]!=q["images"]:
            raise ValueError("Immutable model forecast collision/revision")
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(source,target)
    for p in q["images"]:
        if hashfile(target/p["file"])!=p["sha256"] or hashfile(target/p["cog"])!=p["cogSha256"]:
            raise ValueError("Published forecast asset hash mismatch")
    if hashfile(target/q["difference"]["file"])!=q["difference"]["sha256"]:
        raise ValueError("Forecast difference asset digest mismatch")
    entries={
        s["id"]:s for s in existing["snapshots"]
        if (cache/"runs"/s["id"]/"candidate.json").is_file()
    }
    entries[identity]={
        "id":identity,"validAt":q["validAt"],
        "runAt":q["latestRunAt"],"sourceObservedAt":q["sourceIndexObservedAt"],
        "manifest":"runs/"+identity+"/candidate.json"}
    kept=sorted(entries.values(),key=lambda v:v["validAt"],reverse=True)[:MAX_SNAPSHOTS]
    retain={x["id"] for x in kept}
    for sub in (cache/"runs").iterdir():
        if sub.is_dir() and sub.name not in retain:
            shutil.rmtree(sub)
    result={"schema":SCHEMA,"updatedAt":now.isoformat(timespec="seconds").replace("+00:00","Z"),
            "snapshots":kept,"forecastSkillVerified":False,
            "availabilityGuarantee":False,
            "scope":"regional HRRR model imagery; no severe-weather probability",
            "cachePolicy":"six recent valid-hour snapshots, GitHub Actions artifact retention <=7d"}
    # Catalog pointer becomes visible only after all files/size checks.
    total=sum(f.stat().st_size for f in cache.rglob("*") if f.is_file())
    if total>MAX_CACHE_BYTES:raise ValueError("Asset cache size budget exceeded")
    (cache/"latest.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

def verify(cache:Path)->dict:
    result=catalog(cache)
    for entry in result["snapshots"]:
        if not re.fullmatch(r"\d{8}T\d\dZ",entry["id"]):
            raise ValueError("Invalid immutable model snapshot identifier")
        if entry["manifest"]!="runs/"+entry["id"]+"/candidate.json":
            raise ValueError("Unsafe model manifest path")
        root=cache/"runs"/entry["id"]
        m=json.loads((root/"candidate.json").read_text())
        if m.get("validAt")!=entry["validAt"] or m.get("latestRunAt")!=entry["runAt"]:
            raise ValueError("Catalog snapshot run/valid mismatch")
        if m.get("schema")!="stormchase-hrrr-live-candidate/1" or m.get("calibratedSevereWeatherProbability") is not False:
            raise ValueError("Invalid scientific data type")
        for x in m["images"]:
            if x["file"] not in ("older.png","newer.png"):
                raise ValueError("Unexpected image filename")
            if hashfile(root/x["file"])!=x["sha256"]:
                raise ValueError("Stored HRRR PNG changed")
        if hashfile(root/"difference.png")!=m["difference"]["sha256"]:
            raise ValueError("Stored HRRR cycle-difference changed")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--cache",type=Path,required=True)
    a=ap.parse_args()
    a.cache.mkdir(parents=True,exist_ok=True)
    result=update(a.cache,a.candidate,datetime.now(timezone.utc))
    verify(a.cache)
    print(json.dumps({"latest":result["snapshots"][0],"retained":len(result["snapshots"])},indent=2))
if __name__=="__main__":main()
