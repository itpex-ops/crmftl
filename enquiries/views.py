# Create your views here.
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render ,redirect ,get_object_or_404
from authentications.decorators import allowed_roles
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from .models import Enquiry ,Notification
from django.db import models
from django.db.models import Q
from django.utils import timezone
from orders.models import Order
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
import json
# from authentications.models import User

# User.objects.create_superuser(
#     username="admin",
#     email="admin@parcelex.in",
#     password="admin123",
#     employee_code="EMP001"   # ✅ REQUIRED
# )
#@allowed_roles(['sales'])
#@login_required

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Enquiry, VEHICLE_TYPES


def create_enquiry(request):

    if request.method == "POST":

        customer_name = request.POST.get("customer_name")
        customer_contact = request.POST.get("customer_contact")
        email = request.POST.get("email")

        lead_source = request.POST.get("lead_source")
        reference_name = request.POST.get("reference_name")

        pickups = int(request.POST.get("pickup") or 1)
        deliveries = int(request.POST.get("delivery") or 1)

        vehicle_type = request.POST.get("vehicle_type")
        vehicle_description = request.POST.get("vehicle_desc")
        kms = request.POST.get("kms")

        material = request.POST.get("material")
        pieces = request.POST.get("pieces") or None
        tonnage = request.POST.get("tonnage") or None

        dimension_unit = request.POST.get("dimension_unit")

        length = request.POST.get("length") or None
        breadth = request.POST.get("breadth") or None
        height = request.POST.get("height") or None

        expected_rate = request.POST.get("expected_rate") or None

        status = "Waiting For Rate Approval"

        # ROUTES
        origins = request.POST.getlist("origin[]")
        origin_pins = request.POST.getlist("origin_pin[]")

        destinations = request.POST.getlist("destination[]")
        destination_pins = request.POST.getlist("destination_pin[]")

        routes = []

        for i in range(max(len(origins), len(destinations))):

            route = {
                "origin": origins[i] if i < len(origins) else "",
                "origin_pin": origin_pins[i] if i < len(origin_pins) else "",

                "destination": destinations[i] if i < len(destinations) else "",
                "destination_pin": destination_pins[i] if i < len(destination_pins) else "",
            }

            if route["origin"] or route["destination"]:
                routes.append(route)

        enquiry = Enquiry.objects.create(

            customer_name=customer_name,
            customer_contact=customer_contact,
            email=email,

            lead_source=lead_source,
            reference_name=reference_name,

            pickups=pickups,
            deliveries=deliveries,

            vehicle_type=vehicle_type,
            vehicle_description=vehicle_description,
            kms=kms,

            material=material,

            pieces=int(pieces) if pieces else None,
            tonnage=float(tonnage) if tonnage else None,

            dimension_unit=dimension_unit,

            length=float(length) if length else None,
            breadth=float(breadth) if breadth else None,
            height=float(height) if height else None,

            expected_rate=float(expected_rate) if expected_rate else None,

            status=status,
            routes=routes,

            created_by=request.user
        )

        messages.success(
            request,
            f"{enquiry.enquiry_no} created successfully!"
        )

        return redirect("create_enquiry")

    context = {
        "vehicle_types": VEHICLE_TYPES
    }

    return render(request, "enquiry/create.html", context)
# Only sales or admin users can access

def is_sales(user):
    return user.is_authenticated and (user.role in ['sales', 'admin'])

def is_fleet(user):
    return user.is_authenticated and (user.role in ['fleet','admin'])

#@login_required
#@user_passes_test(is_sales)
def enquiry_list(request):

    user = request.user

    # ================= ROLE FLAGS =================
    is_admin = (
        user.is_superuser or
        user.groups.filter(name="admin").exists()
    )
    print(is_admin)
    is_sales = user.groups.filter(name="sales").exists()

    is_admin = getattr(user, "role", None) == "admin"


    # ================= BASE QUERY =================
    if is_admin or is_admin:
        base_qs = Enquiry.objects.all()
    else:
        base_qs = Enquiry.objects.filter(created_by=user)


    # ================= SEARCH =================
    query = request.GET.get('q')
    if query:
        base_qs = base_qs.filter(
            Q(customer_name__icontains=query) |
            Q(customer_contact__icontains=query)
        )


    # ================= COUNTS =================
    total_count = base_qs.count()
    confirmed_count = base_qs.filter(status='confirmed').count()
    pending_count = base_qs.filter(status__icontains='pending').count()
    cancelled_count = base_qs.filter(status='cancelled').count()


    # ================= FINAL LIST =================
    # 👉 Managers see "Waiting For Rate Approval"
    # 👉 sales see their own records
    if is_admin:
       enquiries = base_qs.exclude(status='confirmed').order_by('-id')
    else:
        enquiries = base_qs.order_by('-id')


    # ================= RENDER =================
    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'query': query or '',
        'total_count': total_count,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'is_admin': is_admin,
        'is_sales': is_sales,
    })

1
#@login_required
def delete_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)

    # ✅ Allow admin OR owner
    if not (request.user.role == 'admin' or enquiry.created_by == request.user):
        messages.error(request, "❌ You are not authorized")
        return redirect('enquiry_list')

    if request.method == "POST":
        enquiry.delete()
        messages.success(request, "✅ Enquiry deleted")
    
    return redirect('enquiry_list')

#@login_required
# @allowed_roles(['admin'])
def update_pitch1(request, enquiry_id, status):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    allowed_status = [
        'Waiting For Rate Approval',
        'pending_pitch1',
        'pending_pitch2',
        'pending_pitch3',
        'confirmed',
        'cancelled',
        'pending'
    ]
    if status in allowed_status:
        enquiry.status = status
        # If you want to update expected_rate from form uncomment below
        # enquiry.expected_rate = request.POST.get("expected_rate")
        enquiry.approved_by = request.user
        enquiry.save()
    return redirect('enquiry_list')  # removed comma

#@allowed_roles(['admin')
#@login_required
#@user_passes_test(is_sales)
@csrf_exempt
def edit_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    if request.method == "POST":
        data = json.loads(request.body)
        pitch = data.get("pitch")
        remarks = data.get("remarks")
        # Save only the relevant pitch based on current status
        if enquiry.status in ["pending_pitch3", "confirmed"] and pitch:
            enquiry.pitch3 = pitch
            enquiry.approval_rate = pitch
            enquiry.status = "confirmed"
        elif enquiry.status == "pending_pitch2" and pitch:
            enquiry.pitch2 = pitch
            enquiry.approval_rate = pitch
            enquiry.status = "pending_pitch2"
        elif enquiry.status in ["pending_pitch1", "Waiting For Rate Approval"] and pitch:
            enquiry.pitch1 = pitch
            enquiry.approval_rate = pitch
            enquiry.status = "pending_pitch1"
        else:
            enquiry.status = "Waiting For Rate Approval"
        enquiry.remarks = remarks
        enquiry.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})

#@login_required
#@user_passes_test(is_sales)
def confirm_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    if enquiry.pitch1 or enquiry.pitch2 or enquiry.pitch3:
        enquiry.status = "confirmed"
        enquiry.approved_by = request.user
        enquiry.approved_rate = (
            enquiry.pitch3 or
            enquiry.pitch2 or
            enquiry.pitch1
        )
        enquiry.save()
        messages.success(request, "✅ Enquiry Confirmed")
    else:
        messages.error(request, "❌ No pitch available to confirm")
    return redirect('enquiry_list')

def cancel_enquiry(request, id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reason = data.get("reason", "")

            enquiry = get_object_or_404(Enquiry, id=id)

            # 🔒 Prevent double cancel
            if enquiry.status == "cancelled":
                return JsonResponse({"success": False, "msg": "Already cancelled"})

            enquiry.status = "cancelled"
            enquiry.cancel_reason = reason
            enquiry.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

@csrf_exempt
def update_pitch2(request, enquiry_id, status):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            remarks = (data.get("remarks") or "").strip()
            pitch_rate = data.get("pitch_rate")
            enquiry = get_object_or_404(Enquiry, id=enquiry_id)
            status = status.lower().strip()
            if status in ["pending_pitch1", "waiting for rate approval"]:
                enquiry.pitch1_remarks = remarks
                enquiry.pitch1 = pitch_rate
                enquiry.status = "pending_pitch2"
            elif status == "pending_pitch2":
                enquiry.pitch2_remarks = remarks
                enquiry.pitch2 = pitch_rate
                enquiry.status = "pending_pitch3"
            elif status == "pending_pitch3":
                enquiry.pitch3_remarks = remarks
                enquiry.pitch3 = pitch_rate
                enquiry.status = "confirmed"
                if pitch_rate is not None:
                    enquiry.approval_rate = pitch_rate
            if enquiry.status == "confirmed" and enquiry.approval_rate is None:
                enquiry.approval_rate = pitch_rate
            enquiry.save()
            return JsonResponse({"success": True, "status": enquiry.status})
        except Exception as e:
            return JsonResponse({"success": False, "msg": str(e)})
    return JsonResponse({"success": False, "msg": "Invalid request"})

def update_status(request, id, status):
    if request.method == "POST":
        data = json.loads(request.body)

        enquiry = Enquiry.objects.get(id=id)

        if status == "confirmed":
            enquiry.status = "confirmed"
            enquiry.approval_rate = data.get("approval_rate")

        enquiry.save()

        return JsonResponse({"success": True})

def enquiry_action(request, id):
    if request.method == "POST":
        data = json.loads(request.body)
        action = data.get("action")

        enquiry = Enquiry.objects.get(id=id)

        if action == "cancel":
            enquiry.status = "cancelled"
            enquiry.cancel_reason = data.get("reason")

        elif action == "disagree":
            enquiry.status = "disagreed"

        enquiry.save()

        return JsonResponse({"success": True})

def update_enquiry_status1(request, id, action):
    if request.method == "POST":
        data = json.loads(request.body)
        enquiry = Enquiry.objects.get(id=id)
        if action == "confirm":
            enquiry.status = "confirmed"
            enquiry.approval_rate = data.get("approval_rate")
            enquiry.save()

            order = Order.objects.create(
                enquiry=enquiry,
               finalized_rate=enquiry.approval_rate
            )

            return JsonResponse({
                "success": True,
                "redirect": True,
                "order_id": order.id
            })
        elif action == "disagree":
            enquiry.status = "disagree"
            enquiry.disagree_reason = data.get("disagree_reason")
        elif action == "cancel":
            enquiry.status = "cancelled"
            enquiry.cancel_reason = data.get("cancel_reason")
        enquiry.save()
        return JsonResponse({
            "success": True,
            "redirect": action == "confirm"
        })
    return JsonResponse({"success": False})

@login_required
def update_enquiry_status2(request, id, action):
    enquiry = get_object_or_404(Enquiry, id=id)
    if request.method == "POST":
        if action == "confirm":
            enquiry.status = "confirmed"
            enquiry.approval_rate = request.POST.get("approve_rate") or 0
            enquiry.save()
            order, created = Order.objects.get_or_create(
                enquiry=enquiry,
                defaults={
                    "finalized_rate": enquiry.approval_rate,
                    "customer_name": enquiry.customer_name,
                    "customer_contact": enquiry.customer_contact,
                    "routes": enquiry.routes,
                    "vehicle_type": enquiry.vehicle_type,
                    "created_by": request.user,
                }
            )
            if not created:
                order.finalized_rate = enquiry.approval_rate
                order.save()
            messages.success(request, "Enquiry confirmed successfully.")
            return redirect("pricing_page", enquiry_id=enquiry.id)
        elif action == "disagree":
            enquiry.status = "disagree"
            enquiry.disagree_reason = request.POST.get("disagree_reason", "")
            enquiry.save()
            messages.warning(request, "Enquiry marked as disagree.")
            return redirect("enquiry_list")
        elif action == "cancel":
            enquiry.status = "cancelled"
            enquiry.cancel_reason = request.POST.get("cancel_reason", "")
            enquiry.save()
            messages.error(request, "Enquiry cancelled.")
            return redirect("enquiry_list")
    return redirect("enquiry_list")

def update_pitch3(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)

    # 🔒 LOCK CHECK
    if enquiry.status == "confirmed":
        messages.error(request, "Already confirmed. Locked.")
        return redirect('enquiry_list')

    if request.method == "POST":

        rate = request.POST.get("pitch_rate")
        remarks = request.POST.get("remarks")
        is_approved = request.POST.get("is_approved") == "true"

        # ----------- SAVE PITCH -----------
        if not enquiry.pitch1:
            enquiry.pitch1 = rate
            enquiry.pitch1_remarks = remarks
            enquiry.status = "pending_pitch2"

        elif not enquiry.pitch2:
            enquiry.pitch2 = rate
            enquiry.pitch2_remarks = remarks
            enquiry.status = "pending_pitch3"

        elif not enquiry.pitch3:
            enquiry.pitch3 = rate
            enquiry.pitch3_remarks = remarks

        # ----------- CONFIRM ANYTIME -----------
        if is_approved and request.user.role == "admin":
            enquiry.approval_rate = rate
            enquiry.status = "confirmed"
            enquiry.confirmed_at = timezone.now()

        enquiry.save()

        # 🔔 notify
        create_notification(enquiry, request.user, "Pitch Updated")

    return redirect('enquiry_list')

def create_notification(enquiry, actor, action):

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # notify admins when sales acts
    if actor.role == "sales":
        users = User.objects.filter(role="admin")

    # notify sales when admin acts
    else:
        users = User.objects.filter(role="sales")

    for user in users:
        Notification.objects.create(
            user=user,
            enquiry=enquiry,
            message=f"{actor.username} {action} - {enquiry.enquiry_no}"
        )

def update_enquiry_status(request, id, action):
    enquiry = get_object_or_404(Enquiry, id=id)

    # 🔒 LOCK
    if enquiry.status == "confirmed":
        messages.error(request, "This enquiry is locked")
        return redirect("enquiry_list")

    if request.user.role != "sales":
        messages.error(request, "Not allowed")
        return redirect("enquiry_list")

    if request.method == "POST":

        if action == "confirm":
            messages.error(request, "Only admin can confirm")
            return redirect("enquiry_list")

        elif action == "disagree":
            enquiry.status = "disagreed"
            enquiry.cancel_reason = request.POST.get("disagree_reason")

        elif action == "cancel":
            enquiry.status = "cancelled"
            enquiry.cancel_reason = request.POST.get("cancel_reason")

        enquiry.save()

        create_notification(enquiry, request.user, "updated status")

    return redirect("enquiry_list")


def update_pitch(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)

    # 🔒 LOCK
    if enquiry.status == "confirmed":
        messages.error(request, "Already confirmed. Locked.")
        return redirect("enquiry_list")

    if request.method == "POST":

        rate = request.POST.get("pitch_rate")
        remarks = request.POST.get("remarks")
        is_approved = request.POST.get("is_approved") == "true"

        # -------- SAVE PITCH --------
        if not enquiry.pitch1:
            enquiry.pitch1 = rate
            enquiry.pitch1_remarks = remarks
            enquiry.status = "pending_pitch2"

        elif not enquiry.pitch2:
            enquiry.pitch2 = rate
            enquiry.pitch2_remarks = remarks
            enquiry.status = "pending_pitch3"

        elif not enquiry.pitch3:
            enquiry.pitch3 = rate
            enquiry.pitch3_remarks = remarks

        # -------- ADMIN CONFIRM ANYTIME --------
        if is_approved and request.user.role == "admin":
            enquiry.approval_rate = rate
            enquiry.status = "confirmed"
            enquiry.confirmed_at = timezone.now()

        enquiry.save()

        create_notification(enquiry, request.user, "updated pitch")

    return redirect("enquiry_list")

def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by('-id')
    return render(request, "notifications.html", {"notes": notes})


def mark_read(request, id):
    note = Notification.objects.get(id=id, user=request.user)
    note.is_read = True
    note.save()
    return JsonResponse({"status": "ok"})


def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})