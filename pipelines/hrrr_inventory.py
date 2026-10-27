"""Bounded NOAA HRRR 2m temperature inventory monitor.

Scientific semantics: an index observed now proves that the corresponding
GRIB2 index existed at check time. It does NOT prove that message bytes were
downloadable, decoded, first published at that time, or current enough for
safety-critical nowcasting. Scheduled Actions can be late or skipped.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import argparse
import json
import math
import sys

from pipelines.hrrr_subset import HEADERS, choose, parse_idx, source_url

SCHEMA = "stormchase-hrrr-inventory/1"
INDEX_MAX_BYTES = 64_000
CANDIDATE_LIMIT = 5
# Safe fallback: we do not advertise a pair older than 4 hours in inventory.
MAX_AGE_HOURS = 4


def iso(t: datetime) -> str:
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError("Explicit UTC timestamp required")
    return t.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validation_time(t:datetime)->datetime:
    if not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError("Real UTC now required")
    return t.astimezone(timezone.utc)


def target_valid_times(now: datetime, count: int = CANDIDATE_LIMIT) -> list[datetime]:
    """Prefer a valid hour at most +1h in the future; bounded recent fallback."""
    now=validation_time(now)
    if type(count) is not int or not 1<=count<=CANDIDATE_LIMIT:
        raise ValueError("Invalid candidate count")
    rounded=now.replace(minute=0,second=0,microsecond=0)
    target=rounded + (timedelta(hours=1) if now.minute >= 30 else timedelta())
    return [target-timedelta(hours=i) for i in range(count)]


def inspect_index(run:datetime,lead:int)->dict:
    """One bounded GET to the *index* only; no GRIB bytes transferred."""
    if lead not in (2,3):
        raise ValueError("Unexpected forecast lead for fixed-cost inventory")
    url=source_url(run,lead)+".idx"
    try:
        with urlopen(Request(url,headers=HEADERS),timeout=15) as response:
            http_status=response.status
            raw=response.read(INDEX_MAX_BYTES+1)
            last_modified=response.headers.get("Last-Modified")
            etag=response.headers.get("ETag")
    except HTTPError as e:
        # Absence is not a forecast failure. A 403/429/5xx is a source error.
        if e.code==404:
            return {"state":"not_found","source_index":url,"http_status":404,
                    "runAt":iso(run),"leadHours":lead,"sourceLastModified":None}
        return {"state":"source_error","source_index":url,"http_status":e.code,
                "runAt":iso(run),"leadHours":lead,"sourceLastModified":None,
                "error":"HTTP "+str(e.code)}
    except (URLError,TimeoutError,OSError) as e:
        return {"state":"source_error","source_index":url,"http_status":None,
                "runAt":iso(run),"leadHours":lead,"sourceLastModified":None,
                "error":type(e).__name__}
    if http_status!=200 or len(raw)>INDEX_MAX_BYTES:
        raise ValueError("Unexpected/oversize index response")
    try:
        entries=parse_idx(raw.decode("utf-8"),run)
        selected, end=choose(entries,"TMP","2 m above ground")
        if selected.descriptor != f"{lead} hour fcst":
            raise ValueError("Index forecast-step descriptor mismatch")
        if end is None:
            # Full-grid last-message length cannot be bounded from an index;
            # retain this as an incomplete inventory, never download blindly.
            raise ValueError("No bounded ending byte offset")
        length=end-selected.offset+1
        if not 1<=length<=64*1024*1024:
            raise ValueError("Indexed GRIB message size exceeds cap")
    except (ValueError,UnicodeDecodeError) as e:
        return {"state":"invalid_index","source_index":url,"http_status":200,
                "runAt":iso(run),"leadHours":lead,"sourceLastModified":last_modified,
                "error":type(e).__name__+": "+str(e)[:120]}
    modification=None
    if last_modified:
        try:
            t=parsedate_to_datetime(last_modified)
            modification=iso(t.astimezone(timezone.utc))
        except (TypeError,ValueError,OverflowError):
            modification=None
    return {
        "state":"inventory_observed", "source_index":url,"http_status":200,
        "runAt":iso(run),"leadHours":lead,"validAt":iso(run+timedelta(hours=lead)),
        "sourceLastModified":modification,"sourceETag":etag,
        "byteStart":selected.offset,"byteEndInclusive":end,
        "estimatedMessageBytes":length,
        "field":"TMP:2 m above ground",
        "gribDecoded":False,"messageTransferred":False,
    }


def discover(now:datetime,probe=inspect_index,max_candidates=CANDIDATE_LIMIT)->dict:
    now=validation_time(now)
    checked=iso(now)
    attempts=[]
    selection=None
    for valid in target_valid_times(now,max_candidates):
        pair=[]
        for lead in (3,2):  # older first, then newer
            run=valid-timedelta(hours=lead)
            result=probe(run,lead)
            if not isinstance(result,dict) or result.get("state") not in (
                "inventory_observed","not_found","invalid_index","source_error"
            ):
                raise ValueError("Probe returned invalid status")
            pair.append(result)
        attempts.append({"targetValidAt":iso(valid),"runs":pair})
        if all(x["state"]=="inventory_observed" for x in pair):
            # Do not confuse forecast lead/cycle with source index arrival.
            if any(x.get("validAt")!=iso(valid) or
                   x.get("runAt")!=iso(valid-timedelta(hours=x["leadHours"]))
                   for x in pair):
                raise ValueError("Provider probe run/lead/valid mismatch")
            valid_age=(now-valid).total_seconds()/3600
            if valid_age>MAX_AGE_HOURS:
                break
            selection={"validAt":iso(valid),"runs":pair,
                       "validTimeAgeHoursAtCheck":round(valid_age,3)}
            break
    return {
        "schema":SCHEMA,
        "provider":"NOAA NODD HRRR public S3",
        "checkedAt":checked,
        "status":"pair_inventory_observed" if selection else "no_verified_pair",
        "targetValidAt":iso(target_valid_times(now,1)[0]),
        "selected":selection,
        "attempts":attempts,
        "probeCount":sum(len(x["runs"]) for x in attempts),
        "totalEstimatedMessageBytes":sum(x["estimatedMessageBytes"] for x in
             (selection["runs"] if selection else [])),
        "firstSeenAt":None,
        "actualUpstreamFirstPublicationAt":None,
        "sourceAvailabilityLatencyMinutes":None,
        "measuredLagNote":"CHECK TIME only, not first publication; Last-Modified is S3 object metadata, not release latency",
        "scientificState":"inventory-only; no GRIB decode, geographic QA or forecast skill",
        "operationalForChaseDecisions":False,
        "nextStep":"Separate bounded GRIB byte-range acquisition/decoding; do not display inventory as a forecast",
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--at-utc",help="Testing only: timezone-aware YYYY-MM-DDTHH:MM:SSZ")
    a=parser.parse_args()
    if a.at_utc:
        try:now=datetime.fromisoformat(a.at_utc.replace("Z","+00:00"))
        except ValueError as e:raise SystemExit("Invalid --at-utc") from e
    else:now=datetime.now(timezone.utc)
    result=discover(now)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    # Missing data is a scientifically valid degraded state. This exits 0:
    # status is in JSON and cannot be misrepresented as a positive observation.
    return 0


if __name__=="__main__":
    sys.exit(main())
