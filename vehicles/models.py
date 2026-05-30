
from django.db import models
from django.db import transaction
from decimal import Decimal

from orders.models import Order
from manual_order.models import ManualOrder


class Vehicle(models.Model):

    # =========================
    # ORDER RELATIONS
    # =========================

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="vehicle",
        null=True,
        blank=True
    )

    manual_order = models.ForeignKey(
    ManualOrder,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='vehicles'
)

    # =========================
    # BASIC
    # =========================

    ftl_no = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )

    vehicle_number = models.CharField(
        max_length=50
    )

    driver_number = models.CharField(
        max_length=15
    )

    owner_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    # =========================
    # SOURCE
    # =========================

    SOURCE_TYPES = [
        ('direct', 'Direct'),
        ('transporters', 'Transporters'),
        ('brokers', 'Brokers'),
        ('drivers', 'Drivers'),
        ('others', 'Others'),
    ]

    source = models.CharField(
        max_length=100,
        choices=SOURCE_TYPES,
        blank=True,
        null=True
    )

    ORDER_TYPE = [
        ('crm', 'CRM Order'),
        ('manual', 'Manual Order'),
    ]

    order_type = models.CharField(
        max_length=10,
        choices=ORDER_TYPE,
        default='crm'
    )

    # =========================
    # FREIGHT
    # =========================

    freight_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    halting = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    loading_unloading = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    brokerage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_freight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    advance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    margin_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    profit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # =========================
    # APPROVAL
    # =========================

    approval_required = models.BooleanField(
        default=False
    )

    approval_name = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    approval_reason = models.TextField(
        blank=True,
        null=True
    )

    # =========================
    # BANK
    # =========================

    account_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    account_number = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    ifsc = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    ac_type = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    bank_verified = models.BooleanField(
        default=False
    )

    bank_verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    beneficiary_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # =========================
    # UPI
    # =========================

    UPI_CHOICES = [
        ('phonepe', 'PhonePe'),
        ('gpay', 'Google Pay'),
        ('paytm', 'Paytm'),
        ('other', 'Other'),
    ]

    upi_app = models.CharField(
        max_length=10,
        choices=UPI_CHOICES,
        default='phonepe'
    )

    upi_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    upi_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    # =========================
    # OTHER
    # =========================

    vehicle_reassign_date = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =========================
    # SAVE
    # =========================

    def save(self, *args, **kwargs):

        # =========================
        # ORDER TYPE VALIDATION (NEW)
        # =========================

        if hasattr(self, "order_type"):

            if self.order_type == "crm" and not self.order:
                raise ValueError("CRM vehicle must have Order")

            if self.order_type == "manual" and not self.manual_order:
                raise ValueError("Manual vehicle must have ManualOrder")

        else:
            # fallback (old system safety)
            if not self.order and not self.manual_order:
                raise ValueError(
                    "Vehicle must be linked to Order or ManualOrder"
                )

        # =========================
        # BALANCE
        # =========================

        self.balance = (
            Decimal(self.freight_amount or 0)
            - Decimal(self.advance or 0)
        )

        # =========================
        # TOTAL FREIGHT
        # =========================

        self.total_freight = (
            Decimal(self.freight_amount or 0)
            + Decimal(self.halting or 0)
            + Decimal(self.loading_unloading or 0)
            + Decimal(self.brokerage or 0)
        )

        # =========================
        # AUTO FTL NUMBER
        # =========================

        if not self.ftl_no:

            with transaction.atomic():

                last_vehicle = (
                    Vehicle.objects
                    .select_for_update()
                    .exclude(ftl_no__isnull=True)
                    .exclude(ftl_no__exact='')
                    .order_by('-id')
                    .first()
                )

            new_num = 1

            if last_vehicle and last_vehicle.ftl_no:

                try:
                    # safer parsing
                    last_num = int(
                        last_vehicle.ftl_no.replace("FTL", "").strip()
                    )
                    new_num = last_num + 1

                except (ValueError, AttributeError):
                    new_num = 1

            self.ftl_no = f"FTL{new_num:03d}"
        super().save(*args, **kwargs)

    # =========================
    # STRING
    # =========================

    def __str__(self):

        if self.order:
            return f"{self.ftl_no} - {self.order.order_no}"

        if self.manual_order:
            return f"{self.ftl_no} - {self.manual_order.order_no}"

        return self.ftl_no


class Tracking(models.Model):

    # =========================
    # ORDER RELATION
    # =========================

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="tracking",
        null=True,
        blank=True
    )

    manual_order = models.OneToOneField(
        ManualOrder,
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
    fleet_departed = models.BooleanField(default=False)
    advance_received = models.BooleanField(default=False)
    arrived = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    pod_received = models.BooleanField(default=False)

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

