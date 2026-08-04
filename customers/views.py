from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from .models import ExCustomer
from .forms import ExCustomerForm
from django.contrib.auth.decorators import login_required
from customers.models import ExCustomer
from django.utils import timezone
from datetime import timedelta

def customer_list(request):
    query = request.GET.get("q", "")

    customers = ExCustomer.objects.all()

    if query:
        customers = customers.filter(
            Q(customer_code__icontains=query) |
            Q(name__icontains=query) |
            Q(phone1__icontains=query) |
            Q(phone2__icontains=query) |
            Q(gst_number__icontains=query)
        )

    context = {
        "customers": customers,
        "query": query
    }
    return render(request, "Excustomers/customer_list.html", context)
import re
from django.core.exceptions import ValidationError

def validate_pan(pan):
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
    if not re.match(pattern, pan):
        raise ValidationError("Invalid PAN format")

from django.db.models import Max

@login_required
def customer_create(request):

    last_id = ExCustomer.objects.aggregate(
        max_id=Max("id")
    )["max_id"] or 0

    next_customer_code = f"C{last_id + 1:05d}"

    if request.method == "POST":
        try:
            customer = ExCustomer.objects.create(
                name=request.POST.get("name"),
                phone1=request.POST.get("phone1"),
                phone2=request.POST.get("phone2"),
                email=request.POST.get("email"),
                pan_number=(request.POST.get("pan_number") or "").upper(),
                gst_number=request.POST.get("gst_number"),
                state=request.POST.get("state"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                pincode=request.POST.get("pincode"),
                is_active=request.POST.get("is_active") == "True",
                created_by=request.user.username
            )

            messages.success(
                request,
                f"Customer created successfully! Code: {customer.customer_code}"
            )

            return redirect("customer_create")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        "next_customer_code": next_customer_code
    }

    return render(
        request,
        "Excustomers/customer_form.html",
        context
    )

def customer_update(request, pk):

    customer = get_object_or_404(ExCustomer, pk=pk)

    if request.method == "POST":

        customer.name = request.POST.get("name")
        customer.phone1 = request.POST.get("phone1")
        customer.phone2 = request.POST.get("phone2")
        customer.email = request.POST.get("email")

        customer.gst_number = request.POST.get("gst_number")
        customer.pan_number = request.POST.get("pan_number")
        customer.state = request.POST.get("state")

        customer.address = request.POST.get("address")
        customer.city = request.POST.get("city")
        customer.pincode = request.POST.get("pincode")

        customer.is_active = (
            request.POST.get("is_active") == "True"
        )

        customer.save()

        messages.success(request, "Customer updated successfully.")
        return redirect("customer_list")

    return render(
        request,
        "Excustomers/customer_edit.html",
        {
            "customer": customer,
            "title": "Edit Customer",
        },
    )

def customer_delete(request, pk):
    customer = get_object_or_404(ExCustomer, pk=pk)

    if request.method == "POST":
        customer.delete()
        return redirect("customer_list")

    return render(request, "Excustomers/customer_delete.html", {
        "customer": customer
    })

