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
from django.db.models import Count
from datetime import datetime
# def is_fleet(user):
#     return user.is_authenticated and (user.role in ['fleet','admin'])

# def is_sales(user):
#      return user.is_authenticated and (user.role in ['sales','admin'])

from datetime import datetime

from datetime import datetime
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

# views.py

from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from enquiries.models import Enquiry
from .models import Order

# orders/views.py

from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import Order
from vehicles.models import Tracking
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from enquiries.models import Enquiry
from .models import Order


# =====================================================
# HELPERS
# =====================================================

def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_datetime(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")
    except:
        return None


def parse_date(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except:
        return None


# =====================================================
# COMMON SAVE FUNCTION
# =====================================================

def save_order_data(order, request):

    # =================================================
    # DATES
    # =================================================

    order.vehicle_place_date = parse_datetime(
        request.POST.get("vehicle_place_date", "")
    )

    order.credit_date = parse_date(
        request.POST.get("credit_date", "")
    )

    order.due_date = parse_date(
        request.POST.get("due_date", "")
    )

    # =================================================
    # PRICING
    # =================================================

    order.finalized_rate = to_float(
        request.POST.get("finalized_rate")
    )

    order.loading_charges = to_float(
        request.POST.get("loading_charges")
    )

    order.halting_charges = to_float(
        request.POST.get("halting_charges")
    )

    order.gst_percent = to_float(
        request.POST.get("gst_percent")
    )

    order.total_rate = to_float(
        request.POST.get("total_rate")
    )

    # =================================================
    # PAYMENT
    # =================================================

    order.payment_terms = request.POST.get(
        "payment_terms", ""
    )

    order.advance = to_float(
        request.POST.get("advance")
    )

    order.balance = to_float(
        request.POST.get("balance")
    )

    order.topay = to_float(
        request.POST.get("topay")
    )

    order.credit = to_float(
        request.POST.get("credit")
    )

    order.credit_days = int(
        request.POST.get("credit_days") or 0
    )

    # =================================================
    # SAVE
    # =================================================

    order.save()

    return order


# =====================================================
# CREATE / UPDATE ORDER
# =====================================================

@login_required
def pricing_page(request, enquiry_id):

    enquiry = get_object_or_404(
        Enquiry,
        id=enquiry_id
    )

    order = Order.objects.filter(
        enquiry=enquiry
    ).first()

    approval_rate = enquiry.approval_rate or 0

    # =================================================
    # SAVE
    # =================================================

    if request.method == "POST":

        # =============================================
        # CREATE ORDER FIRST TIME
        # =============================================

        if not order:

            order = Order(
                enquiry=enquiry,
                customer_name=enquiry.customer_name,
                customer_contact=enquiry.customer_contact,
                routes=enquiry.routes,
                vehicle_type=enquiry.vehicle_type,
                created_by=request.user
            )

        # =============================================
        # SAVE COMMON DATA
        # =============================================

        save_order_data(order, request)

        # =============================================
        # MARK ENQUIRY CONVERTED
        # =============================================

        enquiry.is_converted_to_order = True
        enquiry.save()

        messages.success(
            request,
            f"Order {order.order_no} saved successfully!"
        )

        return redirect("enquiry_list")

    # =================================================
    # PAGE LOAD
    # =================================================

    context = {
        "order": order,
        "enquiry": enquiry,
        "approval_rate": approval_rate,
    }

    return render(
        request,
        "orders/order_detail.html",
        context
    )


# =====================================================
# ORDER DETAIL / UPDATE
# =====================================================

@login_required
def order_detail(request, id):

    order = get_object_or_404(
        Order,
        id=id
    )

    enquiry = getattr(order, "enquiry", None)

    approval_rate = (
        enquiry.approval_rate
        if enquiry and enquiry.approval_rate
        else 0
    )

    # =================================================
    # UPDATE
    # =================================================

    if request.method == "POST":

        save_order_data(order, request)

        messages.success(
            request,
            "Order updated successfully!"
        )

        return redirect(
            "order_detail",
            id=order.id
        )

    # =================================================
    # PAGE LOAD
    # =================================================

    context = {
        "order": order,
        "enquiry": enquiry,
        "approval_rate": approval_rate,
    }

    return render(
        request,
        "orders/order_detail.html",
        context
    )
#@user_passes_test(is_sales)
@login_required
def convert_to_order1(request, enquiry_id):

    enquiry = get_object_or_404(Enquiry, id=enquiry_id)

    if enquiry.is_converted_to_order:
        messages.warning(request, "Order already created.")
        return redirect('/')

    if request.method == "POST":

        order = Order.objects.create(
            enquiry=enquiry,
            customer_name=enquiry.customer_name,
            customer_contact=enquiry.customer_contact,
            routes=enquiry.routes,
            vehicle_type=enquiry.vehicle_type,

            finalized_rate=request.POST.get('finalized_rate') or enquiry.approval_rate or 0,
            loading_charges=request.POST.get('loading_charges') or 0,
            halting_charges=request.POST.get('halting_charges') or 0,
            gst_percent=request.POST.get('gst_percent') or 0,
            advance=request.POST.get('advance') or 0,
            payment_terms=request.POST.get('payment_terms'),

            created_by=request.user
        )

        enquiry.is_converted_to_order = True
        enquiry.save()

        messages.success(
            request,
            f"Order {order.order_no} created successfully!"
        )

        return redirect('order_detail', id=order.id)

@login_required
def order_list(request):

    orders = Order.objects.select_related('tracking').order_by('-id')

    for o in orders:
        try:
            o.vehicle_obj = o.vehicles
        except:
            o.vehicle_obj = None

    total_orders = orders.count()

    assigned_count = orders.filter(
        vehicles__isnull=False
    ).count()

    not_assigned_count = orders.filter(
        vehicles__isnull=True
    ).count()

    pending_count = orders.filter(
        tracking__isnull=True
    ).count()

    delivered_count = orders.filter(
        tracking__delivered=True
    ).count()

    transit_count = orders.filter(
        tracking__fleet_departed=True,
        tracking__delivered=False
    ).count()

    total_revenue = sum(
        float(order.total_rate or 0)
        for order in orders
    )

    return render(request, "orders/orders.html", {
        "orders": orders,
        "total_orders": total_orders,
        "assigned_count": assigned_count,
        "not_assigned_count": not_assigned_count,
        "pending_count": pending_count,
        "delivered_count": delivered_count,
        "transit_count": transit_count,
        "total_revenue": int(total_revenue),
    })


@login_required
def assign_vehicle(request, order_id):
    order = get_object_or_404(Order, id=order_id)

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
            balance=freight - advance,
            brokerage=request.POST.get("brokerage"),
            loading=request.POST.get("loading"),
            total_freight=request.POST.get("total_freight"),
            upi_number=request.POST.get("upi_number"),
            account_name=request.POST.get("account_name"),
            account_number=request.POST.get("account_number"),
            ifsc=request.POST.get("ifsc"),
            ac_type=request.POST.get('ac_type'),
            upi_app=request.POST.get("upi_app"),
        )

        tracking, created = Tracking.objects.get_or_create(order=order)

        tracking.vehicle_placed = True
        tracking.vehicle_document = True
        tracking.save()

        return redirect('order_listr', order_id=order.id)

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

# views.py

@login_required
def view_order(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related(
            'enquiry',
            'created_by',
            'tracking'
        ).prefetch_related(
            'vehicles'
        ),
        id=order_id
    )

    return render(request, 'orders/view_order.html', {
        'order': order
    })

@login_required
def create_order_from_enquiry(request, enquiry_id):
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    if hasattr(enquiry, 'order'):
        return redirect('order_detail', id=enquiry.order.id)
    order = Order.objects.create(
        enquiry=enquiry,
        customer_name=enquiry.customer_name,
        customer_contact=enquiry.customer_contact,
        routes=enquiry.routes,
        vehicle_type=enquiry.vehicle_type,
        created_by=request.user)
    enquiry.is_converted_to_order = True
    enquiry.save()
    return redirect('order_detail', id=order.id)