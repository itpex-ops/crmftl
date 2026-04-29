from django.utils import timezone
from django.db import models
from django.conf import settings

class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    customer_code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

class ManualOrder(models.Model):
    order_no = models.CharField(max_length=20, unique=True)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    customer_name = models.CharField(max_length=150)
    customer_contact = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    origin = models.TextField(blank=True)
    destination = models.TextField(blank=True)

    vehicle_type = models.CharField(max_length=100, blank=True)
    vehicle_description = models.CharField(max_length=200, blank=True)

    material = models.CharField(max_length=200, blank=True)

    pieces = models.IntegerField(default=0)
    tonnage = models.FloatField(default=0)

    expected_rate = models.FloatField(default=0)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_no
    
class Pricing(models.Model):
    order = models.OneToOneField(ManualOrder, on_delete=models.CASCADE)

    base_freight = models.FloatField(default=0)
    extra_charges = models.FloatField(default=0)
    advance_amount = models.FloatField(default=0)
    balance_amount = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)

class Payment(models.Model):
    PAYMENT_MODE = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Credit'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    )

    order = models.OneToOneField(ManualOrder, on_delete=models.CASCADE)

    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE)
    payment_status = models.CharField(max_length=20, choices=STATUS)

    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)

class ExistingCustomerVehicle(models.Model):
    order = models.ForeignKey(ManualOrder, on_delete=models.CASCADE, related_name="exvehicles")
    vehicle_number = models.CharField(max_length=50)
    driver_number = models.CharField(max_length=15)
    owner_number = models.CharField(max_length=15)

    freight_amount = models.FloatField(default=0)

    UPI_CHOICES = (
        ('gpay', 'Google Pay'),
        ('phonepe', 'PhonePe'),
        ('paytm', 'Paytm'),
    )

    upi_app = models.CharField(max_length=20, choices=UPI_CHOICES, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

