import { describe, expect, it } from 'vitest';
import { REGION_BOUNDS, REGION_OPTIONS } from './regions';

describe('navigation presets', () => {
  it('provides a bounded map extent for every view', () => {
    for (const option of REGION_OPTIONS) {
      const [[west,south],[east,north]] = REGION_BOUNDS[option.value];
      expect(west).toBeLessThan(east);
      expect(south).toBeLessThan(north);
      expect(west).toBeGreaterThanOrEqual(-180);
      expect(north).toBeLessThanOrEqual(90);
    }
  });
  it('keeps the national view available for resetting the map', () => {
    expect(REGION_OPTIONS[0].value).toBe('conus');
  });
});
