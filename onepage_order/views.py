from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CustomerForm,
    OrderForm,
    VehiclePaymentForm,
    CustomerPaymentForm,
)

from .models import (
    Customer,
    Order,
    VehiclePayment,
    CustomerPayment,
    TrackingSession,
    LiveLocation,
)

# Telenity services
from live_tracking.services.auth_service import TrackingAuthService
from live_tracking.services.consent_auth_service import ConsentAuthService
from live_tracking.services.consent_service import ConsentService
from live_tracking.services.import_service import ImportService
from live_tracking.services.location_service import LocationService
from live_tracking.services.modify_service import ModifyService
from live_tracking.services.delete_service import DeleteService


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def _safe_message(value: Any) -> str:
    """
    Convert API/service responses into a readable message.
    """

    if isinstance(value, dict):

        if value.get("errorMessage"):
            return str(value["errorMessage"])

        if value.get("message"):
            return str(value["message"])

        if value.get("raw_response"):
            return str(value["raw_response"])

    return str(value)


def _tracking_queryset():
    """
    Common TrackingSession queryset.

    TrackingSession is linked to Order through:
        TrackingSession.order
    """

    return (
        TrackingSession.objects
        .select_related(
            "order",
            "order__customer",
        )
        .prefetch_related(
            Prefetch(
                "locations",
                queryset=LiveLocation.objects.order_by("-received_at"),
            )
        )
    )


# ============================================================
# ORDER LIST
# ============================================================


@login_required
def onepageorder_list(request):

    query = request.GET.get("q", "").strip()

    orders = (
        Order.objects
        .select_related("customer")
        .prefetch_related(
            "vehicle_payments",
            "customer_payments",
        )
        .order_by("-id")
    )

    if query:

        orders = orders.filter(
            Q(trip_number__icontains=query)
            | Q(customer__name__icontains=query)
            | Q(vehicle_number__icontains=query)
            | Q(origin__icontains=query)
            | Q(destination__icontains=query)
        )

    context = {
        "orders": orders,
        "q": query,
    }

    return render(
        request,
        "onepageorders/order_list.html",
        context,
    )


# ============================================================
# CREATE ORDER
# ============================================================
from decimal import Decimal
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect

from .models import Customer, Order


def decimal_value(value, default="0.00"):
    """
    Convert empty/invalid numeric values safely to Decimal.
    """
    if value in (None, ""):
        return Decimal(default)

    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def int_value(value, default=0):
    """
    Convert empty/invalid integer values safely to int.
    """
    if value in (None, ""):
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def date_value(value):
    """
    HTML <input type="date"> sends YYYY-MM-DD.
    """
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@login_required
def onepageorder_create(request):

    if request.method == "POST":

        try:
            with transaction.atomic():

                # =====================================================
                # CUSTOMER
                # =====================================================

                customer_name = request.POST.get("customer_name", "").strip()
                contact_number = request.POST.get(
                    "contact_number", ""
                ).strip()
                email = request.POST.get(
                    "email", ""
                ).strip()
                address = request.POST.get(
                    "address", ""
                ).strip()

                if not customer_name:
                    messages.error(
                        request,
                        "Customer Name is required."
                    )

                    return render(
                        request,
                        "onepage_order/order_create.html"
                    )

                customer = Customer(
                    name=customer_name,
                    contact_number=contact_number,
                    email=email,
                    address=address,
                )

                customer.full_clean()
                customer.save()

                # =====================================================
                # ORDER
                # =====================================================

                order = Order(
                    customer=customer,

                    # -------------------------------------------------
                    # Customer / Sales
                    # -------------------------------------------------
                    lead_generated_through=request.POST.get(
                        "lead_generated_through", ""
                    ),
                    sales_closed_by=request.POST.get(
                        "sales_closed_by", ""
                    ).strip(),

                    # -------------------------------------------------
                    # Shipment
                    # -------------------------------------------------
                    origin=request.POST.get(
                        "origin", ""
                    ).strip(),
                    destination=request.POST.get(
                        "destination", ""
                    ).strip(),
                    material=request.POST.get(
                        "material", ""
                    ).strip(),
                    packing_type=request.POST.get(
                        "packing_type", ""
                    ).strip(),

                    no_of_pieces=int_value(
                        request.POST.get("no_of_pieces")
                    ),

                    weight_tons=decimal_value(
                        request.POST.get("weight_tons"),
                        "0.000"
                    ),

                    # -------------------------------------------------
                    # Vehicle
                    # -------------------------------------------------
                    vehicle_type=request.POST.get(
                        "vehicle_type", ""
                    ).strip(),

                    vehicle_number=request.POST.get(
                        "vehicle_number", ""
                    ).strip(),

                    driver_number=request.POST.get(
                        "driver_number", ""
                    ).strip(),

                    owner_number=request.POST.get(
                        "owner_number", ""
                    ).strip(),

                    vehicle_sourced_by=request.POST.get(
                        "vehicle_sourced_by", "Direct"
                    ),

                    owner_broker_name=request.POST.get(
                        "owner_broker_name", ""
                    ).strip(),

                    # -------------------------------------------------
                    # Commercials
                    # -------------------------------------------------
                    freight_amount=decimal_value(
                        request.POST.get("freight_amount")
                    ),

                    loading_unloading_charges=decimal_value(
                        request.POST.get(
                            "loading_unloading_charges"
                        )
                    ),

                    halting_charges=decimal_value(
                        request.POST.get("halting_charges")
                    ),

                    other_charges=decimal_value(
                        request.POST.get("other_charges")
                    ),

                    selling_amount=decimal_value(
                        request.POST.get("selling_amount")
                    ),

                    manager_approval=request.POST.get(
                        "manager_approval", "Pending"
                    ),

                    approved_by=request.POST.get(
                        "approved_by", ""
                    ).strip(),

                    # -------------------------------------------------
                    # Customer Payment
                    # -------------------------------------------------
                    customer_billing_type=request.POST.get(
                        "customer_billing_type", ""
                    ),

                    customer_payment_type=request.POST.get(
                        "customer_payment_type", ""
                    ),

                    customer_advance_amount=decimal_value(
                        request.POST.get(
                            "customer_advance_amount"
                        )
                    ),

                    customer_balance_amount=decimal_value(
                        request.POST.get(
                            "customer_balance_amount"
                        )
                    ),

                    customer_payment_method=request.POST.get(
                        "customer_payment_method", ""
                    ),

                    promised_due_date=date_value(
                        request.POST.get("promised_due_date")
                    ),

                    # -------------------------------------------------
                    # Contracted Vehicle Payment
                    # -------------------------------------------------
                    vehicle_advance_amount=decimal_value(
                        request.POST.get(
                            "vehicle_advance_amount"
                        )
                    ),

                    vehicle_balance_amount=decimal_value(
                        request.POST.get(
                            "vehicle_balance_amount"
                        )
                    ),

                    vehicle_owner_name=request.POST.get(
                        "vehicle_owner_name", ""
                    ).strip(),

                    pan_card=request.POST.get(
                        "pan_card", ""
                    ).strip(),

                    account_name=request.POST.get(
                        "account_name", ""
                    ).strip(),

                    account_number=request.POST.get(
                        "account_number", ""
                    ).strip(),

                    ifsc_code=request.POST.get(
                        "ifsc_code", ""
                    ).strip(),

                    upi_number=request.POST.get(
                        "upi_number", ""
                    ).strip(),

                    # -------------------------------------------------
                    # Other
                    # -------------------------------------------------
                    send_sms=(
                        request.POST.get("send_sms") == "on"
                    ),

                    create_agreement_tds=(
                        request.POST.get(
                            "create_agreement_tds"
                        ) == "on"
                    ),
                )

                # Validate Django model choices/field values
                order.full_clean()

                # Order.save() calculates total_trip_cost
                # and generates trip_number.
                order.save()

            messages.success(
                request,
                f"Order {order.trip_number} created successfully."
            )

            return redirect(
                "onepageorder_detail",
                pk=order.pk
            )

        except Exception as e:

            print("ORDER SAVE ERROR:", repr(e))

            messages.error(
                request,
                f"Unable to create order: {str(e)}"
            )

            return render(
                request,
                "onepageorders/order_create.html"
            )

    return render(
        request,
        "onepageorders/order_create.html"
    )
# ============================================================
# ORDER DETAIL
# ============================================================


@login_required
def onepageorder_detail(request, pk):

    order = get_object_or_404(
        Order.objects
        .select_related("customer")
        .prefetch_related(
            "vehicle_payments",
            "customer_payments",
        ),
        pk=pk,
    )

    tracking_session = (
        TrackingSession.objects
        .filter(order=order)
        .first()
    )

    context = {
        "order": order,
        "tracking_session": tracking_session,
    }

    return render(
        request,
        "onepageorders/order_detail.html",
        context,
    )


# ============================================================
# EDIT ORDER
# ============================================================


from decimal import Decimal
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect

from .models import Customer, Order


def edit_decimal(value, default="0.00"):
    if value in (None, ""):
        return Decimal(default)

    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def edit_int(value, default=0):
    if value in (None, ""):
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def edit_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return None


@login_required
def onepageorder_edit(request, pk):

    order = get_object_or_404(
        Order.objects.select_related("customer"),
        pk=pk
    )

    if request.method == "POST":

        try:

            with transaction.atomic():

                # =================================================
                # CUSTOMER
                # =================================================

                customer = order.customer

                customer.name = request.POST.get(
                    "customer_name",
                    ""
                ).strip()

                customer.contact_number = request.POST.get(
                    "contact_number",
                    ""
                ).strip()

                customer.email = request.POST.get(
                    "email",
                    ""
                ).strip()

                customer.address = request.POST.get(
                    "address",
                    ""
                ).strip()

                if not customer.name:
                    messages.error(
                        request,
                        "Customer Name is required."
                    )

                    return render(
                        request,
                        "onepage_order/order_edit.html",
                        {
                            "order": order
                        }
                    )

                customer.full_clean()
                customer.save()


                # =================================================
                # ORDER
                # =================================================

                order.lead_generated_through = request.POST.get(
                    "lead_generated_through",
                    ""
                )

                order.sales_closed_by = request.POST.get(
                    "sales_closed_by",
                    ""
                ).strip()


                # =================================================
                # SHIPMENT
                # =================================================

                order.origin = request.POST.get(
                    "origin",
                    ""
                ).strip()

                order.destination = request.POST.get(
                    "destination",
                    ""
                ).strip()

                order.material = request.POST.get(
                    "material",
                    ""
                ).strip()

                order.packing_type = request.POST.get(
                    "packing_type",
                    ""
                ).strip()

                order.no_of_pieces = edit_int(
                    request.POST.get("no_of_pieces")
                )

                order.weight_tons = edit_decimal(
                    request.POST.get("weight_tons"),
                    "0.000"
                )


                # =================================================
                # VEHICLE
                # =================================================

                order.vehicle_type = request.POST.get(
                    "vehicle_type",
                    ""
                ).strip()

                order.vehicle_number = request.POST.get(
                    "vehicle_number",
                    ""
                ).strip()

                order.driver_number = request.POST.get(
                    "driver_number",
                    ""
                ).strip()

                order.owner_number = request.POST.get(
                    "owner_number",
                    ""
                ).strip()

                order.vehicle_sourced_by = request.POST.get(
                    "vehicle_sourced_by",
                    "Direct"
                )

                order.owner_broker_name = request.POST.get(
                    "owner_broker_name",
                    ""
                ).strip()


                # =================================================
                # COMMERCIALS
                # =================================================

                order.freight_amount = edit_decimal(
                    request.POST.get("freight_amount")
                )

                order.loading_unloading_charges = edit_decimal(
                    request.POST.get(
                        "loading_unloading_charges"
                    )
                )

                order.halting_charges = edit_decimal(
                    request.POST.get("halting_charges")
                )

                order.other_charges = edit_decimal(
                    request.POST.get("other_charges")
                )

                order.selling_amount = edit_decimal(
                    request.POST.get("selling_amount")
                )

                order.manager_approval = request.POST.get(
                    "manager_approval",
                    "Pending"
                )

                order.approved_by = request.POST.get(
                    "approved_by",
                    ""
                ).strip()


                # =================================================
                # CUSTOMER PAYMENT
                # =================================================

                order.customer_billing_type = request.POST.get(
                    "customer_billing_type",
                    ""
                )

                order.customer_payment_type = request.POST.get(
                    "customer_payment_type",
                    ""
                )

                order.customer_advance_amount = edit_decimal(
                    request.POST.get(
                        "customer_advance_amount"
                    )
                )

                order.customer_balance_amount = edit_decimal(
                    request.POST.get(
                        "customer_balance_amount"
                    )
                )

                order.customer_payment_method = request.POST.get(
                    "customer_payment_method",
                    ""
                )

                order.promised_due_date = edit_date(
                    request.POST.get(
                        "promised_due_date"
                    )
                )


                # =================================================
                # CONTRACTED VEHICLE
                # =================================================

                order.vehicle_advance_amount = edit_decimal(
                    request.POST.get(
                        "vehicle_advance_amount"
                    )
                )

                order.vehicle_balance_amount = edit_decimal(
                    request.POST.get(
                        "vehicle_balance_amount"
                    )
                )

                order.vehicle_owner_name = request.POST.get(
                    "vehicle_owner_name",
                    ""
                ).strip()

                order.pan_card = request.POST.get(
                    "pan_card",
                    ""
                ).strip()

                order.account_name = request.POST.get(
                    "account_name",
                    ""
                ).strip()

                order.account_number = request.POST.get(
                    "account_number",
                    ""
                ).strip()

                order.ifsc_code = request.POST.get(
                    "ifsc_code",
                    ""
                ).strip()

                order.upi_number = request.POST.get(
                    "upi_number",
                    ""
                ).strip()


                # =================================================
                # SAVE ORDER
                # =================================================

                order.full_clean()

                # This recalculates total_trip_cost
                order.save()


            messages.success(
                request,
                f"Order {order.trip_number} updated successfully."
            )

            return redirect(
                "onepageorder_detail",
                pk=order.pk
            )


        except Exception as e:

            print(
                "ORDER UPDATE ERROR:",
                repr(e)
            )

            messages.error(
                request,
                f"Unable to update order: {str(e)}"
            )

            return render(
                request,
                "onepage_order/order_edit.html",
                {
                    "order": order
                }
            )


    return render(
        request,
        "onepage_order/order_edit.html",
        {
            "order": order
        }
    )

# ============================================================
# VEHICLE PAYMENTS
# ============================================================

@login_required
def vehicle_payments(request):

    payments = (
        VehiclePayment.objects
        .select_related("order")
        .order_by("-paid_at")
    )

    form = VehiclePaymentForm(
        request.POST or None
    )

    if request.method == "POST":

        if form.is_valid():

            payment = form.save()

            messages.success(
                request,
                (
                    f"Vehicle payment of "
                    f"₹{payment.amount:,.2f} saved successfully."
                ),
            )

            return redirect(
                "vehicle_payments"
            )

        messages.error(
            request,
            "Please correct the payment form.",
        )

    return render(
        request,
        "onepageorders/vehicle_payments.html",
        {
            "payments": payments,
            "form": form,
        },
    )


# ============================================================
# CUSTOMER PAYMENTS
# ============================================================


@login_required
def customer_payments(request):

    payments = (
        CustomerPayment.objects
        .select_related(
            "order",
            "order__customer",
        )
        .order_by("-received_at")
    )

    form = CustomerPaymentForm(
        request.POST or None
    )

    if request.method == "POST":

        if form.is_valid():

            payment = form.save()

            messages.success(
                request,
                (
                    f"Customer payment of "
                    f"₹{payment.received_amount:,.2f} saved successfully."
                ),
            )

            return redirect(
                "customer_payments"
            )

        messages.error(
            request,
            "Please correct the payment form.",
        )

    return render(
        request,
        "onepageorders/customer_payments.html",
        {
            "payments": payments,
            "form": form,
        },
    )


# ============================================================
# ADMIN MARGIN
# ============================================================


@login_required
def admin_margin(request):

    orders = (
        Order.objects
        .select_related("customer")
        .prefetch_related(
            "vehicle_payments",
            "customer_payments",
        )
        .order_by("-id")
    )

    return render(
        request,
        "onepageorders/admin_margin.html",
        {
            "orders": orders,
        },
    )


# ============================================================
# CREATE / GET TRACKING SESSION
# ============================================================


@login_required
def tracking_setup(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related("customer"),
        pk=order_id,
    )

    session = (
        TrackingSession.objects
        .filter(order=order)
        .first()
    )

    return render(
        request,
        "live_tracking/setup.html",
        {
            "order": order,
            "session": session,
        },
    )


# ============================================================
# CREATE TRACKING SESSION FOR ORDER
# ============================================================


@login_required
def create_tracking_session(request, order_id):

    if request.method != "POST":

        return redirect(
            "live_tracking_setup",
            order_id=order_id,
        )

    order = get_object_or_404(
        Order.objects.select_related("customer"),
        pk=order_id,
    )

    # --------------------------------------------------------
    # Already exists
    # --------------------------------------------------------

    existing = (
        TrackingSession.objects
        .filter(order=order)
        .first()
    )

    if existing:

        messages.info(
            request,
            "Tracking session already exists for this order.",
        )

        return redirect(
            "live_tracking_setup",
            order_id=order.id,
        )

    # --------------------------------------------------------
    # Driver mobile
    # --------------------------------------------------------

    driver_mobile = (
        request.POST.get("driver_mobile")
        or order.driver_number
    )

    if not driver_mobile:

        messages.error(
            request,
            "Driver mobile number is required.",
        )

        return redirect(
            "live_tracking_setup",
            order_id=order.id,
        )

    # --------------------------------------------------------
    # Tracking reference
    # --------------------------------------------------------

    tracking_reference = (
        request.POST.get("tracking_reference")
        or order.trip_number
    )

    try:

        with transaction.atomic():

            session = TrackingSession.objects.create(
                order=order,
                tracking_reference=tracking_reference,
                driver_mobile=driver_mobile,
                status="not_enabled",
                tracking_enabled=False,
                consent_received=False,
            )

        messages.success(
            request,
            "Tracking session created successfully.",
        )

    except Exception as exc:

        messages.error(
            request,
            f"Unable to create tracking session: {exc}",
        )

    return redirect(
        "live_tracking_setup",
        order_id=order.id,
    )


# ============================================================
# IMPORT DRIVER TO TELENITY
# ============================================================


@login_required
def import_driver(request, session_id):

    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=session_id,
    )

    result = ImportService.import_driver(session)

    if result.get("success"):

        if result.get("already_exists"):

            messages.info(
                request,
                (
                    "Driver is already registered in "
                    "Telenity. Existing tracking profile will be used."
                ),
            )

        else:

            messages.success(
                request,
                "Driver imported successfully into Telenity.",
            )

        session.status = "imported"
        session.save(
            update_fields=["status"]
        )

    else:

        error_message = _safe_message(
            result.get(
                "message",
                "Driver import failed.",
            )
        )

        messages.error(
            request,
            error_message,
        )

    return redirect(
        "tracking_setup",
        order_id=session.order_id,
    )


# ============================================================
# CHECK CONSENT
# ============================================================


@login_required
def check_consent(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id,
    )

    result = ConsentService.check_consent(
        session
    )

    if not result.get("success"):

        messages.error(
            request,
            _safe_message(
                result.get(
                    "message",
                    "Unable to check consent.",
                )
            ),
        )

        return redirect(
            "vehicle_live",
            session_id=session.id,
        )

    consent_status = result.get(
        "status"
    )

    approved_statuses = {
        "approved",
        "accepted",
        "consent_received",
        "active",
    }

    if consent_status in approved_statuses:

        session.consent_received = True
        session.status = "consent_received"

        session.save(
            update_fields=[
                "consent_received",
                "status",
            ]
        )

        # --------------------------------------------
        # Start tracking
        # --------------------------------------------

        modify_result = (
            ModifyService.start_tracking(
                session
            )
        )

        if modify_result.get("success"):

            session.tracking_enabled = True
            session.status = "waiting_location"

            session.save(
                update_fields=[
                    "tracking_enabled",
                    "status",
                ]
            )

            messages.success(
                request,
                "Consent received. Live tracking activated.",
            )

        else:

            messages.warning(
                request,
                (
                    "Consent received, but tracking could not "
                    "be activated: "
                    + _safe_message(
                        modify_result.get(
                            "message",
                            "Modify API failed.",
                        )
                    )
                ),
            )

    else:

        session.status = (
            "waiting_location"
            if session.tracking_enabled
            else "sms_sent"
        )

        session.save(
            update_fields=["status"]
        )

        messages.warning(
            request,
            f"Consent status: {consent_status}",
        )

    return redirect(
        "vehicle_live",
        session_id=session.id,
    )


# ============================================================
# LIVE TRACKING LIST
# ============================================================


@login_required
def live_tracking_list(request):

    query = request.GET.get(
        "q",
        "",
    ).strip()

    sessions = (
        _tracking_queryset()
        .order_by("-id")
    )

    if query:

        sessions = sessions.filter(
            Q(order__trip_number__icontains=query)
            | Q(order__customer__name__icontains=query)
            | Q(order__vehicle_number__icontains=query)
            | Q(order__driver_number__icontains=query)
            | Q(driver_mobile__icontains=query)
        )

    return render(
        request,
        "live_tracking/list.html",
        {
            "sessions": sessions,
            "query": query,
        },
    )


# ============================================================
# LIVE TRACKING PAGE
# ============================================================


@login_required
def vehicle_live(request, session_id):

    session = get_object_or_404(
        _tracking_queryset(),
        pk=session_id,
    )

    locations = (
        session.locations
        .all()
        .order_by("-received_at")
    )

    latest_location = (
        locations.first()
    )

    return render(
        request,
        "live_tracking/vehicle_live.html",
        {
            "session": session,
            "locations": locations,
            "latest_location": latest_location,
        },
    )


# ============================================================
# REFRESH LOCATION
# ============================================================


@login_required
def refresh_location(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id,
    )

    # --------------------------------------------------------
    # 1. Consent
    # --------------------------------------------------------

    if not session.consent_received:

        messages.warning(
            request,
            "Driver consent has not been approved yet.",
        )

        return redirect(
            "vehicle_live",
            session_id=session.id,
        )

    # --------------------------------------------------------
    # 2. Activate tracking if necessary
    # --------------------------------------------------------

    if not session.tracking_enabled:

        modify_result = (
            ModifyService.start_tracking(
                session
            )
        )

        if not modify_result.get("success"):

            messages.error(
                request,
                (
                    "Unable to start tracking: "
                    + _safe_message(
                        modify_result.get(
                            "message",
                            "Unknown error.",
                        )
                    )
                ),
            )

            return redirect(
                "vehicle_live",
                session_id=session.id,
            )

        session.tracking_enabled = True
        session.status = "active"

        session.save(
            update_fields=[
                "tracking_enabled",
                "status",
            ]
        )

    # --------------------------------------------------------
    # 3. Fetch location
    # --------------------------------------------------------

    result = LocationService.fetch_location(
        session
    )

    if result.get("success"):

        response = result.get(
            "response",
            {},
        )

        terminals = response.get(
            "terminalLocation",
            [],
        )

        if terminals:

            terminal = terminals[0]

            current = terminal.get(
                "currentLocation"
            )

            if current:

                messages.success(
                    request,
                    "Vehicle location updated successfully.",
                )

            else:

                messages.info(
                    request,
                    (
                        "Tracking is enabled, but the "
                        "current location is not available yet."
                    ),
                )

        else:

            messages.warning(
                request,
                "Location information is not available yet.",
            )

    else:

        messages.error(
            request,
            _safe_message(
                result.get(
                    "message",
                    "Unable to retrieve vehicle location.",
                )
            ),
        )

    return redirect(
        "vehicle_live",
        session_id=session.id,
    )


# ============================================================
# TRACKING HISTORY
# ============================================================


@login_required
def tracking_history(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id,
    )

    history = (
        session.locations
        .all()
        .order_by("-received_at")
    )

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "history": history,
        },
    )


# ============================================================
# API TOKEN TEST
# ============================================================


@login_required
def test_tracking_auth(request):

    result = (
        TrackingAuthService
        .get_tracking_token()
    )

    return JsonResponse(
        result,
        safe=False,
    )


@login_required
def test_consent_auth(request):

    result = (
        ConsentAuthService
        .get_consent_token()
    )

    return JsonResponse(
        result,
        safe=False,
    )


@login_required
def api_token_status(request):

    tracking = (
        TrackingAuthService
        .get_tracking_token()
    )

    consent = (
        ConsentAuthService
        .get_consent_token()
    )

    return JsonResponse(
        {
            "tracking": tracking,
            "consent": consent,
        },
        safe=False,
    )


# ============================================================
# TEST LOCATION
# ============================================================


@login_required
def test_location(request, session_id):

    session = get_object_or_404(
        TrackingSession,
        pk=session_id,
    )

    result = LocationService.get_location(
        session.driver_mobile
    )

    return JsonResponse(
        result,
        safe=False,
    )


# ============================================================
# DELETE TRACKING
# ============================================================


@login_required
def delete_tracking(request, session_id):

    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=session_id,
    )

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "live_tracking_list"
        )

    result = (
        DeleteService
        .delete_tracking(session)
    )

    if result.get("success"):

        session.tracking_enabled = False
        session.status = "deleted"

        session.save(
            update_fields=[
                "tracking_enabled",
                "status",
            ]
        )

        messages.success(
            request,
            (
                f"{session.driver_mobile} "
                "tracking removed successfully."
            ),
        )

    else:

        messages.error(
            request,
            _safe_message(
                result.get(
                    "message",
                    "Unable to delete tracking.",
                )
            ),
        )

    return redirect(
        "live_tracking_list"
    )