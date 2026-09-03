from django.core.serializers import python
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
from live_tracking.models import TrackingSession
from live_tracking.services.delete_service import DeleteService
from django.db.models import Q
from .services.modify_service import ModifyService

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

@login_required
def check_consent(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )

    # --------------------------------
    # CHECK CONSENT
    # --------------------------------
    result = ConsentService.check_consent(session)

    if not result.get("success"):

        messages.error(
            request,
            str(result.get(
                "message",
                "Unable to check consent."
            ))
        )

        return redirect("live_tracking_list")

    consent_status = result.get("status")

    # --------------------------------
    # CONSENT RECEIVED
    # --------------------------------
    if consent_status in [
        "approved",
        "accepted",
        "consent_received",
        "active"
    ]:

        session.consent_received = True
        session.status = "consent_received"
        session.save(
            update_fields=[
                "consent_received",
                "status"
            ]
        )

        # --------------------------------
        # ACTIVATE TRACKING
        # --------------------------------
        modify_result = ModifyService.start_tracking(session)

        if modify_result.get("success"):

            session.tracking_enabled = True
            session.status = "waiting_location"

            session.save(
                update_fields=[
                    "tracking_enabled",
                    "status"
                ]
            )

            messages.success(
                request,
                "Consent received. Live tracking has been activated."
            )

        else:

            messages.warning(
                request,
                "Consent received, but live tracking could not be activated: "
                + str(
                    modify_result.get(
                        "message",
                        "Modify API failed."
                    )
                )
            )

    else:

        messages.warning(
            request,
            f"Consent Status : {consent_status}"
        )

    return redirect("live_tracking_list")
def test_location(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    result = LocationService.get_location(
        vehicle.driver_number
    )
    return JsonResponse(result)

def live_tracking_list(request):

    query = request.GET.get("q", "")

    vehicles = Vehicle.objects.select_related(
        "tracking_session",
        "order__tracking"
    ).filter(
        tracking_session__isnull=False
    ).exclude(
        order__tracking__settled=True
    ).order_by("-id")

    if query:
        vehicles = vehicles.filter(
            Q(ftl_no__icontains=query) |
            Q(vehicle_number__icontains=query) |
            Q(driver_number__icontains=query)
        )

    return render(request, "live_tracking/list.html", {
        "vehicles": vehicles
    })

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

def vehicle_live(request, session_id):
    session = get_object_or_404(
        TrackingSession,
        pk=session_id
    )
    return render(
        request,
        "live_tracking/vehicle_live.html",
        {
            "session": session,
            "locations": session.locations.all(),
        }
    )

def vehicle_history(request, pk):

    session = get_object_or_404(
        TrackingSession,
        pk=pk
    )

    locations = session.locations.all().order_by("-received_at")

    # Keep only the latest record for each latitude/longitude
    history = []
    seen = set()

    for location in locations:

        key = (
            location.latitude,
            location.longitude
        )

        if key not in seen:
            seen.add(key)
            history.append(location)

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "history": history,
        }
    )

def live_tracking_history(request,pk):

    session = get_object_or_404(
            TrackingSession,
            pk=pk
        )

    locations = session.locations.all().order_by("-received_at")

    # Keep only the latest record for each latitude/longitude
    history = []
    seen = set()

    for location in locations:

        key = (
            location.latitude,
            location.longitude
        )

        if key not in seen:
            seen.add(key)
            history.append(location)

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "history": history,
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

    result = LocationService.get_location(session)
    if not result.get("success"):
        messages.warning(
            request,
            result.get(
                "message",
                "Unable to retrieve the vehicle location."
            )
        )

        return redirect(
            "vehicle_live",
            session_id=session.id
        )

    location = result.get("location")

    # --------------------------------------------------
    # NO LOCATION AVAILABLE
    # --------------------------------------------------

    if not location:
        messages.warning(
            request,
            "Current vehicle location is not available yet. "
            "Telenity has not retrieved the location."
        )

        return redirect(
            "vehicle_live",
            session_id=session.id
        )

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    # --------------------------------------------------
    # LOCATION NOT RETRIEVED / NO COORDINATES
    # --------------------------------------------------

    if latitude is None or longitude is None:

        status = location.get(
            "location_status",
            "Not Retrieved"
        )

        messages.warning(
            request,
            f"Vehicle location is currently unavailable "
            f"({status}). Please try again later."
        )

        return redirect(
            "vehicle_live",
            session_id=session.id
        )

    # --------------------------------------------------
    # SAVE LOCATION ONLY WHEN COORDINATES EXIST
    # --------------------------------------------------

    LiveLocation.objects.create(
        session=session,
        tracked=location.get("tracked", False),
        location_status=location.get(
            "location_status",
            ""
        ),
        address=location.get(
            "address",
            ""
        ),
        latitude=latitude,
        longitude=longitude,
        accuracy=location.get(
            "accuracy",
            0
        ) or 0,
        location_name=location.get(
            "location_name",
            ""
        ),
        received_at=timezone.now()
    )

    # Update latest location in TrackingSession

    session.latitude = latitude
    session.longitude = longitude
    session.last_location = (
        location.get("location_name")
        or location.get("address")
        or ""
    )
    session.location_status = location.get(
        "location_status",
        ""
    )
    session.last_updated = timezone.now()
    session.status = "active"
    session.tracking_enabled = True
    session.save(
        update_fields=[
            "latitude",
            "longitude",
            "last_location",
            "location_status",
            "last_updated",
            "status",
            "tracking_enabled",
        ]
    )

    messages.success(
        request,
        "Vehicle location updated successfully."
    )

    return redirect(
        "vehicle_live",
        session_id=session.id
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

