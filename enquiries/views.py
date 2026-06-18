# Create views here.
from django.shortcuts import render ,redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Enquiry,Notification ,VEHICLE_TYPES
from orders.models import Order
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
import json
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db.models import Q
User = get_user_model()
from django.http import JsonResponse
from customers.models import ExCustomer

@login_required
def edit_enquiry(request, id):
    enquiry = get_object_or_404(
        Enquiry,
        id=id
    )
    if request.method == 'POST':
        enquiry.expected_rate = request.POST.get('expected_rate') or None
        enquiry.approval_rate = request.POST.get('approval_rate') or None
        enquiry.status = request.POST.get('status')
        enquiry.pitch1 = request.POST.get('pitch1')
        enquiry.pitch2 = request.POST.get('pitch2')
        enquiry.pitch3 = request.POST.get('pitch3')
        enquiry.cancel_reason = request.POST.get('cancel_reason')
        enquiry.save()
        messages.success(request,'Enquiry updated successfully')
        if enquiry.approval_rate :
            messages.success(request,'Rendering to Pricing Page')
            return redirect("pricing_page",enquiry_id=enquiry.id)
        return redirect('enquiry_list')
    context = {
        'enquiry': enquiry,
        'is_superadmin': request.user.is_superuser,
    }
    return render(
        request,'enquiry/edit.html',context)

def send_notification(user, enquiry, message):

    if user:
        Notification.objects.create(
            user=user,
            enquiry=enquiry,
            message=message
        )

@login_required
def notifications(request):

    notes = (
        Notification.objects
        .filter(user=request.user)
        .select_related('enquiry')
        .order_by('-created_at')
    )

    # Mark unread notifications as read
    notes.filter(is_read=False).update(is_read=True)

    notification_count = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False
        )
        .count()
    )

    return render(
        request,
        'enquiry/notifications.html',
        {
            'notes': notes,
            'notification_count': notification_count
        }
    )

@login_required
def confirm_enquiry(request, enquiry_id):

    enquiry = get_object_or_404(Enquiry, id=enquiry_id)

    # Update status
    enquiry.status = 'confirmed'
    enquiry.save()

    # ------------------------------
    # Notification for Admin
    # ------------------------------

    send_notification(
        request.user,
        enquiry,
        f"You confirmed enquiry {enquiry.enquiry_no}"
    )

    # ------------------------------
    # Notification for Sales/User
    # ------------------------------

    # Replace created_by with your actual field name
    if enquiry.request.user:

        send_notification(
            enquiry.request.user,
            enquiry,
            f"Your enquiry {enquiry.enquiry_no} was confirmed by Admin"
        )

    messages.success(request, 'Enquiry confirmed successfully.')

    return redirect('enquiry_list', enquiry_id=enquiry.id)

@login_required
def create_enquiry(request):
    # search_value = request.GET.get("customer_code", "").strip()
    # if search_value:
    #     customers = ExCustomer.objects.filter(
    #         Q(customer_code__iexact=search_value) |
    #         Q(phone1__icontains=search_value) |
    #         Q(phone2__icontains=search_value) |
    #         Q(name__icontains=search_value) |
    #         Q(gst_number__icontains=search_value) |
    #         Q(pan_number__icontains=search_value)
    #     ).first()
    customers = ExCustomer.objects.all().order_by("customer_code")

    vehicle_types = Enquiry._meta.get_field("vehicle_type").choices
    if request.method == "POST":
        customer_name = request.POST.get("customer_name") or None
        customer_contact = request.POST.get("customer_contact") or None
        email = request.POST.get("email") or None
        lead_source = request.POST.get("lead_source") or None
        reference_name = request.POST.get("reference_name") or None

        # =========================
        # VEHICLE
        # =========================

        pickups = request.POST.get("pickups") or 1
        deliveries = request.POST.get("deliveries") or 1

        vehicle_type = request.POST.get("vehicle_type") or None
        vehicle_description = request.POST.get("vehicle_description") or None

        # HTML name="kms"
        kms = request.POST.get("kms") or None

        # =========================
        # MATERIAL
        # =========================

        material = request.POST.get("material") or None
        pieces = request.POST.get("pieces") or None
        tonnage = request.POST.get("tonnage") or None
        kg = request.POST.get("kg") or None

        # =========================
        # DIMENSIONS
        # =========================

        length = float(request.POST.get("length") or 0)
        breadth = float(request.POST.get("breadth") or 0)
        height = float(request.POST.get("height") or 0)

        dimension_unit = request.POST.get("dimension_unit") or ""

        # =========================
        # VOLUMETRIC CALCULATION
        # =========================

        volume = length * breadth * height

        volumetric_weight = 0

        if volume > 0:

            if dimension_unit == "cm":

                volumetric_weight = volume / 4500

            elif dimension_unit == "inch":

                volumetric_weight = volume / 274.6

            elif dimension_unit == "feet":

                volumetric_weight = volume / 0.1589

            elif dimension_unit == "meter":

                volumetric_weight = volume / 0.0045

        # =========================
        # ROUND VALUES
        # =========================

        volume = round(volume, 2)

        volumetric_weight = round(volumetric_weight, 2)

        # =========================
        # RATE
        # =========================

        expected_rate = request.POST.get("expected_rate") or None

        # =========================
        # ROUTES
        # =========================

        origins = request.POST.getlist("origin[]")
        origin_pins = request.POST.getlist("origin_pin[]")
        destinations = request.POST.getlist("destination[]")
        destination_pins = request.POST.getlist("destination_pin[]")
        routes = []
        max_rows = max(
            len(origins),
            len(origin_pins),
            len(destinations),
            len(destination_pins)
        )
        for i in range(max_rows):
            route = {
                "origin": origins[i] if i < len(origins) else "",
                "origin_pin": origin_pins[i] if i < len(origin_pins) else "",
                "destination": destinations[i] if i < len(destinations) else "",
                "destination_pin": destination_pins[i] if i < len(destination_pins) else "",
            }
            if (
                route["origin"] or
                route["origin_pin"] or
                route["destination"] or
                route["destination_pin"]
            ):
                routes.append(route)
        approval_rate = request.POST.get('approval_rate') or None
        enquiry = Enquiry.objects.create(

            customer_name=customer_name,
            customer_contact=customer_contact,
            email=email,

            lead_source=lead_source,
            reference_name=reference_name,

            pickups=pickups,
            deliveries=deliveries,

            vehicle_type=vehicle_type,
            vehicle_description=vehicle_description,
            kms=kms,

            material=material,

            pieces=int(pieces) if pieces else None,
            tonnage=float(tonnage) if tonnage else None,
            kg=float(kg) if kg else None,

            dimension_unit=dimension_unit,

            # ORIGINAL VALUES
            length=length,
            breadth=breadth,
            height=height,

            # CALCULATED VALUES
            volume=volume,
            volumetric_weight=volumetric_weight,

            expected_rate=float(expected_rate) if expected_rate else None,
            approval_rate = float(approval_rate) if approval_rate else None,

            status='waiting for rate approval',

            routes=routes,

            created_by=request.user
        )
        
        messages.success(
            request,
            f"{enquiry.enquiry_no} created successfully!"
        )
        if approval_rate :
             return redirect(
                "pricing_page",
                enquiry_id=enquiry.id
            )


        return redirect("create_enquiry")
        
    return render(
        request,
        "enquiry/create.html",
        {
            "vehicle_types": vehicle_types,
            #"search_value": search_value,
            "customers": customers,
        }
    )

@login_required
def enquiry_list(request):
    user = request.user
    is_admin = user.role == 'admin'
    is_sales = user.role == 'sales'
    is_superadmin = user.role == 'superadmin'
    if is_admin:
        base_qs = Enquiry.objects.filter(
            is_converted_to_order=False,
         status__in=[
             'waiting for rate approval',
                'pending_pitch1',
                'pending_pitch2',
                'pending_pitch3',
                
            ])
    else:
        base_qs = Enquiry.objects.filter(
            is_converted_to_order=False,
            status__in=[
                'waiting for rate approval',
                'pending_pitch1',
                'pending_pitch2',
                'pending_pitch3',
            ]
    )
    total_count = base_qs.count()
    confirmed_count = base_qs.filter(status='confirmed').count()
    pending_count = base_qs.filter(
        status__in=[
            'pending_pitch1',
            'pending_pitch2',
            'pending_pitch3'
        ]).count()
    cancelled_count = base_qs.filter(status='cancelled').count()
    #pitch_remarks =  base_qs.filter()
    enquiries = base_qs.order_by('-id')

    for e in enquiries:
        e.has_pickups = any(
            r.get("origin") or r.get("origin_pin")
            for r in e.routes
        )

        e.has_drops = any(
            r.get("destination") or r.get("destination_pin")
            for r in e.routes
        )
    return render(request, 'enquiry/list.html', {
        'enquiries': enquiries,
        'total_count': total_count,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'is_admin': is_admin,
        'is_sales': is_sales,
        'is_superadmin': is_superadmin,
        #"pitch_remarks":pitch_remarks
    })

@login_required
def update_enquiry_status(request, id, action):
    enquiry = get_object_or_404(Enquiry, id=id)
    if request.method == "POST":
        # =====================================
        # CONFIRM
        # =====================================
        if action == "confirm":
            enquiry.status = "pitch3"
            enquiry.approval_rate = request.POST.get(
                "approve_rate"
            ) or 0
            enquiry.save()
            order, created = Order.objects.get_or_create(
                enquiry=enquiry,
                defaults={
                    "finalized_rate": enquiry.approval_rate,
                    "customer_name": enquiry.customer_name,
                    "customer_contact": enquiry.customer_contact,
                    "routes": enquiry.routes,
                    "vehicle_type": enquiry.vehicle_type,
                    "created_by": request.user,
                }
            )

            if not created:
                order.finalized_rate = enquiry.approval_rate
                order.save()

            if enquiry.created_by:
                Notification.objects.create(
                    user=enquiry.created_by,
                    enquiry=enquiry,
                    message=(
                        f"Your enquiry "
                        f"{enquiry.enquiry_no} "
                        f"has been confirmed"
                    )
                )

            messages.success(
                request,
                "Enquiry confirmed successfully."
            )

            return redirect(
                "pricing_page",
                enquiry_id=enquiry.id
            )

        # =====================================
        # DISAGREE
        # =====================================
        elif action == "disagree":

            enquiry.disagree_rate = request.POST.get(
                "disagree_rate"
            )

            enquiry.disagree_reason = request.POST.get(
                "disagree_reason",
                ""
            )
            #enquiry.status = "waiting for rate approval"
            enquiry.save()
            if enquiry.created_by:
                Notification.objects.create(
                    user=enquiry.created_by,
                    enquiry=enquiry,
                    message=(
                        f"Disagreement raised for "
                        f"{enquiry.enquiry_no}. "
                        f"Expected Rate ₹{enquiry.expected_rate} | "
                        f"Disagree Rate ₹{enquiry.disagree_rate}"
                    )
                )

            messages.warning(
                request,
                "Disagreement submitted successfully."
            )
            return redirect("enquiry_list")

        # =====================================
        # CANCEL
        # =====================================
        elif action == "cancel":

            enquiry.status = "cancelled"

            enquiry.cancel_reason = request.POST.get(
                "cancel_reason",
                ""
            )

            enquiry.save()

            if enquiry.created_by:
                Notification.objects.create(
                    user=enquiry.created_by,
                    enquiry=enquiry,
                    message=(
                        f"Your enquiry "
                        f"{enquiry.enquiry_no} "
                        f"has been cancelled"
                    )
                )

            messages.error(
                request,
                "Enquiry cancelled."
            )

            return redirect("enquiry_list")

    return redirect("enquiry_list")
# =====================================
# UPDATE STATUS
# =====================================

@login_required
def update_status(request, id, status):
    if request.method == "POST":

        data = json.loads(request.body)

        enquiry = get_object_or_404(Enquiry, id=id)

        if status == "pending_pitch3":

            enquiry.status = "confirmed"
            enquiry.approval_rate = data.get("approval_rate")

            enquiry.save()
            if enquiry.created_by:

                send_notification(
                    enquiry.created_by,
                    enquiry,
                    f"Enquiry {enquiry.enquiry_no} was confirmed by Admin"
                )
        return JsonResponse({"success": True})
    return JsonResponse({
        "success": False
    })

# =====================================
# UPDATE PITCH
# =====================================

@login_required
def update_pitch(request, id):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "msg": "Invalid request method"
        })

    enquiry = get_object_or_404(Enquiry, id=id)

    if enquiry.status == "confirmed":

        return HttpResponseForbidden(
            "Already confirmed. Cannot modify."
        )

    remarks = request.POST.get("remarks", "").strip()
    pitch_rate = request.POST.get("pitch_rate")
    is_approved = request.POST.get("is_approved") == "true"

    pitch_rate = request.POST.get("pitch_rate")

    if not pitch_rate:
        return JsonResponse({
            "success": False,
            "msg": "Pitch rate required"
        })

    try:
        pitch_rate = Decimal(pitch_rate)
    except:
        return JsonResponse({
            "success": False,
            "msg": "Invalid rate"
        })

    # --------------------------------
    # ADMIN CHECK
    # --------------------------------

    can_approve = (
        request.user.is_superuser or
        getattr(request.user, "role", "") == "admin"
    )

    current_status = (enquiry.status or "").lower()

    # =====================================
    # APPROVE DIRECTLY
    # =====================================

    if is_approved:

        if not can_approve:
            return HttpResponseForbidden(
                "Only Super Admin can approve"
            )

        latest_rate = (
            enquiry.pitch3 or
            enquiry.pitch2 or
            enquiry.pitch1 or
            enquiry.expected_rate
        )

        enquiry.status = "confirmed"
        enquiry.approval_rate = latest_rate

        enquiry.save()
        # --------------------------------
        # NOTIFICATION TO SALES USER
        # --------------------------------

        if enquiry.created_by:

            send_notification(
                enquiry.created_by,
                enquiry,
                f"Your enquiry {enquiry.enquiry_no} was approved by Super Admin"
            )

        return redirect("enquiry_list")

    # =====================================
    # PITCH 1
    # =====================================

    if current_status in ["", "waiting for rate approval"]:

        enquiry.pitch1 = pitch_rate
        enquiry.pitch1_remarks = remarks
        #enquiry.expected_rate = pitch_rate
        enquiry.approval_rate = pitch_rate
        enquiry.status = "pending_pitch1"
        enquiry.save()

        # Notification
        if enquiry.created_by:

            send_notification(
                enquiry.created_by,
                enquiry,
                f"Pitch 1 updated for enquiry {enquiry.enquiry_no}"
            )

    # =====================================
    # PITCH 2
    # =====================================

    elif current_status == "pending_pitch1":

        enquiry.pitch2 = pitch_rate
        enquiry.pitch2_remarks = remarks
        #enquiry.expected_rate = pitch_rate
        enquiry.approval_rate = pitch_rate
        enquiry.status = "pending_pitch2"

        enquiry.save()

        # Notification
        if enquiry.created_by:

            send_notification(
                enquiry.created_by,
                enquiry,
                f"Pitch 2 updated for enquiry {enquiry.enquiry_no} by {enquiry.created_by}"
            )

    # =====================================
    # FINAL CONFIRM
    # =====================================

    elif current_status == "pending_pitch2":

        enquiry.pitch3 = pitch_rate
        enquiry.pitch3_remarks = remarks
        enquiry.approval_rate = pitch_rate
        enquiry.status = "Pending_pitch3"

        enquiry.save()

        # Notification
        if enquiry.created_by:

            send_notification(
                enquiry.created_by,
                enquiry,
                f"Your enquiry {enquiry.enquiry_no} has been confirmed"
            )

    else:

        return JsonResponse({
            "success": False,
            "msg": "Maximum pitch attempts completed"
        })

    return redirect("enquiry_list")

def enquiry_dashboard(request):

    today = timezone.now().date()

    enquiries = Enquiry.objects.all()

    context = {

        "total_enquiries": enquiries.count(),

        "today_enquiries":
            enquiries.filter(
                created_at__date=today
            ).count(),

        "converted_orders":
            enquiries.filter(
                is_converted_to_order=True
            ).count(),

        "existing_customers":
            enquiries.filter(
                customer__isnull=False
            ).count(),

        "new_customers":
            enquiries.filter(
                customer__isnull=True
            ).count(),

        "rate_approval":
            enquiries.filter(
                status__icontains="approval"
            ).count(),

        "confirmed":
            enquiries.filter(
                status="confirmed"
            ).count(),

        "cancelled":
            enquiries.exclude(
                cancel_reason__isnull=True
            ).exclude(
                cancel_reason=""
            ).count(),

        "pitch1":
            enquiries.exclude(
                pitch1__isnull=True
            ).exclude(
                pitch1=""
            ).count(),

        "pitch2":
            enquiries.exclude(
                pitch2__isnull=True
            ).exclude(
                pitch2=""
            ).count(),

        "pitch3":
            enquiries.exclude(
                pitch3__isnull=True
            ).exclude(
                pitch3=""
            ).count(),

        "recent_enquiries":
            enquiries.order_by("-id")[:15]
    }

    return render(
        request,
        "dashboards/enquiry_dashboard.html",
        context
    )