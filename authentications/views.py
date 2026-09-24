from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from onepage_order.models import Order, Tracking, TrackingSession
from datetime import datetime

User = get_user_model()

def home(request):

    total_orders = Order.objects.count()

    vehicle_placements = Tracking.objects.filter(
        vehicle_placed=True
    ).count()

    live_tracking = TrackingSession.objects.filter(
        tracking_enabled=True
    ).count()

    now = datetime.now().date()

    return render(
        request,
        "dashboards/home.html",
        {
            "total_orders": total_orders,
            "vehicle_placements": vehicle_placements,
            "live_tracking": live_tracking,
            "now": now,
        },
    )


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