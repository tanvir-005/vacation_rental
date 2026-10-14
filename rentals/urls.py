from django.urls import path

from rentals.views import LocationAutocompleteView

urlpatterns = [
    path(
        "api/locations/autocomplete/",
        LocationAutocompleteView.as_view(),
        name="location-autocomplete",
    ),
]