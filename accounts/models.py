from django.db import models
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal
from enquiries.models import Enquiry
from orders.models import Order
from vehicles.models import Vehicle
from django.core.exceptions import ValidationError

class CustomerTransaction(models.Model):

    TYPE_CHOICES = [
        ('invoice', 'Invoice Raised'),
        ('advance', 'Advance Received'),
        ('payment', 'Payment Received'),
    ]

    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank', 'Bank Transfer'),
    ]

    enquiry = models.ForeignKey(
        Enquiry,
        on_delete=models.CASCADE,
        related_name='customer_transactions'
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODES,
        blank=True,
        null=True
    )

    reference_no = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    date = models.DateField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return f"{self.enquiry.customer_name} - {self.amount}"

class VehicleTransaction(models.Model):

    TYPE_CHOICES = [
        ('advance', 'Advance Payment'),
        ('balance', 'Balance Payment'),
        ('fuel', 'Fuel'),
        ('driver_advance', 'Driver Advance'),
        ('toll', 'Toll'),
        ('maintenance', 'Maintenance'),
        ('rent', 'Vehicle Rent'),
        ('others', 'Others'),
    ]

    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank', 'Bank Transfer'),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODES,
        blank=True,
        null=True
    )

    transaction_no = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('success', 'Success'),
    ('failed', 'Failed'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    utr_no = models.CharField(
    max_length=100,
    blank=True,
    null=True
)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    date = models.DateField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    def clean(self):

        if self.transaction_type == "advance":

            remaining = self.vehicle.remaining_balance_amount

            if remaining <= 0:
                raise ValidationError("Advance not allowed. Balance is zero.")

            if self.amount > remaining:
                raise ValidationError(
                    f"Advance cannot exceed {remaining}"
                )
   
   
    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.amount}"

class BankTransaction(models.Model):

    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    bank_name = models.CharField(
        max_length=100
    )

    txn_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference_no = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    party_name = models.CharField(
        max_length=150
    )

    purpose = models.CharField(
        max_length=150
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    date = models.DateField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.bank_name} - {self.amount}"

class Expense(models.Model):

    EXPENSE_TYPES = [
        ('office', 'Office Expense'),
        ('salary', 'Salary'),
        ('rent', 'Office Rent'),
        ('internet', 'Internet'),
        ('electricity', 'Electricity'),
        ('misc', 'Miscellaneous'),
    ]

    expense_type = models.CharField(
        max_length=30,
        choices=EXPENSE_TYPES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    date = models.DateField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return f"{self.expense_type} - ₹{self.amount}"

class LedgerEntry(models.Model):

    ACCOUNT_TYPES = [
        ('customer', 'Customer'),
        ('vehicle', 'Vehicle'),
        ('bank', 'Bank'),
        ('expense', 'Expense'),
    ]

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES
    )

    voucher_no = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    enquiry = models.ForeignKey(
        Enquiry,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    order = models.ForeignKey(
        Order,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    vehicle = models.ForeignKey(
        Vehicle,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.account_type} - D:{self.debit} C:{self.credit}"