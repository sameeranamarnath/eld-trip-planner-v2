# Voiceover script — Spotter ELD walkthrough (target 4:10, limit 5:00)

The brief asks for **3–5 minutes** covering *the app and the code*. This script lands at about
**4 minutes 10 seconds** of screen time, which leaves ~50 seconds of headroom for a natural
speaking pace. Every timecode below matches the reference video in this folder, so you can play
the reference and read along.

**Pace:** ~150 words/minute. The rule that keeps you inside 5 minutes: if you fall behind a
timecode, cut the parenthetical clauses first, never the numbers.

---

## Before you record

| | |
| --- | --- |
| **Backend** | `cd backend` then `..\spotter2\Scripts\python.exe manage.py runserver 8090` |
| **Frontend** | `cd frontend` then `npm run dev` — open `http://127.0.0.1:5173` |
| **Trip to use** | Green Bay, WI → Chicago, IL → Nashville, TN, cycle 0 h |
| **Why that trip** | 672 mi, 2 log sheets, exactly one 10-hour reset. It exercises every rule without being slow to plan. |
| **Window** | Maximise the browser. 1440x900 or larger. Close other apps. |
| **Loom settings** | Camera bubble **bottom-left**, size medium. "Screen only" plus camera. Record the **whole screen** or just the browser — hide your bookmarks bar either way. |
| **Do these first** | Type the three cities once so the geocoder is warm, then **clear the form** before you hit record. A cold first plan takes noticeably longer. |
| **Have ready** | A second tab open on the repo root so the code segment is one click away. |

---

## The script

### 1 — 00:00 · 9s · Landing page
> Hi, I'm Amar. This is **Spotter ELD** — a Django and React app that takes four trip inputs and
> returns a legal route plus a filled-out FMCSA daily log for every day of the trip.

### 2 — 00:09 · 13s · Form, filled in
> The four inputs are exactly what the brief asks for: current location, pickup, drop-off, and
> hours already used in the seventy-hour, eight-day cycle. Everything else on this screen is
> optional header detail for the paper form.

### 3 — 00:22 · 11s · Type "Nashville" in the drop-off field
> Locations autocomplete from OpenStreetMap, so you're choosing a real dispatchable city. I rank
> city and town results above counties and states, because "the middle of Tennessee" is not a
> place a truck can be sent to.

### 4 — 00:33 · 10s · Open "Add departure time & log header"
> Optional departure time, and the driver and carrier fields — driver number, tractor and
> trailer, shipper, commodity — so the drawn sheet matches the form it replaces.

### 5 — 00:43 · 7s · Click "Build route & ELD logs" (spinner)
> Planning here is pure computation with no database, which is why the backend deploys anywhere
> as a stateless function.

### 6 — 00:50 · 15s · Summary tiles
> Six hundred and seventy-two miles, two log sheets, one ten-hour reset. The summary tiles are
> the whole plan at a glance: driving hours, cycle hours used, fuel stops, breaks and rests.

### 7 — 01:05 · 12s · Map
> The route comes from OSRM over OpenStreetMap tiles — both free and keyless. Every stop, rest
> and fuel stop is placed on the route itself, not offset next to it.

### 8 — 01:17 · 12s · Stops list
> Each stop is a real duty-status change with an arrival time, a duration and a mile marker, and
> it's the same data the log grid is drawn from. There's one source of truth.

### 9 — 01:29 · 17s · Route instructions tab
> Route instructions are their own output in the brief, so they're their own tab: fifty-seven
> turn-by-turn steps with maneuvers, distances, durations and running mileage. OSRM returns
> machine-readable maneuver codes, so the backend writes the sentences.

### 10 — 01:46 · 15s · Daily log sheets, day 1 (zoom the grid)
> Now the part that matters. Four duty-status lines on a fifteen-minute grid, brackets where the
> truck sat still, a numbered remark flag at every status change with the city and state,
> per-line totals, and the seventy-hour recap at the bottom.

### 11 — 02:01 · 12s · Scroll to day 2
> Longer trips just add sheets. Day two totals twenty-four hours again, and carries the recap
> forward so the cycle maths never gets lost between pages.

### 12 — 02:13 · 9s · Logbook toolbar, hover "Print / save as PDF"
> Every sheet prints or saves as a PDF at one clean landscape page per day — real vector text,
> not a screenshot of a table.

### 13 — 02:22 · 9s · Click "HOS rules" in the header
> The rules dialog lists every limit the planner enforces with the paragraph each one comes
> from: the eleven-hour limit, the fourteen-hour window, the thirty-minute break, the 70-hour
> cycle.

### 14 — 02:31 · 7s · Toggle the theme to dark
> And a dark theme. The log sheet deliberately stays white in both, because it's paper.

### 15 — 02:38 · 14s · Code: `backend/eld/services/hos.py`
> Now the code. The HOS engine is deliberately pure: give it a route and a start time and it
> returns duty segments. Every tunable rule lives in one dataclass at the top of the file, so
> the regulation can be read against it line by line.

### 16 — 02:52 · 13s · Code: `backend/eld/services/logs.py`
> A separate builder slices that stream into one sheet per calendar day. Keeping it separate
> means the grid arithmetic — totals, remark flags, the seventy-hour recap — is unit-testable
> without ever opening a browser.

### 17 — 03:05 · 11s · Code: `backend/eld/services/routing.py`
> The router turns OSRM's machine-readable maneuver codes into plain-language instructions, and
> rescales the polyline so the mile markers agree with the provider's own distance.

### 18 — 03:16 · 12s · Code: `frontend/src/components/LogSheet.jsx`
> The sheet itself is SVG generated in React, which is why it prints crisply, and why the grid,
> the brackets and the numbered remark flags are all real vector output rather than an image.

### 19 — 03:28 · 12s · Code: `backend/eld/tests/test_hos.py`
> Fifty-two offline tests cover the HOS arithmetic and the geocoding ranking. On top of that a
> contract script replays a 672-mile trip and asserts 633 fields against the running stack.

### 20 — 03:40 · 9s · Code: `frontend/vite.config.js`
> There are no API keys anywhere — OSRM, Nominatim and Photon all run keyless, so a fresh clone
> works on the first try.

### 21 — 03:49 · 10s · Dark logbook view
> So the app plans a legal trip, draws the logs, and hands them to a driver as a PDF that looks
> like the form it replaces.

### 22 — 03:59 · 11s · Back to the landing page
> The repository and the live link are in the description below. Thanks for watching.

---

## If you are running long

Cut in this order — each is safe to lose:

1. Beat 4 (the optional header fields).
2. Beat 14 (dark theme) and beat 20 (keyless providers).
3. Trim every parenthetical clause. Keep every **number**: 672 miles, 57 steps, 2 sheets, 52
   tests, 633 assertions. Numbers are what make it credible.

## If you are running short

Add, in this order:

1. Click **Coast-to-coast · 4 log sheets** on the empty state and show that a long trip produces
   four sheets without you touching anything.
2. On the log sheet, point at the bracket on the driving line and explain that it marks a
   stationary on-duty block, which is why the grid line is drawn as a bracket and not a bar.
3. Show `?current=..&pickup=..&dropoff=..&run=1` in the URL bar — plans are deep-linkable, which
   is how I generated the reference frames.

## Delivery notes

- Say the **numbers**, don't read the screen. The viewer can read.
- Zoom the browser to ~125% for the log-sheet beats; the grid detail is the strongest visual.
- Pause half a second after each click — the plan takes a moment and dead air reads as lag.
- Do one dry run of beats 1–5 to warm the geocoder before the real take.

