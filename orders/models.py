from django.db import models
from django.conf import settings
from django.utils import timezone
from enquiries.models import Enquiry

class Order(models.Model):
    # Link to Enquiry
    enquiry = models.OneToOneField(
        Enquiry,
        on_delete=models.CASCADE,
        related_name='order'
    )

    # Auto-generated Order No
    order_no = models.CharField(max_length=50, unique=True, blank=True)

    # Customer Details
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    customer_contact = models.CharField(max_length=15, blank=True, null=True)

    # Routes & Vehicle
    routes = models.JSONField(default=list, blank=True)
    vehicle_type = models.CharField(max_length=100, blank=True, null=True)

    # Order Dates
    date = models.DateTimeField(auto_now_add=True)

    # Pricing
    final_rate = models.FloatField(blank=True, null=True)
    loading_unloading = models.FloatField(default=0)
    halting_charges = models.FloatField(default=0)
    gst_percent = models.FloatField(default=0)
    total_rate = models.FloatField(blank=True, null=True)

    # Order Status
    ORDER_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='draft')

    # Payment
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    advance = models.FloatField(blank=True, null=True)
    balance = models.FloatField(blank=True, null=True)
    credit_days = models.IntegerField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # Auto-generate Order No
        if not self.order_no:
            today = timezone.now().strftime("%d%m%Y")
            last_order = Order.objects.filter(order_no__startswith=f"ORD-{today}").order_by('id').last()
            new_no = int(last_order.order_no.split('-')[-1]) + 1 if last_order else 1
            self.order_no = f"ORD-{today}-{str(new_no).zfill(4)}"

        # Copy data from enquiry if missing
        if self.enquiry:
            self.customer_name = self.customer_name or self.enquiry.customer_name
            self.customer_contact = self.customer_contact or self.enquiry.customer_contact
            self.routes = self.routes or self.enquiry.routes
            self.vehicle_type = self.vehicle_type or self.enquiry.vehicle_type
            self.final_rate = self.final_rate or float(self.enquiry.approval_rate or 0)
            self.gst_percent = self.gst_percent or float(self.enquiry.gstbill or 0)

        # Total calculation
        base = self.final_rate or 0
        extra = (self.loading_unloading or 0) + (self.halting_charges or 0)
        gst = (base + extra) * (self.gst_percent or 0) / 100
        self.total_rate = base + extra + gst

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_no