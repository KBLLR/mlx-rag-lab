# QA Checklist — Smart Campus 3D

> Duplicate this file per QA run and attach to the session log / PR summary.

## Metadata
- **Build / Commit**: `<hash>`
- **Environment**: `<local / staging / prod>`
- **Tester**: `<name>`
- **Date**: `<YYYY-MM-DD>`

## Pre-flight
- [ ] `npm install` (or `pnpm install`)
- [ ] `npm run build`
- [ ] `npm run lint`
- [ ] Session log created (`docs/projects/.../sessions/`)

## Critical Paths

### 1. Three.js Scene
- [ ] Canvas renders campus geometry on load
- [ ] Orbit/zoom/pan respond to mouse & touchpad
- [ ] Sun/moon controllers update without console warnings

### 2. HUD & UI Shell
- [ ] HUD labels appear immediately with correct category badges
- [ ] Toolbar filters hide/show matching labels
- [ ] Panel tray opens/closes via floating button without blocking orbit
- [ ] Sensor dashboard glass panel displays latest sensor data

### 3. Home Assistant WS
- [ ] Connection status pill shows green “Connected”
- [ ] Sample entity update propagates to HUD + panel tray
- [ ] No “room not found” warnings in console

### 4. Export / Tooling
- [ ] GLB export succeeds (`Export → GLB`)
- [ ] STL export succeeds (`Export → STL`)
- [ ] `node src/tools/generateRoomRegistry.js` finishes cleanly

## Visual Checks
- [ ] Canvas background and UI overlays align with design (glass theme)
- [ ] No overlapping panel in bottom tray
- [ ] No stray debug panes (Tweakpane hidden, UIL pending)

## Regression / Smoke Notes
- 

## Follow-up Issues
- [ ] Logged in `docs/projects/3d-experience/tasks.md` (IDs: …)

## Sign-off
- ✅ / ⚠️ / ❌  — *Tester signature*
