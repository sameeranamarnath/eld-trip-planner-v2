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

[next] Repo hygiene: .gitignore, README.md, `git init`, commit, push as amar-cbre. Then deploy guidance.

