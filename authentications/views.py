from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User, PasswordResetRequest
from .decorators import allowed_roles
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, get_user_model
import json
User = get_user_model()
from django.contrib.auth.decorators import login_required
from  onepage_order.models import Order, Tracking, TrackingSession
from datetime import datetime,timezone


@login_required
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
            # "cancelled_orders": cancelled_orders,
            # "total_vehicles": total_vehicles,
             "now": timezone.now(),
        },
    )

def auth_page(request):
    # ✅ If already logged in → go to dashboard (no loop)
    if request.user.is_authenticated:
        if request.path == '/auth/':  # or your auth URL
            return redirect('home')
    context = {}

    if request.method == "POST":
        action = request.POST.get("action")

        # 🔐 LOGIN
        if action == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                        
                next_url = request.GET.get('next')

                if next_url:
                    return redirect(next_url)
                else:
                    return redirect ('home') # ✅' correct

            else:
                context['login_error'] = "Invalid username or password"

        # 📝 REGISTER
        elif action == "register":
            employee_code = request.POST.get("emp_code")
            phone = request.POST.get("phone")
            username = request.POST.get("username")
            password = request.POST.get("password")

            # ✅ validation
            if not username or not password:
                context['register_error'] = "Username and Password required"

            elif User.objects.filter(username=username).exists():
                context['register_error'] = "Username already exists"

            else:
                role = request.POST.get("role")  # from form

                user = User.objects.create_user(
                    username=username,
                    password=password
                )

                user.employee_code = employee_code
                user.phone = phone
                user.role = role   # ✅ IMPORTANT
                user.save() 

                context['success'] = "Account created! Please login."

    return render(request, "authentication/auth.html", context)

def logout_user(request):
    logout(request)
    request.session.flush()
    return redirect('auth')

# def clear_session(request):
#     response = redirect('auth')
#     response.delete_cookie('sessionid')  # Django session cookie
#     return response

# from django.shortcuts import redirect

def clear_session(request):
    request.session.flush()   # ✅ clears everything properly
    return redirect('auth')

# @allowed_roles(['admin', 'it'])
# def approve_reset(request, request_id):
#     reset_request = PasswordResetRequest.objects.get(id=request_id)
#     reset_request.status = 'approved'
#     reset_request.approved_at = timezone.now()
#     reset_request.save()

#     # 🔗 Generate reset link
#     reset_link = request.build_absolute_uri(f"/reset-password/{reset_request.token}/")

#     # 📧 Send mail to user
#     send_mail(
#         subject="Password Reset Approved",
#         message=f"Click to reset password: {reset_link}",
#         from_email=settings.EMAIL_HOST_USER,
#         recipient_list=[reset_request.user.email],
#         fail_silently=True,
#     )
#     return redirect('admin_reset_requests')

# @allowed_roles(['admin', 'it'])
# def reject_reset(request, request_id):
#     reset_request = PasswordResetRequest.objects.get(id=request_id)
#     reset_request.status = 'rejected'
#     reset_request.save()
#     return redirect('admin_reset_requests')

# def reset_password(request, token):
#     try:
#         reset_request = PasswordResetRequest.objects.get(token=token, status='approved')
#     except PasswordResetRequest.DoesNotExist:
#         return render(request, "accounts/reset_invalid.html")

#     if request.method == "POST":
#         password = request.POST.get("password")

#         user = reset_request.user
#         user.set_password(password)
#         user.save()

#         # mark as used
#         reset_request.status = 'completed'
#         reset_request.save()

#         return redirect('auth')

#     return render(request, "accounts/reset_password.html")

# @allowed_roles(['admin', 'it'])
# def admin_reset_requests(request):
#     requests = PasswordResetRequest.objects.all().order_by('-created_at')
#     return render(request, "accounts/admin_reset_requests.html", {"requests": requests})



