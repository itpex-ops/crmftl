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

from django.shortcuts import render, get_object_or_404
from vehicles.models import Vehicle
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import TrackingSession
from .services.consent_service import ConsentService

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from live_tracking.models import TrackingSession
from live_tracking.services.delete_service import DeleteService

def delete_tracking(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    result = DeleteService.delete_tracking(session)

    print("=" * 80)
    print("DELETE RESULT")
    print(result)
    print("=" * 80)

    if result.get("success"):

        messages.success(
            request,
            f"{session.driver_mobile} removed successfully from SmartTrail."
        )

    else:

        message = result.get("message", "Unable to delete tracking.")

        if isinstance(message, dict):
            message = str(message)

        messages.error(
            request,
            message
        )

    return redirect("live_tracking_list")

def send_consent(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    result = ConsentService.check_consent(session)

    if result["success"]:
        messages.success(request, "Consent status checked successfully.")
    else:
        messages.error(request, str(result["message"]))

    return redirect("live_tracking_list")

def check_consent(request, session_id):
    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )
    result = ConsentService.check_consent(session)

    if result["success"]:

        messages.success(
            request,
            f"Consent Status : {result['status']}"
        )

    else:

        messages.error(
            request,
            str(result["message"])
        )

    return redirect("live_tracking_list")

def test_location(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    result = LocationService.get_location(
        vehicle.driver_number
    )
    return JsonResponse(result)

def live_tracking_list(request):
    vehicles = Vehicle.objects.select_related(
        "order"
    ).order_by("-id")
    return render(
        request,
        "live_tracking/list.html",
        {
            "vehicles": vehicles
        }
    )

def live_tracking_setup(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    session = TrackingSession.objects.filter(
        vehicle=vehicle
    ).first()
    return render(
        request,
        "live_tracking/setup.html",
        {
            "vehicle": vehicle,
            "session": session,
        }
    )

def test_consent_auth(request):

    result = ConsentAuthService.get_consent_token()

    return JsonResponse(result)

def test_tracking_auth(request):
    result = TrackingAuthService.get_tracking_token()
    print(type(result))
    print(result)
    return JsonResponse(result, safe=False)

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

def vehicle_live(request, pk):
    session = get_object_or_404(
        TrackingSession,
        pk=pk
    )
    print(f"Vehicle Live View: Session ID {session.id}, Vehicle ID {session.vehicle.id}")
    print(f"Driver Mobile: {session.driver_mobile}, Status: {session.status}")
    print(f"Last Location: {session.last_location}, Last Updated: {session.last_updated}")
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

    if result.get("success"):

        if result.get("already_exists"):
            messages.info(
                request,
                "Driver is already registered in Telenity. Using the existing tracking profile."
            )
        else:
            messages.success(
                request,
                "Driver imported successfully into Telenity."
            )

        return redirect(
            "live_tracking_setup",
            vehicle_id=vehicle.id
        )

    error_message = result.get("message", "Import failed.")

    if isinstance(error_message, dict):
        if "errorMessage" in error_message:
            error_message = error_message["errorMessage"]
        elif "raw_response" in error_message:
            error_message = error_message["raw_response"]
        else:
            error_message = str(error_message)

    messages.error(
        request,
        error_message
    )

    return redirect(
        "live_tracking_setup",
        vehicle_id=vehicle.id
    )

def refresh_location(request, session_id):
    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )
    result = LocationService.fetch_location(session)
    session.refresh_from_db()

    print("=" * 80)
    print("DATABASE VALUES")
    print("Status:", session.status)
    print("Latitude:", session.latitude)
    print("Longitude:", session.longitude)
    print("Tracking Enabled:", session.tracking_enabled)
    print("Location Status:", session.location_status)
    print("=" * 80)
    if result["success"]:
        messages.success(request, "Location updated.")
    else:
        messages.error(request, result["message"])
    return redirect(
        "vehicle_live",
        pk=session.id
    )

def tracking_history(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    history = session.locations.all()

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "history": history
        }
    )