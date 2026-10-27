/** Immutable, real-data ARCHIVED geospatial pilot; never a live forecast. */
export const HRRR_PILOT_PATH='pilot/hrrr-20261027-18z/';
export type PilotMode='earlier'|'later'|'difference';
export interface PilotProduct {
  model:'HRRR';
  parameter:'TMP';
  level:'2 m above ground';
  units:'K';
  runAt:string;
  leadHours:number;
  validAt:string;
  image:string;
  cog:string;
  grib_sha256:string;
  image_sha256:string;
  cog_sha256:string;
  geolocation_QA:{coverage_fraction:number;max_nearest_km:number;unmatched_cells:number};
  min_K:number;
  max_K:number;
}
export interface PilotManifest {
  schema:'stormchase-hrrr-archived-pilot/1';
  status:'historical-experimental-display-not-live';
  validAt:string;
  bounds:[number,number,number,number];
  rasterCrs:'EPSG:4326';
  products:[PilotProduct,PilotProduct];
  differenceImage:string;
  difference_sha256:string;
}
export interface PilotOverlay {url:string;bounds:[number,number,number,number];kind:PilotMode|'convective'}
function object(x:unknown):x is Record<string,unknown>{
  return typeof x==='object'&&x!==null&&!Array.isArray(x);
}
function sha(x:unknown):x is string {return typeof x==='string'&&/^[a-f0-9]{64}$/.test(x)}
function image(x:unknown):x is string {return typeof x==='string'&&/^[a-z0-9_-]+\.png$/.test(x)}
function iso(x:unknown):x is string {
  return typeof x==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(x)&&
    Number.isFinite(Date.parse(x))&&new Date(x).toISOString().replace('.000','')===x;
}
export function parsePilotManifest(raw:unknown):PilotManifest {
  if(!object(raw)||raw.schema!=='stormchase-hrrr-archived-pilot/1'||
     raw.status!=='historical-experimental-display-not-live'||
     raw.rasterCrs!=='EPSG:4326'||!iso(raw.validAt))
    throw new Error('Unsupported or incomplete archived HRRR pilot metadata');
  if(!Array.isArray(raw.bounds)||raw.bounds.length!==4||
     !raw.bounds.every(x=>typeof x==='number'&&Number.isFinite(x)))
    throw new Error('Invalid archive geographic bounds');
  const [west,south,east,north]=raw.bounds as number[];
  if(!(-180<=west&&west<east&&east<=180&&-90<=south&&south<north&&north<=90))
    throw new Error('Invalid archive geodetic bounds');
  if(!Array.isArray(raw.products)||raw.products.length!==2)throw new Error('Exactly two forecast cycles required');
  if(!image(raw.differenceImage)||!sha(raw.difference_sha256))throw new Error('Missing hashed difference image');
  for(const p of raw.products){
    if(!object(p)||p.model!=='HRRR'||p.parameter!=='TMP'||p.level!=='2 m above ground'||p.units!=='K'||
       !iso(p.runAt)||!iso(p.validAt)||p.validAt!==raw.validAt||
       typeof p.leadHours!=='number'||!Number.isInteger(p.leadHours)||
       p.leadHours<0||p.leadHours>48||
       Date.parse(p.runAt)+p.leadHours*3600_000!==Date.parse(p.validAt)||
       !image(p.image)||!sha(p.grib_sha256)||!sha(p.image_sha256)||!sha(p.cog_sha256)||
       typeof p.cog!=='string'||!/^[a-z0-9_-]+\.tif$/.test(p.cog)||
       !object(p.geolocation_QA)||
       typeof p.geolocation_QA.coverage_fraction!=='number'||p.geolocation_QA.coverage_fraction<0.97||
       typeof p.geolocation_QA.max_nearest_km!=='number'||p.geolocation_QA.max_nearest_km>5.001||
       typeof p.min_K!=='number'||typeof p.max_K!=='number'||p.min_K>p.max_K)
      throw new Error('Archived forecast cycle failed run/valid/geolocation provenance contract');
  }
  if(raw.products[0].runAt===raw.products[1].runAt||
     raw.products[0].leadHours===raw.products[1].leadHours)
    throw new Error('Cycles must have distinct initializations and leads');
  if(raw.validAt!=='2026-10-27T18:00:00Z')
    throw new Error('Unexpected archived pilot forecast valid time');
  return raw as unknown as PilotManifest;
}
export function pilotOverlay(manifest:PilotManifest,mode:PilotMode,base:string):PilotOverlay{
  if(!base.endsWith('/'))throw new Error('Asset base must end in slash');
  const products=[...manifest.products].sort((a,b)=>a.runAt.localeCompare(b.runAt));
  const name=mode==='difference'?manifest.differenceImage:
    (mode==='earlier'?products[0]:products[1]).image;
  return {url:base+name,bounds:manifest.bounds,kind:mode};
}
