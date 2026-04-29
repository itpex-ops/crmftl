from django.contrib import admin
from .models import CustomerTransaction, VehicleTransaction


@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'enquiry',
        'transaction_type',
        'amount',
        'date',
        'created_by',
    )
    list_filter = (
        'transaction_type',
        'date',
    )
    search_fields = (
        'enquiry__enquiry_no',
        'enquiry__customer_name',
        'remarks',
    )
    ordering = ('-id',)


@admin.register(VehicleTransaction)
class VehicleTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'vehicle',
        'transaction_type',
        'amount',
        'date',
        'created_by',
    )
    list_filter = (
        'transaction_type',
        'date',
    )
    search_fields = (
        'vehicle__vehicle_no',
        'remarks',
    )
    ordering = ('-id',)