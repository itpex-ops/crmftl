# dashboards/services.py

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count
from django.utils import timezone

from enquiries.models import Enquiry
from orders.models import Order
from vehicles.models import Vehicle, Tracking

from accounts.models import CustomerTransaction, VehicleTransaction


ZERO = Decimal("0.00")


def money(value):
    """
    Safely convert DB aggregate values to Decimal.
    """
    return Decimal(value or 0)


def get_month_range(months=6):
    """
    Returns the first day of each month for the last `months` months.
    """
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
    """
    Main data service for the Management Dashboard.

    All business calculations are kept here rather than inside
    the template or view.
    """

    # ============================================================
    # BASE QUERYSETS
    # ============================================================

    orders = Order.objects.all()
    vehicles = Vehicle.objects.all()
    enquiries = Enquiry.objects.all()

    # ============================================================
    # ORDER KPIs
    # ============================================================

    total_orders = orders.count()

    assigned_orders = (
        orders
        .filter(vehicles__isnull=False)
        .distinct()
        .count()
    )

    unassigned_orders = max(total_orders - assigned_orders, 0)

    # ============================================================
    # TRACKING KPIs
    # ============================================================

    total_tracking = Tracking.objects.count()

    delivered_orders = Tracking.objects.filter(
        delivered=True
    ).count()

    arrived_orders = Tracking.objects.filter(
        arrived=True,
        delivered=False,
    ).count()

    in_transit_orders = Tracking.objects.filter(
        fleet_departed=True,
        delivered=False,
    ).count()

    settled_orders = Tracking.objects.filter(
        settled=True
    ).count()

    pending_pod = Tracking.objects.filter(
        delivered=True,
        pod_received=False,
    ).count()

    # ============================================================
    # VEHICLE KPIs
    # ============================================================

    total_vehicles = vehicles.count()

    vehicles_with_order = (
        vehicles
        .filter(order__isnull=False)
        .count()
    )

    vehicles_without_order = (
        vehicles
        .filter(order__isnull=True)
        .count()
    )

    approval_required = vehicles.filter(
        approval_required=True
    ).count()

    bank_pending = vehicles.filter(
        bank_verified=False
    ).count()

    # ============================================================
    # VEHICLE FINANCIALS
    # ============================================================

    vehicle_financials = vehicles.aggregate(
        total_freight=Sum("total_freight"),
        total_profit=Sum("profit_amount"),
        total_advance=Sum("advance"),
        total_balance=Sum("balance"),
    )

    total_vehicle_freight = money(
        vehicle_financials["total_freight"]
    )

    total_profit = money(
        vehicle_financials["total_profit"]
    )

    vehicle_advance = money(
        vehicle_financials["total_advance"]
    )

    vehicle_balance = money(
        vehicle_financials["total_balance"]
    )

    # ============================================================
    # CUSTOMER FINANCIALS
    # ============================================================

    total_billed = money(
        orders.aggregate(
            total=Sum("total_rate")
        )["total"]
    )

    customer_received = money(
        CustomerTransaction.objects.filter(
            transaction_type__in=[
                "payment",
                "advance",
            ]
        ).aggregate(
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
        VehicleTransaction.objects.exclude(
            transaction_type__in=[
                "advance",
                "balance",
            ]
        ).aggregate(
            total=Sum("amount")
        )["total"]
    )

    # ============================================================
    # MONTHLY CHART DATA
    # ============================================================

    monthly_data = []

    for year, month in get_month_range(6):

        start_date = timezone.datetime(
            year,
            month,
            1,
            tzinfo=timezone.get_current_timezone(),
        )

        if month == 12:
            next_month = timezone.datetime(
                year + 1,
                1,
                1,
                tzinfo=timezone.get_current_timezone(),
            )
        else:
            next_month = timezone.datetime(
                year,
                month + 1,
                1,
                tzinfo=timezone.get_current_timezone(),
            )

        month_orders = orders.filter(
            created_at__gte=start_date,
            created_at__lt=next_month,
        )

        month_vehicles = vehicles.filter(
            created_at__gte=start_date,
            created_at__lt=next_month,
        )

        revenue = money(
            month_orders.aggregate(
                total=Sum("total_rate")
            )["total"]
        )

        profit = money(
            month_vehicles.aggregate(
                total=Sum("profit_amount")
            )["total"]
        )

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
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    enquiry_status_data = []

    for row in enquiry_status_rows:
        status = row["status"] or "Unknown"

        enquiry_status_data.append({
            "label": str(status).replace("_", " ").title(),
            "count": row["total"],
        })

    total_enquiries = enquiries.count()

    # ============================================================
    # CONVERSION
    # ============================================================

    conversion_rate = 0

    if total_enquiries:
        conversion_rate = round(
            (total_orders / total_enquiries) * 100,
            1
        )

    # ============================================================
    # OPERATIONAL PIPELINE
    # ============================================================

    pipeline = {
        "vehicle_placed": Tracking.objects.filter(
            vehicle_placed=True,
            delivered=False,
        ).count(),

        "live_tracking": Tracking.objects.filter(
            status="live_tracking",
            delivered=False,
        ).count(),

        "fleet_departed": Tracking.objects.filter(
            fleet_departed=True,
            delivered=False,
        ).count(),

        "arrived": Tracking.objects.filter(
            arrived=True,
            delivered=False,
        ).count(),

        "delivered": Tracking.objects.filter(
            delivered=True,
        ).count(),

        "pod_pending": pending_pod,

        "settled": Tracking.objects.filter(
            settled=True
        ).count(),
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

        tracking = (
            Tracking.objects
            .filter(order=order)
            .first()
        )

        if tracking:
            status = tracking.get_status_display()
        elif vehicle:
            status = "Vehicle Assigned"
        else:
            status = "Pending Assignment"

        recent_orders_data.append({
            "order_no": order.order_no,
            "customer_name": order.customer_name,
            "vehicle_number": (
                vehicle.vehicle_number
                if vehicle
                else "-"
            ),
            "total_rate": money(order.total_rate),
            "status": status,
            "created_at": order.created_at,
        })

    # ============================================================
    # ALERTS
    # ============================================================

    alerts = []

    if unassigned_orders:
        alerts.append({
            "type": "warning",
            "title": "Vehicle assignment pending",
            "count": unassigned_orders,
            "message": "Orders are waiting for vehicle assignment.",
        })

    if in_transit_orders:
        alerts.append({
            "type": "info",
            "title": "Vehicles in transit",
            "count": in_transit_orders,
            "message": "Vehicles are currently marked as departed.",
        })

    if pending_pod:
        alerts.append({
            "type": "warning",
            "title": "POD pending",
            "count": pending_pod,
            "message": "Delivered trips are waiting for POD.",
        })

    if approval_required:
        alerts.append({
            "type": "danger",
            "title": "Approval required",
            "count": approval_required,
            "message": "Vehicle transactions require management approval.",
        })

    if bank_pending:
        alerts.append({
            "type": "warning",
            "title": "Bank verification pending",
            "count": bank_pending,
            "message": "Vehicle bank details are not verified.",
        })

    # ============================================================
    # RETURN DATA
    # ============================================================

    return {

        # KPI
        "total_enquiries": total_enquiries,
        "total_orders": total_orders,
        "assigned_orders": assigned_orders,
        "unassigned_orders": unassigned_orders,

        "total_vehicles": total_vehicles,
        "vehicles_with_order": vehicles_with_order,
        "vehicles_without_order": vehicles_without_order,

        "in_transit_orders": in_transit_orders,
        "arrived_orders": arrived_orders,
        "delivered_orders": delivered_orders,
        "settled_orders": settled_orders,

        # Finance
        "total_billed": total_billed,
        "customer_received": customer_received,
        "customer_outstanding": customer_outstanding,

        "total_vehicle_freight": total_vehicle_freight,
        "vehicle_advance": vehicle_advance,
        "vehicle_balance": vehicle_balance,
        "vehicle_expenses": vehicle_expenses,
        "total_profit": total_profit,

        # Operations
        "approval_required": approval_required,
        "bank_pending": bank_pending,
        "pending_pod": pending_pod,

        # Conversion
        "conversion_rate": conversion_rate,

        # Charts
        "monthly_data": monthly_data,
        "enquiry_status_data": enquiry_status_data,

        # Pipeline
        "pipeline": pipeline,

        # Tables
        "recent_orders": recent_orders_data,

        # Alerts
        "alerts": alerts,

        # Misc
        "last_updated": timezone.now(),
    }