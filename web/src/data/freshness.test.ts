import {describe,it,expect} from 'vitest';
import {outlookHealth,warningHealth} from './freshness';
import type {FeedState} from '../hooks/useWeather';
import type {OutlookData,AlertData} from './weather';
const now=Date.parse('2026-10-27T21:00:00Z');
const active:OutlookData={
 geometry:{type:'FeatureCollection',features:[]},sourceFile:null,expectedFeatureCount:0,
 times:{issued:'2026-10-27T20:00:00Z',valid:'2026-10-27T12:00:00Z',expires:'2026-10-28T12:00:00Z',gisIngested:'2026-10-27T20:05:00Z',gisFiledate:null}};
const feed=<T,>(data:T):FeedState<T>=>({data,state:'ready',lastAttempt:'2026-10-27T20:59:00Z',lastSuccess:'2026-10-27T20:59:00Z',error:null});
describe('health semantics',()=>{
 it('blocks product that expired despite fresh download',()=>{
  expect(outlookHealth(feed({...active,times:{...active.times,expires:'2026-10-27T20:00:00Z'}}),now).render).toBe(false);
 });
 it('flags unknown metadata without inventing timestamps',()=>{
  expect(outlookHealth(feed({...active,times:{...active.times,issued:null}}),now).state).toBe('partial');
 });
 it('separates transport failure from meteorological zero',()=>{
  expect(outlookHealth({data:null,state:'error',error:'HTTP 503',lastSuccess:null,lastAttempt:null},now).state).toBe('error');
 });
 it('distinguishes legitimate empty alerts and missing polygons',()=>{
  const base:AlertData={geometry:{type:'FeatureCollection',features:[]},records:[],newestSent:null,totalMatchingCount:0,missingGeometryCount:0};
  expect(warningHealth(feed(base),now).state).toBe('available');
  expect(warningHealth(feed({...base,missingGeometryCount:1}),now).state).toBe('partial');
 });
});