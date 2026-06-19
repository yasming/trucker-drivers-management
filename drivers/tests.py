from datetime import datetime
from unittest.mock import Mock, patch

from django.test import override_settings
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Trip
from .services.geocoding import GeocodingError
from .services.hours_of_service import DRIVING, MAX_DRIVE_HOURS, Leg, plan_logs
from .services import routing
from .services.routing import RouteResult

START = datetime(2026, 6, 19, 8, 0)
# Rough LA -> Houston -> NYC geometry as [lon, lat] pairs.
GEOM = [[-118.24, 34.05], [-95.37, 29.76], [-74.00, 40.71]]

class HoursOfServiceEngineTests(TestCase):
    """Unit tests for the pure Hours of Service engine (no HTTP, no DB)."""

    def test_short_trip_is_one_day_with_pickup_and_dropoff(self):
        res = plan_logs([Leg(60, 1.0), Leg(120, 2.0)], GEOM, 0.0, START)
        self.assertEqual(len(res["days"]), 1)
        types = [s["type"] for s in res["stops"]]
        self.assertIn("pickup", types)
        self.assertIn("dropoff", types)
        self.assertAlmostEqual(sum(res["days"][0]["totals"].values()), 24.0, places=2)

    def test_every_day_sums_to_24_hours(self):
        res = plan_logs([Leg(200, 3.5), Leg(2000, 33.0)], GEOM, 0.0, START)
        self.assertGreater(len(res["days"]), 1)
        for day in res["days"]:
            self.assertAlmostEqual(sum(day["totals"].values()), 24.0, places=2)

    def test_driving_never_exceeds_11h_in_a_day(self):
        res = plan_logs([Leg(200, 3.5), Leg(2000, 33.0)], GEOM, 0.0, START)
        for day in res["days"]:
            self.assertLessEqual(day["totals"][DRIVING], MAX_DRIVE_HOURS + 0.01)

    def test_long_trip_inserts_10h_rest(self):
        res = plan_logs([Leg(200, 3.5), Leg(2000, 33.0)], GEOM, 0.0, START)
        self.assertTrue(any(s["type"] == "rest" for s in res["stops"]))

    def test_break_inserted_after_8h_of_driving(self):
        # 10h of continuous driving forces a 30-minute break.
        res = plan_logs([Leg(0, 0.0), Leg(600, 10.0)], GEOM, 0.0, START)
        self.assertTrue(any(s["type"] == "break" for s in res["stops"]))

    def test_fuel_stop_at_least_every_1000_miles(self):
        res = plan_logs([Leg(0, 0.0), Leg(2500, 40.0)], GEOM, 0.0, START)
        fuel = [s for s in res["stops"] if s["type"] == "fuel"]
        self.assertGreaterEqual(len(fuel), 2)

    def test_high_starting_cycle_triggers_34h_restart(self):
        res = plan_logs([Leg(100, 2.0), Leg(300, 5.0)], GEOM, 68.0, START)
        self.assertTrue(any(s["type"] == "restart" for s in res["stops"]))

    def test_stop_coordinates_fall_within_route_bounds(self):
        res = plan_logs([Leg(200, 3.5), Leg(2000, 33.0)], GEOM, 0.0, START)
        lats = [p[1] for p in GEOM]
        lons = [p[0] for p in GEOM]
        for stop in res["stops"]:
            if stop["lat"] is not None:
                self.assertGreaterEqual(stop["lat"], min(lats) - 0.01)
                self.assertLessEqual(stop["lat"], max(lats) + 0.01)
                self.assertGreaterEqual(stop["lon"], min(lons) - 0.01)
                self.assertLessEqual(stop["lon"], max(lons) + 0.01)


class RoutingServiceTests(TestCase):
    """Unit tests for ORS routing request behavior."""

    @override_settings(
        ORS_API_KEY="test-key",
        ORS_BASE_URL="https://api.openrouteservice.org",
        ORS_ROUTING_PROFILE="driving-hgv",
        ORS_FALLBACK_ROUTING_PROFILES=["driving-car"],
    )
    @patch("drivers.services.routing.requests.post")
    def test_hgv_404_falls_back_to_driving_car(self, mock_post):
        hgv_response = Mock(status_code=404)
        car_response = Mock(status_code=200)
        car_response.json.return_value = {
            "features": [
                {
                    "geometry": {"coordinates": GEOM},
                    "properties": {
                        "summary": {"distance": 1609.344, "duration": 3600},
                        "segments": [{"distance": 1609.344, "duration": 3600}],
                    },
                }
            ]
        }
        mock_post.side_effect = [hgv_response, car_response]

        result = routing.route([(34.05, -118.24), (29.76, -95.37)])

        self.assertEqual(result.distance_miles, 1.0)
        self.assertEqual(result.duration_hours, 1.0)
        self.assertIn("/driving-hgv/", mock_post.call_args_list[0].args[0])
        self.assertIn("/driving-car/", mock_post.call_args_list[1].args[0])

    @override_settings(
        ORS_API_KEY="test-key",
        ORS_BASE_URL="https://api.openrouteservice.org",
        ORS_ROUTING_PROFILE="driving-car",
        ORS_FALLBACK_ROUTING_PROFILES=[],
    )
    @patch("drivers.services.routing.requests.post")
    def test_404_returns_actionable_error(self, mock_post):
        response = Mock(status_code=404, text="")
        response.json.return_value = {"error": {"message": "Source point not found"}}
        http_error = routing.requests.HTTPError(response=response)
        response.raise_for_status.side_effect = http_error
        mock_post.return_value = response

        with self.assertRaises(routing.RoutingError) as ctx:
            routing.route([(34.05, -118.24), (29.76, -95.37)])

        self.assertIn("Try choosing a more specific street address", str(ctx.exception))
        self.assertIn("Source point not found", str(ctx.exception))


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

    @patch("drivers.services.routing.route")
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
