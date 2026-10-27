"""Bounded one-shot official SPC probability vs conditional-intensity survey.

This is source schema reconnaissance ONLY, not a ready-to-display hazard map.
No raw polygons stored, no probabilities inferred/calibrated, no active polling.
"""
from __future__ import annotations
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from pathlib import Path
import argparse
import json
import sys
import time

BASE="https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer"
HEADERS={"User-Agent":"StormChaseOS/0.1 source study (https://github.com/JacZerin24/stormchase-os)",
         "Accept":"application/json"}
# Service layer inventory was verified against the current official FeatureServer.
LAYERS={
 2:("Day 1","tornado","conditional intensity"),
 3:("Day 1","tornado","occurrence probability"),
 4:("Day 1","hail","conditional intensity"),
 5:("Day 1","hail","occurrence probability"),
 6:("Day 1","wind","conditional intensity"),
 7:("Day 1","wind","occurrence probability"),
 10:("Day 2","tornado","conditional intensity"),
 11:("Day 2","tornado","occurrence probability"),
 12:("Day 2","hail","conditional intensity"),
 13:("Day 2","hail","occurrence probability"),
 14:("Day 2","wind","conditional intensity"),
 15:("Day 2","wind","occurrence probability"),
 18:("Day 3","severe","conditional intensity"),
 19:("Day 3","severe","occurrence probability"),
}
SAMPLE_LIMIT=12
ATTRS=("dn","label","label2","issue","valid","expire","idp_source","idp_ingestdate","idp_filedate")


def read_json(url:str)->dict:
    req=Request(url,headers=HEADERS)
    with urlopen(req,timeout=20) as response:
        if response.status!=200:raise RuntimeError(f"HTTP {response.status}")
        body=response.read(1_000_001)
    if len(body)>1_000_000:raise RuntimeError("Source JSON exceeded bound")
    data=json.loads(body)
    if not isinstance(data,dict) or "error" in data:
        raise RuntimeError("ArcGIS response error")
    return data


def survey_layer(layer:int)->dict:
    if layer not in LAYERS:raise ValueError("Unreviewed layer ID")
    day,hazard,kind=LAYERS[layer]
    base=f"{BASE}/{layer}/query"
    count=read_json(base+"?"+urlencode({"where":"1=1","returnCountOnly":"true","f":"json"})).get("count")
    if not isinstance(count,int) or count<0:raise ValueError("Bad layer count")
    sampled=read_json(base+"?"+urlencode({
       "where":"1=1","outFields":",".join(ATTRS),"returnGeometry":"false",
       "resultRecordCount":str(SAMPLE_LIMIT),"f":"json"
    }))
    features=sampled.get("features")
    if not isinstance(features,list) or len(features)>min(SAMPLE_LIMIT,count):
        raise ValueError("Bad paged attribute sample or count mismatch")
    attrs=[]
    for f in features:
        if not isinstance(f,dict) or not isinstance(f.get("attributes"),dict):
            raise ValueError("Missing ArcGIS attributes")
        attrs.append(f["attributes"])
    vals={}
    for key in ATTRS:
        vals[key]=list(dict.fromkeys(str(a.get(key)) for a in attrs))[:SAMPLE_LIMIT]
    # Important: source DN can encode percent or significance depending on layer.
    # Never reuse the categorical DN legend without a per-product contract.
    return {
      "layer":layer,"day":day,"hazard":hazard,"semantic":kind,
      "polygon_count":count,"sample_count":len(attrs),
      "fields":vals,
      "exceeded_transfer_limit":bool(sampled.get("exceededTransferLimit")),
      "interpretation":"UNVERIFIED field semantics; review official SPC text and legend",
      "limitation":"Up to 12 ATTRIBUTES only; no raw geometry, no full layer QA",
    }


def report()->dict:
    out={"generatedAt":datetime.now(timezone.utc).isoformat(),
         "officialService":BASE,
         "purpose":"Source-schema investigation; NOT operational probability or CIG map",
         "layers":[],"errors":{}}
    for lid in LAYERS:
        try:out["layers"].append(survey_layer(lid))
        except Exception as exc:out["errors"][str(lid)]=f"{type(exc).__name__}: {str(exc)[:140]}"
        time.sleep(.15)
    out["allQueriesSucceeded"]=len(out["errors"])==0
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    obj=report()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2))
    return 0 if obj["allQueriesSucceeded"] else 1


if __name__=="__main__":sys.exit(main())
