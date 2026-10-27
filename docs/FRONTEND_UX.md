# Frontend Interaction Design — v0.1 review branch

Status: **proposed in a stacked PR**; automated browser behavior is not yet verified.

## Interface priorities

- Map takes precedence over controls. Desktop uses a narrow layer inspector; mobile uses a collapsed bottom sheet so the map fills the viewport until controls are requested.
- The **Go to region** control changes only a map camera extent. View presets must never be presented as meteorological targets or safe chase regions.
- Day 1 SPC polygons support adjustable fill opacity independent of warning opacity. Layer visibility toggles do not modify provider values.
- Only supported data layers are interactive. HRRR model/run selectors, soundings, chase targeting, road networks and radar remain out of the interface until verified adapters exist.
- UTC issuance, validity, expiry and retrieval timestamps remain visible in the detail inspector. A positive fetch status is not equivalent to a current official warning service.
- Display disabled or erroneous feeds with explicit text; never imply a blank map is hazard-free.

## Browser acceptance checklist

- [ ] At 1440x900 verify map controls, region changes and readable date metadata.
- [ ] At 390x844 verify initial collapsed sheet, open/close, scroll, and usable unobstructed map.
- [ ] Keyboard-only: tab to sheet trigger, region selector, slider, layer toggles and reset action; verify focus ring and input operation.
- [ ] Check zoom/pan after region changes; confirm reset works after map is manually moved.
- [ ] Confirm outlook opacity reaches 0 and 85 percent without altering warnings.
- [ ] Verify official feed failures, malformed responses and stale times remain discoverable on mobile.
- [ ] Verify the map responds to viewport resizing and the map tile attribution remains legible.
- [ ] Inspect browser console for MapLibre errors and perform Lighthouse/axe accessibility audit.

Automated unit tests cover static region extent constraints, **not** end-to-end interaction or official feed availability. The complete v0.1 release gates remain tracked by docs/ROADMAP.md and issue #2.
