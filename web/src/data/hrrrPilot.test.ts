import {describe,it,expect} from 'vitest';
import {parsePilotManifest,pilotOverlay} from './hrrrPilot';
const sha='a'.repeat(64);
const product=(runAt:string,leadHours:number)=>({
  model:'HRRR',parameter:'TMP',level:'2 m above ground',units:'K',
  runAt,leadHours,validAt:'2026-10-27T18:00:00Z',
  image:'hrrr_'+leadHours+'.png',cog:'hrrr_'+leadHours+'.tif',
  grib_sha256:sha,image_sha256:sha,cog_sha256:sha,
  geolocation_QA:{coverage_fraction:0.999,max_nearest_km:3,unmatched_cells:0},
  min_K:270,max_K:300
});
const manifest={
 schema:'stormchase-hrrr-archived-pilot/1',
 status:'historical-experimental-display-not-live',
 validAt:'2026-10-27T18:00:00Z',bounds:[-103,33,-94,39.5],
 rasterCrs:'EPSG:4326',
 products:[product('2026-10-27T12:00:00Z',6),product('2026-10-27T15:00:00Z',3)],
 differenceImage:'diff.png',difference_sha256:sha
};
describe('archived HRRR pilot',()=>{
 it('requires two real-cycle timestamps aligned at identical valid time',()=>{
  const d=parsePilotManifest(manifest);
  expect(pilotOverlay(d,'earlier','/pilot/').url).toBe('/pilot/hrrr_6.png');
  expect(pilotOverlay(d,'later','/pilot/').url).toBe('/pilot/hrrr_3.png');
  expect(pilotOverlay(d,'difference','/pilot/').url).toBe('/pilot/diff.png');
 });
 it('blocks broken forecast valid-time arithmetic',()=>{
  expect(()=>parsePilotManifest({...manifest,products:[product('2026-10-27T13:00:00Z',6),manifest.products[1]]})).toThrow();
 });
 it('rejects geographical QA failures and traversal file names',()=>{
  expect(()=>parsePilotManifest({...manifest,products:[{...manifest.products[0],geolocation_QA:{...manifest.products[0].geolocation_QA,coverage_fraction:0.4}},manifest.products[1]]})).toThrow();
  expect(()=>parsePilotManifest({...manifest,differenceImage:'../../current.png'})).toThrow();
 });
 it('forbids promotion to live from historical static product',()=>{
  expect(()=>parsePilotManifest({...manifest,status:'current'})).toThrow();
  expect(()=>parsePilotManifest({...manifest,validAt:'2026-10-28T18:00:00Z'})).toThrow();
 });
});
