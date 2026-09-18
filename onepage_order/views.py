from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import (
    Customer,
    Order,
    Tracking,
    TrackingDocument,
    VehiclePayment,
    CustomerPayment,
    TrackingSession,
    LiveLocation,
    SMSLog,
    ApiLog,
    ApiToken,)
from .services.auth_service import TrackingAuthService
from  .services.consent_auth_service import ConsentAuthService
from .services.import_service import ImportService
from .services.consent_service import ConsentService
from .services.location_service import LocationService
from .services.delete_service import DeleteService
from .services.modify_service import ModifyService
logger = logging.getLogger(__name__)

# =============================================================
# COMMON HELPERS
# =============================================================

def get_post_value(request, field, default=""):
    """Return a cleaned POST string."""
    value = request.POST.get(field, default)
    return value.strip() if isinstance(value, str) else default


def to_decimal(value, default="0.00"):
    """Safely convert POST input to Decimal."""
    if value in (None, ""):
        return Decimal(default)

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def to_integer(value, default=0):
    """Safely convert POST input to integer."""
    if value in (None, ""):
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def to_date(value):
    """Convert HTML date input (YYYY-MM-DD) to a Python date."""
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None

def gst_from_request(request):
    """
    Read and validate the GST checkbox value.

    Supported values:
    0, 7, 8, 10, 13
    """
    raw_value = request.POST.get("gst_percent", "0")
    gst_percent = to_decimal(raw_value, "0.00")

    valid_rates = {
        Decimal("0.00"),
        Decimal("7.00"),
        Decimal("8.00"),
        Decimal("10.00"),
        Decimal("13.00"),
    }

    if gst_percent not in valid_rates:
        raise ValidationError("Invalid GST percentage selected.")

    return gst_percent


def order_queryset():
    """Common optimized Order queryset."""
    return (
        Order.objects
        .select_related(
            "customer",
            "tracking",
            "tracking_session",
        )
        .prefetch_related(
            "vehicle_payments",
            "customer_payments",
        )
        .order_by("-id")
    )


def payment_page_context(orders, payments):
    return {
        "orders": orders,
        "payments": payments,
    }


def add_tracking_template_flags(tracking):
    """
    Backward-compatible template aliases.

    Tracking model stores:
    - live tracking as live_tracking_at
    - balance transfer as balance_to_fleet

    Older tracking_page templates may still use:
    - tracking.live_tracking
    - tracking.balance_trans_fleet
    """
    tracking.live_tracking = bool(
        tracking.live_tracking_at
    )
    tracking.balance_trans_fleet = bool(
        tracking.balance_to_fleet
    )
    return tracking
# =============================================================
# LIVE TRACKING PAGE
# =============================================================
@login_required
def vehicle_live(request, pk):
    """
    Display the live-tracking page using a TrackingSession PK.
    TrackingSession is linked directly to Order.
    """
    tracking_session = get_object_or_404(
        TrackingSession.objects.select_related(
            "order",
            "order__customer",
            "order__tracking",
        ),
        pk=pk,
    )
    order = tracking_session.order
    tracking = getattr(order, "tracking", None)

    latest_location = (
        LiveLocation.objects
        .filter(session=tracking_session)
        .order_by("-received_at")
        .first()
    )

    context = {
        "tracking_session": tracking_session,
        "order": order,
        "tracking": tracking,
        "latest_location": latest_location,
    }

    return render(
        request,
        "onepageorders/tracking.html",
        context,
    )

@login_required
def vehicle_live_location(request, pk):
    """
    Return the latest location using a TrackingSession PK.
    """
    tracking_session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=pk,
    )

    order = tracking_session.order

    latest_location = (
        LiveLocation.objects
        .filter(session=tracking_session)
        .order_by("-received_at")
        .first()
    )

    if not latest_location:
        return JsonResponse({
            "success": True,
            "tracking": True,
            "has_location": False,
            "vehicle_number": order.vehicle_number or "",
            "driver_number": order.driver_number or "",
            "trip_number": order.trip_number or "",
            "tracking_reference": (
                tracking_session.tracking_reference
            ),
            "status": tracking_session.get_status_display(),
            "tracking_enabled": (
                tracking_session.tracking_enabled
            ),
            "consent_received": (
                tracking_session.consent_received
            ),
            "message": "Waiting for vehicle location...",
        })

    latitude = (
        float(latest_location.latitude)
        if latest_location.latitude is not None
        else None
    )

    longitude = (
        float(latest_location.longitude)
        if latest_location.longitude is not None
        else None
    )

    return JsonResponse({
        "success": True,
        "tracking": True,
        "has_location": True,
        "vehicle_number": order.vehicle_number or "",
        "driver_number": order.driver_number or "",
        "trip_number": order.trip_number or "",
        "tracking_reference": (
            tracking_session.tracking_reference
        ),
        "status": tracking_session.get_status_display(),
        "tracking_enabled": (
            tracking_session.tracking_enabled
        ),
        "consent_received": (
            tracking_session.consent_received
        ),
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": latest_location.accuracy,
        "location_name": (
            latest_location.location_name or ""
        ),
        "address": latest_location.address or "",
        "location_status": (
            latest_location.location_status or ""
        ),
        "tracked": latest_location.tracked,
        "received_at": (
            latest_location.received_at.isoformat()
        ),
        "session_last_updated": (
            tracking_session.last_updated.isoformat()
            if tracking_session.last_updated
            else None
        ),
    })

# =============================================================
# ORDER DELETE
# =============================================================

@login_required
def onepageorder_delete(request, pk):
    if request.method != "POST":
        messages.error(
            request,
            "Invalid request.",
        )
        return redirect(
            "onepageorder_list",
            pk=pk,
        )

    order = get_object_or_404(
        Order,
        pk=pk,
    )

    trip_number = order.trip_number

    try:
        with transaction.atomic():
            order.delete()

        messages.success(
            request,
            f"Order {trip_number} deleted successfully.",
        )

    except Exception:
        logger.exception(
            "Unable to delete order %s",
            trip_number,
        )
        messages.error(
            request,
            f"Unable to delete order {trip_number}.",
        )

    return redirect("onepageorder_list")


# Backward-compatible name if an old URL still points to delete_vehicle.
@login_required
def delete_vehicle(request, pk):
    return onepageorder_delete(request, pk)

# =============================================================
# ORDER LIST
# =============================================================

@login_required
def onepageorder_list(request):
    search = request.GET.get("q", "").strip()

    orders = order_queryset()

    if search:
        orders = orders.filter(
            Q(trip_number__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(origin__icontains=search)
            | Q(destination__icontains=search)
            | Q(vehicle_number__icontains=search)
            | Q(vehicle_type__icontains=search)
        )

    return render(
        request,
        "onepageorders/order_list.html",
        {
            "orders": orders,
            "q": search,
        },
    )

# =============================================================
# ORDER CREATE HELPERS
# =============================================================

def create_customer_from_request(request):
    customer_name = get_post_value(
        request,
        "customer_name",
    )

    if not customer_name:
        raise ValidationError(
            "Customer Name is required."
        )

    customer = Customer(
        name=customer_name,
        contact_number=get_post_value(
            request,
            "contact_number",
        ),
        email=get_post_value(
            request,
            "email",
        ),
        address=get_post_value(
            request,
            "address",
        ),
    )

    customer.full_clean()
    customer.save()

    return customer


def build_order_from_request(request, customer):
    """
    Build an Order from POST data.
    The object is returned without saving.
    """

    order = Order(
        customer=customer,

        # Customer / Sales
        lead_generated_through=get_post_value(
            request,
            "lead_generated_through",
        ),
        reference_name=get_post_value(
            request,
            "reference_name",
        ),
        sales_closed_by=get_post_value(
            request,
            "sales_closed_by",
        ),

        # Shipment
        origin=get_post_value(
            request,
            "origin",
        ),
        destination=get_post_value(
            request,
            "destination",
        ),
        material=get_post_value(
            request,
            "material",
        ),
        packing_type=get_post_value(
            request,
            "packing_type",
        ),
        no_of_pieces=to_integer(
            request.POST.get("no_of_pieces"),
        ),
        weight_tons=to_decimal(
            request.POST.get("weight_tons"),
            "0.000",
        ),

        # Vehicle
        vehicle_type=get_post_value(
            request,
            "vehicle_type",
        ),
        vehicle_number=get_post_value(
            request,
            "vehicle_number",
        ),
        driver_number=get_post_value(
            request,
            "driver_number",
        ),
        owner_number=get_post_value(
            request,
            "owner_number",
        ),
        vehicle_sourced_by=request.POST.get(
            "vehicle_sourced_by",
            "Direct",
        ),
        owner_broker_name=get_post_value(
            request,
            "owner_broker_name",
        ),

        # Commercials
        freight_amount=to_decimal(
            request.POST.get("freight_amount"),
        ),
        loading_unloading_charges=to_decimal(
            request.POST.get(
                "loading_unloading_charges"
            ),
        ),
        halting_charges=to_decimal(
            request.POST.get(
                "halting_charges"
            ),
        ),
        other_charges=to_decimal(
            request.POST.get("other_charges"),
        ),
        selling_amount=to_decimal(
            request.POST.get("selling_amount"),
        ),
        gst_percent=gst_from_request(request),

        manager_approval=request.POST.get(
            "manager_approval",
            "Pending",
        ),
        approved_by=get_post_value(
            request,
            "approved_by",
        ),

        # Customer Payment Terms
        customer_billing_type=request.POST.get(
            "customer_billing_type",
            "",
        ),
        customer_payment_type=request.POST.get(
            "customer_payment_type",
            "",
        ),
        customer_advance_amount=to_decimal(
            request.POST.get(
                "customer_advance_amount"
            ),
        ),
        customer_balance_amount=to_decimal(
            request.POST.get(
                "customer_balance_amount"
            ),
        ),
        customer_payment_method=request.POST.get(
            "customer_payment_method",
            "",
        ),
        promised_due_date=to_date(
            request.POST.get(
                "promised_due_date"
            )
        ),

        # Contracted Vehicle Payment Terms
        vehicle_advance_amount=to_decimal(
            request.POST.get(
                "vehicle_advance_amount"
            ),
        ),
        vehicle_balance_amount=to_decimal(
            request.POST.get(
                "vehicle_balance_amount"
            ),
        ),
        vehicle_owner_name=get_post_value(
            request,
            "vehicle_owner_name",
        ),
        pan_card=get_post_value(
            request,
            "pan_card",
        ),
        account_name=get_post_value(
            request,
            "account_name",
        ),
        account_number=get_post_value(
            request,
            "account_number",
        ),
        ifsc_code=get_post_value(
            request,
            "ifsc_code",
        ),
        upi_number=get_post_value(
            request,
            "upi_number",
        ),

        # Options
        send_sms=(
            request.POST.get("send_sms") == "on"
        ),
        create_agreement_tds=(
            request.POST.get(
                "create_agreement_tds"
            ) == "on"
        ),
    )

    return order


def prepare_order_for_validation(order):
    """
    Order.full_clean() runs before Order.save(), so generate
    trip_number first.
    """
    if not order.trip_number:
        order.trip_number = Order.generate_trip_number()

    return order

# =============================================================
# ORDER CREATE
# =============================================================

@login_required
def onepageorder_create(request):
    template_name = "onepageorders/order_create.html"
    if request.method != "POST":
        return render(
            request,
            template_name,
        )
    try:
        with transaction.atomic():

            customer = create_customer_from_request(
                request
            )

            order = build_order_from_request(
                request,
                customer,
            )

            prepare_order_for_validation(
                order
            )

            order.full_clean()
            order.save()

            # Create the workflow record together with the order.
            Tracking.objects.get_or_create(
                order=order
            )

        messages.success(
            request,
            (
                f"Order {order.trip_number} "
                "created successfully."
            ),
        )

        return redirect(
            "onepageorder_detail",
            pk=order.pk,
        )

    except ValidationError as e:
        logger.warning(
            "Order validation failed: %s",
            e,
            exc_info=True,
        )

        if hasattr(e, "message_dict"):
            error_messages = []

            for field, errors in (
                e.message_dict.items()
            ):
                for error in errors:
                    error_messages.append(
                        f"{field}: {error}"
                    )

            messages.error(
                request,
                " | ".join(error_messages),
            )
        else:
            messages.error(
                request,
                str(e),
            )

        return render(
            request,
            template_name,
        )

    except Exception:
        logger.exception(
            "Unexpected error while creating order"
        )

        messages.error(
            request,
            (
                "Unable to create the order. "
                "Please check the entered details "
                "and try again."
            ),
        )

        return render(
            request,
            template_name,
        )

# =============================================================
# ORDER DETAIL
# =============================================================

@login_required
def onepageorder_detail(request, pk):
    order = get_object_or_404(
        Order.objects
        .select_related(
            "customer",
            "tracking",
            "tracking_session",
        )
        .prefetch_related(
            "vehicle_payments",
            "customer_payments",
            "tracking__documents",
        ),
        pk=pk,
    )

    return render(
        request,
        "onepageorders/order_detail.html",
        {
            "order": order,
            "tracking": getattr(
                order,
                "tracking",
                None,
            ),
        },
    )

# =============================================================
# LIVE TRACKING - ORDER LOCATION API
# =============================================================

@login_required
def order_live_location(request, pk):
    order = get_object_or_404(
        Order.objects.select_related(
            "tracking_session",
        ),
        pk=pk,
    )

    tracking_session = getattr(
        order,
        "tracking_session",
        None,
    )

    if not tracking_session:
        return JsonResponse(
            {
                "success": False,
                "tracking": False,
                "message": (
                    "Live tracking is not enabled "
                    "for this order."
                ),
            },
            status=404,
        )

    latest_location = (
        LiveLocation.objects
        .filter(session=tracking_session)
        .order_by("-received_at")
        .first()
    )

    if not latest_location:
        return JsonResponse({
            "success": True,
            "tracking": True,
            "has_location": False,
            "trip_number": order.trip_number or "",
            "vehicle_number": (
                order.vehicle_number or ""
            ),
            "driver_number": (
                order.driver_number or ""
            ),
            "status": (
                tracking_session.get_status_display()
            ),
            "tracking_reference": (
                tracking_session.tracking_reference
            ),
            "driver_mobile": (
                tracking_session.driver_mobile
            ),
            "tracking_enabled": (
                tracking_session.tracking_enabled
            ),
            "consent_received": (
                tracking_session.consent_received
            ),
            "message": (
                "Waiting for vehicle location..."
            ),
        })

    latitude = (
        float(latest_location.latitude)
        if latest_location.latitude is not None
        else None
    )

    longitude = (
        float(latest_location.longitude)
        if latest_location.longitude is not None
        else None
    )

    return JsonResponse({
        "success": True,
        "tracking": True,
        "has_location": True,
        "trip_number": order.trip_number or "",
        "vehicle_number": (
            order.vehicle_number or ""
        ),
        "driver_number": (
            order.driver_number or ""
        ),
        "status": (
            tracking_session.get_status_display()
        ),
        "tracking_enabled": (
            tracking_session.tracking_enabled
        ),
        "consent_received": (
            tracking_session.consent_received
        ),
        "tracking_reference": (
            tracking_session.tracking_reference
        ),
        "driver_mobile": (
            tracking_session.driver_mobile
        ),
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": latest_location.accuracy,
        "location_name": (
            latest_location.location_name or ""
        ),
        "address": (
            latest_location.address or ""
        ),
        "location_status": (
            latest_location.location_status or ""
        ),
        "tracked": latest_location.tracked,
        "received_at": (
            latest_location.received_at.isoformat()
        ),
        "session_last_updated": (
            tracking_session.last_updated.isoformat()
            if tracking_session.last_updated
            else None
        ),
    })


# =============================================================
# TRACKING WORKFLOW
# =============================================================

@login_required
def tracking_page(request, pk):
    """
    Order Tracking Page.

    Tracking workflow fields:
        vehicle_placed
        vehicle_document
        invoice_eway
        advance_to_fleet
        balance_to_fleet
        fleet_departed
        arrived
        delivered
        pod_received
        lr_no_b
        settled

    Live Tracking:
        Tracking.live_tracking_at = timestamp/event
        TrackingSession = actual SmartTrail tracking session
    """

    order = get_object_or_404(
        Order.objects.select_related(
            "customer",
            "tracking",
            "tracking_session",
        ),
        pk=pk,
    )

    # ------------------------------------------------------------
    # GET / CREATE TRACKING
    # ------------------------------------------------------------

    tracking, _created = Tracking.objects.get_or_create(
        order=order
    )

    add_tracking_template_flags(tracking)

    # ------------------------------------------------------------
    # POST
    # ------------------------------------------------------------

    if request.method == "POST":

        # --------------------------------------------------------
        # LOCK AFTER SETTLEMENT
        # --------------------------------------------------------

        if tracking.settled:
            messages.warning(
                request,
                "Tracking already settled. Editing is locked.",
            )

            return redirect(
                "onepageorder_detail",
                pk=order.pk,
            )

        try:
            with transaction.atomic():

                now = timezone.now()

                # =================================================
                # CHECKBOXES
                # =================================================

                tracking.vehicle_document = (
                    "vehicle_document" in request.POST
                )

                tracking.vehicle_placed = (
                    "vehicle_placed" in request.POST
                )

                tracking.invoice_eway = (
                    "invoice_eway" in request.POST
                )

                tracking.advance_to_fleet = (
                    "advance_to_fleet" in request.POST
                )

                # HTML field:
                # balance_trans_fleet
                #
                # Model field:
                # balance_to_fleet

                tracking.balance_to_fleet = (
                    "balance_trans_fleet" in request.POST
                )

                tracking.fleet_departed = (
                    "fleet_departed" in request.POST
                )

                tracking.arrived = (
                    "arrived" in request.POST
                )

                tracking.delivered = (
                    "delivered" in request.POST
                )

                tracking.pod_received = (
                    "pod_received" in request.POST
                )

                tracking.settled = (
                    "settled" in request.POST
                )

                # =================================================
                # LR
                # =================================================

                tracking.lr_no_b = (
                    "lr_no_b" in request.POST
                )

                tracking.lr_no = get_post_value(
                    request,
                    "lr_no",
                )

                # =================================================
                # REMARKS
                # =================================================

                tracking.remarks = get_post_value(
                    request,
                    "remarks",
                )

                # =================================================
                # LIVE TRACKING
                # =================================================
                #
                # live_tracking_at is an event timestamp.
                #
                # Once enabled, DO NOT remove it when later
                # workflow statuses are completed.
                # =================================================

                live_tracking_requested = (
                    "live_tracking" in request.POST
                )

                if (
                    live_tracking_requested
                    and not tracking.live_tracking_at
                ):
                    tracking.live_tracking_at = now

                # =================================================
                # TIMELINE
                # =================================================

                if (
                    tracking.vehicle_placed
                    and not tracking.vehicle_placed_at
                ):
                    tracking.vehicle_placed_at = now

                if (
                    tracking.fleet_departed
                    and not tracking.fleet_departed_at
                ):
                    tracking.fleet_departed_at = now

                if (
                    tracking.arrived
                    and not tracking.arrived_at
                ):
                    tracking.arrived_at = now

                if (
                    tracking.delivered
                    and not tracking.delivered_at
                ):
                    tracking.delivered_at = now

                # =================================================
                # CURRENT WORKFLOW STATUS
                # =================================================
                #
                # Live Tracking is NOT used as the permanent
                # current status once the trip progresses.
                #
                # Example:
                # Live Tracking enabled
                #        ↓
                # Fleet Departed
                #        ↓
                # Arrived
                #        ↓
                # Delivered
                #
                # live_tracking_at remains stored.
                # =================================================

                if tracking.settled:
                    tracking.status = "settled"

                elif tracking.pod_received:
                    tracking.status = "pod_received"

                elif tracking.delivered:
                    tracking.status = "delivered"

                elif tracking.arrived:
                    tracking.status = "arrived"

                elif tracking.balance_to_fleet:
                    tracking.status = "balance_trans_fleet"

                elif tracking.fleet_departed:
                    tracking.status = "fleet_departed"

                elif tracking.advance_to_fleet:
                    tracking.status = "advance_to_fleet"

                elif tracking.invoice_eway:
                    tracking.status = "invoice_eway"

                elif tracking.lr_no_b:
                    tracking.status = "lr_generated"

                elif tracking.vehicle_document:
                    tracking.status = "vehicle_document"

                elif tracking.live_tracking_at:
                    tracking.status = "live_tracking"

                elif tracking.vehicle_placed:
                    tracking.status = "vehicle_placed"

                tracking.save()

                add_tracking_template_flags(tracking)

                # =================================================
                # DOCUMENT UPLOAD
                # =================================================

                uploaded_files = request.FILES.getlist(
                    "documents"
                )

                for uploaded_file in uploaded_files:

                    TrackingDocument.objects.create(
                        tracking=tracking,
                        file=uploaded_file,
                    )

            # ====================================================
            # LIVE TRACKING NAVIGATION
            # ====================================================

            if live_tracking_requested:

                tracking_session = getattr(
                    order,
                    "tracking_session",
                    None,
                )

                # -----------------------------------------------
                # Existing Tracking Session
                # -----------------------------------------------

                if tracking_session:

                    return redirect(
                        "onepageordervehicle_live",
                        tracking_session.pk,
                    )

                # -----------------------------------------------
                # No Tracking Session
                # -----------------------------------------------

                return redirect(
                    "import_driver",
                    order.pk,
                )

            # ====================================================
            # NORMAL SAVE
            # ====================================================

            messages.success(
                request,
                "Tracking updated successfully.",
            )

            return redirect(
                "onepageorder_detail",
                pk=order.pk,
            )

        except ValidationError as e:

            logger.warning(
                "Tracking validation failed: %s",
                e,
                exc_info=True,
            )

            messages.error(
                request,
                str(e),
            )

        except Exception:

            logger.exception(
                "Unexpected error while updating tracking "
                "for order %s",
                order.pk,
            )

            messages.error(
                request,
                "Unable to update tracking. Please try again.",
            )

    # ------------------------------------------------------------
    # LIVE TRACKING SESSION
    # ------------------------------------------------------------

    tracking_session = getattr(
        order,
        "tracking_session",
        None,
    )

    # ------------------------------------------------------------
    # RENDER
    # ------------------------------------------------------------

    return render(
        request,
        "onepageorders/tracking.html",
        {
            "order": order,
            "tracking": tracking,
            "tracking_session": tracking_session,
            "documents": tracking.documents.all(),
            "live_tracking_enabled": bool(
                tracking.live_tracking_at
            ),
        },
    )

# =============================================================
# ORDER EDIT
# =============================================================

@login_required
def onepageorder_edit(request, pk):

    order = get_object_or_404(
        Order.objects.select_related("customer"),
        pk=pk,
    )

    if request.method == "POST":

        try:
            with transaction.atomic():

                # ------------------------------------------------
                # CUSTOMER
                # ------------------------------------------------

                customer = order.customer

                customer.name = get_post_value(
                    request,
                    "customer_name",
                )

                customer.contact_number = get_post_value(
                    request,
                    "contact_number",
                )

                customer.email = get_post_value(
                    request,
                    "email",
                )

                customer.address = get_post_value(
                    request,
                    "address",
                )

                if not customer.name:
                    raise ValidationError(
                        "Customer Name is required."
                    )

                customer.full_clean()
                customer.save()

                # ------------------------------------------------
                # CUSTOMER / SALES
                # ------------------------------------------------

                order.lead_generated_through = get_post_value(
                    request,
                    "lead_generated_through",
                )

                order.reference_name = get_post_value(
                    request,
                    "reference_name",
                )

                order.sales_closed_by = get_post_value(
                    request,
                    "sales_closed_by",
                )

                # ------------------------------------------------
                # SHIPMENT
                # ------------------------------------------------

                order.origin = get_post_value(
                    request,
                    "origin",
                )

                order.destination = get_post_value(
                    request,
                    "destination",
                )

                order.material = get_post_value(
                    request,
                    "material",
                )

                order.packing_type = get_post_value(
                    request,
                    "packing_type",
                )

                order.no_of_pieces = to_integer(
                    request.POST.get(
                        "no_of_pieces"
                    )
                )

                order.weight_tons = to_decimal(
                    request.POST.get(
                        "weight_tons"
                    ),
                    "0.000",
                )

                # ------------------------------------------------
                # VEHICLE
                # ------------------------------------------------

                order.vehicle_type = get_post_value(
                    request,
                    "vehicle_type",
                )

                order.vehicle_number = get_post_value(
                    request,
                    "vehicle_number",
                )

                order.driver_number = get_post_value(
                    request,
                    "driver_number",
                )

                order.owner_number = get_post_value(
                    request,
                    "owner_number",
                )

                order.vehicle_sourced_by = request.POST.get(
                    "vehicle_sourced_by",
                    "Direct",
                )

                order.owner_broker_name = get_post_value(
                    request,
                    "owner_broker_name",
                )

                # ------------------------------------------------
                # COMMERCIALS
                # ------------------------------------------------

                order.freight_amount = to_decimal(
                    request.POST.get(
                        "freight_amount"
                    )
                )

                order.loading_unloading_charges = to_decimal(
                    request.POST.get(
                        "loading_unloading_charges"
                    )
                )

                order.halting_charges = to_decimal(
                    request.POST.get(
                        "halting_charges"
                    )
                )

                order.other_charges = to_decimal(
                    request.POST.get(
                        "other_charges"
                    )
                )

                order.selling_amount = to_decimal(
                    request.POST.get(
                        "selling_amount"
                    )
                )

                order.gst_percent = gst_from_request(
                    request
                )

                order.manager_approval = request.POST.get(
                    "manager_approval",
                    "Pending",
                )

                order.approved_by = get_post_value(
                    request,
                    "approved_by",
                )

                # ------------------------------------------------
                # CUSTOMER PAYMENT TERMS
                # ------------------------------------------------

                order.customer_billing_type = request.POST.get(
                    "customer_billing_type",
                    "",
                )

                order.customer_payment_type = request.POST.get(
                    "customer_payment_type",
                    "",
                )

                order.customer_advance_amount = to_decimal(
                    request.POST.get(
                        "customer_advance_amount"
                    )
                )

                order.customer_balance_amount = to_decimal(
                    request.POST.get(
                        "customer_balance_amount"
                    )
                )

                order.customer_payment_method = request.POST.get(
                    "customer_payment_method",
                    "",
                )

                order.promised_due_date = to_date(
                    request.POST.get(
                        "promised_due_date"
                    )
                )

                # ------------------------------------------------
                # CONTRACTED VEHICLE PAYMENT
                # ------------------------------------------------

                order.vehicle_advance_amount = to_decimal(
                    request.POST.get(
                        "vehicle_advance_amount"
                    )
                )

                order.vehicle_balance_amount = to_decimal(
                    request.POST.get(
                        "vehicle_balance_amount"
                    )
                )

                order.vehicle_owner_name = get_post_value(
                    request,
                    "vehicle_owner_name",
                )

                order.pan_card = get_post_value(
                    request,
                    "pan_card",
                )

                order.account_name = get_post_value(
                    request,
                    "account_name",
                )

                order.account_number = get_post_value(
                    request,
                    "account_number",
                )

                order.ifsc_code = get_post_value(
                    request,
                    "ifsc_code",
                )

                order.upi_number = get_post_value(
                    request,
                    "upi_number",
                )

                # ------------------------------------------------
                # OPTIONS
                # ------------------------------------------------

                order.send_sms = (
                    request.POST.get("send_sms")
                    == "on"
                )

                order.create_agreement_tds = (
                    request.POST.get(
                        "create_agreement_tds"
                    )
                    == "on"
                )

                # ------------------------------------------------
                # VALIDATE + SAVE
                # ------------------------------------------------

                order.full_clean()
                order.save()

            messages.success(
                request,
                (
                    f"Order {order.trip_number} "
                    "updated successfully."
                ),
            )

            return redirect(
                "onepageorder_detail",
                pk=order.pk,
            )

        except ValidationError as e:

            logger.warning(
                "Order edit validation failed: %s",
                e,
                exc_info=True,
            )

            if hasattr(e, "message_dict"):
                error_messages = []

                for field, errors in (
                    e.message_dict.items()
                ):
                    for error in errors:
                        error_messages.append(
                            f"{field}: {error}"
                        )

                messages.error(
                    request,
                    " | ".join(error_messages),
                )
            else:
                messages.error(
                    request,
                    str(e),
                )

        except Exception:

            logger.exception(
                "Unexpected error while editing order %s",
                order.pk,
            )

            messages.error(
                request,
                "Unable to update order. Please try again.",
            )

    return render(
        request,
        "onepageorders/order_edit.html",
        {
            "order": order,
        },
    )


# =============================================================
# VEHICLE PAYMENTS
# =============================================================

@login_required
def vehicle_payments(request):

    search = request.GET.get("q", "").strip()

    orders = order_queryset()

    if search:
        orders = orders.filter(
            Q(trip_number__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(origin__icontains=search)
            | Q(destination__icontains=search)
            | Q(vehicle_number__icontains=search)
            | Q(vehicle_type__icontains=search)
        )

    payments = (
        VehiclePayment.objects
        .select_related(
            "order",
            "order__customer",
        )
        .order_by(
            "-paid_at",
            "-id",
        )
    )

    if request.method == "POST":

        try:
            order_id = get_post_value(
                request,
                "order",
            )

            vehicle_number = get_post_value(
                request,
                "vehicle_number",
            ).upper()

            payment_type = get_post_value(
                request,
                "payment_type",
            )

            amount_value = get_post_value(
                request,
                "amount",
            )

            transaction_reference = get_post_value(
                request,
                "transaction_reference",
            )

            if not order_id:
                raise ValidationError(
                    "Please select a Trip / Order."
                )

            order = get_object_or_404(
                Order,
                pk=order_id,
            )

            if not vehicle_number:
                raise ValidationError(
                    "Vehicle Number is required."
                )

            valid_payment_types = {
                "Advance",
                "Balance",
                "Others",
            }

            if payment_type not in valid_payment_types:
                raise ValidationError(
                    "Please select a valid Payment Type."
                )

            amount = to_decimal(
                amount_value,
                "0.00",
            )

            if amount <= 0:
                raise ValidationError(
                    "Payment amount must be greater than zero."
                )

            with transaction.atomic():
                payment = VehiclePayment.objects.create(
                    order=order,
                    vehicle_number=vehicle_number,
                    payment_type=payment_type,
                    amount=amount,
                    transaction_reference=(
                        transaction_reference
                    ),
                )

            messages.success(
                request,
                (
                    f"Vehicle payment of "
                    f"₹{payment.amount:,.2f} "
                    "saved successfully."
                ),
            )

            return redirect(
                "vehicle_payments"
            )

        except ValidationError as e:

            messages.error(
                request,
                str(e),
            )

        except Exception:

            logger.exception(
                "Unexpected vehicle payment error"
            )

            messages.error(
                request,
                "Unable to save vehicle payment.",
            )

    return render(
        request,
        "onepageorders/vehicle_payments.html",
        payment_page_context(
            orders,
            payments,
        ),
    )


# =============================================================
# CUSTOMER PAYMENTS
# =============================================================

@login_required
def customer_payments(request):

    search = request.GET.get("q", "").strip()

    orders = order_queryset()

    if search:
        orders = orders.filter(
            Q(trip_number__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(origin__icontains=search)
            | Q(destination__icontains=search)
            | Q(vehicle_number__icontains=search)
            | Q(vehicle_type__icontains=search)
        )

    payments = (
        CustomerPayment.objects
        .select_related(
            "order",
            "order__customer",
        )
        .order_by(
            "-received_at",
            "-id",
        )
    )

    if request.method == "POST":

        try:
            order_id = get_post_value(
                request,
                "order",
            )

            received_amount = to_decimal(
                get_post_value(
                    request,
                    "received_amount",
                ),
                "0.00",
            )

            received_through = get_post_value(
                request,
                "received_through",
            )

            utr_details = get_post_value(
                request,
                "utr_details",
            )

            if not order_id:
                raise ValidationError(
                    "Please select a Trip / Order."
                )

            order = get_object_or_404(
                Order,
                pk=order_id,
            )

            # Customer payment is against the GST-inclusive
            # total selling amount.
            selling_amount = order.total_selling_amount

            if selling_amount <= 0:
                raise ValidationError(
                    (
                        "Total selling amount is not available "
                        f"for Trip {order.trip_number}."
                    )
                )

            if received_amount < 0:
                raise ValidationError(
                    "Received Amount cannot be negative."
                )

            valid_modes = {
                "RTGS",
                "NEFT",
                "CASH",
                "IMPS",
                "UPI",
            }

            if received_through not in valid_modes:
                raise ValidationError(
                    "Please select a valid payment mode."
                )

            with transaction.atomic():
                payment = CustomerPayment.objects.create(
                    order=order,
                    selling_amount=selling_amount,
                    received_amount=received_amount,
                    received_through=received_through,
                    utr_details=utr_details,
                )

            messages.success(
                request,
                (
                    f"Customer payment of "
                    f"₹{payment.received_amount:,.2f} "
                    "saved successfully."
                ),
            )

            return redirect(
                "customer_payments"
            )

        except ValidationError as e:

            messages.error(
                request,
                str(e),
            )

        except Exception:

            logger.exception(
                "Unexpected customer payment error"
            )

            messages.error(
                request,
                "Unable to save customer payment.",
            )

    return render(
        request,
        "onepageorders/customer_payments.html",
        payment_page_context(
            orders,
            payments,
        ),
    )


# =============================================================
# ADMIN MARGIN
# =============================================================

@login_required
def admin_margin(request):

    orders = (
        Order.objects
        .select_related(
            "customer",
            "tracking",
        )
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

# # =============================================================
# HELPER FUNCTIONS
# =============================================================

def get_driver_mobile(session):
    return session.driver_mobile or session.order.driver_number or ""


def unique_location_history(session):
    locations = session.locations.all().order_by("-received_at")
    history = []
    seen = set()

    for location in locations:
        key = (location.latitude, location.longitude)
        if key not in seen:
            seen.add(key)
            history.append(location)

    return history


# =============================================================
# LIVE TRACKING LIST
# =============================================================

@login_required
def live_tracking_list(request):
    query = request.GET.get("q", "").strip()

    orders = (
        Order.objects
        .select_related("customer", "tracking", "tracking_session")
        .filter(tracking_session__isnull=False)
        .exclude(tracking__settled=True)
        .order_by("-id")
    )

    if query:
        orders = orders.filter(
            Q(trip_number__icontains=query)
            | Q(customer__name__icontains=query)
            | Q(vehicle_number__icontains=query)
            | Q(driver_number__icontains=query)
            | Q(origin__icontains=query)
            | Q(destination__icontains=query)
        )

    return render(
        request,
        "live_tracking/list.html",
        {
            "orders": orders,
            "q": query,
        },
    )


# =============================================================
# LIVE TRACKING SETUP
# =============================================================

@login_required
def onepageorderlive_tracking_setup(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related(
            "customer", "tracking", "tracking_session"
        ),
        pk=order_id,
    )

    session = getattr(order, "tracking_session", None)

    return render(
        request,
        "onepageorders/setup.html",
        {
            "order": order,
            "session": session,
        },
    )

# # =============================================================
# # IMPORT DRIVER
# # =============================================================

@login_required
def import_driver(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    # ImportService must accept Order rather than Vehicle.
    result = ImportService.import_driver(order)

    if result.get("success"):
        if result.get("already_exists"):
            messages.info(
                request,
                "Driver is already registered in Telenity. "
                "Using the existing tracking profile.",
            )
        else:
            messages.success(
                request,
                "Driver imported successfully into Telenity.",
            )

        return redirect(
            "onepageorderlive_tracking_setup",
            order_id=order.pk,
        )

    error_message = result.get("message", "Import failed.")

    if isinstance(error_message, dict):
        error_message = (
            error_message.get("errorMessage")
            or error_message.get("raw_response")
            or str(error_message)
        )

    messages.error(request, error_message)

    return redirect(
        "onepageorderlive_tracking_setup",
        order_id=order.pk,
    )


# =============================================================
# DELETE TRACKING
# =============================================================

@login_required
def delete_tracking(request, pk):
    if request.method != "POST":
        return redirect("live_tracking_list")

    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=pk,
    )

    if not session.entity_id:
        messages.warning(
            request,
            "Tracking entity ID is missing.",
        )
        return redirect("live_tracking_list")

    result = DeleteService.delete_tracking(session)

    if result.get("success"):
        session.status = "deleted"
        session.tracking_enabled = False
        session.save(update_fields=["status", "tracking_enabled"])

        messages.success(
            request,
            "Tracking deleted successfully for "
            f"{session.order.trip_number}.",
        )
    else:
        messages.error(
            request,
            result.get("message", "Unable to delete tracking."),
        )

    return redirect("live_tracking_list")


# # =============================================================
# # SEND / CHECK CONSENT
# # =============================================================

@login_required
def send_consent(request, session_id):
    session = get_object_or_404(TrackingSession, pk=session_id)
    result = ConsentService.check_consent(session)

    if result.get("success"):
        messages.success(
            request,
            "Consent status checked successfully.",
        )
    else:
        messages.error(
            request,
            str(result.get("message", "Unable to check consent.")),
        )

    return redirect("live_tracking_list")


@login_required
def check_consent(request, session_id):
    session = get_object_or_404(TrackingSession, pk=session_id)
    result = ConsentService.check_consent(session)

    if not result.get("success"):
        messages.error(
            request,
            str(result.get("message", "Unable to check consent.")),
        )
        return redirect("live_tracking_list")

    consent_status = result.get("status")

    if consent_status in {
        "approved",
        "accepted",
        "consent_received",
        "active",
    }:
        session.consent_received = True
        session.status = "consent_received"
        session.save(update_fields=["consent_received", "status"])

        modify_result = ModifyService.start_tracking(session)

        if modify_result.get("success"):
            session.tracking_enabled = True
            session.status = "waiting_location"
            session.save(
                update_fields=["tracking_enabled", "status"]
            )

            messages.success(
                request,
                "Consent received. Live tracking has been activated.",
            )
        else:
            messages.warning(
                request,
                "Consent received, but live tracking could not be "
                "activated: "
                + str(
                    modify_result.get(
                        "message",
                        "Modify API failed.",
                    )
                ),
            )
    else:
        messages.warning(
            request,
            f"Consent Status : {consent_status}",
        )

    return redirect("live_tracking_list")

# =============================================================
# TEST LOCATION
# =============================================================

@login_required
def test_location(request, session_id):
    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=session_id,
    )

    driver_mobile = get_driver_mobile(session)

    if not driver_mobile:
        return JsonResponse(
            {
                "success": False,
                "message": "Driver mobile number is not available.",
            },
            status=400,
        )

    result = LocationService.get_location(driver_mobile)
    return JsonResponse(result, safe=False)


# =============================================================
# LIVE TRACKING PAGE
# =============================================================

@login_required
def vehicle_live(request, session_id):
    session = get_object_or_404(
        TrackingSession.objects.select_related(
            "order",
            "order__customer",
            "order__tracking",
        ),
        pk=session_id,
    )

    order = session.order
    latest_location = (
        session.locations
        .order_by("-received_at")
        .first()
    )

    return render(
        request,
        "live_tracking/vehicle_live.html",
        {
            "session": session,
            "order": order,
            "tracking": getattr(order, "tracking", None),
            "latest_location": latest_location,
            "locations": session.locations.all(),
        },
    )

# # # =============================================================
# # # LOCATION HISTORY
# # # =============================================================

@login_required
def vehicle_history(request, session_id):
    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=session_id,
    )

    history = unique_location_history(session)

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "order": session.order,
            "history": history,
        },
    )


@login_required
def live_tracking_history(request, session_id):
    return vehicle_history(request, session_id)


@login_required
def tracking_history(request, session_id):
    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=session_id,
    )

    history = session.locations.all().order_by("-received_at")

    return render(
        request,
        "live_tracking/history.html",
        {
            "session": session,
            "order": session.order,
            "history": history,
        },
    )


# =============================================================
# REFRESH LOCATION
# =============================================================

@login_required
def refresh_location(request, session_id):
    session = get_object_or_404(
        TrackingSession.objects.select_related("order"),
        pk=session_id,
    )

    logger.info(
        "REFRESH LOCATION | session=%s order=%s driver_mobile=%s "
        "entity_id=%s consent=%s status=%s",
        session.id,
        session.order.trip_number,
        get_driver_mobile(session),
        session.entity_id,
        session.consent_received,
        session.status,
    )

    # ---------------------------------------------------------
    # 1. CONSENT CHECK
    # ---------------------------------------------------------

    if not session.consent_received:
        messages.warning(
            request,
            "Driver consent has not been approved yet.",
        )
        return redirect(
            "vehicle_live",
            session_id=session.id,
        )

    # ---------------------------------------------------------
    # 2. START TRACKING IF NOT ENABLED
    # ---------------------------------------------------------

    if not session.tracking_enabled:
        modify_result = ModifyService.start_tracking(session)

        if not modify_result.get("success"):
            messages.error(
                request,
                "Unable to start tracking: "
                f"{modify_result.get('message', 'Unknown error')}",
            )
            return redirect(
                "vehicle_live",
                session_id=session.id,
            )

        session.tracking_enabled = True
        session.status = "active"
        session.save(
            update_fields=["tracking_enabled", "status"]
        )

        messages.success(
            request,
            "Tracking started. Fetching vehicle location...",
        )

    # ---------------------------------------------------------
    # 3. FETCH LOCATION
    # ---------------------------------------------------------

    result = LocationService.fetch_location(session)

    logger.info(
        "REFRESH LOCATION RESULT | session=%s result=%s",
        session.id,
        result,
    )

    if result.get("success"):
        response = result.get("response", {})
        terminals = response.get("terminalLocation", [])

        if terminals:
            terminal = terminals[0]
            current = terminal.get("currentLocation")

            if current:
                messages.success(
                    request,
                    "Vehicle location updated successfully.",
                )
            else:
                messages.info(
                    request,
                    "Tracking is enabled, but the current location "
                    "has not been retrieved yet.",
                )
        else:
            messages.warning(
                request,
                "Location information is not available yet.",
            )
    else:
        messages.error(
            request,
            result.get(
                "message",
                "Unable to retrieve vehicle location.",
            ),
        )

    return redirect(
        "vehicle_live",
        session_id=session.id,
    )

# # =============================================================
# # TEST AUTHENTICATION
# # =============================================================

@login_required
def test_consent_auth(request):
    result = ConsentAuthService.get_consent_token()
    return JsonResponse(result, safe=False)


@login_required
def test_tracking_auth(request):
    result = TrackingAuthService.get_tracking_token()
    logger.info("Tracking auth result type=%s", type(result))
    return JsonResponse(result, safe=False)


@login_required
def api_token_status(request):
    tracking = TrackingAuthService.get_tracking_token()
    consent = ConsentAuthService.get_consent_token()

    return JsonResponse(
        {
            "tracking": tracking,
            "consent": consent,
        }
    )
