"""On-demand HRRR full-grid GRIB2 message download (transport/provenance only).

No GRIB value decoding, geographic subsetting, live scheduling or map layers.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import argparse
import hashlib
import json
import re

BASE = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com"
MAX_BYTES = 64 * 1024 * 1024
ALLOWED = {("TMP", "2 m above ground"), ("DPT", "2 m above ground"),
           ("UGRD", "10 m above ground"), ("VGRD", "10 m above ground")}
HEADERS = {"User-Agent": "StormChaseOS/0.1 research (github.com/JacZerin24/stormchase-os)"}


@dataclass(frozen=True)
class Entry:
    index: int
    offset: int
    cycle: str
    variable: str
    level: str
    descriptor: str
    raw: str


def utc_cycle(value: str) -> datetime:
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid UTC cycle") from error
    if t.tzinfo is None or t.utcoffset() != timedelta(0) or t.minute or t.second or t.microsecond:
        raise ValueError("Cycle must be an exact, timezone-aware UTC hour")
    return t.astimezone(timezone.utc)


def source_url(cycle: datetime, lead: int) -> str:
    if cycle.tzinfo is None or cycle.utcoffset() != timedelta(0):
        raise ValueError("Cycle must be UTC")
    if type(lead) is not int or not 0 <= lead <= 48:
        raise ValueError("Forecast lead must be an integer from 0 to 48 hours")
    return (f"{BASE}/hrrr.{cycle:%Y%m%d}/conus/"
            f"hrrr.t{cycle:%H}z.wrfsfcf{lead:02d}.grib2")


def parse_idx(text: str, cycle: datetime) -> list[Entry]:
    found = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(":")
        if len(parts) < 6 or not parts[0].isdigit() or not parts[1].isdigit() or not parts[2].startswith("d="):
            raise ValueError("Malformed .idx record")
        number, offset = int(parts[0]), int(parts[1])
        if number != len(found) + 1 or offset <= (found[-1].offset if found else -1):
            raise ValueError("Nonmonotonic message index/offset")
        if parts[2][2:] != cycle.strftime("%Y%m%d%H"):
            raise ValueError("Index initialization differs from requested cycle")
        found.append(Entry(number, offset, parts[2][2:], parts[3], parts[4], parts[5], line))
    if not found or found[0].offset != 0:
        raise ValueError("Empty/truncated .idx inventory")
    return found


def choose(entries: list[Entry], variable: str, level: str) -> tuple[Entry, int | None]:
    if (variable, level) not in ALLOWED:
        raise ValueError("Unverified pilot field selection")
    matches = [(i, e) for i, e in enumerate(entries) if e.variable == variable and e.level == level]
    if len(matches) != 1:
        raise ValueError("Expected precisely one GRIB inventory match, got " + str(len(matches)))
    i, e = matches[0]
    return e, entries[i + 1].offset - 1 if i + 1 < len(entries) else None


def fetch_index(url: str) -> str:
    with urlopen(Request(url + ".idx", headers=HEADERS), timeout=30) as response:
        body = response.read(5_000_001)
    if len(body) > 5_000_000:
        raise ValueError("Index exceeds byte cap")
    return body.decode("utf-8")


def fetch_message(url: str, start: int, end: int | None) -> tuple[bytes, str]:
    limit = str(end) if end is not None else ""
    request = Request(url, headers={**HEADERS, "Range": f"bytes={start}-{limit}"})
    with urlopen(request, timeout=30) as response:
        if response.status != 206:
            raise ValueError("HTTP 206 required; provider ignored Range")
        header = response.headers.get("Content-Range", "")
        parsed = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", header)
        if not parsed:
            raise ValueError("Missing Content-Range")
        lo, hi, total = map(int, parsed.groups())
        if lo != start or (end is not None and hi != end) or hi >= total or hi < lo:
            raise ValueError("Unexpected GRIB byte interval")
        if hi - lo + 1 > MAX_BYTES:
            raise ValueError("Message exceeds download byte cap")
        body = response.read(MAX_BYTES + 1)
    if len(body) != hi - lo + 1 or len(body) > MAX_BYTES:
        raise ValueError("Truncated or oversized download")
    if not body.startswith(b"GRIB") or not body.endswith(b"7777"):
        raise ValueError("Invalid GRIB message framing")
    return body, header


def acquire(cycle: datetime, lead: int, variable: str, level: str,
            output: Path, dry_run: bool = False) -> dict:
    url = source_url(cycle, lead)
    entry, end = choose(parse_idx(fetch_index(url), cycle), variable, level)
    manifest = {
        "status": "inventory_verified_only" if dry_run else "transport_verified_not_decoded",
        "provider": "NOAA NODD public HRRR AWS", "url": url, "index_url": url + ".idx",
        "forecast_reference_at": cycle.isoformat().replace("+00:00", "Z"),
        "forecast_lead_hours": lead,
        "valid_at": (cycle + timedelta(hours=lead)).isoformat().replace("+00:00", "Z"),
        "variable": variable, "level": level, "index_record": entry.raw,
        "byte_start": entry.offset, "byte_end_inclusive": end,
        "published_at": None, "units": None, "projection": None, "missing_mask": None,
        "retrieved_at": None, "bytes": None, "sha256": None
    }
    if dry_run:
        return manifest
    metadata_path = output.with_suffix(output.suffix + ".json")
    if output.exists() or metadata_path.exists():
        raise FileExistsError("Refusing to overwrite previous immutable acquisition")
    body, content_range = fetch_message(url, entry.offset, end)
    manifest.update(retrieved_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                    content_range=content_range)
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    try:
        partial.write_bytes(body)
        metadata_path.write_text(json.dumps(manifest, indent=2) + "\n")
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="2026-10-27T12:00:00Z")
    parser.add_argument("--lead", type=int, required=True)
    parser.add_argument("--variable", required=True)
    parser.add_argument("--level", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(acquire(utc_cycle(args.run), args.lead, args.variable,
                             args.level, args.out, args.dry_run), indent=2))


if __name__ == "__main__":
    main()
