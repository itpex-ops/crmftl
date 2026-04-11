
# Create your views here.
from django.shortcuts import render ,redirect ,get_object_or_404
from authentications.decorators import allowed_roles
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from .models import Enquiry
from django.db import models
from django.db.models import Q
from django.utils import timezone
from orders.models import Order
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
#@allowed_roles(['sales'])
@login_required
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
        vehicle_description = request.POST.get('vehicle_desc')
        kms = request.POST.get('kms')
        material = request.POST.get("material")
        pieces = request.POST.get("pieces") or None
        tonnage = request.POST.get("tonnage") or None
        dimension_unit = request.POST.get("dimension_unit")
        length = request.POST.get("length") or None
        breadth = request.POST.get("breadth") or None
        height = request.POST.get("height") or None
        expected_rate = request.POST.get("expected_rate") or None
        status="Waiting For Rate Approval"
        # Build routes JSON
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

        # Save Enquiry
        enquiry = Enquiry.objects.create(
            customer_name=customer_name,
            customer_contact=customer_contact,
            email=email,
            lead_source=lead_source,
            reference_name=reference_name,
            pickups=pickups,
            deliveries=deliveries,
            vehicle_type=vehicle_type,
            vehicle_description = vehicle_description,
            kms = kms ,
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
        messages.success(request, f"Enquiry #{enquiry.id} created successfully!")
        return redirect('create_enquiry')
    return render(request, 'enquiry/create.html')

# Only sales or admin users can access
def is_sales(user):
    return user.is_authenticated and (user.role in ['sales', 'admin'])

def is_fleet(user):
    return user.is_authenticated and (user.role in ['fleet','admin'])

@login_required
@user_passes_test(is_sales)
def enquiry_list(request):
    # Base queryset depending on user role
    if request.user.role == 'sales':
        base_qs = Enquiry.objects.order_by('-created_at')
    else:
        base_qs = Enquiry.objects.filter(created_by=request.user)

    # Search filter
    query = request.GET.get('q')
    if query:
        base_qs = base_qs.filter(
            Q(customer_name__icontains=query) |
            Q(customer_contact__icontains=query)
        )

    # Counts for dashboard
    total_count = base_qs.count()
    confirmed_count = base_qs.filter(status='confirmed').count()
    pending_count = base_qs.filter(status__icontains='pending').count()
    cancelled_count = base_qs.filter(status='cancelled').count()
    enquiries = base_qs.filter(
        created_by=request.user,
        status='Waiting For Rate Approval'
    ).order_by('-id')
    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'query': query or '',
        'total_count': total_count,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
    })

@login_required
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

@login_required
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
@login_required
@user_passes_test(is_sales)
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

@login_required
@user_passes_test(is_sales)
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
def update_pitch(request, enquiry_id, status):
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

def update_enquiry_status(request, id, action):
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
                "message": "Enquiry confirmed successfully",
                "status": enquiry.status,
                "approval_rate": enquiry.approval_rate,   # ✅ ADD THIS
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
            "message": "Updated successfully",
            "status": enquiry.status
        })

    return JsonResponse({"success": False})