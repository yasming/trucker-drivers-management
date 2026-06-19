from rest_framework import serializers

from .models import Driver, Trip


class DriverSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "license_number",
            "license_expiry",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TripInputSerializer(serializers.Serializer):
    """Validates the four planner inputs from the client."""

    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used = serializers.FloatField(
        min_value=0, max_value=70, default=0,
        help_text="Hours already used in the 70hr/8day cycle.",
    )


class TripSerializer(serializers.ModelSerializer):
    """Serializes a stored Trip with its computed route and log sheets."""

    class Meta:
        model = Trip
        fields = [
            "id",
            "current_location",
            "pickup_location",
            "dropoff_location",
            "current_cycle_used",
            "total_distance_miles",
            "total_drive_hours",
            "route_geometry",
            "stops",
            "days",
            "created_at",
        ]
        read_only_fields = fields
