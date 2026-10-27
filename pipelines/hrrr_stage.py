"""Generate a bounded, real recent HRRR pair as an Actions STAGING artifact.

Never automatically writes to GitHub Pages. Not an independent forecast
verification, nowcast, warning feed or operational publication workflow.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from pipelines.hrrr_inventory import discover,iso,validation_time
from pipelines.hrrr_subset import acquire,utc_cycle

MAX_STAGED_BYTES=1_000_000
MAX_SOURCE_BYTES=64*1024*1024
SCHEMA="stormchase-hrrr-staged-pair/1"


def check_pair(report:dict,now:datetime)->tuple[str,list[dict]]:
    now=validation_time(now)
    if report.get("schema")!="stormchase-hrrr-inventory/1" or report.get("status")!="pair_inventory_observed":
        raise ValueError("No verified recent HRRR inventory pair")
    selection=report.get("selected")
    if not isinstance(selection,dict) or not isinstance(selection.get("runs"),list) or len(selection["runs"])!=2:
        raise ValueError("Missing two explicit model cycles")
    valid=utc_cycle(selection["validAt"])
    lag=(now-valid).total_seconds()/3600
    if lag>2.0 or lag< -1.0:
        raise ValueError("Model forecast valid time exceeds experimental freshness window")
    checked=datetime.fromisoformat(report["checkedAt"].replace("Z","+00:00"))
    if checked.tzinfo is None or checked.utcoffset()!=timedelta() or (now-checked).total_seconds()>600 or checked>now+timedelta(seconds=5):
        raise ValueError("Inventory observation timestamp invalid/stale")
    runs=selection["runs"]
    if [r.get("leadHours") for r in runs]!=[3,2]:
        raise ValueError("Expected older f03 and newer f02")
    for r in runs:
        if r.get("state")!="inventory_observed" or r.get("field")!="TMP:2 m above ground":
            raise ValueError("Wrong inventory state or field")
        cycle=utc_cycle(r["runAt"])
        if cycle+timedelta(hours=r["leadHours"])!=valid or r.get("validAt")!=iso(valid):
            raise ValueError("Run/lead/valid mismatch")
        n=r.get("estimatedMessageBytes")
        if type(n) is not int or not 0<n<=MAX_SOURCE_BYTES:
            raise ValueError("Unbounded source transfer estimate")
    if runs[0]["runAt"]>=runs[1]["runAt"]:
        raise ValueError("Model cycles not in increasing order")
    return iso(valid),runs


def filehash(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(inputs:list[tuple[Path,dict]],output:Path)->dict:
    # Imported only after inventory validation; metadata poll stays stdlib-only.
    import numpy as np
    from PIL import Image
    from pipelines.hrrr_georeg import (
        BOUNDS,STEP_DEG,load_field,nearest_regrid,spotcheck_output_against_eccodes,
        write_cog,png_rgba
    )
    output.mkdir()
    arrays=[]
    products=[]
    for idx,(path,source) in enumerate(inputs):
        init=utc_cycle(source["runAt"])
        lead=source["leadHours"]
        lat,lon,values,grib=load_field(path,init,lead)
        area,qa=nearest_regrid(lat,lon,values)
        qa["eccodesOutputPixelChecks"]=spotcheck_output_against_eccodes(path,area)
        prefix="older" if idx==0 else "newer"
        tif=prefix+".tif"
        png=prefix+".png"
        tifsha=write_cog(output/tif,area)
        Image.fromarray(png_rgba(area,"temperature"),"RGBA").save(output/png,optimize=True)
        products.append({
            "model":"HRRR","runAt":source["runAt"],"leadHours":lead,
            "validAt":grib["valid_at"],"parameter":"TMP","level":"2 m above ground",
            "units":"K","sourceGribSha256":grib["sha256"],"sourceGribBytes":grib["bytes"],
            "sourceIndex":source["source_index"],
            "sourceIndexLastModified":source.get("sourceLastModified"),
            "actualSourceReleaseAt":None,
            "image":png,"imageSha256":filehash(output/png),
            "cog":tif,"cogSha256":tifsha,
            "geolocationQA":qa,"minK":float(np.nanmin(area)),"maxK":float(np.nanmax(area))
        })
        arrays.append(area)
    delta=arrays[1]-arrays[0]
    Image.fromarray(png_rgba(delta,"trend"),"RGBA").save(output/"difference.png",optimize=True)
    return {
        "bounds":list(BOUNDS),"crs":"EPSG:4326",
        "width":int(arrays[0].shape[1]),"height":int(arrays[0].shape[0]),
        "pixelStepDegrees":STEP_DEG,
        "products":products,
        "difference":{"image":"difference.png","sha256":filehash(output/"difference.png"),
                      "minK":float(np.nanmin(delta)),"maxK":float(np.nanmax(delta)),
                      "definition":"newer minus older same-valid-time HRRR forecast"},
    }


def stage(output:Path,now:datetime|None=None,
          discover_fn=discover,acquire_fn=acquire,render_fn=render)->dict:
    if output.exists():
        raise FileExistsError("Refusing to overwrite previous staged asset set")
    now=validation_time(now or datetime.now(timezone.utc))
    start=time.monotonic()
    report=discover_fn(now)
    valid,runs=check_pair(report,now)
    with TemporaryDirectory() as dirpath:
        temp=Path(dirpath)
        sources=[]
        for i,source in enumerate(runs):
            path=temp/f"source_{i}.grib2"
            meta=acquire_fn(utc_cycle(source["runAt"]),source["leadHours"],
                            "TMP","2 m above ground",path)
            if meta.get("status")!="transport_verified_not_decoded" or \
               not isinstance(meta.get("sha256"),str) or \
               meta.get("forecast_reference_at")!=source["runAt"] or \
               meta.get("forecast_lead_hours")!=source["leadHours"] or \
               meta.get("valid_at")!=valid:
                raise ValueError("Acquired GRIB identity/provenance mismatch")
            if meta.get("byte_start")!=source.get("byteStart") or \
               meta.get("byte_end_inclusive")!=source.get("byteEndInclusive"):
                raise ValueError("Source inventory changed between selection and download")
            if type(meta.get("bytes")) is not int or not 0<meta["bytes"]<=MAX_SOURCE_BYTES:
                raise ValueError("GRIB download exceeds bounded transfer budget")
            sources.append((path,source))
        staging=temp/"data"
        field=render_fn(sources,staging)
        file_bytes=sum(p.stat().st_size for p in staging.iterdir() if p.is_file())
        if file_bytes>MAX_STAGED_BYTES:
            raise ValueError("Staged raster size exceeds 1-MB cost cap")
        for p in field["products"]:
            if filehash(staging/p["image"])!=p["imageSha256"] or \
               filehash(staging/p["cog"])!=p["cogSha256"]:
                raise ValueError("Derived asset SHA mismatch")
        result={
            "schema":SCHEMA,"status":"staged_experimental_not_published",
            "source":"NOAA NODD public HRRR S3",
            "inventoryCheckedAt":report["checkedAt"],
            "processedAt":iso(datetime.now(timezone.utc)),
            "validAt":valid,
            "firstSeenAt":None,
            "actualPublicationAt":None,
            "sourcePublicationLatencyMinutes":None,
            "transferBytes":sum(p["sourceGribBytes"] for p in field["products"]),
            "derivedBytes":file_bytes,
            "wallSeconds":round(time.monotonic()-start,3),
            "spatialQA":"native ecCodes geographic coordinates + nearest-gridpoint pixel checks",
            "independentForecastVerification":"not performed",
            "operational":False,
            "automaticallyPublished":False,
            **field
        }
        (staging/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
        output.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(staging,output)
        return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(stage(args.out),indent=2))


if __name__=="__main__":
    main()
