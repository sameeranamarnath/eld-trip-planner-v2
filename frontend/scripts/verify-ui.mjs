/**
 * TEMPORARY UI verification: exercises the new "Route instructions" tab and
 * renders the log sheets to PDF to prove the landscape print rule works.
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

  const trip =
    'current=Green%20Bay%2C%20WI&pickup=Chicago%2C%20IL&dropoff=Nashville%2C%20TN&cycle=0'
  await page.goto(`${APP}/?${trip}&run=1&tab=directions`, {
    waitUntil: 'networkidle2',
    timeout: 60000,
  })

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

  // Dark mode: the toggle writes data-theme onto <html>.
  const toggled = await clickByLabelPrefix('Switch to dark')
  await sleep(500)
  const themeAttr = await page.evaluate(() => document.documentElement.dataset.theme)
  console.log(`theme toggle clicked=${toggled} -> data-theme=${themeAttr}`)
  await page.screenshot({ path: resolve(OUT, 'theme-dark.png') })

  // HOS rules dialog.
  const opened = await page.evaluate(() => {
    const button = Array.from(document.querySelectorAll('button')).find((el) =>
      el.innerText.includes('HOS'),
    )
    if (!button) return false
    button.click()
    return true
  })
  await sleep(400)
  const ruleCount = await page.evaluate(() => document.querySelectorAll('.rule').length)
  console.log(`hos rules opened=${opened} rules rendered=${ruleCount}`)
  await page.screenshot({ path: resolve(OUT, 'hos-rules.png') })
  await page.keyboard.press('Escape')
  await sleep(300)
  const closed = await page.evaluate(() => document.querySelectorAll('.modal').length === 0)
  console.log(`escape closes the dialog: ${closed}`)

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
