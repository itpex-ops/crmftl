from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from accounts.models import Account


@receiver(post_save, sender=Order)
def create_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(order=instance)