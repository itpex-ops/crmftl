from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from onepage_order.models import Order, Tracking, TrackingSession
from datetime import datetime
User = get_user_model()
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from  onepage_order.models import Order, Tracking, TrackingSession

@login_required(login_url="/auth/")
def home(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    # Main dashboard metrics
    total_orders = Order.objects.count()
    vehicle_placements = Tracking.objects.filter(vehicle_placed=True).count()
    live_tracking = TrackingSession.objects.filter(tracking_enabled=True).count()

    # The supplied Order model has no cancellation field. Use its
    # manager_approval field for this KPI instead.
    pending_approval = Order.objects.filter(manager_approval="Pending").count()

    # Vehicle number is stored directly on Order in the supplied model.
    total_vehicles = (
        Order.objects.exclude(vehicle_number="")
        .exclude(vehicle_number__isnull=True)
        .values("vehicle_number")
        .distinct()
        .count()
    )

    # Seven calendar days, including today.
    weekly_labels = []
    weekly_orders = []
    weekly_vehicle_placements = []

    for offset in range(7):
        day = start_date + timedelta(days=offset)
        weekly_labels.append(day.strftime("%d %b"))
        weekly_orders.append(Order.objects.filter(created_at__date=day).count())
        weekly_vehicle_placements.append(
            Tracking.objects.filter(
                vehicle_placed=True,
                vehicle_placed_at__date=day,
            ).count()
        )

    context = {
        "total_orders": total_orders,
        "vehicle_placements": vehicle_placements,
        "live_tracking": live_tracking,
        "pending_approval": pending_approval,
        "total_vehicles": total_vehicles,
        "weekly_labels": weekly_labels,
        "weekly_orders": weekly_orders,
        "weekly_vehicle_placements": weekly_vehicle_placements,
        "now": today,
    }
    return render(request, "dashboards/home.html", context)


def auth_page(request):

    # Already logged in
    if request.user.is_authenticated:
        return redirect("home")

    context = {}

    if request.method == "POST":

        action = request.POST.get("action")

        # =====================================================
        # LOGIN
        # =====================================================

        if action == "login":

            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "")

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is not None:

                login(request, user)

                next_url = request.GET.get("next")

                # Only allow internal URLs
                if next_url and next_url.startswith("/"):
                    return redirect(next_url)

                return redirect("home")

            context["login_error"] = "Invalid username or password"

        # =====================================================
        # REGISTER
        # =====================================================

        elif action == "register":

            employee_code = request.POST.get("emp_code", "").strip()
            phone = request.POST.get("phone", "").strip()
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "")
            role = request.POST.get("role")

            if not username or not password:

                context["register_error"] = (
                    "Username and Password required"
                )

            elif User.objects.filter(username=username).exists():

                context["register_error"] = (
                    "Username already exists"
                )

            else:

                user = User.objects.create_user(
                    username=username,
                    password=password,
                )

                user.employee_code = employee_code
                user.phone = phone
                user.role = role
                user.save()

                context["success"] = (
                    "Account created! Please login."
                )

    return render(
        request,
        "authentication/auth.html",
        context,
    )


def logout_user(request):

    logout(request)

    return redirect("auth")


def clear_session(request):

    request.session.flush()

    return redirect("auth")