# Tasks — ordered, each with its own proof

Legend: [ ] open, [x] done. Each task names the files it touches and the command that proves it.

## Phase 1 — Close the accuracy + coverage gaps

- [x] **T1 - Route instructions, backend.** DONE. `routing.py` sends `steps=true` and
  `_collect_steps()` flattens OSRM maneuvers into `RouteStep`s with `cumulative_miles`;
  new `describe_step()` writes the instruction prose (OSRM returns only `{type, modifier}`).
  Verified live: 57 steps over 2 legs, real street names, monotonic mileage.
- [x] **T2 - Route instructions, frontend.** DONE. `Directions.jsx` + 9 maneuver glyphs in
  `Icon.jsx` + a third tab. Verified: 57 rows render with glyph, distance, duration, mile.
- [x] **T3 - 395.8(d) completeness.** DONE, all 11 elements. Added `main_office_address` and
  `period_start_time` to `DEFAULT_HEADER`, the serializer and the form; the sheet subtitle now
  states the midnight period start and the home-terminal time base (f)(8). New test
  `test_sheet_carries_the_49_cfr_395_8_d_elements`. Suite 45/45.
- [x] **T4 - Print / Save as PDF.** DONE. Added `@page { size: letter landscape }`, colour
  preservation, and a `break-before` rule; wrapped `SummaryPanel` in `no-print`.
  Verified: 792x612 pt, no horizontal overflow, **exactly 2 pages for 2 sheets**.
- [x] **T-extra - tab deep-linking.** DONE. The `?tab=` param only understood `logs`, so any
  other value silently fell back to route. Now validated against `TABS`.

## Phase 2 — Engineering signals reviewers look for

- [ ] **T5 - Lint + build scripts.**
  Files: `frontend/package.json`, eslint flat config.
  Add `lint`. Do not introduce a toolchain that fights the existing code.
  Prove: `npm run lint` exit 0, `npm run build` exit 0.

- [ ] **T6 - Re-verify the whole suite after the above.**
  Prove: `python manage.py test eld` 45/45 green, `verify_contract.py` green,
  `python -c "import api.index"` OK.

## Phase 2b — Differentiating polish (user-approved scope)

- [ ] **T9 - HOS explainer panel.** A "HOS rules" dialog explaining each limit and citing
  where it is applied. A rival ships this; it reads as domain mastery.
- [ ] **T10 - Dark mode.** App chrome only - the log sheet stays white on purpose, because
  the artifact is a paper form. Needs the hardcoded chrome colours moved onto the existing
  `--*` custom properties.
- [ ] **T11 - Mobile / narrow layout.** The two-column layout and the 56-column grid need a
  plan below ~900px.
- [ ] **T12 - Accessibility pass.** Landmarks, labels, focus-visible rings, `aria-live` for
  the plan result, contrast check.

## Phase 3 — Deliverables

- [ ] **T7 - Push the repo and document deploy.**
- [ ] **T8 - Recording kit.** LAST - it narrates the frozen feature set.

## Final state

- [x] **T1** route instructions (backend) - DONE, 57 live steps.
- [x] **T2** route instructions tab - DONE, verified rendering.
- [x] **T3** all 11 elements of 49 CFR 395.8(d) on the drawn sheet - DONE.
- [x] **T4** print / Save as PDF, one landscape page per day - DONE, verified 2 pages.
- [x] **T5** `npm run lint` clean + `npm run build` - DONE.
- [x] **T6** full re-verify: 52/52 tests, 633/633 contract assertions - DONE.
- [x] **T9** HOS rules dialog with CFR citations - DONE.
- [x] **T10** dark theme (log sheet deliberately stays white) - DONE.
- [x] **T11** narrow-phone layout, no horizontal overflow - DONE.
- [x] **T12** accessibility: focus rings, aria-live, Escape-to-close dialog - DONE.
- [x] **T8** recording kit: 22-beat voiceover script + 4:10 Loom-style reference video - DONE.
- [ ] **T7** push the repo + deploy - BLOCKED on the remote decision and credentials.

## Found and fixed while doing the above

These were not in the original plan; each was found by testing rather than reasoning.

| Bug | Impact | Fix |
| --- | --- | --- |
| Autocomplete offered state codes for city queries (`Nashville` -> `TN`) | The most natural user input produced unusable options, and picking one geocoded to the middle of a state | `_PLACE_RANK` weights + recover the place name Photon puts in `name`; 7 regression tests |
| `?tab=` only understood `logs` | Deep links to any other tab silently fell back to route | Validate the parameter against `TABS` |
| README documented Vite's proxy as port 8000 | Following the README gave ECONNREFUSED, surfacing as a 500 in the browser | Corrected to 8090; pinned `host: '127.0.0.1'` in `vite.config.js` |
| `puppeteer-core` was installed `--no-save` | A fresh clone could not run the capture scripts at all | Declared it as a devDependency |
| 1.5 MB of vendored React DevTools in `scripts/.render-check.*` | Dead weight in the repo, referenced by nothing | Deleted |
| Printing produced 3 pages for 2 sheets | A blank trailing page, and the summary card stole page 1 | `break-before` on subsequent sheets; summary wrapped in `no-print` |
| Headless Edge reports a dark colour scheme | Rebuilding the video silently produced dark "light" shots | Pinned `prefers-color-scheme: light` during capture |

- Starting Django on 8000: `vite.config.js` proxies to **8090**. Wrong port = ECONNREFUSED,
  which the browser reports as a 500 from the dev server, not as a failed API call.
- `playwright-parallel` MCP here: writes its output dir under `Program Files` -> EPERM.
  Use `puppeteer-core` + Edge.
- `break-after: page` on every sheet: leaves a trailing blank page. Use
  `.log-sheet + .log-sheet { break-before: page }`.
