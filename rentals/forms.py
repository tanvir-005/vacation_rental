
from django import forms


class PropertySearchForm(forms.Form):
    destination = forms.CharField(
        max_length=255,
        label="Destination",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Where do you want to go?",
                "autocomplete": "off",
            }
        ),
    )

    radius_km = forms.FloatField(
        min_value=1,
        max_value=500,
        initial=20,
        label="Search radius (km)",
    )
