
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
#@allowed_roles(['sales'])
@login_required
def create_enquiry(request):
    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        customer_contact = request.POST.get("customer_contact")
        email = request.POST.get("email")
        lead_source = request.POST.get("lead_source")
        reference_name = request.POST.get("reference_name")
        pickups = int(request.POST.get("pickup_count") or 1)
        deliveries = int(request.POST.get("delivery_count") or 1)
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
def enquiry_list1(request):
    if request.user.role == 'admin':
        enquiries = Enquiry.objects.exclude(status='confirmed')
    else:
        enquiries = Enquiry.objects.filter(
            created_by=request.user
        ).exclude(status='confirmed')
    query = request.GET.get('q')
    if query:
        enquiries = enquiries.filter(
            Q(customer_name__icontains=query) |
            Q(customer_contact__icontains=query)
        )
    enquiries = enquiries.order_by('-id')
    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'query': query or ''
    })

from django.db.models import Q

def enquiry_list1(request):
    # Get enquiries based on user role
    if request.user.role == 'admin':
        enquiries = Enquiry.objects.exclude(status='confirmed')
    else:
        enquiries = Enquiry.objects.filter(
            created_by=request.user
        ).exclude(status='confirmed')

    # Search filter
    query = request.GET.get('q')
    if query:
        enquiries = enquiries.filter(
            Q(customer_name__icontains=query) |
            Q(customer_contact__icontains=query)
        )

    # Order by newest first
    enquiries = enquiries.order_by('-id')

    # Include is_converted_to_order field for each enquiry
    # (This assumes is_converted_to_order is a BooleanField in Enquiry model)
    # If you want to filter only non-converted enquiries, you could do:
    # enquiries = enquiries.filter(is_converted_to_order=False)

    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'query': query or ''
    })

def enquiry_list(request):
    enquiries = Enquiry.objects.filter(
        is_converted_to_order=False 
    ).order_by('-id')
    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries
    })

def enquiry_list2(request):
    # Get enquiries based on user role
    if request.user.role == 'admin':
        enquiries = Enquiry.objects.exclude(status='confirmed')
    else:
        enquiries = Enquiry.objects.filter(
            created_by=request.user
        ).exclude(status='confirmed')

    # Search filter
    query = request.GET.get('q')
    if query:
        enquiries = enquiries.filter(
            Q(customer_name__icontains=query) |
            Q(customer_contact__icontains=query)
        )

    # Order by newest first
    enquiries = enquiries.order_by('-id')

    # Include is_converted_to_order field for each enquiry
    # (This assumes is_converted_to_order is a BooleanField in Enquiry model)
    # If you want to filter only non-converted enquiries, you could do:
    # enquiries = enquiries.filter(is_converted_to_order=False)

    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'query': query or ''
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
def update_pitch(request, enquiry_id, status):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    allowed_status = [
        'Waiting For Rate Approval',
        'pending_pitch1',
        'pending_pitch2',
        'pending_pitch3',
        'confirmed',
        'rejected'
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
def reject_pitch(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)

    # Define the rejection flow
    rejection_flow = {
        "pending_pitch1": "pending_pitch2",
        "pending_pitch2": "pending_pitch3",
        "pending_pitch3": "rejected"  # final stage
    }

    # Update status if it exists in the flow
    if enquiry.status in rejection_flow:
        enquiry.status = rejection_flow[enquiry.status]
        enquiry.save()
        messages.success(request, f"Enquiry status updated to '{enquiry.status}'")
    else:
        messages.warning(request, "Enquiry status cannot be rejected further")

    return redirect('enquiry_list')

def approve_enquiry_logic(enquiry, user):
    if enquiry.status == 'pending_pitch1' and enquiry.pitch1:
        enquiry.approved_rate = enquiry.pitch1

    elif enquiry.status == 'pending_pitch2' and enquiry.pitch2:
        enquiry.approved_rate = enquiry.pitch2

    elif enquiry.status == 'pending_pitch3' and enquiry.pitch3:
        enquiry.approved_rate = enquiry.pitch3
        enquiry.status = "confirmed"  # only final stage confirms

    enquiry.approved_by = user
    enquiry.save()

@login_required
@user_passes_test(is_sales)
def edit_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    if request.method == "POST":
        enquiry.pitch1 = request.POST.get("pitch1") or None
        enquiry.pitch2 = request.POST.get("pitch2") or None
        enquiry.pitch3 = request.POST.get("pitch3") or None
        enquiry.remarks = request.POST.get("remarks")
        if enquiry.pitch3:
            enquiry.status = "pending_pitch3"
        elif enquiry.pitch2:
            enquiry.status = "pending_pitch2"
        elif enquiry.pitch1:
            enquiry.status = "pending_pitch1"
        else:
            enquiry.status = "Waiting For Rate Approval"
        enquiry.save()
        # ✅ Apply approval logic
        approve_enquiry_logic(enquiry, request.user)
        messages.success(request, "Enquiry updated successfully")
        return redirect('enquiry_list')
    return render(request, 'enquiry/edit.html', {'e': enquiry})

@login_required
@allowed_roles(['admin','sales'])
def approve_pitch(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    #enquiry.approved_rate = enquiry.pitch3 or enquiry.pitch2 or enquiry.pitch1
    if request.method == "POST":
        enquiry.pitch1 = request.POST.get("pitch1") or None
        enquiry.pitch2 = request.POST.get("pitch2") or None
        enquiry.pitch3 = request.POST.get("pitch3") or None
        enquiry.remarks = request.POST.get("remarks")

        # 🔥 LOGIC: assign approved_rate based on status
        if enquiry.status == "pending_pitch1" and enquiry.pitch1:
            enquiry.approved_rate = enquiry.pitch1
            enquiry.created_by = request.user

        elif enquiry.status == "pending_pitch2" and enquiry.pitch2:
            enquiry.approved_rate = enquiry.pitch2
            enquiry.created_by = request.user


        elif enquiry.status == "pending_pitch3" and enquiry.pitch3:
            enquiry.approved_rate = enquiry.pitch3
            enquiry.created_by = request.user

        enquiry.save()
    return redirect('enquiry_list')

@login_required
@user_passes_test(is_sales)
def confirm_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)

    # Allow only if any pitch exists
    if enquiry.pitch1 or enquiry.pitch2 or enquiry.pitch3:

        enquiry.status = "confirmed"
        enquiry.approved_by = request.user

        # Priority: pitch3 > pitch2 > pitch1
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

@login_required
@user_passes_test(is_sales)
def convert_to_order(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    # Prevent duplicate
    if enquiry.is_converted_to_order:
        messages.warning(request, "Order already created")
        return redirect("edit_enquiry", id=enquiry.id)
    # Only confirmed
    if enquiry.status != "confirmed":
        messages.error(request, "Enquiry not confirmed")
        return redirect("edit_enquiry", id=enquiry.id)
    # CREATE ORDER safely
    try:
        order = Order.objects.create(
            enquiry=enquiry,
            customer_name=enquiry.customer_name,
            customer_contact=enquiry.customer_contact,
            routes=enquiry.routes,
            vehicle_type=enquiry.vehicle_type,
            final_rate=enquiry.approved_rate,
            gst_percent=getattr(enquiry, 'gstbill', 0),
            created_by=request.user
        )
    except Exception as e:
        messages.error(request, f"Order creation failed: {e}")
        return redirect("edit_enquiry", id=enquiry.id)

    # Update enquiry
    enquiry.is_converted_to_order = True
    enquiry.save()

    messages.success(request, f"Order {order.order_no} created")
    return redirect("order_list", id=order.id)
