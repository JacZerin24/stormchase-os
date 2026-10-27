"""Desktop/mobile smoke of a real recent NOAA HRRR Pages-ready model cache."""
from __future__ import annotations
import asyncio
import json
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright

ROOT="http://127.0.0.1:4173/"
ART=Path("browser-artifacts")
ART.mkdir(exist_ok=True)

async def run_one(browser,mobile):
    mode="mobile" if mobile else "desktop"
    page=await browser.new_page(
        viewport={"width":375,"height":812} if mobile else {"width":1440,"height":900},
        is_mobile=mobile,has_touch=mobile)
    responses=[]
    page.on("response",lambda res: responses.append((res.url,res.status)) if "/live/hrrr/" in res.url else None)
    try:
        await page.goto(ROOT,wait_until="domcontentloaded",timeout=60000)
        if mobile:
            await page.locator("button.sheet-trigger").click()
        panel=page.locator(".model-live-panel")
        await panel.locator("#hrrr-live-mode").wait_for(timeout=20000)
        if "RECENT FORECAST" not in await panel.inner_text():
            raise AssertionError("Fresh source metadata not visible")
        await panel.locator(".switch").click()
        await page.locator(".archive-map-banner").wait_for(timeout=10000)
        banner=await page.locator(".archive-map-banner").inner_text()
        if "NOT OBSERVED" not in banner or "EXPERIMENTAL" not in banner:
            raise AssertionError("Model forecast disclosure missing")
        expected=["newer.png","older.png","difference.png"]
        for setting,filename in zip(("newer","older","difference"),expected):
            await panel.locator("#hrrr-live-mode").select_option(setting)
            result=await page.evaluate("""async filename=>{
              const response=await fetch('/live/hrrr/latest.json',{cache:'no-store'});
              if(!response.ok)throw Error('Latest manifest HTTP '+response.status);
              const c=await response.json();
              const id=c.snapshots[0].id;
              const blob=await (await fetch('/live/hrrr/runs/'+id+'/'+filename)).blob();
              const im=await createImageBitmap(blob);
              const size={width:im.width,height:im.height,bytes:blob.size};
              im.close();return size;
            }""",filename)
            if result["width"]!=225 or result["height"]!=160 or result["bytes"]<200:
                raise AssertionError("Incorrect model PNG bytes or georeg size")
        await page.locator(".theme-button").click()
        await page.wait_for_timeout(800)
        if not await page.locator(".archive-map-banner").is_visible():
            raise AssertionError("Forecast source status disappeared on theme change")
        await page.screenshot(path=str(ART/f"recent-hrrr-{mode}.png"),full_page=True)
        images=[url for url,status in responses if status==200 and url.endswith(".png")]
        if not images:
            raise AssertionError("MapLibre made no successful model image source request")
        return {"viewport":mode,"forecast":banner,"modelImageRequests":len(images)}
    finally:
        await page.close()

async def main():
    report={"checkedAt":datetime.now(timezone.utc).isoformat(),"success":[],"errors":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader"])
        try:
            for mobile in (False,True):
                try:report["success"].append(await run_one(browser,mobile))
                except Exception as exc:report["errors"].append(str(exc))
        finally:await browser.close()
    (ART/"live-hrrr.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if len(report["success"])==2 and not report["errors"] else 1

if __name__=="__main__":
    raise SystemExit(asyncio.run(main()))
