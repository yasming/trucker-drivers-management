from django.test import TestCase

from drivers.services.hours_of_service import (
    DRIVING,
    MAX_DRIVE_HOURS,
    Leg,
    plan_logs,
)

from .fixtures import GEOM, START


class HoursOfServiceEngineTests(TestCase):
    """Unit tests for the pure Hours of Service engine."""

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
