from django.urls import path

from rentals.views import (
    LocationAutocompleteView,
    PropertySearchView,
)

from rentals.frontend_views import (
    home,
    property_detail,
    property_list,
)

urlpatterns = [
    path(
        "api/locations/autocomplete/",
        LocationAutocompleteView.as_view(),
        name="location-autocomplete",
    ),
    path(
        "api/properties/search/",
        PropertySearchView.as_view(),
        name="property-search",
    ),

    path("", home, name="home"),
    path("properties/", property_list, name="property-list"),
    path(
        "properties/<int:property_id>/",
        property_detail,
        name="property-detail",
    ),
]