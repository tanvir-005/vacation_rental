
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

from pgvector.django import CosineDistance
from rest_framework.response import Response
from rest_framework.views import APIView

from rentals.models import Property
from rentals.serializers import (
    LocationAutocompleteQuerySerializer,
    LocationAutocompleteSerializer,
    PropertySearchQuerySerializer,
    PropertySearchSerializer,
)
from rentals.services.semantic_search import (
    get_embedding_model,
    search_locations,
)


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

        data = query_serializer.validated_data
        query = data["q"]
        radius_km = data["radius_km"]
        limit = data["limit"]
        destination = data["destination"]

        model = get_embedding_model()
        query_embedding = model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        properties = Property.objects.filter(
            embedding__isnull=False
        )

        selected_location = None

        if destination:
            selected_location = next(
                iter(search_locations(destination, limit=1)),
                None,
            )

            if (
                selected_location is None
                or selected_location.point is None
            ):
                return Response({
                    "query": query,
                    "destination": destination,
                    "message": (
                        "No matching destination with coordinates was found."
                    ),
                    "selected_location": None,
                    "results": [],
                })

            properties = properties.filter(
                point__distance_lte=(
                    selected_location.point,
                    D(km=radius_km),
                )
            ).annotate(
                distance=Distance("point", selected_location.point)
            )

        properties = (
            properties
            .annotate(
                semantic_distance=CosineDistance(
                    "embedding",
                    query_embedding,
                )
            )
            .select_related("location")
            .order_by("semantic_distance", "id")[:limit]
        )

        response_serializer = PropertySearchSerializer(
            properties,
            many=True,
        )

        response = {
            "query": query,
            "destination": destination or None,
            "radius_km": radius_km if destination else None,
            "results": response_serializer.data,
        }

        if selected_location:
            response["selected_location"] = {
                "id": selected_location.id,
                "name": selected_location.name,
            }

        return Response(response)
