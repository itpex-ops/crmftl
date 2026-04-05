from django.shortcuts import render, redirect
#from .forms import OrderForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required ,user_passes_test
import uuid
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from enquiries.models import Enquiry
from .models import Order
from vehicles.models import Vehicle , Tracking
from authentications.decorators import allowed_roles

# def is_fleet(user):
#     return user.is_authenticated and (user.role in ['fleet','admin'])

def is_sales(user):
     return user.is_authenticated and (user.role in ['sales','admin'])

@user_passes_test(is_sales)
@login_required
def convert_to_order(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    if enquiry.is_converted_to_order:
        messages.warning(request, "Order already created for this enquiry.")
        return redirect('edit_enquiry', id=enquiry.id)
    order = Order.objects.create(
        enquiry=enquiry,
        customer_name=enquiry.customer_name,
        customer_contact=enquiry.customer_contact,
        routes=enquiry.routes,
        vehicle_type=enquiry.vehicle_type,
        created_by=request.user)
    enquiry.is_converted_to_order = True
    enquiry.save()

    messages.success(request, f"Order {order.order_no} created successfully!")
    return redirect('order_detail', id=order.id)

@login_required
def order_list(request):
    orders = Order.objects.order_by('-id')
    for i in orders:

        print(i)
    return render(request, 'orders/order_list.html', {
        'orders': orders
    })

@login_required
def order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    return render(request, 'orders/order_detail.html', {
        'order': order
    })

def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
@login_required 
def assign_vehicle(request, id):
    order = get_object_or_404(Order, id=id)

    if request.method == "POST":
        freight = float(request.POST.get("freight_amount") or 0)
        advance = float(request.POST.get("advance") or 0)
        brokerage = float(request.POST.get("brokerage") or 0)
        loading = float(request.POST.get("loading") or 0)
        total_freight = float(request.POST.get("total_freight") or 0)

        Vehicle.objects.create(
            order=order,
            vehicle_number=request.POST.get("vehicle_number"),
            driver_number=request.POST.get("driver_number"),
            owner_number=request.POST.get("owner_number"),
            source=request.POST.get("source"),
            freight_amount=freight,
            advance=advance,
            balance=freight - advance,  # ✅ correct
            brokerage=brokerage,
            loading=loading,
            total_freight=total_freight,
            upi_number=request.POST.get("upi_number"),
            account_name=request.POST.get("account_name"),
            account_number=request.POST.get("account_number"),
            ifsc=request.POST.get("ifsc"),
            ac_type=request.POST.get('ac_type'),
            upi_app=request.POST.get("upi_app"),
        )

        # ✅ CREATE TRACKING (if not exists)
        Tracking.objects.get_or_create(order=order)
        tracking, created = Tracking.objects.get_or_create(order=order)

        # 🔥 UPDATE STATUS
        tracking.vehicle_placed = True
        tracking.vehicle_document = True
        tracking.save()
        return redirect('order_detail', id=order.id)

    return render(request, 'orders/assign_vehicle.html', {'order': order})

@login_required
def tracking_update(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    tracking, created = Tracking.objects.get_or_create(order=order)
    if request.method == "POST":                                                                                                                                                
        tracking.vehicle_placed = 'vehicle_placed' in request.POST
        tracking.vehicle_document = 'vehicle_document' in request.POST
        tracking.invoice_eway = 'invoice_eway' in request.POST
        tracking.advance_to_fleet = 'advance_to_fleet' in request.POST
        tracking.fleet_departed = 'fleet_departed' in request.POST
        tracking.advance_received = 'advance_received' in request.POST
        tracking.arrived = 'arrived' in request.POST
        tracking.delivered = 'delivered' in request.POST
        tracking.pod_received = 'pod_received' in request.POST
        tracking.transporter_paid = 'transporter_paid' in request.POST
        tracking.customer_paid = 'customer_paid' in request.POST
        tracking.settled = 'settled' in request.POST
        tracking.remarks = request.POST.get("remarks")
        tracking.save()
        return redirect('order_list')
    return render(request, 'orders/tracking.html', {
        'order': order,
        'tracking': tracking
    })

@property
def profit(self):
    vehicle_cost = sum(v.total_freight for v in self.vehicles.all())
    return (self.total_rate or 0) - vehicle_cost
