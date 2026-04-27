from django.db import models
from django.conf import settings
from django.utils import timezone


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
    ('Flat Low Bed 20 Ft', 'Flat Low Bed 20 Ft'),
    ('Flat Low Bed 32 Ft', 'Flat Low Bed 32 Ft'),
    ('Flat Low Bed 40 Ft', 'Flat Low Bed 40 Ft'),

    ('Flat High Bed 20 Ft', 'Flat High Bed 20 Ft'),
    ('Flat High Bed 32 Ft', 'Flat High Bed 32 Ft'),
    ('Flat High Bed 40 Ft', 'Flat High Bed 40 Ft'),

    # SPECIAL
    ('JCB', 'JCB'),
    ('ODC', 'ODC'),

    # TORRES
    ('Torres 6 Wheels', 'Torres 6 Wheels'),
    ('Torres 10 Wheels', 'Torres 10 Wheels'),
    ('Torres 12 Wheels', 'Torres 12 Wheels'),
    ('Torres 14 Wheels', 'Torres 14 Wheels'),
    ('Torres 16 Wheels', 'Torres 16 Wheels'),
]

class Enquiry(models.Model):
    enquiry_no = models.CharField(max_length=20, unique=True, blank=True)

    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    lead_source = models.CharField(max_length=50, blank=True, null=True)
    reference_name = models.CharField(max_length=200, blank=True, null=True)

    pickups = models.IntegerField(default=1)
    deliveries = models.IntegerField(default=1)

    vehicle_type = models.CharField(
        max_length=100,
        choices=VEHICLE_TYPES,
        blank=True,
        null=True
    )

    vehicle_description = models.TextField(
        max_length=300,
        blank=True,
        null=True
    )

    kms = models.CharField(max_length=200, blank=True, null=True)

    material = models.CharField(max_length=200, blank=True, null=True)
    pieces = models.IntegerField(blank=True, null=True)
    tonnage = models.FloatField(blank=True, null=True)

    dimension_unit = models.CharField(max_length=20, blank=True, null=True)

    length = models.FloatField(blank=True, null=True)
    breadth = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)

    expected_rate = models.FloatField(blank=True, null=True)
    approval_rate = models.FloatField(blank=True, null=True)

    gstbill = models.IntegerField(blank=True, null=True)

    routes = models.JSONField(default=list, blank=True)

    status = models.CharField(max_length=200, blank=True, null=True)

    pitch1 = models.CharField(max_length=200, blank=True, null=True)
    pitch2 = models.CharField(max_length=200, blank=True, null=True)
    pitch3 = models.CharField(max_length=200, blank=True, null=True)

    cancel_reason = models.CharField(max_length=200, blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    is_converted_to_order = models.BooleanField(
        default=False,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.enquiry_no:

            today = timezone.now().strftime("%d%m%y")

            last_enquiry = Enquiry.objects.filter(
                enquiry_no__startswith=f"EQR-{today}"
            ).order_by('-id').first()

            if last_enquiry and last_enquiry.enquiry_no:
                last_series = int(
                    last_enquiry.enquiry_no.split('-')[-1]
                )
                new_series = f"{last_series+1:03d}"
            else:
                new_series = "001"

            self.enquiry_no = f"EQR-{today}-{new_series}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enquiry_no} - {self.customer_name}"
