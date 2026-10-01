"""HTTP surface of the ELD trip planner."""

from __future__ import annotations

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from eld.serializers import TripPlanRequestSerializer
from eld.services.geocoding import get_geocoder
from eld.services.hos import DEFAULT_RULES
from eld.services.planner import TripPlanRequest, plan_trip

logger = logging.getLogger(__name__)


class HealthView(APIView):
    """Cheap liveness probe that also reports the active providers."""

    def get(self, _request):
        config = settings.SPOTTER
        return Response(
            {
                "status": "ok",
                "service": "spotter-eld-trip-planner",
                "version": "1.0.0",
                "providers": {
                    "routing": "osrm",
                    "geocoding": "nominatim/photon",
                },
                "rules": {
                    "driving_limit_hours": DEFAULT_RULES.max_drive_hours,
                    "on_duty_window_hours": DEFAULT_RULES.max_window_hours,
                    "break_after_driving_hours": DEFAULT_RULES.break_after_drive_hours,
                    "reset_hours": DEFAULT_RULES.reset_off_hours,
                    "cycle": "70 hours / 8 days",
                    "fuel_interval_miles": DEFAULT_RULES.fuel_interval_miles,
                },
                "endpoints": {
                    "osrm": config["OSRM_BASE_URL"],
                    "nominatim": config["NOMINATIM_BASE_URL"],
                    "photon": config["PHOTON_BASE_URL"],
                },
            }
        )


class PlaceSearchView(APIView):
    """Autocomplete for the three location inputs."""

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        try:
            limit = int(request.query_params.get("limit") or 6)
        except (TypeError, ValueError):
            limit = 6
        limit = max(1, min(limit, 10))

        results = get_geocoder().suggest(query, limit) if query else []
        return Response({"query": query, "results": [place.to_dict() for place in results]})


class PlanTripView(APIView):
    """Build the route, the stop plan and every daily ELD log sheet."""

    def post(self, request):
        serializer = TripPlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = plan_trip(
            TripPlanRequest(
                current_location=data["current_location"],
                pickup_location=data["pickup_location"],
                dropoff_location=data["dropoff_location"],
                cycle_used_hours=float(data.get("cycle_used_hours") or 0.0),
                departure_time=data.get("departure_time"),
                header=data.get("header") or {},
                start_odometer=float(data.get("start_odometer") or 0.0),
            )
        )
        return Response(plan, status=status.HTTP_200_OK)
