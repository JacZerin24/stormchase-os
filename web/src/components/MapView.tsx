import { useEffect, useRef, useState } from 'react';
import maplibregl, { type Map as MapInstance, type GeoJSONSource } from 'maplibre-gl';
import { emptyCollection, SPC_CATEGORIES, type AreaCollection } from '../data/weather';
import { REGION_BOUNDS, type RegionKey } from '../data/regions';
import { basemapStyle, type DisplayTheme } from '../theme';
import type {PilotOverlay} from '../data/hrrrPilot';

type Props = {
  outlook: AreaCollection | null;
  warnings: AreaCollection | null;
  showOutlook: boolean;
  showWarnings: boolean;
  onCoordinates: (value:string)=>void;
  focus: { region: RegionKey; revision: number };
  outlookOpacity: number;
  theme: DisplayTheme;
  pilotImage: PilotOverlay | null;
  pilotFocusRevision: number;
};
const categoryColor = ['match',['get','dn'],2,'#c1e9c1',3,'#66a366',4,'#ffe066',5,'#ffa366',6,'#e06666',8,'#ee99ee','#96a8b8'] as any;
const warningColor = ['match',['get','event'],'Tornado Warning','#fb4b69','Severe Thunderstorm Warning','#ffb04d','#cedbe2'] as any;

export default function MapView({outlook,warnings,showOutlook,showWarnings,onCoordinates,focus,outlookOpacity,theme,pilotImage,pilotFocusRevision}:Props) {
  const element = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapInstance | null>(null);
  const [styleEpoch,setStyleEpoch] = useState(0);
  const appliedTheme = useRef(theme);
  const [mapError,setMapError] = useState<string | null>(null);
  useEffect(() => {
    if (!element.current) return;
    const map = new maplibregl.Map({
      container:element.current,style:basemapStyle(appliedTheme.current),
      center:[-97.5,38],zoom:3.4,minZoom:2,maxZoom:14
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(),'bottom-right');
    const update = () => {const c=map.getCenter();onCoordinates(`${c.lat.toFixed(2)}°N · ${Math.abs(c.lng).toFixed(2)}°${c.lng<0?'W':'E'}`);};
    map.on('moveend',update);
    update();
    map.on('error',()=>setMapError('Map style or tiles failed to load. Check the network connection.'));
    // Register click handlers once: theme switches should never duplicate popups.
    map.on('click','spc-fill',(e)=>{
      const dn=Number(e.features?.[0]?.properties?.dn);
      new maplibregl.Popup().setLngLat(e.lngLat).setText('SPC Day 1 · '+(SPC_CATEGORIES[dn]?.label??'Category unknown')).addTo(map);
    });
    map.on('click','warning-fill',(e)=>{
      const p=e.features?.[0]?.properties;
      new maplibregl.Popup().setLngLat(e.lngLat).setText(String(p?.headline??p?.event??'NWS warning')).addTo(map);
    });
    // style.load fires after the initial load and every light/dark basemap change.
    // Recreate custom overlays because MapLibre setStyle replaces style sources/layers.
    map.on('style.load',()=>{
      map.addSource('spc-day1',{type:'geojson',data:emptyCollection()});
      map.addSource('nws-warnings',{type:'geojson',data:emptyCollection()});
      map.addLayer({id:'spc-fill',type:'fill',source:'spc-day1',layout:{'fill-sort-key':['get','dn']},paint:{'fill-color':categoryColor,'fill-opacity':0.28}});
      map.addLayer({id:'spc-line',type:'line',source:'spc-day1',layout:{'line-sort-key':['get','dn']},paint:{'line-color':categoryColor,'line-width':1.5}});
      map.addLayer({id:'warning-fill',type:'fill',source:'nws-warnings',paint:{'fill-color':warningColor,'fill-opacity':0.28}});
      map.addLayer({id:'warning-line',type:'line',source:'nws-warnings',paint:{'line-color':warningColor,'line-width':2.4}});
      setStyleEpoch(epoch => epoch + 1);
    });
    return () => { mapRef.current=null;map.remove(); };
  },[onCoordinates]);
  useEffect(()=>{
    const m=mapRef.current;
    if (styleEpoch && m) (m.getSource('spc-day1') as GeoJSONSource | undefined)?.setData(outlook??emptyCollection());
  },[styleEpoch,outlook]);
  useEffect(()=>{
    const m=mapRef.current;
    if (styleEpoch && m) (m.getSource('nws-warnings') as GeoJSONSource | undefined)?.setData(warnings??emptyCollection());
  },[styleEpoch,warnings]);
  useEffect(()=>{
    const map=mapRef.current;
    if(!styleEpoch||!map)return;
    // Remove old raster first. A theme change destroys style sources, so
    // re-add on every style epoch. Keep SPC/NWS vector data ABOVE this image.
    if(map.getLayer('hrrr-archived-image'))map.removeLayer('hrrr-archived-image');
    if(map.getSource('hrrr-archived-source'))map.removeSource('hrrr-archived-source');
    if(!pilotImage)return;
    const [west,south,east,north]=pilotImage.bounds;
    map.addSource('hrrr-archived-source',{type:'image',url:pilotImage.url,
      coordinates:[[west,north],[east,north],[east,south],[west,south]]});
    map.addLayer({id:'hrrr-archived-image',type:'raster',source:'hrrr-archived-source',
      paint:{'raster-opacity':0.82,'raster-fade-duration':0}},
      map.getLayer('spc-fill')?'spc-fill':undefined);
  },[styleEpoch,pilotImage?.url,pilotImage?.bounds,pilotImage]);
  useEffect(()=>{
    const map=mapRef.current;
    if(!pilotFocusRevision||!pilotImage||!styleEpoch||!map)return;
    const [west,south,east,north]=pilotImage.bounds;
    map.fitBounds([[west,south],[east,north]],{padding:32,maxZoom:8,
      duration:window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:450});
  },[pilotFocusRevision,styleEpoch,pilotImage?.bounds]);
  useEffect(()=>{
    const m=mapRef.current;
    if (!styleEpoch||!m) return;
    for (const id of ['spc-fill','spc-line']) if (m.getLayer(id)) m.setLayoutProperty(id,'visibility',showOutlook?'visible':'none');
    for (const id of ['warning-fill','warning-line']) if (m.getLayer(id)) m.setLayoutProperty(id,'visibility',showWarnings?'visible':'none');
  },[styleEpoch,showOutlook,showWarnings]);
  useEffect(()=>{
    const m=mapRef.current;
    if (styleEpoch && m?.getLayer('spc-fill')) m.setPaintProperty('spc-fill','fill-opacity',outlookOpacity);
  },[styleEpoch,outlookOpacity]);
  const mapReady = styleEpoch > 0;
  useEffect(()=>{
    const m=mapRef.current;
    if (mapReady && m) m.fitBounds(REGION_BOUNDS[focus.region], {padding:36,duration:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 450,maxZoom:7});
    // A basemap switch does not change the user-selected extent or zoom.
  },[mapReady,focus]);
  useEffect(() => {
    if (appliedTheme.current === theme) return;
    appliedTheme.current = theme;
    setMapError(null);
    mapRef.current?.setStyle(basemapStyle(theme));
  }, [theme]);
  return <div className="map-host">
    <div ref={element} className="map-canvas" role="application" aria-label="Interactive CONUS weather map" />
    {mapError&&<div className="map-error" role="status">{mapError}</div>}
  </div>;
}
