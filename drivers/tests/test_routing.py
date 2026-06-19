from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from drivers.services import routing

from .fixtures import GEOM


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

        result = routing.get_open_route_service_route([(34.05, -118.24), (29.76, -95.37)])

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
            routing.get_open_route_service_route([(34.05, -118.24), (29.76, -95.37)])

        self.assertIn("Try choosing a more specific street address", str(ctx.exception))
        self.assertIn("Source point not found", str(ctx.exception))
