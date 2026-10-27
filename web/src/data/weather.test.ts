import { describe, expect, it } from 'vitest';
import { alertUrl, isExpired, isRetrievalStale, normalizeAlerts, normalizeOutlook, parseSourceTime, spcUrl } from './weather';

const square = { type: 'Polygon', coordinates: [[[-100,35],[-99,35],[-99,36],[-100,35]]] };
describe('SPC adapter', () => {
  it('maps the official category field and source times', () => {
    const data = normalizeOutlook({type:'FeatureCollection',features:[{type:'Feature',geometry:square,properties:{dn:4,issue:'2026-10-27 12:30:00',valid:'2026-10-27 12:00:00',expire:'2026-10-28 12:00:00',idp_source:'day1otlk_20261027_1200_cat'}}]});
    expect(data.geometry.features).toHaveLength(1);
    expect(data.times.issued).toBe('2026-10-27T12:30:00.000Z');
    expect(data.times.expires).toBe('2026-10-28T12:00:00.000Z');
  });
  it('rejects malformed feed collections', () => {
    expect(() => normalizeOutlook({features:[]})).toThrow('FeatureCollection');
  });
  it('excludes unrecognized category values', () => {
    const data = normalizeOutlook({type:'FeatureCollection',features:[{type:'Feature',geometry:square,properties:{dn:99}}]});
    expect(data.geometry.features).toHaveLength(0);
    expect(data.times.issued).toBeNull();
  });
});
describe('NWS alerts adapter', () => {
  it('counts missing geometry rather than pretending full warning coverage', () => {
    const data = normalizeAlerts({type:'FeatureCollection',features:[
      {type:'Feature',geometry:square,properties:{event:'Tornado Warning',sent:'2026-10-27T20:00:00Z'}},
      {type:'Feature',geometry:null,properties:{event:'Severe Thunderstorm Warning'}},
      {type:'Feature',geometry:square,properties:{event:'Flood Warning'}}
    ]});
    expect(data.totalMatchingCount).toBe(2);
    expect(data.missingGeometryCount).toBe(1);
    expect(data.geometry.features).toHaveLength(1);
  });
});
describe('timing and requests', () => {
  it('normalizes known UTC values and rejects invalid times', () => {
    expect(parseSourceTime('20261027_1630')).toBe('2026-10-27T16:30:00.000Z');
    expect(parseSourceTime('not-a-time')).toBeNull();
  });
  it('distinguishes expiration from stale retrieval', () => {
    expect(isExpired('2026-10-27T12:00:00Z',Date.parse('2026-10-28T00:00:00Z'))).toBe(true);
    expect(isRetrievalStale('2026-10-27T12:00:00Z',Date.parse('2026-10-27T12:20:00Z'))).toBe(true);
  });
  it('points to NOAA services', () => {
    expect(spcUrl()).toContain('f=geojson');
    expect(decodeURIComponent(alertUrl())).toContain('Tornado Warning,Severe Thunderstorm Warning');
  });
});
