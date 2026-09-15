# dashboards/services.py

from decimal import Decimal

from django.db.models import Sum, Count
from django.utils import timezone

from enquiries.models import Enquiry
from orders.models import Order
from vehicles.models import Vehicle, Tracking
from accounts.models import CustomerTransaction, VehicleTransaction


ZERO = Decimal("0.00")


def money(value):
    return Decimal(value or 0)


def get_month_range(months=6):

    today = timezone.localdate()

    current_year = today.year
    current_month = today.month

    result = []

    for i in range(months - 1, -1, -1):

        month = current_month - i
        year = current_year

        while month <= 0:
            month += 12
            year -= 1

        result.append((year, month))

    return result


def get_management_dashboard_data():

    # ============================================================
    # BASE QUERYSETS
    # ============================================================

    orders = Order.objects.all()
    vehicles = Vehicle.objects.all()
    enquiries = Enquiry.objects.all()
    tracking = Tracking.objects.all()


    # ============================================================
    # ORDERS
    # ============================================================

    total_orders = orders.count()

    assigned_orders = (
        orders
        .filter(vehicles__isnull=False)
        .distinct()
        .count()
    )

    unassigned_orders = max(
        total_orders - assigned_orders,
        0
    )


    # ============================================================
    # ENQUIRIES
    # ============================================================

    total_enquiries = enquiries.count()


    # ============================================================
    # TRACKING
    # ============================================================

    delivered_orders = tracking.filter(
        delivered=True
    ).count()

    arrived_orders = tracking.filter(
        arrived=True,
        delivered=False
    ).count()

    in_transit_orders = tracking.filter(
        fleet_departed=True,
        delivered=False
    ).count()

    settled_orders = tracking.filter(
        settled=True
    ).count()

    pending_pod = tracking.filter(
        delivered=True,
        pod_received=False
    ).count()

    live_tracking_count = tracking.filter(
        status="live_tracking",
        delivered=False
    ).count()

    vehicle_placed_count = tracking.filter(
        vehicle_placed=True,
        delivered=False
    ).count()


    # ============================================================
    # VEHICLES
    # ============================================================

    total_vehicles = vehicles.count()

    vehicles_with_order = vehicles.filter(
        order__isnull=False
    ).count()

    vehicles_without_order = vehicles.filter(
        order__isnull=True
    ).count()

    bank_pending = vehicles.filter(
        bank_verified=False
    ).count()


    # ============================================================
    # VEHICLE FINANCIALS
    #
    # Vehicle model contains:
    # freight_amount
    # total_freight
    # advance
    # balance
    #
    # There is NO profit_amount.
    # ============================================================

    vehicle_financials = vehicles.aggregate(

        total_freight=Sum("total_freight"),

        total_advance=Sum("advance"),

        total_balance=Sum("balance"),

    )


    total_vehicle_freight = money(
        vehicle_financials["total_freight"]
    )

    vehicle_advance = money(
        vehicle_financials["total_advance"]
    )

    vehicle_balance = money(
        vehicle_financials["total_balance"]
    )


    # ============================================================
    # CUSTOMER BILLING
    # ============================================================

    total_billed = money(
        orders.aggregate(
            total=Sum("total_rate")
        )["total"]
    )


    # ============================================================
    # CUSTOMER PAYMENTS
    #
    # Use actual CustomerTransaction records.
    # ============================================================

    customer_received = money(
        CustomerTransaction.objects.aggregate(
            total=Sum("amount")
        )["total"]
    )


    customer_outstanding = max(
        total_billed - customer_received,
        ZERO
    )


    # ============================================================
    # VEHICLE EXPENSES
    # ============================================================

    vehicle_expenses = money(
        VehicleTransaction.objects.aggregate(
            total=Sum("amount")
        )["total"]
    )


    # ============================================================
    # MANAGEMENT PROFIT
    #
    # No profit_amount field exists in Vehicle.
    #
    # Therefore:
    #
    # Revenue - Vehicle Freight
    #
    # This is the gross operating margin before any
    # additional company overhead.
    # ============================================================

    total_profit = (
        total_billed -
        total_vehicle_freight
    )


    if total_profit < ZERO:
        total_profit = ZERO


    # ============================================================
    # PROFIT MARGIN
    # ============================================================

    profit_margin = 0

    if total_billed > 0:

        profit_margin = round(
            (
                total_profit /
                total_billed
            ) * 100,
            1
        )


    # ============================================================
    # MONTHLY CHART DATA
    # ============================================================

    monthly_data = []


    for year, month in get_month_range(6):

        current_tz = timezone.get_current_timezone()

        start_date = timezone.datetime(
            year,
            month,
            1,
            tzinfo=current_tz
        )


        if month == 12:

            next_month = timezone.datetime(
                year + 1,
                1,
                1,
                tzinfo=current_tz
            )

        else:

            next_month = timezone.datetime(
                year,
                month + 1,
                1,
                tzinfo=current_tz
            )


        month_orders = orders.filter(
            created_at__gte=start_date,
            created_at__lt=next_month
        )


        month_vehicles = vehicles.filter(
            created_at__gte=start_date,
            created_at__lt=next_month
        )


        revenue = money(
            month_orders.aggregate(
                total=Sum("total_rate")
            )["total"]
        )


        freight = money(
            month_vehicles.aggregate(
                total=Sum("total_freight")
            )["total"]
        )


        profit = revenue - freight


        if profit < ZERO:
            profit = ZERO


        order_count = month_orders.count()


        monthly_data.append({

            "label": start_date.strftime("%b %Y"),

            "revenue": float(revenue),

            "profit": float(profit),

            "orders": order_count,

        })


    # ============================================================
    # ENQUIRY STATUS
    # ============================================================

    enquiry_status_rows = (
        enquiries
        .values("status")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )


    enquiry_status_data = []


    for row in enquiry_status_rows:

        status = row["status"] or "Unknown"


        enquiry_status_data.append({

            "label":
                str(status)
                .replace("_", " ")
                .title(),

            "count":
                row["total"],

        })


    # ============================================================
    # CONVERSION RATE
    # ============================================================

    conversion_rate = 0


    if total_enquiries:

        conversion_rate = round(
            (
                total_orders /
                total_enquiries
            ) * 100,
            1
        )


    # ============================================================
    # OPERATIONS PIPELINE
    # ============================================================

    pipeline = {

        "vehicle_placed":
            vehicle_placed_count,

        "live_tracking":
            live_tracking_count,

        "fleet_departed":
            tracking.filter(
                fleet_departed=True,
                delivered=False
            ).count(),

        "arrived":
            tracking.filter(
                arrived=True,
                delivered=False
            ).count(),

        "delivered":
            delivered_orders,

        "pod_pending":
            pending_pod,

        "settled":
            settled_orders,

    }


    # ============================================================
    # RECENT ORDERS
    # ============================================================

    recent_orders = (
        orders
        .select_related("enquiry")
        .order_by("-created_at")[:10]
    )


    recent_orders_data = []


    for order in recent_orders:

        vehicle = (
            Vehicle.objects
            .filter(order=order)
            .first()
        )


        order_tracking = (
            Tracking.objects
            .filter(order=order)
            .first()
        )


        if order_tracking:

            status = (
                order_tracking
                .get_status_display()
            )

        elif vehicle:

            status = "Vehicle Assigned"

        else:

            status = "Pending Assignment"


        recent_orders_data.append({

            "order_no":
                order.order_no,

            "customer_name":
                order.customer_name,

            "vehicle_number":
                (
                    vehicle.vehicle_number
                    if vehicle
                    else "-"
                ),

            "total_rate":
                money(order.total_rate),

            "status":
                status,

            "created_at":
                order.created_at,

        })


    # ============================================================
    # MANAGEMENT ALERTS
    # ============================================================

    alerts = []


    if unassigned_orders:

        alerts.append({

            "type": "warning",

            "title":
                "Vehicle assignment pending",

            "count":
                unassigned_orders,

            "message":
                "Orders are waiting for vehicle assignment.",

        })


    if in_transit_orders:

        alerts.append({

            "type": "info",

            "title":
                "Vehicles in transit",

            "count":
                in_transit_orders,

            "message":
                "Vehicles are currently marked as departed.",

        })


    if pending_pod:

        alerts.append({

            "type": "warning",

            "title":
                "POD pending",

            "count":
                pending_pod,

            "message":
                "Delivered trips are waiting for POD.",

        })


    if bank_pending:

        alerts.append({

            "type": "warning",

            "title":
                "Bank verification pending",

            "count":
                bank_pending,

            "message":
                "Vehicle bank details are not verified.",

        })


    # ============================================================
    # RETURN CONTEXT
    # ============================================================

    return {

        # --------------------------------------------------------
        # ORDER / ENQUIRY
        # --------------------------------------------------------

        "total_enquiries":
            total_enquiries,

        "total_orders":
            total_orders,

        "assigned_orders":
            assigned_orders,

        "unassigned_orders":
            unassigned_orders,


        # --------------------------------------------------------
        # VEHICLES
        # --------------------------------------------------------

        "total_vehicles":
            total_vehicles,

        "vehicles_with_order":
            vehicles_with_order,

        "vehicles_without_order":
            vehicles_without_order,


        # --------------------------------------------------------
        # OPERATIONS
        # --------------------------------------------------------

        "in_transit_orders":
            in_transit_orders,

        "arrived_orders":
            arrived_orders,

        "delivered_orders":
            delivered_orders,

        "settled_orders":
            settled_orders,

        "pending_pod":
            pending_pod,

        "bank_pending":
            bank_pending,


        # --------------------------------------------------------
        # FINANCIAL
        # --------------------------------------------------------

        "total_billed":
            total_billed,

        "customer_received":
            customer_received,

        "customer_outstanding":
            customer_outstanding,

        "total_vehicle_freight":
            total_vehicle_freight,

        "vehicle_advance":
            vehicle_advance,

        "vehicle_balance":
            vehicle_balance,

        "vehicle_expenses":
            vehicle_expenses,

        "total_profit":
            total_profit,

        "profit_margin":
            profit_margin,


        # --------------------------------------------------------
        # CONVERSION
        # --------------------------------------------------------

        "conversion_rate":
            conversion_rate,


        # --------------------------------------------------------
        # CHARTS
        # --------------------------------------------------------

        "monthly_data":
            monthly_data,

        "enquiry_status_data":
            enquiry_status_data,


        # --------------------------------------------------------
        # PIPELINE
        # --------------------------------------------------------

        "pipeline":
            pipeline,


        # --------------------------------------------------------
        # RECENT ORDERS
        # --------------------------------------------------------

        "recent_orders":
            recent_orders_data,


        # --------------------------------------------------------
        # ALERTS
        # --------------------------------------------------------

        "alerts":
            alerts,


        # --------------------------------------------------------
        # LAST UPDATED
        # --------------------------------------------------------

        "last_updated":
            timezone.now(),

    }