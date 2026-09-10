from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Customer,
    Order,
    VehiclePayment,
    CustomerPayment,
)


# =============================================================
# HELPER FUNCTIONS
# =============================================================

def to_decimal(value, default="0.00"):
    """
    Safely convert POST value to Decimal.
    """
    if value in (None, ""):
        return Decimal(default)

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def to_integer(value, default=0):
    """
    Safely convert POST value to integer.
    """
    if value in (None, ""):
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def to_date(value):
    """
    HTML date input sends YYYY-MM-DD.
    """
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return None


# =============================================================
# ORDER LIST
# =============================================================

@login_required
def onepageorder_list(request):

    search = request.GET.get(
        "q",
        ""
    ).strip()

    orders = (
        Order.objects
        .select_related("customer")
        .prefetch_related(
            "vehicle_payments",
            "customer_payments",
        )
        .order_by("-id")
    )

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
# CREATE ORDER
# =============================================================

@login_required
def onepageorder_create(request):

    if request.method == "POST":

        try:

            with transaction.atomic():

                # =================================================
                # CUSTOMER
                # =================================================

                customer_name = request.POST.get(
                    "customer_name",
                    ""
                ).strip()

                contact_number = request.POST.get(
                    "contact_number",
                    ""
                ).strip()

                email = request.POST.get(
                    "email",
                    ""
                ).strip()

                address = request.POST.get(
                    "address",
                    ""
                ).strip()


                if not customer_name:

                    messages.error(
                        request,
                        "Customer Name is required."
                    )

                    return render(
                        request,
                        "onepageorders/order_create.html"
                    )


                customer = Customer(
                    name=customer_name,
                    contact_number=contact_number,
                    email=email,
                    address=address,
                )

                customer.full_clean()

                customer.save()


                # =================================================
                # ORDER
                # =================================================

                order = Order(

                    # -------------------------------------------------
                    # Customer / Sales
                    # -------------------------------------------------

                    customer=customer,

                    lead_generated_through=request.POST.get(
                        "lead_generated_through",
                        ""
                    ),

                    sales_closed_by=request.POST.get(
                        "sales_closed_by",
                        ""
                    ).strip(),


                    # -------------------------------------------------
                    # Shipment
                    # -------------------------------------------------

                    origin=request.POST.get(
                        "origin",
                        ""
                    ).strip(),

                    destination=request.POST.get(
                        "destination",
                        ""
                    ).strip(),

                    material=request.POST.get(
                        "material",
                        ""
                    ).strip(),

                    packing_type=request.POST.get(
                        "packing_type",
                        ""
                    ).strip(),

                    no_of_pieces=to_integer(
                        request.POST.get(
                            "no_of_pieces"
                        )
                    ),

                    weight_tons=to_decimal(
                        request.POST.get(
                            "weight_tons"
                        ),
                        "0.000"
                    ),


                    # -------------------------------------------------
                    # Vehicle
                    # -------------------------------------------------

                    vehicle_type=request.POST.get(
                        "vehicle_type",
                        ""
                    ).strip(),

                    vehicle_number=request.POST.get(
                        "vehicle_number",
                        ""
                    ).strip(),

                    driver_number=request.POST.get(
                        "driver_number",
                        ""
                    ).strip(),

                    owner_number=request.POST.get(
                        "owner_number",
                        ""
                    ).strip(),

                    vehicle_sourced_by=request.POST.get(
                        "vehicle_sourced_by",
                        "Direct"
                    ),

                    owner_broker_name=request.POST.get(
                        "owner_broker_name",
                        ""
                    ).strip(),


                    # -------------------------------------------------
                    # Commercials
                    # -------------------------------------------------

                    freight_amount=to_decimal(
                        request.POST.get(
                            "freight_amount"
                        )
                    ),

                    loading_unloading_charges=to_decimal(
                        request.POST.get(
                            "loading_unloading_charges"
                        )
                    ),

                    halting_charges=to_decimal(
                        request.POST.get(
                            "halting_charges"
                        )
                    ),

                    other_charges=to_decimal(
                        request.POST.get(
                            "other_charges"
                        )
                    ),

                    selling_amount=to_decimal(
                        request.POST.get(
                            "selling_amount"
                        )
                    ),

                    manager_approval=request.POST.get(
                        "manager_approval",
                        "Pending"
                    ),

                    approved_by=request.POST.get(
                        "approved_by",
                        ""
                    ).strip(),


                    # -------------------------------------------------
                    # Customer Payment Terms
                    # -------------------------------------------------

                    customer_billing_type=request.POST.get(
                        "customer_billing_type",
                        ""
                    ),

                    customer_payment_type=request.POST.get(
                        "customer_payment_type",
                        ""
                    ),

                    customer_advance_amount=to_decimal(
                        request.POST.get(
                            "customer_advance_amount"
                        )
                    ),

                    customer_balance_amount=to_decimal(
                        request.POST.get(
                            "customer_balance_amount"
                        )
                    ),

                    customer_payment_method=request.POST.get(
                        "customer_payment_method",
                        ""
                    ),

                    promised_due_date=to_date(
                        request.POST.get(
                            "promised_due_date"
                        )
                    ),


                    # -------------------------------------------------
                    # Contracted Vehicle Payment
                    # -------------------------------------------------

                    vehicle_advance_amount=to_decimal(
                        request.POST.get(
                            "vehicle_advance_amount"
                        )
                    ),

                    vehicle_balance_amount=to_decimal(
                        request.POST.get(
                            "vehicle_balance_amount"
                        )
                    ),

                    vehicle_owner_name=request.POST.get(
                        "vehicle_owner_name",
                        ""
                    ).strip(),

                    pan_card=request.POST.get(
                        "pan_card",
                        ""
                    ).strip(),

                    account_name=request.POST.get(
                        "account_name",
                        ""
                    ).strip(),

                    account_number=request.POST.get(
                        "account_number",
                        ""
                    ).strip(),

                    ifsc_code=request.POST.get(
                        "ifsc_code",
                        ""
                    ).strip(),

                    upi_number=request.POST.get(
                        "upi_number",
                        ""
                    ).strip(),


                    # -------------------------------------------------
                    # Optional
                    # -------------------------------------------------

                    send_sms=(
                        request.POST.get(
                            "send_sms"
                        ) == "on"
                    ),

                    create_agreement_tds=(
                        request.POST.get(
                            "create_agreement_tds"
                        ) == "on"
                    ),
                )


                # Validate model fields/choices.
                order.full_clean()

                # Calculates total_trip_cost and trip_number.
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

            print(
                "ORDER CREATE ERROR:",
                repr(e)
            )

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


# =============================================================
# ORDER DETAIL
# =============================================================

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

    return render(
        request,
        "onepageorders/order_detail.html",
        {
            "order": order,
        },
    )


# =============================================================
# EDIT ORDER
# =============================================================

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
                        "onepageorders/order_edit.html",
                        {
                            "order": order,
                        }
                    )


                customer.full_clean()

                customer.save()


                # =================================================
                # CUSTOMER / SALES
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

                order.no_of_pieces = to_integer(
                    request.POST.get(
                        "no_of_pieces"
                    )
                )

                order.weight_tons = to_decimal(
                    request.POST.get(
                        "weight_tons"
                    ),
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

                order.manager_approval = request.POST.get(
                    "manager_approval",
                    "Pending"
                )

                order.approved_by = request.POST.get(
                    "approved_by",
                    ""
                ).strip()


                # =================================================
                # CUSTOMER PAYMENT TERMS
                # =================================================

                order.customer_billing_type = request.POST.get(
                    "customer_billing_type",
                    ""
                )

                order.customer_payment_type = request.POST.get(
                    "customer_payment_type",
                    ""
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
                    ""
                )

                order.promised_due_date = to_date(
                    request.POST.get(
                        "promised_due_date"
                    )
                )


                # =================================================
                # CONTRACTED VEHICLE
                # =================================================

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
                # OPTIONAL CHECKBOXES
                # =================================================

                order.send_sms = (
                    request.POST.get(
                        "send_sms"
                    ) == "on"
                )

                order.create_agreement_tds = (
                    request.POST.get(
                        "create_agreement_tds"
                    ) == "on"
                )


                # =================================================
                # VALIDATE + SAVE
                # =================================================

                order.full_clean()

                # Recalculates total_trip_cost.
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
                "ORDER EDIT ERROR:",
                repr(e)
            )

            messages.error(
                request,
                f"Unable to update order: {str(e)}"
            )

            return render(
                request,
                "onepageorders/order_edit.html",
                {
                    "order": order,
                }
            )


    return render(
        request,
        "onepageorders/order_edit.html",
        {
            "order": order,
        }
    )


# =============================================================
# VEHICLE PAYMENTS
# =============================================================

@login_required
def vehicle_payments(request):

    # ---------------------------------------------------------
    # Orders for dropdown
    # ---------------------------------------------------------

    orders = (
        Order.objects
        .select_related("customer")
        .order_by("-id")
    )


    # ---------------------------------------------------------
    # Payment history
    # ---------------------------------------------------------

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


    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    if request.method == "POST":

        try:

            order_id = request.POST.get(
                "order",
                ""
            ).strip()

            vehicle_number = request.POST.get(
                "vehicle_number",
                ""
            ).strip().upper()

            payment_type = request.POST.get(
                "payment_type",
                ""
            ).strip()

            amount_value = request.POST.get(
                "amount",
                ""
            ).strip()

            transaction_reference = request.POST.get(
                "transaction_reference",
                ""
            ).strip()


            # =================================================
            # ORDER
            # =================================================

            if not order_id:

                messages.error(
                    request,
                    "Please select a Trip / Order."
                )

                return render(
                    request,
                    "onepageorders/vehicle_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            order = get_object_or_404(
                Order,
                pk=order_id
            )


            # =================================================
            # VEHICLE
            # =================================================

            if not vehicle_number:

                messages.error(
                    request,
                    "Vehicle Number is required."
                )

                return render(
                    request,
                    "onepageorders/vehicle_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            # =================================================
            # PAYMENT TYPE
            # =================================================

            valid_payment_types = {
                "Advance",
                "Balance",
                "Others",
            }

            if payment_type not in valid_payment_types:

                messages.error(
                    request,
                    "Please select a valid Payment Type."
                )

                return render(
                    request,
                    "onepageorders/vehicle_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            # =================================================
            # AMOUNT
            # =================================================

            try:

                amount = Decimal(
                    amount_value
                )

            except (
                InvalidOperation,
                ValueError,
                TypeError,
            ):

                messages.error(
                    request,
                    "Please enter a valid payment amount."
                )

                return render(
                    request,
                    "onepageorders/vehicle_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            if amount <= 0:

                messages.error(
                    request,
                    "Payment amount must be greater than zero."
                )

                return render(
                    request,
                    "onepageorders/vehicle_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            # =================================================
            # SAVE
            # =================================================

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
                    f"saved successfully."
                )
            )

            return redirect(
                "vehicle_payments"
            )


        except Exception as e:

            print(
                "VEHICLE PAYMENT ERROR:",
                repr(e)
            )

            messages.error(
                request,
                f"Unable to save payment: {str(e)}"
            )

            return render(
                request,
                "onepageorders/vehicle_payments.html",
                {
                    "orders": orders,
                    "payments": payments,
                }
            )


    return render(
        request,
        "onepageorders/vehicle_payments.html",
        {
            "orders": orders,
            "payments": payments,
        }
    )


# =============================================================
# CUSTOMER PAYMENTS
# =============================================================

@login_required
def customer_payments(request):

    # ---------------------------------------------------------
    # Orders for dropdown
    # ---------------------------------------------------------

    orders = (
        Order.objects
        .select_related("customer")
        .order_by("-id")
    )


    # ---------------------------------------------------------
    # Receipt history
    # ---------------------------------------------------------

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


    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    if request.method == "POST":

        try:

            order_id = request.POST.get(
                "order",
                ""
            ).strip()

            selling_amount_value = request.POST.get(
                "selling_amount",
                ""
            ).strip()

            received_amount_value = request.POST.get(
                "received_amount",
                ""
            ).strip()

            received_through = request.POST.get(
                "received_through",
                ""
            ).strip()

            utr_details = request.POST.get(
                "utr_details",
                ""
            ).strip()


            # =================================================
            # ORDER
            # =================================================

            if not order_id:

                messages.error(
                    request,
                    "Please select a Trip / Order."
                )

                return render(
                    request,
                    "onepageorders/customer_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            order = get_object_or_404(
                Order,
                pk=order_id
            )


            # =================================================
            # SELLING AMOUNT
            # =================================================

            try:

                selling_amount = Decimal(
                    selling_amount_value
                )

            except (
                InvalidOperation,
                ValueError,
                TypeError,
            ):

                messages.error(
                    request,
                    "Please enter a valid Selling Amount."
                )

                return render(
                    request,
                    "onepageorders/customer_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            if selling_amount <= 0:

                messages.error(
                    request,
                    "Selling Amount must be greater than zero."
                )

                return render(
                    request,
                    "onepageorders/customer_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            # =================================================
            # RECEIVED AMOUNT
            # =================================================

            try:

                received_amount = Decimal(
                    received_amount_value
                )

            except (
                InvalidOperation,
                ValueError,
                TypeError,
            ):

                messages.error(
                    request,
                    "Please enter a valid Received Amount."
                )

                return render(
                    request,
                    "onepageorders/customer_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            if received_amount < 0:

                messages.error(
                    request,
                    "Received Amount cannot be negative."
                )

                return render(
                    request,
                    "onepageorders/customer_payments.html",
                    {
                        "orders": orders,
                        "payments": payments,
                    }
                )


            # =================================================
            # PAYMENT MODE
            # =================================================

            valid_modes = {
                "RTGS",
                "NEFT",
                "CASH",
                "IMPS",
                "UPI",
            }

            if received_through not in valid_modes:
                received_through = ""


            # =================================================
            # SAVE
            # =================================================

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
                    f"saved successfully."
                )
            )

            return redirect(
                "customer_payments"
            )


        except Exception as e:

            print(
                "CUSTOMER PAYMENT ERROR:",
                repr(e)
            )

            messages.error(
                request,
                f"Unable to save customer payment: {str(e)}"
            )

            return render(
                request,
                "onepageorders/customer_payments.html",
                {
                    "orders": orders,
                    "payments": payments,
                }
            )


    return render(
        request,
        "onepageorders/customer_payments.html",
        {
            "orders": orders,
            "payments": payments,
        }
    )


# =============================================================
# ADMIN MARGIN
# =============================================================

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
        }
    )