from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from .models import ExCustomer
from .forms import ExCustomerForm
from django.contrib.auth.decorators import login_required

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

@login_required
def customer_create(request):

    if request.method == "POST":

        try:
            ExCustomer.objects.create(
                name=request.POST.get("name"),
                phone1=request.POST.get("phone1"),
                phone2=request.POST.get("phone2"),
                email=request.POST.get("email"),
                pan_number=(request.POST.get("pan_number") or "").upper(),
                gst_number=request.POST.get("gst_number"),
                state=request.POST.get("state"),
                state_code=request.POST.get("state_code"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                pincode=request.POST.get("pincode"),
                is_active=True if request.POST.get("is_active") == "True" else False,
                created_by=request.user
            )

            messages.success(request, "Customer created successfully!")
            return redirect("customer_create")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
    }

    return render(request, "Excustomers/customer_form.html", context)

def customer_update(request, pk):
    customer = get_object_or_404(ExCustomer, pk=pk)

    if request.method == "POST":
        form = ExCustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("customer_list")
    else:
        form = ExCustomerForm(instance=customer)

    return render(request, "Excustomers/customer_form.html", {
        "form": form,
        "title": "Edit Customer"
    })

def customer_delete(request, pk):
    customer = get_object_or_404(ExCustomer, pk=pk)

    if request.method == "POST":
        customer.delete()
        return redirect("customer_list")

    return render(request, "Excustomers/customer_delete.html", {
        "customer": customer
    })

