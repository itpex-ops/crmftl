from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order
from vehicles.models import Vehicle
from .models import LedgerEntry

@receiver(post_save, sender=Order)
def order_to_ledger(sender, instance, created, **kwargs):

    if not created:
        return

    # 👤 CUSTOMER LEDGER (SALE)
    LedgerEntry.objects.create(
        account_type='customer',
        enquiry=instance.enquiry,
        order=instance,
        debit=instance.total_rate or 0,
        credit=0,
        remarks=f"Order Created - {instance.order_no}"
    )

    # 💰 ADVANCE RECEIVED (BANK IN)
    if instance.advance:
        LedgerEntry.objects.create(
            account_type='bank',
            order=instance,
            credit=instance.advance,
            remarks=f"Advance Received - {instance.order_no}"
        )
@receiver(post_save, sender=Vehicle)
def vehicle_to_ledger(sender, instance, created, **kwargs):

    if not created:
        return

    # 🚛 VEHICLE EXPENSE
    LedgerEntry.objects.create(
        account_type='vehicle',
        vehicle=instance,
        debit=instance.total_freight,
        credit=0,
        remarks=f"Trip Expense - {instance.vehicle_number}"
    )

    # 💸 ADVANCE PAID TO DRIVER
    if instance.advance:
        LedgerEntry.objects.create(
            account_type='bank',
            vehicle=instance,
            debit=instance.advance,
            remarks=f"Driver Advance - {instance.vehicle_number}"
        )