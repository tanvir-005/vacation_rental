
from urllib.parse import urlencode

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from rentals.forms import PropertySearchForm
from rentals.models import Property
from rentals.services.semantic_search import search_locations


def home(request):
    form = PropertySearchForm(request.GET or None)

    if request.GET and form.is_valid():
        query = urlencode({
            "q": form.cleaned_data["destination"],
            "radius_km": form.cleaned_data["radius_km"],
        })

        return redirect(f"/properties/?{query}")

    return render(
        request,
        "rentals/home.html",
        {"form": form},
    )


def property_list(request):
    destination = request.GET.get("q", "").strip()

    try:
        radius_km = float(request.GET.get("radius_km", 20))
    except (TypeError, ValueError):
        radius_km = 20

    if not 1 <= radius_km <= 500:
        radius_km = 20

    selected_location = None
    properties = Property.objects.none()

    if destination:
        selected_location = next(
            iter(search_locations(destination, limit=1)),
            None,
        )

        if selected_location and selected_location.point:
            properties = (
                Property.objects
                .filter(
                    point__distance_lte=(
                        selected_location.point,
                        D(km=radius_km),
                    )
                )
                .annotate(
                    distance=Distance("point", selected_location.point)
                )
                .prefetch_related("images")
                .order_by("distance", "id")
            )

    paginator = Paginator(properties, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "rentals/property_list.html",
        {
            "page_obj": page_obj,
            "selected_location": selected_location,
            "radius_km": radius_km,
            "destination": destination,
        },
    )


def property_detail(request, property_id):
    property_obj = get_object_or_404(
        Property.objects.prefetch_related("images"),
        pk=property_id,
    )

    destination = request.GET.get("q", "").strip()

    try:
        radius_km = float(request.GET.get("radius_km", 20))
    except (TypeError, ValueError):
        radius_km = 20

    if not 1 <= radius_km <= 500:
        radius_km = 20

    selected_location = None
    distance_km = None

    if destination:
        selected_location = next(
            iter(search_locations(destination, limit=1)),
            None,
        )

        if selected_location and selected_location.point:
            distance_km = (
                property_obj.point.distance(selected_location.point) / 1000
            )

    return render(
        request,
        "rentals/property_detail.html",
        {
            "property": property_obj,
            "selected_location": selected_location,
            "distance_km": distance_km,
            "radius_km": radius_km,
        },
    )
