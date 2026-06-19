from django.db import models


class Driver(models.Model):
    """A truck driver tracked by the fleet management system."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ON_TRIP = "on_trip", "On trip"
        OFF_DUTY = "off_duty", "Off duty"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
