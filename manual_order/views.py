
from django.shortcuts import render, redirect
from .models import ManualOrder, Customer, Pricing, Payment,ExistingCustomerVehicle
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json

def generate_customer_code():
    last = Customer.objects.order_by('-id').first()
    if last:
        num = int(last.customer_code.replace("CUST", "")) + 1
    else:
        num = 1
    return f"CUST{num:04d}"

def generate_order_no():
    last = ManualOrder.objects.order_by('-id').first()
    if last:
        num = int(last.order_no.replace("ORD", "")) + 1
    else:
        num = 1
    return f"ORD{num:05d}"

@login_required
def create_ManualOrder(request):
    if request.method == "POST":
        # 👤 Customer
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

        # 🚚 Order
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

        # 💰 Pricing
        base = float(request.POST.get("base_freight") or 0)
        extra = float(request.POST.get("extra_charges") or 0)
        total = base + extra

        Pricing.objects.create(
            order=order,
            base_freight=base,
            extra_charges=extra,
            advance_amount=request.POST.get("advance_amount") or 0,
            balance_amount=request.POST.get("balance_amount") or 0,
            total_amount=total
        )

        # 💳 Payment
        Payment.objects.create(
            order=order,
            payment_mode=request.POST.get("payment_mode"),
            payment_status=request.POST.get("payment_status"),
            transaction_id=request.POST.get("transaction_id"),
            remarks=request.POST.get("payment_remarks")
        )

        messages.success(request, "✅ Order Created Successfully")
        return redirect("order_list")

    return render(request, "manual_order/form.html")

@login_required
def assign_vehicle_ajax(request, order_id):
    if request.method == "POST":
        data = json.loads(request.body)
        order = ManualOrder.objects.get(id=order_id)
        vehicle = ExistingCustomerVehicle.objects.create(
            order=order,
            vehicle_number=data.get("vehicle_number"),
            driver_number=data.get("driver_number"),
            owner_number=data.get("owner_number"),
            freight_amount=data.get("freight_amount") or 0,
            upi_app=data.get("upi_app"),
            upi_id=data.get("upi_id"),
        )
        return JsonResponse({
            "status": "success",
            "vehicle_number": vehicle.vehicle_number,
            "driver_number": vehicle.driver_number,
            "owner_number": vehicle.owner_number,
            "freight_amount": vehicle.freight_amount,
            "upi_app": vehicle.get_upi_app_display(),
            "upi_id": vehicle.upi_id,
        })

