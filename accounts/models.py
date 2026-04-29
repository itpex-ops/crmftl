from django.db import models
from enquiries.models import Enquiry
from vehicles.models import Vehicle
from django.conf import settings


class CustomerTransaction(models.Model):
    TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('payment', 'Payment Received'),
        ('advance', 'Advance Received'),
    ]

    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.enquiry.customer_name


class VehicleTransaction(models.Model):
    TYPE_CHOICES = [
        ('fuel', 'Fuel'),
        ('driver_advance', 'Driver Advance'),
        ('toll', 'Toll'),
        ('rent', 'Vehicle Rent'),
        ('maintenance', 'Maintenance'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.vehicle.vehicle_no

class BankTransaction(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    bank_name = models.CharField(max_length=100)
    txn_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_no = models.CharField(max_length=120, blank=True, null=True)
    party_name = models.CharField(max_length=150)
    purpose = models.CharField(max_length=150)
    remarks = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.txn_type} - {self.amount}"
    
class LedgerEntry(models.Model):

    ACCOUNT_TYPES = [
        ('customer', 'Customer'),
        ('vehicle', 'Vehicle'),
        ('bank', 'Bank'),
    ]

    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)

    date = models.DateTimeField(auto_now_add=True)

    # links (optional)
    enquiry = models.ForeignKey('enquiries.Enquiry', null=True, blank=True, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', null=True, blank=True, on_delete=models.CASCADE)
    vehicle = models.ForeignKey('vehicles.Vehicle', null=True, blank=True, on_delete=models.CASCADE)

    debit = models.FloatField(default=0)   # outgoing
    credit = models.FloatField(default=0)  # incoming

    remarks = models.CharField(max_length=255, blank=True, null=True)
