
from django import forms


class PropertySearchForm(forms.Form):
    mode = forms.ChoiceField(
        choices=[
            ("place", "Explore a Place"),
            ("stay", "Find a Stay"),
        ],
        initial="place",
        widget=forms.RadioSelect,
    )

    destination = forms.CharField(
        required=False,
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
        required=False,
        min_value=1,
        max_value=500,
        initial=20,
        label="Search radius (km)",
    )

    semantic_query = forms.CharField(
        required=False,
        max_length=255,
        label="Describe your ideal stay",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. A quiet cottage near a lake",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        mode = cleaned_data.get("mode")
        destination = cleaned_data.get("destination", "").strip()
        semantic_query = cleaned_data.get("semantic_query", "").strip()
        radius_km = cleaned_data.get("radius_km")

        if mode == "place":
            if not destination:
                self.add_error(
                    "destination",
                    "Enter a destination.",
                )

            if radius_km is None:
                self.add_error(
                    "radius_km",
                    "Enter a search radius.",
                )

        elif mode == "stay":
            if not semantic_query:
                self.add_error(
                    "semantic_query",
                    "Describe the kind of stay you want.",
                )

        return cleaned_data
