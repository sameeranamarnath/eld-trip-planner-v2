import { useState } from 'react'
import Icon from './Icon.jsx'
import LocationField from './LocationField.jsx'

export const EXAMPLE_TRIPS = [
  {
    label: 'Green Bay → Chicago → Nashville',
    current: 'Green Bay, WI',
    pickup: 'Chicago, IL',
    dropoff: 'Nashville, TN',
    cycle: 0,
  },
  {
    label: 'Coast-to-coast · 4 log sheets',
    current: 'Green Bay, WI',
    pickup: 'Denver, CO',
    dropoff: 'Los Angeles, CA',
    cycle: 12,
  },
  {
    label: 'Near the cycle limit',
    current: 'Atlanta, GA',
    pickup: 'Charlotte, NC',
    dropoff: 'Newark, NJ',
    cycle: 62,
  },
]

export const DEFAULT_HEADER = {
  driver_name: 'J. Driver',
  driver_number: 'SCH-4471',
  carrier: 'Spotter Freight Systems',
  home_terminal: 'Green Bay, WI',
  tractor_number: 'T-1042',
  trailer_number: 'TR-5580',
  shipper: "Don's Paper Company",
  commodity: 'Paper products',
  load_id: 'LD-88231',
}

/** Examples always start at 06:30 today so the generated logs are comparable. */
function morningDeparture() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T06:30`
}

export default function TripForm({ value, onChange, onSubmit, loading, error }) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const set = (patch) => onChange({ ...value, ...patch })
  const setHeader = (patch) => set({ header: { ...value.header, ...patch } })

  const canSubmit =
    value.current_location.trim().length > 1 &&
    value.pickup_location.trim().length > 1 &&
    value.dropoff_location.trim().length > 1 &&
    !loading

  return (
    <form
      className="card sticky-panel"
      onSubmit={(event) => {
        event.preventDefault()
        if (canSubmit) onSubmit()
      }}
    >
      <div className="card__head">
        <Icon name="route" size={18} />
        <div>
          <h2>Trip details</h2>
          <p>Everything the planner needs to build a legal run.</p>
        </div>
      </div>

      <div className="card__body">
        <div className="form-grid">
          <LocationField
            id="current_location"
            label="Current location"
            hint="where the truck sits now"
            icon="pin"
            accent="#2563eb"
            placeholder="e.g. Green Bay, WI"
            value={value.current_location}
            onChange={(text) => set({ current_location: text })}
          />

          <LocationField
            id="pickup_location"
            label="Pickup location"
            hint="1 h on duty"
            icon="package"
            accent="#059669"
            placeholder="e.g. Chicago, IL"
            value={value.pickup_location}
            onChange={(text) => set({ pickup_location: text })}
          />

          <LocationField
            id="dropoff_location"
            label="Drop-off location"
            hint="1 h on duty"
            icon="flag"
            accent="#db2777"
            placeholder="e.g. Nashville, TN"
            value={value.dropoff_location}
            onChange={(text) => set({ dropoff_location: text })}
          />

          <div className="field">
            <label className="field__label" htmlFor="cycle_used_hours">
              <span
                className="field__dot"
                style={{ background: '#f59e0b', boxShadow: '0 0 0 3px #f59e0b22' }}
              />
              Current cycle used
              <span className="field__hint">70 h / 8 days</span>
            </label>
            <div className="range-row">
              <input
                id="cycle_used_hours"
                type="range"
                min="0"
                max="70"
                step="0.5"
                value={value.cycle_used_hours}
                onChange={(event) => set({ cycle_used_hours: Number(event.target.value) })}
              />
              <span className="range-badge">{Number(value.cycle_used_hours).toFixed(1)} h</span>
            </div>
            <span className="field__hint">
              Hours already burned in the rolling 8-day window. Hitting 70 h forces a 34-hour
              restart.
            </span>
          </div>

          <button
            type="button"
            className="btn btn--subtle"
            onClick={() => setShowAdvanced((prev) => !prev)}
            aria-expanded={showAdvanced}
          >
            <Icon name={showAdvanced ? 'x' : 'sparkle'} size={15} />
            {showAdvanced ? 'Hide optional details' : 'Add departure time & log header'}
          </button>

          {showAdvanced ? (
            <div className="split-2">
              <div className="field">
                <label className="field__label" htmlFor="departure_time">
                  <Icon name="calendar" size={14} /> Departure time
                </label>
                <input
                  id="departure_time"
                  className="input"
                  type="datetime-local"
                  value={value.departure_time}
                  onChange={(event) => set({ departure_time: event.target.value })}
                />
              </div>
              <div className="field">
                <label className="field__label" htmlFor="start_odometer">
                  <Icon name="gauge" size={14} /> Tractor odometer
                </label>
                <input
                  id="start_odometer"
                  className="input"
                  type="number"
                  min="0"
                  step="1"
                  placeholder="e.g. 142500"
                  value={value.start_odometer}
                  onChange={(event) => set({ start_odometer: event.target.value })}
                />
              </div>

              <HeaderInput
                id="driver_name"
                label="Driver name"
                value={value.header.driver_name}
                onChange={(text) => setHeader({ driver_name: text })}
              />
              <HeaderInput
                id="driver_number"
                label="Driver number"
                value={value.header.driver_number}
                onChange={(text) => setHeader({ driver_number: text })}
              />
              <HeaderInput
                id="carrier"
                label="Carrier"
                value={value.header.carrier}
                onChange={(text) => setHeader({ carrier: text })}
              />
              <HeaderInput
                id="home_terminal"
                label="Home terminal"
                value={value.header.home_terminal}
                onChange={(text) => setHeader({ home_terminal: text })}
              />
              <HeaderInput
                id="shipper"
                label="Shipper"
                value={value.header.shipper}
                onChange={(text) => setHeader({ shipper: text })}
              />
              <HeaderInput
                id="commodity"
                label="Commodity"
                value={value.header.commodity}
                onChange={(text) => setHeader({ commodity: text })}
              />
              <HeaderInput
                id="tractor_number"
                label="Tractor number"
                value={value.header.tractor_number}
                onChange={(text) => setHeader({ tractor_number: text })}
              />
              <HeaderInput
                id="trailer_number"
                label="Trailer number"
                value={value.header.trailer_number}
                onChange={(text) => setHeader({ trailer_number: text })}
              />
              <HeaderInput
                id="load_id"
                label="Load ID"
                value={value.header.load_id}
                onChange={(text) => setHeader({ load_id: text })}
              />
            </div>
          ) : null}

          {error ? (
            <div className="alert alert--error" role="alert">
              <Icon name="alert" size={17} />
              <span>{error}</span>
            </div>
          ) : null}

          <button className="btn btn--primary btn--block" type="submit" disabled={!canSubmit}>
            {loading ? (
              <>
                <span className="spinner" />
                Planning route &amp; logs…
              </>
            ) : (
              <>
                <Icon name="sparkle" size={16} />
                Build route &amp; ELD logs
              </>
            )}
          </button>
        </div>

        <hr className="divider" />
        <div className="section-title">Try an example</div>
        <div className="example-row">
          {EXAMPLE_TRIPS.map((example) => (
            <button
              key={example.label}
              type="button"
              className="example-chip"
              disabled={loading}
              onClick={() =>
                set({
                  current_location: example.current,
                  pickup_location: example.pickup,
                  dropoff_location: example.dropoff,
                  cycle_used_hours: example.cycle,
                  departure_time: morningDeparture(),
                })
              }
            >
              {example.label}
            </button>
          ))}
        </div>
      </div>
    </form>
  )
}

function HeaderInput({ id, label, value, onChange }) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={`header_${id}`}>
        {label}
      </label>
      <input
        id={`header_${id}`}
        className="input"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  )
}
