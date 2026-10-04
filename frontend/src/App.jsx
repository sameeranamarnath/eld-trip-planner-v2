import { useCallback, useEffect, useRef, useState } from 'react'
import Icon from './components/Icon.jsx'
import TripForm from './components/TripForm.jsx'
import RouteMap from './components/RouteMap.jsx'
import Itinerary from './components/Itinerary.jsx'
import SummaryPanel from './components/SummaryPanel.jsx'
import LogBook from './components/LogBook.jsx'
import Directions from './components/Directions.jsx'
import HosRulesPanel from './components/HosRulesPanel.jsx'
import { fetchHealth, planTrip } from './api.js'
import { toDateTimeInputValue } from './format.js'
import { DEFAULT_HEADER } from './logHeader.js'
import { useTheme } from './useTheme.js'

const TABS = [
  { id: 'route', label: 'Route & stops', icon: 'route' },
  { id: 'directions', label: 'Route instructions', icon: 'list' },
  { id: 'logs', label: 'Daily log sheets', icon: 'file' },
]

// The headline limits, shown as chips in the header.
const HOS_FACTS = [
  ['70', 'hours / 8 days'],
  ['11', 'h driving limit'],
  ['14', 'h on-duty window'],
  ['30', 'min break after 8 h'],
  ['1,000', 'mi between fuel stops'],
]

/**
 * Trips are deep-linkable so a plan can be shared, e.g.
 * `/?current=Green%20Bay%2C%20WI&pickup=Chicago%2C%20IL&dropoff=Nashville%2C%20TN&cycle=0&run=1`
 */
function readQueryParams() {
  if (typeof window === 'undefined') return new URLSearchParams()
  return new URLSearchParams(window.location.search)
}

function initialForm() {
  const params = readQueryParams()
  return {
    current_location: params.get('current') || 'Green Bay, WI',
    pickup_location: params.get('pickup') || 'Chicago, IL',
    dropoff_location: params.get('dropoff') || 'Nashville, TN',
    cycle_used_hours: Number(params.get('cycle') || 0),
    departure_time: params.get('departure') || toDateTimeInputValue(new Date()),
    start_odometer: params.get('odometer') || '142500',
    header: { ...DEFAULT_HEADER },
  }
}

export default function App() {
  const [form, setForm] = useState(initialForm)
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState(() => {
    const requested = readQueryParams().get('tab')
    return TABS.some((entry) => entry.id === requested) ? requested : 'route'
  })
  const [activePin, setActivePin] = useState(null)
  const [health, setHealth] = useState(null)
  const [rulesOpen, setRulesOpen] = useState(false)
  const [theme, setTheme] = useTheme()
  const submitRef = useRef(null)

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  const handleSubmit = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await planTrip({
        current_location: form.current_location.trim(),
        pickup_location: form.pickup_location.trim(),
        dropoff_location: form.dropoff_location.trim(),
        cycle_used_hours: Number(form.cycle_used_hours) || 0,
        departure_time: form.departure_time || null,
        start_odometer: Number(form.start_odometer) || 0,
        header: form.header,
      })
      setPlan(result)
      setActivePin(null)
    } catch (requestError) {
      setError(requestError.message || 'Something went wrong while planning this trip.')
      setPlan(null)
    } finally {
      setLoading(false)
    }
  }, [form])

  submitRef.current = handleSubmit

  useEffect(() => {
    if (readQueryParams().get('run') !== '1') return undefined
    const timer = window.setTimeout(() => submitRef.current?.(), 60)
    return () => window.clearTimeout(timer)
  }, [])


  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__inner">
          <div className="brand">
            <span className="brand__mark">
              <Icon name="truck" size={21} strokeWidth={2.1} />
            </span>
            <div className="brand__text">
              <h1>Spotter ELD</h1>
              <span>Trip planner &amp; automatic driver&apos;s daily log sheets</span>
            </div>
          </div>
          <div className="topbar__facts">
            {HOS_FACTS.map(([value, label]) => (
              <span className="fact-chip" key={label}>
                <b>{value}</b> {label}
              </span>
            ))}
            {health ? (
              <span className="fact-chip" title="Providers used by the planner">
                <b>OSRM</b> + <b>OpenStreetMap</b> live
              </span>
            ) : null}
            <button
              type="button"
              className="fact-chip fact-chip--action"
              onClick={() => setRulesOpen(true)}
              aria-haspopup="dialog"
            >
              <b>HOS</b> rules
            </button>
            <button
              type="button"
              className="fact-chip fact-chip--action"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            >
              <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={14} />
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="layout">
          <div className="column no-print">
            <TripForm
              value={form}
              onChange={setForm}
              onSubmit={handleSubmit}
              loading={loading}
              error={error}
            />
          </div>

          <div className="column" aria-live="polite" aria-busy={loading}>
            {!plan && !loading ? <EmptyState onSubmit={handleSubmit} /> : null}
            {loading ? <LoadingState /> : null}

            {plan && !loading ? (
              <>
                <div className="no-print">
                  <SummaryPanel plan={plan} />
                </div>

                <div className="tabs no-print">
                  {TABS.map((entry) => (
                    <button
                      key={entry.id}
                      type="button"
                      className={`tab${tab === entry.id ? ' tab--active' : ''}`}
                      onClick={() => setTab(entry.id)}
                    >
                      <Icon name={entry.icon} size={15} />
                      {entry.label}
                      {entry.id === 'logs' ? (
                        <span className="tab__count">{plan.logs.length}</span>
                      ) : null}
                      {entry.id === 'directions' ? (
                        <span className="tab__count">{plan.directions?.step_count ?? 0}</span>
                      ) : null}
                    </button>
                  ))}
                </div>

                {tab === 'route' ? (
                  <div className="result-grid">
                    <RouteMap plan={plan} activePin={activePin} onActivate={setActivePin} />
                    <div className="card">
                      <div className="card__head">
                        <Icon name="list" size={17} />
                        <div>
                          <h3>Stops, rests &amp; fuel</h3>
                          <p>{plan.stops.length} planned stops in running order</p>
                        </div>
                      </div>
                      <div className="card__body card__body--tight">
                        <Itinerary plan={plan} activePin={activePin} onActivate={setActivePin} />
                      </div>
                    </div>
                  </div>
                ) : tab === 'directions' ? (
                  <Directions plan={plan} />
                ) : (
                  <LogBook plan={plan} />
                )}
              </>
            ) : null}
          </div>
        </div>
      </main>

      <HosRulesPanel open={rulesOpen} onClose={() => setRulesOpen(false)} />
    </div>
  )
}

function EmptyState({ onSubmit }) {
  return (
    <div className="empty">
      <div className="empty__icon">
        <Icon name="file" size={28} />
      </div>
      <h2>Route map + filled-out ELD logs in one run</h2>
      <p>
        Enter the truck&apos;s current location, the pickup and the drop-off, and how much of the
        70-hour cycle is already used. Spotter plots the shortest legal route, places every break,
        fuel stop and 10-hour reset along it, then draws a complete FMCSA daily log sheet for each
        day of the trip.
      </p>
      <button type="button" className="btn btn--primary" onClick={onSubmit}>
        <Icon name="sparkle" size={16} />
        Generate from the example trip
      </button>

      <div className="empty__grid">
        <div className="empty__feature">
          <h4>
            <Icon name="route" size={14} /> Legal route planning
          </h4>
          <p>
            11 h driving, 14 h window, a 30-min break after 8 h, 10-h resets and 34-h cycle
            restarts are all applied automatically.
          </p>
        </div>
        <div className="empty__feature">
          <h4>
            <Icon name="fuel" size={14} /> Fuel every 1,000 mi
          </h4>
          <p>
            Fuel stops are inserted on the route itself, so the tank is never planned past its
            range.
          </p>
        </div>
        <div className="empty__feature">
          <h4>
            <Icon name="file" size={14} /> Draws the log, not just the numbers
          </h4>
          <p>
            Duty-status lines on a 15-minute grid, brackets, numbered remark flags, per-line totals
            and the 70-hour recap.
          </p>
        </div>
        <div className="empty__feature">
          <h4>
            <Icon name="pin" size={14} /> Free map APIs only
          </h4>
          <p>OpenStreetMap tiles, OSRM routing and Photon/Nominatim geocoding - no API keys.</p>
        </div>
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <>
      <div className="card">
        <div className="card__body">
          <div className="stats">
            {[0, 1, 2, 3, 4, 5].map((index) => (
              <div className="skeleton" style={{ height: 76 }} key={index} />
            ))}
          </div>
        </div>
      </div>
      <div className="card">
        <div className="card__body">
          <div className="skeleton" style={{ height: 420 }} />
        </div>
      </div>
    </>
  )
}
