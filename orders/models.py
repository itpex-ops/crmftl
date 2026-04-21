# orders/models.py
from django.utils import timezone
from django.db import models
from django.conf import settings
from enquiries.models import Enquiry
class Order(models.Model):
    enquiry = models.OneToOneField(Enquiry, on_delete=models.CASCADE)

    order_no = models.CharField(max_length=20, unique=True, blank=True)

    customer_name = models.CharField(max_length=255)
    customer_contact = models.CharField(max_length=15)

    routes = models.JSONField(null=True, blank=True)
    vehicle_type = models.CharField(max_length=100)
    vehicle_place_date = models.DateTimeField(blank=True,null=True)

    # 💰 Pricing
    finalized_rate = models.FloatField(null=True, blank=True)
    loading_charges = models.FloatField(null=True, blank=True)
    halting_charges = models.FloatField(null=True, blank=True)
    gst_percent = models.FloatField(null=True, blank=True)
    total_rate = models.FloatField(null=True, blank=True)

    # 💳 Payment
    payment_terms = models.CharField(max_length=50, null=True, blank=True)
    advance = models.FloatField(null=True, blank=True)
    balance = models.FloatField(null=True, blank=True)
    topay = models.FloatField(null=True, blank=True)
    credit = models.FloatField(null = True , blank = True)
    credit_date = models.DateTimeField(blank=True,null=True)
    credit_days = models.IntegerField(blank=True,null=True)
    due_date = models.DateTimeField(blank= True,null = True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_no:
            today = timezone.now().strftime("%d%m%y")  # e.g., 090426
            # Count existing orders for today
            count_today = Order.objects.filter(order_no__startswith=f"ORD-{today}").count() + 1
            self.order_no = f"ORD-{today}-{str(count_today).zfill(3)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_no
    
