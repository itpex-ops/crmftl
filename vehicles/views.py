from django.shortcuts import render, redirect, get_object_or_404
from authentications.decorators import allowed_roles
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
from .forms import VehicleForm
from django.urls import reverse
from .models import Vehicle, Tracking
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from django.utils.dateparse import parse_datetime

from django.shortcuts import render
from vehicles.models import Vehicle, Tracking
from django.db.models import Q

def tracking_view(request):
    query = request.GET.get("q")
    tracking = None
    vehicle = None

    if query:
        tracking = Tracking.objects.select_related("order").filter(
            lr_no__icontains=query
        ).first()

        if not tracking:
            tracking = Tracking.objects.select_related("order").filter(
                order__ftl_no__icontains=query
            ).first()

        if tracking:
            vehicle = tracking.order  # adjust if your FK is different

    return render(request, "tracking.html", {
        "tracking": tracking,
        "vehicle": vehicle
    })
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Tracking, TrackingDocument


@require_POST
def upload_tracking_docs(request, id):
    tracking = get_object_or_404(Tracking, id=id)

    # ✅ Safety check: allow upload only after POD received
    if not tracking.pod_received:
        messages.error(request, "Cannot upload documents before POD is received.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    files = request.FILES.getlist("documents")

    # ✅ Validate files
    if not files:
        messages.error(request, "Please select at least one file.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    for f in files:
        # optional file validation
        if hasattr(f, "content_type") and f.content_type not in allowed_types:
            messages.warning(request, f"{f.name} skipped (unsupported format)")
            continue

        TrackingDocument.objects.create(
            tracking=tracking,
            file=f
        )

    messages.success(request, "Documents uploaded successfully.")
    return redirect(request.META.get("HTTP_REFERER", "/"))
def public_tracking(request):
    """
    Search by FTL No or LR No
    Example:
    /tracking/?q=FTL_001
    /tracking/?q=LR12345
    """

    query = request.GET.get("q", "").strip()

    tracking = None
    vehicle = None

    if query:

        # Search by FTL No OR LR No
        vehicle = Vehicle.objects.filter(
            Q(ftl_no__iexact=query) |
            Q(order__tracking__lr_no__iexact=query)
        ).select_related("order").first()

        if vehicle:
            tracking = Tracking.objects.filter(
                order=vehicle.order
            ).first()

    context = {
        "query": query,
        "vehicle": vehicle,
        "tracking": tracking,
    }

    return render(request, "vehicle/public_tracking.html", context)


@login_required
def assign_vehicle(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":

        # SOURCE
        source = request.POST.get("source")
        source_other = request.POST.get("source_other")

        if source == "others" and source_other:
            source = source_other

        # OTP VERIFY CHECK
        driver_verified = request.POST.get("driver_verified")

        if driver_verified != "1":
            messages.error(request, "Driver number not OTP verified.")
            return redirect("assign_vehicle", order_id=order.id)

        Vehicle.objects.create(
            order=order,

            # BASIC
            vehicle_number=request.POST.get("vehicle_number"),
            driver_number=request.POST.get("driver_number"),
            owner_number=request.POST.get("owner_number"),
            source=source,

            # MONEY
            freight_amount=Decimal(request.POST.get("freight_amount") or 0),
            halting=Decimal(request.POST.get("halting") or 0),
            loading_unloading=Decimal(request.POST.get("loading_unloading") or 0),
            brokerage=Decimal(request.POST.get("brokerage") or 0),
            total_freight=Decimal(request.POST.get("total_freight") or 0),
            advance=Decimal(request.POST.get("advance") or 0),
            balance=Decimal(request.POST.get("balance") or 0),
            # PAYMENT
            upi_app=request.POST.get("upi_app"),
            upi_id=request.POST.get("upi_id"),
            upi_number=request.POST.get("upi_number"),

            account_name=request.POST.get("account_name"),
            account_number=request.POST.get("account_number"),
            ifsc=request.POST.get("ifsc"),
            ac_type=request.POST.get("ac_type"),
            beneficiary_name = request.POST.get('beneficiary_name')
        )

        # AUTO CREATE TRACKING
        Tracking.objects.get_or_create(order=order)

        messages.success(request, "Vehicle assigned successfully.")
        return redirect("order_list")

    return render(
        request,
        "vehicle/assign_vehicle.html",
        {
            "order": order
        }
    )
def assigned_vehicles(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    vehicles = order.vehicles.all().order_by('-created_at')  # newest first
    return render(request, 'vehicle/assigned.html', {
        'order': order,
        'vehicles': vehicles,
    })

def assign_vehicle12(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.order = order
            vehicle.save()
            return redirect('order_list')
    else:
        form = VehicleForm()
    return render(request, 'vehicle/assign_vehicle.html', {
        'form': form,
        'order': order,
    })

def edit_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    order = vehicle.order

    if request.method == "POST":

        # Vehicle Details
        vehicle.vehicle_number = request.POST.get("vehicle_number")
        vehicle.driver_number = request.POST.get("driver_number")
        vehicle.owner_number = request.POST.get("owner_number")
        vehicle.source = request.POST.get("source")

        # Amount Details
        vehicle.freight_amount = request.POST.get("freight_amount") or 0
        vehicle.advance = request.POST.get("advance") or 0
        vehicle.brokerage = request.POST.get("brokerage") or 0
        vehicle.loading_unloading = request.POST.get("loading_unloading") or 0

        # Payment Details
        vehicle.upi_number = request.POST.get("upi_number")
        vehicle.upi_app = request.POST.get("upi_app")
        vehicle.account_name = request.POST.get("account_name")
        vehicle.account_number = request.POST.get("account_number")
        vehicle.ifsc = request.POST.get("ifsc")
        vehicle.ac_type = request.POST.get("ac_type")

       
        # Reassign Date Update in Order
        vehicle_date = request.POST.get("vehicle_reassign_date")

        if vehicle_date:
            vehicle_date.vehicle_reassign_date = parse_datetime(vehicle_date)
        else:
            vehicle_date.vehicle_reassign_date = None

         # Save Vehicle
        vehicle.save()


        messages.success(request, "Vehicle updated successfully.")
        return redirect('all_assigned_vehicles')

    return render(request, 'vehicle/edit_vehicle.html', {
        'vehicle': vehicle
    })

# All vehicles
def all_assigned_vehicles(request):
    vehicles = Vehicle.objects.select_related('order').order_by('-created_at')
    for vehicle in vehicles:
        print("placed number",vehicle.order.vehicle_place_date)
    return render(request, 'vehicle/assigned.html', {
        'vehicles': vehicles
    })

def delete_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    order_id = vehicle.order.id
    vehicle.delete()
    return redirect(reverse('assigned_vehicles', args=[order_id]))

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

@login_required
def tracking_page(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    tracking, created = Tracking.objects.get_or_create(order=vehicle.order)

    if request.method == "POST":

        # 🚫 BLOCK EDIT IF SETTLED
        if tracking.settled:
            messages.warning(request, "Tracking already settled. Editing is locked.")
            return redirect("all_assigned_vehicles")

        # -----------------------
        # CHECKBOX VALUES
        # -----------------------
        tracking.vehicle_placed    = 'vehicle_placed' in request.POST
        tracking.vehicle_document  = 'vehicle_document' in request.POST
        tracking.invoice_eway     = 'invoice_eway' in request.POST
        tracking.advance_to_fleet = 'advance_to_fleet' in request.POST
        tracking.fleet_departed   = 'fleet_departed' in request.POST
        tracking.advance_received = 'advance_received' in request.POST
        tracking.arrived          = 'arrived' in request.POST
        tracking.delivered        = 'delivered' in request.POST
        tracking.pod_received     = 'pod_received' in request.POST

        # 🔥 FIXED KEY (was wrong earlier: lrno_received)
        tracking.lr_no_b         = 'lr_no_b' in request.POST

        tracking.lr_no = request.POST.get('lr_no', '').strip()

        # SETTLED
        tracking.settled = 'settled' in request.POST

        now = timezone.now()

        # -----------------------
        # TIMELINE AUTO STAMPS
        # -----------------------
        if tracking.vehicle_placed and not tracking.vehicle_placed_at:
            tracking.vehicle_placed_at = now

        if tracking.fleet_departed and not tracking.fleet_departed_at:
            tracking.fleet_departed_at = now

        if tracking.arrived and not tracking.arrived_at:
            tracking.arrived_at = now

        if tracking.delivered and not tracking.delivered_at:
            tracking.delivered_at = now

        # -----------------------
        # REMARKS
        # -----------------------
        tracking.remarks = request.POST.get("remarks", "").strip()

        tracking.save()

        messages.success(request, "Tracking updated successfully.")
        return redirect("all_assigned_vehicles")

    return render(request, "vehicle/tracking_page.html", {
        "vehicle": vehicle,
        "tracking": tracking
    })


@csrf_exempt
def update_tracking_ajax(request):

    if request.method == "POST":

        data = json.loads(request.body)

        order_id = data.get("order_id")
        field    = data.get("field")
        value    = data.get("value")

        tracking = Tracking.objects.get(order_id=order_id)

        setattr(tracking, field, value)

        now = timezone.now()

        if field == "vehicle_placed" and value and not tracking.vehicle_placed_at:
            tracking.vehicle_placed_at = now

        if field == "fleet_departed" and value and not tracking.fleet_departed_at:
            tracking.fleet_departed_at = now

        if field == "arrived" and value and not tracking.arrived_at:
            tracking.arrived_at = now

        if field == "delivered" and value and not tracking.delivered_at:
            tracking.delivered_at = now

        tracking.save()

        # live status
        if tracking.settled:
            status = "Settled"
            badge_class = "bg-dark"

        elif tracking.delivered:
            status = "Delivered"
            badge_class = "bg-success"

        elif tracking.fleet_departed:
            status = "In Transit"
            badge_class = "bg-info"

        elif tracking.invoice_eway:
            status = "Invoice / Eway"
            badge_class = "bg-warning text-dark"

        else:
            status = "Pending"
            badge_class = "bg-secondary"

        return JsonResponse({
            "success": True,
            "status": status,
            "badge_class": badge_class
        })

    return JsonResponse({"success": False})

@csrf_exempt
def update_vehicle_inline(request):
    if request.method == "POST":
        data = json.loads(request.body)
        vid = data.get("vehicle_id")
        field = data.get("field")
        value = data.get("value")

        vehicle = Vehicle.objects.get(id=vid)
        setattr(vehicle, field, float(value))
        vehicle.save()

        # Prepare balance badge
        if vehicle.balance == 0:
            balance_html = f'<span class="badge bg-success">₹ {vehicle.balance}</span>'
        elif vehicle.balance < vehicle.total_freight:
            balance_html = f'<span class="badge bg-warning text-dark">₹ {vehicle.balance}</span>'
        else:
            balance_html = f'<span class="badge bg-danger">₹ {vehicle.balance}</span>'

        return JsonResponse({"success": True, "balance_html": balance_html, "total_freight": vehicle.total_freight})
    return JsonResponse({"success": False})

