from django import forms
from .models import ExCustomer

class ExCustomerForm(forms.ModelForm):

    class Meta:
        model = ExCustomer
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["is_active"].widget.attrs["class"] = "form-check-input"

        self.fields["customer_code"].widget.attrs["readonly"] = True

        self.fields["address"].widget.attrs.update({
            "rows": 3
        })