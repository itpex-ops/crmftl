from django.utils import timezone
from django.db import models
from django.conf import settings

class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    customer_code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

VEHICLE_TYPES = [
    # OPEN BODY
    ('Open Body 9 Ft', 'Open Body 9 Ft'),
    ('Open Body 10 Ft', 'Open Body 10 Ft'),
    ('Open Body 12 Ft', 'Open Body 12 Ft'),
    ('Open Body 14 Ft', 'Open Body 14 Ft'),
    ('Open Body 16 Ft', 'Open Body 16 Ft'),
    ('Open Body 17 Ft', 'Open Body 17 Ft'),
    ('Open Body 20 Ft', 'Open Body 20 Ft'),
    ('Open Body 24 Ft', 'Open Body 24 Ft'),

    # CONTAINER
    ('Container 9 Ft', 'Container 9 Ft'),
    ('Container 10 Ft', 'Container 10 Ft'),
    ('Container 12 Ft', 'Container 12 Ft'),
    ('Container 14 Ft', 'Container 14 Ft'),
    ('Container 16 Ft', 'Container 16 Ft'),
    ('Container 17 Ft', 'Container 17 Ft'),
    ('Container 20 Ft', 'Container 20 Ft'),
    ('Container 24 Ft', 'Container 24 Ft'),
    ('Container 32 Ft', 'Container 32 Ft'),

    # TRAILER
    ('Trailer Flat Low Bed 20 Ft','Trailer Flat Low Bed 20 Ft'),
    ('Trailer Flat Low Bed 32 Ft','Trailer Flat Low Bed 32 Ft'),
    ('Trailer Flat Low Bed 40 Ft','Trailer Flat Low Bed 40 Ft'),

    ('Trailer Flat High Bed 20 Ft', 'Trailer Flat High Bed 20 Ft'),
    ('Trailer Flat High Bed 32 Ft', 'Trailer Flat High Bed 32 Ft'),
    ('Trailer Flat High Bed 40 Ft', 'Trailer Flat High Bed 40 Ft'),

    # SPECIAL
    ('JCB', 'JCB'),
    ('ODC', 'ODC'),
    ('TATA ACE','Tata Ace 7 Ft'),
    ('TATA 407','Tata 407 10 to 12 Ft'),
    ('Bolero PickUP','Bolero Pickup 8 to 10 Ft'),
    ('Dost 8 to 9 Ft','Dost 8 to 9 Ft'),
    ('BadaDost 10 Ft','BadaDost 10 Ft'),

    # TORRES
    ('Torres 6 Wheels', 'Torres 6 Wheels'),
    ('Torres 10 Wheels', 'Torres 10 Wheels'),
    ('Torres 12 Wheels', 'Torres 12 Wheels'),
    ('Torres 14 Wheels', 'Torres 14 Wheels'),
    ('Torres 16 Wheels', 'Torres 16 Wheels'),
]

class ManualOrder(models.Model):

    order_no = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )

    customer_name = models.CharField(max_length=150)

    customer_contact = models.CharField(max_length=15)

    email = models.EmailField(blank=True, null=True)

    origin = models.TextField(blank=True)

    destination = models.TextField(blank=True)

    vehicle_type = models.CharField(
        max_length=100,
        choices=VEHICLE_TYPES,
        blank=True,
        null=True
    )

    vehicle_description = models.CharField(
        max_length=200,
        blank=True
    )

    material = models.CharField(
        max_length=200,
        blank=True
    )

    pieces = models.IntegerField(default=0)

    tonnage = models.FloatField(default=0)

    expected_rate = models.FloatField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.order_no:

            today = timezone.now().strftime("%d%m%y")

            count_today = ManualOrder.objects.filter(
                order_no__startswith=f"EX-{today}"
            ).count() + 1

            self.order_no = f"EX-{today}-{str(count_today).zfill(3)}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_no
  
class Pricing(models.Model):
    order = models.OneToOneField(ManualOrder, on_delete=models.CASCADE)

    base_freight = models.FloatField(default=0)
    extra_charges = models.FloatField(default=0)
    advance_amount = models.FloatField(default=0)
    balance_amount = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)

class Payment(models.Model):
    PAYMENT_MODE = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Credit'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    )

    order = models.OneToOneField(ManualOrder, on_delete=models.CASCADE)

    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE)
    payment_status = models.CharField(max_length=20, choices=STATUS)

    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
