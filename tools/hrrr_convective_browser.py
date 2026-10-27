"""Browser acceptance for seven genuine but HISTORICAL NOAA HRRR convective products.

Map graphics are simulations, not current radar or observed storm tracks.
This verifies image resources and UI science disclaimers, not forecast skill.
"""
from __future__ import annotations
import asyncio
import json
from datetime import datetime,timezone
from pathlib import Path
from playwright.async_api import async_playwright

ROOT='http://127.0.0.1:4173/'
OUTPUT=Path('browser-artifacts');OUTPUT.mkdir(exist_ok=True)
KEYS=('refc_f03','uh25_max_f03','uh25_swath_3h','hgt500_f03',
      't700_f03','cape_sb_f03','srh01_f03')

async def exercise(browser,mobile:bool)->dict:
    page=await browser.new_page(viewport={'width':375,'height':812} if mobile else {'width':1440,'height':900},
                                is_mobile=mobile,has_touch=mobile)
    seen=[]
    page.on('response',lambda response:
        seen.append({'file':response.url.split('/')[-1],'status':response.status})
        if '/pilot/hrrr-convective-20261027-20z/' in response.url else None)
    label='mobile' if mobile else 'desktop'
    try:
        await page.goto(ROOT,wait_until='domcontentloaded',timeout=60000)
        await page.locator('.map-canvas').wait_for(timeout=25000)
        if mobile:await page.locator('button.sheet-trigger').click()
        panel=page.locator('.model-archive-panel').first
        await panel.locator('#convective-field-select').wait_for(timeout=25000)
        if '20:00 UTC' not in await panel.inner_text():
            raise AssertionError('Model valid time not visible')
        tested=[]
        for key in KEYS:
            await panel.locator('#convective-field-select').select_option(key)
            await page.locator('.archive-map-banner').wait_for(timeout=10000)
            banner=await page.locator('.archive-map-banner').inner_text()
            if 'ARCHIVED' not in banner or 'NOT CURRENT' not in banner:
                raise AssertionError('Archived forecast not distinctly identified')
            data=await page.evaluate("""async name=>{
                const url='/pilot/hrrr-convective-20261027-20z/'+name+'.png';
                const response=await fetch(url,{cache:'no-store'});
                if(!response.ok)throw new Error('PNG HTTP '+response.status);
                const blob=await response.blob();
                const im=await createImageBitmap(blob);
                const result={width:im.width,height:im.height,bytes:blob.size};
                im.close();return result;
            }""",key)
            if data['width']!=225 or data['height']!=160 or data['bytes']<200:
                raise AssertionError('Unexpected authentic HRRR PNG shape/bytes: '+str(data))
            if key=='refc_f03':
                if 'not observed radar' not in (await panel.inner_text()).lower():
                    raise AssertionError('Simulated reflectivity disclaimer missing')
            if key=='uh25_swath_3h':
                if 'not an individual storm track' not in (await panel.inner_text()).lower():
                    raise AssertionError('UH swath mislabeled as a real storm track')
                await page.screenshot(path=str(OUTPUT/f'{label}-uh-swath.png'),full_page=True)
            tested.append({'key':key,'image':data})
        await page.locator('.theme-button').click()
        await page.wait_for_timeout(1000)
        if not await page.locator('.archive-map-banner').is_visible():
            raise AssertionError('Map restyle removed historical warning')
        delivered=[x['file'] for x in seen if x['status']==200]
        if not any(x.endswith('.png') for x in delivered):
            raise AssertionError('MapLibre never requested a genuine historical image')
        await page.screenshot(path=str(OUTPUT/f'{label}-reflectivity-and-controls.png'),full_page=True)
        return {'viewport':label,'products':tested,'loadedImageRequests':len(delivered)}
    finally:await page.close()

async def main():
    result={'timestamp':datetime.now(timezone.utc).isoformat(),
            'scope':'real archived GRIB image UI, not independent weather skill',
            'passed':[],'failures':[]}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,args=['--use-gl=angle','--use-angle=swiftshader'])
            try:
                for mobile in (False,True):
                    try:result['passed'].append(await exercise(browser,mobile))
                    except Exception as error:result['failures'].append(f'{"mobile" if mobile else "desktop"}: {error}')
            finally:await browser.close()
    except Exception as error:
        result['failures'].append(f'Chromium startup: {error}')
    OUTPUT.joinpath('convective-qa.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if len(result['passed'])==2 and not result['failures'] else 1
if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
