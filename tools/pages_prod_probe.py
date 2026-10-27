"""One-shot public Pages smoke; DOES NOT constitute alert/forecast validity QA."""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen
import argparse
import json
import re
import sys

ROOT="https://jaczerin24.github.io/stormchase-os/"
PILOT="pilot/hrrr-20261027-18z/"
MAX_BYTES=2_000_000
UA="StormChaseOS/0.1 source verification (github.com/JacZerin24/stormchase-os)"


def get(url:str)->tuple[bytes,dict]:
    if not url.startswith(ROOT):
        raise ValueError("Only expected official public StormChase OS path allowed")
    req=Request(url,headers={"User-Agent":UA})
    with urlopen(req,timeout=20) as result:
        content=result.read(MAX_BYTES+1)
        metadata={"url":result.geturl(),"status":result.status,
                  "content_type":result.headers.get("Content-Type"),
                  "length":len(content)}
        if result.status!=200:raise ValueError(f"Unexpected HTTP {result.status}")
    if len(content)>MAX_BYTES:raise ValueError("Public asset exceeded bounded QA download")
    return content,metadata


def check()->dict:
    report={
        "checkedAt":datetime.now(timezone.utc).isoformat(),
        "scope":"production public HTTPS routing and immutable assets only",
        "expectedOrigin":ROOT,"passed":False,"files":[]
    }
    html,info=get(ROOT)
    document=html.decode("utf8")
    if "<html" not in document.lower() or "stormchase" not in document.lower():
        raise ValueError("Production root is not the expected HTML")
    report["files"].append(info)
    scripts=re.findall(r'src="(/stormchase-os/assets/[^"]+\.js)"',document)
    if not scripts:
        raise ValueError("Missing Vite JavaScript asset under repo-relative Pages base")
    for script in scripts[:2]:
        body,metadata=get(urljoin(ROOT,script))
        if not body or b"html" in body[:25].lower():
            raise ValueError("JavaScript asset served wrong content")
        report["files"].append(metadata)
    raw,meta=get(urljoin(ROOT,PILOT+"manifest.json"))
    report["files"].append(meta)
    manifest=json.loads(raw)
    if manifest.get("schema")!="stormchase-hrrr-archived-pilot/1" or \
       manifest.get("status")!="historical-experimental-display-not-live" or \
       manifest.get("validAt")!="2026-10-27T18:00:00Z" or \
       len(manifest.get("products",[]))!=2:
        raise ValueError("Published model manifest missing scientific archive contract")
    expected=[]
    for p in manifest["products"]:
        expected.extend([(p["image"],p["image_sha256"]),(p["cog"],p["cog_sha256"])])
    expected.append((manifest["differenceImage"],manifest["difference_sha256"]))
    for name,hashvalue in expected:
        if not isinstance(name,str) or not re.fullmatch(r"[a-z0-9_-]+\.(?:png|tif)",name):
            raise ValueError("Unsupported product path")
        data,record=get(urljoin(ROOT,PILOT+name))
        if sha256(data).hexdigest()!=hashvalue:
            raise ValueError("Published asset SHA256 differs from verified manifest")
        record["sha256"]=hashvalue
        report["files"].append(record)
    report["passed"]=True
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        result=check()
        status=0
    except Exception as error:
        result={"at":datetime.now(timezone.utc).isoformat(),"passed":False,
                "error":str(error),"expectedOrigin":ROOT}
        status=1
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return status

if __name__=="__main__":
    sys.exit(main())
