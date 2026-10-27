"""Actual Chromium browser smoke for the Weather v0.1 frontend.

Run from a GitHub Actions runner after starting a local Vite dev server.
Unlike urllib-only smoke this exercises CORS in browser JS; it is still not a
human visual signoff or a guarantee of warning accuracy/delivery.
"""
from __future__ import annotations
from datetime import datetime, timezone
from json import dumps
from pathlib import Path
import asyncio
import os
import sys
from playwright.async_api import async_playwright

URL = os.getenv("STORMCHASE_BROWSER_URL", "http://127.0.0.1:4173/")
OUTPUT = Path("browser-artifacts")
OUTPUT.mkdir(exist_ok=True)


async def inspect(page, viewport: str) -> dict:
    await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    await page.locator(".map-canvas").wait_for(timeout=25000)
    # On mobile the layer inspector is deliberately a collapsed bottom sheet.
    # Open it before asserting visibility; hidden content is intended behavior.
    if viewport == "mobile":
        await page.locator("button.sheet-trigger").click()
    await page.locator("article.layer-card").first.wait_for(timeout=25000)
    async def feed_labels():
        return [t.strip() for t in await page.locator(".layer-card .feed-status").all_text_contents()]
    for _ in range(60):
        labels = await feed_labels()
        if len(labels) == 2 and not any("CONNECTING" in t for t in labels):
            break
        await page.wait_for_timeout(1000)
    else:
        raise AssertionError("Weather layer statuses never resolved from CONNECTING")
    labels = await feed_labels()
    retries = 0
    # NOAA services occasionally fail transiently; retry one user-initiated
    # refresh while retaining the evidence that a transient failure occurred.
    while any("SOURCE ERROR" in t for t in labels) and retries < 2:
        retries += 1
        await page.get_by_role("button", name="REFRESH WEATHER DATA").click()
        await page.wait_for_timeout(4500)
        labels = await feed_labels()
    if any("SOURCE ERROR" in t for t in labels):
        details = [await page.locator("article.layer-card").nth(i).inner_text() for i in range(2)]
        raise AssertionError("Weather source error despite retries: " + str(labels)
                             + " | visible details: " + str(details)[:1100])
    result = {
        "viewport": viewport,
        "url": page.url,
        "feed_labels": labels,
        "manual_refresh_retries": retries,
        "spc_metadata": await page.locator("article.layer-card").nth(0).locator(".meta").inner_text(),
        "nws_metadata": await page.locator("article.layer-card").nth(1).locator(".meta").inner_text(),
        "map_canvas_present": await page.locator(".map-canvas").count() == 1,
        "source_links": await page.locator("a.source-link").count(),
    }
    # These request checks really execute fetch in a cross-origin browser context.
    async def check(url: str, mime: str) -> dict:
        return await page.evaluate(
            """async ({url, mime}) => {
                 try {
                   const response=await fetch(url,{headers:{Accept:mime},cache:'no-store'});
                   const data=await response.json();
                   return {ok:response.ok,status:response.status,
                           type:data?.type??null,feature_count:data?.features?.length??null,
                           count:data?.count??null,upstream_error:!!data?.error};
                 } catch(error){return {ok:false,error:String(error)}}
            }""", {"url":url, "mime":mime})
    spc="https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer/1/query?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=geojson"
    nws="https://api.weather.gov/alerts/active?event=Tornado+Warning"
    result["browser_spc_fetch"] = await check(spc,"application/geo+json")
    result["browser_nws_fetch"] = await check(nws,"application/geo+json")
    if not result["browser_spc_fetch"].get("ok") or result["browser_spc_fetch"].get("type")!="FeatureCollection":
        raise AssertionError("Browser SPC GeoJSON request failed: "+str(result["browser_spc_fetch"]))
    if not result["browser_nws_fetch"].get("ok") or result["browser_nws_fetch"].get("type")!="FeatureCollection":
        raise AssertionError("Browser NWS GeoJSON request failed: "+str(result["browser_nws_fetch"]))
    await page.screenshot(path=str(OUTPUT/f"{viewport}.png"), full_page=True, timeout=25000)
    return result


async def main() -> int:
    report = {"at":datetime.now(timezone.utc).isoformat(),"website":URL,
              "scope":"Chromium real-browser CORS and UI smoke; no human visual approval",
              "views":[],"errors":[]}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--use-gl=angle","--use-angle=swiftshader"])
            try:
                desktop=await browser.new_page(viewport={"width":1440,"height":900})
                try:
                    report["views"].append(await inspect(desktop,"desktop"))
                except Exception as ex:
                    report["errors"].append("desktop: "+str(ex))
                    await desktop.screenshot(path=str(OUTPUT/"desktop-error.png"),full_page=True)
                await desktop.close()
                mobile=await browser.new_page(viewport={"width":375,"height":812},is_mobile=True,has_touch=True)
                try:
                    report["views"].append(await inspect(mobile,"mobile"))
                except Exception as ex:
                    report["errors"].append("mobile: "+str(ex))
                    await mobile.screenshot(path=str(OUTPUT/"mobile-error.png"),full_page=True)
                await mobile.close()
            finally:
                await browser.close()
    except Exception as exc:
        report["errors"].append("browser environment: "+str(exc))
    OUTPUT.joinpath("browser-smoke.json").write_text(dumps(report,indent=2)+"\n")
    print(dumps(report,indent=2))
    return 0 if not report["errors"] and len(report["views"])==2 else 1


if __name__=="__main__":
    sys.exit(asyncio.run(main()))
