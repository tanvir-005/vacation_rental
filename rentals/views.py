
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

from rest_framework.response import Response
from rest_framework.views import APIView

from rentals.models import Property
from rentals.serializers import (
    LocationAutocompleteQuerySerializer,
    LocationAutocompleteSerializer,
    PropertySearchQuerySerializer,
    PropertySearchSerializer,
)
from rentals.services.semantic_search import search_locations


class LocationAutocompleteView(APIView):
    def get(self, request):
        query_serializer = LocationAutocompleteQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        query = query_serializer.validated_data["q"]
        limit = query_serializer.validated_data["limit"]

        locations = search_locations(query, limit=limit)

        response_serializer = LocationAutocompleteSerializer(
            locations,
            many=True,
        )

        return Response({
            "query": query,
            "results": response_serializer.data,
        })


class PropertySearchView(APIView):
    def get(self, request):
        query_serializer = PropertySearchQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        query = query_serializer.validated_data["q"]
        radius_km = query_serializer.validated_data["radius_km"]
        limit = query_serializer.validated_data["limit"]

        location = next(iter(search_locations(query, limit=1)), None)

        if location is None or location.point is None:
            return Response({
                "query": query,
                "message": "No matching location with coordinates was found.",
                "selected_location": None,
                "results": [],
            })

        properties = (
            Property.objects
            .filter(
                point__distance_lte=(
                    location.point,
                    D(km=radius_km),
                )
            )
            .annotate(
                distance=Distance("point", location.point)
            )
            .order_by("distance", "id")[:limit]
        )

        response_serializer = PropertySearchSerializer(
            properties,
            many=True,
        )

        return Response({
            "query": query,
            "selected_location": {
                "id": location.id,
                "name": location.name,
            },
            "radius_km": radius_km,
            "results": response_serializer.data,
        })
