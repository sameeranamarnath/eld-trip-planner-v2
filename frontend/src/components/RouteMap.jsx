import { useEffect, useMemo, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export const STOP_COLORS = {
  origin: '#0b1220',
  pickup: '#059669',
  dropoff: '#db2777',
  fuel: '#f59e0b',
  break: '#7c3aed',
  rest: '#475569',
  restart: '#dc2626',
  inspection: '#2563eb',
}

const LEGEND = [
  ['origin', 'Start'],
  ['pickup', 'Pickup'],
  ['dropoff', 'Drop-off'],
  ['fuel', 'Fuel'],
  ['break', '30-min break'],
  ['rest', '10-h reset'],
]

function markerHtml(colour, label) {
  const size = label.length > 2 ? 32 : 26
  return `<div class="pin" style="background:${colour};width:${size}px;height:${size}px">${label}</div>`
}

const clockOf = (iso) => (iso ? iso.slice(11, 16) : '')

/** Build the ordered pin list: origin, then every planned stop. */
export function buildMarkers(plan) {
  const pins = []
  const origin = plan?.places?.current
  if (origin) {
    pins.push({
      type: 'origin',
      title: `Start · ${origin.short_label}`,
      label: 'S',
      colour: STOP_COLORS.origin,
      lat: origin.lat,
      lng: origin.lng,
      location: origin.short_label,
      time: clockOf(plan.summary?.departure),
      date: (plan.summary?.departure || '').slice(0, 10),
      durationMin: null,
      note: 'Trip begins here.',
      stopIndex: null,
      miles: 0,
    })
  }

  ;(plan?.stops || []).forEach((stop, index) => {
    const type = stop.type || 'inspection'
    // Inspections happen where the truck already is - don't stack a second pin.
    if (type === 'inspection') {
      const previous = pins[pins.length - 1]
      if (
        previous &&
        Math.abs(previous.lat - stop.lat) < 0.002 &&
        Math.abs(previous.lng - stop.lng) < 0.002
      ) {
        return
      }
    }
    pins.push({
      type,
      title: stop.title,
      label: String(pins.length),
      colour: STOP_COLORS[type] || '#2563eb',
      lat: stop.lat,
      lng: stop.lng,
      location: stop.location || stop.city || '',
      time: clockOf(stop.arrive),
      date: stop.date,
      durationMin: stop.duration_min,
      note: stop.note,
      stopIndex: index,
      miles: stop.miles_from_start,
      dayLabel: stop.arrive_time?.split(' ')[0] || '',
    })
  })

  return pins
}

export default function RouteMap({ plan, activePin, onActivate }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const layerRef = useRef(null)
  const markersRef = useRef([])

  const geometry = useMemo(() => plan?.route?.geometry || [], [plan])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined

    const map = L.map(containerRef.current, { zoomControl: true, scrollWheelZoom: true })
    map.setView([39.5, -98.35], 4)

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors &middot; routing by OSRM',
    }).addTo(map)

    layerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      layerRef.current = null
      markersRef.current = []
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const layer = layerRef.current
    if (!map || !layer || !plan?.route) return

    layer.clearLayers()
    markersRef.current = []

    if (geometry.length > 1) {
      const latlngs = geometry.map(([lat, lng]) => [lat, lng])
      L.polyline(latlngs, { color: '#ffffff', weight: 9, opacity: 0.95 }).addTo(layer)
      L.polyline(latlngs, { color: '#2563eb', weight: 4.5, opacity: 0.95 }).addTo(layer)
    }

    buildMarkers(plan).forEach((pin, index) => {
      const marker = L.marker([pin.lat, pin.lng], {
        icon: L.divIcon({
          html: markerHtml(pin.colour, pin.label),
          className: '',
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        }),
        title: `${pin.title} · ${pin.location}`,
        zIndexOffset: pin.type === 'origin' ? 300 : 100,
      })
      marker.bindPopup(
        `<h4>${pin.title}</h4>` +
          `<div class="popup-meta">${pin.location || ''}</div>` +
          (pin.meta ? `<div class="popup-meta">${pin.meta}</div>` : '') +
          (pin.note ? `<div style="margin-top:6px">${pin.note}</div>` : ''),
      )
      marker.on('click', () => onActivate?.(index))
      marker.addTo(layer)
      markersRef.current.push(marker)
    })

    const bounds = L.latLngBounds([
      [plan.route.bounds.min_lat, plan.route.bounds.min_lng],
      [plan.route.bounds.max_lat, plan.route.bounds.max_lng],
    ])
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [44, 44] })
  }, [plan, geometry, onActivate])

  useEffect(() => {
    if (activePin == null) return
    const marker = markersRef.current[activePin]
    if (marker) {
      mapRef.current?.panTo(marker.getLatLng(), { animate: true })
      marker.openPopup()
    }
  }, [activePin])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return undefined
    const invalidate = () => map.invalidateSize()
    window.addEventListener('resize', invalidate)
    const timer = window.setTimeout(invalidate, 120)
    return () => {
      window.removeEventListener('resize', invalidate)
      window.clearTimeout(timer)
    }
  }, [])

  const route = plan?.route

  return (
    <div className="map-shell">
      <div className="map-canvas" ref={containerRef} />
      <div className="map-legend">
        {LEGEND.map(([type, label]) => (
          <span className="legend-item" key={type}>
            <span className="legend-swatch" style={{ background: STOP_COLORS[type] }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
