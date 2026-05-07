# Create views here.
from django.shortcuts import render ,redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Enquiry,Notification ,VEHICLE_TYPES
from orders.models import Order
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
import json
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def create_enquiry(request):
    vehicle_types = Enquiry._meta.get_field("vehicle_type").choices

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

        # ROUTES
        origins = request.POST.getlist("origin[]")
        destinations = request.POST.getlist("destination[]")

        routes = []
        for i in range(max(len(origins), len(destinations))):
            route = {
                "origin": origins[i] if i < len(origins) else "",
                "destination": destinations[i] if i < len(destinations) else "",
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

            status='pending',  # ✅ FIXED

            routes=routes,
            created_by=request.user
        )

        # 🔔 NOTIFICATION
        admins = User.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"New enquiry {enquiry.enquiry_no} created by {request.user.username}"
            )

        messages.success(request, f"{enquiry.enquiry_no} created successfully!")

        return redirect("create_enquiry")

    # ✅ THIS WAS MISSING
    return render(request, "enquiry/create.html", 
        { "vehicle_types": vehicle_types}
    )

@login_required
def enquiry_list(request):
    user = request.user

    is_admin = user.role == 'admin'
    is_sales = user.role == 'sales'

    # ✅ Admin sees all
    if is_admin:
        base_qs = Enquiry.objects.exclude(status='confirmed') 
    else:
        base_qs = Enquiry.objects.exclude(status='confirmed')

    total_count = base_qs.count()
    confirmed_count = base_qs.filter(status='confirmed').count()
    pending_count = base_qs.filter(status='pending').count()
    cancelled_count = base_qs.filter(status='cancelled').count()

    enquiries = base_qs.order_by('-id')

    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'total_count': total_count,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'is_admin': is_admin,
        'is_sales': is_sales,
    })

@login_required
def update_status(request, id, status):
    if request.method == "POST":
        data = json.loads(request.body)

        enquiry = Enquiry.objects.get(id=id)

        if status == "confirmed":
            enquiry.status = "confirmed"
            enquiry.approval_rate = data.get("approval_rate")

        enquiry.save()

        return JsonResponse({"success": True})

@login_required
def update_enquiry_status(request, id, action):
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

@login_required
def update_pitch(request, id):

    if request.method != "POST":
        return JsonResponse({"success": False, "msg": "Invalid request method"})

    enquiry = get_object_or_404(Enquiry, id=id)

    # 🚫 BLOCK if already confirmed
    if enquiry.status == "confirmed":
        return HttpResponseForbidden("Already confirmed. Cannot modify.")

    remarks = request.POST.get("remarks") or ""
    pitch_rate = request.POST.get("pitch_rate")
    is_approved = request.POST.get("is_approved") == "true"

    # ✅ Admin / Manager check
    can_approve = (
        request.user.role == "admin" or
        request.user.is_superuser or
        request.user.groups.filter(name="Managers").exists()
    )

    status = (enquiry.status or "").lower()

    # ================= ADMIN CONFIRM (ANY STAGE) =================
    if is_approved:
        if not can_approve:
            return HttpResponseForbidden("Only admin/manager can approve")

        enquiry.status = "confirmed"
        enquiry.approval_rate = pitch_rate

        enquiry.save()

        # 👉 DO NOT create order here (pricing page will handle)
        return redirect("enquiry_list")

    # ================= SALES PITCH FLOW =================
    if status in ["pending_pitch1", "waiting for rate approval", ""]:
        enquiry.pitch1 = pitch_rate
        enquiry.approval_rate = pitch_rate
        enquiry.pitch1_remarks = remarks
        enquiry.status = "pending_pitch2"

    elif status == "pending_pitch2":
        enquiry.pitch2 = pitch_rate
        enquiry.approval_rate = pitch_rate
        enquiry.pitch2_remarks = remarks
        enquiry.status = "pending_pitch3"

    elif status == "pending_pitch3":
        enquiry.pitch3 = pitch_rate
        enquiry.approval_rate = pitch_rate
        enquiry.pitch3_remarks = remarks

        # ✅ No auto confirm
        enquiry.status = "pending_pitch3"  # stay here until admin acts

    else:
        enquiry.status = "pending_pitch1"

    enquiry.save()

    return redirect("enquiry_list")

@login_required
def notifications(request):
    notes = request.user.notification_set.all().order_by('-id')

    # mark as read
    notes.update(is_read=True)

    return render(request, 'notifications.html', {'notes': notes})
