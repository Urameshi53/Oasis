from django import forms

from .models import RiderProfile


class BecomeRiderForm(forms.ModelForm):
    class Meta:
        model = RiderProfile
        fields = ["phone", "vehicle_type"]
        widgets = {
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. 0551234567", "autofocus": "autofocus"}
            ),
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {"phone": "Phone number", "vehicle_type": "How will you deliver?"}
