from django.db import models
from vehicles.models import Vehicle

class TrackingSession(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("stopped", "Stopped"),
        ("license_hold", "License Hold"),
        ("error", "Error"),
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
    latitude = models.DecimalField(
    max_digits=10,
    decimal_places=7,
    null=True,
    blank=True
)

    longitude = models.DecimalField(
    max_digits=10,
    decimal_places=7,
    null=True,
    blank=True
)

    last_location = models.TextField(blank=True, null=True)

    last_updated = models.DateTimeField(
    null=True,
    blank=True
)
    location_status = models.CharField(max_length=100, blank=True, null=True)
    entity_id = models.BigIntegerField(
    null=True,
    blank=True,
    unique=True
)
    operator = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    consent_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    tracking_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle.ftl_no}"
    
class LiveLocation(models.Model):

    tracked = models.BooleanField(default=False)

    location_status = models.CharField(
        max_length=50,
        blank=True
    )

    address = models.TextField(blank=True)
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

    mobile = models.CharField(max_length=15)

    sms_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    message = models.TextField()

    delivery_status = models.CharField(
        max_length=50,
        default="Pending"
    )

    api_response = models.JSONField(
        blank=True,
        null=True
    )

    sent_at = models.DateTimeField(auto_now_add=True)

class ApiToken(models.Model):

    TOKEN_TYPES = (
        ("TRACKING", "Tracking"),
        ("CONSENT", "Consent"),
    )

    token_type = models.CharField(
        max_length=20,
        choices=TOKEN_TYPES,
        unique=True
    )

    access_token = models.TextField()

    response_json = models.JSONField(
    blank=True,
    null=True
)
    last_used = models.DateTimeField(
    null=True,
    blank=True
)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.token_type
    
class ApiLog(models.Model):

    api_name = models.CharField(max_length=100)

    request_url = models.TextField()

    request_method = models.CharField(max_length=10)

    request_headers = models.JSONField(blank=True, null=True)

    request_body = models.JSONField(blank=True, null=True)

    response_code = models.IntegerField()

    response_body = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
