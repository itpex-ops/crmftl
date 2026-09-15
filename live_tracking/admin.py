from django.contrib import admin
from .models import TrackingSession, LiveLocation, SMSLog


@admin.register(TrackingSession)
class TrackingSessionAdmin(admin.ModelAdmin):

    list_display = (
        "vehicle",
        "driver_mobile",
        "status",
        "last_location",
        "last_updated",
    )

    search_fields = (
        "vehicle__ftl_no",
        "driver_mobile",
    )


@admin.register(LiveLocation)
class LiveLocationAdmin(admin.ModelAdmin):

    list_display = (
        "session",
        "location_name",
        "received_at",
    )


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):

    list_display = (
        "mobile",
        "delivery_status",
        "sent_at",
    )