# Progress

[done] Recon — spotter2 holds only assessment docx, hos pdf, how-to-guide.txt. Will not touch ..\spotter.
[done] Read how-to-guide transcript (Schneider logbook walkthrough) — defines log grid + remarks + recap.
[done] Verified toolchain + free APIs (OSRM, Nominatim, Photon) reachable.
[done] Backend scaffold: config (settings/urls/wsgi/asgi), eld app (views/serializers/exceptions/urls).
[done] Services: http (stdlib), geocoding (Nominatim+Photon, LRU), routing (OSRM + RoutePath interpolation).
[done] hos.py HosSimulator: 11h/14h/8h-break/10h-reset/70h-34h-restart/1000mi fuel loop.
[done] logs.py LogBookBuilder: per-day grid entries, remarks flags, per-line totals, mileage, 70h recap.
[done] planner.py: geocode -> route -> simulate -> reverse-geocode labels -> logs + stops + summary.
[done] venv named `spotter2` at repo root (Django 5.2.17, DRF 3.18.1, cors-headers 4.9.0). Removed stray backend/.venv.
[done] Live smoke test GB->Chicago->Nashville (672 mi): 2 log sheets, 24:00 totals on both, accurate remarks.
[done] Fixed: SimulationResult.end_time was the midnight log-fill tail; now the real post-trip completion.

[done] Real HOS bug fixed: HosSimulator._ensure_cycle_room() now gives on-duty blocks their own 70h look-ahead.
[found] The contract test caught a duplicate cycle-break emission after the fix; assertions tightened.
[done] Offline `eld` suite green: 43/43. `verify_contract.py` green: 633/633.
[done] Frontend (Vite + React + Leaflet): trip form w/ live geocode autocomplete, route map, itinerary, summary tiles, SVG log sheets.
[done] Real app captured live: 13 frames -> docs/video/assets/app/*.png + assets/plan.json (frontend/scripts/capture-video.mjs).
[done] docs/video/render.py: HTML frame renderer (wallpaper backdrop, VS Code chrome, browser chrome, captions).
[done] render.py gutter rasterises: verified 7,548 glyph pixels in a smoke frame (line numbers are real, not blank).
[done] render.py: zoom/focus params added to browser_frame and applied to the .bpage <img>.
[done] render.py: implemented the missing _panel() builder (was referenced at the call site but never defined).
[done] docs/video/make_video.py: 27-shot timeline + cue table, greedy SRT writer, ffmpeg concat encoder, ffprobe verifier.
[bug]  concat demuxer + duplicated final entry added a phantom 9s (249s). Fixed with an explicit -t <total>.
[bug]  verify() read ffprobe as one flat dict; the subtitle stream's width=N/A overwrote the video's. Fixed with -select_streams.
[done] BUILT + VERIFIED docs/video/spotter2-walkthrough.mp4: 1920x1080 h264, 240.0s, 10.8 MB, soft mov_text SRT (25 cues), 5/5 checks PASS.
[done] Spot-checked frames 014 / 025 / 130s: contained log sheet, terminal panel, highlight bands + Ln/Col status all render correctly.
[done] Scratch cleaned: backend/{test,contract}.log, docs/screens/desktop-probe.png, build/*.log, build/*.html.

[done] Extracted the real assessment brief from the .docx (deliverables, grading signals, named outputs).
[done] Research: 49 CFR 395.8(d) requires 11 elements; our sheet has 9 (missing 24-h period start time, main office address).
[done] Research: 395.8(h) grid prep + 395.8(f)(8) home-terminal time base confirmed; HOS numbers all match 395.3.
[done] Competitor recon: fingerprinted 3 live sites + 1 GitHub repo with puppeteer-core.
[bug]  probe script: `uniq()` applied to DOM elements before `.map(txt)` -> "s.slice is not a function". Fixed.
[bug]  `playwright-parallel` browser MCP cannot run here: writes output to Program Files -> EPERM. Switched to puppeteer-core.
[found] Competitor indureddy08-d has turn-by-turn route instructions + Print/PDF; henna has home terminal
        address + HOS explainer; both live-hosted. roadlog/optimizer are minimal forms.
[found] `routing.py` line ~155 sends OSRM `"steps": "false"` - we discard route instructions the brief asks for.
[done] Spec written to disk: specs/submission-ranking/{research.md,spec.md,tasks.md}.
[note] Verdict: 7.90/10, 3rd of 5. Not yet best. Gap = route instructions + deliverables (not deployed).
[done] T1 route instructions backend: OSRM steps=true, describe_step() prose, RouteStep cumulative miles. Live: 57 steps / 2 legs.
[done] T2 directions UI: Directions.jsx + 9 maneuver glyphs + 3rd tab. Verified 57 rows render.
[done] T3 395.8(d): added main_office_address + period_start_time; subtitle states midnight start + home-terminal base. 45/45 tests.
[done] T4 print: @page letter landscape, colour preserve, break-before (no trailing blank), summary wrapped no-print. PDF = 2 pages for 2 sheets, 792x612pt.
[bug]  App.jsx ?tab= only understood 'logs' -> tab=directions silently fell back to route. Now validated against TABS.
[bug]  verify-ui.mjs hung 60s because of the above; found via the stuck waitForFunction.
[bug]  Printed output had 3 pages (summary card consumed page 1) -> wrapped SummaryPanel in no-print.
[done] T5 lint: eslint 9 + react plugin + jsx-uses-vars. `npm run lint` exit 0 (0 errors, 4 fast-refresh warnings).
[note] ESLint 10 + react-hooks 7 produced 355 errors of bleeding-edge opinions. Pinned to the Vite template set (eslint 9.17).
[clean] Deleted 1.5 MB of accidentally-vendored React DevTools (scripts/.render-check.cjs/.mjs) + scripts/out/ + probe-competitors.mjs. Nothing referenced them.
[bug]  RouteMap.jsx had dead `const route = plan?.route`.
[bug]  verify_contract.py posts via 127.0.0.1:5173 but Vite 5 bound localhost as IPv6-only -> ECONNREFUSED. Set host:'127.0.0.1' in vite.config.js.
[done] T6 full re-verify: 45/45 tests, lint 0, build 0, wsgi import OK, verify_contract 633/633 ALL CHECKS PASSED.
[done] T9 HOS rules dialog (6 rules + CFR citations), T10 dark theme, T11 narrow-phone layout, T12 a11y. Verified: 6 rules render, Escape closes, mobile doc scrollWidth == clientWidth (no overflow).
[found] REAL BUG: autocomplete offered state codes for city queries - "Nashville" -> TN, GA, IN, AR and no Nashville; picking one geocoded to the middle of Tennessee. Cause: Photon leaves `city` empty when the match IS the city. Fixed via _PLACE_RANK + name recovery. Live after fix: Nashville, TN first; Green Bay, WI first.
[done] 7 geocoding regression tests (backend/eld/tests/test_geocoding.py). Suite 45 -> 52, all green.
[done] capture-video.mjs: pinned prefers-color-scheme light (headless Edge defaults to dark and was silently darkening the "light" shots) + 6 new shots (directions, HOS rules, dark theme).
[done] T8 voiceover script: docs/recording/voiceover-script.md, 22 beats, 4:10, with trim/pad guidance.
[done] T8 Loom-style reference video: docs/video/make_reference.py -> spotter2-loom-reference.mp4, 250.0s (4:10), 1920x1080 h264 + mov_text narration, 10.8 MB, 5/5 ffprobe PASS. Overlay = webcam bubble + chapter tag + clock + progress bar.
[done] README: fixed the proxy port (8090 not 8000), documented the new outputs, lint, the recording kit and the capture command.
[note] Only T7 (push + deploy) outstanding - needs the remote decision and credentials.

