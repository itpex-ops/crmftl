from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CustomerForm, OrderForm, VehiclePaymentForm, CustomerPaymentForm
from .models import Order, VehiclePayment, CustomerPayment

def onepageorder_list(request):
    q=request.GET.get('q','').strip()
    orders=Order.objects.select_related('customer').prefetch_related('vehicle_payments','customer_payments')
    if q: orders=orders.filter(Q(trip_number__icontains=q)|Q(customer__name__icontains=q)|Q(vehicle_number__icontains=q)|Q(origin__icontains=q)|Q(destination__icontains=q))
    return render(request,'onepageorders/order_list.html',{'orders':orders,'q':q})

def onepageorder_create(request):
    if request.method=='POST':
        customer_form=CustomerForm(request.POST); order_form=OrderForm(request.POST)
        if customer_form.is_valid() and order_form.is_valid():
            customer=customer_form.save(); order=order_form.save(commit=False); order.customer=customer; order.save()
            messages.success(request,f'{order.trip_number} created successfully.'); return redirect('onepageorder_detail',pk=order.pk)
    else: customer_form=CustomerForm(); order_form=OrderForm()
    return render(request,'onepageorders/order_form.html',{'customer_form':customer_form,'order_form':order_form,'title':'Create Order'})

def onepageorder_detail(request,pk):
    order=get_object_or_404(Order.objects.prefetch_related('vehicle_payments','customer_payments'),pk=pk)
    return render(request,'onepageorders/order_detail.html',{'order':order})

def onepageorder_edit(request,pk):
    order=get_object_or_404(Order,pk=pk)
    if request.method=='POST':
        form=OrderForm(request.POST,instance=order)
        if form.is_valid(): form.save(); messages.success(request,'Order updated.'); return redirect('onepageorder_detail',pk=pk)
    else: form=OrderForm(instance=order)
    return render(request,'onepageorders/order_edit.html',{'form':form,'order':order})

def vehicle_payments(request):
    payments=VehiclePayment.objects.select_related('order').order_by('-paid_at')
    form=VehiclePaymentForm(request.POST or None)
    if request.method=='POST' and form.is_valid(): form.save(); messages.success(request,'Vehicle payment saved.'); return redirect('vehicle_payments')
    return render(request,'onepageorders/vehicle_payments.html',{'payments':payments,'form':form})

def customer_payments(request):
    payments=CustomerPayment.objects.select_related('order','order__customer').order_by('-received_at')
    form=CustomerPaymentForm(request.POST or None)
    if request.method=='POST' and form.is_valid(): form.save(); messages.success(request,'Customer payment saved.'); return redirect('customer_payments')
    return render(request,'onepageorders/customer_payments.html',{'payments':payments,'form':form})

def admin_margin(request):
    orders=Order.objects.select_related('customer').prefetch_related('vehicle_payments','customer_payments')
    return render(request,'onepageorders/admin_margin.html',{'orders':orders})
