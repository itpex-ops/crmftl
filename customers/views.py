from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import ExCustomer
from .forms import ExCustomerForm


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


def customer_create(request):
    if request.method == "POST":
        form = ExCustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("customer_list")
    else:
        form = ExCustomerForm()

    return render(request, "Excustomers/customer_form.html", {
        "form": form,
        "title": "Create Customer"
    })


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