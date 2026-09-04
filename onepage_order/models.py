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
    LEAD_CHOICES=[('Social Media','Social Media'),('Outbound Calls','Outbound Calls'),('Reference','Reference'),('Field Sales','Field Sales'),('Justdial','Justdial')]
    SOURCE_CHOICES=[('Direct','Direct'),('Broker','Broker')]
    trip_number=models.CharField(max_length=30, unique=True, editable=False)
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT,related_name='orders')
    lead_generated_through=models.CharField(max_length=40,choices=LEAD_CHOICES,blank=True)
    sales_closed_by=models.CharField(max_length=120,blank=True)
    origin=models.CharField(max_length=120)
    destination=models.CharField(max_length=120)
    material=models.CharField(max_length=150,blank=True)
    packing_type=models.CharField(max_length=100,blank=True)
    no_of_pieces=models.PositiveIntegerField(default=0)
    weight_tons=models.DecimalField(max_digits=10,decimal_places=3,default=0)
    vehicle_type=models.CharField(max_length=80)
    vehicle_number=models.CharField(max_length=30)
    driver_number=models.CharField(max_length=20,blank=True)
    owner_number=models.CharField(max_length=20,blank=True)
    vehicle_sourced_by=models.CharField(max_length=20,choices=SOURCE_CHOICES,default='Direct')
    owner_broker_name=models.CharField(max_length=150,blank=True)
    freight_amount=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    loading_unloading_charges=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    halting_charges=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    other_charges=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    @property
    def customer_selling_amount(self):
        return sum((x.amount for x in self.customer_payments.all()), Decimal('0.00')) if self.customer_payments.exists() else self.freight_amount + self.loading_unloading_charges + self.halting_charges + self.other_charges
    @property
    def vehicle_cost(self):
        return sum((x.amount for x in self.vehicle_payments.all()), Decimal('0.00'))
    @property
    def margin(self): return self.customer_selling_amount - self.vehicle_cost
    def save(self,*args,**kwargs):
        if not self.trip_number:
            last=Order.objects.order_by('-id').first()
            n=(last.id+2101) if last else 2101
            self.trip_number=f'TRIP{n}'
        super().save(*args,**kwargs)
    def __str__(self): return f'{self.trip_number} - {self.origin} to {self.destination}'

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
