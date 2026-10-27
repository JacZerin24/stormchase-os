/** Latest-published HRRR forecast assets: source/geography checked, NOT skill verified. */
export const LIVE_ROOT='live/hrrr/';
export type LiveMode='older'|'newer'|'difference';
type Item={id:string;validAt:string;runAt:string;sourceObservedAt:string;manifest:string};
export interface LiveCatalog{
 schema:'stormchase-hrrr-pages-catalog/1';
 updatedAt:string|null;
 snapshots:Item[];
 forecastSkillVerified:false;
}
export interface LiveImage {
 key:'older'|'newer';
 file:string;sha256:string;cog:string;cogSha256:string;
 runAt:string;validAt:string;leadHours:number;units:'K';
 sourceSha256:string;geoCoverage:number;nativeDistanceKm:number;
}
export interface LiveCandidate{
 schema:'stormchase-hrrr-live-candidate/1';
 model:'HRRR';status:'geographic_QA_passed_forecast_skill_not_verified';
 forecastType:'model_prediction_not_observation';
 validAt:string;latestRunAt:string;sourceIndexObservedAt:string;generatedAt:string;
 bounds:[number,number,number,number];crs:'EPSG:4326';
 images:[LiveImage,LiveImage];
 difference:{file:'difference.png';sha256:string;units:string};
 calibratedSevereWeatherProbability:false;
}
const isObj=(x:unknown):x is Record<string,unknown>=>!!x&&typeof x==='object'&&!Array.isArray(x);
const sha=(v:unknown)=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const ts=(v:unknown):v is string=>typeof v==='string'&&
 /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(v)&&
 Number.isFinite(Date.parse(v))&&new Date(v).toISOString().replace('.000Z','Z')===v;
const id=(v:unknown)=>typeof v==='string'&&/^\d{8}T\d\dZ$/.test(v);
const dateMs=(v:string)=>Date.parse(v);
export function parseLiveCatalog(raw:unknown):LiveCatalog{
 if(!isObj(raw)||raw.schema!=='stormchase-hrrr-pages-catalog/1'||
    raw.forecastSkillVerified!==false||!Array.isArray(raw.snapshots)||
    raw.snapshots.length>6||(raw.updatedAt!==null&&!ts(raw.updatedAt)))
  throw new Error('Untrusted latest-model catalog');
 let prior=Number.POSITIVE_INFINITY;
 for(const entry of raw.snapshots){
  if(!isObj(entry)||!id(entry.id)||!ts(entry.validAt)||!ts(entry.runAt)||
     !ts(entry.sourceObservedAt)||entry.manifest!==`runs/${entry.id}/candidate.json`||
     dateMs(entry.validAt)>prior||dateMs(entry.runAt)>=dateMs(entry.validAt))
   throw new Error('Model catalog contains inconsistent UTC/source record');
  prior=dateMs(entry.validAt);
 }
 return raw as unknown as LiveCatalog;
}
export function parseLiveCandidate(raw:unknown,entry:Item):LiveCandidate{
 if(!isObj(raw)||raw.schema!=='stormchase-hrrr-live-candidate/1'||
    raw.status!=='geographic_QA_passed_forecast_skill_not_verified'||
    raw.forecastType!=='model_prediction_not_observation'||raw.model!=='HRRR'||
    raw.calibratedSevereWeatherProbability!==false||
    !ts(raw.validAt)||raw.validAt!==entry.validAt||
    !ts(raw.latestRunAt)||raw.latestRunAt!==entry.runAt||
    !ts(raw.sourceIndexObservedAt)||!ts(raw.generatedAt)||
    raw.crs!=='EPSG:4326'||!Array.isArray(raw.bounds)||
    raw.bounds.join(',')!=='-103,33,-94,39.4')
  throw new Error('Recent HRRR candidate fails scientific provenance gate');
 if(!Array.isArray(raw.images)||raw.images.length!==2)throw new Error('Missing comparison cycles');
 const images=raw.images as unknown[];
 for(let i=0;i<2;i++){
  const x=images[i];
  if(!isObj(x)||x.key!==(i===0?'older':'newer')||x.file!==(i===0?'older.png':'newer.png')||
     x.cog!==(i===0?'older.tif':'newer.tif')||!sha(x.sha256)||!sha(x.cogSha256)||
     !sha(x.sourceSha256)||!ts(x.runAt)||!ts(x.validAt)||x.validAt!==entry.validAt||
     x.leadHours!==(i===0?3:2)||dateMs(x.runAt)+x.leadHours*3_600_000!==dateMs(x.validAt)||
     x.units!=='K'||typeof x.geoCoverage!=='number'||x.geoCoverage<.97||
     typeof x.nativeDistanceKm!=='number'||x.nativeDistanceKm>5.01)
   throw new Error('Recent HRRR run metadata invalid or incomplete');
 }
 if(!isObj(raw.difference)||raw.difference.file!=='difference.png'||!sha(raw.difference.sha256))
  throw new Error('Missing hashed same-valid-time forecast difference');
 return raw as unknown as LiveCandidate;
}
export function liveFreshness(validAt:string,nowMs:number):'fresh'|'stale'|'future_invalid'{
 const ageMs=nowMs-dateMs(validAt);
 if(!Number.isFinite(ageMs)||ageMs< -3_600_000)return 'future_invalid';
 return ageMs>3*3_600_000?'stale':'fresh';
}
export function liveOverlay(candidate:LiveCandidate,id:string,mode:LiveMode,root:string){
 if(!/^\d{8}T\d\dZ$/.test(id)||!root.endsWith('/'))throw new Error('Invalid model image base');
 const file=mode==='difference'?'difference.png':(mode==='older'?'older.png':'newer.png');
 return {url:root+'runs/'+id+'/'+file,bounds:candidate.bounds,kind:'live' as const};
}
