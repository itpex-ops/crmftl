
from django.db import models
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum
from orders.models import Order
from django.core.exceptions import ValidationError

class Vehicle(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )

    ftl_no = models.CharField(max_length=20, unique=True, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50)
    driver_number = models.CharField(max_length=15)
    owner_number = models.CharField(max_length=15, blank=True, null=True)

    SOURCE_TYPES = [
        ('direct','Direct'),
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
    is_overpaid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        total_freight = Decimal(self.total_freight or 0)
        if total_freight < 0:
            raise ValidationError("Invalid freight amount")
        
    @property
    def total_advance_paid(self):
        return self.transactions.filter(
            transaction_type="advance"
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")


    @property
    def total_balance_paid(self):

        return self.transactions.filter(
            transaction_type="balance"
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

    @property
    def total_paid(self):

        return self.transactions.filter(
            transaction_type__in=['advance', 'balance']
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

    @property
    def remaining_balance_amount(self):
        total_freight = Decimal(self.total_freight or 0)
        paid = Decimal(self.total_paid or 0)
        return max(total_freight - paid, Decimal("0"))

    @property
    def is_payment_completed(self):
        return self.remaining_balance_amount <= 0

    @property
    def is_trip_completed(self):
        if hasattr(self.order, "tracking"):
            return self.order.tracking.delivered
        return False

    @property
    def is_locked(self):

        if hasattr(self.order, "tracking"):
            return self.order.tracking.settled
        return False

    @property
    def total_expense(self):
            return self.transactions.aggregate(
                total=Sum('amount')
            )['total'] or 0

    @property
    def can_take_advance(self):
        return self.remaining_balance_amount > 0

    def can_take_balance(self):
        return self.remaining_balance_amount == 0
    
    def save(self, *args, **kwargs):
        self.total_freight = (
            Decimal(self.freight_amount or 0)
            + Decimal(self.brokerage or 0)
            + Decimal(self.loading_unloading or 0)
            + Decimal(self.halting or 0)
        )

        self.balance = (
            Decimal(self.total_freight or 0)
            - Decimal(self.advance or 0)

        )

        # 🔥 RUN VALIDATION BEFORE SAVE
        #self.full_clean()

        if not self.ftl_no:
            with transaction.atomic():
                last_vehicle = (
                    Vehicle.objects
                    .select_for_update()
                    .filter(ftl_no__isnull=False)
                    .order_by('-id')
                    .first()
                )

                if last_vehicle and last_vehicle.ftl_no:
                    try:
                        last_num = int(last_vehicle.ftl_no.replace("FTL", ""))
                    except ValueError:
                        last_num = 0
                    new_num = last_num + 1
                else:
                    new_num = 1

                self.ftl_no = f"FTL{new_num:03d}"

        super().save(*args, **kwargs)

class Tracking(models.Model):

    # =========================
    # ORDER RELATION
    # =========================

    STATUS_CHOICES = [
    ("vehicle_placed", "Vehicle Placed"),
    ("vehicle_document", "Vehicle Document"),
    ("invoice_eway", "Invoice / E-way"),

    ("advance_to_fleet", "Advance To Fleet"),
    ("fleet_departed", "Fleet Departed"),
    ("balance_trans_fleet", "Balance Transfer To Fleet"),
    ("arrived", "Arrived"),
    ("delivered", "Delivered"),
    ("pod_received", "POD Received"),
    ("settled", "Settled"),
    ("lr_generated", "LR Generated"),
    ]

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="vehicle_placed"
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="tracking",
        null=True,
        blank=True
    )
    # =========================
    # STATUS
    # =========================

    vehicle_placed = models.BooleanField(default=False)
    vehicle_document = models.BooleanField(default=False)
    invoice_eway = models.BooleanField(default=False)
    advance_to_fleet = models.BooleanField(default=False)
    balance_to_fleet = models.BooleanField(default=False)
    fleet_departed = models.BooleanField(default=False)
    advance_received = models.BooleanField(default=False)
    arrived = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    pod_received = models.BooleanField(default=False)
    balance_paid = models.BooleanField(default=False)
    lr_no_b = models.BooleanField(default=False)

    lr_no = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    transporter_paid = models.BooleanField(default=False)
    customer_paid = models.BooleanField(default=False)
    settled = models.BooleanField(default=False)

    # =========================
    # DATES
    # =========================

    vehicle_placed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    fleet_departed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    arrived_at = models.DateTimeField(
        null=True,
        blank=True
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # =========================
    # OTHER
    # =========================

    remarks = models.TextField(blank=True)

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =========================
    # STRING
    # =========================

    def __str__(self):

        if self.order:
            return f"Tracking - {self.order.order_no}"

        if self.manual_order:
            return f"Tracking - {self.manual_order.order_no}"

        return "Tracking"

class TrackingDocument(models.Model):

    tracking = models.ForeignKey(
        Tracking,
        related_name="documents",
        on_delete=models.CASCADE
    )

    file = models.FileField(
        upload_to="tracking_docs/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.file.name
