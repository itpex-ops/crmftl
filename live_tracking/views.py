from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from vehicles.models import Vehicle
from .models import TrackingSession, LiveLocation
from vehicles.models import Vehicle

from .models import (
    TrackingSession,
    LiveLocation,
)

from .services.auth_service import TrackingAuthService
from .services.consent_auth_service import ConsentAuthService
from .services.import_service import ImportService
from .services.consent_service import ConsentService
from .services.location_service import LocationService

def test_tracking_auth(request):
    result = TrackingAuthService.get_tracking_token()
    return JsonResponse(result)


def send_consent(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    result = ConsentService.send_consent(session)

    if result["success"]:
        messages.success(request, result["message"])
    else:
        messages.error(request, result["message"])

    return redirect("live_tracking_list")
def api_token_status(request):

    tracking = TrackingAuthService.get_tracking_token()
    consent = ConsentAuthService.get_tracking_token()

    return JsonResponse({
        "tracking": tracking,
        "consent": consent,
    })


def live_tracking_dashboard(request):

    context = {
        "total": TrackingSession.objects.count(),
        "active": TrackingSession.objects.filter(status="active").count(),
        "pending": TrackingSession.objects.filter(status="pending").count(),
        "stopped": TrackingSession.objects.filter(status="stopped").count(),
        "recent_locations":
            LiveLocation.objects.select_related(
                "session",
                "session__vehicle"
            ).order_by("-received_at")[:10]
    }

    return render(
        request,
        "live_tracking/dashboard.html",
        context
    )

def live_tracking_list(request):

    sessions = TrackingSession.objects.select_related(
        "vehicle",
        "vehicle__order"
    ).order_by("-created_at")

    return render(
        request,
        "live_tracking/list.html",
        {
            "tracking_list": sessions
        }
    )

def vehicle_live(request, pk):

    session = get_object_or_404(
        TrackingSession,
        pk=pk
    )

    return render(
        request,
        "live_tracking/vehicle_live.html",
        {
            "session": session,
            "locations": session.locations.all()[:30]
        }
    )

def vehicle_history(request, pk):

    session = get_object_or_404(
        TrackingSession,
        pk=pk
    )

    locations = session.locations.all()

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "locations": locations,
        }
    )

from .models import LiveLocation

def live_tracking_history(request):

    locations = LiveLocation.objects.select_related(
        "session",
        "session__vehicle"
    ).order_by("-received_at")

    return render(
        request,
        "live_tracking/history.html",
        {
            "locations": locations
        }
    )

def import_driver(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        pk=vehicle_id
    )

    result = ImportService.import_driver(vehicle)

    if result["success"]:

        messages.success(
            request,
            "Driver imported successfully."
        )

    else:

        messages.error(
            request,
            result["message"]
        )

    return redirect("live_tracking_list")

def send_consent(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    result = ConsentService.send_consent(session)

    if result["success"]:

        messages.success(
            request,
            "Consent SMS sent."
        )

    else:

        messages.error(
            request,
            result["message"]
        )

    return redirect("live_tracking_list")

def refresh_location(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    result = LocationService.fetch_location(session)

    if result["success"]:

        messages.success(
            request,
            "Location updated."
        )

    else:

        messages.error(
            request,
            result["message"]
        )

    return redirect(
        "vehicle_live",
        pk=session.id
    )
