"""Routing provider (key-less OSRM) plus the polyline model the HOS engine walks."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

from eld.exceptions import RoutingError
from eld.services.geocoding import Place
from eld.services.http import get_json

logger = logging.getLogger(__name__)

EARTH_RADIUS_MILES = 3958.7613
METERS_PER_MILE = 1609.344


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(min(1.0, math.sqrt(a)))


@dataclass
class PathLeg:
    """One driving leg (origin -> waypoint) sliced out of the full polyline."""

    label_from: str
    label_to: str
    start_miles: float
    distance_miles: float
    duration_hours: float

    @property
    def end_miles(self) -> float:
        return self.start_miles + self.distance_miles

    @property
    def speed_mph(self) -> float:
        if self.duration_hours <= 0:
            return 55.0
        return self.distance_miles / self.duration_hours


@dataclass
class RoutePath:
    """The full route as a cumulative-mile indexed polyline.

    ``points`` is ``[(cumulative_miles, lat, lng), ...]`` computed with the
    haversine metric and then linearly scaled so that the last entry equals the
    provider-reported total distance.  That makes ``position_at(miles)`` agree
    with OSRM's own distance/duration numbers.
    """

    points: list[tuple[float, float, float]]
    legs: list[PathLeg]
    total_miles: float
    total_hours: float
    provider: str = "osrm"

    @property
    def speed_mph(self) -> float:
        if self.total_hours <= 0:
            return 55.0
        return self.total_miles / self.total_hours

    def position_at(self, miles: float) -> tuple[float, float]:
        """Interpolate ``(lat, lng)`` at ``miles`` along the route."""
        if not self.points:
            return 0.0, 0.0
        if miles <= 0:
            return self.points[0][1], self.points[0][2]
        if miles >= self.total_miles:
            return self.points[-1][1], self.points[-1][2]

        lo, hi = 0, len(self.points) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.points[mid][0] <= miles:
                lo = mid
            else:
                hi = mid

        d0, lat0, lng0 = self.points[lo]
        d1, lat1, lng1 = self.points[hi]
        span = d1 - d0
        if span <= 1e-9:
            return lat0, lng0
        t = (miles - d0) / span
        return lat0 + (lat1 - lat0) * t, lng0 + (lng1 - lng0) * t

    def simplified_geometry(self, tolerance_miles: float = 3.0) -> list[list[float]]:
        """Decimate the polyline for the wire (keeps the payload small)."""
        if not self.points:
            return []
        coords: list[list[float]] = []
        last_kept = -1e9
        for index, (cumulative, lat, lng) in enumerate(self.points):
            is_endpoint = index in (0, len(self.points) - 1)
            if is_endpoint or cumulative - last_kept >= tolerance_miles:
                coords.append([round(lat, 5), round(lng, 5)])
                last_kept = cumulative
        if coords and coords[-1] != [
            round(self.points[-1][1], 5),
            round(self.points[-1][2], 5),
        ]:
            coords.append([round(self.points[-1][1], 5), round(self.points[-1][2], 5)])
        return coords

    def bounds(self) -> dict[str, float]:
        lats = [p[1] for p in self.points]
        lngs = [p[2] for p in self.points]
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs),
        }


class RoutingClient:
    """Thin OSRM wrapper that produces a :class:`RoutePath`."""

    def __init__(self) -> None:
        config = settings.SPOTTER
        self._base_url = config["OSRM_BASE_URL"].rstrip("/")
        self._cache_size = int(config.get("ROUTE_CACHE_SIZE", 64))
        self._cache: dict[str, RoutePath] = {}

    def route(self, anchor_points: list[tuple[Place, str]]) -> RoutePath:
        """Route through ``[(place, label), ...]`` in order."""
        if len(anchor_points) < 2:
            raise RoutingError("At least two locations are required to build a route.")

        cache_key = "|".join(
            f"{round(p.lat, 4)},{round(p.lng, 4)}" for p, _ in anchor_points
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        coordinates = ";".join(f"{p.lng:.6f},{p.lat:.6f}" for p, _ in anchor_points)
        payload = get_json(
            f"{self._base_url}/route/v1/driving/{coordinates}",
            {
                "overview": "full",
                "geometries": "geojson",
                "steps": "false",
                "annotations": "false",
                "continue_straight": "false",
            },
        )

        if not isinstance(payload, dict) or payload.get("code") != "Ok":
            message = (payload or {}).get("message") or (payload or {}).get("code") or "unknown"
            raise RoutingError(f"The routing provider could not build this route ({message}).")

        routes = payload.get("routes") or []
        if not routes:
            raise RoutingError("The routing provider returned no route for those locations.")

        path = self._build_path(routes[0], anchor_points)
        if len(self._cache) >= self._cache_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = path
        return path

    def _build_path(
        self, route: dict[str, Any], anchor_points: list[tuple[Place, str]]
    ) -> RoutePath:
        raw_coords = ((route.get("geometry") or {}).get("coordinates")) or []
        if len(raw_coords) < 2:
            raise RoutingError("The routing provider returned an empty geometry.")

        # OSRM geometry is [lng, lat]; convert and accumulate haversine miles.
        cumulative = [0.0]
        for index in range(1, len(raw_coords)):
            lng0, lat0 = raw_coords[index - 1][0], raw_coords[index - 1][1]
            lng1, lat1 = raw_coords[index][0], raw_coords[index][1]
            cumulative.append(cumulative[-1] + haversine_miles(lat0, lng0, lat1, lng1))

        computed_total = cumulative[-1] or 1.0
        reported_miles = float(route.get("distance", 0.0)) / METERS_PER_MILE
        reported_hours = float(route.get("duration", 0.0)) / 3600.0
        scale = (reported_miles / computed_total) if reported_miles > 0 else 1.0

        points = [
            (cumulative[i] * scale, float(raw_coords[i][1]), float(raw_coords[i][0]))
            for i in range(len(raw_coords))
        ]
        total_miles = points[-1][0] if points else 0.0

        raw_legs = route.get("legs") or []
        legs: list[PathLeg] = []
        cursor = 0.0
        for index in range(len(anchor_points) - 1):
            leg_payload = raw_legs[index] if index < len(raw_legs) else {}
            leg_miles = float(leg_payload.get("distance", 0.0)) / METERS_PER_MILE
            leg_hours = float(leg_payload.get("duration", 0.0)) / 3600.0
            if leg_miles <= 0 and index == len(anchor_points) - 2:
                leg_miles = max(0.0, total_miles - cursor)
            legs.append(
                PathLeg(
                    label_from=anchor_points[index][1],
                    label_to=anchor_points[index + 1][1],
                    start_miles=cursor,
                    distance_miles=leg_miles,
                    duration_hours=leg_hours,
                )
            )
            cursor += leg_miles

        if total_miles <= 0:
            raise RoutingError("The routing provider returned a zero-length route.")

        return RoutePath(
            points=points,
            legs=legs,
            total_miles=total_miles,
            total_hours=reported_hours or (total_miles / 55.0),
        )


_router: RoutingClient | None = None


def get_router() -> RoutingClient:
    """Lazily construct the process-wide router."""
    global _router
    if _router is None:
        _router = RoutingClient()
    return _router

