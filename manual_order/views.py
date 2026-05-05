from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import (
    ManualOrder, Customer, Pricing, Payment
)

# 🔢 CUSTOMER CODE GENERATOR
def generate_customer_code():
    last = Customer.objects.order_by("-id").first()
    if last and last.customer_code:
        try:
            num = int(last.customer_code.replace("CUST", ""))
        except:
            num = 0
    else:
        num = 0
    return f"CUST{num + 1:04d}"


# 🔢 ORDER NO GENERATOR
def generate_order_no():
    last = ManualOrder.objects.order_by("-id").first()
    if last and last.order_no:
        try:
            num = int(last.order_no.replace("ORD", ""))
        except:
            num = 0
    else:
        num = 0
    return f"ORD{num + 1:05d}"


@login_required
def manual_order_create(request):
    
    vehicle_types = ManualOrder._meta.get_field("vehicle_type").choices
    if request.method == "POST":

        with transaction.atomic():

            # 👤 CUSTOMER
            name = request.POST.get("customer_name")
            phone = request.POST.get("customer_contact")
            email = request.POST.get("email")

            customer, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "email": email,
                    "customer_code": generate_customer_code()
                }
            )

            # 🚚 ORDER
            order = ManualOrder.objects.create(
                order_no=generate_order_no(),
                customer=customer,

                customer_name=name,
                customer_contact=phone,
                email=email,

                origin=request.POST.get("origin"),
                destination=request.POST.get("destination"),

                vehicle_type=request.POST.get("vehicle_type"),
                vehicle_description=request.POST.get("vehicle_description"),

                material=request.POST.get("material"),
                pieces=request.POST.get("pieces") or 0,
                tonnage=request.POST.get("tonnage") or 0,

                expected_rate=request.POST.get("expected_rate") or 0,

                created_by=request.user
            )

            # 💰 PRICING
            base = float(request.POST.get("base_freight") or 0)
            extra = float(request.POST.get("extra_charges") or 0)
            advance = float(request.POST.get("advance_amount") or 0)

            total = base + extra

            Pricing.objects.create(
                order=order,
                base_freight=base,
                extra_charges=extra,
                advance_amount=advance,
                balance_amount=total - advance,
                total_amount=total
            )

            # 💳 PAYMENT
            Payment.objects.create(
                order=order,
                payment_mode=request.POST.get("payment_mode"),
                payment_status=request.POST.get("payment_status"),
                transaction_id=request.POST.get("transaction_id"),
                remarks=request.POST.get("payment_remarks")
            )

            messages.success(request, f"Order {order.order_no} created successfully")
            return redirect("manual_order_create")

    return render(request, "manual_order/form.html",{ "vehicle_types": vehicle_types})