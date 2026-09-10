from decimal import Decimal
from django.db import models

class Customer(models.Model):
    name=models.CharField(max_length=150)
    contact_number=models.CharField(max_length=20, blank=True)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
    
class Order(models.Model):

    LEAD_CHOICES = [
        ("Social Media", "Social Media"),
        ("Outbound Calls", "Outbound Calls"),
        ("Reference", "Reference"),
        ("Field Sales", "Field Sales"),
        ("Justdial", "Justdial"),
    ]

    SOURCE_CHOICES = [
        ("Direct", "Direct"),
        ("Broker", "Broker"),
    ]

    BILLING_CHOICES = [
        ("Retail", "Retail"),
        ("Credit", "Credit"),
    ]

    CUSTOMER_PAYMENT_CHOICES = [
        ("Paid", "Paid"),
        ("Today", "Today"),
        ("TBB", "TBB"),
    ]

    CUSTOMER_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("Account", "Account"),
        ("UPI", "UPI"),
    ]

    APPROVAL_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    trip_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders"
    )

    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    lead_generated_through = models.CharField(
        max_length=40,
        choices=LEAD_CHOICES,
        blank=True
    )

    sales_closed_by = models.CharField(
        max_length=120,
        blank=True
    )

    # =====================================================
    # SHIPMENT DETAILS
    # =====================================================

    origin = models.CharField(
        max_length=120,
        blank=True
    )

    destination = models.CharField(
        max_length=120,
        blank=True
    )

    material = models.CharField(
        max_length=150,
        blank=True
    )

    packing_type = models.CharField(
        max_length=100,
        blank=True
    )

    no_of_pieces = models.PositiveIntegerField(
        default=0
    )

    weight_tons = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0
    )

    # =====================================================
    # VEHICLE DETAILS
    # =====================================================

    vehicle_type = models.CharField(
        max_length=80,
        blank=True
    )

    vehicle_number = models.CharField(
        max_length=30,
        blank=True
    )

    driver_number = models.CharField(
        max_length=20,
        blank=True
    )

    owner_number = models.CharField(
        max_length=20,
        blank=True
    )

    vehicle_sourced_by = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="Direct"
    )

    owner_broker_name = models.CharField(
        max_length=150,
        blank=True
    )

    # =====================================================
    # COMMERCIALS
    # =====================================================

    freight_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    loading_unloading_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    halting_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    other_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total_trip_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    selling_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    manager_approval = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default="Pending"
    )

    approved_by = models.CharField(
        max_length=120,
        blank=True
    )

    # =====================================================
    # PAYMENT TERMS BY CUSTOMER
    # =====================================================

    customer_billing_type = models.CharField(
        max_length=20,
        choices=BILLING_CHOICES,
        blank=True
    )

    customer_payment_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_PAYMENT_CHOICES,
        blank=True
    )

    customer_advance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    customer_balance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    customer_payment_method = models.CharField(
        max_length=20,
        choices=CUSTOMER_METHOD_CHOICES,
        blank=True
    )

    promised_due_date = models.DateField(
        null=True,
        blank=True
    )

    # =====================================================
    # PAYMENT TERMS TO CONTRACTED VEHICLE
    # =====================================================

    vehicle_advance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    vehicle_balance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    vehicle_owner_name = models.CharField(
        max_length=150,
        blank=True
    )

    pan_card = models.CharField(
        max_length=20,
        blank=True
    )

    account_name = models.CharField(
        max_length=150,
        blank=True
    )

    account_number = models.CharField(
        max_length=50,
        blank=True
    )

    ifsc_code = models.CharField(
        max_length=20,
        blank=True
    )

    upi_number = models.CharField(
        max_length=100,
        blank=True
    )

    send_sms = models.BooleanField(
        default=False
    )

    create_agreement_tds = models.BooleanField(
        default=False
    )

    # =====================================================
    # AUDIT
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =====================================================
    # CALCULATIONS
    # =====================================================

    @property
    def customer_selling_amount(self):
        """
        Customer selling amount comes from the Order itself.
        CustomerPayment records are receipts against this amount.
        """
        return self.selling_amount


    @property
    def vehicle_cost(self):
        """
        Total amount paid to the vehicle for this order.
        """
        return sum(
            (
                payment.amount
                for payment in self.vehicle_payments.all()
            ),
            Decimal("0.00")
        )


    @property
    def margin(self):
        """
        Margin = Customer Selling Amount - Total Vehicle Cost
        """
        return (
            self.customer_selling_amount
            - self.vehicle_cost
        )
        # =====================================================
        # SAVE
        # =====================================================

        def save(self, *args, **kwargs):

            self.total_trip_cost = (
                self.freight_amount +
                self.loading_unloading_charges +
                self.halting_charges +
                self.other_charges
            )

            if not self.trip_number:

                last = Order.objects.order_by("-id").first()

                number = (
                    last.id + 2101
                    if last
                    else 2101
                )

                self.trip_number = f"TRIP{number}"

            super().save(*args, **kwargs)

        def __str__(self):

            return (
                f"{self.trip_number} - "
                f"{self.origin} to {self.destination}"
            )

class VehiclePayment(models.Model):
    PAYMENT_TYPES=[('Advance','Advance'),('Balance','Balance'),('Others','Others')]
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='vehicle_payments')
    vehicle_number=models.CharField(max_length=30)
    payment_type=models.CharField(max_length=20,choices=PAYMENT_TYPES)
    amount=models.DecimalField(max_digits=12,decimal_places=2)
    transaction_reference=models.CharField(max_length=100,blank=True)
    paid_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.order.trip_number} - {self.payment_type}'

class CustomerPayment(models.Model):
    PAYMENT_MODES=[('RTGS','RTGS'),('NEFT','NEFT'),('CASH','CASH'),('IMPS','IMPS'),('UPI','UPI')]
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='customer_payments')
    selling_amount=models.DecimalField(max_digits=12,decimal_places=2)
    received_amount=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    received_through=models.CharField(max_length=20,choices=PAYMENT_MODES,blank=True)
    utr_details=models.CharField(max_length=150,blank=True)
    received_at=models.DateTimeField(auto_now_add=True)
    @property
    def status(self):
        if self.received_amount<=0: return 'Pending'
        if self.received_amount>=self.selling_amount: return 'Payment Cleared'
        return 'Part Amount Received'
    def __str__(self): return f'{self.order.trip_number} - Customer Payment'

class TrackingSession(models.Model):

    STATUS_CHOICES = [
    ("not_enabled", "Not Enabled"),
    ("imported", "Imported"),
    ("sms_sent", "SMS Sent"),
    ("consent_received", "Consent Received"),
    ("waiting_location", "Waiting Location"),
    ("active", "Live Tracking"),
    ("paused", "Paused"),
    ("stopped", "Stopped"),
    ("deleted", "Deleted"),
    ("license_hold", "License Hold"),
    ("expired", "Consent Expired"),
    ("error", "Error"),
]
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="tracking_session"
    )

    tracking_reference = models.CharField(
        max_length=100,
        unique=True
    )

    driver_mobile = models.CharField(max_length=15 )

    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default="not_enabled"
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
        return f"{self.order.trip_number}"
  
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