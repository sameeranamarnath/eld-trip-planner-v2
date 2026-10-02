# Spec — make this the best submission in the field

## Problem

The brief is graded on accuracy, requirement coverage, UI/UX, and three concrete deliverables.
`research.md` establishes that we are **strong but not first**: we lead on engineering quality,
trail on two explicit requirements, and are last on deliverables purely because nothing is
deployed or pushed yet.

## Definition of "best" (acceptance criteria, all testable)

| # | Criterion | Proof |
| --- | --- | --- |
| A1 | Turn-by-turn **route instructions** are a first-class output, with distance/time per step | `GET`/plan payload contains a non-empty `directions` list; UI tab renders it |
| A2 | Every one of the 11 elements in 49 CFR 395.8(d) appears on the drawn sheet | rendered sheet shows all 11, incl. 24-hour period starting time and main office address |
| A3 | Log sheets can leave the browser: **Print / Save as PDF**, one clean page per day | print CSS; each sheet prints on one landscape page |
| A4 | The sheet states the **time base** (home terminal time) | visible on the sheet |
| A5 | Engineering checks are runnable by a reviewer: backend tests, frontend build, **lint** | `npm run lint`, `npm run build`, `python manage.py test` all pass |
| A6 | No fabricated data anywhere: if routing fails, the API errors loudly | no lookup-table/stub distance fallback |
| A7 | Live hosted backend + frontend exist and are documented | deployed URLs in README |
| A8 | A 3-5 min Loom script with timeline markers exists, and a Loom-style reference video | script + reference MP4 in `docs/` |

## Non-goals (explicitly out of scope)

- No AI/LLM assistant (needs a paid key; breaks the keyless property).
- No auth, accounts, or persistence - the app is stateless by design and that is a feature.
- No database, no migrations.
- No certified-ELD compliance claims; it is a planner and stays described as one.
- No change to the HOS rule values - they already match 49 CFR 395.3 exactly.

## Decisions

**D1 - Add route instructions by turning OSRM steps back on.**
*Alternatives:* build our own geometry→maneuver synthesis; scrape another provider; omit.
*Why:* `routing.py` currently sends `"steps": "false"` and throws away data OSRM already
computes. Re-enabling it is a small, honest change and matches the brief's own wording.

**D2 - Fix the 395.8(d) gaps by adding the two missing fields, not by redesigning the sheet.**
*Alternatives:* leave them (they are minor); redesign the header.
*Why:* accuracy is graded against the regulation. Two labels close the gap for near-zero risk;
a redesign risks the working layout.

**D3 - Print support via CSS `@media print`, not a server-side PDF renderer.**
*Alternatives:* WeasyPrint/ReportLab server-side; html2canvas + jsPDF client-side.
*Why:* the sheet is already real DOM/SVG, so print CSS is the smallest correct change, adds no
dependency, and gives vector text rather than a rasterised image.

**D4 - Keep the app keyless.**
*Alternatives:* add a keyed provider for prettier routes.
*Why:* "free map API" is a stated requirement; keyless OSRM satisfies it and removes the
"works only with my key" failure mode that one competitor has.

**D5 - Deliverables (live host, Loom) are tracked but the recording is the user's.**
*Alternatives:* script a deploy; record it ourselves.
*Why:* no Vercel/Docker credentials on this machine, and the user has chosen to record.

## Current score vs target

Weights follow the brief's own emphasis. Competitor rows are estimates from `research.md` §4.

| Area | Weight | Ours now | Target | henna (est) | indureddy (est) | roadlog (est) |
| --- | --- | --- | --- | --- | --- | --- |
| Accuracy vs regulation | 30% | 8.5 | 9.5 | 8.0 | 7.5 | 7.0 |
| UI/UX & aesthetics | 25% | 9.0 | 9.5 | 8.5 | 7.5 | 7.0 |
| Requirement coverage | 20% | 7.0 | 10.0 | 8.5 | 9.5 | 6.5 |
| Deliverables | 15% | 5.0 | 9.0 | 10.0 | 10.0 | 10.0 |
| Engineering quality | 10% | 9.5 | 9.5 | 7.0 | 8.0 | 6.5 |
| **Weighted** | | **7.90** | **9.53** | 8.43 | 8.33 | 7.30 |

So the verdict is **not yet best**: 3rd of 5 on this rubric, and the two reasons are concrete
and fixable - missing route instructions plus incomplete deliverables.

## Open question for the user

Whether to stop at the requirement-traceable fixes (`tasks.md` T1-T8) or also add
differentiating polish (dark mode, mobile layout, accessibility pass, HOS explainer panel).
The polish is cheap and the brief rewards UI/UX, but it is scope beyond the requirements.
