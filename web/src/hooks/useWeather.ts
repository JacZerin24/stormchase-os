import { useCallback, useEffect, useRef, useState } from 'react';
import {fetchAlerts,fetchOutlook,type AlertData,type OutlookData,type SPCDay} from '../data/weather';

export interface FeedState<T> {
  data: T | null;
  state: 'loading' | 'ready' | 'error';
  lastSuccess: string | null;
  lastAttempt: string | null;
  error: string | null;
}
const initial = <T,>(): FeedState<T> => ({data:null,state:'loading',lastSuccess:null,lastAttempt:null,error:null});

export function useWeather() {
  const [outlook, setOutlook] = useState<FeedState<OutlookData>>(initial);
  const [day,setSelectedDay] = useState<SPCDay>(1);
  const setDay=useCallback((next:SPCDay)=>{
    setOutlook(initial<OutlookData>());
    setSelectedDay(next);
  },[]);
  const [alerts, setAlerts] = useState<FeedState<AlertData>>(initial);
  const controller = useRef<AbortController | null>(null);
  const refresh = useCallback(() => {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    const attempted = new Date().toISOString();
    setOutlook(prev=>({...prev,lastAttempt:attempted,state:'loading'}));
    setAlerts(prev=>({...prev,lastAttempt:attempted}));
    void fetchOutlook(request.signal,day).then(data => {
      if (!request.signal.aborted) setOutlook(prev=>({...prev,data,state:'ready',lastSuccess:new Date().toISOString(),error:null}));
    }).catch((error: unknown) => {
      if (!request.signal.aborted) setOutlook(prev => ({...prev,state:'error',error:error instanceof Error ? error.message:'Unknown fetch error'}));
    });
    void fetchAlerts(request.signal).then(data => {
      if (!request.signal.aborted) setAlerts(prev=>({...prev,data,state:'ready',lastSuccess:new Date().toISOString(),error:null}));
    }).catch((error: unknown) => {
      if (!request.signal.aborted) setAlerts(prev => ({...prev,state:'error',error:error instanceof Error ? error.message:'Unknown fetch error'}));
    });
  }, [day]);
  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh,300000);
    return () => {window.clearInterval(interval);controller.current?.abort();};
  },[refresh]);
  return {outlook,alerts,refresh,day,setDay};
}
