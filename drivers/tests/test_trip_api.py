from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from drivers.models import Trip
from drivers.services.geocoding import GeocodingError
from drivers.services.hours_of_service import Leg
from drivers.services.routing import RouteResult

from .fixtures import GEOM


class TripApiTests(TestCase):
    """Endpoint tests for /api/trips/ with geocoding/routing mocked out."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Houston, TX",
            "dropoff_location": "New York, NY",
            "current_cycle_used": 0,
        }

    @patch("drivers.services.routing.get_open_route_service_route")
    @patch("drivers.services.geocoding.geocode")
    def test_create_trip_computes_and_persists(self, mock_geocode, mock_route):
        mock_geocode.side_effect = [
            (34.05, -118.24, "Los Angeles, CA"),
            (29.76, -95.37, "Houston, TX"),
            (40.71, -74.00, "New York, NY"),
        ]
        mock_route.return_value = RouteResult(
            distance_miles=2200,
            duration_hours=36.0,
            geometry=GEOM,
            legs=[Leg(200, 3.5), Leg(2000, 32.5)],
        )

        resp = self.client.post("/api/trips/", self.payload, format="json")

        self.assertEqual(resp.status_code, 201, resp.content)
        data = resp.json()
        self.assertGreaterEqual(len(data["days"]), 1)
        self.assertTrue(any(s["type"] == "start" for s in data["stops"]))
        self.assertTrue(any(s["type"] == "dropoff" for s in data["stops"]))
        self.assertEqual(Trip.objects.count(), 1)

    def test_invalid_input_returns_400(self):
        resp = self.client.post(
            "/api/trips/", {"current_location": "LA"}, format="json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Trip.objects.count(), 0)

    @patch("drivers.services.geocoding.geocode", side_effect=GeocodingError("nope"))
    def test_geocoding_failure_returns_502(self, _mock_geocode):
        resp = self.client.post("/api/trips/", self.payload, format="json")
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(Trip.objects.count(), 0)
