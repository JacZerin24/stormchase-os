"""Chromium acceptance for real archived HRRR map assets on desktop/mobile.

Historical case only. This checks resource loading, provenance UI and network
assets; independent geographic map inspection remains a human scientific gate.
"""
from __future__ import annotations
import asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import os
import sys
from playwright.async_api import async_playwright

BASE=os.environ.get("STORMCHASE_BROWSER_URL","http://127.0.0.1:4173/")
OUT=Path("browser-artifacts")
OUT.mkdir(exist_ok=True)
SOURCE="pilot/hrrr-20261027-18z/"

async def case(browser, mobile):
    name="mobile" if mobile else "desktop"
    page=await browser.new_page(
        viewport={"width":375,"height":812} if mobile else {"width":1440,"height":900},
        is_mobile=mobile,has_touch=mobile
    )
    responses=[]
    page.on("response",lambda response:responses.append(
        {"url":response.url.split('/')[-1],"status":response.status}
        if SOURCE in response.url else None))
    try:
        await page.goto(BASE,wait_until="domcontentloaded",timeout=60000)
        await page.locator(".map-canvas").wait_for(timeout=25000)
        if mobile:await page.locator("button.sheet-trigger").click()
        panel=page.locator(".model-archive-panel")
        await panel.wait_for(timeout=20000)
        await panel.locator("#model-cycle").wait_for(timeout=20000)
        if "2026-10-27 18:00 UTC" not in await panel.inner_text():
            raise AssertionError("Expected common 18Z model valid time not displayed")
        await panel.locator(".switch").click()
        await page.locator(".archive-map-banner").wait_for(timeout=10000)
        if "NOT CURRENT" not in await page.locator(".archive-map-banner").inner_text():
            raise AssertionError("Static historical forecast missing explicit archive warning")
        checks=[]
        files={
            "earlier":"hrrr_20261027_12z_f06_tmp2m.png",
            "later":"hrrr_20261027_15z_f03_tmp2m.png",
            "difference":"hrrr_valid18z_delta.png",
        }
        for value,filename in files.items():
            await page.locator("#model-cycle").select_option(value)
            # Fetch/decode independent of MapLibre to ensure the asset is a real
            # image file at the published URL. MapLibre network requests are
            # captured separately by on_response.
            info=await page.evaluate("""async (url)=>{
                const response=await fetch(url,{cache:'no-cache'});
                if(!response.ok)throw Error('PNG HTTP '+response.status);
                const blob=await response.blob();
                const image=await createImageBitmap(blob);
                const result={ok:true,width:image.width,height:image.height,bytes:blob.size};
                image.close();return result;
            }""",BASE+SOURCE+filename)
            if info["width"]!=225 or info["height"]!=160 or info["bytes"]<2000:
                raise AssertionError(f"Invalid {value} PNG geometry/size: {info}")
            await page.wait_for_timeout(600)
            checks.append({"mode":value,"image":filename,"png":info,
                "banner":await page.locator(".archive-map-banner").inner_text()})
            await page.screenshot(path=str(OUT/f"{name}-{value}.png"),full_page=True)
        await panel.get_by_role("button",name="FOCUS PLAINS TEST DOMAIN").click()
        # Initial display theme may follow system preference or storage;
        # toggle the actual control independent of initial light/dark state.
        await page.locator(".theme-button").click()
        await page.wait_for_timeout(1200)
        if not await page.locator(".archive-map-banner").is_visible():
            raise AssertionError("Archive overlay warning disappeared after basemap restyle")
        requested={p["url"] for p in responses if p["status"]==200}
        # At least one MapLibre/network fetch must have used the same asset.
        if not (requested & set(files.values())):
            raise AssertionError("No successful archived model image request observed")
        return {"viewport":name,"run_modes":checks,"asset_response_count":len(responses),
                "loaded_images":sorted(requested)}
    finally:
        await page.close()

async def main():
    report={"at":datetime.now(timezone.utc).isoformat(),"base":BASE,
            "scope":"Historical archived data smoke, not independently verified forecast/map geometry",
            "cases":[],"errors":[]}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader"])
            try:
                for mobile in (False,True):
                    try:report["cases"].append(await case(browser,mobile))
                    except Exception as exc:report["errors"].append(f"{'mobile' if mobile else 'desktop'}: {exc}")
            finally:await browser.close()
    except Exception as exc:report["errors"].append(f"browser: {exc}")
    OUT.joinpath("hrrr-browser-check.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if len(report["cases"])==2 and not report["errors"] else 1

if __name__=="__main__":
    sys.exit(asyncio.run(main()))
