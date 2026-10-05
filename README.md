# ELD Trip Planner (v2)

Give it where the truck is now, a pickup, a drop-off and how many
hours are already used on the 70-hour cycle, and it returns:

- a legal **truck route** on a map, with every required stop pinned at the mile it happens,
- a filled-out **FMCSA daily log sheet for every calendar day** of the trip,
- a **turn-by-turn instruction list** for the whole route - maneuver, distance, duration and
  running mileage per step,
- a printable **PDF of the sheets**, one landscape page per day.

- **Backend** - Django 5.2 + DRF. Stateless: every plan is computed per request, so it
  deploys to serverless or a container with no database.
- **Frontend** - Vite + React 18 + Leaflet over OpenStreetMap raster tiles. Light and dark
  themes; the log sheet stays white in both, because it is a paper form.
- **Accuracy** - the drawn sheet carries all eleven elements 49 CFR 395.8(d) requires, and
  the header says which time base the grid is on.
- **Walkthrough video** - [`docs/video/walkthrough.mp4`](docs/video/walkthrough.mp4)
  (4:00, 1920x1080, burned-in subtitles, `.srt` sidecar).

## How it works

1. **Geocode** - the three locations resolve through Nominatim, with live type-ahead in
   the form (`GET /api/v1/places/?q=`).
2. **Route** - OSRM's demo server returns the road route. The polyline is interpolated by
   distance, so any mile marker maps back to a real coordinate for stop placement.
3. **Simulate hours of service** - `HosSimulator` walks the route leg by leg. Before each
   driving chunk it asks what the law requires next, then drives only as far as the
   tightest of the five caps allows.
4. **Build the logs** - a second pass slices the simulated duty segments into 24-hour
   grids, clipping each day at midnight, and renders one log sheet per day with brackets,
   numbered remark flags, per-line totals and the seven-day recap.

Every external dependency is keyless and free: OSRM (routing), Nominatim (geocoding),
Photon (reverse geocoding), OpenStreetMap tiles (map).

## Hours-of-service rules modelled

Property carrier, 70 hours / 8 days, no adverse driving conditions:

| Rule | Value |
| --- | --- |
| Driving limit | 11 hours per shift |
| On-duty window | 14 hours per shift |
| Break | 30 min after 8 hours of cumulative driving |
| Reset | 10 consecutive hours off duty |
| Cycle | 70 hours / 8 days, 34-hour restart to clear it |
| Fuel | at least every 1,000 miles |

Fixed duty events: 30-min pre-trip, 60-min pickup, 60-min drop-off, 30-min post-trip,
30-min fuel stop. A break and an imminent fuel stop are merged into a single stop when the
remaining fuel distance falls inside the break window.

**Assumption:** all times are treated as naive local time at the home terminal.

## Running it locally

### Backend

```bash
python -m venv .venv                      # from the repo root
.venv\Scripts\activate                    # Windows;  source .venv/bin/activate elsewhere
pip install -r backend/requirements.txt
cd backend
python manage.py runserver 8090
```

The API is then on `http://127.0.0.1:8090`. Try `GET /` for the endpoint index.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/health/` | liveness probe |
| `GET /api/v1/places/?q=Chicago,IL` | place search for the form |
| `POST /api/v1/plan/` | the whole plan: route, stops, summary, log sheets |

### Frontend

```bash
cd frontend
npm install
npm run dev                                  # http://127.0.0.1:5173
```

In development `vite.config.js` proxies `/api/*` to `http://127.0.0.1:8090`, so run the
backend on **8090** (as above) and leave `VITE_API_BASE_URL` unset. For a production build
set it to the deployed API origin (see `frontend/.env.example`).

## Tests

```bash
cd backend
python manage.py test eld                    # 52 tests, fully offline - no network
python scripts/verify_contract.py            # 633 assertions against a real 672-mile trip

cd ../frontend
npm run lint                                 # ESLint, zero errors
npm run build
```

The offline suite pins each individual rule (the 11 hours, the 14, the break, the reset,
the fuel interval, the cycle look-ahead) plus the geocoder ranking, which is what stops a
bare "Nashville" from being offered as the state abbreviation `TN`. `verify_contract.py` is
the end-to-end check: it asserts the shape and arithmetic of a real two-day trip, including
that both log sheets total exactly 24:00 and that the duty lines close the grid.

## The walkthrough video

The video is generated, not screen-recorded - which is why the code is pixel-crisp and the
subtitles can never drift out of sync with the narration.

```bash
python docs/video/make_video.py              # render frames + encode the MP4
python docs/video/make_video.py --frames     # frames only, for inspecting layout
python docs/video/make_video.py --skip-render  # re-encode using the existing frames
```

- `docs/video/make_video.py` holds the shot list (`SHOTS`) and the caption text (`CUES`).
  Those two tables are the single source of truth for the video, the burned-in captions and
  the `.srt` sidecar.
- `docs/video/render.py` draws each 1920x1080 frame as HTML - the wallpaper backdrop, the
  VS Code window with real gutter numbers and syntax highlighting, the browser chrome, the
  captions - and headless Edge screenshots it.
- The app screenshots in `docs/video/assets/app/` were captured from the running app by
  `frontend/scripts/capture-video.mjs` (`cd frontend && npm run capture`). The browser
  driver is a declared devDependency, so a fresh clone can rebuild every asset.
- ffmpeg concatenates the stills and muxes the `.srt` as a soft `mov_text` track; the script
  then ffprobes its own output and fails if the duration, resolution or subtitle track is
  wrong.

## The recording kit

The brief asks for a **3-5 minute Loom covering the app and the code**. The rehearsal
material for it lives here:

- [`docs/recording/voiceover-script.md`](docs/recording/voiceover-script.md) - 22 beats with
  timecodes, the exact words to say, what is on screen at each one, and what to cut first if
  you run long.
- [`docs/video/loom-reference.mp4`](docs/video/loom-reference.mp4) - the
  same 22 beats as a Loom-style reference: webcam bubble, chapter tag, elapsed clock, a
  progress bar, and the narration as a teleprompter line. **4:10**, inside the 5-minute cap.
  It is a target to record against, not the submitted video.

```bash
python docs/video/make_reference.py                # render frames + encode
python docs/video/make_reference.py --skip-render  # re-encode using existing frames
```

The beat table in `docs/video/make_reference.py` and the voiceover script are kept in step
with each other, so a line change moves its timecode in both.

## Deployment

Nothing needs a database or a paid key. Two pieces, deployed separately:

**Backend** - either route:

- **Render** - commit `render.yaml` and create a Blueprint. It builds `backend/` and starts
  `gunicorn config.wsgi:application`; `gunicorn` is pinned in `backend/requirements.txt`.
- **Docker** - `docker build -t eld-trip-planner . && docker run -p 8000:8000 spotter-eld`.
  Works anywhere that runs containers (Fly.io, Railway, Cloud Run).
- **Vercel (serverless)** - push `backend/`. Vercel's Django preset resolves the app from
  `WSGI_APPLICATION`, so no `rewrites` are needed - a catch-all rewrite passes `/api/index.py`
  through as the request path and 404s every route. `backend/vercel.json` only raises the
  function timeout to 60 s, and `backend/api/index.py` exposes the same WSGI callable as `app`
  for runtimes that look for that name.

**Frontend** - deploy `frontend/` to Vercel; `frontend/vercel.json` is already configured
for Vite with an SPA rewrite. Set `VITE_API_BASE_URL` to the backend's `/api/v1` origin and
make sure the backend's `CORS_ALLOW_ALL_ORIGINS` (or an explicit allow-list) covers it.

## Repository layout

```
backend/               Django project
  config/              settings, urls, wsgi/asgi
  eld/                 the app under test
    services/          http, geocoding, routing, hos (the simulator), logs, planner
    tests/             offline unit suite - no network, no fixtures
  scripts/             smoke_plan.py, verify_contract.py (end-to-end contract check)
  api/index.py         WSGI shim for Vercel's Python runtime
frontend/              Vite + React app
  src/components/      one component per panel
  src/*.js             api, format, markers, logHeader, useTheme
  scripts/             capture-video.mjs (rebuild the video assets), verify-ui.mjs
docs/
  reference/           the source material this was built against
  screens/             stills used in the write-up
  recording/           the voiceover script for the Loom
  video/               the generators plus the rendered MP4s
specs/                 ranking research, spec and task list
memory-bank/           working state carried between sessions
```

Naming: Python modules and functions `snake_case`, classes `PascalCase`, constants
`UPPER_SNAKE`; React components `PascalCase.jsx`, hooks `useX.js`, other modules camelCase
`.js`; Markdown and asset filenames kebab-case. Everything is UTF-8.
