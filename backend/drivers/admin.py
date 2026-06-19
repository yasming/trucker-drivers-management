from django.contrib import admin

from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "license_number", "status", "license_expiry")
    list_filter = ("status",)
    search_fields = ("first_name", "last_name", "email", "license_number")
