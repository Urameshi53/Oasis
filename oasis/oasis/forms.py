from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.apps.customer.forms import EmailUserCreationForm


class RegistrationForm(EmailUserCreationForm):
    """Oscar's registration form + first/last name (collected at sign-up)."""

    first_name = forms.CharField(
        label=_("First name"),
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": "autofocus"}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    field_order = ["first_name", "last_name", "email", "password1", "password2"]

    class Meta(EmailUserCreationForm.Meta):
        # Adding these to the model fields means they're saved onto the User.
        fields = ("first_name", "last_name", "email")
