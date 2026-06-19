from rest_framework import serializers

class TripInputSerializer(serializers.Serializer):
    """Validates the four planner inputs from the client."""

    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used = serializers.FloatField(
        min_value=0, max_value=70, default=0,
        help_text="Hours already used in the 70hr/8day cycle.",
    )


class TripSerializer(serializers.Serializer):
    """Serializes an in-memory planned trip."""

    id = serializers.IntegerField(read_only=True)
    current_location = serializers.CharField(read_only=True)
    pickup_location = serializers.CharField(read_only=True)
    dropoff_location = serializers.CharField(read_only=True)
    current_cycle_used = serializers.FloatField(read_only=True)
    total_distance_miles = serializers.FloatField(read_only=True)
    total_drive_hours = serializers.FloatField(read_only=True)
    route_geometry = serializers.ListField(read_only=True)
    stops = serializers.ListField(read_only=True)
    days = serializers.ListField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
