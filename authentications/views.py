from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User, PasswordResetRequest
from .decorators import allowed_roles
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import render, redirect

User = get_user_model()

def auth_page(request):
    # ✅ If already logged in → go to dashboard (no loop)
    if request.user.is_authenticated:
        if request.path == '/auth/':  # or your auth URL
            return redirect('user_dashboard')
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
                    return redirect ('user_dashboard') # ✅' correct

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

def redirect_user_dashboard(user):

    if not user.role:
        return redirect('/auth/')  # fallback safe

    role_redirect_map = {
        "sales": "sales_dashboard",
        "admin": "admin_dashboard",
        "fleet": "fleet_dashboard",
        "accounts": "accounts_dashboard",
        "it": "it_dashboard",
    }

    url_name = role_redirect_map.get(user.role.lower())

    if not url_name:
        return redirect('user_dashboard')

    return redirect(url_name)


def user_dashboard(request):
    return render(request,"enquiry/create.html") # "dashboards/user.html")


def auth_page0(request):
    # 🔁 Redirect if already logged in
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)
    context = {}
    if request.method == "POST":
        action = request.POST.get("action")
        # ---------------- LOGIN ----------------
        if action == "login":
            username = request.POST.get("username") # emp_code
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user:
                if not user.is_approved:
                    context['login_error'] = "Account not approved by admin"
                    context['active_tab'] = "login"
                else:
                    login(request, user)
                    return redirect_user_dashboard(user)
            else:
                context['login_error'] = "Invalid username or password"
                context['active_tab'] = "login"
        # ---------------- REGISTER ----------------
        elif action == "register":
            emp_code = request.POST.get("emp_code")
            phone = request.POST.get("phone")
            username = request.POST.get("username")
            password = request.POST.get("password")
            if User.objects.filter(username=username).exists():
                context['register_error'] = "Username already exists"
            elif User.objects.filter(employee_code=emp_code).exists():
                context['register_error'] = "Employee code already used"
            else:
                User.objects.create(
                    username=username,
                    password=make_password(password),
                    employee_code=emp_code,
                    phone=phone,
                        is_active=True,
                    is_approved=False
                )
                context['register_success'] = "Account created. Waiting for admin approval"
            context['active_tab'] = "register"

        # # ---------------- FORGOT PASSWORD ----------------
        elif action == "forgot":
            username = request.POST.get("username")
            reason = request.POST.get("reason")
            try:
                user = User.objects.get(username=username)
                if PasswordResetRequest.objects.filter(user=user, status='pending').exists():
                    context['forgot_error'] = "Request already pending"
                else:
                    PasswordResetRequest.objects.create(
                        user=user,
                        reason=reason
                    )
                    # 📧 Email to IT
                    send_mail(
                        subject="Password Reset Request",
                        message=f"User: {user.username}\nReason: {reason}",
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=["it@parcelex.in"],
                        fail_silently=True,
                    )
                    context['forgot_success'] = "Request sent to IT"
            except User.DoesNotExist:
                context['forgot_error'] = "User not found"
            context['active_tab'] = "forgot"
    return render(request, "authentication/auth.html", context)

def auth_page1(request):
    context = {}
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect_user_dashboard(user)
            context.update({
                'login_error': "Invalid username or password",
                'active_tab': "login"
            })
        elif action == "register":
            emp_code = request.POST.get("emp_code")
            phone = request.POST.get("phone")
            username = request.POST.get("username")
            password = request.POST.get("password")
            if User.objects.filter(username=username).exists():
                context['register_error'] = "Username already exists"
            elif User.objects.filter(employee_code=emp_code).exists():
                context['register_error'] = "Employee code already used"
            else:
                User.objects.create(
                    username=username,
                    password=make_password(password),
                    employee_code=emp_code,
                    phone=phone,
                    role='sales'  # default
                )
                context['register_success'] = "Account created. Login now."
            context['active_tab'] = "register"
        #elif action == "forgot":
            # username = request.POST.get("username")
            # reason = request.POST.get("reason")
            # try:
            #     user = User.objects.get(username=username)
            #     if PasswordResetRequest.objects.filter(user=user, status='pending').exists():
            #         context['forgot_error'] = "Request already pending"
            #     else:
            #         PasswordResetRequest.objects.create(
            #             user=user,
            #             reason=reason
            #         )
            #         send_mail(
            #             subject="Password Reset Request",
            #             message=f"User: {user.username}\nReason: {reason}",
            #             from_email=settings.EMAIL_HOST_USER,
            #             recipient_list=["it@parcelex.in"],
            #             fail_silently=True,
            #         )
            #         context['forgot_success'] = "Request sent to IT"
            # except User.DoesNotExist:
            #     context['forgot_error'] = "User not found"
            context['active_tab'] = "forgot"
    return render(request, "authentication/auth.html", context)

# @login_required
# def sales_dashboard(request):
#     return render(request ,'enquiry/create.html')
#     #return render(request, "dashboards/sales.html")

# @login_required
# def admin_dashboard(request):
#     return render(request, "dashboards/admin.html")

# @login_required
# def fleet_dashboard(request):
#     return render(request, "dashboards/fleet.html")

# @login_required
def it_dashboard(request):
    return render(request, "dashboards/it.html")

#@login_requiredz


# @login_required
# @allowed_roles(['accounts', 'admin'])
# def accounts_dashboard(request):
#     #orders = Order.objects.all().order_by('-created_at')
#     return render(request, "accounts/accounts_dashboard.html") #, {"orders": orders})

# # # 🔁 ROLE BASED REDIRECT

# def role_required(role):
#     def decorator(view_func):
#         def wrapper(request, *args, **kwargs):
#             if request.user.role != role:
#                 return redirect("user_dashboard")
#             return view_func(request, *args, **kwargs)
#         return wrapper
#     return decorator

# from django.utils import timezone
# from django.contrib.admin.views.decorators import staff_member_required
# from django.views.decorators.http import require_POST

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



