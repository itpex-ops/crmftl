from django.db import models
from orders.models import Order
from decimal import Decimal
from django.db.models import Max
from django.db import transaction

class Vehicle(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='vehicles'   # 🔥 IMPORTANT
    )
    ftl_no = models.CharField(max_length=20, unique=True, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50)
    driver_number = models.CharField(max_length=15)
    owner_number = models.CharField(max_length=15, blank=True, null=True)

    SOURCE_TYPES = [
        ('directors','Directors'),
        ('transporters','Transporters'),
        ('brokers','Brokers'),
        ('drivers','Drivers'),
        ('others','Others')
    ]
    
    source = models.CharField(max_length=100, choices = SOURCE_TYPES, blank=True, null=True )

    # 💰 MONEY FIELDS (use DecimalField)
    freight_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    halting = models.DecimalField(max_digits=200,decimal_places=2,default=0)
    loading_unloading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    brokerage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # 💳 PAYMENT
    account_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    ifsc = models.CharField(max_length=20, blank=True, null=True)
    ac_type = models.CharField(max_length=20, blank = True, null=True)
    bank_verified = models.BooleanField(default=False)
    bank_verified_at = models.DateTimeField(null=True, blank=True)
    beneficiary_name = models.CharField(max_length=100, blank=True, null=True)

    UPI_CHOICES = [
    ('phonepe', 'PhonePe'),
    ('gpay', 'Google Pay'),
    ('paytm', 'Paytm'),
    ('other', 'Other'),
    ]

    upi_app = models.CharField(max_length=10, choices=UPI_CHOICES, default='phonepe')
    upi_id = models.CharField(max_length=200,blank=True,null=True)
    upi_number = models.CharField(max_length=200, blank=True,null=True)
    vehicle_reassign_date = models.DateTimeField(blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.balance = Decimal(self.freight_amount or 0) - Decimal(self.advance or 0)
        self.total_freight = (
            Decimal(self.freight_amount or 0)
            + Decimal(self.brokerage or 0)
            + Decimal(self.loading_unloading or 0)
        )
        if not self.ftl_no:
            with transaction.atomic():
                last_vehicle = (
                    Vehicle.objects
                    .select_for_update()
                    .order_by('-id')
                    .first()
                )
                if last_vehicle and last_vehicle.ftl_no:
                    last_num = int(last_vehicle.ftl_no.split('_')[1])
                    new_num = last_num + 1
                else:
                    new_num = 1

                self.ftl_no = f"FTL_{new_num:03d}"
        super().save(*args, **kwargs)
        def __str__(self):
            return f"{self.vehicle_number} ({self.order.order_no})"

class Tracking(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="tracking")

    vehicle_placed = models.BooleanField(default=False)
    vehicle_document = models.BooleanField(default=False)
    invoice_eway = models.BooleanField(default=False)
    advance_to_fleet = models.BooleanField(default=False)
    fleet_departed = models.BooleanField(default=False)
    advance_received = models.BooleanField(default=False)
    arrived = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    pod_received = models.BooleanField(default=False)
    lr_no_b = models.BooleanField(default=False)
    lr_no = models.TextField(max_length=200, blank=True,null=True)

    transporter_paid = models.BooleanField(default=False)
    customer_paid = models.BooleanField(default=False)
    settled = models.BooleanField(default=False)

    vehicle_placed_at = models.DateTimeField(null=True, blank=True)
    fleet_departed_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tracking - {self.order.order_no}"

