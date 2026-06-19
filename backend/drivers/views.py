from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Trip
from .serializers import TripInputSerializer, TripSerializer
from .services import geocoding, routing
from .services.geocoding import GeocodingError
from .services.hos import plan_logs
from .services.routing import RoutingError


class TripViewSet(viewsets.ModelViewSet):
    """Plan trips and read back saved ones.

    POST runs the pipeline (geocode -> route -> HOS engine), persists a Trip,
    and returns the full result. GET lists/retrieves saved trips. Trips are
    immutable, so PUT/PATCH are not exposed.
    """

    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def create(self, request, *args, **kwargs):
        input_serializer = TripInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            current = geocoding.geocode(data["current_location"])
            pickup = geocoding.geocode(data["pickup_location"])
            dropoff = geocoding.geocode(data["dropoff_location"])
            route_result = routing.route(
                [
                    (current[0], current[1]),
                    (pickup[0], pickup[1]),
                    (dropoff[0], dropoff[1]),
                ]
            )
        except (GeocodingError, RoutingError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        plan = plan_logs(
            route_result.legs,
            route_result.geometry,
            current_cycle_used=data["current_cycle_used"],
        )

        stops = self._build_stops(plan["stops"], route_result, current, pickup, dropoff)

        trip = Trip.objects.create(
            current_location=data["current_location"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            current_cycle_used=data["current_cycle_used"],
            total_distance_miles=plan["total_distance_miles"],
            total_drive_hours=plan["total_drive_hours"],
            route_geometry=route_result.geometry,
            stops=stops,
            days=plan["days"],
        )
        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _build_stops(stops, route_result, current, pickup, dropoff):
        """Prepend a start marker and label pickup/dropoff with their addresses."""
        if route_result.geometry:
            start_lat, start_lon = route_result.geometry[0][1], route_result.geometry[0][0]
        else:
            start_lat, start_lon = current[0], current[1]
        start = {
            "type": "start",
            "label": f"Start: {current[2]}",
            "lat": start_lat,
            "lon": start_lon,
            "arrive": None,
            "depart": None,
        }
        for stop in stops:
            if stop["type"] == "pickup":
                stop["label"] = f"Pickup: {pickup[2]}"
            elif stop["type"] == "dropoff":
                stop["label"] = f"Dropoff: {dropoff[2]}"
        return [start, *stops]
