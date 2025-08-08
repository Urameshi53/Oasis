from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from oscar.apps.customer.utils import normalise_email
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.forms.mixins import PhoneNumberMixin


User = get_user_model()
AbstractAddressForm = get_class("address.forms", "AbstractAddressForm")
Country = get_model("address", "Country")
ghana = Country('Ghana')


class ShippingAddressForm(PhoneNumberMixin, AbstractAddressForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('phone_number', None)


    class Meta:
        model = get_model("order", "shippingaddress")
        fields = [
            "first_name",
            "last_name",
            "location",
            "hostel",
            "room_number",
            "phone",
            "notes",
        ]


class ShippingMethodForm(forms.Form):
    method_code = forms.ChoiceField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        methods = kwargs.pop("methods", [])
        super().__init__(*args, **kwargs)
        self.fields["method_code"].choices = ((m.code, m.name) for m in methods)

