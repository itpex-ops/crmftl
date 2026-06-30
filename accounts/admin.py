from django.contrib import admin
from .models import CustomerTransaction, VehicleTransaction


@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enquiry",
        "customer_name",
        "amount",
        "payment_against",
        "account_type",
        "payment_mode",
        "reference_no",
        "transaction_datetime",
        "created_by",
    )

    list_filter = (
        "payment_against",
        "account_type",
        "payment_mode",
        "transaction_datetime",
    )

    search_fields = (
        "enquiry__enquiry_no",
        "enquiry__customer_name",
        "reference_no",
        "remarks",
    )

    ordering = ("-id",)

    date_hierarchy = "transaction_datetime"

    @admin.display(description="Customer")
    def customer_name(self, obj):
        return obj.enquiry.customer_name


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