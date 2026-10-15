
from urllib.parse import urlencode

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from pgvector.django import CosineDistance

from rentals.forms import PropertySearchForm
from rentals.models import Property
from rentals.services.semantic_search import (
    get_embedding_model,
    search_locations,
)


def home(request):
    form = PropertySearchForm(request.GET or None)

    if request.GET and form.is_valid():
        data = form.cleaned_data
        params = {"mode": data["mode"]}

        if data["mode"] == "place":
            params["q"] = data["destination"]
            params["radius_km"] = data["radius_km"]
        else:
            params["search"] = data["semantic_query"]

        return redirect(
            f"/properties/?{urlencode(params)}"
        )

    return render(
        request,
        "rentals/home.html",
        {"form": form},
    )


def property_list(request):
    destination = request.GET.get("q", "").strip()
    semantic_query = request.GET.get("search", "").strip()
    mode = request.GET.get("mode", "").strip()

    # Support older URLs that do not include a mode.
    if mode not in ("place", "stay"):
        mode = (
            "place"
            if destination
            else "stay" if semantic_query else "place"
        )

    try:
        radius_km = float(request.GET.get("radius_km", 20))
    except (TypeError, ValueError):
        radius_km = 20

    if not 1 <= radius_km <= 500:
        radius_km = 20

    selected_location = None
    properties = Property.objects.none()
    search_error = None

    if mode == "place" and destination:
        selected_location = next(
            iter(search_locations(destination, limit=1)),
            None,
        )

        if selected_location and selected_location.point:
            properties = (
                Property.objects
                .filter(
                    embedding__isnull=False,
                    point__distance_lte=(
                        selected_location.point,
                        D(km=radius_km),
                    ),
                )
                .annotate(
                    distance=Distance(
                        "point",
                        selected_location.point,
                    )
                )
                .prefetch_related("images")
                .order_by("distance", "id")
            )
        else:
            search_error = (
                "No matching destination with coordinates was found."
            )

    elif mode == "stay" and semantic_query:
        model = get_embedding_model()
        query_embedding = model.encode(
            semantic_query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        properties = (
            Property.objects
            .filter(embedding__isnull=False)
            .annotate(
                semantic_distance=CosineDistance(
                    "embedding",
                    query_embedding,
                )
            )
            .prefetch_related("images")
            .order_by("semantic_distance", "id")
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
            "semantic_query": semantic_query,
            "mode": mode,
            "search_error": search_error,
        },
    )


def property_detail(request, property_id):
    property_obj = get_object_or_404(
        Property.objects.prefetch_related("images"),
        pk=property_id,
    )

    destination = request.GET.get("q", "").strip()
    semantic_query = request.GET.get("search", "").strip()
    mode = request.GET.get("mode", "").strip()

    # Infer the mode for older detail-page URLs.
    if mode not in ("place", "stay"):
        mode = (
            "place"
            if destination
            else "stay" if semantic_query else "place"
        )

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

        if (
            selected_location
            and selected_location.point
            and property_obj.point
        ):
            distance_km = (
                property_obj.point.distance(
                    selected_location.point
                ) / 1000
            )

    # Preserve the original search when returning to the results.
    back_params = {"mode": mode}

    if destination:
        back_params["q"] = destination
        back_params["radius_km"] = radius_km

    if semantic_query:
        back_params["search"] = semantic_query

    back_url = f"/properties/?{urlencode(back_params)}"

    return render(
        request,
        "rentals/property_detail.html",
        {
            "property": property_obj,
            "selected_location": selected_location,
            "distance_km": distance_km,
            "radius_km": radius_km,
            "destination": destination,
            "semantic_query": semantic_query,
            "mode": mode,
            "back_url": back_url,
        },
    )
