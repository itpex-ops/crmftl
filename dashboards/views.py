# dashboards/views.py
from django.shortcuts import render
from django.db.models import Sum 
from django.utils import timezone
from customers.models import ExCustomer
from enquiries.models import Enquiry
from orders.models import Order
from vehicles.models import Vehicle, Tracking
from django.contrib.auth.decorators import login_required
from live_tracking.models import TrackingSession, LiveLocation
from accounts.models import (
    CustomerTransaction,
    VehicleTransaction,
    BankTransaction,
    Expense
)
def customer_dashboard(request):
    today = timezone.now()
    context = {
        "total_customers": ExCustomer.objects.count(),
        "active_customers": ExCustomer.objects.filter(is_active=True).count(),
        "inactive_customers": ExCustomer.objects.filter(is_active=False).count(),
        "new_this_month": ExCustomer.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count(),
        "recent_customers": ExCustomer.objects.order_by('-id')
    }
    return render(
        request,
        "dashboards/customer_dashboard.html",
        context
    )

@login_required
def live_tracking_dashboard(request):
    context = {
        "total": TrackingSession.objects.count(),

        "active": TrackingSession.objects.filter(
            status="active"
        ).count(),

        "waiting_location": TrackingSession.objects.filter(
            status="waiting_location"
        ).count(),

        "sms_sent": TrackingSession.objects.filter(
            status="sms_sent"
        ).count(),

        "consent_received": TrackingSession.objects.filter(
            status="consent_received"
        ).count(),

        "paused": TrackingSession.objects.filter(
            status="paused"
        ).count(),

        "stopped": TrackingSession.objects.filter(
            status="stopped"
        ).count(),

        "license_hold": TrackingSession.objects.filter(
            status="license_hold"
        ).count(),

        "expired": TrackingSession.objects.filter(
            status="expired"
        ).count(),

        "error": TrackingSession.objects.filter(
            status="error"
        ).count(),

        # -------------------------
        # RECENT LOCATIONS
        # -------------------------

        "recent_locations": (
            LiveLocation.objects
            .select_related(
                "session",
                "session__vehicle"
            )
            .order_by("-received_at")
        ),
    }

    return render(
        request,
        "dashboards/live_tracking.html",
        context
    )

# dashboards/views.py

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from .services import get_management_dashboard_data

def management_access_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())

        # Superuser always has access.
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Your custom User model has a role field.
        role = getattr(request.user, "role", None)

        # Management dashboard access.
        allowed_roles = {
            "admin",
            "it",
        }

        if role not in allowed_roles:
            raise PermissionDenied(
                "You do not have permission to access the Management Dashboard."
            )

        return view_func(request, *args, **kwargs)

    return wrapper

@management_access_required
def management_dashboard(request):

    context = get_management_dashboard_data()

    return render(
        request,
        "dashboards/management_dashboard.html",
        context,
    )