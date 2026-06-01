from django.db import models

# Create your models here.
from django.db import models

class ExCustomer(models.Model):

    # Basic Information
    customer_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    name = models.CharField(max_length=150)

    phone1 = models.CharField(
        max_length=15,
        unique=True
    )

    phone2 = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    # GST Information
    gst_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    pan_number = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state_code = models.CharField(
        max_length=5,
        blank=True,
        null=True
    )

    # Address
    address = models.TextField()

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    # Status
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.customer_code:
            self.customer_code = f"CUST{self.id:05d}"
            super().save(update_fields=["customer_code"])

    def __str__(self):
        return f"{self.customer_code} - {self.name}"