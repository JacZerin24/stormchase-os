import { useEffect, useMemo, useState } from 'react';
import {HRRR_PILOT_PATH,parsePilotManifest,pilotOverlay,type PilotManifest,type PilotMode} from './data/hrrrPilot';
import {CONV_ARCHIVE_PATH,CONV_DISPLAY,CONV_LEGENDS,convectiveLegendCss,convectiveImage,parseConvectiveManifest,type ConvectiveManifest,type ConvDisplayKey} from './data/hrrrConvective';
import MapView from './components/MapView';
import {activeWarningGeometry,NWS_INFO,SPC_CATEGORIES,SPC_INFO} from './data/weather';
import {outlookHealth,warningHealth,type WeatherHealth} from './data/freshness';
import {useWeather} from './hooks/useWeather';
import { REGION_OPTIONS, type RegionKey } from './data/regions';
import { getInitialTheme, THEME_STORAGE_KEY, type DisplayTheme } from './theme';

function utc(value: string | null | undefined): string {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unavailable' : `${date.toISOString().slice(0,16).replace('T',' ')} UTC`;
}
function Status({health}:{health:WeatherHealth}) {
  return <span className={`feed-status ${health.state==='available'?'good':'bad'}`}><span className="status-dot"/>{health.label}</span>;
}
function Toggle({label,enabled,onChange}: {label:string;enabled:boolean;onChange:(v:boolean)=>void}) {
  return <label className="switch"><span className="sr-only">{label}</span><input type="checkbox" checked={enabled} onChange={e=>onChange(e.currentTarget.checked)}/><span className="track" aria-hidden="true"><span /></span></label>;
}
export default function App() {
  const {outlook,alerts,refresh,day,setDay} = useWeather();
  const [theme,setTheme] = useState<DisplayTheme>(getInitialTheme);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content',theme === 'dark' ? '#161b20' : '#f2f0e9');
    try { window.localStorage.setItem(THEME_STORAGE_KEY,theme); } catch { /* Storage can be disabled; theme still works for this session. */ }
  }, [theme]);
  const [showOutlook,setShowOutlook] = useState(true);
  const [showWarnings,setShowWarnings] = useState(true);
  const [outlookOpacity,setOutlookOpacity] = useState(42);
  const [focus,setFocus] = useState<{ region: RegionKey; revision: number }>({region:'conus',revision:0});
  const [sheetOpen,setSheetOpen] = useState(false);
  const focusRegion = (region: RegionKey) => setFocus(previous => ({region, revision:previous.revision+1}));
  const [coords,setCoords] = useState('CONUS INITIAL VIEW');
  const [now,setNow] = useState(Date.now());
  useEffect(()=>{const id=window.setInterval(()=>setNow(Date.now()),60000);return ()=>window.clearInterval(id);},[]);
  const spcHealth=outlookHealth(outlook,now);
  const nwsHealth=warningHealth(alerts,now);
  const currentWarnings=activeWarningGeometry(alerts.data,now);
  const [pilotManifest,setPilotManifest] = useState<PilotManifest | null>(null);
  const [pilotLoadError,setPilotLoadError] = useState<string | null>(null);
  const [pilotMode,setPilotMode] = useState<PilotMode>('earlier');
  const [pilotEnabled,setPilotEnabled] = useState(false);
  const [pilotFocusRevision,setPilotFocusRevision] = useState(0);
  useEffect(()=>{
    const abort=new AbortController();
    const manifestUrl=import.meta.env.BASE_URL+HRRR_PILOT_PATH+'manifest.json';
    void fetch(manifestUrl,{signal:abort.signal,cache:'no-cache'}).then(async r=>{
      if(!r.ok)throw new Error('Archived model assets not published (HTTP '+r.status+')');
      const parsed=parsePilotManifest(await r.json() as unknown);
      if(!abort.signal.aborted)setPilotManifest(parsed);
    }).catch((error:unknown)=>{
      if(!abort.signal.aborted)setPilotLoadError(error instanceof Error?error.message:'Unknown asset problem');
    });
    return ()=>abort.abort();
  },[]);
  const [convectiveManifest,setConvectiveManifest]=useState<ConvectiveManifest|null>(null);
  const [convectiveLoadError,setConvectiveLoadError]=useState<string|null>(null);
  const [convectiveEnabled,setConvectiveEnabled]=useState(false);
  const [convectiveField,setConvectiveField]=useState<ConvDisplayKey>('refc_f03');
  useEffect(()=>{
    const abort=new AbortController();
    const url=import.meta.env.BASE_URL+CONV_ARCHIVE_PATH+'manifest.json';
    void fetch(url,{signal:abort.signal,cache:'no-cache'}).then(async r=>{
      if(!r.ok)throw new Error('Archived convective case unavailable: HTTP '+r.status);
      const value=parseConvectiveManifest(await r.json() as unknown);
      if(!abort.signal.aborted)setConvectiveManifest(value);
    }).catch((error:unknown)=>{
      if(!abort.signal.aborted)setConvectiveLoadError(error instanceof Error?error.message:'Unknown model asset failure');
    });
    return ()=>abort.abort();
  },[]);
  const pilotImage=useMemo(()=>{
    if(convectiveEnabled && convectiveManifest){
      return convectiveImage(convectiveManifest,convectiveField,import.meta.env.BASE_URL+CONV_ARCHIVE_PATH);
    }
    return pilotEnabled && pilotManifest ?
      pilotOverlay(pilotManifest,pilotMode,import.meta.env.BASE_URL+HRRR_PILOT_PATH) : null;
  },[convectiveEnabled,convectiveManifest,convectiveField,pilotEnabled,pilotManifest,pilotMode]);
  return <div className="shell">
    <aside className="rail" aria-hidden="true"><div className="rail-mark">SC<span>·</span></div><div className="rail-line"/><div className="rail-icon">⌖</div><div className="rail-version">V0.1</div></aside>
    <section className={`sidebar ${sheetOpen ? 'is-open' : ''}`} aria-label="Weather data layers">
      <button type="button" className="sheet-trigger" aria-expanded={sheetOpen} aria-controls="layers-panel" onClick={() => setSheetOpen(value => !value)}><span className="sheet-handle" aria-hidden="true" /><span>LAYERS & DATA STATUS</span><span className="sheet-chevron" aria-hidden="true">{sheetOpen ? '⌄' : '⌃'}</span></button>
      <header className="brand"><small>FIELD ANALYSIS / METEOROLOGY</small><h1>STORMCHASE <em>OS</em></h1><div><span className="pulse"/> OPERATIONAL ANALYSIS WORKSPACE <span className="version">/ V0.1</span></div></header>
      <div className="sidebar-scroll" id="layers-panel">
        <div className="section-index"><span>01 / MAP OPERATIONS</span><span>CONUS</span></div>
        <div className="region-control"><label htmlFor="region-select">GO TO REGION</label><select id="region-select" value={focus.region} onChange={event => focusRegion(event.currentTarget.value as RegionKey)}>{REGION_OPTIONS.map(region => <option key={region.value} value={region.value}>{region.label}</option>)}</select><p>Presets change map extent only. They are not chase targets.</p></div>
        <div className="region-control"><label htmlFor="spc-day">SPC CATEGORICAL PERIOD</label><select id="spc-day" value={day} onChange={event=>setDay(Number(event.currentTarget.value) as 1|2|3)}><option value={1}>Day 1</option><option value={2}>Day 2</option><option value={3}>Day 3</option></select><p>These are official categorical products. Probabilistic and conditional-intensity layers have different meanings and are not combined.</p></div>
        <h2>ACTIVE DATA LAYERS</h2>
        <article className="layer-card">
          <div className="layer-head"><span className="layer-icon cyan">◇</span><div className="layer-name"><strong>Convective outlook</strong><small>SPC · DAY {day} CATEGORICAL</small></div><Toggle label="Show SPC outlook" enabled={showOutlook} onChange={setShowOutlook}/></div>
          <Status health={spcHealth}/>
          <div className="opacity-control"><label htmlFor="outlook-opacity">POLYGON OPACITY <output htmlFor="outlook-opacity">{outlookOpacity}%</output></label><input id="outlook-opacity" type="range" min="0" max="85" step="5" value={outlookOpacity} onChange={event => setOutlookOpacity(Number(event.currentTarget.value))} /></div>
          <dl className="meta"><div><dt>Issued</dt><dd>{utc(outlook.data?.times.issued)}</dd></div><div><dt>Valid from</dt><dd>{utc(outlook.data?.times.valid)}</dd></div><div><dt>Valid until</dt><dd>{utc(outlook.data?.times.expires)}</dd></div><div><dt>GIS ingested</dt><dd>{utc(outlook.data?.times.gisIngested)}</dd></div><div><dt>Last attempt</dt><dd>{utc(outlook.lastAttempt)}</dd></div><div><dt>Last retrieval</dt><dd>{utc(outlook.lastSuccess)}</dd></div></dl>
          
          {spcHealth.explanation&&<p className="warning">{spcHealth.explanation}</p>}
          <a className="source-link" target="_blank" rel="noreferrer" href={SPC_INFO}>OPEN OFFICIAL SPC OUTLOOK ↗</a>
        </article>
        <article className="layer-card">
          <div className="layer-head"><span className="layer-icon amber">!</span><div className="layer-name"><strong>Active warnings</strong><small>NWS · TORNADO / SEVERE TSTM</small></div><Toggle label="Show NWS warnings" enabled={showWarnings} onChange={setShowWarnings}/></div>
          <Status health={nwsHealth}/>
          <dl className="meta"><div><dt>Current polygons</dt><dd>{alerts.data?currentWarnings.features.length:"Unavailable"}</dd></div><div><dt>Unmapped alerts</dt><dd>{alerts.data?.missingGeometryCount??'Unavailable'}</dd></div><div><dt>Latest product sent</dt><dd>{utc(alerts.data?.newestSent)}</dd></div><div><dt>Last attempt</dt><dd>{utc(alerts.lastAttempt)}</dd></div><div><dt>Last retrieval</dt><dd>{utc(alerts.lastSuccess)}</dd></div></dl>
          <p className="caveat">Some active warnings lack polygon geometry. A blank map does not mean warnings are absent.</p>
          {nwsHealth.explanation&&<p className="warning">{nwsHealth.explanation}</p>}
          <a className="source-link" target="_blank" rel="noreferrer" href={NWS_INFO}>OPEN OFFICIAL NWS WARNINGS ↗</a>
        </article>
        <div className="section-index legend-heading"><span>02 / CATEGORICAL KEY</span><span>SPC</span></div>
        <div className="legend">{Object.entries(SPC_CATEGORIES).map(([id,entry])=><div className="legend-entry" key={id}><span className="swatch" style={{backgroundColor:entry.color}}/><b>{entry.abbreviation}</b><small>{entry.label}</small></div>)}</div>
        <div className="section-index legend-heading"><span>03 / CONVECTIVE MODEL LAB</span><span>HISTORICAL HRRR</span></div>
        <article className="layer-card model-archive-panel">
          <div className="layer-head"><span className="layer-icon cyan">◈</span><div className="layer-name"><strong>Convective forecast fields</strong><small>17Z OCT 27 2026 · ARCHIVED</small></div>
            <Toggle label="Show archived convective HRRR analysis" enabled={convectiveEnabled} onChange={v=>{setConvectiveEnabled(v);if(v)setPilotEnabled(false)}}/>
          </div>
          <p className="caveat">Actual NOAA HRRR model output, not current weather. Simulated reflectivity is not radar; a UH swath is not a storm track or tornado probability.</p>
          {convectiveManifest ? <>
            <dl className="meta">
              <div><dt>Model initialized</dt><dd>{utc(convectiveManifest.runAt)}</dd></div>
              <div><dt>Final valid hour</dt><dd>{utc(convectiveManifest.finalValidAt)}</dd></div>
              <div><dt>Product</dt><dd>{CONV_DISPLAY[convectiveField].kind}</dd></div>
              <div><dt>Source units</dt><dd>{CONV_DISPLAY[convectiveField].unit}</dd></div>
            </dl>
            <div className="region-control">
              <label htmlFor="convective-field-select">SELECT VERIFIED GRIB-DERIVED FIELD</label>
              <select id="convective-field-select" value={convectiveField} onChange={e=>{setConvectiveField(e.currentTarget.value as ConvDisplayKey);setConvectiveEnabled(true);setPilotEnabled(false);}}>
                <optgroup label="Storm structure / simulated radar">
                  <option value="refc_f03">Composite reflectivity · simulated</option>
                  <option value="uh25_max_f03">2–5 km UH · hourly maximum</option>
                  <option value="uh25_swath_3h">2–5 km UH · 3-hour max swath</option>
                </optgroup>
                <optgroup label="Upper-air dynamics">
                  <option value="hgt500_f03">500-hPa geopotential height</option>
                  <option value="t700_f03">700-hPa temperature</option>
                </optgroup>
                <optgroup label="Instability and shear">
                  <option value="cape_sb_f03">Surface-based CAPE</option>
                  <option value="srh01_f03">0–1 km storm-relative helicity</option>
                </optgroup>
              </select>
              <p>{CONV_DISPLAY[convectiveField].notice}</p>
            </div>
            <div className="convective-legend" role="img" aria-label={'Fixed color scale for '+CONV_DISPLAY[convectiveField].title}>
              <div className="legend-range-heading">FIXED FORECAST SCALE · {CONV_LEGENDS[convectiveField].unit}</div>
              <div className="legend-color-ramp" style={{background:convectiveLegendCss(convectiveField)}}/>
              <div className="legend-color-ticks"><span>{CONV_LEGENDS[convectiveField].ticks[0]}</span><span>{CONV_LEGENDS[convectiveField].ticks[Math.floor(CONV_LEGENDS[convectiveField].ticks.length/2)]}</span><span>{CONV_LEGENDS[convectiveField].ticks[CONV_LEGENDS[convectiveField].ticks.length-1]}</span></div>
            </div>
            {CONV_LEGENDS[convectiveField].maskBelow!==null&&
              <p className="caveat">Pixels below {CONV_LEGENDS[convectiveField].maskBelow} {CONV_LEGENDS[convectiveField].unit} are transparent, not missing source data.</p>}
            {convectiveField.startsWith('uh25')&&convectiveManifest.fieldProducts[convectiveField].maxValue<25&&
              <p className="warning">This archived region did not reach the 25 m²/s² color threshold in this simulated product. Blank shading does not establish the absence of real storms or tornado potential.</p>}
            <button type="button" className="model-focus" onClick={()=>{setConvectiveEnabled(true);setPilotEnabled(false);setPilotFocusRevision(i=>i+1);}}>FOCUS ARCHIVED PLAINS REGION</button>
            <p className="caveat">QA: native source run/level/step, geographic pixel checks and hashes. Independent forecast verification and observed storm-object tracking are not complete.</p>
          </> : <p className="warning">{convectiveLoadError??'Checking real archived convective GRIB assets...'}</p>}
        </article>
        <div className="section-index legend-heading"><span>04 / EARLIER MODEL LAB</span><span>HRRR</span></div>
        <article className="layer-card model-archive-panel">
          <div className="layer-head"><span className="layer-icon cyan">◈</span><div className="layer-name"><strong>HRRR model cycle test</strong><small>ARCHIVED 27 OCT 2026 · NOT LIVE</small></div><Toggle label="Show archived HRRR pilot overlay" enabled={pilotEnabled} onChange={v=>{setPilotEnabled(v);if(v)setConvectiveEnabled(false)}}/></div>
          <p className="caveat">Historical, real-data test. The images do not update and must never be interpreted as a current forecast.</p>
          {pilotManifest ? <>
            <dl className="meta">
              <div><dt>Common valid time</dt><dd>{utc(pilotManifest.validAt)}</dd></div>
              <div><dt>Spatial method</dt><dd>Nearest gridpoint · 5 km cap</dd></div>
              <div><dt>Displayed field</dt><dd>2-m temperature · °F</dd></div>
            </dl>
            <div className="region-control"><label htmlFor="model-cycle">SAME VALID TIME / DIFFERENT CYCLES</label><select id="model-cycle" value={pilotMode} onChange={event=>setPilotMode(event.currentTarget.value as PilotMode)}>
              <option value="earlier">12Z initialization · +6 h</option>
              <option value="later">15Z initialization · +3 h</option>
              <option value="difference">15Z − 12Z · temperature change</option>
            </select><p>{pilotMode==='difference'?'Color scale: °F difference between forecast cycles; not observed change.':'Temperature colors use identical fixed °F thresholds across both cycles.'}</p></div>
            <button type="button" className="model-focus" onClick={()=>{setPilotEnabled(true);setConvectiveEnabled(false);setPilotFocusRevision(i=>i+1);}}>FOCUS PLAINS TEST DOMAIN</button>
            <p className="caveat">QA caveat: geometric regridding and GRIB identity checked; independent numerical forecast skill and map alignment signoff remain outstanding.</p>
          </> : <p className="warning">{pilotLoadError??'Checking archived HRRR test assets...'}</p>}
        </article>
        <p className="disclaimer">Source: NOAA/NWS. Product issue/validity times and browser retrieval times are separate. This experimental website is not an official alert service or a safe-route guarantee.</p>
      </div>
      <footer className="side-footer"><button type="button" onClick={refresh}>↻ &nbsp; REFRESH WEATHER DATA</button><div><span>5 MIN AUTOMATIC REFRESH</span><span>UTC {new Date(now).toISOString().slice(11,16)}</span></div></footer>
    </section>
    <main className="main-area">
      <MapView outlook={outlook.data?.geometry??null} warnings={currentWarnings}
        focus={focus} outlookOpacity={outlookOpacity/100} theme={theme}
        showOutlook={showOutlook&&spcHealth.render}
        showWarnings={showWarnings&&nwsHealth.render}
        pilotImage={pilotImage} pilotFocusRevision={pilotFocusRevision}
        onCoordinates={setCoords}/>
      <div className="map-header"><div className="map-title"><span className="map-title-mark">⌖</span><div><small>FORECAST DESK / 01</small><strong>Severe Weather Analysis</strong></div></div><div className="map-header-actions"><button type="button" className="theme-button" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={() => setTheme(previous => previous === 'dark' ? 'light' : 'dark')}><span className="theme-glyph" aria-hidden="true">{theme === 'dark' ? '☼' : '◕'}</span><span>{theme === 'dark' ? 'LIGHT' : 'DARK'} MODE</span></button><button type="button" className="extent-reset" onClick={() => focusRegion('conus')}>RESET VIEW</button><div className="map-utc"><b>UTC</b> {new Date(now).toISOString().slice(0,16).replace('T',' · ')}</div></div></div>
      <div className="map-label"><span className="map-label-rule" aria-hidden="true" />CONTIGUOUS UNITED STATES <span>/ LATEST RETRIEVED PRODUCTS</span></div>
      {pilotImage&&<div className="archive-map-banner" role="status">
        {convectiveEnabled ? 'ARCHIVED HRRR SIMULATED FORECAST · NOT CURRENT' : 'ARCHIVED HRRR TEST CASE · VALID 2026-10-27 18Z · NOT CURRENT'}
        <span>{convectiveEnabled ? CONV_DISPLAY[convectiveField].title+' · '+CONV_DISPLAY[convectiveField].kind :
          (pilotMode==='difference'?'15Z − 12Z FORECAST CHANGE':'MODEL INIT '+(pilotMode==='earlier'?'12Z':'15Z'))}</span>
      </div>}
      <div className="map-footer"><span>{coords}</span><span className={spcHealth.render && nwsHealth.render ? 'feeds-ok' : 'feeds-degraded'}><i/> {spcHealth.render && nwsHealth.render ? 'FEEDS RETRIEVED · LATENCY POSSIBLE' : 'CHECK SOURCE STATUS · NOT ALERT DELIVERY'}</span></div>
    </main>
  </div>;
}
