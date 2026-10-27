import {describe,it,expect} from 'vitest';
import {parseLiveCatalog,parseLiveCandidate,liveFreshness,liveOverlay} from './hrrrLive';
const sha='a'.repeat(64),valid='2026-10-27T21:00:00Z';
const entry={id:'20261027T21Z',validAt:valid,runAt:'2026-10-27T19:00:00Z',
 sourceObservedAt:'2026-10-27T20:54:00Z',manifest:'runs/20261027T21Z/candidate.json'};
const catalog={schema:'stormchase-hrrr-pages-catalog/1',updatedAt:'2026-10-27T21:15:00Z',
 snapshots:[entry],forecastSkillVerified:false};
const image=(key:string,runAt:string,leadHours:number)=>({
 key,file:key+'.png',sha256:sha,cog:key+'.tif',cogSha256:sha,
 runAt,leadHours,validAt:valid,sourceSha256:sha,geoCoverage:1,nativeDistanceKm:2,units:'K'});
const candidate={schema:'stormchase-hrrr-live-candidate/1',
 model:'HRRR',status:'geographic_QA_passed_forecast_skill_not_verified',
 forecastType:'model_prediction_not_observation',validAt:valid,latestRunAt:entry.runAt,
 sourceIndexObservedAt:entry.sourceObservedAt,generatedAt:'2026-10-27T21:05:00Z',
 bounds:[-103,33,-94,39.4],crs:'EPSG:4326',
 images:[image('older','2026-10-27T18:00:00Z',3),image('newer',entry.runAt,2)],
 difference:{file:'difference.png',sha256:sha,units:'°F forecast difference'},
 calibratedSevereWeatherProbability:false};
describe('near-current HRRR public model gate',()=>{
 it('requires trusted latest catalog and exact run/valid pairing',()=>{
  const c=parseLiveCatalog(catalog);
  const v=parseLiveCandidate(candidate,c.snapshots[0]);
  expect(liveOverlay(v,c.snapshots[0].id,'difference','/live/hrrr/').url)
   .toBe('/live/hrrr/runs/20261027T21Z/difference.png');
 });
 it('blocks fake forecast skill and unverified model time',()=>{
  expect(()=>parseLiveCatalog({...catalog,forecastSkillVerified:true})).toThrow();
  expect(()=>parseLiveCandidate({...candidate,latestRunAt:'2026-10-27T18:00:00Z'},entry)).toThrow();
  expect(()=>parseLiveCandidate({...candidate,images:[
   image('older','2026-10-27T18:00:00Z',3),
   image('newer','2026-10-27T18:00:00Z',2)]},entry)).toThrow();
 });
 it('flags staleness and rejects future forecast beyond accepted window',()=>{
  const t=Date.parse(valid);
  expect(liveFreshness(valid,t+60*60_000)).toBe('fresh');
  expect(liveFreshness(valid,t+4*60*60_000)).toBe('stale');
  expect(liveFreshness(valid,t-2*60*60_000)).toBe('future_invalid');
 });
 it('cannot traverse model asset paths',()=>{
  const c=parseLiveCandidate(candidate,entry);
  expect(()=>liveOverlay(c,'../x','newer','/live/hrrr/')).toThrow();
 });
});
