from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid

class User(AbstractUser):
    employee_code = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    ROLE_CHOICES = (
        ('admin', 'Admin'),
         ('it', 'IT'),
        ('sales', 'Sales'),
        ('fleet', 'Fleet'),
        ('support', 'Support'),
        ('accounts', 'Accounts'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales')
    is_approved = models.BooleanField(default=False)  # 🔥 for admin approval

    def __str__(self):
        return self.username

class PasswordResetRequest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # 🔐 unique token for reset link
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.user.username} - {self.status}"