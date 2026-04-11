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
@login_required
def assign_vehicle12(request, id):
    order = get_object_or_404(Order, id=id)
    if request.method == "POST":
        freight = float(request.POST.get("freight_amount") or 0)
        advance = float(request.POST.get("advance") or 0)
        Vehicle.objects.create(
            order=order,
            vehicle_number=request.POST.get("vehicle_number"),
            driver_number=request.POST.get("driver_number"),
            owner_number=request.POST.get("owner_number"),
            source=request.POST.get("source"),
            freight_amount=freight,
            advance=advance,
            balance=freight - advance,  # 🔥 auto calc
            brokerage=request.POST.get("brokerage") or 0,
            loading=request.POST.get("loading") or 0,
            total_freight=request.POST.get("total_freight") or 0,
            upi_number=request.POST.get("upi_number"),
            account_name=request.POST.get("account_name"),
            account_number=request.POST.get("account_number"),
            ifsc=request.POST.get("ifsc"),
        )
        Tracking.objects.get_or_create(order=order)
        return redirect('order_list')
    return render(request, 'orders/assign_vehicle.html', {'order': order})

def assigned_vehicles(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    vehicles = order.vehicles.all().order_by('-created_at')  # newest first
    return render(request, 'vehicle/assigned.html', {
        'order': order,
        'vehicles': vehicles,
    })

def assign_vehicle(request, order_id):
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
    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            return redirect(reverse('assigned_vehicles', args=[vehicle.order.id]))
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'vehicle/edit_vehicle.html', {
        'form': form,
        'vehicle': vehicle,
    })

# All vehicles
def all_assigned_vehicles(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'vehicle/assigned.html', {'vehicles': vehicles})

def delete_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    order_id = vehicle.order.id
    vehicle.delete()
    return redirect(reverse('assigned_vehicles', args=[order_id]))

def tracking_page(request, vehicle_id):
    """
    Display and update tracking for a specific vehicle.
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    # Get or create tracking for this order
    tracking, created = Tracking.objects.get_or_create(order=vehicle.order)
    if request.method == "POST":
        # Update tracking fields from checkboxes
        tracking.vehicle_placed = bool(request.POST.get("vehicle_placed"))
        tracking.vehicle_document = bool(request.POST.get("vehicle_document"))
        tracking.invoice_eway = bool(request.POST.get("invoice_eway"))
        tracking.advance_to_fleet = bool(request.POST.get("advance_to_fleet"))
        tracking.fleet_departed = bool(request.POST.get("fleet_departed"))
        tracking.advance_received = bool(request.POST.get("advance_received"))
        tracking.arrived = bool(request.POST.get("arrived"))
        tracking.delivered = bool(request.POST.get("delivered"))
        tracking.pod_received = bool(request.POST.get("pod_received"))
        tracking.settled = bool(request.POST.get("settled"))

        # Update timestamps automatically for key steps
        now = timezone.now()
        if tracking.vehicle_placed and not tracking.vehicle_placed_at:
            tracking.vehicle_placed_at = now
        if tracking.fleet_departed and not tracking.fleet_departed_at:
            tracking.fleet_departed_at = now
        if tracking.arrived and not tracking.arrived_at:
            tracking.arrived_at = now
        if tracking.delivered and not tracking.delivered_at:
            tracking.delivered_at = now
        # Remarks
        tracking.remarks = request.POST.get("remarks", "").strip()

        tracking.save()
        messages.success(request, "Tracking updated successfully!")
        return redirect("all_assigned_vehicles")
    context = {
        "vehicle": vehicle,
        "tracking": tracking,
    }
    return render(request, "vehicle/tracking_page.html", context)

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

@csrf_exempt
def update_tracking_ajax(request):
    if request.method == "POST":
        data = json.loads(request.body)
        order_id = data.get("order_id")
        field = data.get("field")
        value = data.get("value")

        tracking = Tracking.objects.get(order_id=order_id)
        setattr(tracking, field, value)
        tracking.save()

        # Determine badge status
        if tracking.delivered:
            status = "Delivered"
            badge_class = "bg-success"
        elif tracking.fleet_departed:
            status = "In Transit"
            badge_class = "bg-info"
        else:
            status = "Pending"
            badge_class = "bg-secondary"

        return JsonResponse({"success": True, "status": status, "badge_class": badge_class})
    return JsonResponse({"success": False})
