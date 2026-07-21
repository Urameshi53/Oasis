from django import forms
from django.contrib.auth.models import User

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    # Custom fields
    phone = forms.CharField(required=False)
    location = forms.CharField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["password1"] != cleaned_data["password2"]:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

            # Save profile fields
            user.userprofile.phone = self.cleaned_data["phone"]
            user.userprofile.location = self.cleaned_data["location"]
            user.userprofile.save()

        return user
