# Frontend Interaction Design — v0.1 review branch

Status: frontend foundation merged; manual browser behavior and live-data verification remain separate release checks.

## Interface priorities

- Map takes precedence over controls. Desktop uses a narrow layer inspector; mobile uses a collapsed bottom sheet so the map fills the viewport until controls are requested.
- The **Go to region** control changes only a map camera extent. View presets must never be presented as meteorological targets or safe chase regions.
- Day 1 SPC polygons support adjustable fill opacity independent of warning opacity. MapLibre feature sort keys draw higher categorical DN levels above lower levels if provider polygons overlap; browser comparison with SPC remains necessary. Layer visibility toggles do not modify provider values.
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

## Visual system — dual-theme revision (2026-10-27)

- **Design direction:** meteorological field workstation, not a conversational dashboard. Narrow display typography (Barlow Condensed), readable IBM Plex Sans, and tabular IBM Plex Mono; system-font fallbacks when Google Fonts is unavailable.
- **Dark:** graphite / blackened-steel backgrounds, copper focus accents, restrained muted neutral metadata; **Light:** warm-paper surfaces, charcoal text, oxidized-copper accents. SPC categorical risk colors and NWS warning classifications remain semantically consistent across both.
- Theme toggle sits in the map toolbar on desktop and mobile; explicit choice persists in localStorage where permitted, otherwise changes remain usable during the session. First visit respects OS appearance preference; color-scheme and theme-color are kept consistent.
- MapLibre switches between CARTO dark-matter and CARTO positron styles; both styles require network access and provider permission. Overlay sources and paint settings are restored after every style load. Camera position and user-selected extent should not jump solely from switching appearance.
- [ ] Manual QA: repeatedly toggle modes with SPC/warnings visible, hide one layer, change opacity, pan/zoom and confirm layers and camera are preserved.
- [ ] Manual QA: mobile theme button fits at 320px and larger, collapsed sheet remains usable, map attribution remains visible.
- [ ] Manual QA: contrast audit WCAG 2.2 AA on buttons, small timestamps, focus rings, and cartographic controls for both modes.
- [ ] Manual QA: reload after selecting each theme; test missing localStorage and blocked fonts, and OS appearance on first visit.
