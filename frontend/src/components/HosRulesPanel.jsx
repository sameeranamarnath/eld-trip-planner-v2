import { useEffect, useRef } from 'react'
import Icon from './Icon.jsx'

/**
 * The hours-of-service rules the planner enforces, with the paragraph each one
 * comes from. Reading the limits off the regulation is what separates a planner
 * that happens to produce a log from one that is accountable for it.
 */
const RULES = [
  {
    value: '11 h',
    title: 'Driving limit',
    body: 'No driving after 11 cumulative hours at the controls. Only a qualifying break of 10 consecutive hours off duty resets it.',
    cite: '49 CFR 395.3(a)(3)',
  },
  {
    value: '14 h',
    title: 'On-duty window',
    body: 'No driving past the 14th hour after coming on duty. Unlike the driving clock, a break or a fuel stop does not pause this one.',
    cite: '49 CFR 395.3(a)(2)',
  },
  {
    value: '30 min',
    title: 'Rest break',
    body: 'Required once 8 cumulative hours of driving have elapsed, and it must be a consecutive interruption in driving status.',
    cite: '49 CFR 395.3(a)(3)(ii)',
  },
  {
    value: '10 h',
    title: 'Daily reset',
    body: 'Ten consecutive hours off duty clears the 11-hour driving limit and the 14-hour window.',
    cite: '49 CFR 395.3(a)(1)',
  },
  {
    value: '70 h / 8 d',
    title: 'Cycle limit',
    body: 'No driving once 70 on-duty hours have accumulated across 8 consecutive days. A 34-hour restart clears the cycle.',
    cite: '49 CFR 395.3(b)(2)',
  },
  {
    value: '1,000 mi',
    title: 'Fuel interval',
    body: 'At least one fuel stop every 1,000 miles, so the tank is never planned past its range.',
    cite: 'Assessment assumption',
  },
]

export default function HosRulesPanel({ open, onClose }) {
  const closeRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    closeRef.current?.focus()
    const onKey = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="hos-rules-title"
      onClick={onClose}
    >
      {/* Clicking the backdrop closes; clicking the panel must not. */}
      <div className="modal__panel" onClick={(event) => event.stopPropagation()}>
        <div className="modal__head">
          <Icon name="shield" size={18} />
          <h2 id="hos-rules-title">Hours-of-service rules applied</h2>
          <button
            ref={closeRef}
            type="button"
            className="btn btn--ghost btn--icon"
            onClick={onClose}
            aria-label="Close the rules panel"
          >
            <Icon name="x" size={16} />
          </button>
        </div>

        <p className="modal__lead">
          Property-carrying driver, 70 hours in 8 days, no adverse driving conditions. Every mile
          of the route is planned against these ceilings, and each one is re-checked before the
          truck is allowed to move again.
        </p>

        <ul className="rule-grid">
          {RULES.map((rule) => (
            <li className="rule" key={rule.title}>
              <span className="rule__value">{rule.value}</span>
              <span className="rule__title">{rule.title}</span>
              <p className="rule__body">{rule.body}</p>
              <span className="rule__cite">{rule.cite}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
