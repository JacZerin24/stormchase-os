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
export const emptyCollection = (): AreaCollection => ({ type: 'FeatureCollection', features: [] });

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function areaFeature(value: unknown): value is AreaFeature {
  return record(value) && value.type === 'Feature' && record(value.geometry)
    && (value.geometry.type === 'Polygon' || value.geometry.type === 'MultiPolygon')
    && Array.isArray(value.geometry.coordinates);
}
function featureList(value: unknown): unknown[] {
  if (!record(value) || value.type !== 'FeatureCollection' || !Array.isArray(value.features)) {
    throw new Error('Provider response is not a GeoJSON FeatureCollection.');
  }
  return value.features;
}
function props(feature: AreaFeature): Record<string, unknown> {
  return record(feature.properties) ? feature.properties : {};
}
export function parseSourceTime(value: unknown): string | null {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return null;
    const stamp = new Date(value);
    return Number.isNaN(stamp.getTime()) ? null : stamp.toISOString();
  }
  if (typeof value !== 'string' || !value.trim()) return null;
  const raw = value.trim();
  const compact = raw.match(/^(\d{4})(\d{2})(\d{2})[_ ](\d{2})(\d{2})$/);
  let candidate = raw;
  if (compact) candidate = `${compact[1]}-${compact[2]}-${compact[3]}T${compact[4]}:${compact[5]}:00Z`;
  else if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?$/.test(raw)) {
    candidate = raw.replace(' ', 'T') + 'Z';
  }
  const stamp = new Date(candidate);
  return Number.isNaN(stamp.getTime()) ? null : stamp.toISOString();
}
export interface ProductTimes {
  issued: string | null;
  valid: string | null;
  expires: string | null;
  gisIngested: string | null;
}
export interface OutlookData { geometry: AreaCollection; times: ProductTimes; sourceFile: string | null }
export interface AlertData { geometry: AreaCollection; missingGeometryCount: number; totalMatchingCount: number; newestSent: string | null }

export function normalizeOutlook(payload: unknown): OutlookData {
  const features = featureList(payload).filter((f): f is AreaFeature =>
    areaFeature(f) && typeof props(f).dn === 'number' && Object.hasOwn(SPC_CATEGORIES, String(props(f).dn))
  );
  const head = features[0] ? props(features[0]) : {};
  return {
    geometry: { type: 'FeatureCollection', features },
    times: {
      issued: parseSourceTime(head.issue),
      valid: parseSourceTime(head.valid),
      expires: parseSourceTime(head.expire),
      gisIngested: parseSourceTime(head.idp_ingestdate)
    },
    sourceFile: typeof head.idp_source === 'string' ? head.idp_source : null
  };
}
const WARNING_EVENTS = new Set(['Tornado Warning', 'Severe Thunderstorm Warning']);
export function normalizeAlerts(payload: unknown): AlertData {
  const features = featureList(payload).filter((f): f is AreaFeature =>
    record(f) && record(f.properties) && WARNING_EVENTS.has(String(f.properties.event))
  );
  const polygonFeatures = features.filter(areaFeature);
  const sent = features
    .map((f) => record(f.properties) ? parseSourceTime(f.properties.sent) : null)
    .filter((v): v is string => v !== null)
    .sort();
  return {
    geometry: { type: 'FeatureCollection', features: polygonFeatures },
    totalMatchingCount: features.length,
    missingGeometryCount: features.length - polygonFeatures.length,
    newestSent: sent.at(-1) ?? null
  };
}
export function isExpired(expires: string | null, now = Date.now()): boolean {
  return expires !== null && Date.parse(expires) < now;
}
export function isRetrievalStale(at: string | null, now = Date.now(), maxAgeMs = 15 * 60_000): boolean {
  return at !== null && now - Date.parse(at) > maxAgeMs;
}
export function spcUrl(): string {
  const params = new URLSearchParams({where:'1=1',outFields:'*',returnGeometry:'true',outSR:'4326',f:'geojson'});
  return `https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/FeatureServer/1/query?${params.toString()}`;
}
export function alertUrl(): string {
  return `https://api.weather.gov/alerts/active?event=${encodeURIComponent('Tornado Warning,Severe Thunderstorm Warning')}`;
}
async function fetchGeoJSON(url: string, signal: AbortSignal): Promise<unknown> {
  const response = await fetch(url, { headers: { Accept: 'application/geo+json' }, cache: 'no-cache', signal });
  if (!response.ok) throw new Error(`HTTP ${response.status} from source`);
  return response.json() as Promise<unknown>;
}
export async function fetchOutlook(signal: AbortSignal): Promise<OutlookData> {
  return normalizeOutlook(await fetchGeoJSON(spcUrl(), signal));
}
export async function fetchAlerts(signal: AbortSignal): Promise<AlertData> {
  return normalizeAlerts(await fetchGeoJSON(alertUrl(), signal));
}
