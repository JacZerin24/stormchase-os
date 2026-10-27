import type { Feature, FeatureCollection, GeoJsonProperties, Polygon, MultiPolygon } from 'geojson';

export type AreaFeature = Feature<Polygon | MultiPolygon, GeoJsonProperties>;
export type AreaCollection = FeatureCollection<Polygon | MultiPolygon, GeoJsonProperties>;
export const SPC_INFO = 'https://www.spc.noaa.gov/products/outlook/';
export const NWS_INFO = 'https://www.weather.gov/';
export const SPC_CATEGORIES: Record<number, { abbreviation: string; label: string; color: string }> = {
  2: { abbreviation: 'TSTM', label: 'General thunderstorm', color: '#c1e9c1' },
  3: { abbreviation: 'MRGL', label: 'Marginal', color: '#66a366' },
  4: { abbreviation: 'SLGT', label: 'Slight', color: '#ffe066' },
  5: { abbreviation: 'ENH', label: 'Enhanced', color: '#ffa366' },
  6: { abbreviation: 'MDT', label: 'Moderate', color: '#e06666' },
  8: { abbreviation: 'HIGH', label: 'High', color: '#ee99ee' }
};
export const emptyCollection = (): AreaCollection => ({type:'FeatureCollection', features:[]});

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function featureList(payload: unknown): unknown[] {
  if (!record(payload) || payload.type !== 'FeatureCollection' || !Array.isArray(payload.features)) {
    throw new Error('Provider response is not a GeoJSON FeatureCollection.');
  }
  return payload.features;
}
function isRing(value: unknown): boolean {
  if (!Array.isArray(value) || value.length < 4) return false;
  const positions = value as unknown[];
  if (!positions.every(p=>Array.isArray(p) && p.length >= 2 &&
    typeof p[0] === 'number' && typeof p[1] === 'number' &&
    Number.isFinite(p[0]) && Number.isFinite(p[1]) &&
    Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90)) return false;
  const first = positions[0] as number[], last = positions.at(-1) as number[];
  return first[0] === last[0] && first[1] === last[1];
}
function areaFeature(value: unknown): value is AreaFeature {
  if (!record(value) || value.type !== 'Feature' || !record(value.geometry)) return false;
  const geom = value.geometry;
  if (!Array.isArray(geom.coordinates)) return false;
  if (geom.type === 'Polygon') return geom.coordinates.length > 0 &&
    geom.coordinates.every(isRing);
  if (geom.type === 'MultiPolygon') return geom.coordinates.length > 0 &&
    geom.coordinates.every(p=>Array.isArray(p) && p.length > 0 && p.every(isRing));
  return false;
}
function props(value: unknown): Record<string, unknown> {
  return record(value) && record(value.properties) ? value.properties : {};
}

/** Numeric ArcGIS dates are Unix milliseconds. Bare ISO instants must include timezone. */
export function parseSourceTime(value: unknown): string | null {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d.toISOString();
  }
  if (typeof value !== 'string' || !value.trim()) return null;
  const s = value.trim();
  // Real SPC GIS feed observed 2026-10-27: issue/valid/expire are 12-digit
  // YYYYMMDDHHmm strings; GIS ingest times are epoch-millisecond strings.
  // Never confuse either with browser retrieval time.
  if (/^\d{13}$/.test(s)) {
    const ms = Number(s);
    const d = new Date(ms);
    return Number.isNaN(d.getTime()) ? null : d.toISOString();
  }
  const compact = /^(\d{4})(\d{2})(\d{2})[_ ]?(\d{2})(\d{2})(\d{2})?$/.exec(s);
  const utcText = /^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}(?::\d{2})?)$/.exec(s);
  if (compact) {
    const year=Number(compact[1]),month=Number(compact[2]),day=Number(compact[3]);
    const hour=Number(compact[4]),minute=Number(compact[5]),second=Number(compact[6]??'0');
    const d = new Date(Date.UTC(year,month-1,day,hour,minute,second));
    if (d.getUTCFullYear()!==year || d.getUTCMonth()+1!==month || d.getUTCDate()!==day ||
        d.getUTCHours()!==hour || d.getUTCMinutes()!==minute || d.getUTCSeconds()!==second) return null;
    return d.toISOString();
  }
  const canonical = utcText ? utcText[1]+'T'+utcText[2]+'Z' : s;
  if (!/(Z|[+-]\d{2}:\d{2})$/i.test(canonical)) return null;
  const d = new Date(canonical);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}
export interface ProductTimes {
  issued: string | null;
  valid: string | null;
  expires: string | null;
  gisIngested: string | null;
  gisFiledate: string | null;
}
export interface OutlookData {
  geometry: AreaCollection;
  times: ProductTimes;
  sourceFile: string | null;
  expectedFeatureCount: number | null;
}
export interface WarningRecord {
  id: string;
  event: 'Tornado Warning' | 'Severe Thunderstorm Warning';
  sent: string | null;
  effective: string | null;
  onset: string | null;
  expires: string | null;
  ends: string | null;
  headline: string | null;
  sourceUrl: string | null;
  mapped: boolean;
}
export interface AlertData {
  geometry: AreaCollection;
  missingGeometryCount: number;
  totalMatchingCount: number;
  newestSent: string | null;
  records: WarningRecord[];
}

const timeFields = ['issue','valid','expire','idp_ingestdate','idp_filedate'] as const;
export function normalizeOutlook(payload: unknown, expectedFeatureCount: number | null = null): OutlookData {
  const items = featureList(payload);
  if (expectedFeatureCount !== null && items.length !== expectedFeatureCount) {
    throw new Error('Incomplete SPC outlook: expected '+expectedFeatureCount+' features, received '+items.length+'.');
  }
  if (items.length && !items.every(areaFeature)) throw new Error('SPC returned malformed or unmappable polygons.');
  const features = items as AreaFeature[];
  const source = features.length ? props(features[0]) : {};
  for (const f of features) {
    const p = props(f);
    const dn = p.dn;
    if (typeof dn !== 'number' || !Number.isInteger(dn) || !Object.hasOwn(SPC_CATEGORIES, dn)) {
      throw new Error('Unknown SPC categorical dn value: '+String(dn));
    }
    for (const key of timeFields) {
      const a = parseSourceTime(source[key]), b = parseSourceTime(p[key]);
      if (a !== b) throw new Error('Mixed or missing SPC '+key+' timestamps across polygons.');
    }
    if (p.idp_source !== source.idp_source) {
      throw new Error('Mixed SPC source revisions across polygons.');
    }
  }
  const times: ProductTimes = {
    issued: parseSourceTime(source.issue),
    valid: parseSourceTime(source.valid),
    expires: parseSourceTime(source.expire),
    gisIngested: parseSourceTime(source.idp_ingestdate),
    gisFiledate: parseSourceTime(source.idp_filedate)
  };
  if (features.length && (!times.valid || !times.expires)) {
    throw new Error('SPC outlook valid/expiration metadata missing or invalid.');
  }
  if (times.valid && times.expires && times.valid >= times.expires) {
    throw new Error('SPC outlook validity interval is reversed.');
  }
  return {
    geometry: {type:'FeatureCollection', features}, times,
    sourceFile: typeof source.idp_source === 'string' ? source.idp_source : null,
    expectedFeatureCount
  };
}

const warningEvents = new Set(['Tornado Warning','Severe Thunderstorm Warning']);
function warningId(f: Record<string,unknown>, p: Record<string,unknown>): string | null {
  const value = (typeof f.id === 'string' && f.id) || (typeof p.id === 'string' && p.id) || null;
  return value;
}
export function normalizeAlerts(payload: unknown): AlertData {
  const raw = featureList(payload);
  const unique = new Map<string,{feature:unknown; props:Record<string,unknown>}>();
  for (const item of raw) {
    const p = props(item);
    if (!warningEvents.has(p.event as string)) continue;
    if (!record(item)) throw new Error('Malformed warning entry.');
    const id = warningId(item,p);
    if (!id) throw new Error('NWS warning is missing a stable identifier.');
    const prior = unique.get(id);
    const sent = parseSourceTime(p.sent);
    if (!prior || (sent??'') > (parseSourceTime(prior.props.sent)??'')) unique.set(id,{feature:item,props:p});
  }
  const polygons: AreaFeature[] = [], records: WarningRecord[] = [];
  for (const [id,{feature,props:p}] of unique) {
    const mapped = areaFeature(feature);
    if (record(feature) && feature.geometry !== null && !mapped) {
      throw new Error('NWS warning '+id+' has invalid polygon coordinates.');
    }
    if (mapped) polygons.push(feature as AreaFeature);
    records.push({
      id, event:p.event as WarningRecord['event'], mapped,
      sent:parseSourceTime(p.sent), effective:parseSourceTime(p.effective),
      onset:parseSourceTime(p.onset), expires:parseSourceTime(p.expires),
      ends:parseSourceTime(p.ends),
      headline:typeof p.headline==='string'?p.headline:null,
      sourceUrl:id.startsWith('https://')?id:null
    });
  }
  const sent = records.map(r=>r.sent).filter((x):x is string=>x!==null).sort();
  return {geometry:{type:'FeatureCollection',features:polygons},
    missingGeometryCount:records.length-polygons.length,
    totalMatchingCount:records.length,newestSent:sent.at(-1)??null,records};
}
export function isExpired(expires:string|null, now=Date.now()):boolean {
  return expires!==null && Date.parse(expires)<=now;
}
export function isRetrievalStale(at:string|null,now=Date.now(),maxAgeMs=15*60_000):boolean {
  return at===null || !Number.isFinite(Date.parse(at)) || now-Date.parse(at)>maxAgeMs;
}
export function isOutlookExpiredOrUnknown(data:OutlookData|null,now=Date.now()):boolean {
  return !data || !data.times.expires || isExpired(data.times.expires,now);
}
export function activeWarningGeometry(data:AlertData|null,now=Date.now()):AreaCollection {
  if (!data) return emptyCollection();
  const eligible = new Set(data.records.filter(r=>{
    const end = r.ends && r.expires ? (r.ends<r.expires?r.ends:r.expires) : r.ends ?? r.expires;
    return end === null || !isExpired(end,now);
  }).map(r=>r.id));
  return {type:'FeatureCollection',
    features:data.geometry.features.filter(f=>record(f) && (
      (typeof f.id==='string' && eligible.has(f.id)) ||
      (record(f.properties) && typeof f.properties.id==='string' && eligible.has(f.properties.id))
    ))};
}
const SPC_URL='https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer/1/query';
export function spcUrl():string {
  return SPC_URL+'?'+new URLSearchParams({where:'1=1',outFields:'*',returnGeometry:'true',outSR:'4326',f:'geojson'});
}
export function spcCountUrl():string {
  return SPC_URL+'?'+new URLSearchParams({where:'1=1',returnCountOnly:'true',f:'json'});
}
export function alertUrl(event:WarningRecord['event']):string {
  return 'https://api.weather.gov/alerts/active?'+new URLSearchParams({event});
}
// Two short bounded retries for transient NOAA network/CORS/5xx failures.
// Persistent CORS problems still fail visibly; this is not an alert-delivery service.
function abortablePause(ms:number,signal:AbortSignal):Promise<void> {
  return new Promise((resolve,reject)=>{
    if(signal.aborted) {reject(signal.reason??new DOMException('Aborted','AbortError'));return;}
    const stop=()=>{clearTimeout(timer);reject(signal.reason??new DOMException('Aborted','AbortError'));};
    const timer=setTimeout(()=>{signal.removeEventListener('abort',stop);resolve();},ms);
    signal.addEventListener('abort',stop,{once:true});
  });
}
async function fetchJSON(url:string,signal:AbortSignal,accept:string):Promise<unknown> {
  for(let attempt=0;attempt<3;attempt++){
    try {
      const response=await fetch(url,{headers:{Accept:accept},cache:'no-cache',signal});
      if(!response.ok) {
        if(![429,500,502,503,504].includes(response.status)||attempt===2){
          throw new Error('HTTP '+response.status+' from '+new URL(url).host);
        }
      } else return response.json() as Promise<unknown>;
    } catch(error) {
      if(signal.aborted || attempt===2) throw error;
      if(error instanceof Error && error.message.startsWith('HTTP ')) throw error;
    }
    await abortablePause(attempt===0?350:1200,signal);
  }
  throw new Error('Exhausted NOAA source retries.');
}
export async function fetchOutlook(signal:AbortSignal):Promise<OutlookData> {
  const [payload,countResponse]=await Promise.all([
    fetchJSON(spcUrl(),signal,'application/geo+json'),
    fetchJSON(spcCountUrl(),signal,'application/json')
  ]);
  if (!record(countResponse) || typeof countResponse.count!=='number' ||
      !Number.isInteger(countResponse.count) || countResponse.count<0) {
    throw new Error('SPC count request failed or returned invalid data.');
  }
  return normalizeOutlook(payload,countResponse.count);
}
export async function fetchAlerts(signal:AbortSignal):Promise<AlertData> {
  // An independently filtered single-event call avoids relying on undocumented comma list semantics.
  const [tor,svr]=await Promise.all([
    fetchJSON(alertUrl('Tornado Warning'),signal,'application/geo+json'),
    fetchJSON(alertUrl('Severe Thunderstorm Warning'),signal,'application/geo+json')
  ]);
  return normalizeAlerts({type:'FeatureCollection',features:[...featureList(tor),...featureList(svr)]});
}
