# dashboards/views.py

from django.shortcuts import render
from django.db.models import Sum 
from django.utils import timezone

from customers.models import ExCustomer
from enquiries.models import Enquiry
from orders.models import Order
from vehicles.models import Vehicle, Tracking

from accounts.models import (
    CustomerTransaction,
    VehicleTransaction,
    BankTransaction,
    Expense
)
def management_dashboard(request):

    today = timezone.now().date()

    context = {

        # CUSTOMERS
        "total_customers":
            ExCustomer.objects.count(),

        "active_customers":
            ExCustomer.objects.filter(
                is_active=True
            ).count(),

        # ENQUIRIES
        "total_enquiries":
            Enquiry.objects.count(),

        "today_enquiries":
            Enquiry.objects.filter(
                created_at__date=today
            ).count(),

        "confirmed_enquiries":
            Enquiry.objects.filter(
                status="confirmed"
            ).count(),

        "converted_orders":
            Enquiry.objects.filter(
                is_converted_to_order=True
            ).count(),

        # ORDERS
        "total_orders":
            Order.objects.count(),

        "today_orders":
            Order.objects.filter(
                created_at__date=today
            ).count(),

        "vehicle_pending":
            Order.objects.filter(
                vehicle_place_date__isnull=True
            ).count(),

        "vehicle_placed":
            Order.objects.filter(
                vehicle_place_date__isnull=False
            ).count(),

        # VEHICLES
        "total_vehicles":
            Vehicle.objects.count(),

        "in_transit":
            Tracking.objects.filter(
                fleet_departed=True,
                delivered=False
            ).count(),

        "delivered":
            Tracking.objects.filter(
                delivered=True
            ).count(),

        "pod_pending":
            Tracking.objects.filter(
                delivered=True,
                pod_received=False
            ).count(),

        "settled":
            Tracking.objects.filter(
                settled=True
            ).count(),

        # FINANCE
        "customer_collection":
            CustomerTransaction.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,

        "transporter_payment":
            VehicleTransaction.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,

        "bank_credit":
            BankTransaction.objects.filter(
                txn_type='credit'
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0,

        "expenses":
            Expense.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,
    }

    return render(
        request,
        "dashboards/management_dashboard.html",
        context
    )

def customer_dashboard(request):
    today = timezone.now()
    context = {
        "total_customers": ExCustomer.objects.count(),
        "active_customers": ExCustomer.objects.filter(is_active=True).count(),
        "inactive_customers": ExCustomer.objects.filter(is_active=False).count(),
        "new_this_month": ExCustomer.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count(),
        "recent_customers": ExCustomer.objects.order_by('-id')[:10]
    }
    return render(
        request,
        "dashboards/customer_dashboard.html",
        context
    )
