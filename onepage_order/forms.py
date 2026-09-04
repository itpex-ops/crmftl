from django import forms
from .models import Customer, Order, VehiclePayment, CustomerPayment

class BootstrapMixin:
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values(): field.widget.attrs.setdefault('class','form-control')

class CustomerForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model=Customer; fields=['name','contact_number','email','address']
        widgets={'address':forms.Textarea(attrs={'rows':2})}

class OrderForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model=Order
        exclude=['trip_number','created_at','updated_at','customer']
        widgets={'weight_tons':forms.NumberInput(attrs={'step':'0.001'}),'no_of_pieces':forms.NumberInput(attrs={'min':0})}

class VehiclePaymentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model=VehiclePayment; fields=['order','vehicle_number','payment_type','amount','transaction_reference']

class CustomerPaymentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model=CustomerPayment; fields=['order','selling_amount','received_amount','received_through','utr_details']
