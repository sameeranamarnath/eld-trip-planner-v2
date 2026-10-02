# Research — is this submission the best, and against what?

Question this file answers: **what does "best" mean for this assessment, and where do we
actually stand?** Everything below is evidence, not opinion.

## 1. The assessment's own words (extracted from `new-full-stack-dev-assessment.docx`)

Deliverables, verbatim:

1. Create a live hosted version (can use Vercel.app)
2. Create a **3-5 minute loom** going over your app **and your code**
3. Share the Github code

Grading signals, verbatim:

- "We will test the hosted version for **accuracy** and the accuracy must be up to standards"
- "**UI and UX must be good.** Pay attention to good design and aesthetics, **it can compensate
  for some inaccuracies in output**"

Objective: "takes trip details as inputs and outputs **route instructions** and draws ELD logs
as outputs".

Inputs: current location, pickup location, dropoff location, current cycle used (hrs).
Outputs: map with route + stops/rests information (must use a **free** map API); **daily log
sheets filled out — "need to draw on the log and fill out the sheet"**, multiple for longer trips.
Assumptions: property-carrying, 70 hrs/8 days, no adverse conditions, fuel at least every
1,000 mi, 1 hour for pickup and drop-off.

Two things follow that are easy to miss:

- "Route instructions" is a **named output**, separate from the map. A stops list is not
  instructions.
- "Draw on the log and fill out the sheet" means the artifact must look like the real form.
  A table of hours does not satisfy it.

## 2. The accuracy yardstick: 49 CFR 395.8(d)

Because accuracy is graded, the yardstick is the regulation, not taste. §395.8(d) requires
these elements **in addition to the grid**:

| # | Required element | Status on our sheet |
| --- | --- | --- |
| 1 | Date | present |
| 2 | Total miles driving today | present |
| 3 | Truck or tractor and trailer number | present |
| 4 | Name of carrier | present |
| 5 | Driver's signature / certification | present |
| 6 | **24-hour period starting time** (e.g. midnight, noon) | **MISSING** |
| 7 | **Main office address** | **MISSING** |
| 8 | Remarks | present |
| 9 | Name of co-driver | present |
| 10 | Total hours (far right edge of grid) | present |
| 11 | Shipping document number(s), or shipper and commodity | present |

**9 of 11.** The two gaps are cheap to close and are exactly the kind of omission an accuracy
checker finds.

Also relevant:

- §395.8(h): a continuous line is drawn between the appropriate time markers for each status;
  the city/town/village **and State abbreviation** must be recorded at **each change of duty
  status**. We comply.
- §395.8(f)(8): the record must be prepared and maintained "using the time standard in effect
  at the driver's **home terminal**". We model naive local time at the home terminal and
  document it - a documented assumption, not a defect - but the sheet should *say* "home
  terminal time" so a reviewer sees it rather than having to read the README.
- §395.8(g) note: the specimen grid "reflects the midnight to midnight 24 hour period".

## 3. The HOS numbers we are graded on

From 49 CFR 395.3 / FMCSA summaries. Property-carrying, no adverse conditions:

| Rule | Value | Our implementation |
| --- | --- | --- |
| Driving limit | 11 h per duty period | `max_drive_hours=11.0` |
| On-duty window | 14 consecutive h, breaks do not extend it | `max_window_hours=14.0` |
| Break | 30 min after 8 h cumulative **driving** (2020 rule) | `break_after_drive_hours=8.0` |
| Reset | 10 consecutive h off duty | `reset_off_hours=10.0` |
| Cycle | 70 h / 8 days | `cycle_limit_hours=70.0`, `cycle_days=8` |
| Restart | 34 h clears the cycle | `restart_hours=34.0` |
| Fuel | at least every 1,000 mi | `fuel_interval_miles=1000.0` |

These all match. The break rule in particular keys on **driving** time, not on-duty time, which
is the 2020 amendment and a common mistake.

## 4. Competitive landscape (same or similar assessment)

Found by search; several are almost certainly other candidates for this exact brief. Method:
DOM/feature fingerprinting via a headless browser plus README review. **Competitor scores in
`spec.md` are estimates from that fingerprinting, not a code review.**

| Submission | Stack | Notable features | Weaknesses observed |
| --- | --- | --- | --- |
| **ours** | Django/DRF + Vite/React + Leaflet | keyless live OSRM routing (no key, no stub), 43 offline tests + 633-assertion contract test, full FMCSA grid sheet, stateless (no DB) | **no route instructions**, no print/PDF, 9/11 form elements, **not deployed/pushed**, no lint script |
| `eld-trip-planner-henna` | "Django REST · React · MUI · Leaflet" | trip start time on the form, driver/carrier details incl. **home terminal address**, "HOS rules" explainer, 3 examples, rule cards | fewer inputs worked through; unknown test depth |
| `indureddy08-d/ELD-Trip-Planner` | Django + React | **step-by-step route instructions with HOS context**, HOS status badge, **Print / Save-as-PDF (one landscape page per day)**, 4 demo scenarios, live Session Tracker, lint script | **needs an `ORS_API_KEY`; falls back to a lookup table without it** - i.e. fabricated distances when unkeyed |
| `eld-road-trip-planner` (RoadLog) | React | clean minimal landing + form, assumptions block | only 4 inputs, single button, no visible richness |
| `trip-route-optimizer-6mgy` | React | clean minimal form | same as above |
| `openeld.vercel.app` | marketing site | markets an "AI co-driver" Q&A, self-hosting, pricing | it is a **landing page** for a product, not a working planner demo |

The strategic read:

- Our **engineering** story is the strongest of the group (real routing that never fabricates,
  thick tests, stateless deploy, generated video).
- Our **requirement coverage** is behind two rivals on one explicit named output (route
  instructions) and one obvious practical expectation (print/PDF).
- Our **deliverables** score is currently the worst, simply because the live URL and the repo
  do not exist yet. That is 15% of the rubric sitting on the floor.

## 5. Ruled out / rejected

- **AI "co-driver" chat (OpenELD)** - needs a paid LLM key, breaks the "no API keys" property
  that is currently a genuine advantage, and the brief does not ask for it.
- **ORS-style keyed routing** - strictly worse than keyless OSRM for this brief.
- **Lookup-table "fallback" routing** - fabricating distances to appear to work is worse than
  failing loudly. Do not copy this from the competitor.
