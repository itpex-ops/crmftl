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
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from .models import Vehicle
from decimal import Decimal
from django.utils import timezone
from django.contrib import messages
import random

# Start Customers Payments #
 
@login_required
def customer_payment(request, enquiry_id):

    enquiry = get_object_or_404(
        Enquiry,
        id=enquiry_id
    )

    transactions = CustomerTransaction.objects.filter(
        enquiry=enquiry
    ).order_by("-id")

    if request.method == "POST":

        request.session["customer_payment"] = {
            "amount": request.POST.get("amount"),
            "account_type": request.POST.get("account_type"),
            "payment_against": request.POST.get("payment_against"),
            "payment_mode": request.POST.get("payment_mode"),
            "transaction_datetime": request.POST.get(
                "transaction_datetime"
            ),
            "remarks": request.POST.get("remarks"),
        }

        return redirect(
            "confirm_customer_payment",
            enquiry.id
        )

    return render(
        request,
        "accounts/customers/customer_payment.html",
        {
            "enquiry": enquiry,
            "transactions": transactions,
        }
    )

@login_required
def confirm_customer_payment(request, enquiry_id):

    enquiry = get_object_or_404(
        Enquiry,
        id=enquiry_id
    )

    payment_data = request.session.get(
        "customer_payment"
    )

    if not payment_data:

        messages.error(
            request,
            "Payment details not found."
        )

        return redirect(
            "customer_payment",
            enquiry.id
        )

    amount = Decimal(
        payment_data["amount"]
    )

    if request.method == "POST":

        ref_no = (
            f"CUST"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )

        CustomerTransaction.objects.create(
            enquiry=enquiry,
            amount=amount,
            account_type=payment_data["account_type"],
            payment_against=payment_data["payment_against"],
            payment_mode=payment_data["payment_mode"],
            transaction_datetime=payment_data[
                "transaction_datetime"
            ],
            reference_no=ref_no,
            remarks=payment_data["remarks"],
            created_by=request.user,
        )

        request.session["last_customer_ref"] = ref_no

        return redirect(
            "customer_payment_success",
            enquiry.id
        )

    return render(
        request,
        "accounts/customers/confirm_customer_payment.html",
        {
            "enquiry": enquiry,
            "payment": payment_data,
            "preview_ref": (
                f"CUST"
                f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
            ),
        }
    )

@login_required
def customer_payment_success(request, enquiry_id):

    enquiry = get_object_or_404(
        Enquiry,
        id=enquiry_id
    )

    ref_no = request.session.get(
        "last_customer_ref"
    )

    transaction = CustomerTransaction.objects.filter(
        enquiry=enquiry,
        reference_no=ref_no
    ).first()

    return render(
        request,
        "accounts/customers/customer_payment_success.html",
        {
            "enquiry": enquiry,
            "transaction": transaction,
        }
    )

def customer_accounts(request):
    enquiries = Enquiry.objects.all().order_by("-id")
    data = []
    for enquiry in enquiries:
        vehicle = Vehicle.objects.filter(enquiry=enquiry).first()
        total_received = CustomerTransaction.objects.filter(
            enquiry=enquiry
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
        advance_received = CustomerTransaction.objects.filter(
            enquiry=enquiry,
            payment_against="advance"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        balance_received = CustomerTransaction.objects.filter(
            enquiry=enquiry,
            payment_against="balance"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        total_freight = float(enquiry.approval_rate) if enquiry.approval_rate is not None else 0.0
        pending_amount = float(total_freight) - float(total_received)

        data.append({
            "enquiry_id": enquiry.id,
            "ftl_no": vehicle.ftl_no if vehicle else "",
            "enquiry_no": enquiry.enquiry_no,
            "customer": enquiry.customer_name,
            "contact": enquiry.customer_contact,
            "total_freight": total_freight,
            "received": total_received,
            "advance": advance_received,
            "balance": balance_received,
            "pending": pending_amount,
        })

    return render(
        request,
        "accounts/customer.html",
        {
            "data": data
        }
    )


# End Customer Payments #

def make_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    context = {
        "vehicle": vehicle,
    }
    return render(
        request,
        "accounts/make_payment.html",
         context
    )

def clean(self):

    if self.transaction_type == "advance":

        remaining = self.vehicle.remaining_balance_amount

        if remaining <= 0:
            raise ValidationError(
                "Advance not allowed. Balance is zero."
            )

        if self.amount > remaining:
            raise ValidationError(
                f"Advance cannot exceed {remaining}"
            )

def create_vehicle_payment(
    request,
    vehicle,
    transaction_type
):
    try:
        txn = VehicleTransaction(
            vehicle=vehicle,
            transaction_type=transaction_type,
            amount=request.POST.get("amount"),
            payment_mode=request.POST.get("payment_mode"),
            transaction_no=request.POST.get("transaction_no"),
            remarks=request.POST.get("remarks"),
            created_by=request.user
        )
        txn.full_clean()
        txn.save()

        # Create Ledger Entry
        LedgerEntry.objects.create(
            account_type="vehicle",
            vehicle=vehicle,
            order=vehicle.order,
            voucher_no=txn.transaction_no,
            debit=txn.amount,
            credit=0,
            remarks=f"{transaction_type.title()} Payment"
        )

        return True

    except ValidationError as e:

        messages.error(
            request,
            ", ".join(e.messages)
        )

        return False

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
            t.label = f"Balance {bal}"
            t.row_class = "row-balance"
        else:
            oth += 1
            t.label = f"OtherS {oth}"
            t.row_class = "row-other"
    context = {
        "vehicle": vehicle,
        "transactions": transactions,
    }
    return render(request, "accounts/vehicle_payments.html", context)

def pay_vehicle_advance(request, vehicle_id):
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )
    transactions = VehicleTransaction.objects.filter(
        vehicle=vehicle
    ).order_by("-id")

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
            t.label = f"Balance {bal}"
            t.row_class = "row-balance"

        else:
            oth += 1
            t.label = f"OtherS {oth}"
            t.row_class = "row-other"

    if request.method == "POST":
        amount = Decimal(
            request.POST.get("amount")
        )
        if amount > vehicle.remaining_balance_amount:
            messages.error(
                request,
                "Amount exceeds remaining balance."
            )
            return redirect(
                "pay_vehicle_advance",
                vehicle.id
            )
        request.session["advance_amount"] = str(amount)
        return redirect("confirm_vehicle_advance",vehicle.id)
    return render(
        request,"accounts/pay_vehicle_advance.html",
        {
            "vehicle": vehicle ,
            "transactions" :transactions
        }
    )

def confirm_vehicle_advance(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    amount = Decimal(
        request.session.get(
            "advance_amount",
            "0"
        )
    )

    if request.method == "POST":

        # Auto Generate Reference No
        utr = (
            f"ADV"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
            f"{random.randint(100,999)}"
        )

        txn = VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type="advance",
            amount=amount,
            payment_mode=request.POST.get(
                "payment_mode"
            ),
            transaction_no=utr,
            remarks="Advance transferred",
            created_by=request.user
        )

        LedgerEntry.objects.create(
            account_type="vehicle",
            vehicle=vehicle,
            order=vehicle.order,
            debit=amount,
            credit=0,
            voucher_no=utr,
            remarks="Advance Payment"
        )

        if hasattr(vehicle.order, "tracking"):

            tracking = vehicle.order.tracking

            tracking.advance_to_fleet = True

            tracking.save(
                update_fields=[
                    "advance_to_fleet"
                ]
            )

        request.session["last_utr"] = utr

        return redirect(
            "advance_success",
            vehicle.id
        )

    preview_utr = (
        f"ADV"
        f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    return render(
        request,
        "accounts/confirm_vehicle_advance.html",
        {
            "vehicle": vehicle,
            "amount": amount,
            "preview_utr": preview_utr,
        }
    )

@login_required
def confirm_vehicle_balance(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    amount = Decimal(
        request.session.get(
            "balance_amount",
            "0"
        )
    )

    if request.method == "POST":

        utr = (
            f"BAL"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
            f"{random.randint(100,999)}"
        )

        VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type="balance",
            amount=amount,
            payment_mode=request.POST.get(
                "payment_mode"
            ),
            transaction_no=utr,
            remarks="Balance transferred",
            created_by=request.user
        )

        LedgerEntry.objects.create(
            account_type="vehicle",
            vehicle=vehicle,
            order=vehicle.order,
            debit=amount,
            credit=0,
            voucher_no=utr,
            remarks="Balance Payment"
        )

        request.session["last_utr"] = utr

        return redirect(
            "balance_success",
            vehicle.id
        )

    preview_utr = (
        f"BAL"
        f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    return render(
        request,
        "accounts/confirm_vehicle_balance.html",
        {
            "vehicle": vehicle,
            "amount": amount,
            "preview_utr": preview_utr,
        }
    )

@login_required
def pay_vehicle_balance(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    transactions = VehicleTransaction.objects.filter(
        vehicle=vehicle
    ).order_by("-id")

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
            t.label = f"Balance {bal}"
            t.row_class = "row-balance"

        else:
            oth += 1
            t.label = f"Other {oth}"
            t.row_class = "row-other"

    if request.method == "POST":

        amount = Decimal(
            request.POST.get("amount")
        )

        if amount > vehicle.remaining_balance_amount:

            messages.error(
                request,
                "Amount exceeds remaining balance."
            )

            return redirect(
                "pay_vehicle_balance",
                vehicle.id
            )

        request.session["balance_amount"] = str(amount)

        return redirect(
            "confirm_vehicle_balance",
            vehicle.id
        )

    return render(
        request,
        "accounts/pay_vehicle_balance.html",
        {
            "vehicle": vehicle,
            "transactions": transactions
        }
    )

@login_required
def balance_success(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    utr = request.session.get(
        "last_utr",
        ""
    )

    return render(
        request,
        "accounts/balance_success.html",
        {
            "vehicle": vehicle,
            "utr": utr
        }
    )

def advance_success(
    request,
    vehicle_id
):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    return render(
        request,
        "accounts/advance_success.html",
        {
            "vehicle": vehicle,
            "utr": request.session.get(
                "last_utr"
            )
        }
    )

@login_required
def vehicle_accounts(request):
    orders = Vehicle.objects.select_related('order').all()
    data = []
    for o in orders:
        status = "Pending"
        if hasattr(o, 'tracking') and o.tracking:
            if o.tracking.settled:
                status = "Settled"
            elif o.tracking.transporter_paid:
                status = "Transporter Paid"
            elif o.tracking.customer_paid:
                status = "Customer Paid"
            elif o.tracking.delivered:
                status = "Delivered"
            elif o.tracking.fleet_departed:
                status = "In Transit"
            elif o.tracking.invoice_eway:
                status = "Invoice / Eway"
            elif o.tracking.lr_no_b:
                status = "LR Created"
            elif o.tracking.advance_to_fleet:
                status = "Fleet Advance"
            elif o.tracking.vehicle_document:
                status = "Documents Collected"
            elif o.tracking.vehicle_placed:
                status = "Vehicle Placed"
            else:
                status = "Pending Dispatch"

    vehicles = Vehicle.objects.select_related(
        "order",
        "order__tracking"
    ).order_by("-id")
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
            "total_advance_paid" : v.total_advance_paid,
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

    transactions = VehicleTransaction.objects.filter(
        vehicle=vehicle,
        transaction_type="others"
    ).order_by("-id")

    count = 0

    for t in transactions:
        count += 1
        t.label = f"Other {count}"

    if request.method == "POST":

        amount = Decimal(
            request.POST.get("amount")
        )

        request.session["other_amount"] = str(amount)

        request.session["other_type"] = request.POST.get(
            "transaction_type"
        )

        return redirect(
            "confirm_vehicle_other",
            vehicle.id
        )

    return render(
        request,
        "accounts/pay_vehicle_other.html",
        {
            "vehicle": vehicle,
            "transactions": transactions
        }
    )

@login_required
def confirm_vehicle_other(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    amount = Decimal(
        request.session.get(
            "other_amount",
            "0"
        )
    )

    if request.method == "POST":

        utr = (
            f"OTH"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
            f"{random.randint(100,999)}"
        )

        transaction_type = request.session.get(
            "other_type",
            "others"
                )

        VehicleTransaction.objects.create(
            vehicle=vehicle,
            transaction_type=transaction_type,
            amount=amount,
            payment_mode=request.POST.get(
                "payment_mode"
            ),
            transaction_no=utr,
            utr_no=utr,
            status="success",
            remarks=transaction_type.replace("_", " ").title(),
            created_by=request.user
        )

        LedgerEntry.objects.create(
            account_type="vehicle",
            vehicle=vehicle,
            order=vehicle.order,
            debit=amount,
            credit=0,
            voucher_no=utr,
            remarks="Other Payment"
        )

        request.session["last_utr"] = utr

        return redirect(
            "other_success",
            vehicle.id
        )

    preview_utr = (
        f"OTH"
        f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    return render(
        request,
        "accounts/confirm_vehicle_other.html",
        {
            "vehicle": vehicle,
            "amount": amount,
            "payment_type": request.session.get("other_type"),
            "preview_utr": preview_utr
        }
    )

@login_required
def other_success(request, vehicle_id):

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id
    )

    utr = request.session.get(
        "last_utr"
    )

    transaction = VehicleTransaction.objects.filter(
        transaction_no=utr
    ).first()

    return render(
        request,
        "accounts/other_success.html",
        {
            "vehicle": vehicle,
            "transaction": transaction
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

from django.db.models import Sum
from enquiries.models import Enquiry
from accounts.models import CustomerTransaction


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

from django.shortcuts import get_object_or_404, render
from decimal import Decimal

def vehicle_ledger(request, vehicle_id):
    vehicle = get_object_or_404(
        Vehicle.objects.select_related('order'),
        id=vehicle_id
    )

    ledger = []
    balance = Decimal('0.00')

    # Initial Freight Entry
    freight = Decimal(vehicle.freight_amount or 0)
    advance = Decimal(vehicle.advance or 0)

    balance += freight - advance

    ledger.append({
        "date": vehicle.created_at,
        "ftlno": vehicle.ftl_no,
        "particular": "Freight Entry",
        "debit": freight,
        "credit": advance,
        "balance": balance,
    })

    # Payment Entries
    transactions = VehicleTransaction.objects.filter(
        vehicle=vehicle
    ).order_by("date", "id")

    adv = bal = oth = 0

    for t in transactions:

        if t.transaction_type == "advance":
            adv += 1
            label = f"Advance {adv}"

        elif t.transaction_type == "balance":
            bal += 1
            label = f"Balance {bal}"

        else:
            oth += 1
            label = f"Others {oth}"

        amount = Decimal(t.amount or 0)

        # Payment received by vehicle owner => Credit
        current_balance = ledger[-1]['balance'] if ledger else 0

        ledger.append({
            "date": t.date,
            "ftlno": vehicle.ftl_no,
            "particular": label,
            "debit": 0,
            "credit": amount,
            "balance": balance,
        })

        t.label = label

    return render(
        request,
        "accounts/vehicle_ledger.html",
        {
            "vehicle": vehicle,
            "ledger": ledger,
            'current_balance': current_balance,
            "transactions": transactions,
        }
    )


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

# accounts/views.py

from django.shortcuts import render
from django.db.models import Sum
from accounts.models import (
    CustomerTransaction,
    VehicleTransaction,
    BankTransaction,
    Expense
)

def accounts_dashboard(request):

    customer_collection = CustomerTransaction.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    transporter_paid = VehicleTransaction.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    bank_credit = BankTransaction.objects.filter(
        txn_type='credit'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    bank_debit = BankTransaction.objects.filter(
        txn_type='debit'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    expenses = Expense.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {

        "customer_collection": customer_collection,
        "transporter_paid": transporter_paid,
        "bank_credit": bank_credit,
        "bank_debit": bank_debit,
        "expenses": expenses,

        "recent_customer_txns":
            CustomerTransaction.objects.order_by('-id')[:10],

        "recent_vehicle_txns":
            VehicleTransaction.objects.order_by('-id')[:10],

        "recent_expenses":
            Expense.objects.order_by('-id')[:10],
    }

    return render(
        request,
        "dashboards/accounts_dashboard.html",
        context
    )