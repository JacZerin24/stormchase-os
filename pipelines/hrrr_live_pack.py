"""Turn scientifically checked recent HRRR staging into a bounded public CANDIDATE.

A candidate is NOT automatically published, an operational forecast, or
a verified severe-weather prediction. It carries immutable source and content
hashes and retains exact model initialization and forecast valid times.
"""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
from pipelines.hrrr_stage import stage

SCHEMA="stormchase-hrrr-live-candidate/1"
MAX_FILES_BYTES=850_000

def digest(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()

def validate_stage(stage_dir:Path,now:datetime)->dict:
    data=json.loads((stage_dir/"manifest.json").read_text())
    if data.get("schema")!="stormchase-hrrr-staged-pair/1" or data.get("status")!="staged_experimental_not_published":
        raise ValueError("Model source stage lacks validated scientific contract")
    if data.get("operational") is not False or data.get("automaticallyPublished") is not False:
        raise ValueError("Scientific stage promoted beyond evidence")
    if data.get("crs")!="EPSG:4326" or data.get("bounds")!=[-103.0,33.0,-94.0,39.4]:
        raise ValueError("Unreviewed region or georeference")
    if (data.get("width"),data.get("height"))!=(225,160):
        raise ValueError("Unexpected grid resolution")
    when=datetime.fromisoformat(data["validAt"].replace("Z","+00:00"))
    if when.tzinfo is None or (now-when).total_seconds()>2*3600 or (when-now).total_seconds()>3600:
        raise ValueError("Source valid time stale or too far in future")
    products=data["products"]
    if len(products)!=2 or [p["leadHours"] for p in products]!=[3,2] or products[0]["runAt"]>=products[1]["runAt"]:
        raise ValueError("Forecast cycles not paired")
    images=[]
    for n,p in enumerate(products):
        run=datetime.fromisoformat(p["runAt"].replace("Z","+00:00"))
        if run.tzinfo is None or run.timestamp()+p["leadHours"]*3600!=when.timestamp() or p["validAt"]!=data["validAt"]:
            raise ValueError("Run and valid time mismatch")
        if p.get("units")!="K" or p.get("parameter")!="TMP" or p.get("level")!="2 m above ground":
            raise ValueError("Unreviewed model parameter")
        geo=p.get("geolocationQA",{})
        check=geo.get("eccodesOutputPixelChecks",{})
        if geo.get("coverage_fraction",0)<.97 or geo.get("unmatched_cells",-1)!=0 or geo.get("max_nearest_km",100)>5.01:
            raise ValueError("Insufficient georeferencing")
        if check.get("checked_output_pixel_centers",0)<16 or check.get("max_abs_temperature_residual_K",100)>1e-3:
            raise ValueError("ecCodes reference point check failed")
        if len(p.get("sourceGribSha256",""))!=64:
            raise ValueError("No authentic source checksum")
        for filename,expected in ((p["image"],p["imageSha256"]),(p["cog"],p["cogSha256"])):
            if filename not in ("older.png","newer.png","older.tif","newer.tif") or digest(stage_dir/filename)!=expected:
                raise ValueError("Invalid packaged model checksum")
        images.append({
            "key":"older" if n==0 else "newer",
            "file":p["image"],"sha256":p["imageSha256"],
            "cog":p["cog"],"cogSha256":p["cogSha256"],
            "runAt":p["runAt"],"leadHours":p["leadHours"],
            "validAt":p["validAt"],"units":"K",
            "sourceSha256":p["sourceGribSha256"],
            "geoCoverage":geo["coverage_fraction"],
            "nativeDistanceKm":geo["max_nearest_km"],
        })
    difference=data["difference"]
    if difference.get("image")!="difference.png" or digest(stage_dir/"difference.png")!=difference.get("sha256"):
        raise ValueError("Difference image checksum invalid")
    sizes=sum(p.stat().st_size for p in stage_dir.iterdir() if p.is_file())
    if sizes>MAX_FILES_BYTES:raise ValueError("Published regional asset budget exceeded")
    return {
       "schema":SCHEMA,"model":"HRRR",
       "status":"geographic_QA_passed_forecast_skill_not_verified",
       "forecastType":"model_prediction_not_observation",
       "field":"2m_temperature","fieldName":"2 m temperature",
       "validAt":data["validAt"],"latestRunAt":images[1]["runAt"],
       "sourceIndexObservedAt":data["inventoryCheckedAt"],
       "generatedAt":data["processedAt"],"firstPublicationAt":None,
       "bounds":data["bounds"],"crs":data["crs"],
       "images":images,
       "difference":{"file":"difference.png","sha256":difference["sha256"],
                     "units":"degree Fahrenheit difference of forecasts at same valid time"},
       "scientificLimitations":[
         "Source indices and GRIB geolocation checked, not independently forecast-skill verified",
         "GitHub Actions timing is best-effort and not an operational warning service",
         "Images interpolate no missing native coordinates and are not live observations"],
       "calibratedSevereWeatherProbability":False,
    }

def produce(out:Path,now:datetime|None=None,stage_fn=stage)->dict:
    if out.exists():raise FileExistsError("Never overwrite a source candidate")
    now=now or datetime.now(timezone.utc)
    stage_fn(out,now=now)
    try:
        manifest=validate_stage(out,now)
        (out/"candidate.json").write_text(json.dumps(manifest,indent=2)+"\n")
        return manifest
    except Exception:
        # Invalid intermediate files cannot survive as a publishable candidate.
        import shutil
        shutil.rmtree(out)
        raise

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    m=produce(args.out)
    print(json.dumps({k:m[k] for k in ("status","field","validAt","latestRunAt","generatedAt")},indent=2))
if __name__=="__main__":main()
