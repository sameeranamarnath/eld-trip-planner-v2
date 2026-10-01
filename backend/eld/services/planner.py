"""End-to-end trip planning: inputs in, map model + ELD log sheets out."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from eld.exceptions import ValidationError
from eld.services.geocoding import Place, get_geocoder
from eld.services.hos import (
    HosRules,
    HosSimulator,
    STATUS_LABELS,
    Segment,
)
from eld.services.logs import LogBookBuilder
from eld.services.routing import get_router, haversine_miles

logger = logging.getLogger(__name__)

ANCHOR_TOLERANCE_MILES = 1.5
MAX_REVERSE_LOOKUPS = 60

# Which activity kinds become a pin on the map, and how they are titled.
_STOP_META: dict[str, dict[str, str]] = {
    "pickup": {"type": "pickup", "title": "Pickup", "icon": "package"},
    "dropoff": {"type": "dropoff", "title": "Drop-off", "icon": "flag"},
    "fuel": {"type": "fuel", "title": "Fuel stop", "icon": "fuel"},
    "break": {"type": "break", "title": "30-minute break", "icon": "coffee"},
    "restart": {"type": "restart", "title": "34-hour restart", "icon": "refresh"},
    "pretrip": {"type": "inspection", "title": "Pre-trip inspection", "icon": "check"},
    "posttrip": {"type": "inspection", "title": "Post-trip inspection", "icon": "check"},
}
_REST_KINDS = {"reset_off", "reset_sleeper"}


@dataclass
class TripPlanRequest:
    """Validated trip inputs."""

    current_location: str
    pickup_location: str
    dropoff_location: str
    cycle_used_hours: float = 0.0
    departure_time: datetime | None = None
    header: dict[str, Any] = field(default_factory=dict)
    start_odometer: float = 0.0
    rules: HosRules = field(default_factory=HosRules)


class TripPlanner:
    """Coordinates the geocoder, the router, the HOS engine and the log builder."""

    def __init__(self, request: TripPlanRequest) -> None:
        self.request = request
        self.geocoder = get_geocoder()
        self.router = get_router()

    # -- public ------------------------------------------------------------
    def plan(self) -> dict[str, Any]:
        request = self.request
        origin = self.geocoder.geocode(request.current_location)
        pickup = self.geocoder.geocode(request.pickup_location)
        dropoff = self.geocoder.geocode(request.dropoff_location)

        anchors: list[tuple[Place, str]] = [
            (origin, origin.short_label),
            (pickup, pickup.short_label),
            (dropoff, dropoff.short_label),
        ]
        path = self.router.route(anchors)

        departure = request.departure_time or _default_departure()
        simulator = HosSimulator(
            path,
            departure,
            cycle_used_hours=request.cycle_used_hours,
            rules=request.rules,
        )
        simulation = simulator.simulate()
        self._label_segments(simulation.segments, anchors)

        day_logs = LogBookBuilder(
            simulation.segments,
            cycle_used_hours=request.cycle_used_hours,
            header=request.header,
            start_odometer=request.start_odometer,
        ).build()

        stops = self._build_stops(simulation.segments)
        route = {
            "distance_miles": round(path.total_miles, 1),
            "duration_hours": round(path.total_hours, 2),
            "geometry": path.simplified_geometry(),
            "bounds": path.bounds(),
            "legs": [
                {
                    "index": index,
                    "from": leg.label_from,
                    "to": leg.label_to,
                    "distance_miles": round(leg.distance_miles, 1),
                    "duration_hours": round(leg.duration_hours, 2),
                }
                for index, leg in enumerate(path.legs)
            ],
            "provider": path.provider,
        }

        return {
            "input": {
                "current_location": request.current_location,
                "pickup_location": request.pickup_location,
                "dropoff_location": request.dropoff_location,
                "cycle_used_hours": request.cycle_used_hours,
                "departure_time": departure.isoformat(),
            },
            "places": {
                "current": origin.to_dict(),
                "pickup": pickup.to_dict(),
                "dropoff": dropoff.to_dict(),
            },
            "route": route,
            "stops": stops,
            "segments": [segment.to_dict() for segment in simulation.segments],
            "logs": [day.to_dict() for day in day_logs],
            "summary": self._summary(simulation, day_logs, path),
        }

    # -- labelling ---------------------------------------------------------
    def _label_segments(
        self, segments: list[Segment], anchors: list[tuple[Place, str]]
    ) -> None:
        """Attach a human-readable place to every segment."""
        positions: dict[tuple[int, int], tuple[float, float]] = {}
        for segment in segments:
            key = (round(segment.lat, 3), round(segment.lng, 3))
            positions.setdefault(key, (segment.lat, segment.lng))

        resolved: dict[tuple[int, int], dict[str, str]] = {}
        pending: list[tuple[tuple[int, int], float, float]] = []

        for key, (lat, lng) in positions.items():
            best_label, best_city, best_state, best_distance = "", "", "", 1e9
            for place, _label in anchors:
                distance = haversine_miles(lat, lng, place.lat, place.lng)
                if distance < best_distance:
                    best_distance = distance
                    best_label = place.short_label or place.label
                    best_city, best_state = place.city, place.state
            if best_distance <= ANCHOR_TOLERANCE_MILES:
                resolved[key] = {"label": best_label, "city": best_city, "state": best_state}
            else:
                pending.append((key, lat, lng))

        if pending:
            pending = pending[:MAX_REVERSE_LOOKUPS]
            workers = min(6, max(1, len(pending)))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = pool.map(
                    lambda item: self.geocoder.reverse(item[1], item[2]), pending
                )
                for (key, _lat, _lng), place in zip(pending, results):
                    resolved[key] = {
                        "label": place.short_label or place.label,
                        "city": place.city,
                        "state": place.state,
                    }

        for segment in segments:
            key = (round(segment.lat, 3), round(segment.lng, 3))
            info = resolved.get(key)
            if info:
                segment.place_label = info["label"]
                segment.place_city = info["city"]
                segment.place_state = info["state"]
            elif not segment.place_label:
                segment.place_label = "En route"

    # -- map stops ---------------------------------------------------------
    def _build_stops(self, segments: list[Segment]) -> list[dict[str, Any]]:
        """Collapse the segment stream into the notable pins shown on the map."""
        stops: list[dict[str, Any]] = []
        cumulative = 0.0
        index = 0
        while index < len(segments):
            segment = segments[index]
            kind = segment.kind

            if kind in _REST_KINDS:
                start, end = segment.start, segment.end
                note = "10-hour reset"
                cursor = index + 1
                while cursor < len(segments) and segments[cursor].kind in _REST_KINDS:
                    end = segments[cursor].end
                    cursor += 1
                stops.append(
                    self._stop_dict(
                        stop_type="rest",
                        title="10-hour reset",
                        icon="bed",
                        segment=segment,
                        start=start,
                        end=end,
                        note=note,
                        cumulative=cumulative,
                    )
                )
                index = cursor
                continue

            meta = _STOP_META.get(kind)
            if meta:
                stops.append(
                    self._stop_dict(
                        stop_type=meta["type"],
                        title=meta["title"],
                        icon=meta["icon"],
                        segment=segment,
                        start=segment.start,
                        end=segment.end,
                        note=segment.note,
                        cumulative=cumulative,
                    )
                )

            cumulative += segment.miles
            index += 1

        return stops

    def _stop_dict(
        self,
        *,
        stop_type: str,
        title: str,
        icon: str,
        segment: Segment,
        start: datetime,
        end: datetime,
        note: str,
        cumulative: float,
    ) -> dict[str, Any]:
        return {
            "type": stop_type,
            "title": title,
            "icon": icon,
            "status": segment.status,
            "status_label": STATUS_LABELS[segment.status],
            "note": note,
            "location": segment.place_label,
            "city": segment.place_city,
            "state": segment.place_state,
            "lat": round(segment.lat, 6),
            "lng": round(segment.lng, 6),
            "arrive": start.isoformat(),
            "depart": end.isoformat(),
            "arrive_time": start.strftime("%a %H:%M"),
            "depart_time": end.strftime("%a %H:%M"),
            "duration_min": round((end - start).total_seconds() / 60.0, 1),
            "miles_from_start": round(cumulative, 1),
            "date": start.date().isoformat(),
        }

    # -- summary -----------------------------------------------------------
    def _summary(self, simulation, day_logs, path) -> dict[str, Any]:
        request = self.request
        counters = simulation.counters or {}
        arrival = simulation.end_time
        wall_hours = (arrival - simulation.start_time).total_seconds() / 3600.0
        on_duty_in_plan = sum(day.on_duty_hours for day in day_logs)
        cycle_after = min(70.0, request.cycle_used_hours + on_duty_in_plan)
        return {
            "total_miles": round(path.total_miles, 1),
            "driving_hours": round(path.total_hours, 2),
            "trip_days": len(day_logs),
            "log_sheets": len(day_logs),
            "wall_clock_hours": round(wall_hours, 2),
            "wall_clock_days": round(wall_hours / 24.0, 2),
            "departure": simulation.start_time.isoformat(),
            "arrival": arrival.isoformat(),
            "fuel_stops": counters.get("fuel_stops", 0),
            "breaks": counters.get("breaks", 0),
            "rests": counters.get("rests", 0),
            "restarts": counters.get("restarts", 0),
            "cycle_used_hours": request.cycle_used_hours,
            "cycle_hours_after_trip": round(cycle_after, 2),
            "cycle_hours_remaining": round(max(0.0, 70.0 - cycle_after), 2),
            "rules": {
                "max_drive_hours": request.rules.max_drive_hours,
                "max_window_hours": request.rules.max_window_hours,
                "break_after_drive_hours": request.rules.break_after_drive_hours,
                "reset_off_hours": request.rules.reset_off_hours,
                "cycle": "70 hours / 8 days",
                "fuel_interval_miles": request.rules.fuel_interval_miles,
                "pickup_minutes": request.rules.pickup_minutes,
                "dropoff_minutes": request.rules.dropoff_minutes,
            },
        }


def _default_departure() -> datetime:
    """Default to the next quarter hour so demo logs look tidy."""
    now = datetime.now().replace(second=0, microsecond=0)
    remainder = now.minute % 15
    if remainder:
        now += timedelta(minutes=15 - remainder)
    return now


def plan_trip(request: TripPlanRequest) -> dict[str, Any]:
    if request.cycle_used_hours < 0 or request.cycle_used_hours > 70:
        raise ValidationError(
            "Current cycle used must be between 0 and 70 hours.",
            details={"cycle_used_hours": request.cycle_used_hours},
        )
    return TripPlanner(request).plan()
