import {describe,expect,it} from 'vitest';
import {compareRuns,parseModelFieldAsset,strictUtc} from './modelTime';
const base={
 model:'HRRR',parameter:'TMP',level:'2 m',units:'K',
 runAt:'2026-10-27T12:00:00Z',leadHours:6,validAt:'2026-10-27T18:00:00Z',
 accumulationStartAt:null,accumulationEndAt:null,
 sourceUrl:'https://example.test/source.grib2',assetUrl:'/models/tmp.tif',
 assetFormat:'cog',crs:'EPSG:4326',sha256:'a'.repeat(64),
 firstSeenAt:'2026-10-27T13:10:00Z',processingState:'validated',
 processingVersion:'pilot-1',missingFraction:0
} as const;
describe('model asset contract',()=>{
 it('requires explicit UTC/offset and precise run/valid time matching',()=>{
  expect(strictUtc('2026-10-27T13:00:00-05:00')).toBe('2026-10-27T18:00:00.000Z');
  expect(()=>strictUtc('2026-10-27T18:00:00')).toThrow();
  expect(()=>strictUtc('2026-02-30T18:00:00Z')).toThrow();
  expect(()=>parseModelFieldAsset({...base,leadHours:5})).toThrow(/mismatch/);
 });
 it('requires full QA provenance before advertising a field as map-ready',()=>{
  expect(parseModelFieldAsset(base).processingState).toBe('validated');
  expect(()=>parseModelFieldAsset({...base,sha256:null})).toThrow(/provenance/);
  expect(parseModelFieldAsset({...base,units:null,crs:null,assetUrl:null,assetFormat:null,sha256:null,processingState:'inventory-only'}).processingState).toBe('inventory-only');
 });
 it('distinguishes time-window accumulations from instantaneous parameters',()=>{
  expect(()=>parseModelFieldAsset({...base,accumulationStartAt:'2026-10-27T17:00:00Z',accumulationEndAt:null})).toThrow(/pair/);
  expect(()=>parseModelFieldAsset({...base,accumulationStartAt:'2026-10-27T14:00:00Z',accumulationEndAt:'2026-10-27T17:00:00Z'})).toThrow(/interval/);
 });
 it('pairs different cycles at same valid time but preserves lead',()=>{
  const old=parseModelFieldAsset(base);
  const newer=parseModelFieldAsset({...base,runAt:'2026-10-27T15:00:00Z',leadHours:3,firstSeenAt:'2026-10-27T16:10:00Z'});
  const incomplete=parseModelFieldAsset({...base,runAt:'2026-10-27T17:00:00Z',leadHours:1,processingState:'decoded-unverified',assetUrl:null,assetFormat:null});
  const cmp=compareRuns([old,newer,incomplete],{model:'HRRR',parameter:'TMP',level:'2 m',validAt:'2026-10-27T18:00:00Z'});
  expect(cmp.available.map(d=>d.leadHours)).toEqual([3,6]);
  expect(cmp.unavailable).toBe(1);
 });
});
