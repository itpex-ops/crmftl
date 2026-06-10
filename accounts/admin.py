from django.contrib import admin
from .models import CustomerTransaction, VehicleTransaction


@admin.register(VehicleTransaction)
class VehicleTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "vehicle",
        "transaction_type",
        "amount",
        "payment_mode",
        "status",
        "utr_no",
        "transaction_no",
        "date",
        "created_by",
    )

    list_filter = (
        "transaction_type",
        "payment_mode",
        "status",
        "date",
    )

    search_fields = (
        "vehicle__vehicle_number",
        "transaction_no",
        "utr_no",
        "remarks",
    )

    ordering = ("-id",)