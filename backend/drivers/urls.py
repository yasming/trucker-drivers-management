from rest_framework.routers import DefaultRouter

from .views import DriverViewSet, TripViewSet

router = DefaultRouter()
router.register(r"drivers", DriverViewSet, basename="driver")
router.register(r"trips", TripViewSet, basename="trip")

urlpatterns = router.urls
