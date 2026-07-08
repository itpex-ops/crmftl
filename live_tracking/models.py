from django.db import models

# Create your models here.
from django.db import models
from vehicles.models import Vehicle


class TrackingSession(models.Model):

    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="live_tracking"
    )

    tracking_reference = models.CharField(max_length=100)

    status = models.CharField(
        max_length=30,
        default="Pending"
    )

    consent_received = models.BooleanField(default=False)

    started_at = models.DateTimeField(auto_now_add=True)

    ended_at = models.DateTimeField(
        null=True,
        blank=True
    )

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

    address = models.TextField(blank=True)

    speed = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

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