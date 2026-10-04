# Active Context — Spotter ELD Trip Planner

## Objective
Make the assessment submission the best in the field, then hand over a recording kit (voiceover
script with timeline markers + Loom-style reference video) for the user's own Loom recording.

## Where the assessment is won (from the .docx)
Deliverables: a live hosted version, a 3-5 minute loom covering the app AND the code, GitHub
code. Grading: "test the hosted version for **accuracy**"; "**UI and UX must be good** ... it can
compensate for some inaccuracies". Named outputs: **route instructions** + a map with stops and
rests + drawn daily log sheets.

## Verdict (evidence in specs/submission-ranking/)
**Not yet the best: 7.90/10, 3rd of 5** on the weighted rubric. Two concrete reasons:
1. No **route instructions** - `routing.py` sends OSRM `"steps": "false"` and discards maneuvers.
2. Deliverables incomplete - not pushed, not deployed (15% of the rubric on the floor).
Plus the log sheet is **9/11 on 49 CFR 395.8(d)** (missing 24-hour period starting time and main
office address), there is no print/PDF export, and no lint script.

## Agreed scope (user-approved)
T1-T8 in `specs/submission-ranking/tasks.md` PLUS differentiating polish: dark mode, mobile
layout, accessibility pass, and an HOS explainer panel. Recording kit (T8) comes LAST because it
narrates the frozen feature set.


## Scope boundary
ALL work happens inside `c:\projects\assessments\spotter2` only. Do not touch `..\spotter`.

## Current focus
T7 DEPLOYED AND LIVE. Backend `https://spotter2-eld-api-rose.vercel.app` (health 200, plan 200
in 6s), frontend `https://spotter2-eld-web.vercel.app` (200, bundle carries the API URL).
Now: refactor + optimise pass (T13), driven by the test suites.

## T13 refactor programme (verify after every step)
Baseline: `backend/eld` 52/52 OK (`manage.py test eld`), `verify_contract.py` 633 checks.
Backend:
1. `geocoding._LruCache` - add a `threading.Lock`; it is already shared by the reverse-geocode
   worker pool and OrderedDict mutation is not thread-safe.
2. `planner.plan()` - geocode current/pickup/dropoff in PARALLEL with the ThreadPoolExecutor
   idiom already used in `_label_segments` (saves ~2 serial round-trips; live call is 6s).
3. `planner._summary` + `plan_trip` - replace the literal `70.0`/`"70 hours / 8 days"` with
   `request.rules.cycle_limit_hours` / `cycle_days` (the field already exists on HosRules).
4. `serializers.MAX_CYCLE_HOURS` - derive from `DEFAULT_RULES.cycle_limit_hours`.
5. `views.py` - health `cycle` label from the rules; add `TripPlanRequest.from_validated()`
   to kill the field-by-field mapping; name the places-search limit constants.
Frontend:
6. `format.js` - de-duplicate the minutes/clock helpers.
7. `App.jsx` - extract the theme persistence into a `useTheme` hook.
Then: redeploy both projects and re-verify live end to end.

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
- `playwright-parallel` browser sessions - the MCP writes its output dir into
  `C:\Program Files\Microsoft VS Code\.playwright-mcp\` which is not writable (EPERM). Use
  `puppeteer-core` + Edge (the proven `capture-video.mjs` pattern) for any headless capture.
- Fetching eCFR.gov - it serves a CAPTCHA bot wall. Use law.cornell.edu for CFR text.

## Next steps
1. **T7 only** - push the repo and deploy. Blocked on: which remote (public
   `spotter2-eld-trip-planner`, private same name, public `spotter-eld-trip-planner`, or
   local-only) and on credentials (no Vercel/Docker token on disk; `gh` is authed as
   `amar-cbre`).
2. The user records their own Loom against `docs/recording/voiceover-script.md` and
   `docs/video/spotter2-loom-reference.mp4`.

## Everything else is done and verified
- T1-T6, T9-T12, T8 complete. `specs/submission-ranking/tasks.md` has the checklist and a
  table of the seven bugs found by testing rather than reasoning.

## Headline find (worth remembering)
The autocomplete offered **state codes for city queries** - typing "Nashville" returned
`TN`, `GA`, `IN`, `AR` and no Nashville. Picking one geocoded to the middle of Tennessee, so
the most natural user input produced a nonsense route. Root cause: Photon leaves `city`
empty when the match *is* the city, so the label degraded to the bare state. Fixed with
`_PLACE_RANK` + recovering the name from `props["name"]`, plus 7 regression tests in
`backend/eld/tests/test_geocoding.py`.
