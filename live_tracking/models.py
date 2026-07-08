from django.db import models
from vehicles.models import Vehicle

class TrackingSession(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sms_sent", "SMS Sent"),
        ("active", "Active"),
        ("stopped", "Stopped"),
        ("failed", "Failed"),
    ]

    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="tracking_session"
    )

    tracking_reference = models.CharField(
        max_length=100,
        unique=True
    )

    driver_mobile = models.CharField(max_length=15)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    consent_received = models.BooleanField(default=False)

    last_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    last_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    last_accuracy = models.FloatField(
        default=0
    )

    last_location = models.CharField(
        max_length=300,
        blank=True
    )

    last_updated = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle.ftl_no}"
    
class LiveLocation(models.Model):

    session = models.ForeignKey(
        TrackingSession,
        on_delete=models.CASCADE,
        related_name="locations"
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    accuracy = models.FloatField(default=0)

    location_name = models.CharField(
        max_length=300,
        blank=True
    )

    received_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

class SMSLog(models.Model):

    session = models.ForeignKey(
        TrackingSession,
        on_delete=models.CASCADE,
        related_name="sms_logs"
    )

    sms_reference = models.CharField(
        max_length=100,
        blank=True
    )

    mobile = models.CharField(max_length=15)

    message = models.TextField()

    delivery_status = models.CharField(
        max_length=50,
        default="Pending"
    )

    sent_at = models.DateTimeField(auto_now_add=True)

class TrackingSMS(models.Model):

    session = models.ForeignKey(
        TrackingSession,
        on_delete=models.CASCADE
    )

    mobile = models.CharField(max_length=15)

    sms_reference = models.CharField(max_length=100)

    message = models.TextField()

    status = models.CharField(max_length=20)

    sent_at = models.DateTimeField(auto_now_add=True)