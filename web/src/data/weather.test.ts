import {describe,expect,it,vi,afterEach} from 'vitest';
import {activeWarningGeometry,alertUrl,fetchAlerts,fetchOutlook,isOutlookExpiredOrUnknown,isRetrievalStale,
  normalizeAlerts,normalizeOutlook,parseSourceTime,spcCountUrl,spcUrl} from './weather';

const ring=[[-100,35],[-99,35],[-99,36],[-100,35]];
const square={type:'Polygon',coordinates:[ring]};
const outlookProps={dn:4,issue:'2026-10-27 12:30:00',valid:'2026-10-27 12:00:00',
  expire:'2026-10-28 12:00:00',idp_source:'day1otlk_20261027_1200_cat'};
const outlook=(features:unknown[])=>({type:'FeatureCollection',features});
const polygon=(id:string,event:string,extra:Record<string,unknown>={},geometry:unknown=square)=>
  ({type:'Feature',id,geometry,properties:{id,event,...extra}});
afterEach(()=>vi.unstubAllGlobals());
describe('SPC adapter',()=>{
  it('enforces complete official source counts and source-derived UTC validity',()=>{
    const data=normalizeOutlook(outlook([{type:'Feature',geometry:square,properties:outlookProps}]),1);
    expect(data.times.issued).toBe('2026-10-27T12:30:00.000Z');
    expect(data.times.expires).toBe('2026-10-28T12:00:00.000Z');
    expect(data.expectedFeatureCount).toBe(1);
    expect(isOutlookExpiredOrUnknown(data,Date.parse('2026-10-28T12:00:00Z'))).toBe(true);
  });
  it('rejects missing/mixed product revisions, rather than guessing from first polygon',()=>{
    expect(()=>normalizeOutlook(outlook([
      {type:'Feature',geometry:square,properties:outlookProps},
      {type:'Feature',geometry:square,properties:{...outlookProps,issue:'2026-10-27 16:30:00'}}
    ]))).toThrow(/Mixed/);
    expect(()=>normalizeOutlook(outlook([{type:'Feature',geometry:square,properties:outlookProps}]),2)).toThrow(/Incomplete/);
  });
  it('rejects unrecognized category values and malformed polygons without silent data loss',()=>{
    expect(()=>normalizeOutlook(outlook([{type:'Feature',geometry:square,properties:{...outlookProps,dn:99}}]))).toThrow(/Unknown/);
    expect(()=>normalizeOutlook(outlook([{type:'Feature',geometry:{type:'Polygon',coordinates:[[[-100,35],[-99,35]]]},properties:outlookProps}]))).toThrow(/malformed/);
    expect(()=>normalizeOutlook({features:[]})).toThrow(/FeatureCollection/);
  });
  it('reports empty valid collection explicitly',()=>expect(normalizeOutlook(outlook([]),0).geometry.features).toHaveLength(0));
});
describe('NWS warnings',()=>{
  it('preserves null-geometry identities, sent/effective/expire and deduplicates revisions',()=>{
    const list=outlook([
      polygon('https://example.test/tor','Tornado Warning',{sent:'2026-10-27T20:00:00Z'}),
      polygon('https://example.test/svr','Severe Thunderstorm Warning',{sent:'2026-10-27T20:01:00Z',expires:'2026-10-27T20:30:00Z'},null),
      polygon('https://example.test/tor','Tornado Warning',{sent:'2026-10-27T20:05:00Z'}),
      polygon('https://example.test/flood','Flood Warning')
    ]);
    const data=normalizeAlerts(list);
    expect(data.totalMatchingCount).toBe(2);
    expect(data.missingGeometryCount).toBe(1);
    expect(data.records[0].sent).toBe('2026-10-27T20:05:00.000Z');
    expect(data.records[1].sourceUrl).toBe('https://example.test/svr');
  });
  it('hides expired warnings while retaining audit metadata',()=>{
    const data=normalizeAlerts(outlook([polygon('a','Tornado Warning',{expires:'2026-10-27T20:00:00Z'})]));
    expect(activeWarningGeometry(data,Date.parse('2026-10-27T20:01:00Z')).features).toHaveLength(0);
    expect(data.records).toHaveLength(1);
  });
  it('rejects missing identifiers and bad non-null geometry',()=>{
    expect(()=>normalizeAlerts(outlook([{type:'Feature',geometry:null,properties:{event:'Tornado Warning'}}]))).toThrow(/identifier/);
    expect(()=>normalizeAlerts(outlook([polygon('abc','Tornado Warning',{}, {type:'Point',coordinates:[-99,35]})]))).toThrow(/invalid polygon/);
  });
});
describe('time parsing and requests',()=>{
  it('normalizes known UTC and numeric ArcGIS millisecond timestamps',()=>{
    expect(parseSourceTime('20261027_1630')).toBe('2026-10-27T16:30:00.000Z');
    expect(parseSourceTime('202610271630')).toBe('2026-10-27T16:30:00.000Z');
    expect(parseSourceTime('1793119002000')).toBe(new Date(1793119002000).toISOString());
    expect(parseSourceTime('202602301630')).toBeNull();
    expect(parseSourceTime('2026-10-27T16:30:00')).toBeNull();
    expect(parseSourceTime('2026-10-27T11:30:00-05:00')).toBe('2026-10-27T16:30:00.000Z');
    expect(parseSourceTime(Date.parse('2026-10-27T16:30:00Z'))).toBe('2026-10-27T16:30:00.000Z');
    expect(parseSourceTime('bad')).toBeNull();
  });
  it('treats missing retrieval timestamp as unavailable, not fresh',()=>{
    expect(isRetrievalStale(null)).toBe(true);
    expect(isRetrievalStale('2026-10-27T12:00:00Z',Date.parse('2026-10-27T12:20:00Z'))).toBe(true);
  });
  it('uses two independent NWS event filters and SPC count query',()=>{
    expect(alertUrl('Tornado Warning')).toContain('Tornado+Warning');
    expect(alertUrl('Severe Thunderstorm Warning')).toContain('Severe+Thunderstorm+Warning');
    expect(spcCountUrl()).toContain('returnCountOnly=true');
    expect(spcUrl()).toContain('f=geojson');
    expect(spcUrl(2)).toContain('/FeatureServer/9/query');
    expect(spcUrl(3)).toContain('/FeatureServer/17/query');
    expect(spcCountUrl(3)).toContain('/FeatureServer/17/query');
  });
  it('fetches SPC count and geometry atomically and fails closed on truncation',async()=>{
    const responses=[outlook([{type:'Feature',geometry:square,properties:outlookProps}]),{count:2}];
    vi.stubGlobal('fetch',vi.fn().mockImplementation(async()=>({ok:true,json:async()=>responses.shift()})));
    await expect(fetchOutlook(new AbortController().signal)).rejects.toThrow(/Incomplete/);
  });
  it('merges single-event responses by id',async()=>{
    const responses=[outlook([polygon('tor','Tornado Warning')]),outlook([polygon('svr','Severe Thunderstorm Warning')])];
    vi.stubGlobal('fetch',vi.fn().mockImplementation(async()=>({ok:true,json:async()=>responses.shift()})));
    const data=await fetchAlerts(new AbortController().signal);
    expect(data.totalMatchingCount).toBe(2);
  });
});
