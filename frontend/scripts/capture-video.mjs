/**
 * Capture the real, running app for the walkthrough video.
 *
 * Uses puppeteer-core against the Edge already on disk (no browser download).
 * The app is deep-linkable, so results are reproducible:
 *   /?current=..&pickup=..&dropoff=..&cycle=..&run=1[&tab=logs]
 *
 * Usage (from frontend/):  node scripts/capture-video.mjs
 * Output: docs/video/assets/app/*.png  and  docs/video/assets/plan.json
 */

import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'

const HERE =
  typeof __dirname !== 'undefined' ? __dirname : dirname(fileURLToPath(import.meta.url))
const OUT = resolve(HERE, '../../docs/video/assets')
const APP = process.env.APP_URL || 'http://127.0.0.1:5173'
const EDGE =
  process.env.EDGE_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

const VIEW = { width: 1600, height: 900, deviceScaleFactor: 1 }
const sleep = (ms) => new Promise((done) => setTimeout(done, ms))

const TRIP = { current: 'Green Bay, WI', pickup: 'Chicago, IL', dropoff: 'Nashville, TN', cycle: 12 }

async function main() {
  mkdirSync(resolve(OUT, 'app'), { recursive: true })
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: true,
    args: ['--force-device-scale-factor=1', '--disable-lcd-text'],
  })

  const page = await browser.newPage()
  await page.setViewport(VIEW)

  let plan = null
  page.on('response', async (response) => {
    if (response.url().includes('/api/v1/plan/') && response.request().method() === 'POST') {
      try {
        plan = await response.json()
      } catch {
        /* ignore: only the successful payload matters */
      }
    }
  })

  const shot = async (name) => {
    await sleep(220)
    await page.screenshot({ path: resolve(OUT, 'app', `${name}.png`) })
    console.log(`  shot ${name}`)
  }
  const elementShot = async (name, selector) => {
    const handle = await page.$(selector)
    if (!handle) {
      console.warn(`  ! ${selector} not found, skipping ${name}`)
      return
    }
    await sleep(150)
    await handle.screenshot({ path: resolve(OUT, 'app', `${name}.png`) })
    console.log(`  shot ${name}`)
  }
  const clearAndType = async (selector, text) => {
    await page.click(selector, { clickCount: 3 })
    await page.keyboard.press('Backspace')
    await page.type(selector, text, { delay: 55 })
  }
  const pickSuggestion = async (match) => {
    await page.waitForSelector('.suggestions .suggestion', { timeout: 15000 })
    await sleep(240)
    const { texts, index } = await page.$$eval(
      '.suggestions .suggestion',
      (nodes, wanted) => ({
        texts: nodes.map((node) => node.textContent),
        index: (() => {
          const hit = nodes.findIndex((node) => node.textContent.includes(wanted))
          if (hit !== -1) return hit
          // Fall back to the longest label: city hits beat state abbreviations.
          return nodes.reduce(
            (best, node, at) =>
              node.textContent.length > nodes[best].textContent.length ? at : best,
            0,
          )
        })(),
      }),
      match,
    )
    if (!texts[index].includes(match)) {
      console.warn(`  ! no suggestion matched ${match}; picked ${JSON.stringify(texts[index])}`)
    }
    await page.click(`.suggestions .suggestion:nth-child(${index + 1})`)
    await sleep(340)
  }
  const clickByText = async (text) => {
    const clicked = await page.$$eval(
      'button',
      (nodes, wanted) => {
        const hit = nodes.find((node) => node.textContent.includes(wanted))
        if (hit) hit.click()
        return Boolean(hit)
      },
      text,
    )
    if (!clicked) throw new Error(`no button containing ${JSON.stringify(text)}`)
  }


  // ---- 1. the form, typed out live -------------------------------------
  await page.goto(APP, { waitUntil: 'networkidle2' })
  await sleep(700)
  await shot('01-landing-empty-state')

  await clearAndType('#current_location', 'Green Bay')
  await page.waitForSelector('.suggestions .suggestion', { timeout: 15000 })
  await sleep(400)
  await shot('02-autocomplete-dropdown')
  await pickSuggestion('Green Bay')

  await clearAndType('#pickup_location', 'Chicago')
  await pickSuggestion('Chicago')
  await clearAndType('#dropoff_location', 'Nashville')
  await pickSuggestion('Nashville')

  await clearAndType('#cycle_used_hours', String(TRIP.cycle))
  await sleep(200)
  await shot('03-form-filled')

  // Open the optional panel and pin the departure to a 06:30 roll.
  await clickByText('Add departure time & log header')
  await sleep(400)
  const departure = await page.$('#departure_time')
  if (departure) {
    await page.evaluate((node) => {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value',
      ).set
      setter.call(node, `${node.value.slice(0, 10)}T06:30`)
      node.dispatchEvent(new Event('input', { bubbles: true }))
      node.dispatchEvent(new Event('change', { bubbles: true }))
    }, departure)
  }
  await sleep(250)
  await shot('03b-departure-and-header')

  // ---- 2. submit and wait for the plan ---------------------------------
  await clickByText('Build route & ELD logs')
  await shot('04-loading-spinner')
  await page.waitForSelector('.map-canvas', { timeout: 120000 })
  await page.waitForSelector('.stops .stop', { timeout: 120000 })
  await sleep(4500) // let the OSM tiles settle

  await page.evaluate(() => window.scrollTo(0, 0))
  await shot('05-route-overview')
  await elementShot('06-map-canvas', '.map-shell')

  await page.evaluate(() => {
    document.querySelector('.stops')?.scrollIntoView({ block: 'center' })
  })
  await sleep(400)
  await shot('07-stops-top')
  await page.evaluate(() => window.scrollBy(0, 620))
  await sleep(400)
  await shot('08-stops-more')

  if (await page.$('.stats')) {
    await page.evaluate(() => document.querySelector('.stats')?.scrollIntoView({ block: 'center' }))
    await sleep(400)
    await elementShot('09-summary-stats', '.stats')
  }

  // ---- 3. the daily log sheets -----------------------------------------
  await clickByText('Daily log sheets')
  await page.waitForSelector('.log-sheet', { timeout: 30000 })
  await sleep(1400)
  await shot('10-logbook-top')
  await elementShot('11-sheet-day1', '.log-sheet')

  const sheets = await page.$$('.log-sheet')
  if (sheets.length > 1) {
    await page.evaluate((node) => node.scrollIntoView({ block: 'start' }), sheets[1])
    await sleep(700)
    await elementShot('12-sheet-day2', '.log-sheet:nth-of-type(2)')
    await shot('13-sheet-day2-in-context')
  }

  // ---- 4. dump the payload the video needs later -----------------------
  if (plan) {
    writeFileSync(resolve(OUT, 'plan.json'), JSON.stringify(plan, null, 2), 'utf8')
    console.log(`  plan.json: ${plan.logs.length} sheets, ${plan.stops.length} stops`)
  } else {
    console.warn('  ! no plan captured')
  }

  await browser.close()
  console.log('capture complete')
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
