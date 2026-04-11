from django.db import models
from django.conf import settings
from orders.models import Order
from vehicles.models import Vehicle

User = settings.AUTH_USER_MODEL


# ===============================
# 💰 MAIN ACCOUNT (Per Order)
# ===============================
class Account(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="account"
    )

    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def calculate(self):
        # Revenue = Order value
        self.total_revenue = self.order.total_rate or 0

        # Expense = sum of vehicle costs
        vehicle_cost = sum(v.total_freight for v in self.order.vehicles.all())

        self.total_expense = vehicle_cost
        self.profit = self.total_revenue - self.total_expense

    def save(self, *args, **kwargs):
        self.calculate()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Account - {self.order.order_no}"


# ===============================
# 📒 LEDGER (Transactions)
# ===============================
class Transaction(models.Model):

    TRANSACTION_TYPE = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE
    )

    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount}"