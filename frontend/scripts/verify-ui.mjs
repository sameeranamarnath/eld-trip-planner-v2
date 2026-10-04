/**
 * Headless UI smoke test: plans a trip through the real form, then checks the
 * route instructions, the printed log sheets, the theme toggle and the mobile
 * layout.
 *
 * Usage (from frontend/):  node scripts/verify-ui.mjs
 * Output: docs/video/build/verify/  (gitignored)
 */

import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'

const HERE =
  typeof __dirname !== 'undefined' ? __dirname : dirname(fileURLToPath(import.meta.url))
const OUT = resolve(HERE, '../../docs/video/build/verify')
const EDGE =
  process.env.EDGE_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const APP = process.env.APP_URL || 'http://127.0.0.1:5173'

const sleep = (ms) => new Promise((done) => setTimeout(done, ms))

/** React tracks the DOM value, so drive the native setter and fire the event. */
async function fillLocations(page, values) {
  const ids = ['current_location', 'pickup_location', 'dropoff_location']
  for (let index = 0; index < ids.length; index += 1) {
    await page.evaluate(
      (id, value) => {
        const input = document.getElementById(id)
        const setter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype,
          'value',
        ).set
        setter.call(input, value)
        input.dispatchEvent(new Event('input', { bubbles: true }))
        input.blur()
      },
      ids[index],
      values[index],
    )
  }
}

async function clickButtonByText(page, text) {
  return page.evaluate((want) => {
    const button = Array.from(document.querySelectorAll('button')).find((el) =>
      el.innerText.includes(want),
    )
    if (!button) return false
    button.click()
    return true
  }, text)
}

async function main() {
  mkdirSync(OUT, { recursive: true })
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: true,
    args: ['--force-device-scale-factor=1'],
  })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 })

  page.on('console', (msg) => {
    if (msg.type() === 'error') console.log('  console.error:', msg.text().slice(0, 200))
  })

  await page.goto(APP, { waitUntil: 'networkidle2', timeout: 60000 })
  await page.screenshot({ path: resolve(OUT, 'empty-state.png') })
  await fillLocations(page, ['Green Bay, WI', 'Chicago, IL', 'Nashville, TN'])
  await clickButtonByText(page, 'Plan trip')

  // The planner calls out to OSRM and the geocoders, so this is the slow wait.
  await page.waitForFunction(() => document.querySelectorAll('.stat').length > 0, {
    timeout: 120000,
  })
  await page.screenshot({ path: resolve(OUT, 'route-view.png') })
  await clickButtonByText(page, 'Route instructions')
  await page.waitForFunction(() => document.querySelectorAll('.direction').length > 0, {
    timeout: 60000,
  })
  await sleep(700)

  const count = await page.evaluate(() => document.querySelectorAll('.direction').length)
  console.log('direction rows rendered:', count)
  const sample = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.direction'))
      .slice(0, 6)
      .map((li) => li.innerText.replace(/\s+/g, ' ').trim()),
  )
  console.log(JSON.stringify(sample, null, 1))
  await page.screenshot({ path: resolve(OUT, 'tab-directions.png') })

  // Exercise print: switch to the log sheets and render straight to PDF.
  await page.evaluate(() => {
    const button = Array.from(document.querySelectorAll('.tab')).find((el) =>
      el.innerText.includes('Daily log'),
    )
    button?.click()
  })
  await sleep(1500)
  await page.screenshot({ path: resolve(OUT, 'tab-logs.png') })
  await page.pdf({
    path: resolve(OUT, 'logs-print.pdf'),
    preferCSSPageSize: true,
    printBackground: true,
  })
  console.log('wrote logs-print.pdf')

  // Verify the printed sheet cannot be clipped: in print emulation the viewport
  // width equals the page width, so any horizontal overflow would be cut off.
  await page.emulateMediaType('print')
  await page.setViewport({ width: 1056, height: 816, deviceScaleFactor: 1 })
  await sleep(500)
  const fit = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    sheets: document.querySelectorAll('.log-sheet').length,
  }))
  console.log('print fit:', JSON.stringify(fit))
  console.log(
    fit.scrollWidth <= fit.clientWidth
      ? 'OK: content fits the landscape page width'
      : `CLIPPED: content is ${fit.scrollWidth - fit.clientWidth}px wider than the page`,
  )
  await page.screenshot({ path: resolve(OUT, 'print-page-1.png') })

  // Back to screen media at a normal desktop size for the polish captures.
  await page.emulateMediaType(null)
  await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 })
  await sleep(400)

  const clickByLabelPrefix = async (prefix) => {
    const ok = await page.evaluate((want) => {
      const button = Array.from(document.querySelectorAll('button')).find((el) =>
        (el.getAttribute('aria-label') || '').startsWith(want),
      )
      if (!button) return false
      button.click()
      return true
    }, prefix)
    return ok
  }

  // The toggle writes data-theme onto <html>; either direction is fine.
  const themeBefore = await page.evaluate(() => document.documentElement.dataset.theme)
  const toggled = await clickByLabelPrefix('Switch to')
  await sleep(500)
  const themeAfter = await page.evaluate(() => document.documentElement.dataset.theme)
  console.log(`theme toggle clicked=${toggled} ${themeBefore} -> ${themeAfter}`)
  await page.screenshot({ path: resolve(OUT, 'theme-dark.png') })

  // Narrow phone width, on the turn list.
  await page.evaluate(() => {
    const button = Array.from(document.querySelectorAll('.tab')).find((el) =>
      el.innerText.includes('Route instructions'),
    )
    button?.click()
  })
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 })
  await sleep(700)
  const layout = await page.evaluate(() => {
    const column = document.querySelector('.logbook, .directions')
    return {
      docScrollWidth: document.documentElement.scrollWidth,
      docClientWidth: document.documentElement.clientWidth,
      hasDirections: !!document.querySelector('.direction'),
      firstColumn: column ? Math.round(column.getBoundingClientRect().width) : 0,
    }
  })
  console.log('mobile layout:', JSON.stringify(layout))
  await page.screenshot({ path: resolve(OUT, 'mobile-directions.png') })

  await browser.close()
}

main()
