import {describe,it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {CONV_ARCHIVE_PATH,CONV_DISPLAY,parseConvectiveManifest,convectiveImage} from './hrrrConvective';
function original(){
 const root=new URL('../../public/'+CONV_ARCHIVE_PATH,import.meta.url);
 const bytes=readFileSync(new URL('manifest.json',root),'utf8');
 return {root,value:JSON.parse(bytes) as unknown};
}
describe('authentic archived NOAA HRRR convective imagery',()=>{
 it('verifies shipped manifest and exact SHA256 of every real GRIB-derived PNG',()=>{
  const {root,value}=original();
  const m=parseConvectiveManifest(value);
  for(const key of m.displayOrder){
   const p=m.fieldProducts[key];
   const actual=createHash('sha256').update(readFileSync(new URL(p.png!,root))).digest('hex');
   expect(actual).toBe(p.pngSHA256);
   expect(convectiveImage(m,key,import.meta.env?.BASE_URL??'/').url.endsWith(p.png!)).toBe(true);
  }
  expect(m.fieldProducts.uh25_max_f03.gribMetadata?.stepType).toBe('max');
  expect(m.fieldProducts.uh25_swath_3h.sourceHours).toEqual([1,2,3]);
  expect(m.observedRadar).toBe(false);
  expect(m.observedStormTrack).toBe(false);
 });
 it('rejects altered valid times, fake radar claims, or missing UH hour',()=>{
  const {value}=original();
  const m=value as Record<string,any>;
  expect(()=>parseConvectiveManifest({...m,observedRadar:true})).toThrow();
  expect(()=>parseConvectiveManifest({...m,finalValidAt:'2026-10-27T21:00:00Z'})).toThrow();
  expect(()=>parseConvectiveManifest({...m,fieldProducts:{...m.fieldProducts,uh25_swath_3h:{...m.fieldProducts.uh25_swath_3h,sourceHours:[1,3]}}})).toThrow();
 });
 it('categorizes all seven actual displayed fields without pretending all 69 were decoded',()=>{
  expect(Object.keys(CONV_DISPLAY)).toHaveLength(7);
 });
});
