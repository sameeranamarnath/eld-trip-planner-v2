# Active Context — Spotter ELD Trip Planner

## Objective
Full-stack Django + React app that takes (current location, pickup, dropoff, current cycle used hrs)
and outputs (a) route map with stops/rests/fuel, (b) filled-out FMCSA daily ELD log sheets
(one per 24h day). Hosted live + GitHub repo + screencap subtitle script.

## Scope boundary
ALL work happens inside `c:\projects\assessments\spotter2` only. Do not touch `..\spotter`.

## Current focus
The walkthrough video is BUILT and verified. Next up: repo hygiene (README, .gitignore,
git init) and then deployment. See "Next steps" at the bottom.

## Verified facts
- Python 3.11.9 (venv `spotter2` at repo root), Node v24.16.0, npm 11.13.0, git 2.53.0.
- ffmpeg 9.0 + ffprobe on PATH; no PIL -> all video compositing is HTML via headless Edge.
- `highlight.js` vendored at `frontend/node_modules/@highlightjs/cdn-assets` (vs2015 theme);
  `puppeteer-core` + highlight.js were installed with `--no-save`.
- Not a git repository yet.
- `gh` CLI authenticated (accounts: amar-cbre [active], amaraxior, sameeranamarnath).
- No Vercel CLI / no Vercel token on disk -> deploy must be scripted + documented.
- Free, keyless, reachable APIs: OSRM demo (routing), Nominatim (geocoding), Photon (reverse).

## Decisions
- Routing: OSRM demo server (keyless). Geocoding: Nominatim. Reverse geocode: Photon -> Nominatim fallback.
- Map tiles in frontend: Leaflet + OpenStreetMap raster tiles (keyless).
- Backend is STATELESS (pure computation) -> deploys cleanly to Vercel serverless + Render/Docker.
- Frontend: Vite + React (JS), hand-rolled CSS design system, react-leaflet.
- Log sheets: rendered as SVG in React from a normalized JSON model returned by the API.
- All times treated as naive local time at the home terminal (documented assumption).

## HOS model (property carrier, 70h/8day, no adverse conditions)
11h driving limit; 14h on-duty window; 30-min break after 8h cumulative driving;
10h consecutive reset; 70h/8day cycle with 34h restart; fuel <= every 1000 mi;
30-min pre-trip, 60-min pickup, 60-min dropoff, 30-min post-trip, 30-min fuel.

## Test state
- `backend/eld/tests`: 43/43 pass (offline suite, no network).
- `backend/scripts/verify_contract.py`: 633/633 pass (real 672-mile trip, 2 log sheets).

## Walkthrough video (deliverable)
- Built by `docs/video/make_video.py`; its `SHOTS` + `CUES` tables are the single source of
  truth for shot order, durations and subtitle text. `docs/video/render.py` draws each
  1920x1080 frame as HTML, headless Edge screenshots it, ffmpeg concats the stills and muxes
  the `.srt` as a soft `mov_text` track.
- Output: `docs/video/spotter2-walkthrough.mp4` - 1920x1080 h264, 240.0s, 10.8 MB, plus
  `docs/video/spotter2-walkthrough.srt` (25 cues).
- 27 shots: 15 real app frames + 12 VS Code code shots.
- Verified: 5/5 ffprobe checks PASS, whole-file decode clean, and the frame extracted at
  t=130s matches the shot the timeline says should be there.
- Rebuild: `python make_video.py` (`--skip-render` reuses existing frames; `--frames` stops
  after rendering, before the encode).

## Ruled out (do not retry)
- Live screen capture as the desktop backdrop - other agents' windows pollute it. Use the
  wallpaper file directly.
- PIL for compositing - not installed; compose in HTML and screenshot with headless Edge.
- Committing `docs/video/build/` - derived artifacts; gitignore it.
- `ffmpeg -vf fps=N,format=yuv420p` WITHOUT an explicit `-t <total>` - the duplicated final
  concat entry inherits the previous duration and adds a whole extra shot (249s not 240s).
- Parsing `ffprobe -of default=noprint_wrappers=1` into one flat dict - the subtitle stream's
  `width=N/A` silently overwrites the video's. Query each stream with `-select_streams`.

## Next steps
1. Add `.gitignore` (node_modules, __pycache__, venv, docs/video/build, *.log).
2. Write repo `README.md` (what it does, how to run, how to rebuild the video, deploy notes).
3. `git init` + commit + create/push the repo with `gh` (account `amar-cbre`).
4. Deploy guidance: Django to Render/Docker, Vite frontend to Vercel (no CLI/token on disk).
5. Sanity-check the app entrypoint imports cleanly before deploying.
