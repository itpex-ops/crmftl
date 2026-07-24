from django.db import models
from django.conf import settings

from orders.models import Order
from vehicles.models import Vehicle
from django.conf import settings
from django.db import models

from orders.models import Order
from vehicles.models import Vehicle

from .choices import (
    PAYMENT_TYPE_CHOICES,
    PAYMENT_MODE_CHOICES,
    PAYMENT_STATUS_CHOICES,
)

class BankConfiguration(models.Model):
    name = models.CharField(max_length=100)

    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name}"

from django.db import models


class ApiLog(models.Model):
    api_name = models.CharField(max_length=100)

    endpoint = models.CharField(max_length=300)

    method = models.CharField(max_length=10)

    request_data = models.JSONField(
        blank=True,
        null=True,
    )

    response_data = models.JSONField(
        blank=True,
        null=True,
    )

    status_code = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    response_time = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        help_text="Response time in seconds",
    )

    success = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "API Log"
        verbose_name_plural = "API Logs"

    def __str__(self):
        return f"{self.api_name} ({self.status_code})"

from django.conf import settings
from django.db import models

from orders.models import Order
from vehicles.models import Vehicle

class Payment(models.Model):
    payment_no = models.CharField(
        max_length=30,
        unique=True,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES,
    )

    beneficiary_name = models.CharField(
        max_length=200,
    )

    account_number = models.CharField(
        max_length=30,
    )

    ifsc = models.CharField(
        max_length=20,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    purpose = models.CharField(
        max_length=250,
        blank=True,
    )

    bank_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="draft",
    )

    remarks = models.TextField(
        blank=True,
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_payments",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.payment_no


from .choices import UPI_STATUS_CHOICES


class UPITransaction(models.Model):
    upi_reference = models.CharField(
        max_length=50,
        unique=True,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payer_name = models.CharField(
        max_length=200,
        blank=True,
    )

    payer_vpa = models.CharField(
        max_length=100,
        blank=True,
    )

    payee_vpa = models.CharField(
        max_length=100,
        blank=True,
    )

    qr_string = models.TextField(
        blank=True,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=UPI_STATUS_CHOICES,
        default="created",
    )

    remarks = models.TextField(
        blank=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.upi_reference
