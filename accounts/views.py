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

@login_required
def pay_vehicle_advance2(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":

        print("POST RECEIVED")
        print(request.POST)

        payment = VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type="advance",
            amount=request.POST.get("amount"),
            remarks=request.POST.get("remarks"),
            created_by=request.user
        )

        print("PAYMENT ID:", payment.id)

        return redirect("vehicle_payments", vehicle_id=vehicle.id)

    return render(
        request,
        "accounts/pay_vehicle_advance.html",
        {"vehicle": vehicle}
    )
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404

@login_required
def vehicle_payments(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    advances = VehicleTransaction.objects.filter(
        vehicle=vehicle,
        transaction_type='advance'
    )

    balances = VehicleTransaction.objects.filter(
        vehicle=vehicle,
        transaction_type='balance'
    )

    total_advance = advances.aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_balance = balances.aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'vehicle': vehicle,
        'advances': advances.order_by('-id'),
        'balances': balances.order_by('-id'),
        'total_advance': total_advance,
        'total_balance': total_balance,
    }

    return render(
        request,
        'accounts/vehicle_payments.html',
        context
    )
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from vehicles.models import Vehicle
from accounts.models import VehicleTransaction, LedgerEntry


@login_required
def pay_vehicle_advance(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":

        try:
            amount = request.POST.get("amount")
            payment_mode = request.POST.get("payment_mode")
            transaction_no = request.POST.get("transaction_no")
            remarks = request.POST.get("remarks")

            print("AMOUNT =", amount)
            print("MODE =", payment_mode)

            payment = VehicleTransaction.objects.create(
                vehicle=vehicle,
                transaction_type="advance",
                payment_mode=payment_mode,
                transaction_no=transaction_no,
                amount=amount,
                remarks=remarks,
                created_by=request.user
            )

            print("PAYMENT SAVED:", payment.id)

            LedgerEntry.objects.create(
                account_type="vehicle",
                vehicle=vehicle,
                credit=float(amount),
                remarks=f"Advance Payment - {payment_mode}"
            )

            print("LEDGER SAVED")

            messages.success(
                request,
                "Advance payment added successfully."
            )

            return redirect(
                "vehicle_payments",
                vehicle_id=vehicle.id
            )

        except Exception as e:
            print("ERROR:", e)
            raise

    return render(
        request,
        "accounts/pay_vehicle_advance.html",
        {"vehicle": vehicle}
    )
def accounts_dashboard(request):

    customer_total = CustomerTransaction.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    vehicle_expense = VehicleTransaction.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    bank_credit = BankTransaction.objects.filter(
        txn_type='credit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    bank_debit = BankTransaction.objects.filter(
        txn_type='debit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    ledger_credit = LedgerEntry.objects.aggregate(
        total=Sum('credit')
    )['total'] or 0

    ledger_debit = LedgerEntry.objects.aggregate(
        total=Sum('debit')
    )['total'] or 0

    recent_bank_txns = BankTransaction.objects.order_by('-date')[:10]

    context = {
        'customer_total': customer_total,
        'vehicle_expense': vehicle_expense,
        'bank_credit': bank_credit,
        'bank_debit': bank_debit,
        'ledger_credit': ledger_credit,
        'ledger_debit': ledger_debit,
        'recent_bank_txns': recent_bank_txns,
    }

    return render(request, 'dashboards/accounts_dashboard.html', context)

@login_required
def pay_vehicle_balance(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    if request.method == "POST":

        amount = request.POST.get("amount")
        payment_mode = request.POST.get("payment_mode")
        transaction_no = request.POST.get("transaction_no")
        remarks = request.POST.get("remarks")

        VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type="balance",
            payment_mode=payment_mode,
            transaction_no=transaction_no,
            amount=amount,
            remarks=remarks,
            created_by=request.user
        )

        LedgerEntry.objects.create(
            account_type="vehicle",
            vehicle=vehicle,
            credit=float(amount),
            remarks=f"Balance Payment - {payment_mode}"
        )

        messages.success(
            request,
            "Balance payment added successfully."
        )

        return redirect(
            "vehicle_payments",
            vehicle_id=vehicle.id
        )

    return render(
        request,
        "accounts/pay_vehicle_balance.html",
        {
            "vehicle": vehicle
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

def pay_vehicle_advance1(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":

        amount = float(request.POST.get("amount", 0))
        mode = request.POST.get("mode")
        remarks = request.POST.get("remarks")

        # Update Vehicle Advance
        current_advance = float(vehicle.advance or 0)
        current_balance = float(vehicle.balance or 0)

        vehicle.advance = current_advance + amount
        vehicle.balance = current_balance - amount

        if vehicle.balance < 0:
            vehicle.balance = 0

        vehicle.save()

        # Vehicle Ledger Entry
        LedgerEntry.objects.create(
            account_type="Vehicle",
            vehicle=vehicle,
            debit=amount,
            credit=0,
            remarks=f"Advance Paid - {mode} - {remarks}"
        )

        # Bank Ledger Entry
        LedgerEntry.objects.create(
            account_type="Bank",
            vehicle=vehicle,
            debit=amount,
            credit=0,
            remarks=f"Vehicle Advance Payment - {vehicle.vehicle_number}"
        )

        messages.success(request, "Vehicle advance paid successfully.")
        return redirect("vehicle_accounts")

    return render(request, "accounts/pay_vehicle_advance.html", {
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
# 🚚 VEHICLE LIST
def vehicle_accounts(request):

    vehicles = Vehicle.objects.select_related('order').all()

    data = []

    for v in vehicles:
        data.append({
            "vehicle_id": v.id,
            "ftlno" : v.ftl_no,
            "vehicle": v.vehicle_number,
            "order_no": v.order_no,
            "freight": float(v.freight_amount or 0),
            "advance": float(v.advance or 0),
            "balance": float(v.balance or 0),
            "total_freight": float(v.total_freight or 0),
        })

    return render(request, "accounts/vehicle.html", {"data": data})

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

# 🏦 BANK (simple placeholder)
def bank_accounts(request):
    return render(request, "accounts/bank.html")

def accounts_dashboard(request):

    customer_in = CustomerTransaction.objects.filter(
        transaction_type='invoice'
    ).aggregate(total=Sum('amount'))['total'] or 0

    customer_received = CustomerTransaction.objects.filter(
        transaction_type='payment'
    ).aggregate(total=Sum('amount'))['total'] or 0

    vehicle_expense = VehicleTransaction.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    bank_credit = BankTransaction.objects.filter(
        txn_type='credit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    bank_debit = BankTransaction.objects.filter(
        txn_type='debit'
    ).aggregate(total=Sum('amount'))['total'] or 0

    bank_balance = bank_credit - bank_debit

    context = {
        "customer_in": customer_in,
        "customer_received": customer_received,
        "pending": customer_in - customer_received,
        "vehicle_expense": vehicle_expense,
        "bank_balance": bank_balance,
    }

    return render(request, "accounts/dashboard.html", context)

def add_customer_transaction(request):
    if request.method == "POST":

        txn = CustomerTransaction.objects.create(
            enquiry_id=request.POST.get("enquiry"),
            transaction_type=request.POST.get("type"),
            amount=request.POST.get("amount"),
            payment_mode=request.POST.get("mode"),
            remarks=request.POST.get("remarks"),
            created_by=request.user
        )

        # ✅ AUTO SYNC TO BANK
        if txn.payment_mode == "bank":

            if txn.transaction_type in ["payment", "advance"]:
                BankTransaction.objects.create(
                    bank_name="Default Bank",
                    txn_type="credit",
                    amount=txn.amount,
                    party_name=txn.enquiry.customer_name,
                    purpose="Customer Payment",
                    remarks=txn.remarks
                )

    return redirect('customer_accounts')

def add_vehicle_transaction(request):
    if request.method == "POST":

        txn = VehicleTransaction.objects.create(
            vehicle_id=request.POST.get("vehicle"),
            transaction_type=request.POST.get("type"),
            amount=request.POST.get("amount"),
            payment_mode=request.POST.get("mode"),
            remarks=request.POST.get("remarks"),
            created_by=request.user
        )

        # ✅ AUTO SYNC TO BANK
        if txn.payment_mode == "bank":

            BankTransaction.objects.create(
                bank_name="Default Bank",
                txn_type="debit",
                amount=txn.amount,
                party_name=txn.vehicle.vehicle_no,
                purpose=txn.transaction_type,
                remarks=txn.remarks
            )

    return redirect('vehicle_accounts')

def add_bank_transaction(request):
    if request.method == "POST":
        BankTransaction.objects.create(
            bank_name=request.POST.get("bank_name"),
            txn_type=request.POST.get("type"),
            amount=request.POST.get("amount"),
            reference_no=request.POST.get("ref"),
            party_name=request.POST.get("party"),
            purpose=request.POST.get("purpose"),
            remarks=request.POST.get("remarks"),
        )
    return redirect('bank_accounts')

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
