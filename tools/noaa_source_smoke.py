"""One-shot upstream-only NOAA smoke test.

Makes bounded NOAA requests and records *aggregated* metadata, not raw alerts
or raw SPC geometries. A GitHub runner is not a browser, so a successful run
DOES NOT certify frontend CORS, visual rendering, warnings completeness, or
official product-to-website equivalence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from json import dumps, loads
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import argparse
import sys

SPC = "https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer"
NWS = "https://api.weather.gov/alerts/active"
ORIGIN = "https://jaczerin24.github.io"
UA = "StormChaseOS-Research/0.1 (https://github.com/JacZerin24/stormchase-os)"
MAX_BYTES = 6_000_000
DAYS = {1: 1, 2: 9, 3: 17}
EVENTS = ("Tornado Warning", "Severe Thunderstorm Warning")


def date_string() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def request_json(url: str, accept: str, retries: int = 1) -> tuple[dict, dict]:
    headers = {"User-Agent": UA, "Accept": accept, "Origin": ORIGIN}
    last_error = None
    for attempt in range(retries + 1):
        start = monotonic()
        try:
            with urlopen(Request(url, headers=headers), timeout=25) as response:
                status = response.status
                raw = response.read(MAX_BYTES + 1)
                meta = {
                    "http_status": status,
                    "elapsed_seconds": round(monotonic() - start, 3),
                    "bytes": len(raw),
                    "content_type": response.headers.get("Content-Type"),
                    "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin"),
                    "date_header": response.headers.get("Date"),
                    "last_modified_header": response.headers.get("Last-Modified"),
                }
            if len(raw) > MAX_BYTES:
                raise ValueError("Response exceeded 6 MB bounded request")
            if status != 200:
                raise ValueError(f"Non-200 HTTP status: {status}")
            result = loads(raw)
            if not isinstance(result, dict):
                raise ValueError("Expected JSON object from source")
            if "error" in result:
                raise ValueError("Upstream JSON error object")
            return result, meta
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {str(exc)[:150]}"
            if attempt < retries:
                sleep(2)
    raise RuntimeError(last_error)


def summarize_spc(day: int) -> dict:
    endpoint = f"{SPC}/{DAYS[day]}/query"
    count_url = endpoint + "?" + urlencode({"where": "1=1", "returnCountOnly": "true", "f": "json"})
    query_url = endpoint + "?" + urlencode({
        "where": "1=1", "outFields": "dn,issue,valid,expire,idp_source,idp_ingestdate",
        "returnGeometry": "true", "outSR": "4326", "resultOffset": "0",
        "resultRecordCount": "10", "f": "geojson"
    })
    count_json, count_http = request_json(count_url, "application/json")
    if not isinstance(count_json.get("count"), int) or count_json["count"] < 0:
        raise ValueError("SPC feature count missing/invalid")
    sample, sample_http = request_json(query_url, "application/geo+json")
    if sample.get("type") != "FeatureCollection" or not isinstance(sample.get("features"), list):
        raise ValueError("SPC not GeoJSON FeatureCollection")
    if len(sample["features"]) > 10 or len(sample["features"]) > count_json["count"]:
        raise ValueError("SPC sample/count mismatch")
    properties = []
    geometry_types = []
    for feature in sample["features"]:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("SPC non-Feature")
        props = feature.get("properties")
        if not isinstance(props, dict):
            raise ValueError("SPC feature without properties")
        properties.append(props)
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError("SPC unexpected/missing geometry")
        geometry_types.append(geometry["type"])
    fields = ("issue", "valid", "expire", "idp_source", "idp_ingestdate")
    values = {name: list(dict.fromkeys(str(p.get(name)) for p in properties))[:4] for name in fields}
    return {
        "day": day, "layer_id": DAYS[day], "provider_count": count_json["count"],
        "sample_count": len(properties), "dn_values": sorted(set(str(p.get("dn")) for p in properties)),
        "geometry_types": sorted(set(geometry_types)),
        "time_fields_sample": values,
        "count_response": count_http, "geojson_response": sample_http,
        "coverage_note": "First 10 polygons ONLY; no full-coverage validation",
    }


def summarize_nws(event: str) -> dict:
    url = NWS + "?" + urlencode({"event": event})
    data, meta = request_json(url, "application/geo+json")
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("NWS not a FeatureCollection")
    polygons = null_geometries = other_geometries = missing_ids = 0
    sent_values = []
    seen_ids = set()
    distinct_events = set()
    for f in data["features"]:
        if not isinstance(f, dict) or not isinstance(f.get("properties"), dict):
            raise ValueError("NWS malformed alert feature")
        p = f["properties"]
        distinct_events.add(str(p.get("event")))
        ident = f.get("id") or p.get("id")
        if not isinstance(ident, str) or not ident:
            missing_ids += 1
        else:
            seen_ids.add(ident)
        if f.get("geometry") is None:
            null_geometries += 1
        elif isinstance(f.get("geometry"), dict) and f["geometry"].get("type") in ("Polygon", "MultiPolygon"):
            polygons += 1
        else:
            other_geometries += 1
        if isinstance(p.get("sent"), str):
            sent_values.append(p["sent"])
    if distinct_events - {event}:
        raise ValueError("NWS single-event query returned unexpected events: " + repr(sorted(distinct_events)))
    return {
        "event": event, "total_features": len(data["features"]),
        "polygon_count": polygons, "null_geometry_count": null_geometries,
        "other_geometry_count": other_geometries, "missing_id_count": missing_ids,
        "unique_ids_count": len(seen_ids),
        "newest_sent": max(sent_values) if sent_values else None,
        "response": meta, "note": "Zero active features is not evidence of complete historical coverage",
    }


def run() -> dict:
    report = {
        "generated_at_utc": date_string(),
        "scope": "Upstream HTTPS smoke test from GitHub Actions; NOT real-browser CORS/visual QA",
        "spc": {}, "nws": {}, "failures": {},
    }
    for day in DAYS:
        try:
            report["spc"][f"day{day}"] = summarize_spc(day)
        except Exception as exc:
            report["failures"][f"spc_day{day}"] = f"{type(exc).__name__}: {str(exc)[:180]}"
    for event in EVENTS:
        try:
            report["nws"][event] = summarize_nws(event)
        except Exception as exc:
            report["failures"][event] = f"{type(exc).__name__}: {str(exc)[:180]}"
    report["transport_checks_passed"] = not bool(report["failures"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dumps(report, indent=2) + "\n")
    print(dumps(report, indent=2))
    return 0 if report["transport_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
