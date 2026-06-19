from django.db import models

class Trip(models.Model):
    """A planned trip: the user's inputs plus the computed route and ELD logs.

    The route geometry, the ordered list of stops/rests, and the per-day log
    sheets are stored as JSON so a single record can fully reconstruct the UI
    (map + daily log sheets) without recomputing or re-calling the routing API.
    """

    # --- Inputs ---
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    # Hours already used in the 70hr/8day cycle before this trip starts.
    current_cycle_used = models.FloatField(default=0)

    # --- Computed results ---
    total_distance_miles = models.FloatField(default=0)
    total_drive_hours = models.FloatField(default=0)
    # List of [lon, lat] pairs tracing the full route (for the map polyline).
    route_geometry = models.JSONField(default=list, blank=True)
    # Ordered stops: pickup / dropoff / fuel / break / rest, each with
    # lat, lon, type, label, and arrive/depart ISO timestamps.
    stops = models.JSONField(default=list, blank=True)
    # One entry per calendar day = one log sheet (segments, totals, miles…).
    days = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.pickup_location} → {self.dropoff_location} ({self.created_at:%Y-%m-%d})"
