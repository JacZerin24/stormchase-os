/** Historical HRRR severe-convective map assets, never live radar/nowcasting. */
export const CONV_ARCHIVE_PATH='pilot/hrrr-convective-20261027-20z/';
export const CONV_DISPLAY={
 refc_f03:{title:'Simulated composite reflectivity',unit:'dB (model)',kind:'forecast instantaneous',notice:'Simulated radar appearance; NOT observed radar'},
 uh25_max_f03:{title:'2–5 km UH · hourly maximum',unit:'m²/s² per NOAA catalog',kind:'19–20Z forecast max',notice:'Not a tornado probability; ecCodes GRIB unit label is unresolved'},
 uh25_swath_3h:{title:'2–5 km UH · 3-hour max swath',unit:'m²/s² per NOAA catalog',kind:'17–20Z forecast maximum',notice:'Not an individual storm track or observed tornado path'},
 hgt500_f03:{title:'500-hPa geopotential height',unit:'gpm',kind:'20Z model forecast',notice:'Shaded height field; contours and wind vectors remain future work'},
 t700_f03:{title:'700-hPa temperature',unit:'K (source)',kind:'20Z model forecast',notice:'Model temperature, not observed sounding data'},
 cape_sb_f03:{title:'Surface-based CAPE',unit:'J/kg',kind:'20Z model forecast',notice:'Model parcel diagnostic, not initiation probability'},
 srh01_f03:{title:'0–1 km storm-relative helicity',unit:'m²/s²',kind:'20Z model forecast',notice:'Model-provided storm motion; not independently derived effective-layer SRH'}
} as const;
export type ConvDisplayKey=keyof typeof CONV_DISPLAY;
export type ConvectiveProduct={
 field:string;runAt?:string;validAt?:string;leadHours?:number;
 png?:string;pngSHA256?:string;sourceSHA256?:string;
 intervalStartAt?:string|null;intervalEndAt?:string|null;
 sourceHours?:number[]; minValue:number;maxValue:number;
 gribMetadata?:{units:string;stepType:string};
 geographicQA?:{matchingCoverageFraction:number;maximumNativeDistanceKm:number};
};
export type ConvectiveManifest={
 schema:'stormchase-convective-archived-model/1';
 status:'experimental_historical_not_current';runAt:'2026-10-27T17:00:00Z';
 finalValidAt:'2026-10-27T20:00:00Z';model:'HRRR';
 crs:'EPSG:4326';bounds:[number,number,number,number];
 displayOrder:ConvDisplayKey[];
 fieldProducts:Record<string,ConvectiveProduct>;
 observedRadar:false;observedStormTrack:false;calibratedTornadoProbability:false;
 independentForecastVerification:'not performed';
};
const sha=(x:unknown):x is string=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const png=(x:unknown):x is string=>typeof x==='string'&&/^[a-z0-9_-]+\.png$/.test(x);
const object=(x:unknown):x is Record<string,unknown>=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const EXPECTED=Object.keys(CONV_DISPLAY).sort();
export function parseConvectiveManifest(value:unknown):ConvectiveManifest{
 if(!object(value)||value.schema!=='stormchase-convective-archived-model/1'||
    value.status!=='experimental_historical_not_current'||value.model!=='HRRR'||
    value.runAt!=='2026-10-27T17:00:00Z'||value.finalValidAt!=='2026-10-27T20:00:00Z'||
    value.crs!=='EPSG:4326'||value.observedRadar!==false||
    value.observedStormTrack!==false||value.calibratedTornadoProbability!==false||
    value.independentForecastVerification!=='not performed')
  throw new Error('Untrusted or current-pretending HRRR convective archive');
 if(!Array.isArray(value.bounds)||value.bounds.length!==4||!value.bounds.every(x=>typeof x==='number'&&Number.isFinite(x)))
  throw new Error('Invalid archive geographic bounds');
 const [w,s,e,n]=value.bounds;
 if(w!==-103||s!==33||e!==-94||n!==39.4)throw new Error('Unrecognized georeferencing bounds');
 if(!Array.isArray(value.displayOrder)||[...value.displayOrder].sort().join('|')!==EXPECTED.join('|'))
  throw new Error('Missing or unexpected archived model display products');
 if(!object(value.fieldProducts))throw new Error('Missing source provenance table');
 const required=[...EXPECTED,'uh25_max_f01','uh25_max_f02'];
 for(const key of required){
  const p=value.fieldProducts[key];
  if(!object(p)||typeof p.minValue!=='number'||typeof p.maxValue!=='number'||
     !Number.isFinite(p.minValue)||!Number.isFinite(p.maxValue)||p.minValue>p.maxValue)
   throw new Error('Incomplete archived field '+key);
  if(key==='uh25_swath_3h'){
   if(!Array.isArray(p.sourceHours)||p.sourceHours.join(',')!=='1,2,3'||
      p.intervalStartAt!=='2026-10-27T17:00:00Z'||p.intervalEndAt!=='2026-10-27T20:00:00Z')
    throw new Error('Invalid contiguous forecast UH swath');
  }else {
   const lead=Number(key.slice(-1));
   if(p.runAt!==value.runAt||p.leadHours!==lead||
      p.validAt!==new Date(Date.parse(value.runAt)+lead*3600_000).toISOString().replace('.000Z','Z')||
      !sha(p.sourceSHA256))
    throw new Error('GRIB cycle/lead/valid identity not verified: '+key);
   if(key.startsWith('uh25_') && (
      p.intervalStartAt!==new Date(Date.parse(value.runAt)+(lead-1)*3600_000).toISOString().replace('.000Z','Z')||
      p.intervalEndAt!==p.validAt||p.gribMetadata?.stepType!=='max'))
    throw new Error('Missing UH interval semantics');
   const q=p.geographicQA;
   if(!object(q)||typeof q.matchingCoverageFraction!=='number'||q.matchingCoverageFraction<.97||
      typeof q.maximumNativeDistanceKm!=='number'||q.maximumNativeDistanceKm>5.01)
    throw new Error('Unverified GRIB geographic registration');
  }
  if(EXPECTED.includes(key) && (!png(p.png)||!sha(p.pngSHA256)))
   throw new Error('Archive map image integrity missing');
 }
 return value as unknown as ConvectiveManifest;
}
export function convectiveImage(m:ConvectiveManifest,key:ConvDisplayKey,base:string){
 if(!(key in CONV_DISPLAY)||!base.endsWith('/'))throw new Error('Unknown model image request');
 const file=m.fieldProducts[key].png;
 if(!png(file))throw new Error('Missing safe PNG');
 return {url:base+file,bounds:m.bounds,kind:'convective' as const};
}
