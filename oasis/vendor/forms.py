from django import forms

from oscar.core.loading import get_model

from .models import VendorProfile

Partner = get_model("partner", "Partner")


class VendorProfileForm(forms.ModelForm):
    """Branding-only fields (rendered in the 'Storefront' section)."""

    class Meta:
        model = VendorProfile
        fields = ["tagline", "description", "logo", "banner"]
        widgets = {
            "tagline": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Fresh groceries, delivered fast"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4,
                       "placeholder": "Tell customers about your store…"}
            ),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "banner": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "logo": "Square image works best.",
            "banner": "Wide image shown at the top of your store.",
        }


class PayoutSettingsForm(forms.ModelForm):
    """Payout/settlement fields a seller controls (not their commission rate)."""

    class Meta:
        model = VendorProfile
        fields = ["settlement_bank", "account_number", "paystack_subaccount_code"]
        labels = {
            "settlement_bank": "Settlement bank / MoMo provider",
            "account_number": "Account / MoMo number",
            "paystack_subaccount_code": "Paystack subaccount code",
        }
        widgets = {
            "settlement_bank": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. MTN, Vodafone, GCB"}),
            "account_number": forms.TextInput(attrs={"class": "form-control"}),
            "paystack_subaccount_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "ACCT_xxxxxxxx"}),
        }
        help_texts = {
            "paystack_subaccount_code": "Where your share of each sale is paid. Ask an admin if you don't have one yet.",
        }


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ["name"]
        labels = {"name": "Shop name"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise forms.ValidationError("Please enter a shop name.")
        return name


class BecomeSellerForm(forms.Form):
    shop_name = forms.CharField(
        label="Shop name",
        max_length=128,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Sahara Traders",
                "autofocus": "autofocus",
            }
        ),
        help_text="This is the name customers will see as the seller of your products.",
    )
