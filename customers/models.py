from django.db import models
from django.db import models

class ExCustomer(models.Model):


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
    created_by = models.CharField(max_length=40,blank=True,null=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        creating = self.pk is None

        super().save(*args, **kwargs)

        if creating:
            self.customer_code = f"C{self.pk:05d}"
            ExCustomer.objects.filter(pk=self.pk).update(
                customer_code=self.customer_code
        )

    def __str__(self):
        return f"{self.customer_code} - {self.name}"
