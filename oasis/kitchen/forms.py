from django import forms
from ..dashboard.models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["category", "name", "description", "base_price", "image", "is_available"]
