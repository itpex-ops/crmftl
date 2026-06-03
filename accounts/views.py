from django.shortcuts import render, redirect
from .models import CustomerTransaction, VehicleTransaction, BankTransaction,LedgerEntry
from enquiries.models import Enquiry
from vehicles.models import Vehicle
from orders.models import Order
from django.db.models import Sum
from django.shortcuts import render,redirect
from django.shortcuts import render, get_object_or_404
from orders.models import Order
from vehicles.models import Vehicle
from enquiries.models import Enquiry
from datetime import timedelta
from django.contrib import messages
from .models import (
    CustomerTransaction,
    VehicleTransaction,
    BankTransaction,
    LedgerEntry
)
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import VehicleTransaction


def create_vehicle_payment(
    request,
    vehicle,
    transaction_type
):
    try:

        VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type=transaction_type,
            amount=request.POST.get("amount"),
            payment_mode=request.POST.get("payment_mode"),
            transaction_no=request.POST.get("transaction_no"),
            remarks=request.POST.get("remarks"),
            created_by=request.user
        )

        return True

    except Exception as e:

        messages.error(request, str(e))
        return False

@login_required
def vehicle_payments(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    transactions = VehicleTransaction.objects.filter(
        vehicle=vehicle
    ).order_by("id")

    adv = 0
    bal = 0
    oth = 0

    for t in transactions:

        if t.transaction_type == "advance":
            adv += 1
            t.label = f"Advance {adv}"
            t.row_class = "row-advance"

        elif t.transaction_type == "balance":
            bal += 1
            t.label = f"Balance{bal}"
            t.row_class = "row-balance"

        else:
            oth += 1
            t.label = f"OtherS{oth}"
            t.row_class = "row-other"

    context = {
        "vehicle": vehicle,
        "transactions": transactions,
    }

    return render(request, "accounts/vehicle_payments.html", context)

def pay_vehicle_advance(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":

        amount = Decimal(request.POST.get("amount") or 0)

        total_freight = Decimal(vehicle.total_freight or 0)
        total_advance = Decimal(vehicle.total_advance_paid or 0)

        balance = total_freight - total_advance

        # ❌ RULE 1: if balance is 0, no advance allowed
        if balance <= 0:
            messages.error(request, "Advance not allowed. Balance is already zero.")
            return redirect("vehicle_payments", vehicle.id)

        # ❌ RULE 2: advance cannot exceed remaining balance
        if amount > balance:
            messages.error(
                request,
                f"Advance cannot exceed balance ₹{balance}"
            )
            return redirect("vehicle_payments", vehicle.id)

        # SAVE PAYMENT
        VehicleTransaction.objects.create(
            vehicle=vehicle,
            amount=amount,
            transaction_type="advance",
            created_by=request.user
        )

        messages.success(request, "Advance payment added successfully.")
        return redirect("vehicle_payments", vehicle.id)

    return render(request, "accounts/pay_vehicle_advance.html", {"vehicle": vehicle})

@login_required
def pay_vehicle_balance(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":

        amount = Decimal(request.POST.get("amount") or 0)

        remaining = vehicle.remaining_balance_amount

        # 🔴 RULE 1: no balance if already cleared
        if remaining <= 0:
            messages.error(request, "Balance already completed. No payment allowed.")
            return redirect("pay_vehicle_balance", vehicle.id)

        # 🔴 RULE 2: cannot exceed remaining balance
        if amount > remaining:
            messages.error(
                request,
                f"Balance payment cannot exceed ₹{remaining}"
            )
            return redirect("pay_vehicle_balance", vehicle.id)

        VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type="balance",
            amount=amount,
            created_by=request.user
        )

        messages.success(request, "Balance payment added.")
        return redirect("pay_vehicle_balance", vehicle.id)

    balances = VehicleTransaction.objects.filter(
        vehicle=vehicle,
        transaction_type="balance"
    ).order_by("-id")

    return render(request, "accounts/pay_vehicle_balance.html", {
        "vehicle": vehicle,
        "balances": balances
    })
@login_required
def vehicle_accounts(request):

    vehicles = Vehicle.objects.select_related(
        "order",
        "order__tracking"
    )

    data = []

    for v in vehicles:

        data.append({
            "vehicle_id": v.id,
            "ftlno": v.ftl_no,
            "vehicle": v.vehicle_number,
            "freight": v.total_freight,
            "paid": v.total_paid,
            "advance" : v.advance,
            "balance": v.balance,
            "trip_completed": v.is_trip_completed,
            "payment_completed": v.is_payment_completed,
            "is_locked": v.is_locked,
            "is_overpaid": v.is_overpaid,
        })

    return render(
        request,
        "accounts/vehicle.html",
        {"data": data}
    )

@login_required
def pay_vehicle_other(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    if request.method == "POST":

        success = create_vehicle_payment(
            request,
            vehicle,
            request.POST.get(
                "transaction_type"
            )
        )

        if success:

            messages.success(
                request,
                "Expense added."
            )

            return redirect(
                "pay_vehicle_other",
                vehicle.id
            )

    others = VehicleTransaction.objects.filter(
        vehicle=vehicle
    ).exclude(
        transaction_type__in=[
            "advance",
            "balance"
        ]
    ).order_by("-id")

    return render(
        request,
        "accounts/pay_vehicle_other.html",
        {
            "vehicle": vehicle,
            "others": others
        }
    )

def edit_vehicle_account(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":

        freight = float(request.POST.get("freight_amount") or 0)
        advance = float(request.POST.get("advance") or 0)
        brokerage = float(request.POST.get("brokerage") or 0)
        loading_unloading = float(request.POST.get("loading_unloading") or 0)

        vehicle.freight_amount = freight
        vehicle.advance = advance
        vehicle.brokerage = brokerage
        vehicle.loading_unloading = loading_unloading

        # Correct calculation
        vehicle.balance = freight - advance

        if vehicle.balance < 0:
            vehicle.balance = 0

        vehicle.total_freight = freight + brokerage + loading_unloading

        vehicle.save()

        messages.success(request, "Vehicle account updated successfully.")
        return redirect("vehicle_accounts")

    return render(request, "accounts/edit_vehicle_account.html", {
        "vehicle": vehicle
    })

def customer_accounts(request):

    flts = Order.objects.select_related('enquiry').all().order_by('-id')

    data = []

    for o in flts:

        # get FTL No from vehicle app
        vehicle = Vehicle.objects.filter(order=o).first()

        credit_date = o.created_at.date() + timedelta(days=7)

        data.append({
            "order_id": o.id,
            "ftl_no": vehicle.ftl_no if vehicle else "",   # from vehicle app
            "enquiry_id": o.enquiry.id,
            "customer": o.customer_name,
            "contact": o.customer_contact,
            "total": o.total_rate or 0,
            "advance": o.advance or 0,
            "balance": o.balance or 0,
            "topay": o.topay or 0,
            "credit": o.credit or 0,
            "credit_date": credit_date,
        })

    return render(request, "accounts/customer.html", {"data": data})

def receive_customer_payment(request, enquiry_id):

    enquiry = get_object_or_404(Enquiry, id=enquiry_id)

    order = Order.objects.get(enquiry=enquiry)

    if request.method == "POST":

        amt = float(request.POST.get("amount"))

        # reduce balance
        order.balance = (order.balance or 0) - amt
        order.save()

        # ledger entry
        LedgerEntry.objects.create(
            enquiry=enquiry,
            account_type="Customer",
            credit=amt,
            remarks="Payment Received"
        )

        LedgerEntry.objects.create(
            enquiry=enquiry,
            account_type="Bank",
            credit=amt,
            remarks="Customer Payment Bank In"
        )

        return redirect("customer_accounts")

    return render(request, "accounts/receive_payment.html", {
        "enquiry": enquiry,
        "order": order
    })

def edit_customer_account(request, enquiry_id):

    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    order = Order.objects.get(enquiry=enquiry)

    if request.method == "POST":

        order.total_rate = request.POST.get("total")
        order.advance = request.POST.get("advance")
        order.balance = request.POST.get("balance")
        order.save()

        return redirect("customer_accounts")

    return render(request, "accounts/edit_customer.html", {
        "order": order,
        "enquiry": enquiry
    })

def customer_ledger(request, enquiry_id):

    enquiry = get_object_or_404(Enquiry, id=enquiry_id)

    ledger = LedgerEntry.objects.filter(
        enquiry=enquiry,
        account_type="Customer"
    ).order_by('date')

    return render(request, "accounts/customer_ledger.html", {
        "enquiry": enquiry,
        "ledger": ledger
    })

# 📒 VEHICLE LEDGER
def vehicle_ledger(request, vehicle_id):

    v = Vehicle.objects.select_related('order').get(id=vehicle_id)

    ledger = []

    balance = 0

    debit = float(v.freight_amount or 0)
    credit = float(v.advance or 0)

    balance += debit - credit

    ledger.append({
        "date": v.created_at,
        "ftlno": v.ftl_no,
        "debit": debit,
        "credit": credit,
        "balance": balance
    })

    return render(request, "accounts/vehicle_ledger.html", {
        "vehicle": v,
        "ledger": ledger,
        "balance": balance
    })

def dashboard(request):

    income = LedgerEntry.objects.filter(
        account_type="Income"
    ).aggregate(total=Sum('credit'))['total'] or 0

    expense = LedgerEntry.objects.filter(
        account_type="Expense"
    ).aggregate(total=Sum('debit'))['total'] or 0

    customer_due = LedgerEntry.objects.filter(
        account_type="Customer"
    ).aggregate(total=Sum('debit'))['total'] or 0

    bank_balance = LedgerEntry.objects.filter(
        account_type="Bank"
    ).aggregate(
        credit=Sum('credit'),
        debit=Sum('debit')
    )

    bank_balance = (bank_balance['credit'] or 0) - (bank_balance['debit'] or 0)

    profit = income - expense

    return render(request, "dashboard.html", {
        "income": income,
        "expense": expense,
        "profit": profit,
        "customer_due": customer_due,
        "bank_balance": bank_balance
    })

def profit_loss(request):

    income = LedgerEntry.objects.filter(account_type="Income").aggregate(Sum('credit'))['credit__sum'] or 0
    expense = LedgerEntry.objects.filter(account_type="Expense").aggregate(Sum('debit'))['debit__sum'] or 0

    return render(request, "reports/pl.html", {
        "income": income,
        "expense": expense,
        "profit": income - expense
    })
