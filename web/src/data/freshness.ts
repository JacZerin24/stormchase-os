import type {FeedState} from '../hooks/useWeather';
import type {OutlookData,AlertData} from './weather';
import {isOutlookExpiredOrUnknown,isRetrievalStale,activeWarningGeometry} from './weather';
export type WeatherStatus='loading'|'available'|'partial'|'expired'|'stale'|'error';
export interface WeatherHealth {state:WeatherStatus;label:string;render:boolean;explanation:string|null}
export function outlookHealth(feed:FeedState<OutlookData>,now=Date.now()):WeatherHealth {
  if(feed.state==='loading')return {state:'loading',label:'CONNECTING',render:false,explanation:null};
  if(feed.state==='error')return {state:'error',label:'SOURCE ERROR',render:false,explanation:feed.error};
  if(!feed.lastSuccess||!feed.data||isRetrievalStale(feed.lastSuccess,now))
    return {state:'stale',label:'RETRIEVAL STALE',render:false,explanation:'Latest successful download missing or older than 15 minutes.'};
  if(isOutlookExpiredOrUnknown(feed.data,now))
    return {state:'expired',label:'EXPIRED PRODUCT',render:false,explanation:'SPC product expiration is missing or already past.'};
  if(!feed.data.times.issued||!feed.data.times.gisIngested)
    return {state:'partial',label:'PARTIAL METADATA',render:true,explanation:'Source issuance or GIS ingestion time is unavailable.'};
  return {state:'available',label:'RETRIEVED',render:true,explanation:null};
}
export function warningHealth(feed:FeedState<AlertData>,now=Date.now()):WeatherHealth {
  if(feed.state==='loading')return {state:'loading',label:'CONNECTING',render:false,explanation:null};
  if(feed.state==='error')return {state:'error',label:'SOURCE ERROR',render:false,explanation:feed.error};
  if(!feed.lastSuccess||!feed.data||isRetrievalStale(feed.lastSuccess,now))
    return {state:'stale',label:'RETRIEVAL STALE',render:false,explanation:'Latest successful download missing or older than 15 minutes.'};
  if(feed.data.missingGeometryCount>0)
    return {state:'partial',label:'PARTIAL WARNING MAP',render:true,explanation:feed.data.missingGeometryCount+' alert(s) have no mappable polygon.'};
  if(activeWarningGeometry(feed.data,now).features.length<feed.data.geometry.features.length)
    return {state:'partial',label:'EXPIRED POLYGONS HIDDEN',render:true,explanation:'Some warnings expired after the last retrieval.'};
  return {state:'available',label:'RETRIEVED',render:true,explanation:null};
}
