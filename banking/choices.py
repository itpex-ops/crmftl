PAYMENT_TYPE_CHOICES = (
    ("advance", "Advance"),
    ("balance", "Balance"),
    ("fuel", "Fuel"),
    ("driver_advance", "Driver Advance"),
    ("brokerage", "Brokerage"),
    ("other", "Other"),
)

PAYMENT_MODE_CHOICES = (
    ("neft", "NEFT"),
    ("rtgs", "RTGS"),
    ("imps", "IMPS"),
    ("upi", "UPI"),
)

PAYMENT_STATUS_CHOICES = (
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("success", "Success"),
    ("failed", "Failed"),
)

UPI_STATUS_CHOICES = (
    
    ("created", "Created"),
    ("pending", "Pending"),
    ("success", "Success"),
    ("failed", "Failed"),
    ("expired", "Expired"),
)

BILL_PAYMENT_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("success", "Success"),
    ("failed", "Failed"),
)
