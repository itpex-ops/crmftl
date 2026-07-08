from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from vehicles.models import Vehicle
from .models import TrackingSession, LiveLocation
from .services import TelenityService

def live_tracking_dashboard(request):

    total = TrackingSession.objects.count()
    active = TrackingSession.objects.filter(status="active").count()
    pending = TrackingSession.objects.filter(status="pending").count()
    stopped = TrackingSession.objects.filter(status="stopped").count()

    recent_locations = LiveLocation.objects.select_related(
        "session",
        "session__vehicle"
    ).order_by("-received_at")[:10]

    context = {
        "total": total,
        "active": active,
        "pending": pending,
        "stopped": stopped,
        "recent_locations": recent_locations,
    }

    return render(
        request,
        "live_tracking/dashboard.html",
        context
    )


def live_tracking_list(request):
    """
    List all tracking sessions
    """

    tracking_list = TrackingSession.objects.select_related(
        "vehicle",
        "vehicle__order"
    ).order_by("-created_at")

    return render(
        request,
        "live_tracking/list.html",
        {
            "tracking_list": tracking_list
        }
    )


def vehicle_live(request, pk):
    """
    Individual Vehicle Tracking
    """

    session = get_object_or_404(
        TrackingSession,
        pk=pk
    )

    locations = session.locations.all()[:20]

    return render(
        request,
        "live_tracking/vehicle_live.html",
        {
            "session": session,
            "locations": locations,
        }
    )


def tracking_history(request, pk):

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


def send_tracking_sms(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        pk=vehicle_id
    )

    session, created = TrackingSession.objects.get_or_create(
        vehicle=vehicle,
        defaults={
            "driver_mobile": vehicle.driver_number,
            "tracking_reference": f"TRK{vehicle.id}",
        }
    )

    # try:

    #     api = TelenityService()

    #     response = api.send_tracking_sms(
    #         vehicle.driver_number
    #     )

    #     session.status = "sms_sent"
    #     session.save()

    #     messages.success(
    #         request,
    #         "Tracking SMS sent successfully."
    #     )

    # except Exception as e:

    #     messages.error(
    #         request,
    #         str(e)
    #     )

    try:
        
        api = TelenityService()

        response = api.send_tracking_sms(vehicle.driver_number)

        session.tracking_reference = response["tracking_reference"]

        # Demo Mode (until Telenity API is available)
        session.status = "active"
        session.consent_received = True

        session.save()

        messages.success(
            request,
            "Tracking SMS sent successfully. (Demo Mode: Tracking Activated)"
        )
    except Exception as e:
        messages.error(
            request,
            str(e)
        )
    
    return redirect("live_tracking_list")


def refresh_location(request, pk):

    session = get_object_or_404(
        TrackingSession,
        pk=pk
    )

    # try:

    #     api = TelenityService()

    #     data = api.get_location(
    #         session.tracking_reference
    #     )

    #     session.last_latitude = data["latitude"]
    #     session.last_longitude = data["longitude"]
    #     session.last_accuracy = data["accuracy"]
    #     session.last_location = data["location"]
    #     session.last_updated = timezone.now()
    #     session.status = "active"

    #     session.save()

    #     LiveLocation.objects.create(
    #         session=session,
    #         latitude=data["latitude"],
    #         longitude=data["longitude"],
    #         accuracy=data["accuracy"],
    #         location_name=data["location"],
    #         received_at=timezone.now(),
    #     )

    #     messages.success(
    #         request,
    #         "Location Updated."
    #     )

    # except Exception as e:

    #     messages.error(
    #         request,
    #         str(e)
    #     )
    try:

        api = TelenityService()

        data = api.get_location(session.tracking_reference)

        session.last_latitude = data["latitude"]
        session.last_longitude = data["longitude"]
        session.last_location = data["location"]
        session.last_accuracy = data["accuracy"]
        session.status = data["status"]
        session.last_updated = timezone.now()

        session.save()

        LiveLocation.objects.create(
            session=session,
            latitude=data["latitude"],
            longitude=data["longitude"],
            accuracy=data["accuracy"],
            location_name=data["location"],
            received_at=timezone.now()
        )
    except Exception as e:

        messages.error(
            request,
            str(e)
        )

    return redirect(
        "vehicle_live",
        pk=session.id
    )