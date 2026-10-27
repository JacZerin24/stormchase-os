"""Bounded, durable history of what StormChase OS actually saw upstream.

Do not infer true NOAA first-publication times from hourly polling or S3
Last-Modified: these records give only observation times and (when a previous
404 was observed) an availability interval bounded by two observations.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from pipelines.hrrr_inventory import iso

SCHEMA="stormchase-hrrr-observation-history/1"
SOURCE_SCHEMA="stormchase-hrrr-inventory/1"
KEEP_DAYS=5
MAX_RECORDS=300


def timestamp(value:str)->datetime:
    if not isinstance(value,str) or not value.endswith("Z"):
        raise ValueError("Explicit UTC timestamp required")
    try:
        t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as error:
        raise ValueError("Invalid UTC timestamp") from error
    if t.utcoffset()!=timedelta():
        raise ValueError("Timestamp must be UTC")
    return t


def blank()->dict:
    return {"schema":SCHEMA,"model":"HRRR","field":"TMP:2 m above ground",
            "updatedAt":None,"records":{},
            "interpretation":"first positive index observation, not official publication time"}


def merge(previous:dict,report:dict)->dict:
    if previous.get("schema")!=SCHEMA or not isinstance(previous.get("records"),dict):
        raise ValueError("Invalid previous observation ledger")
    if report.get("schema")!=SOURCE_SCHEMA or not isinstance(report.get("attempts"),list):
        raise ValueError("Invalid model inventory report")
    at=timestamp(report["checkedAt"])
    old_update=previous.get("updatedAt")
    if old_update is not None and timestamp(old_update)>at:
        raise ValueError("Refusing out-of-order historical replay of availability")
    records=json.loads(json.dumps(previous["records"]))
    for attempt in report["attempts"]:
        for item in attempt.get("runs",[]):
            state=item.get("state")
            if state not in ("inventory_observed","not_found","source_error","invalid_index"):
                raise ValueError("Unrecognized upstream status")
            run=timestamp(item["runAt"])
            lead=item["leadHours"]
            if type(lead) is not int or lead not in (2,3):
                raise ValueError("Unexpected model forecast lead")
            key=f"{iso(run)}__f{lead:02d}__TMP2m"
            record=records.get(key,{
                "runAt":iso(run),"leadHours":lead,"validAt":iso(run+timedelta(hours=lead)),
                "firstObservedIndexAt":None,
                "lastObservedIndexAt":None,
                "lastObserved404At":None,
                "sourceIndexLastModified":None,
                "sourceIndexETag":None,
                "lastObservedStatus":None,
                "latestObservationAt":None,
                "indexBecameObservableBetween":None,
            })
            if record["runAt"]!=iso(run) or record["leadHours"]!=lead:
                raise ValueError("Historical record collision")
            if state=="inventory_observed":
                if item.get("validAt")!=record["validAt"]:
                    raise ValueError("Source index valid-time mismatch")
                if record["firstObservedIndexAt"] is None:
                    record["firstObservedIndexAt"]=iso(at)
                    absent=record["lastObserved404At"]
                    if absent and timestamp(absent)<at:
                        record["indexBecameObservableBetween"]=[absent,iso(at)]
                record["lastObservedIndexAt"]=iso(at)
                record["sourceIndexLastModified"]=item.get("sourceLastModified")
                record["sourceIndexETag"]=item.get("sourceETag")
            elif state=="not_found":
                # Only confirmed HTTP404 can serve as a pre-availability bound.
                if record["firstObservedIndexAt"] is None:
                    record["lastObserved404At"]=iso(at)
            record["lastObservedStatus"]=state
            record["latestObservationAt"]=iso(at)
            records[key]=record
    cutoff=at-timedelta(days=KEEP_DAYS)
    records={k:v for k,v in records.items()
             if timestamp(v["latestObservationAt"])>=cutoff}
    if len(records)>MAX_RECORDS:
        ordered=sorted(records.items(),key=lambda item:item[1]["latestObservationAt"],reverse=True)
        records=dict(ordered[:MAX_RECORDS])
    observed=sum(v["firstObservedIndexAt"] is not None for v in records.values())
    bounded=sum(v["indexBecameObservableBetween"] is not None for v in records.values())
    return {"schema":SCHEMA,"model":"HRRR","field":"TMP:2 m above ground",
            "updatedAt":iso(at),"records":records,
            "recordsRetained":len(records),"positiveIndexRecords":observed,
            "availabilityWindowBoundedRecords":bounded,
            "interpretation":"First seen is StormChase OS observation, not NOAA original publication. An observed 404-to-200 interval bounds index accessibility, not GRIB completeness."}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--previous",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    record=merge(json.loads(a.previous.read_text()),json.loads(a.report.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({k:record[k] for k in ("updatedAt","recordsRetained",
          "positiveIndexRecords","availabilityWindowBoundedRecords")},indent=2))


if __name__=="__main__":
    main()
