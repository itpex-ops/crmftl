from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.shortcuts import render ,redirect ,get_object_or_404
from authentications.decorators import allowed_roles
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
# Create your views here.
from vehicles.models import Vehicle, Tracking

@login_required
def assign_vehicle(request, id):
    order = get_object_or_404(Order, id=id)

    if request.method == "POST":

        freight = float(request.POST.get("freight_amount") or 0)
        advance = float(request.POST.get("advance") or 0)

        Vehicle.objects.create(
            order=order,
            vehicle_number=request.POST.get("vehicle_number"),
            driver_number=request.POST.get("driver_number"),
            owner_number=request.POST.get("owner_number"),
            source=request.POST.get("source"),
            freight_amount=freight,
            advance=advance,
            balance=freight - advance,  # 🔥 auto calc
            brokerage=request.POST.get("brokerage") or 0,
            loading=request.POST.get("loading") or 0,
            total_freight=request.POST.get("total_freight") or 0,
            upi_number=request.POST.get("upi_number"),
            account_name=request.POST.get("account_name"),
            account_number=request.POST.get("account_number"),
            ifsc=request.POST.get("ifsc"),
        )

        # ✅ CREATE TRACKING (if not exists)
        Tracking.objects.get_or_create(order=order)

        return redirect('order_list')

    return render(request, 'orders/assign_vehicle.html', {'order': order})

def view_orders(request):
    orders = Order.objects.order_by('-id')
    return render(request, 'vehicle/orders.html', {
        'orders': orders
    })

