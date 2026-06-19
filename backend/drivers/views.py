from rest_framework import viewsets, filters

from .models import Driver
from .serializers import DriverSerializer


class DriverViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for truck drivers."""

    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["first_name", "last_name", "email", "license_number"]
    ordering_fields = ["last_name", "first_name", "created_at", "status"]
