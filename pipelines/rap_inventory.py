"""One-shot NOAA NOMADS RAP inventory QA: NOT an operational RAP data feed.

No GRIB download, conversion, sounding, forecast overlay or comparison with
HRRR. Exact NOMADS current data paths verified by public directory listing.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen

from pipelines.hrrr_subset import parse_idx,choose
from pipelines.hrrr_inventory import iso,validation_time

BASE="https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod"
MAX_IDX_BYTES=128_000
MAX_ATTEMPTS=3


def source_url(run:datetime,lead:int)->str:
    if run.tzinfo is None or run.utcoffset()!=timedelta() or \
       run.minute or run.second or run.microsecond:
        raise ValueError("RAP requires exact UTC run initialization")
    if type(lead) is not int or not 0<=lead<=21:
        raise ValueError("Unsupported RAP forecast lead")
    return f"{BASE}/rap.{run:%Y%m%d}/rap.t{run:%H}z.awp130bgrbf{lead:02d}.grib2.idx"


def probe(run:datetime,lead:int=2)->dict:
    url=source_url(run,lead)
    try:
        with urlopen(Request(url,headers={
            "User-Agent":"StormChaseOS/0.1 RAP source study (https://github.com/JacZerin24/stormchase-os)",
            "Accept":"text/plain"
        }),timeout=20) as r:
            status=r.status
            data=r.read(MAX_IDX_BYTES+1)
            modified=r.headers.get("Last-Modified")
            mime=r.headers.get("Content-Type")
    except HTTPError as e:
        return {"state":"not_found" if e.code==404 else "source_error",
                "runAt":iso(run),"leadHours":lead,
                "url":url,"httpStatus":e.code,"error":"HTTP "+str(e.code)}
    except (URLError,TimeoutError,OSError) as e:
        return {"state":"source_error","runAt":iso(run),"leadHours":lead,
                "url":url,"httpStatus":None,"error":type(e).__name__}
    if status!=200 or len(data)>MAX_IDX_BYTES:
        return {"state":"invalid_inventory","runAt":iso(run),"leadHours":lead,
                "url":url,"httpStatus":status,"error":"Non-200 or index >128KB"}
    try:
        entries=parse_idx(data.decode("utf8"),run)
        found,end=choose(entries,"TMP","2 m above ground")
        if found.descriptor!=f"{lead} hour fcst" or end is None:
            raise ValueError("Unsupported RAP TMP step or open-ended range")
        if not 0<end-found.offset+1<64*1024*1024:
            raise ValueError("Invalid RAP message size")
    except (ValueError,UnicodeDecodeError) as e:
        # HTTP 200 sometimes transports provider error HTML or a different
        # index dialect. Capture one bounded, sanitized line for source QA.
        first_line=data[:240].decode("utf8",errors="replace").splitlines()[0][:120] if data else ""
        return {"state":"invalid_inventory","runAt":iso(run),"leadHours":lead,
                "url":url,"httpStatus":status,"mime":mime,
                "firstLineSample":first_line,"error":str(e)[:160]}
    return {"state":"index_observed_only","runAt":iso(run),"leadHours":lead,
            "validAt":iso(run+timedelta(hours=lead)), "url":url,
            "httpStatus":200,"nomadsLastModifiedHeader":modified,
            "field":"TMP:2 m above ground","startByte":found.offset,
            "endByteInclusive":end,"estimatedFieldBytes":end-found.offset+1,
            "gribDecoded":False,"geographicGridVerified":False,
            "sourcePublicationAt":None}


def survey(now:datetime,checker=probe)->dict:
    now=validation_time(now)
    anchor=now.replace(minute=0,second=0,microsecond=0)
    items=[]
    for offset in (2,3,4):
        run=anchor-timedelta(hours=offset)
        x=checker(run,2)
        items.append(x)
        if x["state"]=="index_observed_only":
            break
    return {"schema":"stormchase-rap-source-survey/1",
            "checkedAt":iso(now),
            "provider":"NOAA/NCEP NOMADS RAP operational output",
            "status":"inventory_observed" if items[-1]["state"]=="index_observed_only" else "no_usable_inventory",
            "attempts":items,"selected":items[-1] if items[-1]["state"]=="index_observed_only" else None,
            "firstSeenAt":None,"sourcePublicationAt":None,
            "scientificNote":"RAP grid/parameter encoding and regional mapping NOT validated; no HRRR-to-RAP comparison",
            "liveProductEnabled":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    report=survey(datetime.now(timezone.utc))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
