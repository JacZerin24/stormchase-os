import { useEffect, useState } from 'react';
import MapView from './components/MapView';
import { isExpired, isRetrievalStale, NWS_INFO, SPC_CATEGORIES, SPC_INFO } from './data/weather';
import { useWeather, type FeedState } from './hooks/useWeather';
import { REGION_OPTIONS, type RegionKey } from './data/regions';

function utc(value: string | null | undefined): string {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unavailable' : `${date.toISOString().slice(0,16).replace('T',' ')} UTC`;
}
function Status({ feed, now }: { feed: FeedState<unknown>; now: number }) {
  const isOld = isRetrievalStale(feed.lastSuccess,now);
  const status = feed.state === 'error' ? 'SOURCE ERROR' : isOld ? 'STALE DATA' : feed.state === 'loading' ? 'CONNECTING' : 'RECEIVED';
  return <span className={`feed-status ${feed.state==='error'||isOld?'bad':'good'}`}><span className="status-dot" />{status}</span>;
}
function Toggle({label,enabled,onChange}: {label:string;enabled:boolean;onChange:(v:boolean)=>void}) {
  return <label className="switch"><span className="sr-only">{label}</span><input type="checkbox" checked={enabled} onChange={e=>onChange(e.currentTarget.checked)}/><span className="track" aria-hidden="true"><span /></span></label>;
}
export default function App() {
  const {outlook,alerts,refresh} = useWeather();
  const [showOutlook,setShowOutlook] = useState(true);
  const [showWarnings,setShowWarnings] = useState(true);
  const [outlookOpacity,setOutlookOpacity] = useState(42);
  const [focus,setFocus] = useState<{ region: RegionKey; revision: number }>({region:'conus',revision:0});
  const [sheetOpen,setSheetOpen] = useState(false);
  const focusRegion = (region: RegionKey) => setFocus(previous => ({region, revision:previous.revision+1}));
  const [coords,setCoords] = useState('CONUS INITIAL VIEW');
  const [now,setNow] = useState(Date.now());
  useEffect(()=>{const id=window.setInterval(()=>setNow(Date.now()),60000);return ()=>window.clearInterval(id);},[]);
  const expired = isExpired(outlook.data?.times.expires??null,now);
  const spcOld = isRetrievalStale(outlook.lastSuccess,now);
  const nwsOld = isRetrievalStale(alerts.lastSuccess,now);
  return <div className="shell">
    <aside className="rail" aria-hidden="true"><div className="rail-mark">S°</div><div className="rail-line"/><div className="rail-icon">◈</div><div className="rail-version">V0.1</div></aside>
    <section className={`sidebar ${sheetOpen ? 'is-open' : ''}`} aria-label="Weather data layers">
      <button type="button" className="sheet-trigger" aria-expanded={sheetOpen} aria-controls="layers-panel" onClick={() => setSheetOpen(value => !value)}><span className="sheet-handle" aria-hidden="true" /><span>LAYERS & DATA STATUS</span><span className="sheet-chevron" aria-hidden="true">{sheetOpen ? '⌄' : '⌃'}</span></button>
      <header className="brand"><small>METEOROLOGICAL WORKSPACE</small><h1>STORMCHASE <em>OS</em></h1><div><span className="pulse"/> FORECAST INTELLIGENCE <span className="version">/ V0.1</span></div></header>
      <div className="sidebar-scroll" id="layers-panel">
        <div className="section-index"><span>01 / MAP OPERATIONS</span><span>CONUS</span></div>
        <div className="region-control"><label htmlFor="region-select">GO TO REGION</label><select id="region-select" value={focus.region} onChange={event => focusRegion(event.currentTarget.value as RegionKey)}>{REGION_OPTIONS.map(region => <option key={region.value} value={region.value}>{region.label}</option>)}</select><p>Presets change map extent only. They are not chase targets.</p></div>
        <h2>ACTIVE DATA LAYERS</h2>
        <article className="layer-card">
          <div className="layer-head"><span className="layer-icon cyan">◇</span><div className="layer-name"><strong>Convective outlook</strong><small>SPC · DAY 1 CATEGORICAL</small></div><Toggle label="Show SPC outlook" enabled={showOutlook} onChange={setShowOutlook}/></div>
          <Status feed={outlook} now={now}/>
          <div className="opacity-control"><label htmlFor="outlook-opacity">POLYGON OPACITY <output htmlFor="outlook-opacity">{outlookOpacity}%</output></label><input id="outlook-opacity" type="range" min="0" max="85" step="5" value={outlookOpacity} onChange={event => setOutlookOpacity(Number(event.currentTarget.value))} /></div>
          <dl className="meta"><div><dt>Issued</dt><dd>{utc(outlook.data?.times.issued)}</dd></div><div><dt>Valid from</dt><dd>{utc(outlook.data?.times.valid)}</dd></div><div><dt>Valid until</dt><dd>{utc(outlook.data?.times.expires)}</dd></div><div><dt>Last retrieval</dt><dd>{utc(outlook.lastSuccess)}</dd></div></dl>
          {expired&&<p className="warning">Outlook has expired. The polygon overlay is hidden.</p>}
          {(outlook.state==='error'||spcOld)&&<p className="warning">SPC polygons hidden: feed is unavailable or stale. {outlook.error}</p>}
          <a className="source-link" target="_blank" rel="noreferrer" href={SPC_INFO}>OPEN OFFICIAL SPC OUTLOOK ↗</a>
        </article>
        <article className="layer-card">
          <div className="layer-head"><span className="layer-icon amber">!</span><div className="layer-name"><strong>Active warnings</strong><small>NWS · TORNADO / SEVERE TSTM</small></div><Toggle label="Show NWS warnings" enabled={showWarnings} onChange={setShowWarnings}/></div>
          <Status feed={alerts} now={now}/>
          <dl className="meta"><div><dt>Mapped polygons</dt><dd>{alerts.data?.geometry.features.length??'Unavailable'}</dd></div><div><dt>Unmapped alerts</dt><dd>{alerts.data?.missingGeometryCount??'Unavailable'}</dd></div><div><dt>Latest product sent</dt><dd>{utc(alerts.data?.newestSent)}</dd></div><div><dt>Last retrieval</dt><dd>{utc(alerts.lastSuccess)}</dd></div></dl>
          <p className="caveat">Some active warnings lack polygon geometry. A blank map does not mean warnings are absent.</p>
          {(alerts.state==='error'||nwsOld)&&<p className="warning">Warning polygons hidden: feed is unavailable or stale. {alerts.error}</p>}
          <a className="source-link" target="_blank" rel="noreferrer" href={NWS_INFO}>OPEN OFFICIAL NWS WARNINGS ↗</a>
        </article>
        <div className="section-index legend-heading"><span>02 / CATEGORICAL KEY</span><span>SPC</span></div>
        <div className="legend">{Object.entries(SPC_CATEGORIES).map(([id,entry])=><div className="legend-entry" key={id}><span className="swatch" style={{backgroundColor:entry.color}}/><b>{entry.abbreviation}</b><small>{entry.label}</small></div>)}</div>
        <p className="disclaimer">Source: NOAA/NWS. Product issue/validity times and browser retrieval times are separate. This experimental website is not an official alert service or a safe-route guarantee.</p>
      </div>
      <footer className="side-footer"><button type="button" onClick={refresh}>↻ &nbsp; REFRESH WEATHER DATA</button><div><span>5 MIN AUTOMATIC REFRESH</span><span>UTC {new Date(now).toISOString().slice(11,16)}</span></div></footer>
    </section>
    <main className="main-area">
      <MapView outlook={outlook.data?.geometry??null} warnings={alerts.data?.geometry??null}
        focus={focus} outlookOpacity={outlookOpacity/100}
        showOutlook={showOutlook&&outlook.state==='ready'&&!expired&&!spcOld}
        showWarnings={showWarnings&&alerts.state==='ready'&&!nwsOld}
        onCoordinates={setCoords}/>
      <div className="map-header"><div className="map-title"><span>◈</span><div><small>FORECAST CENTER</small><strong>Analysis Map</strong></div></div><div className="map-header-actions"><button type="button" className="extent-reset" onClick={() => focusRegion('conus')}>RESET CONUS EXTENT</button><div className="map-utc"><b>UTC</b> {new Date(now).toISOString().slice(0,16).replace('T',' · ')}</div></div></div>
      <div className="map-label">■ &nbsp; CONTIGUOUS UNITED STATES <span>/ LATEST RETRIEVED PRODUCTS</span></div>
      <div className="map-footer"><span>{coords}</span><span className={outlook.state==='ready' && alerts.state==='ready' && !expired && !spcOld && !nwsOld ? 'feeds-ok' : 'feeds-degraded'}><i/> {outlook.state==='ready' && alerts.state==='ready' && !expired && !spcOld && !nwsOld ? 'FEEDS RETRIEVED · LATENCY POSSIBLE' : 'CHECK SOURCE STATUS · NOT ALERT DELIVERY'}</span></div>
    </main>
  </div>;
}
