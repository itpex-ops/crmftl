# vehicles/forms.py
from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_number', 'driver_number', 'owner_number', 'source',
            'freight_amount', 'advance', 'brokerage', 'loading_unloading',
            'upi_number', 'upi_app', 'account_name', 'account_number', 'ifsc', 'ac_type'
        ]
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_number': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_number': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'freight_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'advance': forms.NumberInput(attrs={'class': 'form-control'}),
            'brokerage': forms.NumberInput(attrs={'class': 'form-control'}),
            'loading_unloading': forms.NumberInput(attrs={'class': 'form-control'}),
            'upi_number': forms.TextInput(attrs={'class': 'form-control'}),
            'upi_app': forms.Select(attrs={'class': 'form-select'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc': forms.TextInput(attrs={'class': 'form-control'}),
            'ac_type': forms.TextInput(attrs={'class': 'form-control'}),
        }