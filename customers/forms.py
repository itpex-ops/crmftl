from django import forms
from .models import ExCustomer


class ExCustomerForm(forms.ModelForm):

    class Meta:
        model = ExCustomer
        fields = "__all__"

        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }