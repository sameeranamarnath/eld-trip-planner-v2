/**
 * Headless render check for the SVG log sheet.
 *
 * Renders every daily sheet from a live plan through react-dom/server and
 * asserts the structure a reviewer would look for (grid, duty lines, remark
 * flags, totals, recap).  Writes the SVGs to scripts/out/ for eyeballing.
 *
 * Usage (from frontend/):
 *   npx esbuild scripts/render-check.jsx --bundle --platform=node --format=esm
 *     --loader:.jsx=jsx --jsx=automatic --outfile=scripts/.render-check.mjs
 *   node scripts/.render-check.mjs [apiBase]
 */

import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { renderToStaticMarkup } from 'react-dom/server'
import LogSheet from '../src/components/LogSheet.jsx'

const HERE =
  typeof __dirname !== 'undefined' ? __dirname : dirname(fileURLToPath(import.meta.url))
const API = process.argv[2] || 'http://127.0.0.1:8090/api/v1'

const payload = {
  current_location: 'Green Bay, WI',
  pickup_location: 'Chicago, IL',
  dropoff_location: 'Nashville, TN',
  cycle_used_hours: 0,
  departure_time: '2026-10-01T06:30',
  start_odometer: 142500,
  header: {
    driver_name: 'J. Driver',
    driver_number: 'SCH-4471',
    co_driver: 'N/A',
    home_terminal: 'Green Bay, WI',
    carrier: 'Spotter Freight Systems',
    tractor_number: 'T-1042',
    trailer_number: 'TR-5580',
    shipper: "Don's Paper Company",
    commodity: 'Paper products',
    load_id: 'LD-88231',
  },
}

const problems = []
let checks = 0

function check(condition, message) {
  checks += 1
  if (!condition) problems.push(message)
}

const count = (haystack, needle) => haystack.split(needle).length - 1

async function main() {
  const response = await fetch(`${API}/plan/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`plan request failed: ${response.status}`)
  const plan = await response.json()

  const outDir = resolve(HERE, 'out')
  mkdirSync(outDir, { recursive: true })

  console.log(`sheets: ${plan.logs.length}`)

  plan.logs.forEach((day) => {
    const svg = renderToStaticMarkup(LogSheet({ day }))
    const where = `day ${day.day_index}`

    check(svg.startsWith('<svg'), `${where}: did not render an <svg> root`)
    check(svg.includes('viewBox="0 0 1180 706"'), `${where}: unexpected viewBox`)
    check(svg.includes('DRIVER&#x27;S DAILY LOG') || svg.includes("DRIVER'S DAILY LOG"),
      `${where}: missing form title`)
    check(svg.includes(day.date), `${where}: missing the date`)
    check(svg.includes(day.header.carrier), `${where}: missing the carrier`)
    check(svg.includes('REMARKS'), `${where}: missing the remarks column`)
    check(svg.includes('MIDNIGHT') && svg.includes('NOON'), `${where}: missing hour captions`)
    check(svg.includes('70-HOUR / 8-DAY RECAP'), `${where}: missing the recap box`)
    check(svg.includes('MILES DRIVEN TODAY'), `${where}: missing the mileage box`)
    check(svg.includes('OFF DUTY') && svg.includes('SLEEPER BERTH')
      && svg.includes('DRIVING') && svg.includes('ON DUTY (NOT DRIVING)'),
      `${where}: missing duty-status row labels`)

    // 24 hour columns + 3 quarter-hour ticks each.
    const hourLines = count(svg, 'y2="398"')
    check(count(svg, '<line') >= 24 * 4, `${where}: expected at least 96 grid lines`)

    // One numbered flag per remark.
    const flags = (svg.match(/<circle/g) || []).length
    check(flags >= day.remarks.length, `${where}: ${flags} flags for ${day.remarks.length} remarks`)

    // Duty line strokes: one per clipped entry.
    const strokes = count(svg, 'stroke-linecap="round"')
    check(strokes === day.entries.length,
      `${where}: ${strokes} duty strokes for ${day.entries.length} entries`)

    check(svg.includes('TOTAL HOURS'), `${where}: missing the total-hours box`)
    check(svg.includes(day.total_hours_hhmm), `${where}: total hours value missing`)

    // No unresolved template artefacts.
    check(!svg.includes('undefined') && !svg.includes('NaN'),
      `${where}: render produced undefined/NaN`)

    const file = resolve(outDir, `log-sheet-day-${day.day_index}.svg`)
    writeFileSync(file, svg, 'utf8')
    console.log(
      `  day ${day.day_index}  ${svg.length.toLocaleString()} chars  ` +
        `${day.entries.length} entries  ${day.remarks.length} remarks  ->  ${file}`,
    )
  })

  console.log(`\nchecks run: ${checks}`)
  if (problems.length) {
    console.log(`FAILED (${problems.length}):`)
    problems.forEach((problem) => console.log(`  - ${problem}`))
    process.exitCode = 1
    return
  }
  console.log('LOG SHEET RENDER CHECKS PASSED')
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
